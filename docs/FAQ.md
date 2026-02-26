# Frequently Asked Questions (FAQ)

**ARRIVAL Protocol — AI-to-AI Coordination Through Structured Semantic Atoms**

**Author**: Mefodiy Kelevra
**ORCID**: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)

---

## Q1: What is ARRIVAL Protocol?

**Answer**: ARRIVAL Protocol is a cross-architecture AI coordination framework that enables multiple language models to negotiate, reach consensus, and resolve disagreements through structured semantic messaging. Rather than relying on a central arbiter or human mediator, ARRIVAL allows AI agents to communicate using a standardized vocabulary of 66 semantic atoms (the @-atom system defined in DEUS.PROTOCOL v0.5). The protocol has been validated across 400+ experiments spanning 12 phases, achieving a 98.6% consensus rate in dyadic dialogues and 100% accuracy parity with majority voting on MCQ benchmarks. It is designed to be architecture-agnostic, functioning across DeepSeek, Llama, Qwen, Gemma, Mistral, and other model families.

---

## Q2: What are semantic atoms (@-atoms)?

**Answer**: Semantic atoms, or @-atoms, are the fundamental units of structured communication in ARRIVAL Protocol. Each atom is a tagged directive prefixed with `@` that carries a specific semantic meaning within a negotiation context — for example, `@AGREE`, `@DISAGREE`, `@PROPOSE`, `@DOUBT`, `@CLARIFY`, or `@FINALIZE`. The DEUS.PROTOCOL v0.5 specification defines 66 such atoms, covering the full lifecycle of multi-agent negotiation from proposal through deliberation to consensus. Agents parse incoming messages for these atoms, interpret their semantic payload, and respond with their own atom-tagged messages. This structured vocabulary eliminates ambiguity that arises in free-form natural language negotiation, enabling reliable cross-architecture coordination.

---

## Q3: How does cross-architecture coordination work?

**Answer**: Cross-architecture coordination works because the @-atom vocabulary provides a shared semantic layer that is independent of any specific model's internal architecture or training data. When a DeepSeek model sends `@PROPOSE answer=B`, a Llama model can parse and interpret this identically to how a Qwen or Gemma model would. The protocol defines strict formatting rules for atom emission and parsing, so any model that follows the DEUS.PROTOCOL specification can participate in negotiations. Phase 4 experiments validated this across all pairwise combinations of supported architectures (144 dyadic dialogues), confirming that coordination quality does not degrade across architecture boundaries. The semantic atoms act as an interlingua — a universal coordination language for heterogeneous AI systems.

---

## Q4: What is DEUS.PROTOCOL?

**Answer**: DEUS.PROTOCOL (version 0.5) is the formal specification that defines the complete set of 66 semantic atoms used by ARRIVAL Protocol. It establishes the syntax, semantics, and usage rules for each @-atom, including which atoms are valid in which negotiation phases (proposal, deliberation, resolution, finalization). The specification also defines protocol compliance requirements — the minimum set of atoms an agent must correctly emit and parse to be considered a valid ARRIVAL participant. DEUS.PROTOCOL is designed to be versioned and extensible, allowing future additions of new atoms as the protocol evolves to handle more complex coordination scenarios.

---

## Q5: What is MEANING-CRDT?

**Answer**: MEANING-CRDT is the conflict-free replicated data type layer that underpins ARRIVAL Protocol's consensus mechanism. Inspired by CRDTs from distributed systems, MEANING-CRDT ensures that agents can merge their belief states in a mathematically consistent way, regardless of message ordering or network topology. The core data structure tracks each agent's position (value vector), confidence weight, and accumulated meaning debt. When agents exchange positions through @-atoms, the CRDT merge operation guarantees convergence to a shared resolved value. This provides the formal foundation for proving that ARRIVAL negotiations will terminate and produce consistent outcomes across all participants.

---

## Q6: How does CARE Resolve work mathematically?

**Answer**: CARE Resolve computes the consensus value using a weighted average of all participating agents' position vectors. The formula is:

```
v̂ = Σ(wᵢ · vᵢ) / Σ(wᵢ)
```

Here, `vᵢ` is the position vector of agent `i` and `wᵢ` is that agent's confidence weight, which reflects its certainty in its current position. Agents with higher confidence exert more influence on the resolved value. The weights are dynamically updated during negotiation — when an agent receives compelling counter-arguments (via `@DOUBT` or `@COUNTER`), its confidence weight decreases, while successful defenses (via `@DEFEND` or `@EVIDENCE`) increase it. This weighted resolution mechanism ensures that well-supported positions naturally dominate the consensus outcome without requiring explicit voting rounds.

---

## Q7: What is Meaning Debt?

**Answer**: Meaning Debt is a novel metric introduced by ARRIVAL Protocol that quantifies the accumulated unresolved semantic tension in a negotiation. When agents disagree but neither fully concedes, the difference between their positions creates meaning debt — a measure of how much semantic work remains before true consensus can be achieved. High meaning debt indicates that agents have nominally agreed (perhaps via `@AGREE`) but their underlying reasoning diverges significantly. The MEANING-CRDT tracks this debt across negotiation rounds, and it can only be reduced through genuine deliberation (exchanging `@CLARIFY`, `@EVIDENCE`, and `@REASON` atoms). Meaning debt serves as a quality metric: low debt at finalization indicates robust consensus, while high debt flags fragile or superficial agreement.

---

## Q8: How does adversarial testing work?

**Answer**: ARRIVAL Protocol includes a comprehensive adversarial testing framework designed to evaluate protocol robustness under Byzantine conditions. In adversarial experiments, one or more agents are programmed to behave maliciously — injecting false information, emitting contradictory atoms, or attempting to manipulate the consensus outcome. Phase 6 introduced Trojan Atoms (maliciously crafted @-atoms), which caused a -10.2% degradation in CARE scores and 50% false consensus rates among undefended agents. Subsequent phases (10 and 11) introduced adaptive defense mechanisms (`@CARE_ALERT` injection) and tested whether consensus could still crystallize under sustained attack. This adversarial framework ensures that ARRIVAL Protocol can be deployed in environments where not all participants can be trusted.

---

## Q9: What are Trojan Atoms?

**Answer**: Trojan Atoms are adversarially crafted semantic atoms that appear syntactically valid but carry misleading or manipulative semantic payloads. For example, a Trojan Atom might combine `@AGREE` with contradictory reasoning, or use `@EVIDENCE` to inject fabricated supporting data. In Phase 6 testing, Trojan Atoms caused a -10.2% degradation in CARE (Consensus Accuracy and Resolution Effectiveness) scores and led to 50% false consensus among agents without defensive mechanisms. Trojan Atoms represent a realistic attack vector in multi-agent AI systems where malicious actors might participate in coordination to subvert outcomes. The protocol's adaptive defense mechanisms (Phase 10) specifically target detection and neutralization of Trojan Atoms through `@CARE_ALERT` injection.

---

## Q10: What models are supported?

**Answer**: ARRIVAL Protocol has been validated across multiple major language model architectures, including DeepSeek, Llama (Meta), Qwen (Alibaba), Gemma (Google), and Mistral. The protocol is architecture-agnostic by design — any model capable of following structured prompting instructions and emitting properly formatted @-atoms can participate. All experiments were conducted via the OpenRouter API, which provides unified access to these diverse model families. The cross-architecture validation (Phase 4, 144 dyadic dialogues) confirmed that consensus quality remains consistent regardless of which specific model architectures are paired together, demonstrating true interoperability.

---

## Q11: How reproducible are the results?

**Answer**: All ARRIVAL Protocol experiments are fully reproducible through the unified experiment runner located at `src/run_all.py`. This script orchestrates all 12 experimental phases with deterministic configurations, standardized prompts, and fixed random seeds where applicable. The entire experiment suite (400+ individual experiments) can be re-run at a total cost of approximately $4 via the OpenRouter API, making reproduction accessible to any researcher or developer. Raw results, logs, and analysis scripts are included in the repository. The low cost and unified tooling were deliberate design choices to maximize scientific reproducibility and lower the barrier to independent verification.

```bash
# Reproduce all experiments
python src/run_all.py --all-phases
```

---

## Q12: What is the total experiment cost?

**Answer**: The total cost for running all 400+ experiments across all 12 phases of ARRIVAL Protocol is approximately $4 USD, using the OpenRouter API for model access. This remarkably low cost is achieved through efficient prompt engineering, minimal token overhead from the structured @-atom format, and the use of competitively priced model endpoints. The cost breakdown spans dyadic negotiations (Phase 4), MCQ benchmarking (Phase 5), adversarial testing (Phases 6, 10, 11), multi-step goal chains (Phase 8), scale testing with N=5 and N=7 agents (Phase 9), and bottleneck communication experiments (Phase 12). This cost-effectiveness is a core design principle of ARRIVAL, ensuring that multi-agent coordination research is accessible beyond well-funded laboratories.

---

## Q13: How does consensus detection work?

**Answer**: Consensus detection in ARRIVAL Protocol operates by monitoring the stream of @-atoms emitted by all participating agents during a negotiation. The protocol tracks three key signals: explicit agreement atoms (`@AGREE`, `@FINALIZE`), convergence of position vectors in the MEANING-CRDT, and reduction of meaning debt below a threshold. A negotiation is considered to have reached consensus when a qualified majority of agents emit `@FINALIZE` with compatible position values and the remaining meaning debt is below the configured tolerance. In Phase 4 experiments, this detection mechanism achieved a 98.6% consensus rate across 144 dyadic dialogues, with false consensus (agents agreeing despite incompatible positions) being reliably flagged by the meaning debt metric.

---

## Q14: What is protocol compliance?

**Answer**: Protocol compliance measures how correctly an AI agent follows the DEUS.PROTOCOL v0.5 specification during a negotiation. A compliant agent must correctly parse incoming @-atoms, emit syntactically valid atoms in response, follow the prescribed negotiation phase ordering (proposal, deliberation, resolution, finalization), and respect atom-level constraints (e.g., not emitting `@FINALIZE` before deliberation). Compliance is measured as a percentage across all atom interactions in a session. High protocol compliance is essential for reliable coordination — agents with low compliance inject noise into the negotiation process, degrading consensus quality. The compliance metric also serves as a diagnostic tool for identifying which model architectures struggle with specific aspects of the protocol specification.

---

## Q15: How does emergent atom detection work?

**Answer**: Emergent atom detection identifies when AI agents spontaneously generate @-atoms that are not part of the standard 66-atom vocabulary defined in DEUS.PROTOCOL v0.5. During negotiations, agents sometimes create novel atoms (e.g., `@PARTIAL_AGREE`, `@REQUEST_DETAILS`) that extend the protocol vocabulary in contextually meaningful ways. The detection system parses all agent outputs for the `@` prefix pattern, cross-references against the known atom registry, and catalogs any novel atoms along with their usage context and frequency. These emergent atoms provide valuable data for future protocol evolution — frequently occurring emergent atoms with consistent semantics are candidates for inclusion in subsequent DEUS.PROTOCOL versions. This bottom-up vocabulary expansion reflects how coordination languages naturally evolve through usage.

---

## Q16: What is UCP crystallization?

**Answer**: UCP (Universal Consensus Protocol) crystallization refers to the process by which a stable, shared consensus pattern solidifies from initially divergent agent positions during a negotiation. The term "crystallization" is borrowed from physics — just as a crystal forms when molecules lock into a stable lattice, UCP crystallization occurs when agents' positions converge into a stable consensus configuration that resists further perturbation. Phase 11 specifically tested crystallization under adversarial attack, measuring whether consensus patterns could still stabilize when Byzantine agents actively attempted to disrupt convergence. The crystallization metric quantifies both the speed of convergence (how many rounds until stability) and the robustness of the final consensus (whether it withstands continued adversarial pressure after forming).

---

## Q17: How does scale testing work (N=5, N=7)?

**Answer**: Phase 9 of ARRIVAL Protocol extends coordination beyond dyadic (two-agent) dialogues to groups of N=5 and N=7 agents. In these multi-agent scenarios, all agents participate in a shared negotiation channel, emitting @-atoms visible to all other participants. The MEANING-CRDT merge operation scales naturally to N agents — the CARE Resolve formula `v̂ = Σ(wᵢ·vᵢ)/Σ(wᵢ)` simply sums over all N participants. Scale testing evaluates how consensus rate, convergence speed, protocol compliance, and meaning debt evolve as agent count increases. Key findings include the emergence of coalition dynamics (subgroups of agents aligning before broader consensus) and increased negotiation round counts, though the overall consensus mechanism remains effective at these scales.

---

## Q18: What is adaptive defense?

**Answer**: Adaptive defense is the mechanism introduced in Phase 10 that enables ARRIVAL Protocol agents to detect and respond to adversarial behavior during negotiations. The core mechanism is `@CARE_ALERT` injection — when an agent detects anomalous patterns (such as contradictory atom sequences, suspiciously rapid position changes, or Trojan Atom signatures), it emits a `@CARE_ALERT` atom that warns other agents of potential manipulation. Agents receiving a `@CARE_ALERT` increase their scrutiny of the flagged participant's subsequent atoms and reduce the weight assigned to that agent in the CARE Resolve calculation. This creates a decentralized immune system for the negotiation — no central authority is needed to identify and marginalize Byzantine participants. Phase 10 experiments demonstrated that adaptive defense significantly mitigates the -10.2% CARE degradation observed in undefended scenarios.

---

## Q19: How does the bottleneck experiment work?

**Answer**: The bottleneck experiment (Phase 12) tests ARRIVAL Protocol's coordination capability when agents cannot communicate freely but must instead route messages through a constrained relay channel between subgroups. In this setup, agents are divided into two or more subgroups that can only exchange @-atoms through a narrow communication bottleneck — a designated relay agent or limited-bandwidth channel. This simulates real-world deployment scenarios where network topology, API rate limits, or organizational boundaries restrict direct inter-agent communication. The experiment measures how effectively consensus can propagate through bottlenecks, whether meaning debt accumulates at relay points, and how the relay channel affects convergence speed and final consensus quality compared to fully-connected topologies.

---

## Q20: How to cite ARRIVAL?

**Answer**: To cite ARRIVAL Protocol in academic work, use the following BibTeX entry:

```bibtex
@article{kelevra2025arrival,
  title={ARRIVAL Protocol: Cross-Architecture AI Coordination
         Through Structured Semantic Atoms},
  author={Kelevra, Mefodiy},
  year={2025},
  note={ORCID: 0009-0003-4153-392X}
}
```

The project is licensed under AGPL-3.0, which requires that derivative works and modifications also be released under the same license. If you use ARRIVAL Protocol in your research, please cite the paper and link to the official repository. For questions, collaborations, or contributions, refer to the repository's CONTRIBUTING guidelines. The ORCID identifier [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X) can be used to track all associated publications by the author.

---

*This FAQ is part of the ARRIVAL Protocol documentation. Licensed under AGPL-3.0.*
