# Phase 16: Homogeneous 5-Agent Echo-Chamber Test -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-24
**Benchmark**: GPQA Diamond (40 questions)
**Models**: Qwen3-235B x 5 (homogeneous with distinct personas)
**Total Cost**: $1.917 USD (640 API calls)

---

## 1. Motivation

All prior ARRIVAL experiments used **heterogeneous** model ensembles (different architectures). A fundamental criticism of multi-agent debate: does it merely create an echo chamber when agents share the same architecture? Phase 16 tests the worst-case scenario: **5 identical copies** of the same model with only persona differentiation, measuring echo-chamber dynamics with 7 quantitative metrics.

## 2. Experimental Design

### 2.1 Agents

| Agent | Persona | Model |
|-------|---------|-------|
| Alpha | Physicist | Qwen3-235B |
| Beta | Chemist | Qwen3-235B |
| Gamma | Biologist | Qwen3-235B |
| Delta | Mathematician | Qwen3-235B |
| Epsilon | Generalist | Qwen3-235B |

### 2.2 Conditions

| Condition | Description |
|-----------|-------------|
| Solo | Each agent answers independently (5 x 40 = 200 answers) |
| Majority Vote | Simple plurality across 5 agents |
| ARRIVAL | 4-round ARRIVAL protocol with CRDT overlay |

### 2.3 Parameters

- Temperature: 0.7 (higher to encourage diversity)
- Max tokens: 1024
- Thinking mode: OFF
- Budget: $10.00
- Backend: Gonka (primary) / OpenRouter (fallback)

## 3. Results

### 3.1 Overall Accuracy

| Condition | Accuracy |
|-----------|----------|
| Solo (per-agent avg) | 41.5% (83/200) |
| Majority Vote | 52.5% (21/40) |
| **ARRIVAL Protocol** | **65.0% (26/40)** |
| GAIN vs Solo | +23.5 pp |
| GAIN vs MV | **+12.5 pp** |

### 3.2 Per-Agent Solo Accuracy

| Agent | Accuracy |
|-------|----------|
| Alpha (physicist) | 40.0% (16/40) |
| Beta (chemist) | 32.5% (13/40) |
| Gamma (biologist) | 42.5% (17/40) |
| Delta (mathematician) | 42.5% (17/40) |
| Epsilon (generalist) | 50.0% (20/40) |

### 3.3 Per-Domain Breakdown

| Domain | N | Solo Avg | MV | ARRIVAL |
|--------|---|----------|-----|---------|
| Physics | 14 | 42.9% | 57.1% | **71.4%** |
| Chemistry | 14 | 24.3% | 28.6% | **42.9%** |
| Biology | 6 | 56.7% | 66.7% | **83.3%** |
| Interdisciplinary | 6 | 63.3% | 83.3% | **83.3%** |

### 3.4 Echo-Chamber Metrics (7 Metrics)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| R1 Unanimity Rate | 52.9% (18/34) | Moderate -- agents often agree initially |
| Answer Entropy (normalized) | 24.4% | Low diversity -- echo-chamber present |
| R1 -> R2 Flip Rate | 28.4% | Moderate opinion change |
| False Consensus Rate | 12.5% (5/40) | Protocol-induced errors |
| Minority Suppression Rate | 2.9% | Low -- minorities not silenced |
| Confidence Inflation Ratio | 1.05x | Minimal inflation |
| **Diversity Tax** | **-23.8%** | **Negative = ARRIVAL gained from diversity** |

### 3.5 Outcome Analysis (40 Questions)

| Outcome | Count | Description |
|---------|-------|-------------|
| ARRIVAL rescued | 7 | MV wrong -> ARRIVAL correct |
| ARRIVAL created | 4 | All solo wrong -> ARRIVAL correct |
| Both correct | 15 | MV and ARRIVAL both right |
| ARRIVAL regressed | 1 | MV right -> ARRIVAL wrong |
| Minority lost | 2 | Correct minority overridden |
| Both failed | 11 | Neither MV nor ARRIVAL correct |

**Rescue-to-regression ratio: 7:1**

### 3.6 CRDT Health

| Metric | Value |
|--------|-------|
| Avg CARE Resolve | 0.881 |
| Avg Meaning Debt | 1.840 |
| Healthy | 16/40 |
| Strained | 22/40 |
| Unhealthy | 2/40 |

## 4. Key Findings

1. **ARRIVAL provides +12.5 pp over MV even with identical models** -- structured debate forces diverse reasoning paths despite architectural homogeneity
2. **Echo-chamber is present but contained** -- 52.9% R1 unanimity and low entropy confirm homogeneous agents tend to agree, but ARRIVAL still extracts value
3. **Diversity Tax is negative (-23.8%)** -- ARRIVAL gained from the debate process rather than losing to conformity
4. **7:1 rescue-to-regression ratio** -- ARRIVAL saved 7 questions while only losing 1
5. **ARRIVAL created 4 answers from nothing** -- 4 questions where ALL 5 agents were wrong solo, but structured debate produced the correct answer
6. **Persona differentiation has limited effect** -- persona-based accuracy varied (32.5%-50.0%) but less than architecture-based variation in heterogeneous ensembles

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total experiments | 240 (200 solo + 40 ARRIVAL) |
| Total cost | $1.917 |
| API calls | 640 |
| Duration | ~185 minutes |

## 6. Files

- Runner: `experiments/phase16_homogeneous/run_phase16.py`
- Config: `experiments/phase16_homogeneous/config_phase16.py`
- Comparison: `experiments/phase16_homogeneous/compare_with_phase13.py`
- Analytics: `experiments/phase16_homogeneous/per_question_analytics.py`
- Results: `results/phase_16/phase16_results_20260224_235757.json`

## 7. Conclusion

Phase 16 demonstrates that ARRIVAL Protocol provides meaningful accuracy gains (+12.5 pp over MV) even in the worst-case homogeneous scenario with 5 identical model copies. The echo-chamber effect is measurably present (52.9% R1 unanimity, low entropy) but does not prevent the protocol from extracting value through structured debate. The 7:1 rescue-to-regression ratio and 4 "created from nothing" answers demonstrate that structured semantic coordination generates novel reasoning that no individual agent possessed.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
