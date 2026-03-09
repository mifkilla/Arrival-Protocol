# Phase 20: ARRIVAL vs Solo CoT on Full GPQA Diamond (N=198)

**Date:** 2026-03-01
**Status:** Complete

## Executive Summary

Phase 20 scales the ARRIVAL Protocol evaluation from 40 to all **198 GPQA Diamond questions**, providing ~5x the statistical power of Phase 13. ARRIVAL R4 achieves **66.7%** accuracy vs Solo CoT MV at **62.1%** (+4.6 pp), but the difference is **not statistically significant** (McNemar p=0.233). The ARRIVAL R4 finalizer provides **no significant benefit** over simple majority voting of R1-R3 (p=0.803).

---

## 1. Experimental Setup

### 1.1 ARRIVAL Protocol (Condition A)
- **Trio Alpha:** GPT-4.1 (R1/R4) + DeepSeek V3 (R2) + Llama 3.3 70B (R3)
- **Protocol:** 4-round sequential (Propose -> Critique -> Synthesize -> Finalize)
- **Temperature:** 0.3, max_tokens=1024
- **API calls:** 792 (4 per question)

### 1.2 Solo Chain-of-Thought (Condition B)
- **Model:** Qwen3-235B-A22B (`/no_think` mode)
- **Protocol:** 5 independent runs, majority vote
- **Temperature:** 0.7, max_tokens=2048
- **API calls:** 990 (5 per question)

### 1.3 Dataset
- **GPQA Diamond:** 198 expert-level MCQ (Physics: 86, Chemistry: 93, Biology: 19)
- **Answer order:** Randomized per question (seed=42+i)
- **Source:** HuggingFace `Idavidrein/gpqa` (gpqa_diamond split)

---

## 2. Results

### 2.1 Overall Accuracy

| Condition | Correct | Total | Accuracy | 95% CI |
|-----------|---------|-------|----------|--------|
| **ARRIVAL R4** | 132 | 198 | **66.7%** | [59.8%, 72.9%] |
| ARRIVAL MV (R1-R3) | 134 | 198 | 67.7% | [60.9%, 73.8%] |
| **Solo CoT MV** | 123 | 198 | **62.1%** | [55.2%, 68.6%] |
| Solo CoT per-run | 585 | 990 | 59.1% | — |
| Solo CoT oracle | 165 | 198 | 83.3% | — |

### 2.2 Per-Domain Accuracy

| Domain | n | ARRIVAL R4 | ARRIVAL MV | Solo CoT MV |
|--------|---|-----------|-----------|-------------|
| Physics | 86 | 80.2% | **82.6%** | 81.4% |
| Biology | 19 | **78.9%** | 73.7% | 57.9% |
| Chemistry | 93 | **51.6%** | 52.7% | 45.2% |

### 2.3 Individual Model Accuracy (ARRIVAL)

| Model | Role | Accuracy |
|-------|------|----------|
| GPT-4.1 | R1 (Proposer) | 63.6% (126/198) |
| DeepSeek V3 | R2 (Critic) | 66.2% (131/198) |
| Llama 3.3 70B | R3 (Synthesizer) | 57.6% (114/198) |
| GPT-4.1 | R4 (Finalizer) | 66.7% (132/198) |

---

## 3. Statistical Tests

### 3.1 McNemar: ARRIVAL R4 vs MV (R1-R3)

|  | MV correct | MV wrong |
|---|---|---|
| **AR correct** | 125 | 7 (rescues) |
| **AR wrong** | 9 (regressions) | 57 |

- **McNemar chi2 = 0.063, p = 0.803 (ns)**
- R4 finalizer does NOT significantly improve over simple majority vote
- Net effect: -2 (7 rescues - 9 regressions)

### 3.2 McNemar: ARRIVAL R4 vs Solo CoT MV

|  | Solo correct | Solo wrong |
|---|---|---|
| **AR correct** | 105 | 27 (AR wins) |
| **AR wrong** | 18 (Solo wins) | 48 |

- **McNemar chi2 = 1.422, p = 0.233 (ns)**
- ARRIVAL does NOT significantly outperform Solo CoT
- AR wins 27 vs Solo wins 18 (net +9, but ns)

### 3.3 Fisher Exact (backup, unpaired)
- ARRIVAL R4 vs MV: p = 0.915
- ARRIVAL R4 vs Solo: p = 0.401

---

## 4. Protocol Dynamics

### 4.1 Flip Rates
| Transition | Flips | Rate |
|------------|-------|------|
| R1 -> R2 | 18 | 9.1% |
| R2 -> R3 | 25 | 12.6% |
| R3 -> R4 | 21 | 10.6% |

### 4.2 Rescue / Regression Analysis
- **Rescues** (MV wrong -> R4 correct): 7 (10.9% of MV errors)
- **Regressions** (MV correct -> R4 wrong): 9 (6.7% of MV successes)
- **Net: -2** — R4 slightly hurts overall performance

### 4.3 CRDT Metrics
- **Avg CARE Resolve:** 0.955 (high consensus)
- **Avg Meaning Debt:** 0.319

---

## 5. Consistency Check (Phase 13 Subset)

40 questions from Phase 13 were matched to Phase 20 results by question text:

| Condition | Phase 13 (N=40) | Phase 20 subset (N=40) | Delta |
|-----------|----------------|----------------------|-------|
| ARRIVAL | 65.0% (26/40) | **75.0%** (30/40) | +10.0 pp |
| MV | 52.5% (21/40) | **75.0%** (30/40) | +22.5 pp |

The improvement is likely due to **GPT-4.1 replacing GPT-4o** in R1/R4 (Phase 13 used GPT-4o).

---

## 6. Extraction Quality

### Solo CoT Extraction Failures
- **21/198 questions** had at least one run with empty extraction (43/990 total runs = 4.3%)
- Fix applied mid-experiment: MAX_TOKENS raised from 1024 to 2048
- Remaining failures are Qwen3's tendency to end with LaTeX or explanatory text

### ARRIVAL Extraction
- **0/198 questions** with extraction failures in any round

---

## 7. Cost Analysis

| Condition | Total Cost | Per Question | API Calls |
|-----------|-----------|-------------|-----------|
| ARRIVAL | $2.41 | $0.0122 | 792 |
| Solo CoT | $2.36 | $0.0119 | 990 |
| **Total** | **$4.77** | — | 1,782 |

Both conditions cost approximately the same per question (~$0.012).

---

## 8. Interpretation

### What Phase 20 shows:
1. **ARRIVAL provides a modest but non-significant advantage** (+4.6 pp) over Solo CoT on GPQA Diamond at full scale
2. **The R4 finalizer is net negative** — simple majority voting of R1-R3 is better
3. **Chemistry is the hardest domain** for all methods (~45-52%), consistent with GPQA design
4. **DeepSeek V3 is the strongest individual model** in the trio (66.2%), outperforming GPT-4.1 (63.6%)
5. **Llama 3.3 70B is the weakest link** (57.6%) — replacing it could improve ARRIVAL

### Comparison with Phase 13 (N=40):
- Phase 13: ARRIVAL 63.8% vs MV 42.5% (McNemar p=0.006) — **significant**
- Phase 20: ARRIVAL 66.7% vs MV 67.7% (McNemar p=0.803) — **not significant**
- The Phase 13 result likely benefited from small-sample variance and/or GPT-4o being weaker than GPT-4.1

### Comparison with Phase 17 Solo CoT (N=40):
- Phase 17: Solo CoT 70.0% vs ARRIVAL 65.0% (Fisher p=0.812) — **ns**
- Phase 20: Solo CoT 62.1% vs ARRIVAL 66.7% (McNemar p=0.233) — **ns**
- Direction flipped but neither is significant

### Limitations:
- Solo CoT uses a single model (Qwen3-235B) while ARRIVAL uses three heterogeneous models
- Solo CoT extraction failures (4.3% of runs) may slightly deflate Solo results
- GPQA Diamond has known position bias in answer ordering (we randomized to mitigate)
- Biology sample is small (n=19), domain-specific conclusions should be cautious

---

## 9. Conclusion

At full GPQA Diamond scale (N=198), **ARRIVAL Protocol does not significantly outperform Solo Chain-of-Thought** (p=0.233). The protocol provides a small accuracy advantage (+4.6 pp) that does not reach statistical significance. The R4 finalizer step is net negative, suggesting that simple majority voting is sufficient.

**Recommendation for the paper:** Report both the Phase 13 (significant) and Phase 20 (non-significant) results honestly. The honest interpretation is that ARRIVAL shows promise on small samples but the effect does not reliably scale. The protocol's value may lie in domains where model disagreement is informative (like biology: +21 pp over Solo), rather than as a universal accuracy booster.
