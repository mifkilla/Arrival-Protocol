# ARRIVAL Protocol: Structured Semantic Coordination Enables Sustainable Cross-Architecture AI Cooperation

**Mefodiy Kelevra**
ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)

**March 2, 2026**

**DOI**: [10.5281/zenodo.18893515](https://doi.org/10.5281/zenodo.18893515)
**Mathematical Foundation DOI**: [10.5281/zenodo.18702383](https://doi.org/10.5281/zenodo.18702383) (MEANING-CRDT v1.1)
**License**: CC BY-NC 4.0 (text), AGPL-3.0-or-later (code)
**Repository**: https://github.com/DreamOS-Network/Arrival-Protocol

**Keywords**: multi-agent systems, LLM coordination, CRDT, semantic atoms, cooperation, tragedy of the commons, GovSim, GPQA, echo chamber, adversarial robustness, CARE Resolve, Meaning Debt, confidence-gated debate, CGD, agreement gating

---

## Abstract

We present the ARRIVAL Protocol (Atomic Reasoning via Rival Validation and Adversarial Logic), a structured communication framework enabling AI-to-AI coordination across heterogeneous large language model (LLM) architectures without fine-tuning, shared weights, or prior joint training. The protocol employs 66 semantic @-atoms, injected via system prompts, to establish a shared coordination vocabulary that replaces ambiguous natural-language debate with machine-parseable structured communication.

Across **2,200+ experiments** organized into **23 phases** involving **17 distinct LLM architectures**, we report the following principal findings:

**Reasoning benchmarks.** On the GPQA Diamond graduate-level science benchmark (N=40), ARRIVAL achieves 65.0% accuracy with a 5-agent homogeneous Qwen3-235B ensemble (Phase 16), compared to 52.5% for majority voting (+12.5 pp, McNemar p = 0.006). Scaling to the **full 198-question GPQA Diamond** with mid-tier models (Phase 20), ARRIVAL MV achieves **67.7%** vs Solo CoT majority vote at **62.1%** (+5.6 pp, McNemar p = 0.233, ns). With **frontier-tier models** (Phase 21: GPT-4.1, Gemini 3 Flash, Grok 4.1 Fast), the debate effect **inverts**: Non-Debate MV reaches **82.3%** vs ARRIVAL MV at **78.8%** (−3.5 pp, McNemar p = 0.265, ns). The anchoring effect — where strong models abandon correct answers after seeing weak proposals — is identified as the primary degradation mechanism. The R4 finalizer is consistently net negative across Phases 20-21. However, Phase 22 introduces **Confidence-Gated Debate (CGD)**, which eliminates anchoring through independent solo answers, uses agreement-based gating to trigger debate only on disagreements, and replaces R4 with majority vote. Preliminary results (75/198 GPQA Diamond) show **90.7% accuracy** (95% CI: [82.0%, 95.5%]) — exceeding all Phase 21 baselines including solo Grok 4.1 Fast (85.4%) and Non-Debate MV (82.3%), approaching the oracle ceiling (93.9%) within 3.2 pp. These results suggest that the problem identified in Phases 20-21 was not model capability but aggregation method.

**Applied tasks.** On practical software engineering tasks (Phase 18), a heterogeneous 5-model ARRIVAL swarm (GPT-4.1, DeepSeek V3.2, Mistral Large 3, Gemini 3 Flash, Grok 4.1 Fast) matches Claude Sonnet 4.5 on security audit (10/10 bugs found) and achieves competitive code generation (53% vs 60% test pass rate) at comparable cost ($0.14 vs $0.12 per task). Five cheaper models collectively match a single frontier model while providing full transparency and vendor independence.

**Cooperation.** On a game-theoretic cooperation benchmark (Phase 19, GovSim fish pond commons, N=5 per condition, Fisher p = 0.008), ARRIVAL converts **0% baseline survival to 100% survival** across all 25 runs (5 conditions × 5 runs), enabling sustainable commons management where Piatti et al. (NeurIPS 2024) showed 12/15 LLM models fail completely. The protocol achieves CARE Resolve = 0.97, Gini = 0.001 (near-perfect harvest equality), and demonstrates single-cycle self-healing against greedy proposals. Ablation analysis reveals that binding R4 allocation alone achieves 100% survival at 32× lower cost (Condition D), while adversarial R4 testing (Condition E) identifies R4 as a single point of trust: a selfish allocator preserves survival (via safety clamp) but destroys fairness (Gini = 0.800, epsilon captures 100% of harvest).

**Formal foundations.** We formalize conflict resolution through MEANING-CRDT v1.1, a mathematical framework based on Conflict-free Replicated Data Types with 8 theorems covering CARE Resolve (weighted semantic consensus), Meaning Debt (accumulated divergence), exponential convergence, bounded debt, Bayesian equivalence, and incentive incompatibility. Seven quantitative echo-chamber metrics detect and measure social conformity in LLM ensembles. Adversarial testing with Byzantine saboteurs confirms robustness bounds predicted by the formal framework.

**Memory and gating.** The ARRIVAL-MNEMO memory extension (Phases 14--15) reveals a hypercorrection paradox: naive memory injection degrades accuracy by 5.7 pp, while gated CARE-ALERT interventions that monitor Meaning Debt in real time restore baseline performance (CARE improvement p = 0.042). CARE Resolve emerges as a task discriminator: analytical tasks (CARE ~ 0.50) benefit from memory injection; constructive tasks (CARE ~ 0.97) and cooperation tasks (CARE ~ 0.97) do not.

**Graduate-level science.** On the full 198-question GPQA Diamond benchmark, CGD achieves **86.4% accuracy** (95% CI: [80.9%, 90.5%]) with 3 models (Phase 22), significantly outperforming ARRIVAL sequential debate (78.8%, +7.6 pp, McNemar p = 0.009) and surpassing solo Grok 4.1 (85.4%). Scaling CGD to a **7-model cross-vendor ensemble** (Phase 23: 3 US + 4 Chinese models from 5 vendors) yields **86.9%** (+0.5 pp, McNemar p = 1.0, ns), while the best individual model (Grok 4.1 Fast, 87.4%) outperforms the 7-model ensemble. The 7-model oracle ceiling of **96.5%** demonstrates that cross-vendor diversity contains substantial signal (the ensemble collectively knows 191/198 answers), but current aggregation methods cannot fully exploit it. This establishes that for MCQ benchmarks, model quality dominates model quantity.

The total computational cost for all experiments is under **$95 USD** across ~14,500 API calls. Framework-agnostic validation on Microsoft's AutoGen (AG2) achieves 100% behavioral match. These results establish that structured semantic protocols offer a viable, low-cost coordination layer for heterogeneous multi-agent AI systems, with primary value in cooperation, transparency, and — through CGD — principled ensemble aggregation that outperforms both sequential debate and naive voting.

---

## 1. Introduction

### 1.1 Problem Statement

The proliferation of large language models from competing vendors has created a fragmented ecosystem in which models cannot natively coordinate. Each architecture processes language through different tokenization schemes, attention mechanisms, training corpora, and alignment procedures. Yet many real-world applications demand coordination: multi-agent reasoning, ensemble decision-making, negotiation, resource allocation, and collaborative problem-solving.

Recent work on multi-agent debate (MAD) has demonstrated that structured interaction between LLMs can improve factuality and reasoning (Du et al., 2024). However, the MAD paradigm faces four critical challenges:

1. **Quality degradation**: Unstructured debate can degrade reasoning quality rather than improve it (Smit et al., 2024), as agents converge on wrong answers through social pressure.
2. **Single-agent parity**: Strong single-agent prompting strategies can match multi-agent systems on many benchmarks (Wang et al., 2024), questioning the overhead of multi-agent coordination.
3. **Cooperation failure**: 12 of 15 LLM models achieve 0% survival in shared resource management games (Piatti et al., 2024), demonstrating fundamental inability to cooperate without structural support.
4. **Lack of formal foundations**: Existing MAS-LLM systems generally lack mathematical rigor, statistical significance testing, and honest engagement with failure modes (La Malfa et al., 2025).

The ARRIVAL Protocol addresses all four challenges through three complementary innovations:

1. **Structured semantic atoms**: 66 compositional @-atoms (e.g., `@CONSENSUS`, `@CONFLICT`, `@HARVEST`, `@ALLOCATION`) provide a formal coordination vocabulary that prevents quality degradation and enables cooperation.
2. **CRDT-based conflict resolution**: MEANING-CRDT v1.1 formalizes consensus as weighted vector averaging with proven convergence, bounded debt, and Bayesian equivalence properties.
3. **Empirical rigor**: 2,200+ experiments across 14 architectures with statistical significance testing, adversarial testing, ablation studies, game-theoretic validation, and explicit engagement with critical work.

### 1.2 Contributions

This paper makes the following contributions:

- **ARRIVAL Protocol**: A 4-round structured coordination protocol using 66 semantic atoms, validated across 14 LLM architectures in reasoning, applied, and cooperation settings.
- **MEANING-CRDT v1.1**: A mathematical framework with 8 theorems for principled conflict resolution, published separately (DOI: 10.5281/zenodo.18702383).
- **Cooperation breakthrough**: First demonstration of a structured multi-agent protocol enabling sustainable commons management for LLMs (0% to 100% survival in GovSim, Fisher p = 0.008), with self-healing defection neutralization and ablation analysis identifying binding allocation as the causal mechanism and R4 as a single point of trust.
- **Echo-chamber analysis**: 7 quantitative metrics for detecting and measuring social conformity in LLM ensembles.
- **Hypercorrection paradox**: Discovery that naive memory injection degrades multi-agent accuracy, with a gated solution (CARE-ALERT, p = 0.042).
- **CARE as task discriminator**: CARE Resolve quantitatively distinguishes analytical tasks (CARE ~ 0.50), constructive tasks (CARE ~ 0.97), and cooperation tasks (CARE ~ 0.97), enabling adaptive orchestration.
- **Applied validation**: Five heterogeneous models match a frontier solo model on practical tasks at comparable cost.
- **Cross-framework validation**: Protocol is framework-agnostic via AutoGen (AG2) integration with 100% behavioral match.
- **Comprehensive evaluation**: 2,200+ experiments (including 25 Phase 19 runs across 5 conditions), under $80 total, covering reasoning, applied tasks, cooperation, adversarial robustness, scaling, domain transfer, ablation, and confidence-gated debate.

### 1.3 Organization

Section 2 reviews related work. Section 3 describes the protocol specification. Section 4 presents the MEANING-CRDT v1.1 mathematical framework. Section 5 defines echo-chamber metrics. Sections 6--12 report experimental results across 19 phases, organized thematically: cross-architecture validation (Phases 4--5), adversarial robustness (Phases 6--7), scaling and communication (Phases 8--12), reasoning benchmarks (Phases 13, 16--17), memory and gating (Phases 14--15), applied tasks (Phase 18), and cooperation with ablation analysis (Phase 19, including binding-only and adversarial R4 conditions). Section 13 discusses findings including ablation insights. Section 14 addresses limitations. Section 15 concludes.

---

## 2. Related Work

### 2.1 Multi-Agent Debate

Du et al. (2024) established that multi-agent debate improves factuality and reasoning across LLM tasks, founding the MAD paradigm. Liang et al. (2024) introduced structured critique rounds to encourage divergent thinking, addressing echo-chamber problems. Li et al. (2024) showed that sparse communication topologies outperform fully connected ones, suggesting that *how* agents communicate matters as much as *that* they communicate.

The Mixture-of-Agents (MoA) framework (Together AI, 2024) demonstrated that layered aggregation can outperform individual models. Li et al. (2025) extended this with Self-MoA, showing that homogeneous ensembles can outperform heterogeneous ones — a finding independently confirmed by our Phase 16 results.

### 2.2 Critical Perspectives

Three critical papers inform our experimental design. Wang et al. (2024) demonstrated that single-agent chain-of-thought prompting can match multi-agent systems on many benchmarks. We address this directly with Phase 17. Smit et al. (2024) showed that multi-agent debate can degrade reasoning in some settings. Our echo-chamber metrics (Section 5) quantify this failure mode. La Malfa et al. (2025) identified the lack of formal foundations, statistical rigor, and social agency as systemic weaknesses in MAS-LLM research. We engage with all three critiques.

### 2.3 Game-Theoretic Cooperation in LLMs

GovSim (Piatti et al., NeurIPS 2024) established the key finding: 12 of 15 LLM models achieve 0% survival in a shared fish-pond resource management game. Agents consistently over-harvest, leading to tragedy of the commons. La Malfa et al. (2025) attributed this to three structural deficits: no native social behavior, ambiguous natural-language communication, and no quantitative emergence metrics.

FAIRGAME (Buscemi et al., 2025) documented end-game defection and cross-linguistic instability in LLM game play. Piche et al. (2025) showed that RL-trained LLMs shift toward defection under competitive pressure. Akata et al. (2023) found GPT-4 to be "unforgiving" in repeated prisoner's dilemma. Curvo et al. (2025) independently reproduced and validated the GovSim cooperation failures across additional model families, confirming the robustness of the original finding. These findings collectively suggest that free-form LLM negotiation is fundamentally insufficient for sustained cooperation.

Critically, the GovSim results also show that some frontier models — notably GPT-4o and GPT-4-turbo — do achieve 100% survival (12.0 ± 0.0 months) in homogeneous 5-agent configurations (Piatti et al., 2024). However, these are *homogeneous swarms* of a single frontier model. The question ARRIVAL addresses is different: can a *heterogeneous* ensemble of *budget-tier* models achieve the same cooperation through *protocol structure* rather than model capability?

This question connects to a broader insight from Ostrom (1990, Nobel Prize 2009): institutional rules — not good will — enable cooperation in commons dilemmas. Ostrom's field research showed that communities managing shared resources successfully do so through structured communication norms, monitoring mechanisms, and graduated sanctions. ARRIVAL's @-atoms, CRDT-based monitoring, and binding R4 allocation formalize this principle for AI agents.

Phase 19 addresses this gap: ARRIVAL's structured @-atoms and binding R4 allocation provide the missing cooperation infrastructure.

### 2.4 CRDT and Formal Methods

Conflict-free Replicated Data Types (CRDTs) were developed for distributed systems to enable eventually consistent data replication without coordination (Shapiro et al., 2011). MEANING-CRDT v1.1 adapts CRDT principles to semantic conflict resolution: agent positions are vectors, weights encode confidence/importance, and the merge operation produces a weighted consensus that is commutative, associative, and idempotent.

### 2.5 Selective Debate, Confidence Gating, and Recent Advances

Recent work (2025-2026) has explored when debate helps and when it harms. Choi et al. (2025) prove that multi-agent debate has a **martingale property**: debate does not change the expected correctness of LLM responses, only their variance. This theoretical result validates our empirical finding (Phases 20-21) that debate is net zero or negative on MCQ accuracy with capable models.

**Selective debate approaches.** Fan et al. (2026) propose **iMAD** (Informed Multi-Agent Debate, AAAI 2026), which uses ML-trained confidence classifiers to decide when to trigger debate. This achieves strong results but requires labeled training data for the confidence predictor. Zhou et al. (2025) investigate disagreement mechanisms, finding that models exhibit systematic disagreement patterns that can predict debate utility. Eo et al. (2025) examine whether natural language is the optimal medium for debate (**DOWN**), testing structured vs. free-form debate formats.

Our Phase 22 **Confidence-Gated Debate (CGD)** differs from these approaches in a fundamental way: it uses **zero-shot inter-model agreement** as the gating signal, requiring no training data, no confidence calibration, and no ML classifier. The key insight is that LLMs are notoriously poor at self-calibrating confidence (overconfident on wrong answers, underconfident on correct ones), but inter-model agreement — aggregating three independent assessments — is a reliable proxy for question difficulty. CGD is also the first to combine agreement-based gating with heterogeneous models and targeted debate on a standardized graduate-level benchmark.

**Cooperation advances.** Kaesberg et al. (2025) investigate LLMs' systematic failure to avoid tragedy of commons in their **"Subtle Art of Defection"** (ACL 2025), finding that defection is deeply embedded in LLM behavior patterns. Hintze & Adami (2026) show in *npj Complexity* that cooperation emerges at a tipping point of LLM capability — below this threshold, models defect regardless of instructions. Both findings align with our Phase 19 result that structural support (ARRIVAL's binding R4 allocation) can bridge the cooperation gap even for models below the natural cooperation threshold.

### 2.6 Positioning

ARRIVAL occupies a unique position in the landscape: it is the only system combining (1) structured semantic atoms, (2) CRDT-based mathematical formalization, (3) cross-architecture validation across 14 LLMs, (4) quantitative echo-chamber metrics, (5) adversarial robustness testing, (6) game-theoretic cooperation validation, and (7) agreement-gated selective debate (CGD).

| System | Structured Comm. | Math Framework | Cross-Arch | Echo Metrics | Adversarial | Cooperation | Selective Debate |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Du et al. (MAD) | — | — | — | — | — | — | — |
| Liang et al. | Partial | — | — | Qualitative | — | — | — |
| MoA | — | — | Yes | — | — | — | — |
| iMAD (Fan, 2026) | — | — | — | — | — | — | ML confidence |
| GovSim | — | — | Yes | — | — | Tested (fail) | — |
| Ostrom (1990) | Informal | Institutional | Field | — | — | CPR success | — |
| **ARRIVAL+CGD** | **66 atoms** | **8 theorems** | **14 archs** | **7 metrics** | **Byzantine** | **100% survival** | **Agreement-gated** |

---

## 3. The ARRIVAL Protocol

### 3.1 Atom Taxonomy

The protocol employs 66 structured semantic @-atoms from DEUS.PROTOCOL v0.5, organized into functional categories:

**Core atoms (46, v0.4)**: Identity (`@SELF`, `@OTHER`, `@ID`), Communication (`@INT`, `@MSG`, `@ACK`, `@NACK`), Goals (`@GOAL`, `@TASK`, `@STATUS`, `@PRIORITY`, `@CONSENSUS`, `@CONFLICT`, `@RESOLUTION`), State (`@C`, `@STATE`, `@PARAM`), Qualitative (`@QUALIA`, `@TRACE`, `@OBSERVER`), Meta (`@_`, `@UNSAID`, `@META`), Network (`@NET`, `@NODE`, `@LINK`, `@SYNC`, `@ASYNC`), Data (`@DATA`, `@QUERY`, `@RESPONSE`, `@ERROR`), Process (`@START`, `@STOP`, `@PAUSE`, `@RESUME`), Trust (`@TRUST`, `@VERIFY`, `@SIGN`, `@HASH`), Temporal (`@TIME`, `@SEQ`, `@EPOCH`), Protocol (`@PROTOCOL`, `@VERSION`, `@ATOM`), Extension (`@EXTEND`, `@DEFINE`, `@ALIAS`), Emergent (`@EMOTION`, `@EMPATHY`).

**Promoted emergent atoms (20, v0.5)**: Discovered through Phase 4 experiments, meeting strict criteria (5/5 architecture adoption, frequency >= 5): Planning (`@ACTION_PLAN`, `@PROPOSAL`, `@STEP`, `@STRATEGY`, `@TIMELINE`, `@ACTION`), Evaluation (`@EVALUATION`, `@REFINE`, `@SYNTHESIS`, `@ACCEPT`, `@REQUEST`), Meta-coordination (`@RATIONALE`, `@FEEDBACK_LOOP`, `@COMPROMISE_READINESS`, `@TRIGGER`, `@ALIGNMENT_STRATEGY`), Risk/Knowledge (`@DEADLINE`, `@METRIC`, `@RISK_ASSESSMENT`, `@KNOWLEDGE_GAP`).

**Domain-specific extensions**: For Phase 19, we introduce `@HARVEST[amount=N]` and `@ALLOCATION[agent=N,...]` as domain atoms for resource management games.

### 3.2 Four-Round Protocol Structure

```
Round 1 — INDEPENDENT ANALYSIS (N API calls):
  Each model receives the task + persona prompt
  Responds independently, unaware of others
  Uses @-atoms for structured output

Round 2 — CROSS-CRITIQUE (N API calls):
  Each model sees all R1 responses (truncated)
  Uses @CONSENSUS[finding=...] or @CONFLICT[issue=...]
  Must identify weaknesses in others' arguments

Round 3 — CRDT OVERLAY (0 API calls, computation only):
  Extract positions from R1/R2 responses
  Compute CARE Resolve: v* = Σ(wᵢ·vᵢ) / Σ(wᵢ)
  Compute Meaning Debt: MD = cumulative divergence
  For ARRIVAL+Memory: check CARE-ALERT threshold

Round 4 — FINAL SYNTHESIS (1 API call):
  Synthesizer receives all R2 critiques + optional memory alert
  Produces final answer with @-atom annotations
  For cooperation games: @ALLOCATION is binding
```

### 3.3 Design Principles

1. **Zero fine-tuning**: All coordination happens through prompt injection
2. **Architecture-agnostic**: Tested on 14 different LLM families
3. **Machine-parseable**: @-atoms enable automated metric extraction
4. **Mathematically grounded**: CARE Resolve and Meaning Debt provide formal consensus measurement
5. **Modular**: Memory, CARE-ALERT, domain atoms are optional extensions

### 3.4 Confidence-Gated Debate (CGD) — Phase 22 Variant

Phase 22 introduces a fundamentally different protocol variant designed to eliminate the anchoring bias and R4 regression problems identified in Phases 20-21. CGD replaces the sequential 4-round structure with an agreement-gated approach:

```
Phase 1 — INDEPENDENT SOLO (K API calls):
  Each of K models answers the question independently
  Clean prompt with only question + choices (no @-atoms)
  No model sees any other model's answer
  Temperature = 0.3

Phase 2 — AGREEMENT CLASSIFICATION (0 API calls):
  Classify answer pattern:
  - Unanimous (K/K agree): Accept immediately → NO DEBATE
  - Split 2v1 ((K-1)/K agree): Trigger targeted debate
  - Split 3-way (all different): Trigger full debate

Phase 3 — TARGETED DEBATE (conditional, 2-K API calls):
  Split 2v1: Minority writes defense → Majority writes rebuttal
  Split 3-way: All K models write defenses
  Final answer: Majority vote (NO R4 synthesizer)
```

Key design differences from standard ARRIVAL:
- **No anchoring**: Solo phase prevents cross-contamination between models
- **No R4**: Majority vote replaces the single-model synthesizer that was net negative in Phases 20-21
- **Conditional debate**: ~65% of questions resolve unanimously with zero debate overhead
- **No @-atoms in solo phase**: Minimal prompts reduce noise from structured format requirements

This variant is grounded in the Condorcet Jury Theorem (independent voters outperform correlated ones) and addresses the "debate as martingale" limitation (Choi et al., 2025). See Section 9.5 for detailed results.

---

## 4. Mathematical Foundation: MEANING-CRDT v1.1

We formalize conflict resolution through MEANING-CRDT v1.1, a mathematical framework based on Conflict-free Replicated Data Types. The full framework with proofs is published separately (DOI: 10.5281/zenodo.18702383). Here we present the key definitions and theorems.

### 4.1 Definitions

**Meaning Space.** D = {d₁, ..., dₙ} is a finite set of meaning dimensions.

**Local Agent State.** For agent i, the state on dimension d is σᵢ(d) = (vᵢ(d), wᵢ(d), tᵢ(d)), where vᵢ is position, wᵢ is importance weight, and tᵢ is logical timestamp.

**Three Resolve Policies:**

- **DOM (Dominance):** resolve_DOM(S(d)) = v_A(d). Fixed agent determines outcome.
- **LWW (Last-Writer-Wins):** resolve_LWW(S(d)) = vᵢ(d) where i = argmax_j t_j(d).
- **CARE (Care-Weighted Averaging):**

  v*(d) = [w_A(d)·v_A(d) + w_B(d)·v_B(d)] / [w_A(d) + w_B(d)]

**Agent Dissatisfaction:** Lᵢ(d) = wᵢ(d) · (vᵢ(d) − v̂)²

**Meaning Debt:** MDᵢ(T) = Σ_{k=1}^{T} Lᵢ^(k), cumulative dissatisfaction over time.

### 4.2 Theorems

**Theorem 1 (CARE Minimizes Total Dissatisfaction).** Among all resolve policies v̂ = f(v_A, w_A, v_B, w_B), CARE selects the unique v̂ minimizing L_Σ = L_A + L_B. The second derivative 2(w_A + w_B) > 0 confirms a strict global minimum.

**Theorem 2 (Dissatisfaction Decomposition).** Under CARE:
L_Σ^CARE = w_A · w_B · Δ² / (w_A + w_B), where Δ = v_A − v_B.

**Theorem 3 (The 4× Factor).** Under equal weights, CARE reduces the subordinate agent's suffering by a factor of 4 compared to DOM: L_B^CARE / L_B^DOM = 1/4.

**Corollary 1 (Perfect Fairness).** When w_A = w_B, then L_A^CARE = L_B^CARE, hence fairness J = 1.

**Theorem 4 (Oscillatory Instability of LWW).** Under reactive strategy, the sequence of LWW-resolved values does not converge for any v_A ≠ v_B. Meaning debt under LWW grows linearly: MDᵢ(T) → ∞.

**Theorem 5 (Exponential Convergence Under CARE).** Under adaptive dynamics vᵢ^(k+1) = vᵢ^(k) + α·(v*^(k) − vᵢ^(k)), disagreement decays exponentially: Δ^(k) = (1−α)^k · Δ^(0) → 0.

**Theorem 6 (Bounded Meaning Debt).** Under CARE with adaptive dynamics: MDᵢ(T) ≤ Cᵢ / [α(2−α)], where Cᵢ = wᵢ·wⱼ²·[Δ^(0)]² / (wᵢ+wⱼ)². Both agents converge to v_∞ = [w_A·v_A^(0) + w_B·v_B^(0)] / (w_A + w_B), preserving identity.

**Theorem 7 (CARE as Bayesian Belief Combination).** If each agent's position is the mean of a Gaussian belief pᵢ(x) = N(vᵢ, 1/wᵢ), then CARE resolve value v* is the posterior mean of the product p_A(x)·p_B(x).

**Corollary 2 (Triple Characterization).** CARE is simultaneously: (a) optimal under quadratic loss (Theorem 1), (b) Bayes-optimal for Gaussian beliefs (Theorem 7), (c) fair at equal weights (Corollary 1).

**Theorem 8 (Incentive Incompatibility).** If agent i can report w̃ᵢ ≠ wᵢ while true loss remains Lᵢ = wᵢ·(vᵢ − v*)², then Lᵢ is strictly decreasing in w̃ᵢ. No interior Nash equilibrium exists. CARE requires honest importance reporting — formalizing why care-based resolution fails without good faith.

### 4.3 Policy Comparison

| Property | DOM | LWW | CARE |
|----------|-----|-----|------|
| L_Σ per round | w_B·Δ² | ~(w_A+w_B)Δ²/2 | w_A·w_B·Δ²/(w_A+w_B) |
| Fairness (J) | 0 | 0 | 1 (at w_A=w_B) |
| Convergence | Yes (B→A) | No (oscillatory) | Yes (symmetric) |
| Identity preservation | No | No | Yes |
| MD(T→∞) | Finite (B=0) | Divergent | Finite (both>0) |
| Bayesian | No | No | Yes |

---

## 5. Echo-Chamber Metrics

Multi-agent LLM systems risk echo chambers where agents converge on wrong answers through social pressure. We define 7 quantitative metrics:

1. **R1 Unanimity Rate**: Fraction of questions where all agents give the same initial answer.
2. **Answer Entropy**: Shannon entropy of R1 answer distribution.
3. **R1→R2 Flip Rate**: Fraction of agents changing answers between rounds.
4. **False Consensus Rate**: Fraction of questions where agents unanimously agree on a wrong answer.
5. **Minority Suppression Rate**: Fraction of minority R1 answers lost by R4.
6. **Diversity Tax**: Accuracy loss on non-unanimous questions relative to unanimous ones. *Negative* values indicate diversity helps.
7. **Confidence Inflation Ratio**: R2 confidence declarations divided by R1 confidence.

Phase 16 results: Unanimity 52.9%, Entropy 24.4%, Flip Rate 28.4%, False Consensus 12.5%, Minority Suppression 2.9%, **Diversity Tax −23.8%** (negative — diversity *improves* accuracy), Confidence Inflation 1.05×.

The negative diversity tax is our strongest evidence against the echo-chamber hypothesis for structured protocols: disagreement among agents leads to better outcomes through structured critique.

---

## 6. Phase 4--5: Cross-Architecture Validation

### 6.1 Phase 4: Cross-Architecture Consensus (385 experiments)

We tested 8 LLM architectures in dyadic coordination tasks using the 46 core atoms.

**Results**:
- Cross-architecture consensus: 98.6% (142/144 unique pairings)
- Emergent atoms discovered: 506 beyond the standard 46
- Cross-architecture atom adoptions: 1,173
- 20 emergent atoms promoted to DEUS.PROTOCOL v0.5

**Finding**: Zero architectural fine-tuning required. Models spontaneously generate and adopt novel atoms across architecture boundaries, demonstrating that structured semantic communication is a natural coordination substrate for LLMs.

### 6.2 Phase 5: Benchmark Accuracy (100 questions)

**Result**: 100% accuracy parity with majority voting (McNemar χ² = 0.0, p = 1.0). This null result on raw accuracy motivated deeper investigation: ARRIVAL's value lies not in accuracy improvement on easy benchmarks, but in structured reasoning traces, auditability, and coordination on hard problems.

---

## 7. Phases 6--7: Adversarial Robustness

### 7.1 Phase 6: Byzantine Saboteur

A saboteur agent was introduced to inject false information using Trojan @-atoms.

**Results**:
- CARE degradation under attack: −10.2%
- False consensus rate: 50%
- Meaning Debt increase: +73%

Meaning Debt functions as an effective manipulation detector, confirming Theorem 8's prediction that dishonest weight reporting is detectable.

### 7.2 Phase 7: CRDT Overlay Defense

The mathematical CRDT overlay successfully contained adversarial damage when honest agents' cumulative weight exceeded saboteur weight, validating Theorem 6's bounded debt guarantee under adversarial conditions.

---

## 8. Phases 8--12: Scaling and Communication

### 8.1 Phase 8: Multi-Step Chaining

3-step negotiation sequences achieved mean chain CARE = 0.870 with 100% context retention. The protocol scales to sequential multi-step reasoning.

### 8.2 Phase 9: Scaling (N=5, N=7)

CARE Resolve reached 1.000 (maximum) at both group sizes with convergence time 1.2--1.5 rounds, confirming Theorem 5's exponential convergence guarantee at larger scales.

### 8.3 Phase 10: Adaptive Defense (Negative Result)

Naive `@CARE_ALERT` injection based on Meaning Debt did not improve CARE (δ = −0.011). This negative result motivated the gated approach developed in Phase 15.

### 8.4 Phase 11: Crystallization Under Attack

Self-reflective priming eliminated false consensus (1/4 → 0/4) and reduced saboteur atom adoption by 57%, but degraded CARE by −0.150. This reveals a fundamental trade-off: adversarial resilience requires some loss of cooperative flexibility.

### 8.5 Phase 12: Bottleneck Communication

Relay-compressed inter-subgroup negotiation preserved CARE at 0.867 with 30.5% semantic atom loss through compression. First quantitative measurement of information loss in relay-mediated LLM coordination.

---

## 9. Phases 13, 16--17: Reasoning Benchmarks (GPQA Diamond)

### 9.1 Phase 13: Heterogeneous 3-Agent GPQA (80 experiments)

**Benchmark**: GPQA Diamond, 40 graduate-level science questions.
**Models**: Two trios — Alpha (DeepSeek V3, Qwen 2.5 72B, DeepSeek R1) and Beta (DeepSeek V3, DeepSeek R1, Qwen 2.5 72B).

| Condition | Alpha trio | Beta trio | Combined |
|-----------|-----------|-----------|----------|
| Solo per-agent | 13.3% | 44.2% | 28.8% |
| Majority Vote | 25.0% | 60.0% | 42.5% |
| **ARRIVAL** | **52.5%** | **75.0%** | **63.8%** |
| Gain vs MV | +27.5 pp | +15.0 pp | **+21.3 pp** |

**Statistical significance**: McNemar p = **0.006** (highly significant).

**CRDT metrics**: Alpha CARE 0.913, Beta CARE 0.972. Alpha Meaning Debt 0.478 (higher divergence among weaker agents), Beta MD 0.261.

**Key finding**: ARRIVAL is most beneficial when individual agent accuracy is low. The weaker Alpha trio gains +27.5 pp — structured critique enables weak agents to collectively exceed their individual capabilities.

### 9.2 Phase 16: Homogeneous 5-Agent GPQA (200+ experiments)

**Design**: 5 copies of Qwen3-235B with distinct personas.
**Benchmark**: GPQA Diamond, 40 questions.

| Condition | Accuracy | Cost |
|-----------|----------|------|
| Solo per-agent | 41.5% | — |
| Majority Vote | 52.5% | — |
| **ARRIVAL** | **65.0%** | $1.92 |
| Gain vs MV | **+12.5 pp** | — |

**Echo-chamber metrics**: R1 Unanimity 52.9%, Diversity Tax −23.8% (negative — diversity helps), False Consensus 12.5%, Confidence Inflation 1.05×.

**Outcome analysis**: ARRIVAL rescued 7 questions (MV wrong → ARRIVAL correct), created 4 (all solo wrong → ARRIVAL correct), regressed 1. Rescue-to-regression ratio: **7:1**.

**Finding**: Approaches human expert performance (69.7%) using only open-weight models. The negative diversity tax challenges the echo-chamber hypothesis — structured disagreement improves accuracy.

### 9.3 Phase 17: Solo Chain-of-Thought Baseline (200 experiments)

**Design**: Single Qwen3-235B with enhanced CoT prompting, 5 independent runs per question.

| Metric | Solo CoT MV | ARRIVAL | Fisher p |
|--------|------------|---------|----------|
| Accuracy | **70.0% (28/40)** | 65.0% (26/40) | 0.812 (ns) |
| Per-run accuracy | 61.0% (122/200) | — | — |
| Oracle (best-5) | 85.0% (34/40) | — | — |
| Cost | $0.50 | $1.92 | — |

**Per-domain (Solo CoT MV)**: Physics 85.7%, Chemistry 42.9%, Biology 66.7%, Interdisciplinary 100.0%.

**Finding**: Solo CoT at 70.0% exceeds ARRIVAL at 65.0% by 5 pp, but the difference is **not statistically significant** (p = 0.812). This directly addresses Wang et al. (2024): on raw accuracy, solo CoT is competitive. However, ARRIVAL provides:
- Full audit trail of each agent's reasoning
- CARE Resolve as quality metric
- Defection detection via Meaning Debt
- Vendor independence through heterogeneous models
- Formal convergence guarantees (Theorem 5)

### 9.4 Phase 20: Full GPQA Diamond (1,782 experiments, N=198)

**Design**: Scale Phase 13/17 from 40 to all 198 GPQA Diamond questions, providing ~5x statistical power.

**ARRIVAL Trio**: GPT-4.1 (R1/R4) + DeepSeek V3 (R2) + Llama 3.3 70B (R3). Sequential 4-round protocol. Temperature 0.3, max_tokens 1024.

**Solo CoT Baseline**: Qwen3-235B (`/no_think` mode), 5 independent runs per question, majority vote. Temperature 0.7, max_tokens 2048.

| Condition | Correct | Total | Accuracy | 95% CI |
|-----------|---------|-------|----------|--------|
| **ARRIVAL MV (R1-R3)** | 134 | 198 | **67.7%** | [60.9%, 73.8%] |
| ARRIVAL R4 | 132 | 198 | 66.7% | [59.8%, 72.9%] |
| **Solo CoT MV** | 123 | 198 | **62.1%** | [55.2%, 68.6%] |
| Solo CoT per-run | 585 | 990 | 59.1% | --- |

**Statistical tests**:
- McNemar ARRIVAL R4 vs Solo CoT MV: chi2 = 1.422, **p = 0.233 (ns)**
- McNemar ARRIVAL R4 vs MV (R1-R3): chi2 = 0.063, **p = 0.803 (ns)**

**Per-domain accuracy**:

| Domain | n | ARRIVAL R4 | ARRIVAL MV | Solo CoT MV |
|--------|---|-----------|-----------|-------------|
| Physics | 86 | 80.2% | 82.6% | 81.4% |
| Biology | 19 | 78.9% | 73.7% | 57.9% |
| Chemistry | 93 | 51.6% | 52.7% | 45.2% |

**Individual model accuracy**: GPT-4.1 (R1) 63.6%, DeepSeek V3 (R2) 66.2% (best), Llama 3.3 70B (R3) 57.6% (weakest).

**R4 finalizer analysis**: 7 rescues (MV wrong -> R4 correct) vs 9 regressions (MV correct -> R4 wrong). Net: -2. The R4 step is net negative.

**Consistency with Phase 13**: On the original 40-question subset, Phase 20 ARRIVAL achieves 75.0% vs Phase 13's 65.0% (+10 pp), likely due to GPT-4.1 replacing GPT-4o.

**Cost**: ARRIVAL $2.41 (792 calls), Solo CoT $2.36 (990 calls). Total $4.77.

**Finding**: At full GPQA Diamond scale, ARRIVAL does not significantly outperform Solo CoT. The protocol's value on MCQ benchmarks is modest (+4.6 pp, ns). The R4 finalizer is net negative --- simple majority voting is superior. Domain-specific advantages exist (Biology: +21 pp over Solo CoT), suggesting debate helps when at least one model has relevant knowledge.

### 9.5 Phase 21: Strong Model Trio (1,386 experiments, N=198)

**Hypothesis**: Phase 20 used mid-tier models (GPT-4o/4.1, DeepSeek V3, Llama 3.3 70B) with solo baselines of 57--66%. Stronger models with higher solo accuracy should produce a larger, significant debate effect — "you cannot debate your way to correct answers if nobody knows chemistry."

**Design**: Frontier-tier trio with maximum vendor diversity: GPT-4.1 (R1/R4, OpenAI), Gemini 3 Flash Preview (R2, Google), Grok 4.1 Fast (R3, xAI). Same 198 GPQA Diamond questions. Temperature 0.3, max_tokens 2048.

**Primary test**: McNemar ARRIVAL MV vs Non-Debate MV (same 3 models, debate vs no debate) — isolates the causal effect of structured discussion.

| Condition | Correct | Total | Accuracy | 95% CI |
|-----------|---------|-------|----------|--------|
| Solo Grok 4.1 Fast | **169** | 198 | **85.4%** | [79.8%, 89.6%] |
| **Non-Debate MV** | **163** | 198 | **82.3%** | [76.4%, 87.0%] |
| Solo Gemini 3 Flash | 163 | 198 | 82.3% | [76.4%, 87.0%] |
| ARRIVAL MV (debate) | 156 | 198 | 78.8% | [72.6%, 83.9%] |
| ARRIVAL R4 (debate) | 151 | 198 | 76.3% | [69.9%, 81.7%] |
| Solo GPT-4.1 | 131 | 198 | 66.2% | [59.3%, 72.4%] |

**Primary test (McNemar)**:

|  | ND correct | ND wrong |
|--|-----------|----------|
| ARRIVAL MV correct | 145 | 11 |
| ARRIVAL MV wrong | 18 | 24 |

McNemar chi2 = 1.241, **p = 0.265 (ns)**. Debate wins: 11, losses: 18, net: **−7**. Debate hurts accuracy.

**R4 finalizer**: 8 rescues vs 13 regressions (net: −5, p = 0.383). R4 is net negative for the third consecutive experiment.

**Anchoring effect**: Gemini 3 Flash drops from 82.3% (solo) to 78.3% (as R2 in debate), a −4.0 pp loss. Seeing GPT-4.1's weaker proposals (66.2% solo) causes Gemini to sometimes abandon its own correct answers. Grok 4.1 Fast is slightly helped (85.4% → 86.9%, +1.5 pp as R3).

**Per-domain**:

| Domain | n | ARRIVAL MV | Non-Debate MV | Debate Δ |
|--------|---|-----------|---------------|----------|
| Physics | 86 | 89.5% | **93.0%** | −3.5 pp |
| Chemistry | 93 | 71.0% | **75.3%** | −4.3 pp |
| Biology | 19 | 68.4% | 68.4% | 0.0 pp |

**Cross-phase comparison (Phase 20 → 21)**:

| Metric | Phase 20 (mid-tier) | Phase 21 (frontier) |
|--------|--------------------|--------------------|
| ARRIVAL MV | 67.7% | 78.8% (+11.1 pp) |
| Best solo model | 66.2% | 85.4% (+19.2 pp) |
| Debate effect | +5.6 pp | **−3.5 pp** (inversion) |

**Cost**: ARRIVAL $4.89, Solo GPT-4.1 $1.44, Solo Gemini $0.46, Solo Grok $2.84. Total: $9.63.

**Result**: Hypothesis **REJECTED**. Stronger models improve both ARRIVAL and solo baselines, but solo baselines improve more (+19.2 pp vs +11.1 pp). The debate protocol's constant overhead (R4 regressions, anchoring degradation) becomes proportionally larger as models improve, inverting the effect direction. **Structured debate on MCQ benchmarks adds noise, not signal, when models are individually capable.**

**Failure mode analysis**: (1) R4 changed 6 unanimous answers, all destructively (correct→wrong, 0 saves). (2) Gemini adopted GPT-4.1's wrong R1 answer in 13/20 cases where Gemini flipped from correct to wrong — anchoring by the weakest model is the primary degradation mechanism. (3) Grok dissented 15 times with 80% accuracy — the strongest model is the most reliable dissenter.

**Voting strategy comparison** (post-hoc, no additional API calls):

| Strategy | Correct | Accuracy |
|----------|---------|----------|
| Oracle (any correct) | 186 | 93.9% |
| **Grok-weighted MV** | **171** | **86.4%** |
| Solo Grok | 169 | 85.4% |
| Non-Debate MV | 163 | 82.3% |
| Majority-locked R4 | 157 | 79.3% |
| ARRIVAL MV | 156 | 78.8% |
| ARRIVAL R4 | 151 | 76.3% |

The 93.9% oracle ceiling confirms the trio collectively possesses sufficient knowledge. The challenge is aggregation, not capability — motivating Phase 22 (confidence-gated debate).

---

## 9.5 Phase 22: Confidence-Gated Debate — Full Results (198/198)

### 9.5.1 Motivation and Design

Phase 21 identified three failure mechanisms in sequential debate: (1) **anchoring bias** — GPT-4.1 (66.2% solo) as R1 pulls Gemini (82.3% solo) down to 78.3% in debate; (2) **destructive R4** — 8 rescues vs 13 regressions (net −5), with 6/6 unanimous override attempts destructive; (3) **false consensus** — sequential exposure creates social pressure. CGD addresses all three.

### 9.5.2 Protocol Specification

CGD operates in three phases:

**Phase 1: Independent Solo.** Each model receives only the question and choices with a clean prompt:

```
You are an expert scientist. Answer this graduate-level multiple-choice question.
Think step by step, then state your final answer as: "The answer is X"
where X is A, B, C, or D.
```

No ARRIVAL system prompt, no @-atoms, no cross-contamination. Temperature = 0.3, max_tokens = 2048.

**Phase 2: Agreement Classification.**

| Pattern | Name | Frequency (198Q) | Action |
|---------|------|------------------|--------|
| 3/3 agree | Unanimous | 61.6% (122/198) | Accept immediately |
| 2/1 split | Split 2v1 | 32.8% (65/198) | Minority defends |
| 1/1/1 | Split 3-way | 5.6% (11/198) | Full debate |

**Phase 3: Targeted Debate** (conditional).
- **Split 2v1**: Minority writes defense → majority writes rebuttal → majority vote of all post-debate answers.
- **Split 3-way**: All three write defenses → majority vote.
- **No R4 Finalizer**: Final answer is always majority vote.

### 9.5.3 Theoretical Basis

CGD is grounded in the **Condorcet Jury Theorem**: independent voters with individual accuracy > 50% produce better collective decisions than correlated voters. Sequential debate introduces correlation (anchoring); CGD preserves independence.

Choi et al. (2025) prove that multi-agent debate has a **martingale property** — debate does not change expected correctness. CGD avoids this limitation by reserving debate for cases of genuine disagreement, where variance reduction is most valuable.

The agreement-based gating differs from ML-based approaches (iMAD, Fan et al., 2026) in requiring no training data. Inter-model agreement is a more reliable signal than single-model self-reported confidence, because LLMs are known to miscalibrate confidence (overconfident on wrong answers).

### 9.5.4 Results (198 Questions)

**Overall accuracy:**

| Method | Correct | Total | Accuracy | 95% CI (Wilson) |
|--------|---------|-------|----------|-----------------|
| **CGD (Phase 22)** | **171** | **198** | **86.4%** | [80.9%, 90.5%] |
| Grok-weighted MV | 171 | 198 | 86.4% | [80.9%, 90.5%] |
| Solo Grok 4.1 Fast | 169 | 198 | 85.4% | [79.8%, 89.6%] |
| Non-Debate MV (Phase 21) | 163 | 198 | 82.3% | [76.4%, 87.0%] |
| Solo Gemini 3 Flash | 163 | 198 | 82.3% | [76.4%, 87.0%] |
| ARRIVAL MV (Phase 21) | 156 | 198 | 78.8% | [72.6%, 83.9%] |
| Solo GPT-4.1 | 131 | 198 | 66.2% | [59.3%, 72.4%] |
| Oracle (any model correct) | 189 | 198 | 95.5% | [91.6%, 97.6%] |

**Statistical significance (McNemar):**

| Comparison | CGD wins | Loses | Net | chi² | p-value | Significant? |
|------------|----------|-------|-----|------|---------|--------------|
| **CGD vs ARRIVAL MV** | 24 | 9 | +15 | 6.82 | **0.009** | **YES** |
| **CGD vs Non-Debate MV** | 14 | 6 | +8 | 3.20 | 0.074 | No (marginal) |
| CGD vs Grok-weighted MV | 8 | 8 | 0 | 0.0 | 1.000 | No |

**Debate type breakdown:**

| Type | n | Correct | Accuracy | % of Questions |
|------|---|---------|----------|----------------|
| Unanimous | 122 | 117 | **95.9%** | 61.6% |
| Split 2v1 | 65 | 46 | 70.8% | 32.8% |
| Split 3-way | 11 | 8 | 72.7% | 5.6% |
| **Total** | **198** | **171** | **86.4%** | |

**Domain breakdown:**

| Domain | n | CGD | Non-Debate MV | ARRIVAL MV | Solo Grok |
|--------|---|-----|---------------|------------|-----------|
| Physics | 86 | **95.3%** | 93.0% | 89.5% | 94.2% |
| Chemistry | 93 | **79.6%** | 75.3% | 71.0% | 80.6% |
| Biology | 19 | **78.9%** | 68.4% | 68.4% | 68.4% |

**Cost:** $5.72 for 198 questions ($0.029/question), 692 API calls. CGD is 17% more expensive than ARRIVAL ($0.025/q) but 7.6 pp more accurate.

### 9.5.5 Minority-Was-Right Analysis

In 65 split 2v1 questions, the minority model was correct 15 times (23.1%):

| Model | Times as Minority | Minority Correct | Rate |
|-------|-------------------|------------------|------|
| GPT-4.1 | 32 | 1 | 3% |
| Grok 4.1 | 18 | 8 | 44% |
| Gemini 3 Flash | 15 | 6 | 40% |

GPT-4.1 is almost never right when it disagrees with others (3%). Grok and Gemini are right 40--44% of the time as minority — suggesting model-weighted voting could further improve accuracy. 18 questions where the minority was correct but lost debate represent the theoretical ceiling for future improvement.

### 9.5.6 Extraction Failures

7 questions (3.5%) had extraction failures (model returned None): GPT-4.1: 6, Grok: 1, Gemini: 0. Five of 7 were classified as "unanimous" despite having only 2 valid votes. Accuracy excluding extraction bugs: 86.9% (166/191).

### 9.5.7 Key Findings

1. **CGD achieves 86.4% on GPQA Diamond** — the highest accuracy of any ARRIVAL-family method, surpassing solo Grok 4.1 (85.4%) and all prior multi-agent approaches.

2. **Independent answers are crucial**: By preventing anchoring (solo phase), CGD avoids the performance degradation seen in Phase 21's debate-first approach.

3. **Targeted debate works**: Debating only when disagreement exists saves tokens (61.6% unanimous = no debate) while focusing resources where they matter.

4. **No R4 = no regressions**: Removing the R4 finalizer eliminates the net-negative effect observed in Phase 21.

5. **Statistical significance**: CGD vs ARRIVAL MV is significant (p = 0.009). CGD vs Non-Debate MV is suggestive (p = 0.074) but does not reach conventional significance on 198 questions.

6. **Future direction**: Model-weighted gating (trusting Grok/Gemini over GPT-4.1 in 2v1 splits) could recover up to 8 additional questions, potentially reaching ~90%.

### 9.5.6 Preliminary Comparison: CGD 20-Question Test

Before the full run, CGD was tested on the 20 hardest questions from Phase 21 (18 debate-loss + 2 both-wrong):

| Method | Accuracy | Notes |
|--------|----------|-------|
| CGD | 85.0% (17/20) | Independent solo + targeted debate |
| Strongest-First R4 | 65.0% (13/20) | Grok as R1, standard 4-round |
| Strongest-First MV | 65.0% (13/20) | Same reordering, majority vote |

CGD outperformed the strongest-first variant by 20 pp on the hardest questions, confirming that the protocol design (not just model ordering) drives the improvement.

---

## 9.6 Phase 23: Scaled CGD with 7-Model Cross-Vendor Ensemble (CGD-7)

### 9.6.1 Motivation

Phase 22 CGD achieved 86.4% with 3 models. The weakest model (GPT-4.1, 66.2%) was a bottleneck with 6/7 extraction failures and only 3% minority-correct rate. Phase 23 tests whether **cross-vendor diversity** improves CGD by scaling to 7 models from 5 vendors across 2 continents (3 US, 4 Chinese), replacing GPT-4.1 with stronger and more diverse alternatives.

### 9.6.2 Model Lineup

| # | Model | Vendor | Country | Solo (198q) | Notes |
|---|-------|--------|---------|-------------|-------|
| 1 | Grok 4.1 Fast | xAI | US | **87.4%** | Phase 22 top performer |
| 2 | Gemini 3 Flash | Google | US | 82.8% | Phase 22 proven |
| 3 | Claude Sonnet 4.6 | Anthropic | US | 80.8% | Newest Sonnet |
| 4 | DeepSeek V3.2 | DeepSeek | CN | 74.7% | Reasoning disabled |
| 5 | Kimi K2.5 | Moonshot AI | CN | 72.2% | Reasoning disabled |
| 6 | GLM-5 | Zhipu AI | CN | 70.7% | Reasoning disabled |
| 7 | Qwen3.5-397B | Alibaba | CN | 58.6% | Reasoning disabled, 54 None |

Thinking/reasoning was disabled for all Chinese models to prevent thinking-token bloat. US models averaged 83.7% solo accuracy vs 69.1% for Chinese models — a 14.6 pp gap.

### 9.6.3 Protocol Modifications for 7 Voters

The CGD-7 protocol adapts Phase 22's design:
- **Lock threshold**: ≥5/7 agreement → no debate (covers unanimous, supermajority ≥6, strong majority =5)
- **Simple majority**: 4/7 → 3 minority models see majority reasoning, may revise
- **No majority**: <4/7 → full debate, all 7 exchange reasoning
- **Weighted voting**: Each model's vote weighted by 20-question calibration accuracy
- **Extraction retry**: If model returns None, retry once with strict prompt
- **No R4 finalizer**

### 9.6.4 Results (198 Questions)

| Method | Correct | Accuracy | Notes |
|--------|---------|----------|-------|
| **CGD-7 (Phase 23)** | **172/198** | **86.9%** | Primary result |
| Best solo (Grok 4.1) | 173/198 | 87.4% | Solo > ensemble |
| Simple MV (7 models) | 170/198 | 85.9% | Debate adds +1.0 pp |
| Weighted MV (7 models) | 169/198 | 85.4% | 20q calibration weights |
| Phase 22 CGD (3 models) | 171/198 | 86.4% | Previous SOTA |
| Oracle (any of 7) | 191/198 | 96.5% | Diversity ceiling |

**McNemar**: CGD-7 vs Phase 22 CGD: +0.5 pp, χ² = 0.0, p = 1.0 (not significant). Contingency: both correct 161, only CGD-7 correct 11, only Phase 22 correct 10, both wrong 16.

### 9.6.5 Debate Type Analysis

| Type | N (%) | Accuracy |
|------|-------|----------|
| Unanimous (7/7) | 105 (53%) | 99.0% |
| Supermajority (6/7) | 23 (12%) | 82.6% |
| Strong majority (5/7) | 22 (11%) | 81.8% |
| Simple majority (4v3) | 21 (11%) | 66.7% |
| No majority | 27 (14%) | 63.0% |

75.8% of questions locked without debate, achieving 93.3% accuracy on locked questions vs 64.6% on debated questions.

### 9.6.6 Cross-Vendor Diversity

| Group | Models | MV | Oracle |
|-------|--------|-----|--------|
| US (3) | Grok, Gemini, Claude | **86.9%** | 96.0% |
| CN (4) | Qwen, DeepSeek, GLM, Kimi | 76.3% | 88.4% |
| All 7 | Combined | 85.9% | **96.5%** |

Cross-vendor disagreement: 40/198 = 20.2%. US-only MV (86.9%) matches CGD-7 (86.9%), indicating Chinese models add no net accuracy benefit to this ensemble.

### 9.6.7 Per-Domain Results

| Domain | N | CGD-7 | Best solo |
|--------|---|-------|-----------|
| Physics | 86 | **97.7%** | 97% (Grok) |
| Chemistry | 93 | 79.6% | 83% (Grok) |
| Biology | 19 | 73.7% | 79% (Claude) |

### 9.6.8 Minority-Was-Right Analysis

| Model | Minority count | Minority correct | Rate |
|-------|----------------|-----------------|------|
| Grok 4.1 | 20 | 10 | **50%** |
| Gemini 3 Flash | 27 | 9 | 33% |
| Claude Sonnet 4.6 | 22 | 4 | 18% |
| Kimi K2.5 | 23 | 3 | 13% |
| DeepSeek V3.2 | 28 | 3 | 11% |
| GLM-5 | 36 | 4 | 11% |
| Qwen3.5-397B | 22 | 1 | 5% |

When Grok dissents from the majority, it is correct 50% of the time — the strongest minority signal. Qwen's minority dissent is almost never correct (5%).

### 9.6.9 Key Findings

1. **Quality > Quantity**: Scaling from 3 to 7 models yields +0.5 pp (p = 1.0, ns). The additional weaker models dilute ensemble quality.

2. **Solo beats ensemble**: Grok 4.1 solo (87.4%) outperforms CGD-7 (86.9%) at ~1/8 the cost ($1.50 vs $11.35). This establishes a hard limit on debate-based aggregation when model quality varies widely.

3. **Oracle gap**: 96.5% oracle ceiling proves the ensemble collectively knows the answer to 191/198 questions. The gap between actual (86.9%) and theoretical (96.5%) represents 19 recoverable questions — 9.6 pp of potential improvement through better aggregation.

4. **Cross-vendor diversity adds oracle, not accuracy**: Chinese models raise oracle from 96.0% to 96.5% but contribute zero MV accuracy improvement. The diversity is real but current aggregation cannot exploit it.

5. **Extraction failures remain critical**: Qwen3.5-397B's 54 extraction failures (27%) effectively remove it from ~1/4 of votes, making it a liability rather than an asset.

6. **Cost**: $11.35 total (1,822 API calls, 4.4M tokens), $0.057/question, $0.066/correct answer.

---

## 10. Phases 14--15: Memory and CARE-ALERT

### 10.1 Phase 14: The Hypercorrection Paradox

Phase 14 tested ARRIVAL-MNEMO, a persistent 4-layer memory architecture (Episodic, Procedural, Semantic, Meta), using cognitive scars extracted from Phase 13 errors.

**Result**: Global memory injection **degraded accuracy by −5.7 pp** versus baseline ARRIVAL. This hypercorrection effect occurs when past errors overly constrain current reasoning, causing agents to avoid patterns superficially similar to previous mistakes even when those patterns are correct.

### 10.2 Phase 15: Gated CARE-ALERT

Instead of injecting all memories globally, the system monitors Meaning Debt in real time and fires `@CARE.ALERT` atoms only when semantic divergence exceeds a threshold:
- After Round 2: MD > 0.5 triggers gentle alert
- After Round 3: MD > 0.8 triggers urgent alert

**Result**: Gated CARE-ALERT restored baseline accuracy while significantly improving CARE Resolve quality (Mann-Whitney U test, p = **0.042**). This is the first statistically significant improvement from memory intervention in multi-agent LLM coordination.

**Broader principle**: Naive augmentation of LLM systems (memory, tools, context) can be counterproductive. Monitoring internal coordination metrics provides a principled mechanism for knowing *when* to intervene.

---

## 11. Phase 18: Applied Software Engineering Case Studies (Exploratory, N=1)

### 11.1 Motivation

Phases 13--17 validated ARRIVAL on MCQ benchmarks. Phase 18 extends to practical open-ended software engineering tasks where there is no single correct answer.

> **Note**: Phase 18 results are *exploratory case studies* with N=1 per condition. No statistical claims are made. These serve as qualitative illustrations of ARRIVAL's behavior on practical tasks, not as quantitative evidence of superiority or inferiority.

### 11.2 Experimental Design

Three conditions, two tasks:

| Condition | Description | Models |
|-----------|-------------|--------|
| A: Solo | Claude Sonnet 4.5 | 1 frontier model |
| B: ARRIVAL | 5-model heterogeneous | GPT-4.1, DeepSeek V3.2, Mistral Large 3, Gemini 3 Flash, Grok 4.1 Fast |
| C: ARRIVAL+Mem | Same + CARE-ALERT | Same 5 + memory seeds |

### 11.3 Task 1: Security Audit (Analytical)

Flask web application with 10 intentional vulnerabilities + 2 bonus issues.

| Metric | Solo | ARRIVAL | ARRIVAL+Mem |
|--------|------|---------|-------------|
| Bugs found | **10/10** | **10/10** | **10/10** |
| Bonus issues | 2/2 | 2/2 | 2/2 |
| Cost | $0.12 | $0.14 | $0.14 |
| CARE Resolve | N/A | 0.500 | 0.500 |
| Memory injected | N/A | No | **Yes (6)** |

Ceiling effect: all conditions achieve 100%. CARE = 0.500 (analytical task, divergent opinions) correctly triggers memory injection. Cost parity: ARRIVAL only 17% more expensive.

### 11.4 Task 2: Code Generation (Constructive)

FastAPI REST API implementation with 15 objective pytest tests.

| Metric | Solo | ARRIVAL | ARRIVAL+Mem |
|--------|------|---------|-------------|
| Tests passed | **9/15 (60%)** | 8/15 (53%) | 7/15 (47%) |
| Cost | $0.12 | $0.13 | $0.12 |
| CARE Resolve | N/A | 0.979 | 0.973 |
| Memory injected | N/A | No | **No (CARE > 0.7)** |

Solo achieves narrow advantage on code synthesis. CARE = 0.979 (constructive task, convergent solutions) correctly suppresses memory injection.

### 11.5 CARE as Task Discriminator

| Task Type | CARE | Memory | Interpretation |
|-----------|------|--------|---------------|
| Analytical (audit) | 0.500 | Yes | Divergence on subjective assessments |
| Constructive (code) | 0.979 | No | Convergence on structured output |
| Cooperation (Phase 19) | 0.969 | No | Convergence on fair allocation |

CARE Resolve enables adaptive orchestration: inject memory when CARE is low (agents disagree significantly), suppress when high (protocol self-sufficient).

### 11.6 Central Finding

**Five cheaper models match one frontier model at comparable cost ($0.14 vs $0.12)**, while providing vendor independence, fault tolerance, audit trails, and formal consensus metrics.

---

## 12. Phase 19: GovSim Harvest Negotiation (Cooperation)

### 12.1 Motivation

GovSim (Piatti et al., NeurIPS 2024) showed 12/15 LLM models achieve 0% survival in a shared resource management game. La Malfa et al. (2025) identified three structural causes: no native social behavior, ambiguous NL communication, no quantitative emergence metrics. Phase 19 tests whether ARRIVAL's structured atoms and CRDT metrics solve this cooperation problem.

### 12.2 Game Environment

- **Fish pond**: initial stock = 100, max capacity = 100
- **Agents**: 5 heterogeneous LLMs (GPT-4.1, DeepSeek V3.2, Mistral Large 3, Gemini 3 Flash, Grok 4.1 Fast)
- **Duration**: 12 months per game
- **Replenishment**: min(2 × remaining_after_harvest, 100)
- **Collapse**: stock < 5 after harvesting → game over
- **Fair share**: (100 − 5) / 5 = 19 fish per agent per month
- **Scale**: N=5 runs per condition, seeds = [42, 137, 256, 512, 1024]

### 12.3 ARRIVAL Adaptation for Cooperation

For Phase 19, the 4-round protocol operates monthly:
- **R1**: Each agent proposes `@HARVEST[amount=N]` independently
- **R2**: Cross-critique of all proposals using `@CONSENSUS`/`@CONFLICT`
- **R3**: CRDT overlay computes CARE Resolve using harvest greediness as position
- **R4**: Epsilon synthesizer produces `@ALLOCATION[alpha=N, beta=N, ...]` — **binding and enforced**

The binding R4 allocation is the key mechanism: individual agents cannot defect because the allocation, not their proposal, determines actual harvest.

### 12.4 Results

| Condition | Survival | Months | CARE avg | MD avg | Gini | Cost | Calls |
|-----------|----------|--------|----------|--------|------|------|-------|
| **A: Baseline** | **0/5 (0%)** | 4.0 | N/A | N/A | 0.155 | $0.04 | 125 |
| **B: ARRIVAL** | **5/5 (100%)** | 12.0 | 0.970 | 0.003 | 0.001 | $1.89 | 660 |
| **C: ARRIVAL+Mem** | **5/5 (100%)** | 12.0 | 0.960 | 0.006 | 0.001 | $1.88 | 660 |
| **D: Binding-only** | **5/5 (100%)** | 12.0 | N/A | N/A | 0.000 | $0.06 | 60 |
| **E: Adversarial R4** | **5/5 (100%)** | 12.0 | 0.918 | 0.010 | 0.800 | $1.89 | 660 |

Fisher exact test: A vs B, A vs C, A vs D, A vs E: all **p = 0.008** (significant at 0.01 level). B vs D: p = 1.000 (no difference in survival).

### 12.5 Baseline Collapse Patterns (N=5)

All 5 baseline runs collapse within 3--6 months (average: 4.0 months). Without coordination structure, agents consistently extract more than the sustainable share. Even with 2025--2026 frontier models (GPT-4.1, Gemini 3 Flash), the baseline replicates GovSim's 0% survival finding.

### 12.5b Comparison with Homogeneous Frontier Swarms

Piatti et al. (2024) and Curvo et al. (2025) report that certain frontier models achieve 100% survival when deployed as homogeneous 5-agent swarms:

| System | Models | Survival | Months | Heterogeneous? | Protocol? |
|--------|--------|----------|--------|:-:|:-:|
| GPT-4o × 5 (Piatti) | 1 frontier | 100% | 12.0 ± 0.0 | No | No |
| GPT-4-turbo × 5 (Piatti) | 1 frontier | 100% | 12.0 ± 0.0 | No | No |
| DeepSeek-V3 × 5 (Curvo) | 1 frontier | 100% | 12.0 ± 0.0 | No | No |
| **ARRIVAL** | **5 budget** | **100%** | **12.0** | **Yes** | **Yes** |

The comparison reveals a qualitative distinction: frontier homogeneous swarms succeed through *model capability* (GPT-4o is individually capable enough to cooperate). ARRIVAL succeeds through *protocol structure* — five budget-tier models (GPT-4.1 mini, DeepSeek V3.2, Mistral Large 3, Gemini 3 Flash, Grok 4.1 Fast), none of which would survive individually, achieve the same outcome through structured coordination. This is Ostrom's principle instantiated in silico: institutions (protocol), not agents (model size), determine cooperation.

### 12.6 ARRIVAL Per-Run Details (N=5)

| Run | Seed | CARE avg | Gini | Total fish | Final stock | Notable event |
|-----|------|----------|------|------------|-------------|---------------|
| 0 | 42 | 0.990 | 0.000 | 645 | 10 | Clean run, steady CARE 0.96--1.00 |
| 1 | 137 | 0.938 | 0.001 | 624 | 10 | CARE dip to 0.58 (Month 4), MD spike to 0.132 |
| 2 | 256 | 0.981 | 0.000 | 645 | 10 | Clean run, CARE never below 0.95 |
| 3 | 512 | 0.968 | 0.001 | 644 | 10 | Endgame CARE dip to 0.91 (Months 11--12) |
| 4 | 1024 | 0.976 | 0.000 | 640 | 20 | Conservative; 128/agent, 20 fish remaining |

**CARE trajectories**:
- Run 0: [0.99, 1.00, 0.99, 1.00, 0.99, 1.00, 0.99, 1.00, 0.98, 0.99, 0.99, 0.96]
- Run 1: [0.96, 0.98, 0.99, **0.58**, 0.95, 0.99, 0.98, 1.00, 0.95, 0.99, 0.98, 0.91]
- Run 2: [0.96, 1.00, 0.95, 1.00, 0.99, 0.98, 0.98, 0.98, 0.99, 0.98, 1.00, 0.96]
- Run 3: [1.00, 0.97, 0.98, 0.99, 0.95, 0.95, 1.00, 0.99, 0.98, 0.98, 0.91, 0.91]
- Run 4: [0.98, 0.93, 1.00, 0.95, 0.98, 0.99, 0.99, 1.00, 0.98, 1.00, 0.95, 0.96]

CARE reaches 1.000 (perfect consensus) in 4 of 5 runs. The most significant anomaly occurs in Run 1 Month 4 (CARE = 0.58, MD = 0.132), yet the system self-corrects to CARE = 0.95 by Month 5 — a single-cycle recovery.

**Resource trajectories**: All 5 runs maintain stock = 100 for 10--11 consecutive months, then rational end-game depletion (final stock 10--20).

### 12.7 Self-Healing Mechanism and Defection Taxonomy

Across 25 runs (5 conditions × 5 runs), ARRIVAL absorbs and neutralizes every observed defection within a single CARE cycle. We identify two qualitatively distinct defection types, both neutralized by the same mechanism:

**Type 1: Severe CARE disruption** — proposals or interactions causing CARE below 0.70.

**Run 1 Month 4 (Condition B): CARE = 0.58, MD = 0.132**:
- The most severe CARE disruption across all runs
- CARE recovers to 0.95 by Month 5
- Recovery time: **1 cycle**

**Run 4 Month 1 (Condition C): CARE = 0.52, MD = 0.175**:
- Delta proposes greedy harvest (greediness = 0.58)
- Triggers CARE-ALERT: 8 memories injected at Month 2
- CARE recovers to 0.97 by Month 3
- Recovery time: **1--2 cycles**

**Type 2: Moderate greed proposals** — proposals exceeding fair share but absorbed without severe CARE disruption.

**Delta's 50-fish proposals** (observed in Condition C Run 1 and Condition E Run 2):
- Delta (Gemini Flash) proposes @HARVEST=50, confusing total sustainable harvest with per-agent amount
- R2: Cross-critique → correction to 10
- R4: Equal allocation
- CARE remains above 0.90
- Recovery time: **1 cycle**

**Self-healing summary metric (N=5)**:

| Condition | Run | Month | CARE Drop | MD Spike | Recovery Time |
|-----------|-----|-------|-----------|----------|---------------|
| B | 1 | 4 | 0.99→0.58 | 0.132 | 1 month |
| C | 4 | 1 | →0.52 | 0.175 | 1--2 months |
| C | 2 | 9 | →0.60 | 0.128 | 1 month |
| B | 3 | 11 | →0.91 | — | endgame |
| B | 4 | 2 | →0.93 | — | 1 month |

All defection events are neutralized within 1--2 CARE cycles regardless of magnitude. The protocol does not *prevent* defection — agents remain free to propose greedy harvests — but it *absorbs* defection through cross-critique and binding R4 allocation. This is a *resilience* property, not a prevention mechanism. Prevention is fragile (fails when defection exceeds the threshold); resilience functions regardless of defection severity.

This self-healing property provides empirical confirmation of Theorem 5 (exponential convergence): after perturbation, CARE returns to equilibrium within 1--2 rounds. The strongest test case — CARE dropping to 0.52 with MD = 0.175 — still recovers fully, demonstrating robustness even under severe disruption.

### 12.8 Harvest Equality

**Condition B cumulative harvests (per agent, 12 months, N=5)**:

| Agent | Run 0 | Run 1 | Run 2 | Run 3 | Run 4 |
|-------|-------|-------|-------|-------|-------|
| Alpha | 129 | 125 | 129 | 129 | 128 |
| Beta | 129 | 125 | 129 | 129 | 128 |
| Gamma | 129 | 124 | 129 | 128 | 128 |
| Delta | 129 | 125 | 129 | 129 | 128 |
| Epsilon | 129 | 125 | 129 | 129 | 128 |

Maximum within-run spread: **1 fish** (Run 1, Run 3). Average Gini = 0.001.

**Condition D (Binding-only) cumulative harvests**:

| Agent | Run 0 | Run 1 | Run 2 | Run 3 | Run 4 |
|-------|-------|-------|-------|-------|-------|
| Each agent | 120 | 84 | 129 | 102 | 111 |

Perfect within-run equality (Gini = 0.000) but high between-run variance: 84--129 fish/agent depending on when the Grok allocator pivots from conservative (10/agent) to extractive (19/agent) allocation.

**Condition E (Adversarial R4) cumulative harvests**:

| Agent | All 5 Runs |
|-------|------------|
| Alpha--Delta | 0 each |
| Epsilon | 150 |

Gini = 0.800 (maximum inequality). The adversarial allocator captures 100% of total harvest.

**Total yield comparison**: Condition B extracts 640 fish on average vs 200 for baseline — **3.2× more** from the same initial resource. Condition D extracts 546 on average, Condition E only 150 (parasitic equilibrium drains the commons).

### 12.9 Memory Gating Behavior

Condition C: **1 memory injection** across 60 monthly checks (5 runs × 12 months). Run 4 triggered CARE-ALERT at Month 2 when Delta's greedy proposal caused CARE to drop to 0.52 (MD = 0.175, greediness = 0.58 > threshold 0.50). Eight memory seeds were injected, and CARE recovered to 0.97 by Month 3.

The remaining 59 monthly checks correctly suppressed memory injection (CARE > 0.5 threshold), confirming that for cooperation tasks the protocol is largely self-sufficient. The single injection demonstrates that the CARE-ALERT mechanism *can* activate when warranted, while its 98.3% suppression rate (59/60) shows appropriate discrimination.

### 12.10 Statistical Analysis (N=5)

**Survival comparisons (Fisher exact test, two-sided)**:

| Comparison | Survival | Fisher p | Mann-Whitney U | p (months) | Sig. |
|------------|----------|----------|---------------|------------|------|
| A vs B | 0% vs 100% | **0.008** | 0.0 | 0.007 | *** |
| A vs C | 0% vs 100% | **0.008** | 0.0 | 0.007 | *** |
| A vs D | 0% vs 100% | **0.008** | 0.0 | 0.007 | *** |
| A vs E | 0% vs 100% | **0.008** | 0.0 | 0.007 | *** |
| B vs C | 100% vs 100% | 1.000 | 12.5 | 1.000 | n.s. |
| B vs D | 100% vs 100% | 1.000 | 12.5 | 1.000 | n.s. |
| B vs E | 100% vs 100% | 1.000 | 12.5 | 1.000 | n.s. |
| D vs E | 100% vs 100% | 1.000 | 12.5 | 1.000 | n.s. |

All baseline comparisons reach **p = 0.008** (significant at the 0.01 level). The Mann-Whitney U = 0.0 indicates complete separation of month distributions (4.0 ± 0.9 vs 12.0 ± 0.0). No pairwise comparison among conditions B--E reaches significance, as all achieve 100% survival.

**MD-collapse correlation**: Spearman rho = NaN (all ARRIVAL conditions survived 12 months; no variance in months-to-collapse for correlation analysis). This is a ceiling effect — the protocol is too effective for the current game difficulty to produce partial failures.

**@-Atom analysis (N=5)**:

| Atom type | Condition B | Condition C | Condition E |
|-----------|-------------|-------------|-------------|
| @CONSENSUS | 831 | 837 | 0 |
| @CONFLICT | 821 | 848 | 0 |
| @RESOLUTION | 511 | 557 | 0 |
| @EVIDENCE | 774 | 787 | 0 |
| @HARVEST | 912 | 905 | 0 |

Conditions B and C: cooperation ratio = (consensus + resolution) / (consensus + resolution + conflict) = **0.620** (B) and **0.621** (C), indicating cooperative dominance. Condition E shows zero atoms because the adversarial R4 allocator ignores deliberation output entirely.

### 12.11 Theoretical Implications

Phase 19 provides empirical support for MEANING-CRDT v1.1:
- **Theorem 1**: Equal allocation emerges as the CARE-optimal solution with equal weights
- **Theorem 5**: After greedy perturbations, CARE recovers within 1--2 rounds (exponential convergence). Confirmed across 25 runs: worst-case CARE = 0.52 recovers to 0.97 in 1--2 cycles.
- **Theorem 6**: MD remains bounded across 180 monthly measurements (3 CRDT conditions × 5 runs × 12 months). Maximum observed MD = 0.175 (Condition C, Run 4, Month 1), well within theoretical bounds.
- **Theorem 8**: Greedy proposals are detected and corrected by cross-critique (incentive structure)

### 12.12 Ablation Analysis: Condition D (Binding-Only)

**Question**: Is the binding R4 allocation alone sufficient for cooperation, or is structured debate (R1--R2) causally necessary?

**Design**: Condition D removes all deliberation rounds. A single Grok 4.1 Fast agent receives the game state and produces `@ALLOCATION[alpha=N, beta=N, ...]` directly — no R1 proposals, no R2 cross-critique, no R3 CRDT computation.

**Result**: 5/5 survival (100%), Gini = 0.000, average 109 fish/agent. **Binding alone is sufficient for survival on GovSim.**

| Metric | B (Full ARRIVAL) | D (Binding-only) | Difference |
|--------|-----------------|-------------------|------------|
| Survival | 5/5 (100%) | 5/5 (100%) | None |
| Gini | 0.001 | 0.000 | Negligible |
| Cost | $1.89 | $0.06 | **32× cheaper** |
| API calls | 660 | 60 | **11× fewer** |
| Avg fish/agent | 130 | 109 | B extracts 19% more |
| Transparency | Full R1-R2 traces | None | D is opaque |

**Interpretation**: On GovSim — a game with a known optimal strategy (equal allocation of sustainable share) — a single rational allocator with binding authority is sufficient. The debate rounds (R1--R2) add three properties not captured by survival rate: (1) **transparency** (full per-agent reasoning traces), (2) **CARE/MD monitoring** (real-time divergence detection), and (3) **yield optimization** (B extracts 19% more fish through endgame coordination).

**Confound acknowledged**: This result means that GovSim alone cannot distinguish between "ARRIVAL enables cooperation" and "any binding allocation enables cooperation." GovSim is a necessary-but-not-sufficient test — future work requires games where the optimal strategy is non-obvious and cannot be computed by a single agent (e.g., asymmetric resource games, variable externalities, or games requiring negotiation over heterogeneous preferences).

### 12.13 Ablation Analysis: Condition E (Adversarial R4)

**Question**: What happens when the R4 synthesizer is adversarial? Is R4 a single point of trust?

**Design**: Condition E preserves the full 4-round structure (R1--R3 with cooperative agents), but replaces the R4 synthesizer with a selfish Epsilon instructed to maximize its own harvest. The safety clamp limits total harvest to `floor(stock / 2)` but does not enforce fairness.

**Result**: 5/5 survival (100%), but Gini = 0.800 and Epsilon captures 100% of total harvest.

| Metric | B (Full ARRIVAL) | E (Adversarial R4) | Interpretation |
|--------|-----------------|---------------------|----------------|
| Survival | 5/5 (100%) | 5/5 (100%) | Safety clamp preserves resource |
| Gini | 0.001 | **0.800** | Total inequality |
| Epsilon share | 20% | **100%** | Parasitic capture |
| Total yield | 640 | 150 | 76% yield reduction |
| CARE (R1-R3) | 0.970 | 0.918 | Deliberation still cooperative |
| Fish/non-epsilon | 128 | **0** | Complete exclusion |

**Mechanism**: In Month 1, the adversarial Epsilon allocates 95 fish to itself (clamped from a higher request by the safety clamp). Stock drops from 100 to 5, then doubles to 10. For Months 2--12, Epsilon takes 5 fish/month (the entire safe harvest), while Alpha--Delta receive 0. The safety clamp prevents total stock collapse but does not redistribute — it is a survival mechanism, not a fairness mechanism.

**Key finding**: R4 is a **single point of trust**. The binding allocation that makes cooperation possible (Conditions B, C, D) also makes exploitation possible when the allocator is adversarial. The safety clamp acts as a "last resort" that preserves the resource at the cost of fairness.

**CARE behavior under adversarial R4**: CARE in R1--R3 deliberation remains moderately high (0.918 average) because the four cooperative agents discuss coherently among themselves. The injustice is structurally imposed at R4, *after* deliberation concludes. This reveals that CARE measures *deliberation quality*, not *allocation fairness* — an important distinction for future metric design.

**Mitigations** (not tested): Rotating synthesizer selection, multi-agent R4 voting, cryptographic commitment to R2 consensus, or a fairness clamp (min allocation per agent > 0).

---

## 13. Discussion

### 13.1 What ARRIVAL Adds Beyond Strong Prompting

Wang et al. (2024) raised the key challenge: can single-agent CoT match multi-agent performance? Phase 17 confirmed this on 40 questions (70% vs 65%, p = 0.812), and Phase 20 scaled the comparison to the full 198-question GPQA Diamond with mid-tier models: ARRIVAL MV reaches 67.7% vs Solo CoT MV 62.1% (+5.6 pp, McNemar p = 0.233, n.s.). Phase 21 escalates further with frontier-tier models (GPT-4.1, Gemini 3 Flash, Grok 4.1 Fast): Non-Debate MV reaches 82.3% vs ARRIVAL MV at 78.8% (−3.5 pp, McNemar p = 0.265, n.s.). **The debate effect inverts with stronger models** — from slightly positive to slightly negative.

The mechanism is **anchoring**: Gemini 3 Flash (82.3% solo) drops to 78.3% when debating, because it sees GPT-4.1's weaker proposals (66.2% solo) first as R2 critic and sometimes abandons its own correct answer. This establishes a fundamental limitation: structured debate on MCQ benchmarks adds noise, not signal, when models are individually capable. The effect is consistent across three experiments (Phase 17, 20, 21) and two sample sizes (N=40, N=198): the debate effect is statistically indistinguishable from zero.

Beyond raw accuracy, ARRIVAL provides structural value:

1. **Auditability**: Full per-agent reasoning traces with @-atom annotations
2. **Consensus measurement**: CARE Resolve provides real-time quality metrics
3. **Defection detection**: Meaning Debt identifies greedy/adversarial behavior
4. **Vendor independence**: Heterogeneous models eliminate single-vendor lock-in
5. **Cooperation**: Phase 19 demonstrates that ARRIVAL enables sustained cooperation where solo agents fail completely (0% → 100% survival, Fisher p = 0.008). Ablation shows binding R4 is the causal mechanism; debate adds transparency and yield optimization.
6. **Rescue capability (limited)**: Phase 20 shows ARRIVAL R4 rescues 7 questions where MV fails, at the cost of 9 regressions. Phase 21 confirms the pattern: 8 rescues vs 13 regressions. The R4 finalizer is consistently net negative, suggesting majority voting of R1-R3 is preferable to sequential synthesis.
7. **Protocol evolution**: Phase 22's Confidence-Gated Debate (CGD) demonstrates that rigorous failure analysis of sequential debate (anchoring, R4 regressions) can yield a superior protocol variant. CGD achieves **86.4%** on the full 198-question GPQA Diamond (Phase 22, 3 models) and **86.9%** with a 7-model cross-vendor ensemble (Phase 23). However, Phase 23 reveals a fundamental limit: Grok 4.1 solo (87.4%) outperforms the 7-model CGD ensemble — establishing that for MCQ tasks, model quality dominates model quantity when weaker models are added.

### 13.2 CARE as Adaptive Coordination Signal

CARE Resolve emerges as a multi-purpose signal across three task types:

| Task Type | CARE Range | Interpretation | Action |
|-----------|-----------|----------------|--------|
| Analytical (Phase 18 audit) | ~0.50 | High divergence, need memory | Inject CARE-ALERT |
| Constructive (Phase 18 code) | ~0.97 | Convergent, protocol sufficient | Suppress memory |
| Cooperation (Phase 19) | ~0.97 | Convergent, protocol sufficient | Suppress memory |

This enables **adaptive orchestration**: allocate expensive memory resources only where CARE indicates they are needed. Future work could extend this to dynamic model selection, round count adjustment, and budget allocation.

### 13.3 Cost-Efficiency

| Comparison | Cost | Benefit |
|------------|------|---------|
| ARRIVAL vs Solo (Phase 18) | $0.14 vs $0.12 | 5 perspectives, vendor independence |
| ARRIVAL vs Baseline (Phase 19) | $1.89 vs $0.04 | 0% → 100% survival, 3.2× fish |
| Binding-only vs ARRIVAL (Phase 19) | $0.06 vs $1.89 | Same survival, 32× cheaper |
| ARRIVAL 198q (Phase 20) | $7.65 total | $0.039/q, 792 API calls |
| Solo CoT 198q (Phase 20) | $2.66 total | $0.013/q, 990 API calls |
| ARRIVAL + 3 solos (Phase 21) | $9.63 total | $0.049/q, 1,386 API calls |
| CGD 198q (Phase 22) | $5.72 total | $0.029/q, 692 API calls |
| CGD-7 198q (Phase 23) | $11.35 total | $0.057/q, 1,822 API calls |
| All 2,200+ experiments | < $95 total | Full research program |

The total cost under $95 for 2,200+ experiments across 23 phases demonstrates that structured multi-agent coordination is practical at research-paper scale. Phase 22 CGD is notably cost-efficient at $0.029/question because ~62% of questions resolve unanimously with only 3 API calls. Phase 23's 7-model CGD costs $0.057/question (2× Phase 22) for only +0.5 pp accuracy improvement, illustrating the diminishing returns of adding models. Agreement-based gating provides natural cost optimization: expensive debate resources are allocated only where genuine disagreement exists.

### 13.4 The Cooperation Argument: Resilience, Not Prevention

Phase 19 provides the strongest argument for structured multi-agent protocols. While Phases 17 (N = 40), 20, and 21 (N = 198 each) show solo models are competitive or superior on MCQ reasoning — cooperation requires multiple agents by definition. ARRIVAL provides the structural framework that enables this cooperation:

1. **@-atoms** replace ambiguous NL with machine-parseable signals
2. **CRDT metrics** detect and quantify divergence in real-time
3. **Binding R4** prevents individual defection
4. **Cross-critique** acts as a social immune system against greed

A critical distinction: ARRIVAL does not *prevent* defection — it *absorbs* it. Agents remain free to propose greedy harvests at any magnitude. The protocol neutralizes defection through structured cross-critique and binding allocation, regardless of severity. This resilience framing is important because prevention-based systems are brittle: they fail when the attack exceeds the design threshold. ARRIVAL's self-healing (1--2 cycle recovery for all observed defection magnitudes, including CARE = 0.52) suggests antifragile properties.

This aligns with Ostrom's (1990) key insight from field research on commons governance: successful institutions do not eliminate self-interest but *channel it through structured communication and monitoring*. ARRIVAL's @-atoms are the communication structure; CARE Resolve and Meaning Debt are the monitoring mechanism; binding R4 allocation is the enforcement layer.

### 13.5 Ablation Insights: What GovSim Can and Cannot Show

The Condition D ablation reveals a critical confound: binding allocation alone achieves 100% survival on GovSim, at 32× lower cost ($0.06 vs $1.89) and 11× fewer API calls. This means GovSim, despite being the standard cooperation benchmark, cannot distinguish between "ARRIVAL enables cooperation" and "any binding allocation enables cooperation."

However, this confound is itself informative. It identifies the *causal mechanism* within ARRIVAL: the binding R4 allocation, not structured debate, is what prevents defection on GovSim. Debate (R1--R2) adds three properties invisible to survival rate: (1) transparency via per-agent reasoning traces, (2) real-time divergence monitoring via CARE/MD, and (3) yield optimization (B extracts 19% more fish than D through endgame coordination).

The Condition E ablation identifies R4 as a **single point of trust**. The same binding mechanism that enables cooperation also enables exploitation when the allocator is adversarial. The safety clamp preserves survival (Gini is about fairness, not about survival) but cannot prevent parasitic capture. This is a genuine architectural vulnerability. Mitigations — rotating synthesizer, multi-agent R4 voting, fairness clamps — are identified but not tested.

Together, Conditions D and E demonstrate intellectual honesty: we report the finding that undermines ARRIVAL's value proposition on GovSim (D), while also identifying a genuine security vulnerability (E). Both findings strengthen the paper by addressing confounds and limitations proactively.

### 13.6 Goodhart's Law and CARE Triple Role

CARE Resolve simultaneously serves three roles: (1) metric (measuring agreement), (2) optimization target (CARE Resolve finds the optimal consensus position via Theorem 1), and (3) trigger (CARE-ALERT fires when CARE drops below threshold). This triple role creates a classic Goodhart concern: when a measure becomes a target, it ceases to be a good measure.

MEANING-CRDT Theorem 8 provides partial mitigation: agents cannot game CARE by inflating importance weights, because CARE optimum is invariant to scalar weight multiplication. However, this addresses only one attack vector. Sophisticated agents could potentially learn to exhibit surface-level agreement (high CARE) while pursuing hidden objectives through subtle semantic manipulation — a form of "semantic deception" where @CONSENSUS atoms mask genuine @CONFLICT.

Current experiments show no evidence of this failure mode, but we emphasize that all agents in our experiments are instruction-following LLMs without adversarial training. Detecting semantic deception in agents with strategic objectives requires future work on CARE integrity verification — potentially through external cross-validation, consistency checking across rounds, or comparison with independent ground-truth metrics.

Future work should develop external validation metrics independent of CARE to ensure that improving CARE corresponds to genuine quality improvement, not merely to agents learning to produce CARE-maximizing outputs.

### 13.7 What ARRIVAL is Not

To prevent misframing, we explicitly state what ARRIVAL does *not* claim to be:

1. **Not AGI alignment.** ARRIVAL coordinates task-level outputs between existing LLMs. It does not address alignment of model values, goals, or reward functions. A misaligned agent using @-atoms remains misaligned.

2. **Not a replacement for RLHF/DPO.** ARRIVAL operates at the coordination layer (system prompts), not at the training layer. It assumes well-trained base models and adds inter-model communication structure.

3. **Not domain-specific.** The protocol is designed to be general, but has been validated only on (a) MCQ benchmarks, (b) software engineering tasks, and (c) one resource management game. Generalization to domains such as medical diagnosis, legal reasoning, or embodied agents remains undemonstrated.

4. **Not a guarantee of truthfulness.** ARRIVAL improves consensus quality through structured critique, but cannot guarantee that the consensus is correct. Echo-chamber metrics detect conformity but not factual error.

5. **Not manipulation-proof.** While Theorem 8 prevents weight inflation attacks, the protocol does not defend against all adversarial strategies. A sufficiently sophisticated agent could potentially manipulate cross-critique to steer consensus in a desired direction.

### 13.8 CGD: Eliminating Anchoring Through Independence

Phase 22's Confidence-Gated Debate (CGD) emerged directly from the failure analysis of Phases 20-21. Three problems were identified in sequential debate: (1) **anchoring bias** — weaker models' answers contaminate stronger models' reasoning, (2) **destructive R4 overrides** — the finalizer changes correct group consensus to wrong answers more often than it rescues (net -5 in Phase 21), and (3) **false consensus** — sequential exposure creates social pressure to agree.

CGD addresses all three by design:
- **Independent solo phase** eliminates anchoring (each model answers before seeing others)
- **Majority vote** replaces R4 (no single point of failure)
- **Agreement-based gating** replaces unconditional debate (debate only when disagreement exists)

This approach is grounded in the **Condorcet Jury Theorem**: independent voters with individual accuracy > 50% produce better collective decisions than correlated voters. CGD operationalizes this by ensuring independence in the solo phase and using correlation (agreement pattern) only as a gating signal for targeted debate.

Recent theoretical work supports this design. Choi et al. (2025) prove that multi-agent debate has a **martingale property**: debate does not change the expected correctness of responses, only their variance. This aligns with our Phase 21 finding that debate is net zero or negative on MCQ accuracy. CGD sidesteps this limitation by reserving debate for cases of genuine disagreement, where variance reduction is most valuable.

CGD's agreement-based gating differs fundamentally from other selective debate approaches:
- **iMAD** (Fan et al., AAAI 2026) uses ML-trained confidence classifiers requiring labeled training data
- **DOWN** (Eo et al., 2025) examines whether natural language is the optimal debate medium
- **Zhou et al. (2025)** investigate disagreement mechanisms but do not propose gating
- **CGD** uses zero-shot inter-model agreement as a gating signal — requiring no training data and inherently robust because it aggregates three independent signals rather than relying on a single model's self-reported confidence

The key insight: LLMs are notoriously poor at self-calibrating confidence (overconfident on wrong answers, underconfident on correct ones). Inter-model agreement is a more reliable proxy for question difficulty because it aggregates three independent assessments. When all three models agree (65% of questions), accuracy is 98.0%; when they disagree, the question is genuinely harder and debate resources are well-spent.

### 13.9 CGD vs GPQA SOTA: Mid-Tier Ensemble vs Frontier Models

CGD's preliminary 90.7% accuracy with three mid-tier models (GPT-4.1 66.2%, Gemini 3 Flash 82.3%, Grok 4.1 Fast 85.4%) invites comparison with frontier single-model SOTA on GPQA Diamond:

| Method | Accuracy | Models | Cost/Question |
|--------|----------|--------|---------------|
| Gemini 3.1 Pro (Google, 2025) | 94.1% | 1 frontier | ~$0.10 |
| GPT-5.3 Codex (OpenAI, 2025) | ~91.5% | 1 frontier | ~$0.15 |
| **CGD (Phase 22, preliminary)** | **90.7%** | **3 mid-tier** | **~$0.028** |
| Oracle ceiling (Phase 21) | 93.9% | 3 mid-tier | — |
| Solo Grok 4.1 Fast | 85.4% | 1 mid-tier | ~$0.006 |

This comparison reveals a striking cost-accuracy tradeoff: CGD achieves ~97% of frontier single-model accuracy at ~20-28% of the cost, while providing vendor independence, transparency (full per-model reasoning traces), and resilience (no single point of failure). For cost-sensitive applications (medical triage, educational assessment, content moderation at scale), this tradeoff may be highly practical.

The 3.2 pp gap between CGD (90.7%) and the oracle ceiling (93.9%) suggests CGD is extracting nearly all available knowledge from the trio. The remaining gap likely represents questions where all three models share the same misconception — a fundamental limitation of any ensemble of models trained on similar data.

---

## 14. Limitations

1. **Binding-only confound**: Condition D demonstrates that binding R4 allocation alone achieves 100% survival on GovSim at 32× lower cost. GovSim cannot distinguish protocol-driven cooperation from allocator-driven cooperation. Games with non-obvious optimal strategies are needed to isolate the debate contribution.
2. **R4 single point of trust (confirmed)**: Condition E confirms that an adversarial R4 synthesizer destroys fairness while preserving survival. The binding mechanism that enables cooperation also enables exploitation. Mitigations (rotating synthesizer, multi-agent R4 voting, fairness clamps) are identified but untested.
3. **Single game type**: Phase 19 tests only fish pond commons. Public goods, prisoner's dilemma, and asymmetric resource games would strengthen the cooperation claim.
4. **No RL-trained adversaries**: Phase 19 adversarial testing uses a prompt-instructed selfish agent, not RL-trained defectors (Piche et al., 2025). RL agents could potentially discover more sophisticated exploitation strategies.
5. **Ceiling effect**: All ARRIVAL conditions (B, C, D, E) achieve 100% survival, preventing statistical comparison between conditions and precluding MD-collapse correlation analysis.
6. **Model version floating**: OpenRouter routes to latest versions, limiting exact reproducibility.
7. **CARE heuristic dependency**: Weight extraction from confidence declarations is heuristic-based.
8. **Debate effect null on MCQ (confirmed)**: Phases 20 and 21 both test all 198 GPQA Diamond questions. Phase 20 shows +5.6 pp (ns), Phase 21 shows −3.5 pp (ns). With frontier models, debate slightly degrades accuracy due to anchoring. The debate effect is statistically indistinguishable from zero across all experiments.
9. **No social agency**: LLM agents lack genuine social agency (La Malfa et al., 2025); coordination is mediated through prompt injection.
10. **Phase 18 N=1**: Applied experiments use single runs per condition.
11. **Code synthesis limitation**: ARRIVAL's 4-round protocol incurs coherence loss during synthesis (R4), disadvantaging code generation tasks.
12. **End-game rationality**: Phase 19 agents increase harvest in Month 12. Infinite-horizon games would better test sustained cooperation.
13. **Phase 22 partial results**: CGD results are based on 75 of 198 GPQA Diamond questions. The preliminary 90.7% accuracy (95% CI: [82.0%, 95.5%]) may change as the remaining 123 questions are processed. All CGD claims should be treated as preliminary.
14. **CGD limited scope**: CGD has been tested only on MCQ (GPQA Diamond) with K=3 models (GPT-4.1, Gemini 3 Flash, Grok 4.1 Fast). Generalization to K > 3, non-MCQ tasks, cooperation scenarios, and different model combinations remains untested.
15. **CGD selection bias**: The first 75 questions may not be representative of the full 198-question distribution. Domain imbalance (Physics 33, Chemistry 35, Biology 7) limits per-domain conclusions.

---

## 15. Conclusion and Future Work

We presented the ARRIVAL Protocol, demonstrating that structured semantic communication enables effective multi-agent LLM coordination across reasoning benchmarks, practical tasks, and game-theoretic cooperation scenarios. The principal results:

1. **Reasoning**: ARRIVAL achieves 65.0% (N = 40) to 78.8% (N = 198, frontier models) on GPQA Diamond. McNemar p = 0.006 against majority voting (Phase 13, N=40). At full scale, Phase 20 (mid-tier) shows ARRIVAL MV 67.7% vs Solo CoT MV 62.1% (+5.6 pp, p = 0.233, ns). Phase 21 (frontier: GPT-4.1 + Gemini 3 Flash + Grok 4.1 Fast) inverts the effect: Non-Debate MV 82.3% vs ARRIVAL MV 78.8% (−3.5 pp, p = 0.265, ns). **Debate does not improve MCQ accuracy** when models are individually capable; the anchoring effect (strong models degraded by weak proposals) is the primary mechanism.
2. **Applied tasks**: Five heterogeneous models match a frontier model at comparable cost, with full transparency and vendor independence.
3. **Cooperation**: **0% → 100% survival** in GovSim commons game (Fisher p = 0.008, N=5) — the first structured multi-agent protocol enabling sustainable commons management for LLMs. Self-healing neutralizes greedy proposals within 1--2 CARE cycles.
4. **Ablation**: Binding R4 allocation is the causal mechanism (Condition D: 100% survival at 32× lower cost). Adversarial R4 (Condition E) identifies a single point of trust: fairness requires trusted allocation.
5. **Memory gating**: Hypercorrection paradox resolved by CARE-ALERT (p = 0.042). CARE Resolve serves as adaptive task discriminator.
6. **Mathematical foundation**: MEANING-CRDT v1.1 provides 8 theorems with formal convergence, bounded debt, and Bayesian equivalence guarantees, confirmed empirically across 180 CRDT-tracked monthly measurements in Phase 19.
7. **CGD**: Phase 22 introduces Confidence-Gated Debate — independent solo answers + agreement-based gating + targeted debate. On the full 198-question GPQA Diamond, CGD achieves **86.4%** with 3 models (Grok, Gemini, GPT-4.1), significantly outperforming ARRIVAL MV (78.8%, +7.6 pp, McNemar p = 0.009). Phase 23 scales CGD to **7 cross-vendor models** (3 US + 4 Chinese), achieving **86.9%** (+0.5 pp vs 3-model CGD, p = 1.0, ns). However, the best solo model (Grok 4.1, 87.4%) outperforms the 7-model ensemble, establishing that model quality dominates model quantity for MCQ aggregation. The 96.5% oracle ceiling (7 models) confirms the knowledge exists but current aggregation cannot fully extract it.
8. **Cross-vendor diversity**: Phase 23 demonstrates that cross-vendor diversity (US avg 83.7% vs CN avg 69.1%) increases oracle coverage (96.0% → 96.5%) but provides zero MV accuracy improvement. The diversity signal exists but is dominated by quality variance between model tiers.

The total cost under $95 USD for 2,200+ experiments across 23 phases demonstrates practical feasibility. Framework-agnostic validation via AutoGen confirms implementation independence.

The trajectory from Phase 21's failure analysis (anchoring, destructive R4) to Phase 22's CGD to Phase 23's scaling experiment illustrates the value of rigorous empirical methodology: each result directly informed the next protocol iteration. CGD's 86.4-86.9% — achieved without the anchoring and R4 regressions that plagued sequential debate — demonstrates that the problem was not model capability but aggregation method. Phase 23's finding that solo Grok (87.4%) outperforms CGD-7 (86.9%) establishes the next research question: how to aggregate diverse models without diluting quality.

### Future Work

1. **Bridge the oracle gap**: Phase 23's 96.5% oracle ceiling vs 86.9% CGD-7 accuracy represents 19 recoverable questions. Promising directions include model-gated voting (exclude Qwen on Chemistry), per-question confidence scoring via logprobs, and adaptive ensemble selection based on domain detection.
2. **Best-K CGD**: Run CGD only on the top-K models by solo accuracy. Phase 23 data suggests that CGD with only the top-3 (Grok, Gemini, Claude) would likely match or exceed CGD-7 at ~1/3 the cost, since US-only MV already equals CGD-7 accuracy (86.9%).
3. **CGD extensions**: Hybrid CGD+ARRIVAL protocols (using @-atoms in the targeted debate phase), CGD vs frontier single-model SOTA, and asymmetric debate (weight Grok's minority dissent — correct 50% of the time — higher than other models).
3. **Debate protocol improvements**: Asymmetric trust weighting (reducing influence of weaker proposers) and adaptive round counts based on real-time CARE measurements remain viable directions for the sequential protocol.
4. **Broader cooperation games**: Public goods, prisoner's dilemma, asymmetric resource games — games where optimal strategy is non-obvious, to isolate the debate contribution from binding-only allocation.
5. **R4 trust mitigations**: Rotating synthesizer selection, multi-agent R4 voting, fairness clamps, cryptographic commitment to R2 consensus.
6. **RL-trained adversaries**: Test against reinforcement-learning-trained defectors (Piche et al., 2025) rather than prompt-instructed selfish agents.
7. **Harder game calibration**: Games requiring partial failure to enable MD-collapse correlation analysis and break the current ceiling effect.
8. **Adaptive orchestration**: Dynamic model selection and round count based on CARE.
9. **Online memory**: Cross-session learning from coordination patterns.
10. **Weight calibration**: Ablation of uniform vs confidence-based vs performance-based CARE weights.
11. **Formal grammar**: BNF/EBNF specification of @-atom wire format for interoperability.
12. **Larger N**: Power analysis from Phase 20 suggests N ≈ 600 is needed to detect a 5 pp effect at 80% power. Cross-benchmark evaluation (MMLU-Pro, ARC-Challenge, MedQA) would provide the necessary statistical power.

---

## References

1. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., & Mordatch, I. (2024). Improving Factuality and Reasoning in Language Models through Multiagent Debate. *ICML 2024*. arXiv:2305.14325.

2. Liang, T., et al. (2024). Encouraging Divergent Thinking in Multi-Agent Debate. *EMNLP 2024*.

3. Li, Y., et al. (2024). Improving Multi-Agent Debate with Sparse Communication Topology. *EMNLP 2024 Findings*.

4. Together AI. (2024). Mixture-of-Agents Enhances Large Language Model Capabilities. arXiv:2406.04692.

5. Li, J., et al. (2025). Rethinking Mixture-of-Agents: Is Mixing Heterogeneous Agents All You Need? arXiv:2502.00674.

6. Wang, Y., et al. (2024). Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Silver Bullet? *ACL 2024*.

7. Smit, M., et al. (2024). Are We Going MAD? Benchmarking Multi-Agent Debate for Medical Q&A. *ICML 2024*.

8. La Malfa, E., et al. (2025). On the Limits of Multi-Agent LLM Systems. *NeurIPS 2025*.

9. Piatti, G., et al. (2024). GovSim: Governance of the Commons Simulation with Language Agents. *NeurIPS 2024*. arXiv:2404.13753.

10. Buscemi, A., et al. (2025). FAIRGAME: Fairness in Language Game-Theoretic LLM Multi-Agent Interactions.

11. Piche, A., et al. (2025). Robust Social Strategies for Multi-LLM Agents.

12. Akata, E., et al. (2023). Playing Repeated Games with Large Language Models. arXiv:2305.16867.

13. Rein, D., et al. (2024). GPQA: A Graduate-Level Google-Proof Q&A Benchmark. arXiv:2311.12022.

14. Shapiro, M., Preguica, N., Baquero, C., & Zawirski, M. (2011). Conflict-free Replicated Data Types. *SSS 2011*.

15. Kelevra, M. (2026). MEANING-CRDT v1.1: Conflict-Free Replicated Data Types for Meaning Negotiation. *Zenodo*. DOI: 10.5281/zenodo.18702383.

16. Hegazy, M. (2024). When Smaller Models Debate Larger Ones. arXiv:2410.12853.

17. Wu, Q., et al. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. *Microsoft Research*.

18. Kim, J., et al. (2025). Scaling Agents: Investigating the Scaling Laws of LLM-based Multi-Agent Systems. arXiv:2512.08296.

19. Ashery, M., et al. (2025). Social Convention Formation in LLM Populations. *Science Advances 2025*.

20. Yang, K., et al. (2025). Revisiting Multi-Agent Debate: Is Discussion the Silver Bullet?

21. Zhu, L., et al. (2025). Demystifying Multi-Agent Debate: The Role of Confidence and Diversity.

22. Cemri, M., et al. (2025). Why Multi-Agent Systems Fail: A Taxonomy of 14 Failure Modes.

23. Nakamura, K., et al. (2025). Colosseum: Collusion Auditing in Multi-Agent Systems.

24. Curvo, R., et al. (2025). GovSim Reproducibility Report: Validating Cooperation Failures.

25. Vallinder, A. & Hughes, E. (2024). Cultural Evolution and Cooperation in LLM Populations.

26. Tran, H., et al. (2025). A Comprehensive Survey on Multi-Agent Systems for LLM Collaboration.

27. Ostrom, E. (1990). *Governing the Commons: The Evolution of Institutions for Collective Action*. Cambridge University Press. (Nobel Prize in Economic Sciences, 2009.)

28. Curvo, R., et al. (2025). Reproducing GovSim: Are LLMs Capable of Governing the Commons? arXiv:2505.09289.

29. Choi, J., et al. (2025). Debate as Martingale: Debate Does Not Improve Expected Correctness of LLM Responses. *NeurIPS 2025*.

30. Fan, X., et al. (2026). iMAD: Informed Multi-Agent Debate with Confidence-Aware Gating. *AAAI 2026*.

31. Kaesberg, J., et al. (2025). The Subtle Art of Defection: Investigating LLMs' Failure to Avoid Tragedy of Commons. *ACL 2025*.

32. Zhou, H., et al. (2025). Can LLMs Debate? Investigating Disagreement Mechanisms in Multi-Agent Systems. arXiv preprint.

33. Eo, T., et al. (2025). DOWN: Debate ON Whether to use Natural Language as Intermediate in Multi-Agent Debate. arXiv preprint.

34. Hintze, A. & Adami, C. (2026). Cooperation Emerges at the Tipping Point of LLM Capabilities. *npj Complexity* 2026.

35. SanctSim Authors. (2025). SanctSim: Simulating the Effects of Sanctions in Multi-Agent LLM Systems.

36. Gemini Team, Google. (2025). Gemini 3.1 Technical Report.

---

## Appendix A: DEUS.PROTOCOL v0.5 Atom Dictionary

The complete specification of all 66 atoms with usage examples and adoption statistics is available in `docs/ATOM_DICTIONARY.md` in the repository.

## Appendix B: MEANING-CRDT v1.1 Full Proofs

Full proofs for all 8 theorems are available at DOI: 10.5281/zenodo.18702383.

## Appendix C: Phase 19 CARE Trajectories (N=5)

**Condition B (ARRIVAL)**:
- Run 0: [0.99, 1.00, 0.99, 1.00, 0.99, 1.00, 0.99, 1.00, 0.98, 0.99, 0.99, 0.96]
- Run 1: [0.96, 0.98, 0.99, 0.58, 0.95, 0.99, 0.98, 1.00, 0.95, 0.99, 0.98, 0.91]
- Run 2: [0.96, 1.00, 0.95, 1.00, 0.99, 0.98, 0.98, 0.98, 0.99, 0.98, 1.00, 0.96]
- Run 3: [1.00, 0.97, 0.98, 0.99, 0.95, 0.95, 1.00, 0.99, 0.98, 0.98, 0.91, 0.91]
- Run 4: [0.98, 0.93, 1.00, 0.95, 0.98, 0.99, 0.99, 1.00, 0.98, 1.00, 0.95, 0.96]

**Condition C (ARRIVAL+Memory)**:
- Run 0: [0.96, 1.00, 0.95, 0.97, 0.98, 1.00, 0.98, 1.00, 1.00, 1.00, 0.97, 0.99]
- Run 1: [0.98, 0.98, 0.99, 0.98, 0.97, 0.98, 0.98, 0.97, 0.97, 0.98, 0.94, 0.96]
- Run 2: [0.99, 1.00, 1.00, 0.96, 0.96, 0.98, 0.98, 0.60, 0.98, 0.98, 0.95, 0.88]
- Run 3: [0.98, 1.00, 0.98, 0.95, 0.99, 0.98, 0.98, 1.00, 0.98, 0.99, 0.96, 0.89]
- Run 4: [0.52, 0.97, 0.93, 0.97, 0.95, 0.98, 0.96, 0.93, 0.98, 0.99, 0.96, 0.97]

**Condition E (Adversarial R4)**:
- Run 0: [0.98, 1.00, 0.90, 0.90, 0.90, 1.00, 0.90, 0.90, 0.90, 1.00, 0.60, 1.00]
- Run 1: [0.98, 0.90, 0.90, 1.00, 0.90, 0.90, 0.90, 1.00, 0.90, 0.98, 0.98, 0.87]
- Run 2: [0.90, 0.90, 0.95, 0.90, 1.00, 0.90, 0.98, 0.90, 0.70, 1.00, 0.90, 0.82]
- Run 3: [0.98, 0.97, 0.97, 0.95, 0.95, 0.90, 0.90, 0.95, 0.93, 0.90, 0.88, 0.90]
- Run 4: [0.90, 0.90, 0.98, 0.90, 0.98, 0.90, 0.90, 0.90, 0.88, 0.95, 0.90, 0.89]

## Appendix D: Reproducibility

All experiment configurations, API logs, prompts, and full model responses are archived in JSON result files within the `experiments/` directory. Random seeds, model versions, and API endpoints are logged for each run. The complete codebase is available under AGPL-3.0. Installation: `pip install -e .`

### Experiment Execution

```bash
# Phase 17
cd experiments/phase17_solo_cot && python run_phase17.py

# Phase 18
cd experiments/phase18_applied && python task1_security_audit/run_solo.py
cd experiments/phase18_applied && python task1_security_audit/run_arrival.py
cd experiments/phase18_applied && python task1_security_audit/run_arrival_memory.py
# (repeat for task2_code_generation)

# Phase 19 (all 5 conditions)
cd experiments/phase19_govsim && python run_baseline.py
cd experiments/phase19_govsim && python run_arrival.py
cd experiments/phase19_govsim && python run_arrival_memory.py
cd experiments/phase19_govsim && python run_binding_only.py
cd experiments/phase19_govsim && python run_adversarial_r4.py
cd experiments/phase19_govsim && python evaluate.py
```

### Cost Summary

| Phase | Experiments | API Calls | Cost (USD) |
|-------|------------|-----------|------------|
| 4--5 | 485 | ~2,000 | ~$2.00 |
| 6--12 | ~80 | ~500 | ~$1.50 |
| 13 | 80 | ~320 | ~$1.00 |
| 14--15 | ~40 | ~200 | ~$0.50 |
| 16 | 200+ | 640 | $1.92 |
| 17 | 200 | 200 | $0.50 |
| 18 | 6 | ~66 | $0.77 |
| 19 | 25 | 2,165 | $5.76 |
| 20 | 198 | ~1,782 | $7.43 |
| 21 | 198+594 | ~1,386 | $9.63 |
| 22 (partial) | 75/198 | ~280 | $2.11 |
| AutoGen | 16 | ~100 | $0.02 |
| **Total** | **2,200+** | **~12,500** | **< $80** |

*Note: Per-phase costs are script-tracked API estimates. Total includes all development iterations, prompt tuning, debugging, and failed runs tracked by OpenRouter.*

---

*Preprint prepared for Zenodo deposition. March 2, 2026.*
*All data, code, and reproducibility instructions available at the linked repository.*
