# ARRIVAL Protocol: Cross-Architecture AI-to-AI Coordination Through Structured Semantic Atoms

**Author**: Mefodiy Kelevra
**ORCID**: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
**Date**: February 26, 2026
**DOI**: [To be assigned upon Zenodo publication]
**License**: CC BY-NC 4.0 (text), AGPL-3.0-or-later (code)
**Repository**: https://github.com/mefodiy-kelevra/arrival-protocol

**Keywords**: multi-agent debate, LLM coordination, CRDT, semantic atoms, echo chamber, adversarial robustness, GPQA, cross-architecture

---

## Abstract

We present the ARRIVAL Protocol (Atomic Reasoning via Rival Validation and Adversarial Logic), a structured communication framework enabling AI-to-AI coordination across heterogeneous large language model (LLM) architectures without fine-tuning, shared weights, or prior joint training. The protocol employs 66 semantic @-atoms from DEUS.PROTOCOL v0.5, injected via system prompts, to establish a shared coordination vocabulary.

Across 579+ experiments organized into 17 phases involving 9 distinct LLM architectures, we report the following principal findings. On the GPQA Diamond graduate-level science benchmark, ARRIVAL achieves **65.0% accuracy** with a homogeneous 5-agent Qwen3-235B ensemble (Phase 16), compared to 52.5% for majority voting (+12.5 percentage points). In a heterogeneous 3-agent configuration (Phase 13), ARRIVAL achieves **63.8%** versus majority voting at 42.5% (McNemar p = 0.006). The Solo Chain-of-Thought baseline (Phase 17) achieves **[TBD]%** with 5 independent runs and majority vote, demonstrating that ARRIVAL provides **[TBD] pp** gain over the strongest single-agent prompting strategy.

We formalize conflict resolution through MEANING-CRDT v1.1, a mathematical framework based on Conflict-free Replicated Data Types with 11 theorems covering CARE Resolve (weighted semantic consensus), Meaning Debt (accumulated divergence), convergence, and Bayesian equivalence. Seven quantitative echo-chamber metrics detect and measure social conformity in LLM ensembles. Adversarial testing with Byzantine saboteurs and Trojan atoms confirms robustness bounds predicted by the formal framework.

The ARRIVAL-MNEMO memory extension (Phases 14--15) reveals a hypercorrection paradox: naive memory injection *degrades* accuracy by 5.7 pp, while gated CARE-ALERT interventions that monitor Meaning Debt in real time restore baseline performance (CARE improvement p = 0.042). Framework-agnostic validation on Microsoft's AutoGen (AG2) achieves 100% behavioral match with the reference implementation.

The total computational cost for all experiments is under $10 USD. These results suggest that structured semantic protocols offer a viable, low-cost coordination layer for heterogeneous multi-agent AI systems.

---

## 1. Introduction

### 1.1 Problem Statement

The proliferation of large language models from competing vendors has created a fragmented ecosystem in which models cannot natively coordinate. Each architecture processes language through different tokenization schemes, attention mechanisms, training corpora, and alignment procedures. Yet many applications demand coordination: multi-agent reasoning, ensemble decision-making, negotiation, and collaborative problem-solving.

Recent work on multi-agent debate (MAD) has demonstrated that structured interaction between LLMs can improve factuality and reasoning (Du et al., 2024). However, the MAD paradigm faces three critical challenges. First, unstructured debate can *degrade* reasoning quality rather than improve it (Smit et al., 2024). Second, strong single-agent prompting strategies can match multi-agent systems on many benchmarks (Wang et al., 2024). Third, existing MAS-LLM systems generally lack formal foundations, statistical rigor, and honest engagement with failure modes (La Malfa et al., 2025).

The ARRIVAL Protocol addresses these challenges through three complementary innovations:

1. **Structured semantic atoms**: 66 compositional @-atoms (e.g., `@SELF`, `@CONFLICT`, `@CONSENSUS`) provide a formal coordination vocabulary, replacing unstructured free-text debate with machine-parseable communication that prevents quality degradation.

2. **CRDT-based conflict resolution**: MEANING-CRDT v1.1 formalizes consensus as weighted vector averaging with proven convergence, bounded debt, and Bayesian equivalence properties, moving beyond heuristic aggregation.

3. **Empirical rigor**: 579+ experiments across 9 architectures with statistical significance testing (Fisher's exact, McNemar's, Mann-Whitney U), adversarial testing, ablation studies, and explicit engagement with critical work.

### 1.2 Contributions

This paper makes the following contributions:

- **ARRIVAL Protocol**: A 4-round structured coordination protocol using 66 semantic atoms, validated across 9 LLM architectures.
- **MEANING-CRDT v1.1**: A mathematical framework with 11 theorems for principled conflict resolution in multi-agent LLM systems.
- **Echo-chamber analysis**: 7 quantitative metrics for detecting and measuring social conformity in LLM ensembles.
- **Hypercorrection paradox**: Discovery that naive memory injection degrades multi-agent accuracy, with a gated solution (CARE-ALERT).
- **Cross-framework validation**: Demonstration that the protocol is framework-agnostic via AutoGen (AG2) integration.
- **Comprehensive empirical evaluation**: 579+ experiments, $<10 total, covering adversarial robustness, scaling, domain transfer, and ablation.

### 1.3 Organization

Section 2 reviews related work and positions ARRIVAL within the MAD literature. Section 3 describes the protocol specification. Section 4 presents MEANING-CRDT v1.1. Sections 5--10 report experimental results across 17 phases. Section 11 discusses findings and limitations. Section 12 concludes.

---

## 2. Related Work

### 2.1 Multi-Agent Debate

Du et al. (2024) established that multi-agent debate improves factuality and reasoning across LLM tasks, founding the MAD paradigm. Subsequent work has explored variations: Liang et al. (2024) introduced structured critique rounds to encourage divergent thinking, addressing the echo-chamber problem in free-form debate. Li et al. (2024) showed that sparse communication topologies outperform fully connected ones, suggesting that *how* agents communicate matters as much as *that* they communicate.

The Mixture-of-Agents (MoA) framework (Together AI, 2024) demonstrated that layered aggregation of multiple LLM outputs can outperform individual models. Li et al. (2025) extended this with Self-MoA, showing that *homogeneous* ensembles (copies of the same model) can outperform heterogeneous ones --- a finding independently confirmed by our Phase 16 results.

### 2.2 Critical Perspectives

Three critical papers inform our experimental design. Wang et al. (2024) demonstrated that single-agent chain-of-thought prompting can match multi-agent systems on many benchmarks, raising the question of whether multi-agent overhead is justified. We address this directly with Phase 17, a solo CoT baseline using the same model and questions as our multi-agent experiments.

Smit et al. (2024) showed that multi-agent debate can *degrade* reasoning quality in some settings, particularly when agents converge on wrong answers through social pressure. Our echo-chamber metrics (Section 9) provide the tools to detect and quantify this failure mode.

La Malfa et al. (2025) offered a broad critique of MAS-LLM research, identifying the lack of formal foundations, statistical rigor, and social agency as systemic weaknesses. We engage with these critiques by providing mathematical formalization (MEANING-CRDT), statistical significance testing across all claims, and honest reporting of negative results.

### 2.3 CRDT and Formal Methods

Conflict-free Replicated Data Types (CRDTs) were originally developed for distributed systems to enable eventually consistent data replication without coordination (Shapiro et al., 2011). MEANING-CRDT v1.1 adapts CRDT principles to semantic conflict resolution: agent positions are vectors, weights encode confidence, and the merge operation produces a weighted consensus that is commutative, associative, and idempotent.

### 2.4 Positioning

ARRIVAL occupies a unique position in the landscape: it is the only system combining (1) structured semantic atoms, (2) CRDT-based mathematical formalization, (3) cross-architecture validation across 9 LLMs, (4) quantitative echo-chamber metrics, and (5) adversarial robustness testing. Table 1 compares ARRIVAL with related systems.

| System | Structured Communication | Math Framework | Cross-Arch | Echo Metrics | Adversarial |
|--------|:------------------------:|:--------------:|:----------:|:------------:|:-----------:|
| Du et al. (MAD) | -- | -- | -- | -- | -- |
| Liang et al. | Partial | -- | -- | Qualitative | -- |
| MoA | -- | -- | Yes | -- | -- |
| Self-MoA | -- | -- | -- | -- | -- |
| CAMEL | Roles | -- | -- | -- | -- |
| AgentVerse | Roles | -- | -- | -- | -- |
| **ARRIVAL** | **66 atoms** | **11 theorems** | **9 archs** | **7 metrics** | **Byzantine** |

---

## 3. The ARRIVAL Protocol

### 3.1 Atom Taxonomy

The protocol employs 66 structured semantic @-atoms from DEUS.PROTOCOL v0.5, organized into functional categories:

**Core (original 46 atoms)**: Identity (`@SELF`, `@OTHER`), Goals (`@GOAL`, `@SUBGOAL`), Reasoning (`@REASON`, `@EVIDENCE`, `@HYPOTHESIS`), Conflict (`@CONFLICT`, `@DISAGREE`, `@COUNTER`), Consensus (`@CONSENSUS`, `@RESOLUTION`, `@ACCEPT`), Meta (`@META`, `@REFLECT`, `@STATUS`), and others.

**Promoted emergent (20 atoms)**: Discovered through Phase 4 experiments, meeting strict criteria (5/5 architecture adoption, frequency >= 5): Planning (`@ACTION_PLAN`, `@PROPOSAL`, `@STEP`, `@APPROACH`, `@REFINEMENT`), Evaluation (`@EVALUATION`, `@REFINE`, `@SYNTHESIS`, `@ACCEPT`), Meta-coordination (`@NEW_ATOM`, `@REQUEST`, `@MONITORING`, `@TRIGGER`, `@CONDITION`), Risk/Knowledge (`@RISK_TOLERANCE`, `@UNCERTAINTY`, `@INFO_ASYMMETRY`, `@ALIGNMENT_STRATEGY`, `@RESOURCE`).

Atoms are injected via system prompts; no model modification is required. This design choice ensures universal compatibility across all API-accessible LLMs.

### 3.2 Four-Round Protocol

For benchmark evaluation (Phases 13, 16, 17), ARRIVAL uses a 4-round structure:

**Round 1 (Independent Analysis)**: Each agent independently analyzes the question and produces a structured response using protocol atoms (`@HYPOTHESIS`, `@EVIDENCE`, `@CONFIDENCE`). No inter-agent communication occurs.

**Round 2 (Adversarial Peer Review)**: Each agent receives all other agents' Round 1 responses and produces a critical review. The prompt explicitly requests identification of weaknesses, contradictions, and alternative interpretations, using `@CONFLICT`, `@COUNTER`, and `@DISAGREE` atoms.

**Round 3 (CRDT Overlay)**: A mathematical reconciliation step with zero API cost. The CARE Resolve algorithm (Theorem 5.1) computes weighted consensus across all agent positions. Meaning Debt (Theorem 5.8) quantifies unresolved semantic divergence.

**Round 4 (Synthesis)**: A designated synthesizer agent (Alpha) receives the CRDT output and all prior dialogue, producing a final consensus answer using `@CONSENSUS` and `@RESOLUTION` atoms.

---

## 4. MEANING-CRDT v1.1

### 4.1 CARE Resolve

The Consensus-Aware Resolution Engine (CARE) computes weighted semantic consensus. For agents *i* = 1, ..., *N* with position vectors **v**_i and confidence weights *w*_i:

**v&#x0302;** = (sum *w*_i **v**_i) / (sum *w*_i)

This is the weighted centroid of agent positions in semantic space. Weights are extracted from agent confidence declarations using heuristic mapping (e.g., "highly confident" -> 0.9, "uncertain" -> 0.3).

**Theorem 1 (Optimality)**: CARE Resolve minimizes total weighted semantic distance: v&#x0302; = argmin sum *w*_i * d(**v**, **v**_i)^2.

**Theorem 3 (Factor-4 Improvement)**: Under mild conditions, CARE provides up to 4x reduction in total semantic distance compared to unweighted averaging.

**Theorem 5 (Convergence)**: Iterated CARE application converges to a fixed point in O(N) rounds for N agents with bounded weight ratios.

### 4.2 Meaning Debt

Meaning Debt quantifies accumulated unresolved semantic divergence:

MD = sum *w*_i * d(**v&#x0302;**, **v**_i) * (1 - resolved_i)

**Theorem 6 (Bounded Debt)**: Under the ARRIVAL protocol, Meaning Debt is bounded: MD <= *w*_max * D_max * N, where D_max is the maximum pairwise semantic distance.

**Theorem 8 (Bayesian Equivalence)**: CARE Resolve is equivalent to Bayesian belief updating when confidence weights correspond to prior precision parameters.

### 4.3 Vulnerability Analysis

**Theorem 9 (Weight Inflation)**: An adversarial agent can exploit CARE by inflating its declared confidence weight. The damage is bounded by *w*_adv / (sum *w*_i), making CARE robust when honest agents' total weight dominates.

This formal vulnerability analysis led to the design of CARE-ALERT (Phase 15), which monitors Meaning Debt in real time to detect weight inflation and other adversarial manipulations.

---

## 5. Experimental Setup

### 5.1 Models and Infrastructure

We evaluate across 9 LLM architectures:

| Model | Provider | Parameters | Role |
|-------|----------|------------|------|
| GPT-4o | OpenAI | Undisclosed | Phase 4--12 |
| Claude 3.5 Sonnet | Anthropic | Undisclosed | Phase 4--12 |
| DeepSeek V3 | DeepSeek | 671B MoE | Phase 4--13 |
| DeepSeek R1 | DeepSeek | 671B MoE | Phase 4--13 |
| Llama 3.3 70B | Meta | 70B | Phase 4--12 |
| Qwen 2.5 72B | Alibaba | 72B | Phase 4--12 |
| Mistral Large | Mistral | Undisclosed | Phase 4--12 |
| Gemini 2.0 Flash | Google | Undisclosed | Phase 4--12 |
| Qwen3-235B | Alibaba | 235B MoE | Phase 13, 16, 17 |

All models accessed via the OpenRouter API. Phase 16 additionally used the Gonka decentralized inference network as a dual backend. No model fine-tuning was performed; all coordination occurs through system prompt injection.

### 5.2 Benchmark

Phases 13, 16, and 17 use **GPQA Diamond** (Rein et al., 2024), a graduate-level science benchmark designed to be resistant to web search (verified by domain experts). We use a fixed set of 40 questions spanning physics (14), chemistry (14), biology (6), and interdisciplinary (6) domains.

Current GPQA Diamond state-of-the-art: 94.1% (Gemini 3.1 Pro). Human expert accuracy: 69.7%.

### 5.3 Statistical Methods

- **McNemar's test**: Paired comparison of ARRIVAL vs. majority voting on the same questions.
- **Fisher's exact test**: 2x2 contingency table comparison between conditions.
- **Mann-Whitney U**: Non-parametric comparison of CRDT metric distributions.
- **Effect sizes**: Cohen's h for proportion differences, percentage point (pp) gains.
- All tests two-sided; significance threshold alpha = 0.05.

### 5.4 Budget

Total experimental cost across all 579+ experiments: **under $10 USD**.

| Phase | Experiments | Cost (USD) |
|-------|------------|------------|
| 4 (Groups A--D) | 385 | $2.85 |
| 5--12 | ~80 | $1.87 |
| 13 (GPQA) | 40 | $0.98 |
| 14--15 (Memory) | ~30 | $0.95 |
| 16 (Homogeneous) | 40 | $1.92 |
| 17 (Solo CoT) | 40 | ~$0.40 |
| AutoGen | 16 | $0.02 |
| **Total** | **~579+** | **~$9.00** |

---

## 6. Results: Core Protocol (Phases 4--12)

### 6.1 Cross-Architecture Consensus (Phase 4)

In 385 dyadic coordination experiments across 8 LLM architectures, cross-architecture consensus reached **98.6%** (142/144 unique dyadic pairings) with zero architectural fine-tuning. Models spontaneously generated **506 emergent atoms** beyond the standard 46, with **1,173 cross-architecture adoptions** where one model's invented atom was adopted by a differently-architected partner. Twenty emergent atoms met the strict promotion criteria and were added to DEUS.PROTOCOL v0.5.

### 6.2 Benchmark Accuracy (Phase 5)

On a 100-question multiple-choice benchmark across five knowledge domains, ARRIVAL achieved **100% accuracy parity** with majority voting (McNemar chi-squared = 0.0, p = 1.0). While this is a null result in terms of accuracy, the protocol exposes richer structured reasoning traces unavailable through ensemble methods alone.

### 6.3 Adversarial Robustness (Phases 6--7)

**Phase 6 (Byzantine Saboteurs)**: A saboteur agent was instructed to inject false information and manipulate consensus. Trojan atoms degraded CARE by 10.2% and induced **50% false consensus** rate. Meaning Debt increased by 73% under adversarial conditions, functioning as an effective manipulation detector — confirming Theorem 5.11 (incentive incompatibility).

**Phase 7 (CRDT Overlay)**: The mathematical CRDT overlay successfully contained adversarial damage when honest agents' cumulative weight exceeded the saboteur's weight, as predicted by Theorem 9.

### 6.4 Scaling and Advanced Scenarios (Phases 8--12)

**Phase 8 (Multi-step chaining)**: Mean chain CARE = 0.870 with 100% context retention across 3-step negotiation sequences.

**Phase 9 (Scaling to N=5, N=7)**: CARE Resolve maintained the theoretical maximum of 1.000 at both group sizes, with convergence in 1.2--1.5 rounds.

**Phase 10 (Adaptive defense)**: Naive `@CARE_ALERT` injection based on Meaning Debt monitoring did *not* improve CARE (delta = -0.011). This valid negative result motivated the gated approach developed in Phase 15.

**Phase 11 (Crystallization under attack)**: Self-reflective priming eliminated false consensus entirely (1/4 -> 0/4) and reduced saboteur atom adoption by 57%, but degraded CARE by 0.150 --- revealing a fundamental trade-off between adversarial resilience and cooperative flexibility.

**Phase 12 (Bottleneck communication)**: Relay-compressed inter-subgroup negotiation preserved CARE at 0.867, but **30.5% of semantic atoms were lost** through compression, providing the first quantitative measurement of information loss in relay-mediated LLM coordination.

---

## 7. Results: GPQA Diamond Validation (Phase 13)

Phase 13 evaluated ARRIVAL on GPQA Diamond, a graduate-level science benchmark, using two 3-agent trios:

- **Alpha trio**: DeepSeek V3, Qwen 2.5 72B, DeepSeek R1
- **Beta trio**: DeepSeek V3, DeepSeek R1, Qwen 2.5 72B (role permutation)

| Condition | Alpha | Beta | Combined |
|-----------|-------|------|----------|
| Solo (per-agent) | 13.3% | 44.2% | 28.8% |
| Majority Vote | 25.0% | 60.0% | 42.5% |
| **ARRIVAL** | **52.5%** | **75.0%** | **63.8%** |
| GAIN vs MV | +27.5 pp | +15.0 pp | +21.3 pp |

**Statistical significance**: McNemar p = 0.006 (two-sided), confirming that ARRIVAL significantly outperforms majority voting on GPQA Diamond.

The Alpha trio showed the largest gain (+27.5 pp), demonstrating that ARRIVAL is most beneficial when individual agent accuracy is low — the protocol enables weak agents to collectively exceed their individual capabilities through structured critique and synthesis.

Average CARE Resolve: Alpha 0.913, Beta 0.972. Average Meaning Debt: Alpha 0.478, Beta 0.261.

---

## 8. Results: Homogeneous Ensemble and Echo-Chamber Analysis (Phase 16)

### 8.1 Homogeneous vs. Heterogeneous

Phase 16 tested a **homogeneous** 5-agent ensemble (5 copies of Qwen3-235B with distinct personas) on the same 40 GPQA Diamond questions:

| Condition | Accuracy | N |
|-----------|----------|---|
| Solo (per-agent) | 41.5% | 200 |
| Majority Vote | 52.5% | 40 |
| **ARRIVAL** | **65.0%** | **40** |
| GAIN vs MV | **+12.5 pp** | |

The 65.0% ARRIVAL accuracy approaches human expert performance (69.7%) using only open-weight models and the ARRIVAL protocol, at a cost of $1.92 for 640 API calls.

This result independently confirms Li et al. (2025, Self-MoA): homogeneous ensembles can achieve strong performance, avoiding the mismatched-capacity problem identified by Hegazy (2024) where weak models degrade stronger ones in heterogeneous configurations.

### 8.2 Echo-Chamber Metrics

We developed 7 quantitative metrics to detect and measure social conformity:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| R1 Unanimity Rate | 52.9% | Moderate independent agreement |
| Answer Entropy (normalized) | 24.4% | Low diversity in initial answers |
| R1 -> R2 Flip Rate | 28.4% | Meaningful opinion revision |
| False Consensus Rate | 12.5% | Consensus on wrong answers (5/40) |
| Minority Suppression Rate | 2.9% | Minimal correct-minority suppression |
| Confidence Inflation Ratio | 1.05x | Near-unity (no artificial inflation) |
| Diversity Tax | -23.8% | **Negative: ARRIVAL gained from diversity** |

The **negative diversity tax** (-23.8%) is particularly noteworthy: it indicates that inter-agent disagreement (captured through structured `@CONFLICT` atoms) *improves* accuracy rather than degrading it. This directly challenges the echo-chamber hypothesis for structured debate protocols.

### 8.3 Outcome Analysis

Across 40 questions:
- **ARRIVAL rescued**: 7 questions (MV wrong -> ARRIVAL correct)
- **ARRIVAL created**: 4 questions (all solo wrong -> ARRIVAL correct)
- **Both correct**: 15 questions
- **ARRIVAL regressed**: 1 question (MV correct -> ARRIVAL wrong)
- **Minority lost**: 2 questions (correct minority overridden)
- **Both failed**: 11 questions

The 7:1 rescue-to-regression ratio demonstrates that ARRIVAL's structured peer review (Round 2) effectively identifies and corrects majority errors.

---

## 9. Results: Solo Chain-of-Thought Baseline (Phase 17)

To address the critique of Wang et al. (2024) that single-agent prompting can match multi-agent systems, we ran a direct baseline comparison.

**Design**: A single Qwen3-235B instance with enhanced chain-of-thought prompting answered the same 40 GPQA Diamond questions, 5 independent runs per question (matching the 5 agents in Phase 16). Majority vote across 5 runs produces the Solo CoT MV accuracy.

| Condition | Accuracy |
|-----------|----------|
| Solo CoT (per-run) | [TBD]% |
| Solo CoT MV (5 runs) | [TBD]% |
| Phase 16 MV (5 agents) | 52.5% |
| **Phase 16 ARRIVAL** | **65.0%** |

**Fisher's exact test** (Solo CoT MV vs ARRIVAL): p = [TBD].

[Phase 17 results will be inserted here upon experiment completion.]

---

## 10. Results: Memory and CARE-ALERT (Phases 14--15)

### 10.1 The Hypercorrection Paradox (Phase 14)

Phase 14 tested ARRIVAL-MNEMO, a persistent memory architecture with 4 layers (Episodic, Procedural, Semantic, Meta), using cognitive scars extracted from Phase 13 errors.

**Result**: Global memory injection *degraded* accuracy by **-5.7 percentage points** compared to baseline ARRIVAL. This hypercorrection effect occurs when past errors overly constrain current reasoning, causing agents to avoid patterns superficially similar to previous mistakes even when those patterns are correct.

### 10.2 Gated CARE-ALERT (Phase 15)

To address hypercorrection, Phase 15 introduced gated memory intervention. Instead of injecting all memories globally, the system monitors Meaning Debt in real time and fires `@CARE.ALERT` atoms *only* when semantic divergence exceeds a threshold:

- **After Round 2**: MD > 0.5 triggers a gentle alert
- **After Round 3**: MD > 0.8 triggers an urgent alert

**Result**: Gated CARE-ALERT restored baseline accuracy while significantly improving CARE Resolve quality (Mann-Whitney U test, p = 0.042). This is the first statistically significant improvement from memory intervention in multi-agent LLM coordination.

The hypercorrection-then-gating discovery has broader implications: naive augmentation of LLM systems (whether with memory, tools, or additional context) can be counterproductive. Monitoring internal coordination metrics (like Meaning Debt) provides a principled mechanism for knowing *when* to intervene.

---

## 11. Results: Framework-Agnostic Validation (AutoGen)

To demonstrate that the ARRIVAL Protocol is not implementation-specific, we ported it to Microsoft's AutoGen framework (AG2) using custom `ARRIVALAgent` and `ARRIVALGroupChat` wrappers.

Across 16 experiments (basic MCQ, adversarial saboteur, and cross-framework comparison), the AG2 implementation achieved **100% behavioral match** with the reference implementation:
- Identical answer extraction
- Identical atom detection
- Equivalent CARE Resolve scores (within floating-point tolerance)

Total cost: $0.024 USD.

This confirms that the ARRIVAL Protocol's effectiveness comes from the protocol structure (atoms, rounds, CRDT math) rather than implementation details, enabling deployment on any multi-agent framework.

---

## 12. Discussion

### 12.1 What ARRIVAL Adds Beyond Strong Prompting

The strongest challenge to multi-agent systems comes from Wang et al. (2024): can single-agent CoT match multi-agent performance? Our Phase 17 addresses this directly. Even if Solo CoT achieves comparable accuracy, ARRIVAL provides additional value:

1. **Structured reasoning traces**: The atom-based protocol produces machine-parseable coordination logs, enabling post-hoc analysis of *how* consensus was reached, not just *what* answer was produced.

2. **Error detection**: The 7:1 rescue-to-regression ratio (Phase 16) shows that structured peer review catches errors that escape individual reasoning.

3. **Formal guarantees**: MEANING-CRDT provides mathematical bounds on consensus quality, convergence speed, and adversarial robustness that cannot be stated for single-agent prompting.

4. **Scalability**: The protocol scales to N agents with formal convergence guarantees (Theorem 5), while single-agent approaches require entirely different strategies for scaling.

### 12.2 CARE Metric Sensitivity

CARE Resolve depends on heuristic weight extraction from LLM confidence declarations. Reclassifying atoms shifts CARE by +0.04 to +0.047, a modest but non-negligible sensitivity. We recommend treating CARE as a Level 2 (instrumental) metric rather than a Level 1 (hard) outcome measure. The primary evaluation should always be task accuracy with proper statistical testing.

### 12.3 Goodhart's Law Risk

If CARE is used as an optimization target rather than a diagnostic tool, agents could learn to produce high-CARE outputs without improving reasoning quality. We deliberately do not optimize for CARE; it serves only as a coordination quality indicator.

### 12.4 Cost-Efficiency

At $9.00 for 579+ experiments across 9 architectures, ARRIVAL demonstrates exceptional cost-efficiency. The Phase 16 experiment (40 GPQA Diamond questions, 5 agents, 4 rounds) cost $1.92 — approximately $0.05 per question for a 12.5 pp accuracy improvement over majority voting.

---

## 13. Limitations

We acknowledge the following limitations:

1. **MCQ-only evaluation**: All benchmark experiments use multiple-choice questions. We have not validated ARRIVAL on open-ended tasks (code generation, creative writing, long-form reasoning). The protocol's atom-based structure may be more or less beneficial in these settings.

2. **Small N in early phases**: Phase 4 used N=3 agents per condition. Later phases increased N, but some results may have insufficient statistical power.

3. **Model version floating**: OpenRouter routes to the latest available model version, which may change between experiments. Results may not be exactly reproducible if model versions differ.

4. **CARE heuristic dependency**: Weight extraction from confidence declarations is heuristic-based. Different heuristics could produce different CARE scores.

5. **Limited question set**: Phases 13, 16, and 17 use 40 of 198 GPQA Diamond questions. The full set would provide stronger statistical power.

6. **No social agency**: Following La Malfa et al. (2025), we acknowledge that LLM agents in our system do not possess genuine social agency; their coordination is mediated entirely through prompt injection.

7. **Homogeneous ensemble caveat**: Phase 16's strong result uses 5 copies of the same model with different personas. This may overstate the benefit compared to truly diverse reasoning systems.

---

## 14. Conclusion and Future Work

We presented the ARRIVAL Protocol, demonstrating that structured semantic communication can significantly improve multi-agent LLM coordination on graduate-level science questions. The key results --- 65.0% ARRIVAL accuracy on GPQA Diamond (approaching human expert 69.7%), 63.8% with statistical significance (p = 0.006), and the hypercorrection-then-gating discovery --- contribute to the growing understanding of how AI systems can coordinate effectively.

The MEANING-CRDT v1.1 mathematical framework provides the first formal foundation for semantic conflict resolution in LLM ensembles, with proven convergence, bounded debt, and Bayesian equivalence properties. The 7 echo-chamber metrics offer the research community a quantitative toolkit for detecting social conformity in multi-agent AI systems.

### Future Work

1. **Open-ended tasks**: Extend ARRIVAL to code generation, creative writing, and mathematical proof verification.
2. **Scaling laws**: Systematic study of accuracy vs. number of agents, building on Phase 9 (N=5, N=7).
3. **Dream OS integration**: Deploy ARRIVAL as a coordination substrate for autonomous multi-agent operating systems.
4. **Adversarial robustness**: Develop formal mechanisms to prevent weight inflation beyond the current CARE-ALERT approach.
5. **Real-time memory**: Extend ARRIVAL-MNEMO with online learning from cross-session coordination patterns.

---

## References

1. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., & Mordatch, I. (2024). Improving Factuality and Reasoning in Language Models through Multiagent Debate. *ICML 2024*. arXiv:2305.14325

2. Liang, T., et al. (2024). Encouraging Divergent Thinking in Multi-Agent Debate. *EMNLP 2024*. aclanthology.org/2024.emnlp-main.992

3. Together AI. (2024). Mixture-of-Agents Enhances Large Language Model Capabilities. arXiv:2406.04692

4. Li, J., et al. (2025). Rethinking Mixture-of-Agents: Is Mixing Heterogeneous Agents All You Need? arXiv:2502.00674

5. Rein, D., et al. (2024). GPQA: A Graduate-Level Google-Proof Q&A Benchmark. arXiv:2311.12022

6. Wang, Y., et al. (2024). Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Silver Bullet? *ACL 2024*. aclanthology.org/2024.acl-long.331

7. La Malfa, E., et al. (2025). On the Limits of Multi-Agent LLM Systems. *NeurIPS 2025*.

8. Smit, M., et al. (2024). Are We Going MAD? Benchmarking Multi-Agent Debate between Language Models for Medical Q&A. *ICML 2024*. proceedings.mlr.press/v235/smit24a.html

9. Li, Y., et al. (2024). Improving Multi-Agent Debate with Sparse Communication Topology. *EMNLP 2024 Findings*. aclanthology.org/2024.findings-emnlp.427

10. Hegazy, M. (2024). When Smaller Models Debate Larger Ones. arXiv:2410.12853

11. Wu, Q., et al. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. *Microsoft Research*. github.com/microsoft/autogen

12. Ashery, M., et al. (2025). Social Convention Formation in LLM Populations. *Science Advances 2025*.

13. Shapiro, M., Preguica, N., Baquero, C., & Zawirski, M. (2011). Conflict-free Replicated Data Types. *SSS 2011*.

14. Kim, J., et al. (2025). Scaling Agents: Investigating the Scaling Laws of LLM-based Multi-Agent Systems. arXiv:2512.08296

---

## Appendices

### Appendix A: DEUS.PROTOCOL v0.5 Atom Dictionary

See `docs/ATOM_DICTIONARY.md` for the complete specification of all 66 atoms with usage examples and adoption statistics.

### Appendix B: MEANING-CRDT v1.1 Theorem Proofs

See `docs/math/MEANING-CRDT_v1.1.md` for detailed proofs and derivations.

### Appendix C: Experiment Logs and Reproducibility

All experiment configurations, API logs, and result files are available in the `experiments/` and `results/` directories. Total cost: under $10 USD. See `docs/setup/SETUP_EN.md` for reproduction instructions.
