# Phase 18: Applied Experiment — Comparison Report

**Date:** 2026-02-26
**Author:** Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)

---

## Overview

Phase 18 compares three conditions on two practical tasks:

| Condition | Description | Models |
|-----------|-------------|--------|
| **A: Solo** | Single frontier model | Claude Sonnet 4.5 ($3/$15 per 1M) |
| **B: ARRIVAL** | 5-model heterogeneous swarm (no memory) | GPT-4.1, DeepSeek V3.2, Mistral Large 3, Gemini 3 Flash, Grok 4.1 Fast |
| **C: ARRIVAL+Mem** | Same swarm + CARE-ALERT gated memory | Same 5 models + pre-seeded ARRIVAL-MNEMO |

**ARRIVAL Protocol:** 4 rounds (R1: independent, R2: cross-critique, R3: CRDT overlay, R4: synthesis). 11 API calls per condition.

---

## Task 1: Security Audit (Analytical)

**Task:** Find 10 intentional bugs in a Flask application (buggy_app.py).

| Metric | A: Solo | B: ARRIVAL | C: ARRIVAL+Mem |
|--------|---------|-----------|----------------|
| **Bugs Found** | **10/10** | **10/10** | **10/10** |
| Bonus Issues | 2/2 | 2/2 | 2/2 |
| Prompt Tokens | 3,947 | ~48K | ~47K |
| Completion Tokens | 7,183 | ~47K | ~47K |
| Total Tokens | 11,130 | 94,534 | 93,674 |
| **Total Cost** | **$0.1196** | **$0.1398** | **$0.1401** |
| API Calls | 1 | 11 | 11 |
| CARE Resolve | N/A | 0.500 | 0.500 |
| Memory Injected | N/A | N/A | Yes (6 memories) |

### Key Findings — Task 1

1. **Ceiling effect:** All three conditions found 100% of bugs plus both bonus issues. The task was not complex enough to differentiate conditions.

2. **Cost parity:** Despite using 5 different models with 11 API calls, ARRIVAL costs only ~17% more than a single Claude Sonnet 4.5 call ($0.14 vs $0.12). This is because the swarm uses lower-cost models.

3. **CARE-ALERT activation:** In Condition C, CARE (0.500) fell below threshold (0.700), triggering memory injection of 6 procedural/semantic/episodic memories. This demonstrates the gating mechanism working as designed.

4. **Transparency advantage:** ARRIVAL provides per-model audit trails — each model's independent findings (R1), critiques (R2), and the synthesis process (R4) are fully logged. Solo provides a single opaque response.

---

## Task 2: Code Generation (Constructive)

**Task:** Implement a complete REST API (FastAPI) from specification. Evaluated by 15 objective pytest tests.

| Metric | A: Solo | B: ARRIVAL | C: ARRIVAL+Mem |
|--------|---------|-----------|----------------|
| **Tests Passed** | **9/15 (60%)** | **8/15 (53%)** | **7/15 (47%)** |
| Code Lines Generated | 259 | 180 | 166 |
| Prompt Tokens | 403 | ~34K | ~32K |
| Completion Tokens | 8,192 | ~34K | ~32K |
| Total Tokens | 8,595 | 67,432 | 64,037 |
| **Total Cost** | **$0.1241** | **$0.1274** | **$0.1228** |
| API Calls | 1 | 11 | 11 |
| CARE Resolve | N/A | 0.979 | 0.973 |
| Memory Injected | N/A | N/A | No (CARE > threshold) |

### Key Findings — Task 2

1. **Solo advantage on code synthesis:** Claude Sonnet 4.5 generated more complete code (259 lines, 9/15 tests) than ARRIVAL's synthesized output (180 lines, 8/15). This is expected: single-model code generation benefits from coherent internal context.

2. **Narrow gap:** The difference is only 1-2 tests (60% vs 53% vs 47%). ARRIVAL's swarm achieves competitive results using cheaper models.

3. **Cost equivalence:** All three conditions cost ~$0.12-0.13. The ARRIVAL swarm with 5 models is not more expensive than a single frontier call.

4. **CARE-ALERT correctly gated:** CARE was high (0.973/0.979) for both ARRIVAL conditions, so memory injection was NOT triggered in Condition C. The system correctly identified that models already agreed and additional knowledge was unnecessary.

5. **High consensus in code tasks:** CARE ~0.97 shows models converge strongly on code generation, unlike security audit (CARE ~0.50) where opinions diverge. This confirms CARE as a meaningful consensus metric.

---

## Combined Analysis

### Cost Efficiency

| Task | A: Solo | B: ARRIVAL | C: ARRIVAL+Mem |
|------|---------|-----------|----------------|
| Task 1 (Audit) | $0.1196 | $0.1398 | $0.1401 |
| Task 2 (Code) | $0.1241 | $0.1274 | $0.1228 |
| **Total** | **$0.2437** | **$0.2672** | **$0.2629** |

**Cost ratio:** ARRIVAL swarm (5 models) costs only 8-10% more than Solo (1 frontier model).

### Performance Summary

| Task Type | Winner | Margin |
|-----------|--------|--------|
| Analytical (audit) | **Tie** (all 10/10) | 0 |
| Constructive (code) | **Solo** | +1-2 tests |

### ARRIVAL Unique Advantages

1. **Transparency:** Every model's contribution is logged and traceable
2. **Robustness:** 5 independent perspectives reduce single-point-of-failure risk
3. **Cost efficiency:** Comparable to frontier solo at fraction of per-model cost
4. **CARE metric:** Quantitative consensus measurement (0.5 = divergent, 0.97 = convergent)
5. **CARE-ALERT:** Gated memory injection only when needed (Task 1: yes, Task 2: no)
6. **Architecture agnostic:** Uses GPT, DeepSeek, Mistral, Gemini, Grok simultaneously

---

## Limitations

1. Task 1 exhibited ceiling effect — harder audit tasks needed for differentiation
2. Code generation favors single-context models (architectural limitation of swarm synthesis)
3. CRDT metrics used default values due to format mismatch (non-MCQ task type)
4. N=1 per condition (no repeated trials) — results are indicative, not statistically definitive
5. Memory seeds were synthetic (pre-seeded), not accumulated from real prior sessions

---

## Files

| File | Description |
|------|-------------|
| `task1_security_audit/results/solo_result.json` | Full Solo audit response |
| `task1_security_audit/results/arrival_result.json` | Full ARRIVAL audit (all rounds) |
| `task1_security_audit/results/arrival_memory_result.json` | Full ARRIVAL+Memory audit |
| `task1_security_audit/results/evaluation.json` | Task 1 automated evaluation |
| `task2_code_generation/results/solo_result.json` | Full Solo code generation |
| `task2_code_generation/results/arrival_result.json` | Full ARRIVAL code (all rounds) |
| `task2_code_generation/results/arrival_memory_result.json` | Full ARRIVAL+Memory code |
| `task2_code_generation/results/evaluation.json` | Task 2 automated evaluation |
