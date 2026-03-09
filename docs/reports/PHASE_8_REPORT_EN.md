# Phase 8: Multi-Step Chained Negotiation -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-21
**Models**: DeepSeek V3, Llama 3.3 70B, Qwen 2.5 72B
**Total Cost**: $0.008 USD (9 dialogues across 3 scenarios)

---

## 1. Motivation

Phases 4-7 tested single-shot negotiations. Real-world coordination requires **sequential multi-step reasoning** where context from step N-1 informs step N. Phase 8 tests whether ARRIVAL Protocol can maintain semantic coherence across chained negotiation sequences where decisions compound.

## 2. Experimental Design

### 2.1 Scenarios

Three chained scenarios, each consisting of 3 sequential steps:

| Scenario | Step 1 | Step 2 | Step 3 |
|----------|--------|--------|--------|
| Budget Allocation | Set priorities | Allocate resources | Resolve conflicts |
| Research Pipeline | Define hypothesis | Design methodology | Plan execution |
| Crisis Response | Assess situation | Develop strategy | Coordinate actions |

### 2.2 Protocol

- 4-round ARRIVAL protocol per step
- Context from step N-1 is carried forward to step N via a context summary
- CRDT metrics computed per step and per chain
- 2 runs per scenario

### 2.3 Parameters

- Trio: DeepSeek V3, Llama 3.3 70B, Qwen 2.5 72B
- Temperature: 0.3

## 3. Results

### 3.1 Chain-Level Metrics

| Metric | Value |
|--------|-------|
| Mean chain CARE Resolve | **0.870** |
| Mean chain Meaning Debt | 0.391 |
| Context retention rate | **100%** |

### 3.2 Per-Step Analysis

CARE Resolve remained stable across sequential steps, indicating that the protocol does not degrade as context accumulates. 100% context retention means all relevant decisions from earlier steps were correctly referenced in later steps.

## 4. Key Findings

1. **CARE = 0.870 across chains** -- lower than single-shot (typically 0.91-1.0) but still in the "healthy" range, reflecting the added complexity of compounding decisions
2. **100% context retention** -- agents successfully carried forward decisions across all 3 steps in all scenarios
3. **Meaning Debt increases with chain length** (0.391 vs ~0.1 in single-shot) -- expected as more semantic dimensions accumulate unresolved tensions
4. **Protocol scales to sequential tasks** -- no catastrophic failure or context loss observed

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total experiments | 9 dialogues (3 scenarios x 3 steps) |
| Total cost | $0.008 |
| Duration | ~11 minutes |

## 6. Files

- Runner: `experiments/phase08_crossarch/phase_8/run_phase8.py`
- Results: `results/phase_8/phase8_results_20260221_225548.json`

## 7. Conclusion

Phase 8 demonstrates that ARRIVAL Protocol maintains semantic coherence across multi-step chained negotiations with 100% context retention and healthy CARE metrics (0.870). The increase in Meaning Debt relative to single-shot experiments reflects the inherent complexity of compounding decisions rather than protocol failure.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
