# Phase 21: ARRIVAL with Strong Heterogeneous Models on GPQA Diamond

**Date**: 2026-03-02
**Author**: Mefodiy Kelevra (automated with Claude)
**Status**: COMPLETE

---

## 1. Objective

Phase 20 showed ARRIVAL MV at 67.7% vs Solo CoT at 62.1% (+5.6 pp, McNemar p=0.233, n.s.) using mid-tier models (GPT-4o, DeepSeek V3, Llama 3.3 70B). The non-significant result may reflect weak base models rather than protocol failure.

**Phase 21 hypothesis**: Stronger models with higher solo baselines will produce a larger, significant debate effect. "You cannot debate your way to a correct answer if nobody knows chemistry."

**Primary test**: McNemar ARRIVAL MV vs Non-Debate MV (same 3 models, debate vs no debate) — this isolates the causal effect of structured discussion.

**Result**: Hypothesis REJECTED. Stronger models improve ARRIVAL accuracy (+11pp vs Phase 20) but Non-Debate MV outperforms ARRIVAL MV by 3.5pp (82.3% vs 78.8%, p=0.265 n.s.). Structured debate does NOT add accuracy when strong models already know the answer.

---

## 2. Models

| Role | Model | OpenRouter ID | Type |
|------|-------|---------------|------|
| R1 (Proposer) | GPT-4.1 | `openai/gpt-4.1` | Frontier (OpenAI) |
| R2 (Critic) | Gemini 3 Flash | `google/gemini-3-flash-preview` | Frontier (Google) |
| R3 (Synthesizer) | Grok 4.1 Fast | `x-ai/grok-4.1-fast` | Frontier (xAI) |
| R4 (Finalizer) | GPT-4.1 | `openai/gpt-4.1` | Same as R1 |

**Key design**: Maximum vendor diversity (OpenAI x Google x xAI). All models are frontier-tier, unlike Phase 20's mid-tier trio.

---

## 3. Conditions

### Condition A: ARRIVAL (4-round sequential debate)
- Round 1: GPT-4.1 proposes independently
- Round 2: Gemini 3 Flash critiques R1 (sees R1 response)
- Round 3: Grok 4.1 Fast synthesizes (sees R1+R2)
- Round 4: GPT-4.1 finalizes (sees R1+R2+R3)
- temp=0.3, max_tokens=2048

### Condition B: Solo Baselines (non-debate)
- Each of the 3 models answers all 198 questions independently
- Single-shot, temp=0.3, max_tokens=2048
- Non-Debate MV = majority vote of 3 solo answers

---

## 4. Results

### 4.1 Overall Accuracy

| Condition | Correct | Total | Accuracy | 95% CI |
|-----------|---------|-------|----------|--------|
| **Non-Debate MV** | **163** | 198 | **82.3%** | [76.4%, 87.0%] |
| ARRIVAL MV (debate) | 156 | 198 | 78.8% | [72.6%, 83.9%] |
| ARRIVAL R4 (debate) | 151 | 198 | 76.3% | [69.9%, 81.7%] |
| Solo Grok 4.1 Fast | 169 | 198 | **85.4%** | [79.8%, 89.6%] |
| Solo Gemini 3 Flash | 163 | 198 | 82.3% | [76.4%, 87.0%] |
| Solo GPT-4.1 | 131 | 198 | 66.2% | [59.3%, 72.4%] |

### 4.2 PRIMARY TEST: McNemar ARRIVAL MV vs Non-Debate MV

Contingency table:

|  | ND correct | ND wrong |
|--|------------|----------|
| ARRIVAL MV correct | 145 | 11 (debate wins) |
| ARRIVAL MV wrong | 18 (debate losses) | 24 |

- **McNemar chi2 = 1.241, p = 0.265 (NOT significant)**
- Debate wins: 11, Debate losses: 18, **Net: -7**
- **Result: Debate HURTS accuracy** (by -3.5pp, but not significantly)

### 4.3 SECONDARY TESTS

**R4 vs MV (within ARRIVAL):**
- R4 rescues: 8, R4 regressions: 13, Net: -5
- McNemar p = 0.383 (R4 is net negative, again)

**ARRIVAL MV vs Solo GPT-4.1:**
- ARRIVAL wins: 33, GPT wins: 8, Net: +25
- **McNemar chi2 = 14.05, p = 0.000178 (HIGHLY SIGNIFICANT)**
- ARRIVAL significantly outperforms the weakest trio member

### 4.4 Per-Domain Breakdown

| Domain | n | AR MV | AR R4 | ND MV | GPT | Gemini | Grok |
|--------|---|-------|-------|-------|-----|--------|------|
| Physics | 86 | 89.5% | 87.2% | **93.0%** | 80.2% | 93.0% | **94.2%** |
| Chemistry | 93 | 71.0% | 65.6% | **75.3%** | 52.7% | 77.4% | **80.6%** |
| Biology | 19 | 68.4% | **78.9%** | 68.4% | 68.4% | 57.9% | 68.4% |

**Key observations:**
- Non-Debate MV beats ARRIVAL MV in Physics (-3.5pp) and Chemistry (-4.3pp)
- Biology is the only domain where ARRIVAL R4 (78.9%) exceeds ND MV (68.4%)
- Grok 4.1 dominates: 94.2% Physics, 80.6% Chemistry

### 4.5 Per-Model Accuracy within ARRIVAL (debate context)

| Model | Role | Solo Accuracy | In-debate Accuracy | Delta |
|-------|------|---------------|-------------------|-------|
| GPT-4.1 | R1 (Proposer) | 66.2% | 66.2% | 0.0pp |
| Gemini 3 Flash | R2 (Critic) | 82.3% | 78.3% | **-4.0pp** |
| Grok 4.1 Fast | R3 (Synthesizer) | 85.4% | 86.9% | **+1.5pp** |

**Critical finding**: Gemini LOSES 4pp of accuracy when debating. It sees R1's (GPT-4.1's) lower-quality answer and sometimes abandons its own correct answer. Grok, as R3 (seeing both R1 and R2), is slightly helped.

### 4.6 Flip Rates

| Transition | Flips | Rate |
|------------|-------|------|
| R1 -> R2 | 40 | 20.2% |
| R2 -> R3 | 28 | 14.1% |
| R3 -> R4 | 28 | 14.1% |

R1->R2 has the highest flip rate (20.2%), consistent with R2 (Gemini) critically reviewing R1 (GPT-4.1)'s weaker proposal.

### 4.7 CRDT Metrics

- Average CARE Resolve: **0.941** (high consensus, as expected with strong models)
- Average Meaning Debt: 0.537
- CARE range: 0.327 -- 1.000

---

## 5. Phase 20 Comparison (Weak vs Strong Trio)

| Metric | Phase 20 (weak) | Phase 21 (strong) | Delta |
|--------|----------------|-------------------|-------|
| ARRIVAL MV | 67.7% | **78.8%** | **+11.1pp** |
| ARRIVAL R4 | 66.7% | **76.3%** | **+9.6pp** |
| Non-Debate MV | N/A | 82.3% | -- |
| Solo CoT MV (Qwen3) | 62.1% | N/A | -- |
| Best solo model | 66.2% (DeepSeek V3) | **85.4% (Grok 4.1)** | +19.2pp |
| McNemar p (debate vs solo) | 0.233 | 0.265 | -- |

**Key insight**: Stronger models improve BOTH ARRIVAL and solo baselines, but solo baselines improve MORE. The debate protocol adds a constant overhead (R4 regressions, Gemini accuracy loss) that becomes proportionally larger as models improve.

---

## 6. Cost Summary

| Component | Cost | API calls |
|-----------|------|-----------|
| ARRIVAL (198 x 4) | $4.89 | 792 |
| Solo GPT-4.1 | $1.44 | 198 |
| Solo Gemini 3 Flash | $0.46 | 198 |
| Solo Grok 4.1 Fast | $2.84 | 198 |
| **TOTAL** | **$9.63** | **1,386** |

Budget: $9.63 / $20.00 limit (48% used)

---

## 7. Extraction Quality

| Model | Missing answers | Rate |
|-------|----------------|------|
| ARRIVAL R1 (GPT-4.1) | 7 | 3.5% |
| ARRIVAL R2 (Gemini) | 2 | 1.0% |
| ARRIVAL R3 (Grok) | 1 | 0.5% |
| ARRIVAL R4 (GPT-4.1) | 0 | 0.0% |
| Solo GPT-4.1 | 6 | 3.0% |
| Solo Gemini 3 Flash | 0 | 0.0% |
| Solo Grok 4.1 Fast | 0 | 0.0% |

All rates under 5% threshold. GPT-4.1 has slightly higher extraction failure rate (3-3.5%).

---

## 8. Key Findings

1. **Non-Debate MV (82.3%) > ARRIVAL MV (78.8%)**: Structured debate does NOT improve accuracy when strong models already know the answers. The 3.5pp deficit is not statistically significant (p=0.265) but the direction is clear.

2. **R4 is net negative (again)**: 8 rescues vs 13 regressions (Net: -5). R4 (GPT-4.1) tends to "second-guess" the correct consensus, consistent with Phase 20 findings.

3. **Debate degrades Gemini's accuracy**: Gemini 3 Flash drops from 82.3% (solo) to 78.3% (as R2 in debate), a -4.0pp loss. Exposure to GPT-4.1's weaker proposals causes Gemini to sometimes abandon its own correct answers.

4. **Grok 4.1 is the star**: 85.4% solo, 86.9% in debate (R3). As the last non-finalizer to see all prior responses, Grok benefits slightly from the debate context.

5. **ARRIVAL MV highly significantly outperforms GPT-4.1**: McNemar p=0.000178, debate wins 33 vs losses 8 (Net: +25). The protocol rescues GPT-4.1's weaknesses through stronger partners, but this is simply an ensemble effect, not debate.

6. **Domain pattern**: Non-Debate MV dominates in Physics (93% vs 89.5%) and Chemistry (75.3% vs 71%). Biology is a draw (68.4% each). No domain shows significant debate advantage.

7. **Phase 20 vs Phase 21**: Stronger models improve ARRIVAL by +11pp (MV) and +9.6pp (R4), confirming that base model capability is the primary driver of performance. But the debate effect remains null or slightly negative.

---

## 9. Interpretation

Phase 21 definitively answers the hypothesis from Phase 20: "Are weak models the bottleneck?" YES, weak models were the bottleneck for absolute accuracy, but NO, stronger models do not make debate helpful.

The result suggests a fundamental limitation: **structured debate on MCQ benchmarks adds noise, not signal, when models are strong enough to answer correctly independently.** The 4-round sequential protocol introduces opportunities for:
- **Anchoring**: Strong models (Gemini, Grok) being drawn toward weak model's (GPT-4.1's) incorrect proposals
- **Overthinking**: R4 finalizer changing correct consensus answers
- **Information loss**: Truncation of responses between rounds

ARRIVAL's value proposition for MCQ benchmarks is therefore limited. Its strengths lie in:
- Cooperation tasks (Phase 19: 0% -> 100% survival)
- Transparency and auditability
- CARE-based consensus measurement
- Scenarios where no single model has the answer

---

## 10. Files

| File | Description |
|------|-------------|
| `run_arrival.py` | ARRIVAL experiment runner |
| `run_solo_baselines.py` | Solo baseline runner (3 models) |
| `evaluate.py` | Statistical evaluation |
| `results/arrival_results.json` | ARRIVAL raw results (198 questions) |
| `results/solo_gpt41.json` | GPT-4.1 solo results (198 questions) |
| `results/solo_gemini3flash.json` | Gemini 3 Flash solo results (198 questions) |
| `results/solo_grok41.json` | Grok 4.1 Fast solo results (198 questions) |
| `results/non_debate_mv.json` | Non-debate majority vote (198 questions) |
| `results/evaluation.json` | Statistical evaluation output |
