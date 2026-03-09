# Phase 9: N-Agent Scaling (N=5, N=7) -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-22
**Models**: DeepSeek V3, Llama 3.3 70B, Qwen 2.5 72B, Gemini 2.0 Flash, Mistral Large, GPT-4o, DeepSeek R1
**Total Cost**: $1.078 USD (12 experiments)

---

## 1. Motivation

Previous phases used N=3 agents. Phase 9 tests whether ARRIVAL Protocol scales to **larger groups** (N=5, N=7) without degradation of consensus quality or convergence speed. This addresses the theoretical question of whether structured semantic coordination can handle the combinatorial explosion of multi-party negotiation.

## 2. Experimental Design

### 2.1 Groups

| Group | N | Models |
|-------|---|--------|
| Medium | 5 | DeepSeek V3, Llama 3.3 70B, Qwen 2.5 72B, Gemini 2.0 Flash, Mistral Large |
| Large | 7 | All of N=5 + GPT-4o, DeepSeek R1 |

### 2.2 Protocol

- 6-round round-robin (increased from 4 to accommodate more agents)
- Full-history visibility (each agent sees all prior messages)
- 3 hardest MCQ questions: SCI_03, LOG_01, TECH_06
- 2 runs per (question, group_size) = 12 experiments total

## 3. Results

### 3.1 Accuracy and Convergence

| Group | Accuracy | Consensus Rate | Avg Convergence Round |
|-------|----------|----------------|----------------------|
| N=5 | **100%** (6/6) | 100% | 1.17 |
| N=7 | **100%** (6/6) | 100% | 1.50 |

### 3.2 CARE Scaling

| Metric | N=5 | N=7 | Delta |
|--------|-----|-----|-------|
| CARE Resolve | 1.000 | 1.000 | 0.000 |

CARE maintained the theoretical maximum at both group sizes with zero degradation.

### 3.3 Convergence Speed

N=7 converged in 1.5 rounds on average vs 1.17 for N=5 -- a modest increase (0.33 rounds) that is well within the 6-round budget and demonstrates the protocol handles larger groups gracefully.

## 4. Key Findings

1. **Perfect scaling** -- CARE Resolve = 1.000 at both N=5 and N=7, no degradation
2. **Rapid convergence** -- 1.2-1.5 rounds even with 5-7 agents, far below the 6-round budget
3. **100% accuracy maintained** -- all questions answered correctly at both group sizes
4. **Cost scales super-linearly** -- $1.078 total is the most expensive phase so far due to N=7 round-robin (each round requires N API calls)
5. **Theoretical validation** -- confirms Theorem 4 (convergence guarantee) extends to larger N

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total experiments | 12 |
| Total cost | $1.078 |
| Duration | ~82 minutes |
| Cost per experiment | $0.090 |

The higher cost reflects the O(N x R) API call structure of round-robin coordination.

## 6. Limitations

- Same question set as earlier phases (ceiling effect possible)
- Cooperative conditions only (no saboteur at N=5 or N=7)
- Round-robin communication topology (star/tree topologies untested)

## 7. Files

- Runner: `experiments/phase09_scaling/phase_9/run_phase9.py`
- Results: `results/phase_9/phase9_results_20260222_001721.json`

## 8. Conclusion

Phase 9 demonstrates that ARRIVAL Protocol scales cleanly to N=5 and N=7 agents with zero CARE degradation and rapid convergence (1.2-1.5 rounds). The cost increase is expected (O(N x R)) but the semantic coordination quality is fully preserved. Combined with Phase 23's later CGD-7 results (86.9% on GPQA Diamond with 7 models), this validates the protocol's scalability under both cooperative and benchmark conditions.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
