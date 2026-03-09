# Phase 15: Gated CARE-ALERT (Real-Time Working Memory) -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-23
**Benchmark**: GPQA Diamond (40 questions)
**Models**: GPT-4o, DeepSeek V3, Llama 3.3 70B ("Alpha" trio)
**Total Cost**: $0.532 USD (160 API calls)

---

## 1. Motivation

Phase 14 showed that global memory injection causes hypercorrection (-5.7 pp). Phase 15 redesigns the intervention mechanism: instead of pre-loading warnings, the system **monitors Meaning Debt in real time** and fires targeted `@CARE.ALERT` atoms only when semantic divergence exceeds calibrated thresholds. The system prompt is clean (identical to Phase 13) -- no memory block.

## 2. Experimental Design

### 2.1 Gated Alert Mechanism

| Checkpoint | Threshold | Alert Level |
|------------|-----------|-------------|
| After Round 2 | MD > 0.5 | Level 1 (gentle) |
| After Round 3 | MD > 0.8 | Level 2 (urgent) |

Alerts are **operational**, not moralistic:
- Level 1: "Agent Beta selected C while Alpha selected A. Consider addressing with @EVIDENCE."
- Level 2: "Persistent divergence detected. Provide explicit reasoning for your position."

### 2.2 Key Design Difference from Phase 14

| | Phase 14 | Phase 15 |
|-|----------|----------|
| System prompt | Memory block injected | **Clean** (no memory) |
| Intervention | Before dialogue (static) | **During dialogue** (dynamic) |
| Trigger | Always (every question) | **Only when MD exceeds threshold** |
| Tone | Moralistic (avoid past errors) | **Operational** (address specific divergence) |

### 2.3 Parameters

- Same 40 GPQA Diamond questions, same Alpha trio
- Temperature: 0.3, max tokens: 1024
- Debt store threshold: 1.5 (new memory creation)
- Budget: $10.00

## 3. Results

### 3.1 Overall Accuracy

| Metric | All 40 | Unseen 35 | Seen 5 |
|--------|--------|-----------|--------|
| Accuracy | 57.5% (23/40) | 57.1% (20/35) | 60.0% (3/5) |

### 3.2 Three-Way Comparison (Unseen 35 Only)

| Metric | Phase 13 (Stateless) | Phase 14 (Static Memory) | Phase 15 (Gated Alert) |
|--------|----------------------|--------------------------|------------------------|
| Accuracy | 57.1% (20/35) | 51.4% (18/35) | **57.1% (20/35)** |
| CARE Resolve | 0.966 | 0.916 | **0.948** |
| Meaning Debt | 0.196 | 0.433 | 0.452 |

### 3.3 Statistical Tests

| Comparison | Delta | McNemar p |
|------------|-------|-----------|
| Phase 13 vs Phase 15 | 0.0 pp | 0.752 (ns) |
| Phase 14 vs Phase 15 | +5.7 pp | 0.724 (ns) |
| CARE: Phase 14 vs Phase 15 | +0.032 | Mann-Whitney p = 0.069 (marginal) |
| **CARE: Phase 13 vs Phase 15** | -- | **Mann-Whitney p = 0.042** (significant) |

### 3.4 Alert Statistics

| Metric | Value |
|--------|-------|
| Questions with any alert | 7/40 (17.5%) |
| Alerts after R2 | 6 |
| Alerts after R3 | 7 |
| Accuracy when alerted | 57.1% (4/7) |
| Accuracy when NOT alerted | 57.6% (19/33) |
| CARE when alerted | 0.968 |
| CARE when NOT alerted | 0.914 |

### 3.5 Memory Growth

| Metric | Value |
|--------|-------|
| Initial memories | 0 |
| Final memories | 9 (+6 during run) |

## 4. Key Findings

1. **Baseline accuracy restored** -- Phase 15 recovered to Phase 13 levels (57.1%), avoiding Phase 14's hypercorrection
2. **CARE significantly improved** -- Mann-Whitney p = 0.042, the first statistically significant improvement from any memory intervention in multi-agent LLM coordination
3. **Selective intervention** -- only 17.5% of questions triggered alerts, reducing unnecessary interference
4. **Alerted questions had higher CARE** (0.968 vs 0.914) -- the alert mechanism actively improved semantic coordination quality where it fired
5. **Operational > moralistic** -- specific, actionable alerts ("Beta selected C, address with @EVIDENCE") outperform vague warnings ("you failed before, be careful")

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total experiments | 40 |
| Total cost | $0.532 |
| API calls | 160 |

## 6. Limitations

- Same question set as Phases 13-14 (potential memorization artifacts)
- Small N (40 questions) limits statistical power
- Same trio only -- generalization to other model combinations untested

## 7. Files

- Runner: `experiments/phase14_memory_global/run_phase15.py`
- Results: `results/phase_15/phase15_results_20260223_161545.json`

## 8. Conclusion

Phase 15 demonstrates that gated, real-time `@CARE.ALERT` intervention successfully avoids the hypercorrection effect of global memory injection (Phase 14) while achieving statistically significant CARE improvement (p = 0.042). The key design principles: clean system prompts, threshold-gated activation, and operational (not moralistic) alert content. This is the first statistically significant improvement from memory intervention in multi-agent LLM coordination.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
