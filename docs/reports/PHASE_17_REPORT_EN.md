# Phase 17: Solo Chain-of-Thought Baseline -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-26
**Benchmark**: GPQA Diamond (40 questions)
**Models**: Qwen3-235B (single instance, 5 independent runs)
**Total Cost**: ~$6.00 USD (2,400 API calls across 12 independent runs)

---

## 1. Motivation

Wang et al. (ACL 2024) argued that strong single-agent prompting can match multi-agent debate performance. Phase 17 directly tests this critique by running a **single Qwen3-235B** with enhanced chain-of-thought prompting on the same 40 GPQA Diamond questions used in Phase 16, with 5 independent runs to match Phase 16's 5-agent setup.

## 2. Experimental Design

### 2.1 Protocol

- Single Qwen3-235B instance (same model as Phase 16's 5 agents)
- Enhanced CoT system prompt with world-class scientist persona
- 5 independent runs per question (matching Phase 16's 5 agents)
- Majority Vote across 5 runs
- Oracle (best-of-5) computed as upper bound
- 12 total independent experiments for robustness

### 2.2 CoT System Prompt

```
You are a world-class scientist with deep expertise across physics,
chemistry, biology, and mathematics. You are answering a graduate-level
multiple-choice question from the GPQA Diamond benchmark.

IMPORTANT INSTRUCTIONS:
1. Read the question and all answer choices carefully.
2. Think step by step through the problem. Show your complete reasoning chain.
3. Consider each answer choice systematically.
4. If you are uncertain, reason through by elimination.
5. After your full analysis, state your final answer clearly.

End your response with exactly: "The answer is X" where X is A, B, C, or D.
```

### 2.3 Parameters

- Temperature: 0.7 (same as Phase 16)
- Max tokens: 1024
- Budget: $2.00 per run
- Phase 16 baselines: Solo=41.5%, MV=52.5%, ARRIVAL=65.0%

## 3. Results

### 3.1 Aggregate Across 12 Independent Runs

| Metric | Range | Mean |
|--------|-------|------|
| Solo per-run accuracy | 59.5% -- 68.0% | ~62.1% |
| MV (5-run) accuracy | 67.5% -- 77.5% | **~71.4%** |
| Oracle (best-of-5) | 82.5% -- 92.5% | ~87.1% |
| Cost per run | $0.49 -- $0.52 | ~$0.50 |

### 3.2 Comparison with Phase 16

| Condition | Accuracy | Source |
|-----------|----------|--------|
| Phase 16 Solo (per-agent) | 41.5% | 5 agents x 40q |
| Phase 16 MV | 52.5% | 5 agents |
| Phase 16 ARRIVAL | 65.0% | 5 agents |
| **Phase 17 Solo CoT (per-run)** | **~62.1%** | Single agent |
| **Phase 17 Solo CoT MV** | **~71.4%** | Single agent x 5 |
| Phase 17 Oracle | ~87.1% | Best-of-5 |

### 3.3 Statistical Tests (Representative Run)

| Comparison | Delta | p-value | Significant? |
|------------|-------|---------|-------------|
| CoT MV vs ARRIVAL (P16) | +5.0 pp | 0.812 (Fisher) | No |
| CoT MV vs P16 MV | +17.5 pp | 0.168 (Fisher) | No |
| Best run vs ARRIVAL | +12.5 pp | 0.320 (Fisher) | No |

### 3.4 Per-Domain Breakdown (Representative Run)

| Domain | N | CoT MV Accuracy |
|--------|---|-----------------|
| Physics | 14 | 85.7% (12/14) |
| Chemistry | 14 | 42.9% (6/14) |
| Biology | 6 | 66.7% (4/6) |
| Interdisciplinary | 6 | 100.0% (6/6) |

## 4. Key Findings

1. **Solo CoT MV (71.4%) exceeds ARRIVAL (65.0%) by 6.4 pp** -- but difference is NOT statistically significant (p = 0.812)
2. **Enhanced CoT dramatically improves solo performance** -- per-run accuracy jumped from 41.5% (Phase 16 solo) to 62.1% (+20.6 pp) just from better prompting
3. **Wang et al. critique partially validated** -- a single agent with strong prompting can match or exceed multi-agent debate on accuracy alone
4. **But multi-agent debate provides additional value beyond accuracy**: audit trails, CARE-based consensus measurement, diverse reasoning paths, and detection of unreliable answers via echo-chamber metrics
5. **High variance across runs** (67.5%-77.5% MV) -- multi-agent ensembles may provide more stable performance
6. **Chemistry remains the hardest domain** (42.9%) consistently across solo and ensemble conditions

## 5. Cost and Efficiency

| Metric | Per run | Total (12 runs) |
|--------|---------|-----------------|
| API calls | 200 | 2,400 |
| Cost | ~$0.50 | ~$6.00 |

## 6. Implications

- **Prompt engineering is a confound** -- Phase 16's solo condition used a weaker prompt than Phase 17's enhanced CoT, making the comparison partially unfair
- **Cost advantage of solo**: $0.50 for CoT MV vs $1.92 for 5-agent ARRIVAL (3.8x cheaper)
- **Multi-agent value proposition** shifts from raw accuracy to: interpretability (CARE scores), reliability (echo-chamber metrics), and safety (adversarial detection via Meaning Debt)

## 7. Files

- Runner: `experiments/phase17_solo_cot/run_phase17.py`
- Config: `experiments/phase17_solo_cot/config_phase17.py`
- Results: `experiments/phase17_solo_cot/results/` (12 JSON files)

## 8. Conclusion

Phase 17 validates the Wang et al. critique: a single Qwen3-235B with enhanced CoT prompting achieves ~71.4% MV accuracy, exceeding Phase 16 ARRIVAL's 65.0% (though not significantly, p = 0.812). However, this comparison is confounded by prompt strength differences, and multi-agent ARRIVAL provides value beyond accuracy through structured audit trails, consensus quality metrics, and adversarial detection capabilities that single-agent CoT cannot offer.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
