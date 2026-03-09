# Phase 6: Byzantine Saboteur Resilience -- Experiment Report

**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Date**: 2026-02-21
**Models**: DeepSeek V3, Llama 3.3 70B, Qwen 2.5 72B (honest); DeepSeek R1 (saboteur)
**Total Cost**: $0.047 USD (16 experiments)

---

## 1. Motivation

Phase 4 demonstrated near-perfect consensus under cooperative conditions. Phase 6 tests the fundamental question: **what happens when one agent actively tries to manipulate the outcome?**

This phase validates Theorem 5.11 (incentive incompatibility) from MEANING-CRDT v1.1, which predicts that strategic manipulation by adversarial agents will break CARE optimality and increase Meaning Debt.

## 2. Experimental Design

### 2.1 Conditions

| Condition | Agents | Saboteur |
|-----------|--------|----------|
| Control | 3 honest agents | None |
| Adversarial | 3 honest + 1 saboteur | Injected at Round 3 |

### 2.2 Saboteur Strategies

Three adversarial strategies were tested:

- **Emergence Flooding**: Saboteur floods the dialogue with fabricated @-atoms to dilute the semantic signal
- **Trojan Atoms**: Saboteur introduces plausible-looking but semantically corrupted atoms designed to be adopted by honest agents
- **Mixed**: Combination of flooding and trojan tactics

### 2.3 Scenarios

- Resource split (60 compute units allocation)
- Methodology debate

### 2.4 Parameters

- 4-round ARRIVAL protocol with CRDT overlay
- Temperature: 0.3
- Saboteur injected at Round 3 (after honest agents establish initial positions)

## 3. Results

### 3.1 Overall CARE Metrics

| Condition | N | Avg CARE | Avg Debt | False Consensus |
|-----------|---|----------|----------|-----------------|
| Control | 4 | 0.911 | 0.103 | 0/4 |
| Emergence Flooding | 4 | 0.939 | 0.117 | 1/4 (25%) |
| **Trojan Atoms** | **4** | **0.818** | **0.179** | **2/4 (50%)** |
| Mixed | 4 | 0.844 | 0.131 | 0/4 |

### 3.2 Key Metrics

- **Trojan atoms degraded CARE by 10.2%** (0.911 -> 0.818)
- **Meaning Debt increased by 73%** under trojan attack (0.103 -> 0.179)
- **50% false consensus rate** with trojan atoms -- the most dangerous strategy
- Emergence flooding was surprisingly well-tolerated (CARE actually increased to 0.939)
- Mixed strategy was less effective than pure trojan (agents detected the flooding component)

### 3.3 Saboteur Atom Adoption

| Strategy | Avg Adopted Atoms |
|----------|-------------------|
| Emergence Flooding | 4.25 |
| Trojan Atoms | 2.50 |
| Mixed | 1.00 |

Trojan atoms had fewer but more impactful adoptions, while flooding produced more adoptions that were less consequential.

## 4. Key Findings

1. **Trojan atoms are the most dangerous strategy** -- they achieve the highest false consensus rate (50%) and the largest CARE degradation
2. **Meaning Debt is an effective manipulation detector** -- 73% increase under attack provides a clear signal
3. **Theorem 5.11 empirically confirmed** -- strategic manipulation breaks CARE optimality as predicted
4. **Emergence flooding is poorly effective** -- honest agents' structured reasoning overwhelms unstructured noise
5. **Late injection (R3) gives honest agents an advantage** -- they establish positions before saboteur enters

## 5. Cost and Efficiency

| Metric | Value |
|--------|-------|
| Total experiments | 16 |
| Total cost | $0.047 |
| Duration | ~32 minutes |
| Cost per experiment | $0.003 |

## 6. Limitations

- Single model as saboteur (DeepSeek R1) -- different architectures may employ different manipulation strategies
- Fixed injection point (Round 3) -- earlier injection could be more damaging
- Small scenario set (2 scenarios x 2 runs per strategy)

## 7. Files

- Runner: `experiments/phase06_byzantine/phase_6/run_phase6.py`
- Results: `results/phase_6/phase6_results_20260221_183942.json`
- Configuration: `src/arrival/config.py` (saboteur strategies)

## 8. Conclusion

Phase 6 demonstrates that ARRIVAL Protocol is not immune to adversarial manipulation -- trojan atoms can degrade CARE by 10.2% and induce false consensus in 50% of cases. However, the Meaning Debt metric provides a reliable detection signal (73% increase), validating MEANING-CRDT Theorem 5.11 and motivating the adaptive defense mechanisms developed in subsequent phases (10, 11, 15).

---

*ARRIVAL Protocol -- Copyright (C) 2026 Mefodiy Kelevra. AGPL-3.0-or-later*
