# Phase 7: CRDT Overlay Validation -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-21
**Models**: DeepSeek V3, Llama 3.3 70B, Qwen 2.5 72B
**Total Cost**: $0.018 USD (15 questions, 45 solo + 15 MV + 15 ARRIVAL)

---

## 1. Motivation

Phase 5 demonstrated a ceiling effect on easy MCQs (100% for both MV and ARRIVAL). Phase 7 addresses this by selecting the **15 hardest questions** from the Phase 5 bank (3 per domain) and applying the full ARRIVAL + CRDT overlay to assess whether the mathematical overlay adds value on genuinely difficult items.

## 2. Experimental Design

### 2.1 Dataset

15 hard questions selected from Phase 5 bank, 3 per domain:
- Science: SCI_03, SCI_08, SCI_09
- History: HIS_02, HIS_04, HIS_10
- Logic/Math: LOG_01, LOG_04, LOG_07
- Law/Ethics: LAW_03, LAW_04, LAW_09
- Technology: TECH_06, TECH_07, TECH_08

### 2.2 Conditions

| Condition | Description |
|-----------|-------------|
| Solo | Each agent answers independently (3 x 15 = 45 answers) |
| Majority Vote | Simple plurality across 3 agents |
| ARRIVAL + CRDT | 4-round ARRIVAL protocol with post-hoc CRDT overlay |

### 2.3 Parameters

- Trio: DeepSeek V3, Llama 3.3 70B, Qwen 2.5 72B
- Temperature: 0.3
- 4-round protocol with CRDT overlay

## 3. Results

### 3.1 Overall Accuracy

| Condition | Accuracy |
|-----------|----------|
| Solo (per-agent avg) | 93.3% (42/45) |
| Majority Vote | 100% (15/15) |
| ARRIVAL + CRDT | 100% (15/15) |

### 3.2 CRDT Health Metrics

| Metric | Value |
|--------|-------|
| Avg CARE Resolve | 1.000 (perfect) |
| Avg Meaning Debt | 0.000 |
| Health status | 15/15 healthy |

### 3.3 Atom Usage

| Atom | Count |
|------|-------|
| @C (Concession) | 149 |
| @CONSENSUS | 72 |
| @INT (Integrate) | 70 |
| @SELF | 56 |
| @GOAL | 54 |
| @OTHER | 40 |
| @RESOLUTION | 20 |
| @CONFLICT | 9 |
| **Total** | **470** |
| Unique atoms | 8 |
| Emergent atoms | 0 |

## 4. Key Findings

1. **Second ceiling effect** -- even the "hardest" questions from the Phase 5 bank were too easy for this trio (93.3% solo)
2. **Perfect CARE Resolve (1.0)** confirms the CRDT overlay produces theoretically optimal convergence on high-agreement items
3. **Zero emergent atoms** -- agents used only standard protocol atoms, suggesting the questions didn't require creative semantic negotiation
4. **Concession (@C) dominated** -- 149/470 = 31.7% of all atoms, indicating rapid agreement rather than genuine debate
5. **Motivates GPQA Diamond** -- these results directly motivated Phase 13's switch to graduate-level questions where ceiling effects would not occur

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total cost | $0.018 |
| Duration | ~25 minutes |
| API calls | ~120 |

## 6. Files

- Runner: `experiments/phase07_personas/phase_7/run_phase7.py`
- Questions: `experiments/phase07_personas/phase_7/questions_hard.py`
- Results: `results/phase_7/phase7_results_20260221_180640.json`

## 7. Conclusion

Phase 7 confirms the CRDT overlay produces mathematically optimal convergence (CARE = 1.0, Debt = 0.0) under cooperative conditions on moderately difficult questions. The persistent ceiling effect (100% MV and ARRIVAL) validates the need for genuinely hard benchmarks, directly motivating the transition to GPQA Diamond in Phase 13.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
