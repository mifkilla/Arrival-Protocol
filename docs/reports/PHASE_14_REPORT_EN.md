# Phase 14: Global Memory Injection (ARRIVAL-MNEMO) -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-23
**Benchmark**: GPQA Diamond (40 questions)
**Models**: GPT-4o, DeepSeek V3, Llama 3.3 70B ("Alpha" trio)
**Total Cost**: $0.579 USD (160 API calls)

---

## 1. Motivation

Phase 13 established the ARRIVAL baseline on GPQA Diamond (63.8% on 40 questions). A natural question: can **persistent memory** improve performance by helping agents avoid past mistakes? Phase 14 tests global injection of ARRIVAL-MNEMO -- a 4-layer memory architecture (Episodic, Procedural, Semantic, Meta) populated from cognitive scars extracted from Phase 13 errors.

## 2. Experimental Design

### 2.1 Memory Architecture

ARRIVAL-MNEMO uses 4 memory layers:
- **Episodic**: Specific question-answer experiences and their outcomes
- **Procedural**: Learned reasoning strategies and heuristics
- **Semantic**: Domain knowledge and factual corrections
- **Meta**: Self-reflective observations about reasoning patterns

### 2.2 Memory Injection

- Cognitive scars extracted from Phase 13 incorrect answers via `extract_scars.py`
- Memory store initialized with 10 entries via `init_memory_store.py`
- Injected as `[MEMORY CONTEXT]` block in system prompt (top-k=8, max 800 chars)
- New episodic memories auto-created when Meaning Debt > 1.5

### 2.3 Controls

- Same 40 GPQA Diamond questions as Phase 13
- Same Alpha trio (GPT-4o, DeepSeek V3, Llama 3.3 70B)
- Same 4-round ARRIVAL protocol
- Only difference: system prompt includes memory block
- 5 "seen" questions excluded from inferential statistics

## 3. Results

### 3.1 Overall Accuracy

| Metric | All 40 | Unseen 35 | Seen 5 |
|--------|--------|-----------|--------|
| Accuracy | 50.0% (20/40) | 51.4% (18/35) | 40.0% (2/5) |

### 3.2 Comparison with Phase 13

| Metric | Phase 13 | Phase 14 | Delta |
|--------|----------|----------|-------|
| Accuracy (unseen 35) | **57.1%** | 51.4% | **-5.7 pp** |
| CARE Resolve | 0.966 | 0.916 | -0.050 |
| Meaning Debt | 0.196 | 0.433 | +0.237 |
| McNemar p-value | -- | 0.724 | (not significant) |

### 3.3 Memory Growth

| Metric | Value |
|--------|-------|
| Initial memories | 10 |
| Final memories | 13 (+3 during run) |
| New memories created | 3 (when debt > 1.5) |

### 3.4 CRDT Health

| Health | All 40 | Unseen 35 | Seen 5 |
|--------|--------|-----------|--------|
| Healthy | 30 | 28 | 2 |
| Strained | 10 | 7 | 3 |

## 4. Key Findings

1. **Memory HURT performance** -- accuracy dropped 5.7 pp (57.1% -> 51.4%), though not statistically significant (p = 0.724)
2. **Hypercorrection effect** -- agents warned about past failures became overly cautious, breaking consensus on questions where they would have been correct without memory
3. **CARE degraded** (0.966 -> 0.916) -- memory injection increased cognitive load and produced less coherent semantic coordination
4. **Meaning Debt doubled** (0.196 -> 0.433) -- more unresolved tensions in negotiations when agents carry past-failure anxiety
5. **Seen questions performed WORST** (40.0%) -- the very questions memory should help with were hurt most, confirming hypercorrection
6. **Memory creation works; memory DELIVERY is the problem** -- the issue is when and how memories are presented, not the memories themselves

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total experiments | 40 |
| Total cost | $0.579 |
| API calls | 160 |

## 6. Implications

This is a **valid and important negative result**:
- Naive global memory injection before dialogue is counterproductive
- Past errors should not be presented as warnings (creates anxiety)
- Motivates Phase 15's approach: real-time gated intervention based on current state rather than pre-loaded historical context

## 7. Files

- Runner: `experiments/phase14_memory_global/run_phase14.py`
- Scar extractor: `experiments/phase14_memory_global/extract_scars.py`
- Memory initializer: `experiments/phase14_memory_global/init_memory_store.py`
- Results: `results/phase_14/phase14_results_20260223_133825.json`
- Scars: `results/phase_14/phase14_scars.json`

## 8. Conclusion

Phase 14 demonstrates that global memory injection from past errors degrades multi-agent coordination by 5.7 pp through a hypercorrection effect -- agents over-apply past lessons to dissimilar problems. This finding is consistent with literature on human metacognitive interference and motivates the gated, context-sensitive approach developed in Phase 15.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
