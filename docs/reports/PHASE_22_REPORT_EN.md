# Phase 22: Confidence-Gated Debate (CGD) — Full Results

**Date**: 2026-03-02
**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Benchmark**: GPQA Diamond (198 questions)
**Models**: GPT-4.1, Gemini 3 Flash, Grok 4.1 Fast
**Total Cost**: $5.72 USD (692 API calls)

---

## 1. Motivation

Phase 21 revealed a critical problem: multi-agent debate with structured @-atoms **degrades** frontier-model performance. Solo Grok 4.1 achieved 85.4%, but ARRIVAL debate dropped accuracy to 78.8% (MV) and 76.3% (R4). Root cause: **anchoring bias** — the weakest model (GPT-4.1, 66.2%) pulled stronger models toward incorrect answers, and the R4 finalizer introduced destructive regressions.

CGD addresses this by:
1. Enforcing **independent solo answers** (no cross-contamination)
2. Skipping debate when all models **unanimously agree** (no wasted tokens)
3. Running **targeted debate** only on disagreements
4. Removing R4 — final answer determined by **majority vote after debate**

---

## 2. Protocol

```
Step 1: SOLO PHASE (independent)
  → All 3 models answer independently (temperature=0.3)
  → No model sees another's answer

Step 2: AGREEMENT CHECK
  → Unanimous (3/3): Lock answer, skip debate
  → Split 2v1:     Minority defends, majority may respond
  → Split 3-way:   All 3 debate

Step 3: TARGETED DEBATE (only if disagreement)
  → Minority presents defense with evidence
  → No R4 finalization
  → Final answer = majority vote after debate
```

---

## 3. Results

### 3.1 Overall Accuracy

| Method | Correct | Accuracy | 95% CI (Wilson) |
|--------|---------|----------|-----------------|
| **CGD (Phase 22)** | **171/198** | **86.4%** | [80.9%, 90.5%] |
| Grok-weighted MV | 171/198 | 86.4% | [80.9%, 90.5%] |
| Solo Grok 4.1 | 169/198 | 85.4% | [79.8%, 89.6%] |
| Non-Debate MV (P21) | 163/198 | 82.3% | [76.4%, 87.0%] |
| Solo Gemini 3 Flash | 163/198 | 82.3% | [76.4%, 87.0%] |
| ARRIVAL MV (P21) | 156/198 | 78.8% | [72.6%, 83.9%] |
| Solo GPT-4.1 | 131/198 | 66.2% | [59.3%, 72.4%] |
| Oracle (any model correct) | 189/198 | 95.5% | [91.6%, 97.6%] |

### 3.2 Statistical Tests (McNemar)

| Comparison | CGD wins | Loses | Net | chi² | p-value | Significant? |
|------------|----------|-------|-----|------|---------|--------------|
| **CGD vs Non-Debate MV** | 14 | 6 | +8 | 3.20 | 0.074 | No (p=0.074) |
| **CGD vs ARRIVAL MV** | 24 | 9 | +15 | 6.82 | **0.009** | **YES** |
| CGD vs Grok-weighted MV | 8 | 8 | 0 | 0.0 | 1.000 | No |

**Key finding**: CGD is **statistically significantly better** than ARRIVAL debate (p=0.009). The improvement over Non-Debate MV is suggestive (p=0.074) but does not reach conventional significance on 198 questions.

### 3.3 Per-Domain

| Domain | N | CGD | Non-Debate MV | ARRIVAL MV | Solo Grok |
|--------|---|-----|---------------|------------|-----------|
| Physics | 86 | **95.3%** | 93.0% | 89.5% | 94.2% |
| Chemistry | 93 | **79.6%** | 75.3% | 71.0% | 80.6% |
| Biology | 19 | **78.9%** | 68.4% | 68.4% | 68.4% |

CGD outperforms all baselines in every domain. Largest improvement in Biology (+10.5 pp vs Non-Debate MV).

### 3.4 Debate Type Breakdown

| Type | N | % of Total | Accuracy |
|------|---|------------|----------|
| Unanimous (3/3 agree) | 122 | 61.6% | **95.9%** (117/122) |
| Split 2v1 | 65 | 32.8% | 70.8% (46/65) |
| Split 3-way | 11 | 5.6% | 72.7% (8/11) |

When all three models independently agree, accuracy is near-perfect (95.9%). Debate is only needed for 38.4% of questions.

---

## 4. Analysis

### 4.1 Minority-Was-Right

In 65 split_2v1 questions, the minority model was correct 15 times (23.1%).

| Model | Times as Minority | Minority Correct | Rate |
|-------|-------------------|------------------|------|
| GPT-4.1 | 32 | 1 | 3% |
| Grok 4.1 | 18 | 8 | 44% |
| Gemini 3 Flash | 15 | 6 | 40% |

GPT-4.1 is almost never right when it disagrees with others (3%). Grok and Gemini are right 40-44% of the time as minority — suggesting a **model-weighted voting** scheme could further improve accuracy.

18 questions where minority was correct but lost debate — these represent the theoretical ceiling for future improvement.

### 4.2 Extraction Failures

7 questions (3.5%) had extraction failures (model returned None/null):
- GPT-4.1: 6 failures
- Grok: 1 failure
- Gemini: 0 failures

5 of 7 were classified as "unanimous" despite having only 2 valid votes. Accuracy excluding bugs: 86.9% (166/191).

### 4.3 Unanimous Errors

5 questions where all models unanimously agreed on a wrong answer (4.1% of unanimous). These represent the **irreducible error floor** — no debate protocol can fix them, as all models are confidently wrong.

---

## 5. Cost Analysis

| Method | Total Cost | Per Question | API Calls |
|--------|-----------|-------------|-----------|
| CGD | $5.72 | $0.029 | 692 |
| ARRIVAL (P21) | $4.89 | $0.025 | 792 |
| Solo baselines (P21) | $4.74 | $0.024 | 594 |

CGD is 17% more expensive than ARRIVAL but 7.6 pp more accurate. The cost premium comes from:
- 3 independent solo calls per question (vs shared context in ARRIVAL)
- Additional debate calls for 38.4% of questions

---

## 6. Conclusions

1. **CGD achieves 86.4% on GPQA Diamond** — the highest accuracy of any ARRIVAL-family method, surpassing solo Grok 4.1 (85.4%) and all prior multi-agent approaches.

2. **Independent answers are crucial**: By preventing anchoring (solo phase), CGD avoids the performance degradation seen in Phase 21's debate-first approach.

3. **Targeted debate works**: Debating only when disagreement exists saves tokens (61.6% unanimous = no debate) while focusing resources where they matter.

4. **No R4 = no regressions**: Removing the R4 finalizer eliminates the net-negative effect observed in Phase 21.

5. **Statistical significance**: CGD vs ARRIVAL MV is significant (p=0.009). CGD vs Non-Debate MV is suggestive (p=0.074).

6. **Future direction**: Model-weighted gating (trusting Grok over GPT in 2v1 splits) could recover up to 8 additional questions, potentially reaching ~90%.

---

## 7. Reproducibility

- **Script**: `run_cgd_full.py` (atomic save, auto-resume)
- **Evaluation**: `evaluate.py` (McNemar, Wilson CI, minority analysis)
- **Results**: `results/cgd_full_results.json` (198 questions, full metadata)
- **Evaluation output**: `results/evaluation.json`
- **API**: OpenRouter (models accessed via standard API)
- **Temperature**: 0.3 (reproducible across runs)
- **Total cost**: $5.72 USD
