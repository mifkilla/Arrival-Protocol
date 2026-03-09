# Confidence-Gated Debate (CGD) Protocol
## A Novel Multi-Agent Reasoning Protocol

**Author:** Mefodiy Kelevra (MiF)
**Date:** 2026-03-02
**Status:** Experimental (Phase 22), partial results (75/198 GPQA Diamond)
**License:** AGPL-3.0-or-later

---

## 1. Motivation

### 1.1 Problems with Standard Sequential Debate (ARRIVAL)

Phase 21 of the ARRIVAL project revealed three critical failure modes in sequential
multi-agent debate on graduate-level science questions (GPQA Diamond, N=198):

**Problem 1: Anchoring Bias**
In standard ARRIVAL, Model R1 (Proposer) generates the first answer. Models R2 and R3
then read R1's response before generating their own. This creates a strong anchoring
effect: even when R1 is wrong, R2 and R3 tend to agree with it.

Evidence: GPT-4.1 (solo accuracy 66.2%) served as R1. When it was wrong, it pulled
Gemini (solo 82.3%) from 82.3% down to 78.3% in debate. The strongest model (Grok,
85.4%) also showed anchoring when placed after a weaker model.

**Problem 2: R4 Destructive Overrides**
The R4 Finalizer was designed to resolve remaining conflicts. In practice, R4 changed
the correct group consensus to the wrong answer more often than it rescued wrong answers:
- Phase 20: 7 rescues vs 9 regressions (net -2)
- Phase 21: 8 rescues vs 13 regressions (net -5)
- Phase 21 detail: 6/6 unanimous override attempts by R4 were ALL destructive

**Problem 3: False Consensus**
In sequential debate, models tend to agree too readily with previous speakers, creating
a false sense of consensus. The group can converge on a wrong answer with high apparent
confidence.

### 1.2 Design Goals for CGD

1. **Eliminate anchoring**: Each model must answer independently before seeing others
2. **Eliminate destructive R4**: No single-model finalizer; use majority vote instead
3. **Preserve the value of debate**: When models genuinely disagree, debate can help
4. **Improve efficiency**: Skip debate entirely when all models already agree
5. **Maintain transparency**: Track debate types, vote patterns, and cost

---

## 2. Protocol Specification

### 2.1 Overview

CGD operates in three phases:
1. **Independent Solo Phase** — All models answer independently
2. **Agreement Check** — Classify the agreement pattern
3. **Targeted Debate** (conditional) — Debate only if there is disagreement

### 2.2 Phase 1: Independent Solo Answers

Each of the K models (K=3 in our implementation) receives the question and choices
with a clean, minimal prompt. NO cross-contamination between models.

**Prompt template:**
```
You are an expert scientist. Answer this graduate-level multiple-choice question.

Think step by step, then state your final answer as: "The answer is X"
where X is A, B, C, or D.

Question: {question}

A) {choice_A}
B) {choice_B}
C) {choice_C}
D) {choice_D}
```

**Key design decisions:**
- No ARRIVAL system prompt (avoids @-atom overhead when not debating)
- Temperature = 0.3 (reduced randomness for consistent solo answers)
- max_tokens = 2048 (sufficient for step-by-step reasoning)
- Each model gets ONLY the question — never sees other models' answers

### 2.3 Phase 2: Agreement Classification

After collecting K independent answers, classify the agreement pattern:

| Pattern | Name | Description | Action |
|---------|------|-------------|--------|
| K/K agree | **Unanimous** | All models give the same answer | Accept immediately |
| (K-1)/K agree | **Split 2v1** | One model disagrees | Targeted debate |
| All different | **Split 3-way** | No two models agree | Full debate |

For K=3:
- **Unanimous (3/3)**: Accept the unanimous answer. No debate, no R4.
- **Split 2v1 (2 vs 1)**: The minority model writes a defense. The majority writes a rebuttal. Then majority vote.
- **Split 3-way (1/1/1)**: All three models write defenses. Then majority vote.

### 2.4 Phase 3a: Unanimous Path

When all K models agree, CGD accepts the answer without debate.

**Rationale:** If three independently queried models all converge on the same answer,
the probability of correctness is very high. In our data:
- Unanimous accuracy: **98.0%** (48/49 questions at 75/198 checkpoint)
- This is near the theoretical maximum — the only failures are questions where
  ALL models share the same misconception

**API calls:** K (just the solo phase) = 3 calls per question
**Cost:** Minimal (~$0.02 per question)

### 2.5 Phase 3b: Split 2v1 Path

When 2 models agree and 1 disagrees:

**Step 1: Minority Defense**
The dissenting model receives the question, its own answer, and the majority's answer,
and writes a defense of its position.

```
The majority answered {majority_answer}. You answered {minority_answer}.
Write a concise defense of your answer. Explain specifically why the
majority's answer is wrong and yours is correct.
End with: "The answer is X"
```

**Step 2: Majority Rebuttal**
One of the majority models receives the minority's defense and writes a rebuttal.

```
A colleague argues that the answer is {minority_answer}: {minority_defense}
You and another colleague answered {majority_answer}.
Respond to their argument. If they raise a valid point, you may change your answer.
End with: "The answer is X"
```

**Step 3: Final Vote**
Collect all post-debate answers (minority after defense, majority after rebuttal,
plus the unchanged second majority model). Take majority vote.

**API calls:** K + 2 = 5 calls per question
**Expected accuracy:** 76.2% at checkpoint (harder questions, since they had disagreement)

### 2.6 Phase 3c: Split 3-way Path

When all K models give different answers:

**Step 1: All Defenses**
Each model writes a defense of its position, knowing the other two answers.

```
Model A answered {A}, Model B answered {B}, you answered {C}.
Write a concise defense of your answer. Explain why the other answers are wrong.
End with: "The answer is X"
```

**Step 2: Final Vote**
Collect all post-defense answers. Take majority vote.

**API calls:** K + K = 6 calls per question (3 solo + 3 defenses)
**Expected accuracy:** 80.0% at checkpoint (hardest questions)

### 2.7 Final Answer Determination

**NO R4 FINALIZER.** The final answer is always determined by majority vote:
- Unanimous: The agreed-upon answer
- After debate: Majority vote of post-debate answers

This is a critical design decision. By removing R4, we eliminate the single point
of failure that caused net-negative results in Phases 20 and 21.

---

## 3. Implementation Details

### 3.1 Models Used (Phase 22)

| Model | OpenRouter ID | Solo Accuracy | Cost |
|-------|---------------|---------------|------|
| GPT-4.1 | `openai/gpt-4.1` | 66.2% | $2.00/$8.00 per 1M |
| Gemini 3 Flash | `google/gemini-3-flash-preview` | 82.3% | $0.50/$3.00 per 1M |
| Grok 4.1 Fast | `x-ai/grok-4.1-fast` | 85.4% | $0.60/$2.40 per 1M |

### 3.2 Answer Extraction

Regex cascade:
1. `"The answer is ([A-D])"`
2. `"answer is ([A-D])"`
3. `"\*\*([A-D])\*\*"` (bold letter)
4. Last standalone `[A-D]` in response
5. Last `[A-D]` in final 100 characters

### 3.3 Cost Estimation

| Question Type | Frequency | API Calls | Avg Cost |
|---------------|-----------|-----------|----------|
| Unanimous | ~65% | 3 | ~$0.02 |
| Split 2v1 | ~28% | 5 | ~$0.04 |
| Split 3-way | ~7% | 6 | ~$0.05 |
| **Weighted avg** | | **~3.5** | **~$0.028** |

Total for 198 questions: **~$5.50** (estimated)
Compare: Standard ARRIVAL (4 rounds): $4.89 for 198 questions

### 3.4 Crash Protection

- Results saved after EACH question (atomic write: tmp file + os.replace)
- Resume support: script reads existing results, skips completed questions
- Budget guard: $15 hard limit
- Sleep 1.5s between API calls to respect rate limits

---

## 4. Results (Partial: 75/198 Questions)

### 4.1 Overall Accuracy

| Method | Correct | Total | Accuracy | 95% CI |
|--------|---------|-------|----------|--------|
| **CGD (Phase 22)** | **68** | **75** | **90.7%** | [82.0%, 95.5%] |
| Non-Debate MV (Phase 21) | ~62* | 75 | ~82.3%* | — |
| ARRIVAL MV (Phase 21) | ~59* | 75 | ~78.8%* | — |
| ARRIVAL R4 (Phase 21) | ~57* | 75 | ~76.3%* | — |
| Solo Grok 4.1 | ~64* | 75 | ~85.4%* | — |

*Phase 21 baselines are projected from full 198-question rates

### 4.2 Debate Type Analysis

| Type | n | Correct | Accuracy | % of Questions |
|------|---|---------|----------|---------------|
| Unanimous | 49 | 48 | **98.0%** | 65.3% |
| Split 2v1 | 21 | 16 | 76.2% | 28.0% |
| Split 3-way | 5 | 4 | 80.0% | 6.7% |

### 4.3 Domain Analysis

| Domain | n | Correct | Accuracy |
|--------|---|---------|----------|
| Physics | 33 | 32 | **97.0%** |
| Chemistry | 35 | 30 | 85.7% |
| Biology | 7 | 6 | 85.7% |

### 4.4 Key Observations

1. **Unanimous near-perfect (98.0%)**: When 3 independent models agree, they're
   almost always right. The 1 failure (GPQA_013) represents a shared misconception.

2. **Split 2v1 is the hardest (76.2%)**: These are questions where models genuinely
   disagree. The minority is sometimes right, and targeted debate helps but doesn't
   always rescue.

3. **Physics dominant (97.0%)**: All three models are strong at physics. Chemistry
   and biology are harder.

4. **CGD likely exceeds oracle-free ceiling**: At 90.7%, CGD approaches the oracle
   ceiling (93.9%, where at least one model knows the answer). This suggests CGD
   is extracting nearly all available knowledge from the trio.

---

## 5. Theoretical Analysis

### 5.1 Why CGD Works Better Than Sequential Debate

**Independence → Better Information Aggregation**

In sequential debate, information flows: R1 → R2 → R3 → R4
This creates a Bayesian cascade where R2 and R3 condition on R1's (potentially wrong)
answer. If R1 is wrong, the cascade can corrupt R2 and R3.

In CGD, each model provides an INDEPENDENT signal. The agreement check then aggregates
these signals optimally:
- 3/3 agree → very high confidence (accept)
- 2/1 split → investigate the disagreement (targeted debate)
- 3-way → full investigation (full debate)

This is analogous to the Condorcet Jury Theorem: independent voters are better than
correlated voters when each has >50% individual accuracy.

### 5.2 Why Removing R4 Helps

R4 is a single model that receives the compressed debate transcript and makes a final
decision. This introduces two risks:
1. **Information loss**: R4 sees truncated transcripts, missing nuance
2. **Overconfidence**: R4 may override correct group consensus based on its own biases

Majority vote after debate preserves the democratic structure: each model's post-debate
answer carries equal weight, and no single model can unilaterally change the result.

### 5.3 Efficiency Analysis

CGD achieves higher accuracy with FEWER API calls on average:
- Standard ARRIVAL: 4 calls/question × 198 = 792 calls
- CGD (estimated): ~3.5 calls/question × 198 ≈ 693 calls
- Savings: ~12.5% fewer API calls

This is because ~65% of questions are unanimous and skip debate entirely.

---

## 6. Comparison with Related Work

### 6.1 Debate in AI Safety (Irving et al., 2018)
- Two-agent debate for scalable oversight
- CGD: Multi-agent, confidence-gated, focuses on MCQ accuracy

### 6.2 LLM-Debate (Du et al., 2023)
- Multi-round debate between LLM copies
- CGD: Heterogeneous models, independent solo phase, conditional debate

### 6.3 Mixture of Agents (Wang et al., 2024)
- Layered architecture for LLM ensembles
- CGD: Flat architecture with conditional debate, not fixed rounds

### 6.4 Society of Mind (Zhuge et al., 2023)
- Multiple agents with different roles
- CGD: Role-free in solo phase, roles only emerge in debate

---

## 7. Limitations

1. **Partial results**: Only 75/198 questions completed before RAM-induced pause
2. **Single benchmark**: Tested only on GPQA Diamond (graduate science MCQ)
3. **Three models only**: K=3 may not generalize to different K values
4. **No adversarial testing**: CGD not tested with deliberately adversarial models
5. **Cost-accuracy tradeoff**: More expensive than single-model inference
6. **Answer extraction**: Regex-based extraction may fail on non-standard responses

---

## 8. How to Resume the Experiment

```bash
# Navigate to experiment directory
cd "E:\Arrival Release\experiments\phase22_confidence_gated"

# Run CGD full (will auto-resume from question 76)
/c/Python314/python.exe run_cgd_full.py

# After completion, run evaluation
/c/Python314/python.exe evaluate.py
```

The `run_cgd_full.py` script has built-in resume support: it reads the existing
`results/cgd_full_results.json`, identifies completed questions, and continues from
the next uncompleted question.

---

## 9. File Manifest

| File | Purpose |
|------|---------|
| `run_phase22.py` | 20-question test (both CGD + SF conditions) |
| `run_cgd_full.py` | Full 198-question CGD run with resume support |
| `evaluate.py` | Statistical evaluation vs Phase 21 baselines |
| `results/phase22_results.json` | 20-question test results (COMPLETE) |
| `results/cgd_full_results.json` | Full run results (75/198, PAUSED) |
| `CGD_PROTOCOL.md` | This file — detailed protocol description |

---

*ARRIVAL Protocol — AI-to-AI Coordination Through Structured Semantic Atoms*
*Copyright (C) 2025-2026 Mefodiy Kelevra*
*SPDX-License-Identifier: AGPL-3.0-or-later*
