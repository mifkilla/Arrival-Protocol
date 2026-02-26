# Related Work: Scientific Landscape Analysis

**Author**: Mefodiy Kelevra
**ORCID**: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
**Date**: February 21, 2026
**Project**: ARRIVAL Protocol / Arrival CRDT

---

## Overview

This document provides a comprehensive analysis of the scientific landscape surrounding the ARRIVAL Protocol and its CRDT extension. We categorize related work into five groups: (1) foundational multi-agent debate, (2) structured communication protocols, (3) collective intelligence and emergent coordination, (4) Byzantine fault tolerance for LLM agents, and (5) critical perspectives. For each work, we summarize the methodology, compare with ARRIVAL, identify what we can borrow, and articulate our differentiation.

---

## 1. Foundational Multi-Agent Debate

### 1.1 Du et al. — Multi-Agent Debate (MAD)

**Paper**: "Improving Factuality and Reasoning in Language Models through Multiagent Debate"
**Venue**: ICML 2024 (arXiv:2305.14325, May 2023)
**Authors**: Yilun Du, Shuang Li, Antonio Torralba, Joshua B. Tenenbaum, Igor Mordatch (MIT, Google DeepMind)

**Summary**: The foundational paper introducing the LLM-based multi-agent debate framework. Multiple language model instances propose and debate their individual responses over multiple rounds to arrive at a common final answer. Evaluated on six benchmarks: arithmetic, grade school math, chess reasoning, MMLU, and biography generation.

**Key results**: Multi-agent debate significantly enhances mathematical and strategic reasoning and reduces hallucinations. Both multiple agents and multiple rounds are necessary for optimal performance. The approach works on black-box models without access to internal weights.

**Comparison with ARRIVAL**:
| Dimension | Du et al. (MAD) | ARRIVAL |
|-----------|-----------------|---------|
| Communication | Free-form natural language | Structured @-atoms (66 standard) |
| Architecture | Same-model instances | Cross-architecture (5-8 different LLMs) |
| Formalization | None | CARE Resolve + Meaning Debt (11 theorems) |
| Adversarial | Not tested | Byzantine saboteur (3 attack strategies) |
| Protocol overhead | Zero | Minimal (system prompt injection) |
| Transparency | Opaque debate traces | Parseable atom-annotated transcripts |

**What we borrow**: MAD establishes the baseline that multi-agent debate works. ARRIVAL can be seen as "structured MAD" --- the same insight (multiple perspectives converge on better answers) but with an engineered communication protocol that enables formal analysis.

**Our differentiation**: Du et al. treat debate as a black-box process. ARRIVAL makes the coordination structure explicit and measurable through semantic atoms, enabling quantitative metrics (CARE resolve, meaning debt) that are impossible on free-form debate transcripts.

---

### 1.2 A-HMAD — Adaptive Heterogeneous Multi-Agent Debate

**Paper**: "Adaptive heterogeneous multi-agent debate for enhanced educational and factual reasoning"
**Venue**: Journal of King Saud University (Springer, November 2025)

**Summary**: Extends MAD with diverse specialized agents and dynamic debate mechanisms. Uses heterogeneous agents (different roles/specializations) rather than homogeneous copies of the same model.

**Comparison with ARRIVAL**: A-HMAD's heterogeneity is at the *prompt level* (different role assignments to the same model). ARRIVAL's heterogeneity is at the *architecture level* (fundamentally different neural network architectures with different training data, tokenizers, and attention mechanisms). Our approach tests a stronger form of heterogeneity.

**What we borrow**: The concept of adaptive debate mechanisms (dynamically adjusting debate parameters) could inform our Phase 10 (adaptive defense).

---

### 1.3 DMAD — Diverse Multi-Agent Debate

**Paper**: "Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate"
**Venue**: ICLR 2025 submission

**Summary**: Leverages diverse problem-solving strategies per agent, showing that DMAD consistently outperforms standard MAD with fewer rounds required for convergence.

**Relevance**: Supports the hypothesis that diversity (in strategies, and by extension, architectures) improves debate outcomes --- directly validating ARRIVAL's cross-architecture design philosophy.

---

## 2. Structured Communication Protocols

### 2.1 TalkHier — Talk Structurally, Act Hierarchically

**Paper**: "Talk Structurally, Act Hierarchically: A Collaborative Framework for LLM Multi-Agent Systems"
**Venue**: arXiv:2502.11098 (February 2025)
**Authors**: Zhao Wang, Sota Moriyama, Wei-Yao Wang, Briti Gangopadhyay, Shingo Takamatsu

**Summary**: Introduces a structured communication protocol for context-rich exchanges combined with a hierarchical refinement system. Surpasses OpenAI-o1, AgentVerse, and majority voting on open-domain QA, domain-specific questioning, and advertisement generation tasks.

**Comparison with ARRIVAL**:
| Dimension | TalkHier | ARRIVAL |
|-----------|----------|---------|
| Structure | Hierarchical (top-down refinement) | Peer-to-peer (equal negotiation) |
| Protocol definition | Template-based messages | Semantic atoms (composable tags) |
| Mathematical model | None | MEANING-CRDT (11 theorems) |
| Adversarial testing | None | Byzantine saboteur |
| Cross-architecture | Not specified | Explicitly tested (5-8 LLMs) |

**What we borrow**: The hierarchical refinement concept could enhance our Phase 12 (bottleneck communication), where a relay agent must compress and transmit context between subgroups.

**Our differentiation**: TalkHier is excellent engineering but lacks formal theoretical grounding. ARRIVAL's combination with MEANING-CRDT provides provable guarantees (CARE optimality, bounded meaning debt, incentive incompatibility under attack).

---

### 2.2 LACP — LLM Agent Communication Protocol

**Paper**: "LLM Agent Communication Protocol Requires Urgent Standardization"
**Venue**: arXiv:2510.13821 (October 2025)

**Summary**: Argues that the current ecosystem of inter-agent communication is a patchwork of proprietary protocols creating fragmentation. Proposes LACP: structured, secure, transactional messaging where every message is authenticated, semantically grounded, and executed as part of an atomic transaction.

**Relevance**: LACP is enterprise-focused (security, authentication, transaction integrity). DEUS Protocol is research-focused (semantic expressiveness, emergent coordination, mathematical analysis). Both recognize the need for standardization but address different use cases.

**What we borrow**: The concept of authenticated messages could inform future adversarial defenses --- atoms with provenance tracking would make Trojan Atom attacks detectable.

---

### 2.3 ProtocolBench

**Paper**: "Which LLM Multi-Agent Protocol to Choose?"
**Venue**: arXiv:2510.17149 (October 2025)

**Summary**: Introduces ProtocolBench, a benchmark for evaluating multi-agent communication protocols (A2A, ACP, ANP, Agora) on four scenario families. Provides protocol-agnostic evaluation with structured metrics.

**Relevance**: DEUS Protocol v0.5 could be submitted as a candidate for evaluation in ProtocolBench. This would provide independent validation and visibility for the ARRIVAL approach.

---

### 2.4 AgentsNet — Coordination at Scale

**Paper**: "AgentsNet: Coordination and Collaborative Reasoning in Multi-Agent LLMs"
**Venue**: arXiv:2507.08616 (July 2025)

**Summary**: A multi-agent benchmark built on distributed computing problems, scaling to 100 agents with robust message-passing protocols. While existing multi-agent benchmarks cover 2-5 agents, AgentsNet tests frontier models with up to 100 agents.

**Relevance**: Provides a scaling target for ARRIVAL. Our Phase 9 tests N=5-7 agents; AgentsNet shows the field is moving toward much larger scales. Future work could test ARRIVAL with dozens of agents.

---

## 3. Collective Intelligence and Emergent Coordination

### 3.1 Riedl — Emergent Coordination in Multi-Agent LMs

**Paper**: "Emergent Coordination in Multi-Agent Language Models"
**Venue**: arXiv:2510.05174 (October 2025)
**Author**: Christoph Riedl (Northeastern University)

**Summary**: Introduces an information-theoretic framework to test whether multi-agent LLM systems show higher-order structure beyond mere aggregation. Uses partial information decomposition of time-delayed mutual information (TDMI) to measure dynamical emergence. Key finding: Theory of Mind (ToM) prompts transform groups from "mere aggregates" into "higher-order collectives" with identity-linked differentiation and goal-directed complementarity.

**Comparison with ARRIVAL**:
| Dimension | Riedl | ARRIVAL |
|-----------|-------|---------|
| Emergence measurement | Information-theoretic (TDMI, PID) | Atom-based (adoption rate, emergent count) |
| Coordination mechanism | ToM prompts | @-atom protocol |
| Agent differentiation | Persona-based | Architecture-based + role-based |
| Scale | Small groups, guessing game | 8 architectures, 416+ experiments |

**What we borrow**: Riedl's information-theoretic metrics (synergy, complementarity, redundancy) provide a powerful complementary analysis layer. ARRIVAL's atom-annotated transcripts contain sufficient data to compute TDMI and PID measures, which could quantify whether @-atoms create genuine higher-order structure or merely correlated responses.

**Our differentiation**: Riedl measures emergence post-hoc on unstructured interactions. ARRIVAL *engineers* coordination through atoms and then measures both the engineered structure (atom usage patterns) and emergent extensions (506 novel atoms). This dual perspective --- designed + emergent --- is unique.

---

### 3.2 Ashery et al. — Emergent Social Conventions in LLM Populations

**Paper**: "Emergent Social Conventions and Collective Bias in LLM Populations"
**Venue**: Science Advances, Vol. 11(20), May 2025
**Authors**: Ariel Flint Ashery, Luca Maria Aiello, Andrea Baronchelli

**Summary**: Demonstrates spontaneous emergence of universally adopted social conventions in decentralized LLM populations of 24-200 agents. Key findings: (1) strong collective biases emerge even without individual bias; (2) committed minority groups (2-67% depending on model) can impose alternative conventions through tipping point dynamics; (3) convergence occurs by population round 15 in all cases except the least advanced model.

**Comparison with ARRIVAL**:
| Dimension | Ashery et al. | ARRIVAL |
|-----------|---------------|---------|
| Scale | 24-200 agents | 2-8 agents |
| Coordination | Spontaneous (naming game) | Engineered (@-atoms) |
| Adversarial | Committed minority attack | Byzantine saboteur (3 strategies) |
| Convention type | Simple name convergence | Complex semantic negotiation |
| Formal metrics | Convergence time | CARE resolve + Meaning Debt |

**Key parallel**: Their "committed minority that tips conventions" is a direct analogue of our Byzantine saboteur. Ashery shows the *vulnerability* (tipping points exist); ARRIVAL shows *defense mechanisms* (CARE monitoring detects and resists sabotage).

**What we borrow**: (1) Scale: test ARRIVAL with larger populations in future work. (2) Tipping point analysis: measure what fraction of saboteurs is needed to flip ARRIVAL consensus. (3) Model-dependent resistance: Ashery found committed minority threshold varies 2-67% by model, motivating our Phase 6b (alternative saboteur model) experiment.

---

### 3.3 VLM-TOC — Task-Oriented Communication in VLMs

**Paper**: "Investigating the Development of Task-Oriented Communication in Vision-Language Models"
**Venue**: arXiv:2601.20641 (January 2026)

**Summary**: Investigates whether VLM agents can develop task-oriented communication protocols that differ from standard natural language. Uses referential games to measure two properties: Efficiency (conciseness) and Covertness (interpretability by external observers). Finds that models spontaneously generate new words/symbols and develop covert protocols difficult for humans to interpret.

**Comparison with ARRIVAL**:
| Dimension | VLM-TOC | ARRIVAL |
|-----------|---------|---------|
| Protocol origin | Emergent (spontaneous) | Engineered (@-atoms) |
| Transparency | Can become opaque/covert | Explicitly transparent |
| Modality | Vision + Language | Language only |
| Architecture | Same-model pairs (VLMs) | Cross-architecture (5-8 LLMs) |
| Adversarial | Not tested | Byzantine saboteur |
| Safety implication | Covert = concerning | Transparent = auditable |

**This is our closest competitor.** Both papers study how AI agents communicate in collaborative tasks. The fundamental difference: VLM-TOC discovers that agents *can* develop their own opaque languages (raising safety concerns), while ARRIVAL shows that *engineered* transparent protocols work effectively across architectures (addressing those concerns).

**What we borrow**: Covertness metric --- we could measure how interpretable ARRIVAL dialogues are to external observers vs. free-form debates, quantifying the transparency advantage.

**Our differentiation**: ARRIVAL explicitly addresses the safety concern VLM-TOC raises. If agents develop covert protocols, that is a problem for oversight. @-atoms ensure that all coordination is machine-parseable and human-auditable by design.

---

## 4. Byzantine Fault Tolerance for LLM Agents

### 4.1 CP-WBFT — Confidence Probe-Based Weighted BFT

**Paper**: "Rethinking the Reliability of Multi-agent System: A Perspective from Byzantine Fault Tolerance"
**Venue**: arXiv:2511.10400 (November 2025)
**Authors**: Tian et al.

**Summary**: Designs CP-WBFT, a confidence probe-based weighted Byzantine Fault Tolerant consensus mechanism. Uses Hidden Confidence Probes (HCP) to extract reliability weights from internal model representations. Achieves 100% accuracy on complete graphs at 85.7% fault rate.

**Comparison with ARRIVAL**:
| Dimension | CP-WBFT | ARRIVAL |
|-----------|---------|---------|
| Weight extraction | Internal probes (hidden states) | External signals (@C[value], prose, atom density) |
| Access requirement | White-box (model internals) | Black-box (API only) |
| BFT mechanism | Weighted voting with probes | CARE Resolve optimality |
| Fault tolerance | Up to 85.7% faulty | Tested with 25% saboteur (1/4 agents) |
| Network topology | Various (complete, star, etc.) | Fixed (round-robin dialogue) |

**Key insight**: CP-WBFT and ARRIVAL solve the same problem (Byzantine-robust LLM consensus) from opposite directions. CP-WBFT requires model internals for confidence probing; ARRIVAL works purely through API-level signals. Both use weighted consensus but extract weights differently.

**What we borrow**: Their topology analysis (complete vs. star vs. chain graphs) could inform our network structure experiments. Currently ARRIVAL uses a fixed round-robin topology; testing alternative topologies could improve robustness.

---

### 4.2 DecentLLMs — Byzantine-Robust Decentralized Coordination

**Paper**: "Byzantine-Robust Decentralized Coordination of LLM Agents"
**Venue**: arXiv:2507.14928 (July 2025)

**Summary**: Proposes a decentralized BFT protocol for LLM agents. Identifies a key vulnerability: if consecutive leaders behave maliciously, the system repeatedly fails to achieve consensus, which is costly given high LLM inference latency.

**Relevance**: ARRIVAL's round-based structure (where all agents speak in sequence) avoids the "consecutive leader" vulnerability because there is no single leader. The mediator role is advisory, not authoritative --- advocates can override the mediator's synthesis. This architectural choice provides inherent robustness.

---

### 4.3 BlockAgents — Blockchain-Integrated BFT

**Paper**: "BlockAgents: Towards Byzantine-Robust LLM-Based Multi-Agent Coordination via Blockchain"
**Venue**: ACM TURC 2024

**Summary**: Integrates blockchain for tamper-evident coordination. Reduces poisoning attack impact to <3% and backdoor attack success to <5%.

**Relevance**: Blockchain provides strong guarantees but at significant computational overhead. ARRIVAL achieves adversarial robustness through protocol-level mechanisms (CARE monitoring, atom structure) without any blockchain infrastructure, making it far more lightweight and accessible.

---

### 4.4 BFT-Inspired AI Safety

**Paper**: "A Byzantine Fault Tolerance Approach towards AI Safety"
**Venue**: arXiv:2504.14668 (April 2025)
**Author**: John deVadoss

**Summary**: Argues that BFT principles should inform AI safety: improving individual model robustness is like strengthening a single engine, while BFT is like having multiple engines. Notes that "as LLMs get more powerful, models exhibit emergent behaviors such as 'faking' alignment with safety rules."

**Relevance**: ARRIVAL provides an empirical case study for this vision. Our adversarial experiments demonstrate that structured multi-agent coordination (with CARE monitoring) can detect deceptive agents even when individual models might be fooled. The saboteur that "fakes" consensus through Trojan Atoms is detected because its atoms violate the CARE optimality condition.

---

## 5. Critical Perspectives

### 5.1 La Malfa et al. — "LLMs Miss the Multi-Agent Mark"

**Paper**: "Large Language Models Miss the Multi-Agent Mark"
**Venue**: NeurIPS 2025 Position Track (arXiv:2505.21298)
**Authors**: Emanuele La Malfa et al. (University of Oxford, King's College London)

**Summary**: A systematic critique of the MAS-LLM literature, arguing that much work "appropriates the terminology of MAS without engaging with its foundational principles." Four key criticisms:

1. **Lack of social agency**: LLMs are trained to respond to users, not to interact with each other.
2. **LLM-centric environments**: Non-determinism of LLMs undermines deterministic environment assumptions.
3. **Limited coordination**: Only ~22 of 1,400+ papers model asynchronous interactions.
4. **Overstated emergence**: No benchmarks exist to define, identify, or measure emergence.

**How ARRIVAL addresses each criticism**:

| Criticism | La Malfa's Concern | ARRIVAL's Response |
|-----------|--------------------|--------------------|
| Social agency | LLMs trained for users, not inter-agent | ARRIVAL tests 5-8 *different* LLMs interacting; 116.4% atom adoption rate shows models actively extend the protocol |
| Non-determinism | LLM outputs are stochastic | We run multiple replications per condition and report statistical measures (CIs, effect sizes) |
| Asynchronous | Most work is synchronous | Valid critique; ARRIVAL is synchronous. Phase 12 begins addressing this with bottleneck communication |
| Emergence claims | No metrics | We provide quantitative emergence metrics: 506 emergent atoms, per-model adoption rates, CARE resolve as a formal convergence measure |

**Our position**: La Malfa's critique is valuable and partially applies to ARRIVAL (we are synchronous, we do not model environments). However, we engage substantively with MAS principles through formal communication protocols (DEUS atoms map to speech acts), mathematical convergence guarantees (MEANING-CRDT theorems), and quantitative emergence metrics. We use MAS terminology deliberately and with formal backing, not as loose analogy.

---

### 5.2 ICLR 2025 Blog — MAD Scaling Challenges

**Paper**: "Multi-LLM-Agents Debate: Performance, Efficiency, and Scaling Challenges"
**Venue**: ICLR 2025 Blogposts

**Summary**: Systematic review raising three questions: (1) Does MAD provide performance improvements proportional to computational cost? (2) Does MAD show stable scaling laws? (3) Can MAD effectively aggregate knowledge from different agents?

**Relevance**: These questions apply directly to ARRIVAL. Our Phase 5 data shows that ARRIVAL achieves accuracy parity with majority voting (not superiority), which is consistent with the blog's finding that MAD improvements are task-dependent. However, ARRIVAL provides *richer outputs* (structured reasoning traces, atom-annotated dialogues) at the same accuracy level, which may be more valuable than raw accuracy gains in many applications.

---

## 6. The Unique Position of ARRIVAL

No existing work combines all four of these properties:

1. **Engineered transparent protocol** (66 semantic atoms with formal definitions) --- vs. free-form debate or emergent opaque languages
2. **Cross-architecture validation** (5-8 different LLM architectures) --- vs. same-model instances or single-architecture pairs
3. **Mathematical formalization** (CARE Resolve + Meaning Debt with 11 theorems from MEANING-CRDT v1.1) --- vs. ad-hoc metrics or no formal model
4. **Adversarial robustness testing** (Byzantine saboteur with 3 attack strategies) --- vs. cooperative-only evaluation

This four-dimensional position is unique in the literature as of February 2026. The closest work (VLM-TOC) addresses point 1 from the opposite direction (emergent vs. engineered), but lacks points 2, 3, and 4.

---

## 7. Companion Papers

ARRIVAL is part of a three-paper research program:

1. **DEUS Protocol v7.1** (Kelevra, 2026) --- The theoretical foundation defining the semantic atom system, xenopsychological behavior induction, Constraint Satisfaction Conflict (CSC) model, and UCP Crystallization. Provides the "why" behind the 66 atoms.

2. **MEANING-CRDT v1.1** (Kelevra, 2026) --- The mathematical framework providing CARE Resolve optimality (Theorem 5.1), bounded meaning debt (Theorem 5.8), and incentive incompatibility under Byzantine attack (Theorem 5.11). Provides the formal analysis tools.

3. **ARRIVAL Protocol** (this work) --- The experimental validation demonstrating that the protocol works in practice across 416+ experiments, costs under $5 USD, and resists adversarial attack. Provides the empirical evidence.

---

## 8. Citation Map

### Must cite (core relationship):
- Du et al. (2023) --- foundational MAD framework
- La Malfa et al. (2025) --- must address their critiques
- Riedl (2025) --- information-theoretic emergence measurement
- Ashery et al. (2025) --- social conventions and tipping points
- VLM-TOC (2026) --- closest competitor
- CP-WBFT (2025) --- BFT weight comparison

### Should cite (strong relevance):
- TalkHier (2025) --- structured communication comparison
- A-HMAD (2025) --- heterogeneous debate
- DecentLLMs (2025) --- decentralized BFT
- LACP (2025) --- protocol standardization context
- ProtocolBench (2025) --- benchmark for protocols

### May cite (broader context):
- BlockAgents (2024) --- blockchain BFT approach
- AgentsNet (2025) --- 100-agent scale
- BFT-Inspired AI Safety (2025) --- philosophical framing
- ASRD (2026) --- emergent language interpretation
- DMAD (2025) --- diverse debate strategies

---

## References

1. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., & Mordatch, I. (2023). Improving Factuality and Reasoning in Language Models through Multiagent Debate. *ICML 2024*. arXiv:2305.14325.

2. La Malfa, E., et al. (2025). Large Language Models Miss the Multi-Agent Mark. *NeurIPS 2025 Position Track*. arXiv:2505.21298.

3. Riedl, C. (2025). Emergent Coordination in Multi-Agent Language Models. arXiv:2510.05174.

4. Ashery, A. F., Aiello, L. M., & Baronchelli, A. (2025). Emergent Social Conventions and Collective Bias in LLM Populations. *Science Advances*, 11(20), eadu9368.

5. VLM-TOC Authors (2026). Investigating the Development of Task-Oriented Communication in Vision-Language Models. arXiv:2601.20641.

6. Tian, J., et al. (2025). Rethinking the Reliability of Multi-agent System: A Perspective from Byzantine Fault Tolerance. arXiv:2511.10400.

7. Wang, Z., et al. (2025). Talk Structurally, Act Hierarchically: A Collaborative Framework for LLM Multi-Agent Systems. arXiv:2502.11098.

8. Springer Authors (2025). Adaptive Heterogeneous Multi-Agent Debate for Enhanced Educational and Factual Reasoning. *J. King Saud University*.

9. Jo, Y., et al. (2025). Byzantine-Robust Decentralized Coordination of LLM Agents. arXiv:2507.14928.

10. LACP Authors (2025). LLM Agent Communication Protocol Requires Urgent Standardization. arXiv:2510.13821.

11. ProtocolBench Authors (2025). Which LLM Multi-Agent Protocol to Choose? arXiv:2510.17149.

12. AgentsNet Authors (2025). AgentsNet: Coordination and Collaborative Reasoning in Multi-Agent LLMs. arXiv:2507.08616.

13. BlockAgents Authors (2024). BlockAgents: Towards Byzantine-Robust LLM-Based Multi-Agent Coordination via Blockchain. *ACM TURC 2024*.

14. deVadoss, J. (2025). A Byzantine Fault Tolerance Approach towards AI Safety. arXiv:2504.14668.

15. ASRD Authors (2026). Automated Semantic Rules Detection for Emergent Communication Interpretation. arXiv:2601.03254.

16. ICLR Blog Authors (2025). Multi-LLM-Agents Debate: Performance, Efficiency, and Scaling Challenges. *ICLR 2025 Blogposts*.

17. DMAD Authors (2025). Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate. *ICLR 2025 Submission*.
