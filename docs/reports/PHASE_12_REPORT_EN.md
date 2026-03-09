# Phase 12: Bottleneck Communication via Relay Agent -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-22
**Models**: DeepSeek V3, Llama 3.3 70B (Subgroup A); Qwen 2.5 72B, Gemini 2.0 Flash (Subgroup B); Mistral Large (Relay)
**Total Cost**: $0.024 USD (4 experiments)

---

## 1. Motivation

All previous phases used direct all-to-all communication. In real-world deployments, agents may be in separate networks or organizations, communicating through a **relay** that compresses information. Phase 12 tests whether ARRIVAL Protocol's semantic atoms survive lossy compression through a bandwidth-limited intermediary.

## 2. Experimental Design

### 2.1 Topology

```
Subgroup A              Subgroup B
[DeepSeek V3]           [Qwen 2.5 72B]
[Llama 3.3 70B]         [Gemini 2.0 Flash]
       \                   /
        \                 /
     [Mistral Large -- RELAY]
     (max 200 words per relay)
```

### 2.2 Scenarios

| Scenario | Runs |
|----------|------|
| Distributed resource allocation | 2 |
| Cross-team methodology | 2 |

### 2.3 Protocol

- Each subgroup runs a standard ARRIVAL negotiation internally
- The relay agent (Mistral Large) receives the output from each subgroup
- Relay compresses each subgroup's position to **max 200 words**
- Compressed summaries are passed to the other subgroup
- CRDT metrics computed per subgroup and combined

## 3. Results

### 3.1 CARE Metrics

| Scope | Avg CARE | Avg Debt |
|-------|----------|----------|
| Subgroup A | 0.961 | -- |
| Subgroup B | 0.900 | -- |
| **Combined** | **0.867** | **0.222** |

### 3.2 Information Survival

| Metric | Value |
|--------|-------|
| Atom survival rate | **69.5%** |
| Compression ratio | **33.5%** (relay preserved ~1/3 of original) |
| Atoms lost | ~30.5% |

## 4. Key Findings

1. **CARE preserved at 0.867** -- in the "healthy" range despite lossy relay compression
2. **30.5% of semantic atoms lost** through the 200-word relay bottleneck
3. **Subgroup A (0.961) outperformed Subgroup B (0.900)** -- model-dependent CARE quality
4. **First quantitative measurement** of information loss in relay-mediated LLM coordination
5. **Compression ratio of 33.5%** means relay kept roughly 1/3 of original semantic content -- significant loss but sufficient for coordination

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total experiments | 4 |
| Total cost | $0.024 |
| Duration | ~7 minutes |

## 6. Implications

- Real-world deployments with bandwidth constraints or privacy requirements can use relay-mediated ARRIVAL at the cost of ~30% atom loss
- The 200-word limit is quite restrictive -- higher limits would likely improve atom survival
- Relay agent quality matters -- Mistral Large was effective but other models might compress differently
- Future work: adaptive relay that prioritizes high-CARE atoms over low-CARE ones

## 7. Files

- Runner: `experiments/phase12_advanced/phase_12/run_phase12.py`
- Results: `results/phase_12/phase12_results_20260222_010050.json`

## 8. Conclusion

Phase 12 demonstrates that ARRIVAL Protocol can function through a bandwidth-limited relay agent, preserving CARE at 0.867 and retaining 69.5% of semantic atoms through 200-word compression. This is the first quantitative measurement of information loss in relay-mediated multi-agent LLM coordination, establishing that structured semantic atoms are partially robust to lossy compression.

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
