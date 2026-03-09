# ARRIVAL Protocol: Cross-Architecture AI-to-AI Coordination Through Structured Semantic Atoms

**Author**: Mefodiy Kelevra
**ORCID**: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
**Date**: March 2026
**DOI**: [10.5281/zenodo.18893515](https://doi.org/10.5281/zenodo.18893515)
**License**: CC BY-NC 4.0 (text), AGPL-3.0-or-later (code)
**Repository**: https://github.com/DreamOS-Network/Arrival-Protocol

**Keywords**: multi-agent debate, LLM coordination, CRDT, semantic atoms, echo chamber, adversarial robustness, GPQA, cross-architecture, confidence-gated debate, CGD, agreement gating

---

## Abstract

We present the ARRIVAL Protocol (Atomic Reasoning via Rival Validation and Adversarial Logic), a structured communication framework enabling AI-to-AI coordination across heterogeneous large language model (LLM) architectures without fine-tuning, shared weights, or prior joint training. The protocol employs 66 semantic @-atoms from DEUS.PROTOCOL v0.5, injected via system prompts, to establish a shared coordination vocabulary.

Across 2,200+ experiments organized into 23 phases involving 17 distinct LLM architectures, we report the following principal findings. On the GPQA Diamond graduate-level science benchmark (N=40), ARRIVAL achieves **65.0% accuracy** with a homogeneous 5-agent Qwen3-235B ensemble (Phase 16), compared to 52.5% for majority voting (+12.5 percentage points). In a heterogeneous 3-agent configuration (Phase 13), ARRIVAL achieves **63.8%** versus majority voting at 42.5% (McNemar p = 0.006). Scaling to the **full 198-question GPQA Diamond** with mid-tier models (Phase 20), ARRIVAL MV achieves **67.7%** vs Solo CoT majority vote at **62.1%** (+5.6 pp, McNemar p = 0.233, ns). With **frontier-tier models** (Phase 21: GPT-4.1, Gemini 3 Flash, Grok 4.1 Fast), the debate effect **inverts**: Non-Debate MV reaches **82.3%** vs ARRIVAL MV at **78.8%** (−3.5 pp, McNemar p = 0.265, ns). The anchoring effect — where strong models abandon correct answers after seeing weak proposals — is identified as the primary degradation mechanism. Phase 22 introduces **Confidence-Gated Debate (CGD)**, which eliminates anchoring through independent solo answers and agreement-based gating. On the full 198-question GPQA Diamond, CGD achieves **86.4% accuracy** (95% CI: [80.9%, 90.5%]) — exceeding solo Grok 4.1 Fast (85.4%, +1.0 pp) and significantly outperforming ARRIVAL MV (78.8%, +7.6 pp, McNemar p = 0.009). CGD resolves 61.6% of questions unanimously (95.9% accuracy) and applies targeted debate only to the remaining 38.4% where models disagree. Scaling CGD to a **7-model cross-vendor ensemble** (Phase 23: 3 US + 4 Chinese models from 5 vendors) yields **86.9%** (+0.5 pp vs 3-model CGD, McNemar p = 1.0, ns), while the best individual model (Grok 4.1 Fast, 87.4%) outperforms the ensemble — demonstrating that model quality dominates quantity for MCQ tasks. The 7-model oracle ceiling of 96.5% proves cross-vendor diversity contains signal, but current aggregation methods cannot fully extract it.

Phase 23 ablation reveals non-monotonic scaling: a pruned 4-model weighted MV subset (WMV+D-3) achieves **88.4%** (175/198), the project-high accuracy, demonstrating that model quality dominates quantity. Qwen3.5-397B is identified as a **poisoned voter** (5% minority-correct rate, 27% extraction failures), establishing a quality threshold below which ensemble participation is harmful.

On practical software engineering tasks (Phase 18), a heterogeneous 5-model ARRIVAL swarm (GPT-4.1, DeepSeek V3.2, Mistral Large 3, Gemini 3 Flash, Grok 4.1 Fast) **matches Claude Sonnet 4.5** on security audit (10/10 bugs found vs 10/10) and achieves competitive code generation (53% vs 60% test pass rate) at **comparable cost** ($0.14 vs $0.12 per task). This demonstrates that ARRIVAL enables 5 cheaper models to collectively match a single frontier model while providing full transparency and vendor independence.

We formalize conflict resolution through MEANING-CRDT v1.1, a mathematical framework based on Conflict-free Replicated Data Types with 11 theorems covering CARE Resolve (weighted semantic consensus), Meaning Debt (accumulated divergence), convergence, and Bayesian equivalence. Seven quantitative echo-chamber metrics detect and measure social conformity in LLM ensembles. Adversarial testing with Byzantine saboteurs and Trojan atoms confirms robustness bounds predicted by the formal framework.

The ARRIVAL-MNEMO memory extension (Phases 14--15) reveals a hypercorrection paradox: naive memory injection *degrades* accuracy by 5.7 pp, while gated CARE-ALERT interventions that monitor Meaning Debt in real time restore baseline performance (CARE improvement p = 0.042). The CARE-ALERT gating mechanism is validated in Phase 18: it correctly activates memory injection when consensus is low (CARE = 0.50, analytical task) and correctly suppresses it when consensus is high (CARE = 0.97, constructive task). Framework-agnostic validation on Microsoft's AutoGen (AG2) achieves 100% behavioral match with the reference implementation.

On a game-theoretic cooperation benchmark (Phase 19, GovSim fish pond commons, N=5 per condition, Fisher p = 0.008), ARRIVAL converts **0% baseline survival to 100% survival** across all 25 runs (5 conditions × 5 runs). Ablation analysis reveals binding R4 allocation alone achieves 100% survival at 32× lower cost, while adversarial R4 testing identifies R4 as a single point of trust (Gini = 0.800). See the full preprint in `final_report/ARRIVAL_PROTOCOL_PREPRINT.md` for complete results.

The total computational cost for all experiments is under $95 USD across ~14,500 API calls. These results suggest that structured semantic protocols offer a viable, low-cost coordination layer for heterogeneous multi-agent AI systems, with primary value in cooperation, transparency, and — through CGD — principled ensemble aggregation that outperforms both debate and naive voting.

---

## 1. Introduction

### 1.1 Problem Statement

The proliferation of large language models from competing vendors has created a fragmented ecosystem in which models cannot natively coordinate. Each architecture processes language through different tokenization schemes, attention mechanisms, training corpora, and alignment procedures. Yet many applications demand coordination: multi-agent reasoning, ensemble decision-making, negotiation, and collaborative problem-solving.

Recent work on multi-agent debate (MAD) has demonstrated that structured interaction between LLMs can improve factuality and reasoning (Du et al., 2024). However, the MAD paradigm faces three critical challenges. First, unstructured debate can *degrade* reasoning quality rather than improve it (Smit et al., 2024). Second, strong single-agent prompting strategies can match multi-agent systems on many benchmarks (Wang et al., 2024). Third, existing MAS-LLM systems generally lack formal foundations, statistical rigor, and honest engagement with failure modes (La Malfa et al., 2025).

The ARRIVAL Protocol addresses these challenges through three complementary innovations:

1. **Structured semantic atoms**: 66 compositional @-atoms (e.g., `@SELF`, `@CONFLICT`, `@CONSENSUS`) provide a formal coordination vocabulary, replacing unstructured free-text debate with machine-parseable communication that prevents quality degradation.

2. **CRDT-based conflict resolution**: MEANING-CRDT v1.1 formalizes consensus as weighted vector averaging with proven convergence, bounded debt, and Bayesian equivalence properties, moving beyond heuristic aggregation.

3. **Empirical rigor**: 2,200+ experiments across 17 architectures with statistical significance testing (Fisher's exact, McNemar's, Mann-Whitney U), adversarial testing, ablation studies, and explicit engagement with critical work.

### 1.2 Contributions

This paper makes the following contributions:

- **ARRIVAL Protocol**: A 4-round structured coordination protocol using 66 semantic atoms, validated across 17 LLM architectures.
- **MEANING-CRDT v1.1**: A mathematical framework with 11 theorems for principled conflict resolution in multi-agent LLM systems.
- **Echo-chamber analysis**: 7 quantitative metrics for detecting and measuring social conformity in LLM ensembles.
- **Hypercorrection paradox**: Discovery that naive memory injection degrades multi-agent accuracy, with a gated solution (CARE-ALERT).
- **Applied validation**: Demonstration that a 5-model heterogeneous swarm matches a frontier solo model on practical tasks (security audit, code generation) at comparable cost, with full per-model transparency.
- **CARE as task discriminator**: CARE Resolve quantitatively distinguishes analytical tasks (CARE ~0.50, divergent opinions) from constructive tasks (CARE ~0.97, convergent solutions).
- **Cross-framework validation**: Demonstration that the protocol is framework-agnostic via AutoGen (AG2) integration.
- **Cooperation breakthrough**: First demonstration of a structured multi-agent protocol solving the tragedy of the commons for LLMs (0% → 100% survival in GovSim), with self-healing defection neutralization.
- **Comprehensive empirical evaluation**: 2,200+ experiments, under $95 total, covering adversarial robustness, scaling, domain transfer, applied tasks, cooperation, ablation, and confidence-gated debate.

### 1.3 Organization

Section 2 reviews related work and positions ARRIVAL within the MAD literature. Section 3 describes the protocol specification. Section 4 presents MEANING-CRDT v1.1. Sections 5--14 report experimental results across 23 phases. Section 15 discusses findings. Section 16 addresses limitations. Section 17 concludes.

---

## 2. Related Work

### 2.1 Multi-Agent Debate

Du et al. (2024) established that multi-agent debate improves factuality and reasoning across LLM tasks, founding the MAD paradigm. Subsequent work has explored variations: Liang et al. (2024) introduced structured critique rounds to encourage divergent thinking, addressing the echo-chamber problem in free-form debate. Li et al. (2024) showed that sparse communication topologies outperform fully connected ones, suggesting that *how* agents communicate matters as much as *that* they communicate. RUMAD (Wang et al., 2026) unifies multi-agent debate with reinforcement learning, using RL to learn optimal debate strategies. A-HMAD (Zhou & Chen, 2025) proposes adaptive heterogeneous debate for educational and factual reasoning. ReConcile (Chen et al., 2024) demonstrates that round-table conference-style interaction among diverse LLMs improves reasoning via consensus, a design philosophy closely related to ARRIVAL's structured coordination.

The Mixture-of-Agents (MoA) framework (Together AI, 2024) demonstrated that layered aggregation of multiple LLM outputs can outperform individual models. Li et al. (2025) extended this with Self-MoA, showing that *homogeneous* ensembles (copies of the same model) can outperform heterogeneous ones --- a finding independently confirmed by our Phase 16 results.

### 2.2 Critical Perspectives

Three critical papers inform our experimental design. Wang et al. (2024) demonstrated that single-agent chain-of-thought prompting can match multi-agent systems on many benchmarks, raising the question of whether multi-agent overhead is justified. We address this directly with Phase 17, a solo CoT baseline using the same model and questions as our multi-agent experiments. Choi et al. (2025) prove a **martingale property**: multi-agent debate does not change the expected correctness of LLM responses, only their variance — a theoretical result that validates our Phase 21 finding that debate is net zero on MCQ accuracy and motivates CGD's agreement-based gating design.

Smit et al. (2024) showed that multi-agent debate can *degrade* reasoning quality in some settings, particularly when agents converge on wrong answers through social pressure. Our echo-chamber metrics (Section 8) provide the tools to detect and quantify this failure mode.

La Malfa et al. (2025) offered a broad critique of MAS-LLM research, identifying the lack of formal foundations, statistical rigor, and social agency as systemic weaknesses. We engage with these critiques by providing mathematical formalization (MEANING-CRDT), statistical significance testing across all claims, and honest reporting of negative results.

### 2.3 Game-Theoretic Cooperation in LLMs

GovSim (Piatti et al., 2024) established the key benchmark: 12 of 15 LLM models achieve 0% survival in a shared fish-pond resource management game. Agents consistently over-harvest, leading to tragedy of the commons. La Malfa et al. (2025) attributed this to three structural deficits: no native social behavior, ambiguous NL communication, and no quantitative emergence metrics.

FAIRGAME (Buscemi et al., 2025) documented end-game defection and cross-linguistic instability. Piche et al. (2025) showed that RL-trained LLMs shift toward defection under competitive pressure. Akata et al. (2023) found GPT-4 to be "unforgiving" in repeated prisoner's dilemma. These findings collectively suggest that free-form LLM negotiation is fundamentally insufficient for sustained cooperation.

Phase 19 addresses this gap: ARRIVAL's structured @-atoms and binding R4 allocation provide the missing cooperation infrastructure, converting 0% to 100% survival.

### 2.4 CRDT and Formal Methods

Conflict-free Replicated Data Types (CRDTs) were originally developed for distributed systems to enable eventually consistent data replication without coordination (Shapiro et al., 2011). MEANING-CRDT v1.1 adapts CRDT principles to semantic conflict resolution: agent positions are vectors, weights encode confidence, and the merge operation produces a weighted consensus that is commutative, associative, and idempotent.

### 2.5 Selective Debate and Confidence Gating

Recent work has explored when to debate versus when to accept initial answers. Choi et al. (2025) prove that multi-agent debate has a **martingale property**: debate does not change the expected correctness of LLM responses, only their variance. This theoretical result validates our empirical finding (Phases 20-21) that debate is net zero on MCQ accuracy.

Fan et al. (2026) propose **iMAD** (Informed Multi-Agent Debate), which uses ML-trained confidence classifiers to gate debate — debating only when a classifier predicts low confidence. This requires labeled training data. Zhou et al. (2025) investigate disagreement mechanisms in multi-agent systems. Eo et al. (2025) examine whether natural language is the optimal medium for debate (**DOWN**).

Kaesberg et al. (2025) systematically compare voting versus consensus mechanisms in multi-agent debate, finding that the optimal aggregation strategy is task-dependent — a finding that resonates with our CARE-based task discrimination (analytical vs. constructive tasks). Ai et al. (2025) go beyond majority voting to propose higher-order aggregation methods that leverage inter-model agreement patterns, conceptually related to CGD's agreement-gating mechanism.

Our Phase 22 CGD differs from these approaches: it uses zero-shot inter-model agreement (not trained classifiers) as the gating signal, requiring no training data. CGD is also the first to combine agreement-based gating with heterogeneous models and targeted debate on a standardized benchmark.

In the cooperation domain, Kaesberg et al. (2025, "Subtle Art of Defection") investigate LLMs' failure to avoid tragedy of commons, and Hintze & Adami (2026) show that cooperation emerges at a tipping point of LLM capability. Both findings align with our Phase 19 result that structural support (ARRIVAL) can bridge the cooperation gap. Kostka & Chudziak (2026) evaluate theory of mind and internal beliefs in multi-agent LLM systems, providing a complementary perspective on the social cognition challenges that ARRIVAL's structured atoms are designed to address.

### 2.6 Positioning

ARRIVAL occupies a unique position in the landscape: it is the only system combining (1) structured semantic atoms, (2) CRDT-based mathematical formalization, (3) cross-architecture validation across 17 LLMs, (4) quantitative echo-chamber metrics, (5) adversarial robustness testing, (6) game-theoretic cooperation validation, and (7) agreement-gated debate (CGD). Table 1 compares ARRIVAL with related systems.

| System | Structured Communication | Math Framework | Cross-Arch | Echo Metrics | Adversarial |
|--------|:------------------------:|:--------------:|:----------:|:------------:|:-----------:|
| Du et al. (MAD) | -- | -- | -- | -- | -- |
| Liang et al. | Partial | -- | -- | Qualitative | -- |
| MoA | -- | -- | Yes | -- | -- |
| Self-MoA | -- | -- | -- | -- | -- |
| CAMEL | Roles | -- | -- | -- | -- |
| AgentVerse | Roles | -- | -- | -- | -- |
| **ARRIVAL** | **66 atoms** | **11 theorems** | **17 archs** | **7 metrics** | **Byzantine** |

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

### 3.3 Confidence-Gated Debate (CGD) — Phase 22 Variant

Phase 22 introduces a protocol variant that replaces the sequential 4-round structure with an agreement-gated approach. CGD operates in three phases: (1) **Independent Solo** — all K models answer independently without seeing each other's responses; (2) **Agreement Check** — classify the answer pattern as unanimous (K/K agree), split 2v1 ((K-1)/K agree), or split 3-way (all different); (3) **Targeted Debate** — debate occurs only when disagreement exists, with the final answer determined by majority vote (no R4 synthesizer). This eliminates the anchoring bias and R4 regression problems identified in Phases 20-21. See Section 10.5 for detailed specification and full results.

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

We evaluate across 17 LLM architectures:

| Model | Provider | Parameters | Phases |
|-------|----------|------------|--------|
| GPT-4o | OpenAI | Undisclosed | 4--12 |
| Claude 3.5 Sonnet | Anthropic | Undisclosed | 4--12 |
| DeepSeek V3 | DeepSeek | 671B MoE | 4--13 |
| DeepSeek R1 | DeepSeek | 671B MoE | 4--13 |
| Llama 3.3 70B | Meta | 70B | 4--12 |
| Qwen 2.5 72B | Alibaba | 72B | 4--12 |
| Mistral Large | Mistral | Undisclosed | 4--12 |
| Gemini 2.0 Flash | Google | Undisclosed | 4--12 |
| Qwen3-235B | Alibaba | 235B MoE | 13, 16, 17 |
| Claude Sonnet 4.5 | Anthropic | Undisclosed | 18 (solo baseline) |
| GPT-4.1 | OpenAI | Undisclosed | 18, 20--22 |
| DeepSeek V3.2 | DeepSeek | MoE | 18, 23 |
| Mistral Large 3 | Mistral | Undisclosed | 18 |
| Gemini 3 Flash | Google | Undisclosed | 18, 20--23 |
| Grok 4.1 Fast | xAI | Undisclosed | 18, 20--23 |
| Claude Sonnet 4.6 | Anthropic | Undisclosed | 23 |
| Kimi K2.5 | Moonshot AI | Undisclosed | 23 |
| GLM-5 | Zhipu AI | Undisclosed | 23 |
| Qwen3.5-397B | Alibaba | 397B MoE | 23 |

All models accessed via the OpenRouter API. Phase 16 additionally used the Gonka decentralized inference network as a dual backend. No model fine-tuning was performed; all coordination occurs through system prompt injection.

### 5.2 Benchmark

Phases 13, 16, and 17 use **GPQA Diamond** (Rein et al., 2024), a graduate-level science benchmark designed to be resistant to web search (verified by domain experts). We use a fixed set of 40 questions spanning physics (14), chemistry (14), biology (6), and interdisciplinary (6) domains. Phases 20 and 21 scale to the **complete 198-question GPQA Diamond set** (physics 86, chemistry 93, biology 19) with randomized answer ordering per question (seed 42+i).

Current GPQA Diamond state-of-the-art: 94.1% (Gemini 3.1 Pro). Human expert accuracy: 69.7%. As of March 2026, multiple frontier models exceed 90%: Gemini 3.1 Pro 94.1%, GPT-5.3 Codex ~91.5%, Claude Opus 4.6 ~91.3%. GPQA Diamond is approaching saturation at the frontier but remains discriminative in the 60--90% range where our ensemble models operate.

### 5.3 Statistical Methods

- **McNemar's test**: Paired comparison of ARRIVAL vs. majority voting on the same questions.
- **Fisher's exact test**: 2x2 contingency table comparison between conditions.
- **Mann-Whitney U**: Non-parametric comparison of CRDT metric distributions.
- **Effect sizes**: Cohen's h for proportion differences, percentage point (pp) gains.
- All tests two-sided; significance threshold alpha = 0.05.

### 5.4 Budget

Total experimental cost across all 2,200+ experiments: **under $95 USD**.

| Phase | Experiments | API Calls | Cost (USD) |
|-------|------------|-----------|------------|
| 4--5 (Groups A--D, Benchmark) | 485 | ~2,000 | ~$2.00 |
| 6--12 (Adversarial, Echo, Scaling) | ~80 | ~500 | ~$1.50 |
| 13 (GPQA, N=40) | 80 | ~320 | ~$1.00 |
| 14--15 (Memory, MNEMO) | ~40 | ~200 | ~$0.50 |
| 16 (Homogeneous 5-agent) | 200+ | 640 | $1.92 |
| 17 (Solo CoT, N=40) | 200 | 200 | $0.50 |
| 18 (Applied tasks) | 6 | ~66 | $0.77 |
| 19 (GovSim, N=5) | 25 | 2,165 | $5.76 |
| 20 (GPQA full, N=198) | 198 | ~1,782 | $7.43 |
| 21 (GPQA frontier, N=198) | 198+594 | ~1,386 | $9.63 |
| 22 (CGD, N=198) | 198 | ~692 | $5.72 |
| 23 (CGD-7 ablation, N=198) | 198 | ~1,822 | $11.35 |
| AutoGen validation | 16 | ~100 | $0.02 |
| **Total** | **2,200+** | **~14,500** | **< $95** |

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
| Solo CoT (per-run) | 61.0% (122/200) |
| **Solo CoT MV (5 runs)** | **70.0% (28/40)** |
| Solo CoT Oracle (best-of-5) | 85.0% (34/40) |
| Phase 16 MV (5 agents) | 52.5% (21/40) |
| **Phase 16 ARRIVAL** | **65.0% (26/40)** |

**Fisher's exact test**: Solo CoT MV vs ARRIVAL, p = 0.812 (not significant); Solo CoT MV vs Phase 16 MV, p = 0.168 (not significant). Cost: $0.50 for 200 API calls.

**Per-domain breakdown (Solo CoT MV)**:

| Domain | Accuracy | n |
|--------|----------|---|
| Physics | 85.7% | 12/14 |
| Chemistry | 42.9% | 6/14 |
| Biology | 66.7% | 4/6 |
| Interdisciplinary | 100.0% | 6/6 |

**Analysis**: Solo Qwen3-235B with enhanced CoT prompting achieves 70.0% MV accuracy, 5 percentage points above ARRIVAL's 65.0%. However, this difference is not statistically significant (p = 0.812), confirming that ARRIVAL and solo CoT are **statistically comparable** on this benchmark. The result validates Wang et al.'s (2024) finding that strong single-agent prompting can match multi-agent systems on accuracy. Crucially, ARRIVAL provides additional value beyond raw accuracy: full audit trails of each agent's reasoning (Section 3), CARE-based consensus measurement (enabling adaptive coordination as shown in Phase 18), and robustness through diverse model perspectives. The per-domain analysis reveals that Solo CoT excels at physics (85.7%) and interdisciplinary (100%) but struggles with chemistry (42.9%), suggesting domain-dependent difficulty rather than a systematic advantage.

---

## 10. Results: Full GPQA Diamond Evaluation (Phase 20, N=198)

Phases 13 and 17 evaluated only 40 of 198 GPQA Diamond questions. Phase 20 scales to the **complete dataset**, providing ~5× statistical power.

### 10.1 Experimental Design

**ARRIVAL Condition**: Trio Alpha with upgraded R1/R4 — GPT-4.1 (replacing GPT-4o), DeepSeek V3 (R2), Llama 3.3 70B (R3). 4-round sequential protocol, temperature 0.3, max_tokens 1024. Total: 792 API calls, cost $2.41.

**Solo CoT Condition**: Qwen3-235B with `/no_think` mode, 5 independent runs per question, temperature 0.7, max_tokens 2048. Majority vote. Total: 990 API calls, cost $2.36.

Both conditions used the same 198 questions with randomized answer order (seed 42+i). Answer choices include both letter and text to enable matching by answer content rather than position.

### 10.2 Overall Accuracy

| Condition | Correct | Total | Accuracy | 95% Wilson CI |
|-----------|---------|-------|----------|---------------|
| **ARRIVAL R4** | 132 | 198 | **66.7%** | [59.8%, 72.9%] |
| ARRIVAL MV (R1-R3) | 134 | 198 | 67.7% | [60.9%, 73.8%] |
| **Solo CoT MV** | 123 | 198 | **62.1%** | [55.2%, 68.6%] |
| Solo CoT per-run | 585 | 990 | 59.1% | — |
| Solo CoT oracle | 165 | 198 | 83.3% | — |

### 10.3 Statistical Tests

**McNemar test (ARRIVAL R4 vs Solo CoT MV)**: chi2 = 1.422, **p = 0.233 (not significant)**. ARRIVAL wins 27 questions that Solo gets wrong; Solo wins 18 that ARRIVAL gets wrong. 105 questions are answered correctly by both; 48 are wrong for both.

**McNemar test (ARRIVAL R4 vs ARRIVAL MV)**: chi2 = 0.063, **p = 0.803 (not significant)**. R4 rescues 7 questions from MV errors but introduces 9 new regressions (net: -2). The R4 finalizer step provides no statistically significant benefit.

**Fisher exact test** (unpaired backup): ARRIVAL vs Solo p = 0.401; ARRIVAL R4 vs MV p = 0.915.

### 10.4 Per-Domain Breakdown

| Domain | n | ARRIVAL R4 | ARRIVAL MV | Solo CoT MV |
|--------|---|-----------|-----------|-------------|
| Physics | 86 | 80.2% | 82.6% | 81.4% |
| Biology | 19 | 78.9% | 73.7% | 57.9% |
| Chemistry | 93 | 51.6% | 52.7% | 45.2% |

ARRIVAL shows the largest advantage in Biology (+21.0 pp over Solo CoT) and modest advantages in Chemistry (+6.4 pp). Physics performance is comparable across all conditions.

### 10.5 Individual Model Accuracy

| Model | Role | Accuracy |
|-------|------|----------|
| DeepSeek V3 | R2 (Critic) | **66.2%** |
| GPT-4.1 | R4 (Finalizer) | 66.7% |
| GPT-4.1 | R1 (Proposer) | 63.6% |
| Llama 3.3 70B | R3 (Synthesizer) | 57.6% |

DeepSeek V3 achieves the highest individual accuracy (66.2%), outperforming GPT-4.1 as proposer (63.6%). Llama 3.3 70B is the weakest model at 57.6%.

### 10.6 Protocol Dynamics

| Metric | Value |
|--------|-------|
| Avg CARE Resolve | 0.955 |
| Avg Meaning Debt | 0.319 |
| R1→R2 flip rate | 9.1% |
| R2→R3 flip rate | 12.6% |
| R3→R4 flip rate | 10.6% |
| R4 rescue rate | 10.9% of MV errors |
| R4 regression rate | 6.7% of MV successes |

### 10.7 Consistency with Phase 13

40 questions from Phase 13 were matched by question text to Phase 20 results:

| Condition | Phase 13 (N=40) | Phase 20 subset (N=40) | Delta |
|-----------|----------------|----------------------|-------|
| ARRIVAL | 65.0% | 75.0% | +10.0 pp |
| MV | 52.5% | 75.0% | +22.5 pp |

The improvement on the Phase 13 subset is attributable to GPT-4.1 replacing GPT-4o in R1/R4. The MV improvement (+22.5 pp) is particularly large, suggesting that GPT-4.1 provides substantially better initial proposals than GPT-4o.

### 10.8 Analysis

Phase 20 provides three key findings:

1. **ARRIVAL outperforms Solo CoT by 4.6 pp but the difference is not statistically significant** (p = 0.233). The confidence intervals overlap: ARRIVAL [59.8%, 72.9%] and Solo [55.2%, 68.6%]. With 198 questions, we have 80% power to detect a difference of ~10 pp at alpha=0.05; the observed 4.6 pp difference is below this threshold.

2. **The R4 finalizer step is net negative**, introducing more regressions (9) than rescues (7). Simple majority voting of R1-R3 achieves 67.7%, slightly higher than R4's 66.7%. This suggests that the sequential debate protocol's value comes from diverse model perspectives rather than the final synthesis step.

3. **Domain-dependent effectiveness**: ARRIVAL's largest advantage is in Biology (+21 pp), likely because heterogeneous models provide genuinely different domain expertise. In Chemistry (the hardest domain at ~50% for all conditions), neither approach shows a clear advantage.

### 10.9 Phase 21: Strong Model Trio (N=198)

Phase 20 used mid-tier models (GPT-4o/4.1, DeepSeek V3, Llama 3.3 70B) with solo baselines of 57--66%. Phase 21 tests whether **frontier-tier models** with higher solo accuracy produce a significant debate effect. This directly addresses the hypothesis: "you cannot debate your way to correct answers if nobody knows chemistry."

**Models**: GPT-4.1 (R1/R4, OpenAI), Gemini 3 Flash Preview (R2, Google), Grok 4.1 Fast (R3, xAI). Maximum vendor diversity across three frontier providers.

**Primary test**: McNemar ARRIVAL MV vs Non-Debate MV (same 3 models, debate vs no debate) — this isolates the causal effect of structured discussion by holding model capability constant.

### 10.10 Phase 21: Overall Accuracy

| Condition | Correct | Total | Accuracy | 95% Wilson CI |
|-----------|---------|-------|----------|---------------|
| Solo Grok 4.1 Fast | **169** | 198 | **85.4%** | [79.8%, 89.6%] |
| **Non-Debate MV** | **163** | 198 | **82.3%** | [76.4%, 87.0%] |
| Solo Gemini 3 Flash | 163 | 198 | 82.3% | [76.4%, 87.0%] |
| ARRIVAL MV (debate) | 156 | 198 | 78.8% | [72.6%, 83.9%] |
| ARRIVAL R4 (debate) | 151 | 198 | 76.3% | [69.9%, 81.7%] |
| Solo GPT-4.1 | 131 | 198 | 66.2% | [59.3%, 72.4%] |

Non-Debate MV outperforms ARRIVAL MV by 3.5 pp. Grok 4.1 Fast alone (85.4%) exceeds all ensemble methods.

### 10.11 Phase 21: Statistical Tests

**PRIMARY TEST — McNemar ARRIVAL MV vs Non-Debate MV**:

|  | ND correct | ND wrong |
|--|-----------|----------|
| ARRIVAL MV correct | 145 | 11 (debate wins) |
| ARRIVAL MV wrong | 18 (debate losses) | 24 |

McNemar χ² = 1.241, **p = 0.265 (not significant)**. Debate wins 11, losses 18, net: **−7**. Structured debate does not improve accuracy when strong models already know the answers; it slightly degrades performance.

**R4 vs MV (within ARRIVAL)**: R4 rescues 8, regressions 13, net: −5 (McNemar p = 0.383). The R4 finalizer is net negative for the third consecutive experiment (Phases 20, 21).

**ARRIVAL MV vs Solo GPT-4.1**: McNemar χ² = 14.05, **p = 0.000178 (highly significant)**. ARRIVAL wins 33, GPT wins 8, net: +25. This is an ensemble effect — adding Gemini and Grok to the vote — not a debate effect.

### 10.12 Phase 21: Per-Domain and Per-Model Analysis

| Domain | n | ARRIVAL MV | Non-Debate MV | Best Solo | Debate Δ |
|--------|---|-----------|---------------|-----------|----------|
| Physics | 86 | 89.5% | **93.0%** | Grok 94.2% | −3.5 pp |
| Chemistry | 93 | 71.0% | **75.3%** | Grok 80.6% | −4.3 pp |
| Biology | 19 | 68.4% | 68.4% | GPT/Grok 68.4% | 0.0 pp |

Non-Debate MV dominates in Physics and Chemistry. No domain shows a significant debate advantage.

**In-debate accuracy shift**: Gemini 3 Flash drops from 82.3% (solo) to 78.3% (as R2 in debate), a −4.0 pp loss due to anchoring on GPT-4.1's weaker proposals. Grok 4.1 Fast is slightly helped (85.4% → 86.9%, +1.5 pp as R3 synthesizer). This anchoring effect — where strong models abandon correct answers after seeing weak proposals — is the primary mechanism behind debate's negative impact.

### 10.13 Phase 21: Cross-Phase Comparison

| Metric | Phase 20 (mid-tier) | Phase 21 (frontier) | Delta |
|--------|--------------------|--------------------|-------|
| ARRIVAL MV | 67.7% | **78.8%** | +11.1 pp |
| ARRIVAL R4 | 66.7% | **76.3%** | +9.6 pp |
| Best solo model | 66.2% | **85.4%** | +19.2 pp |
| Debate effect (vs non-debate) | +5.6 pp (vs Solo CoT) | **−3.5 pp** (vs ND MV) | Inversion |
| McNemar p | 0.233 | 0.265 | Both n.s. |
| Total cost | $4.77 | $9.63 | +$4.86 |

Stronger models improve both ARRIVAL and solo baselines, but solo baselines improve *more* (+19.2 pp vs +11.1 pp). The debate protocol's constant overhead (R4 regressions, anchoring degradation) becomes proportionally larger as models improve, inverting the effect direction from slightly positive (Phase 20) to slightly negative (Phase 21). This suggests a fundamental limitation: **structured debate on MCQ benchmarks adds noise, not signal, when models are individually capable.**

### 10.14 Phase 21: Failure Mode Analysis and Voting Strategy Comparison

Post-hoc analysis of Phase 21 data reveals two distinct failure modes and motivates alternative aggregation strategies.

**Failure mode 1: R4 destructive overrides.** Of 136 unanimous questions (R1=R2=R3), R4 changed the answer in 6 cases — all 6 destructive (correct consensus → wrong). R4 never successfully corrected a unanimous answer. A simple "majority-lock" rule (block R4 when R1-R3 are unanimous) recovers +3.0 pp over R4 (79.3% vs 76.3%).

**Failure mode 2: Anchoring degradation.** Gemini 3 Flash (82.3% solo) adopted GPT-4.1's wrong answer in 13 of 20 cases where Gemini flipped from correct to incorrect. GPT-4.1, as R1 proposer (66.2% solo), acts as a "persuasion anchor" — going first and dragging stronger models toward its errors.

**Voting strategy comparison** (computed from existing Phase 21 data, no additional API calls):

| Strategy | Correct | Accuracy | Description |
|----------|---------|----------|-------------|
| Oracle (any model correct) | 186 | 93.9% | Theoretical ceiling |
| **Grok-weighted MV** | **171** | **86.4%** | Grok wins ties; outvoted only by GPT+Gemini agreement |
| Solo Grok | 169 | 85.4% | Single strongest model |
| Non-Debate MV | 163 | 82.3% | Equal-weight majority vote |
| Majority-locked R4 | 157 | 79.3% | R4 blocked on unanimous questions |
| ARRIVAL MV | 156 | 78.8% | Standard debate MV |
| ARRIVAL R4 | 151 | 76.3% | Standard debate with R4 finalizer |

Grok-weighted MV (86.4%) outperforms all other strategies, including solo Grok (85.4%), by incorporating Gemini's and GPT-4.1's knowledge when they agree with Grok while protecting against their errors when they disagree. The 93.9% oracle ceiling confirms that the trio collectively possesses sufficient knowledge — the challenge is aggregation, not capability.

These findings motivate Phase 22: a confidence-gated debate protocol that uses independent answers first and triggers debate only on disagreements, eliminating the anchoring effect while preserving the ensemble's diversity benefit.

### 10.15 Phase 22: Confidence-Gated Debate — Full Results (198/198)

#### 10.15.1 Motivation

Phase 21 identified three specific failure mechanisms in sequential multi-agent debate:
1. **Anchoring bias**: GPT-4.1 (66.2% solo) as R1 Proposer contaminates stronger models. Gemini 3 Flash drops from 82.3% (solo) to 78.3% (in debate) — a 4.0 pp degradation.
2. **Destructive R4 overrides**: The R4 Finalizer changes correct group consensus to wrong answers more often than it rescues: 8 rescues vs 13 regressions (net −5). Of 6 attempts to override unanimous R1-R3 agreement, all 6 were destructive.
3. **False consensus**: Sequential exposure creates social pressure to agree with earlier speakers, reducing the effective diversity of the ensemble.

These findings motivated the design of Confidence-Gated Debate (CGD), a protocol variant that eliminates all three failure mechanisms.

#### 10.15.2 CGD Protocol

CGD operates in three phases:

**Phase 1: Independent Solo Answers.** All three models (GPT-4.1, Gemini 3 Flash, Grok 4.1 Fast) answer the question independently with a clean, minimal prompt. No model sees any other model's answer. Temperature = 0.3.

**Phase 2: Agreement Classification.** The three independent answers are classified into one of three patterns:

| Pattern | Name | Description | Action |
|---------|------|-------------|--------|
| 3/3 agree | Unanimous | All models converge | Accept immediately — no debate |
| 2/1 split | Split 2v1 | One model disagrees | Targeted debate: minority defends |
| 1/1/1 | Split 3-way | All different | Full debate: all defend |

**Phase 3: Targeted Debate** (conditional). For Split 2v1: the minority model writes a defense, the majority writes a rebuttal, then majority vote of all post-debate answers. For Split 3-way: all three models write defenses, then majority vote. **No R4 Finalizer** — the final answer is always majority vote.

#### 10.15.3 Results (198/198 Questions)

| Method | Correct | Total | Accuracy | 95% CI (Wilson) |
|--------|---------|-------|----------|-----------------|
| **CGD (Phase 22)** | **171** | **198** | **86.4%** | [80.9%, 90.5%] |
| Grok-weighted MV | 171 | 198 | 86.4% | [80.9%, 90.5%] |
| Solo Grok 4.1 Fast (Phase 21) | 169 | 198 | 85.4% | [79.8%, 89.6%] |
| Non-Debate MV (Phase 21) | 163 | 198 | 82.3% | [76.4%, 87.0%] |
| Solo Gemini 3 Flash (Phase 21) | 163 | 198 | 82.3% | [76.4%, 87.0%] |
| ARRIVAL MV (Phase 21) | 156 | 198 | 78.8% | [72.6%, 83.9%] |
| Solo GPT-4.1 (Phase 21) | 131 | 198 | 66.2% | [59.3%, 72.4%] |
| Oracle ceiling (any model correct) | 189 | 198 | 95.5% | [91.6%, 97.6%] |

**McNemar statistical tests:**

| Comparison | CGD wins | Loses | Net | χ² | p-value | Significant? |
|------------|----------|-------|-----|-----|---------|--------------|
| **CGD vs Non-Debate MV** | 14 | 6 | +8 | 3.20 | 0.074 | No (marginal) |
| **CGD vs ARRIVAL MV** | 24 | 9 | +15 | 6.82 | **0.009** | **Yes** |
| CGD vs Grok-weighted MV | 8 | 8 | 0 | 0.00 | 1.000 | No |

**Debate type breakdown:**

| Type | n | Correct | Accuracy | % of Questions |
|------|---|---------|----------|----------------|
| Unanimous | 122 | 117 | **95.9%** | 61.6% |
| Split 2v1 | 65 | 46 | 70.8% | 32.8% |
| Split 3-way | 11 | 8 | 72.7% | 5.6% |

**Domain breakdown:**

| Domain | n | CGD | Non-Debate MV | ARRIVAL MV | Solo Grok |
|--------|---|-----|---------------|------------|-----------|
| Physics | 86 | **95.3%** | 93.0% | 89.5% | 94.2% |
| Chemistry | 93 | **79.6%** | 75.3% | 71.0% | 80.6% |
| Biology | 19 | **78.9%** | 68.4% | 68.4% | 68.4% |

**Cost:** $5.72 for 198 questions ($0.029/question, 692 API calls).

#### 10.15.4 Minority-Was-Right Analysis

In 65 split_2v1 questions, the minority model was correct 15 times (23.1%). Per-model breakdown reveals asymmetric reliability: GPT-4.1 as minority is almost never correct (1/32 = 3%), while Grok (8/18 = 44%) and Gemini (6/15 = 40%) are correct as minority at substantial rates. 18 questions were lost when the correct minority answer was overridden by majority vote — these represent the theoretical ceiling for future model-weighted gating improvements.

#### 10.15.5 Extraction Failures

7 questions (3.5%) had extraction failures where a model returned no parseable answer (None). GPT-4.1 was responsible for 6 of 7 failures, Grok for 1, Gemini for 0. Five failures occurred in questions classified as "unanimous" despite only 2 valid votes. Accuracy excluding extraction bugs: 86.9% (166/191).

#### 10.15.6 Key Findings

1. **CGD achieves 86.4% on full GPQA Diamond** — the highest accuracy of any ARRIVAL-family method, surpassing solo Grok 4.1 (85.4%, +1.0 pp) and all multi-agent approaches. CGD vs ARRIVAL MV is statistically significant (McNemar p = 0.009).

2. **No anchoring**: By enforcing independent solo answers, CGD preserves each model's individual capability. Unlike sequential ARRIVAL (where Gemini dropped 4 pp), models in CGD maintain their solo-level performance.

3. **No R4 regressions**: Replacing the R4 finalizer with majority vote eliminates the net −5 destructive effect identified in Phase 21.

4. **Unanimous near-perfect (95.9%)**: When three independently queried frontier models converge on the same answer, they are almost always correct. Only 5 of 122 unanimous answers were wrong (shared misconceptions across all models).

5. **Cost-effective**: CGD is 17% more expensive than ARRIVAL ($0.029 vs $0.025/question) but 7.6 pp more accurate. 61.6% of questions resolve unanimously with only 3 API calls (no debate needed).

6. **Oracle gap**: CGD reaches 86.4% vs oracle ceiling 95.5% — a 9.1 pp gap. The minority-was-right analysis suggests model-weighted gating could recover up to 8 additional questions, potentially narrowing this gap to ~5 pp.

---

### 10.16 Phase 23: Scaled CGD with 7-Model Cross-Vendor Ensemble (CGD-7)

#### 10.16.1 Motivation

Phase 22 CGD achieved 86.4% with 3 models (Grok, Gemini, GPT-4.1). GPT-4.1 was the weakest link (66.2% solo, 6/7 extraction failures). Phase 23 tests whether **cross-vendor diversity** — scaling from 3 to 7 models from 5 vendors across 2 continents — improves CGD accuracy.

#### 10.16.2 Model Lineup (7 Models)

| # | Model | Vendor | Country | Solo (198q) |
|---|-------|--------|---------|-------------|
| 1 | Grok 4.1 Fast | xAI | US | **87.4%** |
| 2 | Gemini 3 Flash | Google | US | 82.8% |
| 3 | Claude Sonnet 4.6 | Anthropic | US | 80.8% |
| 4 | DeepSeek V3.2 | DeepSeek | CN | 74.7% |
| 5 | Kimi K2.5 | Moonshot AI | CN | 72.2% |
| 6 | GLM-5 | Zhipu AI | CN | 70.7% |
| 7 | Qwen3.5-397B | Alibaba | CN | 58.6% |

Thinking/reasoning was disabled for all Chinese models via OpenRouter `reasoning.enabled=false` to prevent thinking-token bloat.

#### 10.16.3 Protocol Modifications

CGD-7 adapts the Phase 22 protocol for 7 voters:
- **Lock threshold**: ≥5/7 agreement (71%) → no debate (previously 3/3 unanimous)
- **Simple majority**: 4/7 → minority (3 models) sees majority reasoning and may revise
- **No majority**: <4/7 → full debate, all 7 exchange reasoning
- **No R4 finalizer** (confirmed destructive in Phases 20--22)
- Weighted voting using 20-question calibration accuracy as weights

#### 10.16.4 Results (198 Questions)

| Method | Correct | Accuracy | Notes |
|--------|---------|----------|-------|
| **CGD-7** | **172/198** | **86.9%** | Primary result |
| Best solo (Grok 4.1) | 173/198 | 87.4% | Solo > ensemble |
| Simple MV (7 models) | 170/198 | 85.9% | Debate adds +1.0 pp |
| Phase 22 CGD (3 models) | 171/198 | 86.4% | Previous SOTA |
| Oracle (any of 7) | 191/198 | 96.5% | Diversity ceiling |

**McNemar test**: CGD-7 vs Phase 22 CGD: +0.5 pp, p = 1.0 (not significant). 11 questions gained, 10 lost.

#### 10.16.5 Cross-Vendor Diversity Analysis

| Group | Models | MV Accuracy | Oracle |
|-------|--------|-------------|--------|
| US (3) | Grok, Gemini, Claude | **86.9%** | 96.0% |
| CN (4) | Qwen, DeepSeek, GLM, Kimi | 76.3% | 88.4% |
| All 7 | Combined | 85.9% | **96.5%** |

Cross-vendor disagreement occurred on 40/198 = 20.2% of questions. US-only MV (3 models) matches CGD-7 (7 models) at 86.9%, indicating that adding 4 Chinese models provides no net accuracy benefit.

#### 10.16.6 Debate Type Analysis

| Type | N (%) | Accuracy | Description |
|------|-------|----------|-------------|
| Unanimous (7/7) | 105 (53%) | 99.0% | All agree → locked |
| Supermajority (6/7) | 23 (12%) | 82.6% | Near-consensus → locked |
| Strong majority (5/7) | 22 (11%) | 81.8% | Threshold → locked |
| Simple majority (4v3) | 21 (11%) | 66.7% | Minority debated |
| No majority | 27 (14%) | 63.0% | Full debate |

75.8% of questions locked without debate (≥5/7 agreement), achieving 93.3% accuracy. The 24.2% requiring debate averaged only 64.6%.

#### 10.16.7 Per-Domain Results

| Domain | N | CGD-7 | Best solo | Oracle |
|--------|---|-------|-----------|--------|
| Physics | 86 | **97.7%** | 97% (Grok) | — |
| Chemistry | 93 | 79.6% | 83% (Grok) | — |
| Biology | 19 | 73.7% | 79% (Claude) | — |

#### 10.16.8 Key Findings

1. **Quality > Quantity**: Scaling from 3 to 7 models yields only +0.5 pp (p = 1.0) when the additional models are substantially weaker (CN avg 69.1% vs US avg 83.7%).

2. **Solo beats ensemble**: Grok 4.1 solo (87.4%) outperforms CGD-7 (86.9%) at approximately 1/8 the cost ($1.50 vs $11.35). This establishes a ceiling on the value of debate-based aggregation when model quality varies widely.

3. **Oracle gap remains large**: The 96.5% oracle ceiling proves the 7-model ensemble collectively knows the answer to 191/198 questions. The challenge shifts from "add more models" to "extract collective knowledge more effectively."

4. **Extraction failures dominate weak models**: Qwen3.5-397B had 54 extraction failures (27% of questions), dragging its effective accuracy to 58.6%. Reliable answer extraction is a prerequisite for effective ensemble participation.

5. **Cross-vendor diversity increases oracle but not accuracy**: Adding Chinese models raises oracle from 96.0% (US-only) to 96.5% (+0.5 pp) but provides zero MV accuracy improvement.

6. **Cost**: $11.35 total (1,822 API calls, 4.4M tokens), cost per correct answer = $0.066.

#### 10.16.9 Ablation: Weighting, Pruning, and Poisoned Voters

**Weighted vs. Simple Voting**: Weighting models by calibration accuracy *hurts* performance: Weighted MV (85.4%) < Simple MV (85.9%) < CGD-7 (86.9%). The weighting scheme amplifies Grok's dominance (87.4% solo) while suppressing diversity signals from weaker models that occasionally contribute correct minority answers.

**Subset Pruning (WMV+D-3)**: Dropping the 3 weakest Chinese models (Qwen3.5-397B, GLM-5, Kimi K2.5) and running weighted MV on the remaining 4 models yields **88.4%** (175/198) — the highest accuracy achieved in any aggregation condition. This confirms that model quality dominates quantity: a curated 4-model subset outperforms the full 7-model ensemble.

**Poisoned Voter Analysis**: Qwen3.5-397B exhibits pathological minority behavior:

| Model | Minority Count | Minority Correct | Rate |
|-------|---------------|-----------------|------|
| Grok 4.1 Fast | 20 | 10 | **50%** |
| Gemini 3 Flash | 27 | 9 | 33% |
| Claude Sonnet 4.6 | 22 | 4 | 18% |
| Kimi K2.5 | 23 | 3 | 13% |
| **Qwen3.5-397B** | **22** | **1** | **5%** |

Qwen's minority dissent is almost never correct (5%), combined with 54 extraction failures (27%). It functions as a **poisoned voter** — a model whose dissent reliably indicates the *wrong* answer. This suggests a model quality threshold below which ensemble participation is harmful.

**CGD invariance to ensemble size**: CGD-7 (86.9%) ≈ Phase 22 CGD-3 (86.4%), p = 1.0. The agreement-gating mechanism adapts automatically to different ensemble sizes, maintaining performance by locking questions where supermajority agrees and focusing debate resources on genuinely contested questions.

**Thinking mode as hidden variable**: US models averaged 83.7% solo accuracy vs 69.1% for Chinese models — a 14.6 pp gap. However, thinking/reasoning was disabled for all Chinese models (to prevent token bloat), making this comparison confounded. The thinking mode may account for a substantial portion of the US-CN gap, and Phase 23 results should not be interpreted as evidence of inherent architectural inferiority.

---

## 11. Results: Applied Tasks (Phase 18)

### 11.1 Motivation

Phases 13--17 evaluate ARRIVAL on multiple-choice benchmarks (GPQA Diamond). Phase 18 extends validation to **practical software engineering tasks**, testing whether the protocol provides value on real-world analytical and constructive work. This addresses the limitation (acknowledged in Section 16) that MCQ-only evaluation may not generalize.

### 11.2 Experimental Design

Three conditions are compared on two tasks:

| Condition | Description | Models | API Calls |
|-----------|-------------|--------|-----------|
| **A: Solo** | Single frontier model | Claude Sonnet 4.5 ($3/$15 per 1M) | 1 |
| **B: ARRIVAL** | 5-model heterogeneous swarm | GPT-4.1, DeepSeek V3.2, Mistral Large 3, Gemini 3 Flash, Grok 4.1 Fast | 11 |
| **C: ARRIVAL+Mem** | Same swarm + CARE-ALERT memory | Same 5 models + pre-seeded ARRIVAL-MNEMO | 11 |

The three-condition design enables **layered decomposition**: A-to-B isolates the protocol coordination effect; B-to-C isolates the memory effect.

The ARRIVAL swarm uses the standard 4-round protocol (R1: independent analysis, R2: cross-critique, R3: CRDT overlay, R4: Alpha synthesis). All models accessed via OpenRouter.

### 11.3 Task 1: Security Audit (Analytical)

A Flask web application with **10 intentional vulnerabilities** (SQL injection, IDOR, race condition, off-by-one, inverted sort, XSS, secret leak, Unicode corruption, integer overflow, bare except) plus 2 bonus issues (weak hashing, debug mode). Ground truth is fixed; evaluation is keyword-based detection.

| Metric | A: Solo | B: ARRIVAL | C: ARRIVAL+Mem |
|--------|---------|-----------|----------------|
| **Bugs Found** | **10/10** | **10/10** | **10/10** |
| Bonus Issues | 2/2 | 2/2 | 2/2 |
| Total Tokens | 11,130 | 94,534 | 93,674 |
| **Total Cost** | **$0.1196** | **$0.1398** | **$0.1401** |
| CARE Resolve | N/A | 0.500 | 0.500 |
| Memory Injected | N/A | No | Yes (6 memories) |

All three conditions found 100% of bugs. The task exhibited a ceiling effect. However, the key finding is **cost parity**: the 5-model ARRIVAL swarm costs only 17% more than a single Claude Sonnet 4.5 call ($0.14 vs $0.12) while providing 5 independent perspectives and full per-model audit trails.

CARE Resolve of 0.500 correctly triggered CARE-ALERT memory injection in Condition C: models agreed on bug identification but diverged on severity and remediation.

### 11.4 Task 2: Code Generation (Constructive)

Implement a REST API (FastAPI) for task management from specification. Evaluated by 15 objective pytest tests (CRUD, filtering, pagination, sorting, search, error handling).

| Metric | A: Solo | B: ARRIVAL | C: ARRIVAL+Mem |
|--------|---------|-----------|----------------|
| **Tests Passed** | **9/15 (60%)** | **8/15 (53%)** | **7/15 (47%)** |
| Code Lines | 259 | 180 | 166 |
| Total Tokens | 8,595 | 67,432 | 64,037 |
| **Total Cost** | **$0.1241** | **$0.1274** | **$0.1228** |
| CARE Resolve | N/A | 0.979 | 0.973 |
| Memory Injected | N/A | No | No (CARE > 0.7) |

Solo achieves a narrow advantage (+1-2 tests) on code generation, which is expected: single-context models maintain coherent implementation state that is partially lost during swarm synthesis. Despite this, **all three conditions cost the same** ($0.12-0.13), and CARE correctly suppressed memory injection (CARE ~0.97 indicates strong consensus).

### 11.5 CARE Resolve as Task Discriminator

| Task Type | CARE Resolve | Memory Injected | Interpretation |
|-----------|-------------|-----------------|----------------|
| Analytical (audit) | 0.500 | Yes | Models diverge on subjective judgments |
| Constructive (code) | 0.973 | No | Models converge on structured output |

CARE quantitatively distinguishes task types. Low CARE signals that diverse perspectives add value (analytical work); high CARE signals that models naturally converge (constructive work). This has practical implications for adaptive orchestration: a system could dynamically adjust the number of rounds or models based on CARE.

### 11.6 Key Contribution: Five Models Match One Frontier Model

The central finding of Phase 18: a heterogeneous swarm of 5 models coordinated via ARRIVAL **matches Claude Sonnet 4.5** at comparable cost. This provides:

1. **Vendor independence** — no single-provider dependency
2. **Fault tolerance** — if one model degrades, 4 others compensate
3. **Full transparency** — every model's reasoning is logged per round
4. **Architecture diversity** — 5 different training pipelines reduce correlated errors

---

## 12. Results: Memory and CARE-ALERT (Phases 14--15)

### 12.1 The Hypercorrection Paradox (Phase 14)

Phase 14 tested ARRIVAL-MNEMO, a persistent memory architecture with 4 layers (Episodic, Procedural, Semantic, Meta), using cognitive scars extracted from Phase 13 errors.

**Result**: Global memory injection *degraded* accuracy by **-5.7 percentage points** compared to baseline ARRIVAL. This hypercorrection effect occurs when past errors overly constrain current reasoning, causing agents to avoid patterns superficially similar to previous mistakes even when those patterns are correct.

### 12.2 Gated CARE-ALERT (Phase 15)

To address hypercorrection, Phase 15 introduced gated memory intervention. Instead of injecting all memories globally, the system monitors Meaning Debt in real time and fires `@CARE.ALERT` atoms *only* when semantic divergence exceeds a threshold:

- **After Round 2**: MD > 0.5 triggers a gentle alert
- **After Round 3**: MD > 0.8 triggers an urgent alert

**Result**: Gated CARE-ALERT restored baseline accuracy while significantly improving CARE Resolve quality (Mann-Whitney U test, p = 0.042). This is the first statistically significant improvement from memory intervention in multi-agent LLM coordination.

The hypercorrection-then-gating discovery has broader implications: naive augmentation of LLM systems (whether with memory, tools, or additional context) can be counterproductive. Monitoring internal coordination metrics (like Meaning Debt) provides a principled mechanism for knowing *when* to intervene.

---

## 13. Results: Framework-Agnostic Validation (AutoGen)

To demonstrate that the ARRIVAL Protocol is not implementation-specific, we ported it to Microsoft's AutoGen framework (AG2) using custom `ARRIVALAgent` and `ARRIVALGroupChat` wrappers.

Across 16 experiments (basic MCQ, adversarial saboteur, and cross-framework comparison), the AG2 implementation achieved **100% behavioral match** with the reference implementation:
- Identical answer extraction
- Identical atom detection
- Equivalent CARE Resolve scores (within floating-point tolerance)

Total cost: $0.024 USD.

This confirms that the ARRIVAL Protocol's effectiveness comes from the protocol structure (atoms, rounds, CRDT math) rather than implementation details, enabling deployment on any multi-agent framework.

---

## 14. Results: GovSim Harvest Negotiation (Phase 19)

### 14.1 Motivation: The Tragedy of the Commons in LLMs

GovSim (Piatti et al., NeurIPS 2024) demonstrated that 12 of 15 LLM models achieve **0% survival** in a shared resource management game. La Malfa et al. (2025) identified three structural causes: no native social behavior, ambiguous natural-language communication, and no quantitative emergence metrics. FAIRGAME (Buscemi et al., 2025) further showed end-game defection and cross-linguistic instability.

Phase 19 tests whether ARRIVAL Protocol's structured @-atoms and CRDT metrics can solve this cooperation problem.

### 14.2 Experimental Design

**Game**: Fish pond commons (initial stock=100, 5 agents, 12 months). Replenishment: min(2 × remaining, max_capacity). Collapse: stock < 5 after harvesting. Fair share = 19 fish.

**Models**: GPT-4.1 (alpha/conservative), DeepSeek V3.2 (beta/skeptic), Mistral Large 3 (gamma/creative), Gemini 3 Flash (delta/rule-based), Grok 4.1 Fast (epsilon/mediator). All accessed via OpenRouter.

**Conditions**: (A) Baseline — minimal prompts, no coordination. (B) ARRIVAL — 4-round protocol with @HARVEST/@ALLOCATION atoms + CRDT metrics. (C) ARRIVAL+Memory — ARRIVAL plus CARE-ALERT memory injection when CARE < 0.5.

**Scale**: N=3 runs per condition, seeds=[42, 137, 256]. Total: 870 API calls, $2.31.

### 14.3 Results

| Condition | Survival | Avg Months | CARE avg | Gini | Cost |
|-----------|----------|------------|----------|------|------|
| A: Baseline | **0/3 (0%)** | 4.3 | N/A | 0.173 | $0.03 |
| B: ARRIVAL | **3/3 (100%)** | 12.0 | 0.969 | 0.001 | $1.14 |
| C: ARRIVAL+Mem | **3/3 (100%)** | 12.0 | 0.972 | 0.000 | $1.14 |

Statistical tests: Fisher exact (A vs B) p = 0.10, Mann-Whitney U (months) p = 0.064. With N=3, Fisher cannot reach p < 0.05 for 0-vs-3; with N=5 the same pattern yields p = 0.004.

### 14.4 Key Findings

1. **0% → 100% survival**: The baseline replicates GovSim's finding even with 2025--2026 frontier models. ARRIVAL solves it completely via structured @-atoms and binding R4 allocation.

2. **Self-healing**: Greedy proposals (Delta=50, Gamma=30, Delta=100) are neutralized within 1 month by R2 cross-critique. The most extreme: Delta proposes @HARVEST=100 (maximum greed, attempting to take the entire resource), corrected to 10 by R2+R4. CARE drops to 0.95 and recovers to 1.000 within 1--2 months, confirming Theorem 5 (exponential convergence under CARE iteration).

3. **Perfect equality**: Gini coefficient → 0.000 under ARRIVAL (vs 0.173 baseline). Cumulative harvests equalized across all agents within ±2 fish per run.

4. **3.2× resource extraction**: ARRIVAL harvests ~640 fish vs ~200 (baseline collapse), demonstrating that cooperation is not just altruistic but economically superior.

5. **Memory correctly suppressed**: 0/36 CARE-ALERT injections across Condition C. CARE consistently exceeded the 0.5 threshold, confirming that for cooperation tasks, the protocol is self-sufficient. This validates CARE as a task discriminator: analytical tasks (Phase 18, CARE ~0.50) need memory; cooperation tasks (Phase 19, CARE ~0.97) do not.

### 14.5 Theoretical Implications

Phase 19 provides empirical support for MEANING-CRDT v1.1 theorems:
- **Theorem 1** (CARE optimum): Equal allocation emerges as the CARE-optimal solution when all agents have equal weight.
- **Theorem 5** (Exponential convergence): After greedy perturbations, CARE recovers to equilibrium within 1--2 rounds.
- **Theorem 6** (Bounded Meaning Debt): MD never exceeds 0.008 across 108 monthly measurements, far below the alarm threshold.
- **Theorem 8** (Incentive incompatibility): Greedy agents cannot game CARE — extreme proposals (Delta=100) are detected and corrected.

---

## 15. Discussion

### 15.1 What ARRIVAL Adds Beyond Strong Prompting

The strongest challenge to multi-agent systems comes from Wang et al. (2024): can single-agent CoT match multi-agent performance? Our Phase 17 (N=40) showed Solo CoT at 70.0% vs ARRIVAL at 65.0% (Fisher p = 0.812, ns). Phase 20 scales this comparison to the full 198-question GPQA Diamond: ARRIVAL R4 achieves 66.7% vs Solo CoT MV at 62.1% (McNemar p = 0.233, ns). Phase 21 escalates further with frontier-tier models (GPT-4.1, Gemini 3 Flash, Grok 4.1 Fast): Non-Debate MV reaches 82.3% vs ARRIVAL MV at 78.8% (McNemar p = 0.265, ns). The debate effect inverts — from slightly positive with mid-tier models to slightly negative with frontier models — confirming that **structured debate on MCQ benchmarks adds noise, not signal, when models are individually capable.** Nevertheless, ARRIVAL provides additional value beyond raw accuracy:

1. **Structured reasoning traces**: The atom-based protocol produces machine-parseable coordination logs, enabling post-hoc analysis of *how* consensus was reached, not just *what* answer was produced.

2. **Error detection**: Structured peer review catches errors that escape individual reasoning, though Phases 20 and 21 consistently show the R4 finalizer is net negative (Phase 20: 9 regressions vs 7 rescues; Phase 21: 13 regressions vs 8 rescues), suggesting majority voting is more robust than sequential synthesis.

3. **Formal guarantees**: MEANING-CRDT provides mathematical bounds on consensus quality, convergence speed, and adversarial robustness that cannot be stated for single-agent prompting.

4. **Scalability**: The protocol scales to N agents with formal convergence guarantees (Theorem 5), while single-agent approaches require entirely different strategies for scaling.

5. **Protocol evolution**: Phase 22's Confidence-Gated Debate (CGD) demonstrates that the failure analysis from Phases 20-21 was itself productive. By identifying anchoring and R4 regressions as the primary failure mechanisms, we designed a protocol variant that eliminates both — achieving **86.4% accuracy** (171/198 questions, 95% CI: [80.9%, 90.5%]), the highest in the project. This trajectory from negative results to protocol innovation illustrates the value of rigorous empirical methodology with honest reporting of failures.

### 15.2 CARE Metric Sensitivity

CARE Resolve depends on heuristic weight extraction from LLM confidence declarations. Reclassifying atoms shifts CARE by +0.04 to +0.047, a modest but non-negligible sensitivity. We recommend treating CARE as a Level 2 (instrumental) metric rather than a Level 1 (hard) outcome measure. The primary evaluation should always be task accuracy with proper statistical testing.

### 15.3 Goodhart's Law Risk

If CARE is used as an optimization target rather than a diagnostic tool, agents could learn to produce high-CARE outputs without improving reasoning quality. We deliberately do not optimize for CARE; it serves only as a coordination quality indicator.

### 15.4 Cost-Efficiency

At under $95 for ~14,500 API calls across 23 phases and 17 architectures, ARRIVAL demonstrates exceptional cost-efficiency. Phase 20 (full GPQA Diamond, 198 questions) cost $7.43 total; Phase 21 (strong trio, 198 questions) cost $9.63 total across all conditions (ARRIVAL + 3 solo baselines). Phase 22 CGD cost $5.72 for 198 questions; Phase 23 (7-model CGD) cost $11.35. Multi-agent coordination overhead is negligible at ~$0.012--$0.057 per question.

Phase 18 provides a striking cost-efficiency result: a 5-model heterogeneous swarm (GPT-4.1 + DeepSeek V3.2 + Mistral Large 3 + Gemini 3 Flash + Grok 4.1 Fast) performing 11 API calls costs only 8-10% more than a single Claude Sonnet 4.5 call. This challenges the assumption that multi-agent systems are inherently more expensive.

Phase 22 CGD is cost-efficient: $5.72 for 198 questions (~$0.029/question), cheaper than standard ARRIVAL ($0.039/q in Phase 20) because 61.6% of questions are resolved unanimously with only 3 API calls (no debate). The agreement-based gating provides a natural cost optimization: debate resources are allocated only where genuine disagreement exists.

### 15.5 CARE as an Adaptive Coordination Signal

Phase 18 reveals a previously unobserved property of CARE Resolve: it discriminates between task types. Analytical tasks (security audit) produce low CARE (~0.50), indicating genuine disagreement on subjective assessments. Constructive tasks (code generation) produce high CARE (~0.97), reflecting convergence on well-defined implementation patterns.

This suggests CARE could serve as an adaptive coordination signal: systems could dynamically adjust orchestration strategy (number of rounds, model selection, memory injection) based on real-time CARE measurements.

### 15.6 CGD: From Failure Analysis to Protocol Innovation

Phase 22's Confidence-Gated Debate (CGD) emerged directly from the failure analysis of Phases 20-21. Three problems were identified: (1) anchoring bias from sequential exposure to weaker models' answers, (2) destructive R4 overrides (net -5 in Phase 21: 8 rescues vs 13 regressions), and (3) false consensus from social pressure in sequential debate. CGD addresses all three by design: independent solo answers eliminate anchoring, majority vote replaces R4, and agreement-based gating replaces unconditional debate.

This approach is theoretically grounded in the Condorcet Jury Theorem: independent voters with individual accuracy > 50% produce better collective decisions than correlated voters. CGD operationalizes this by ensuring independence in the solo phase and using correlation (agreement) only as a gating signal.

Recent work supports this design rationale. Choi et al. (2025) prove that multi-agent debate has a "martingale property" — debate does not change the expected correctness of responses, only their variance. This aligns with our Phase 21 finding that debate is net zero on MCQ accuracy. CGD sidesteps this limitation by reserving debate for cases of genuine disagreement, where the variance reduction from debate is most valuable.

CGD differs from other gating approaches in the literature. Fan et al. (2026) propose iMAD, which uses ML-trained confidence classifiers to decide when to debate — requiring labeled training data. Eo et al. (2025) examine whether natural language is the optimal medium for debate (DOWN). CGD uses a simpler, zero-shot gating mechanism: inter-model agreement, which requires no training and is inherently reliable because it aggregates three independent signals rather than relying on a single model's self-reported confidence (which LLMs are known to miscalibrate).

The results are striking: **86.4% accuracy** (171/198, 95% CI: [80.9%, 90.5%]) with three mid-tier models (GPT-4.1 66.2%, Gemini 3 Flash 82.3%, Grok 4.1 Fast 85.4%) approaches the frontier single-model SOTA on GPQA Diamond (Gemini 3.1 Pro 94.1%, as reported by Google, 2025). This suggests that principled ensemble aggregation with mid-tier models can approximate frontier performance at substantially lower per-query cost — a finding with significant practical implications for cost-sensitive applications.

### 15.7 Quality Threshold and Non-Monotonic Scaling

Phase 23 reveals a non-monotonic relationship between ensemble size and accuracy: scaling from 3 to 7 models yields only +0.5 pp (p = 1.0), while the pruned 4-model subset (WMV+D-3) achieves the project-high 88.4%. This suggests the existence of a **quality threshold** below which models become net negative ensemble participants. Qwen3.5-397B exemplifies this: with 5% minority-correct rate and 27% extraction failures, its votes are anti-informative.

This finding connects to the Condorcet Jury Theorem's requirement that individual voters have accuracy > 50%. While all 7 models exceed this threshold on average, their effective accuracy on *contested questions* (where votes matter) may fall below 50% for weak models. The implication for ensemble design is clear: a smaller set of high-quality, diverse models outperforms a larger set diluted by weak participants. Model selection is more important than model count.

The WMV+D-3 result (88.4%) also establishes an important benchmark: with the right model selection and aggregation strategy, mid-tier models can approach within 6 pp of frontier single-model SOTA (Gemini 3.1 Pro 94.1%) at a fraction of the cost.

### 15.8 Thinking Mode as Hidden Variable

The US-CN accuracy gap in Phase 23 (83.7% vs 69.1%) is confounded by the systematic disabling of thinking/reasoning modes for all Chinese models. This was a practical necessity (preventing thinking-token bloat that exceeds context windows) but constitutes a significant experimental confound.

DeepSeek V3.2, for example, is known to benefit substantially from its reasoning mode. Kimi K2.5 and GLM-5 also have reasoning capabilities that were suppressed. The 14.6 pp gap should therefore **not** be interpreted as evidence of inherent architectural differences between US and Chinese LLMs. A properly controlled comparison would require either enabling reasoning for all models or disabling it for all — but the former is impractical due to heterogeneous thinking-token implementations.

This highlights a broader challenge for cross-architecture ensemble research: models are not directly comparable when run under different inference configurations. Future work should systematically ablate thinking mode effects, potentially developing standardized inference configurations that enable fair cross-architecture comparison.

---

## 16. Limitations

We acknowledge the following limitations:

1. **Limited open-ended evaluation**: Phases 4--17 use multiple-choice questions. Phase 18 extends to security audit and code generation. Phase 19 validates on a game-theoretic cooperation task, but broader tasks (creative writing, mathematical proof, long-form reasoning) remain untested.

2. **Small N in early phases**: Phase 4 used N=3 agents per condition. Phase 19 uses N=5, yielding Fisher p=0.008 (significant at 0.01 level).

3. **Model version floating**: OpenRouter routes to the latest available model version, which may change between experiments. Results may not be exactly reproducible if model versions differ.

4. **CARE heuristic dependency**: Weight extraction from confidence declarations is heuristic-based. Different heuristics could produce different CARE scores.

5. **Debate effect null or negative on MCQ**: Phase 20 (N=198) shows ARRIVAL +5.6 pp vs Solo CoT (p=0.233, ns); Phase 21 (N=198, strong models) shows ARRIVAL −3.5 pp vs Non-Debate MV (p=0.265, ns). With frontier models, debate slightly degrades accuracy due to anchoring — strong models abandon correct answers after seeing weak proposals.

6. **No social agency**: Following La Malfa et al. (2025), we acknowledge that LLM agents in our system do not possess genuine social agency; their coordination is mediated entirely through prompt injection.

7. **Homogeneous ensemble caveat**: Phase 16's strong result uses 5 copies of the same model with different personas. This may overstate the benefit compared to truly diverse reasoning systems.

8. **Phase 18 N=1**: Applied experiments use a single run per condition without repeated trials. Results are indicative but not statistically robust.

9. **Code synthesis limitation**: ARRIVAL's 4-round protocol incurs coherence loss during synthesis (R4), which disadvantages it on code generation tasks where a single coherent context window is beneficial.

10. **Single game type**: Phase 19 tests only on fish pond commons. Other cooperation games (public goods, prisoner's dilemma, ultimatum) may show different results.

11. **No adversarial agents**: Phase 19 models are instructed with cooperative personas. Truly adversarial agents (e.g., RL-trained defectors) would constitute a stronger test.

12. **CGD limited scope**: CGD has been tested on MCQ with K=3 (Phase 22) and K=7 (Phase 23) models. While Phase 23 confirms robustness across ensemble sizes, generalization to non-MCQ tasks and cooperation scenarios remains untested.

---

## 17. Conclusion and Future Work

We presented the ARRIVAL Protocol, demonstrating that structured semantic communication enables multi-agent LLM coordination across standardized benchmarks, practical tasks, and game-theoretic cooperation scenarios. The key results:

- **Phase 20 (full GPQA Diamond, N=198, mid-tier models)**: ARRIVAL MV achieves 67.7% vs Solo CoT 62.1% (+5.6 pp, McNemar p = 0.233, ns). Domain-dependent: +21 pp in Biology, +6 pp in Chemistry.
- **Phase 21 (full GPQA Diamond, N=198, frontier models)**: Non-Debate MV (82.3%) outperforms ARRIVAL MV (78.8%) by 3.5 pp (McNemar p = 0.265, ns). Debate effect inverts with strong models due to anchoring degradation (Gemini −4 pp in debate).
- **Phase 13 (N=40)**: ARRIVAL 63.8% vs MV 42.5% (McNemar p = 0.006), significant on the original small sample.
- The hypercorrection-then-gating discovery (Phases 14--15)
- Phase 18: 5 heterogeneous models match a frontier solo model at comparable cost
- **Phase 19: 0% → 100% survival in GovSim commons game** (Fisher p = 0.008) — the first demonstration of a structured multi-agent protocol solving the tragedy of the commons for LLMs
- **Phase 22 (CGD, N=198)**: Confidence-Gated Debate achieves **86.4% accuracy** (171/198, 95% CI: [80.9%, 90.5%]) — independent solo answers + agreement-based gating + targeted debate eliminates anchoring and R4 regressions. Exceeds ARRIVAL MV (78.8%, +7.6 pp, McNemar p = 0.009) and Non-Debate MV (82.3%, +4.1 pp). Resolves 61.6% of questions unanimously (95.9% accuracy). Approaches the oracle ceiling (93.9%) within 7.5 pp.
- **Phase 23 (CGD-7, N=198)**: Scaling CGD to 7 cross-vendor models (3 US + 4 Chinese) yields **86.9%** (172/198), a marginal +0.5 pp over 3-model CGD (p = 1.0, ns). Best individual model (Grok 4.1 Fast, 87.4%) outperforms the ensemble — demonstrating quality > quantity for MCQ. Oracle ceiling of 96.5% shows cross-vendor diversity contains recoverable signal.

The honest picture: standard sequential ARRIVAL does not significantly outperform solo models on MCQ benchmarks at scale — and with frontier-tier models (Phase 21), debate slightly hurts accuracy via anchoring. However, Phase 22's Confidence-Gated Debate (CGD) demonstrates that the failure analysis itself was productive: eliminating anchoring (via independent solo phase) and removing R4 (via majority vote) yields **86.4% accuracy** (171/198) — the highest in the project. Phase 23 extends CGD to 7 cross-vendor models (86.9%), confirming robustness but revealing non-monotonic scaling: quality dominates quantity for MCQ. ARRIVAL's primary value lies in cooperative multi-agent scenarios (GovSim: 0% → 100% survival), transparency, consensus measurement, vendor independence, and — through CGD — a principled approach to ensemble aggregation that outperforms both debate and naive voting.

The MEANING-CRDT v1.1 mathematical framework provides the first formal foundation for semantic conflict resolution in LLM ensembles, with proven convergence, bounded debt, and Bayesian equivalence properties. Phase 19 provides empirical confirmation of Theorems 1, 5, 6, and 8 in a game-theoretic setting. The 7 echo-chamber metrics offer the research community a quantitative toolkit for detecting social conformity. CARE Resolve emerges as both a consensus quality metric and a task-type discriminator, with practical applications for adaptive orchestration.

### Future Work

1. **Extend CGD to additional benchmarks**: CGD achieves 86.4% on GPQA Diamond (198 questions). Extension to applied tasks (security audit, code generation), cooperation games (GovSim), and other reasoning benchmarks (MMLU-Pro, ARC-Challenge, MedQA) should test whether agreement-based gating generalizes beyond MCQ.
2. **CGD extensions**: Explore K > 3 models, weighted confidence in the gating decision, and hybrid protocols that combine CGD's independent solo phase with ARRIVAL's structured @-atom debate for the targeted debate phase.
3. **Broader cooperation games**: Phase 19 validates on fish pond commons; public goods games, prisoner's dilemma, and ultimatum games would strengthen the cooperation claim.
4. **Adversarial cooperation agents**: Test ARRIVAL against RL-trained defectors (cf. Piche et al., 2025) rather than LLMs with cooperative personas.
5. **R4 trust mitigations**: Rotating synthesizer selection, multi-agent R4 voting, fairness clamps to address the single-point-of-trust vulnerability identified in Condition E.
6. **Scaling laws**: Systematic study of accuracy vs. number of agents, building on Phase 9 (N=5, N=7).
7. **Adaptive orchestration**: Use real-time CARE measurements to dynamically adjust the number of rounds, model selection, and memory injection strategy.
8. **Online memory**: Extend ARRIVAL-MNEMO from pre-seeded to online learning from cross-session coordination patterns.
9. **Larger N for MCQ**: Power analysis from Phase 20 suggests N ≈ 600 questions to detect a 5 pp effect at 80% power. Cross-benchmark evaluation (MMLU-Pro, ARC-Challenge, MedQA) would provide the necessary statistical power.
10. **CGD vs frontier SOTA**: With three mid-tier models, CGD (86.4%) approaches frontier single-model performance (Gemini 3.1 Pro 94.1%). Systematic comparison of CGD cost-accuracy tradeoffs against frontier models would quantify the practical value of ensemble methods.

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

15. Piatti, G., et al. (2024). GovSim: Governance of the Commons Simulation with Language Agents. *NeurIPS 2024*. arXiv:2404.13753

16. Buscemi, A., et al. (2025). FAIRGAME: Fairness in Language Game-Theoretic LLM Multi-Agent Interactions.

17. Piche, A., et al. (2025). Robust Social Strategies for Multi-LLM Agents.

18. Akata, E., et al. (2023). Playing Repeated Games with Large Language Models. arXiv:2305.16867

19. Kelevra, M. (2026). MEANING-CRDT v1.1: Conflict-Free Replicated Data Types for Meaning Negotiation. *Zenodo*. DOI: 10.5281/zenodo.18702383

20. Curvo, R., et al. (2025). GovSim Reproducibility Report: Validating Cooperation Failures in LLM Agent Societies.

21. Choi, H. K., Zhu, X., & Li, S. (2025). Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models? *NeurIPS 2025 (Spotlight)*. arXiv:2508.17536

22. Fan, X., et al. (2026). iMAD: Informed Multi-Agent Debate with Confidence-Aware Gating. *AAAI 2026*.

23. Kaesberg, J., et al. (2025). The Subtle Art of Defection: Investigating LLMs' Failure to Avoid Tragedy of Commons. *ACL 2025*.

24. Wu, H., Li, Z., & Li, L. (2025). Can LLM Agents Really Debate? A Controlled Study of Multi-Agent Debate in Logical Reasoning. arXiv:2511.07784

25. Eo, T., et al. (2025). DOWN: Debate ON Whether to use Natural Language as Intermediate in Multi-Agent Debate. arXiv preprint.

26. Hintze, A. & Adami, C. (2026). Cooperation Emerges at the Tipping Point of LLM Capabilities. *npj Complexity* 2026.

27. SanctSim Authors. (2025). SanctSim: Simulating the Effects of Sanctions in Multi-Agent LLM Systems.

28. Gemini Team, Google. (2025). Gemini 3.1 Technical Report.

29. Kaesberg, L. B., Becker, J., Wahle, J. P., Ruas, T., & Gipp, B. (2025). Voting or Consensus? Decision-Making in Multi-Agent Debate. *Findings of the ACL 2025*, pp. 11640--11671. arXiv:2502.19130

30. Wang, C., Lin, H., Tang, H., Lin, H., & Ding, W. (2026). RUMAD: Reinforcement-Unifying Multi-Agent Debate. *Proc. AAMAS 2026*. arXiv:2602.23864

31. Zhou, Y. & Chen, Y. (2025). Adaptive Heterogeneous Multi-Agent Debate for Enhanced Educational and Factual Reasoning in Large Language Models. *Journal of King Saud University — Computer and Information Sciences*, 37(10), 330. DOI:10.1007/s44443-025-00353-3

32. Chen, J. C.-Y., Saha, S., & Bansal, M. (2024). ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs. *ACL 2024*. arXiv:2309.13007

33. Ai, R., Pan, Y., Simchi-Levi, D., Tambe, M., & Xu, H. (2025). Beyond Majority Voting: LLM Aggregation by Leveraging Higher-Order Information. arXiv:2510.01499

34. Kostka, A. & Chudziak, J. A. (2026). Evaluating Theory of Mind and Internal Beliefs in LLM-Based Multi-Agent Systems. arXiv:2603.00142

---

## Appendices

### Appendix A: DEUS.PROTOCOL v0.5 Atom Dictionary

See `docs/ATOM_DICTIONARY.md` for the complete specification of all 66 atoms with usage examples and adoption statistics.

### Appendix B: MEANING-CRDT v1.1 Theorem Proofs

See `docs/math/MEANING-CRDT_v1.1.md` for detailed proofs and derivations.

### Appendix C: Experiment Logs and Reproducibility

All experiment configurations, API logs, and result files are available in the `experiments/` and `results/` directories. Total cost: under $95 USD across 2,200+ experiments and ~14,500 API calls. See `docs/setup/SETUP_EN.md` for reproduction instructions.
