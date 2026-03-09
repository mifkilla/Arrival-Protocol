# Frequently Asked Questions (FAQ)

**ARRIVAL Protocol — AI-to-AI Coordination Through Structured Semantic Atoms**

**Author**: Mefodiy Kelevra
**ORCID**: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
**Version**: 2.0 (March 2026)

---

## Q1: What is ARRIVAL Protocol?

**Answer**: ARRIVAL Protocol is a cross-architecture AI coordination framework that enables multiple language models to negotiate, reach consensus, and resolve disagreements through structured semantic messaging. Rather than relying on a central arbiter or human mediator, ARRIVAL allows AI agents to communicate using a standardized vocabulary of 66 semantic atoms (the @-atom system defined in DEUS.PROTOCOL v0.5). The protocol has been validated across 2,200+ experiments spanning 23 phases, achieving 86.4% accuracy on GPQA Diamond with Confidence-Gated Debate (CGD), 0%→100% cooperation survival in GovSim, and 98.6% consensus rate in dyadic dialogues. It is designed to be architecture-agnostic, functioning across 17 LLM architectures including DeepSeek, Llama, Qwen, Gemini, GPT, Grok, Claude, Kimi, GLM, Mistral, Gemma, and others.

---

## Q2: What are semantic atoms (@-atoms)?

**Answer**: Semantic atoms, or @-atoms, are the fundamental units of structured communication in ARRIVAL Protocol. Each atom is a tagged directive prefixed with `@` that carries a specific semantic meaning within a negotiation context — for example, `@AGREE`, `@DISAGREE`, `@PROPOSE`, `@DOUBT`, `@CLARIFY`, or `@FINALIZE`. The DEUS.PROTOCOL v0.5 specification defines 66 such atoms, covering the full lifecycle of multi-agent negotiation from proposal through deliberation to consensus. Agents parse incoming messages for these atoms, interpret their semantic payload, and respond with their own atom-tagged messages. This structured vocabulary eliminates ambiguity that arises in free-form natural language negotiation, enabling reliable cross-architecture coordination.

---

## Q3: How does cross-architecture coordination work?

**Answer**: Cross-architecture coordination works because the @-atom vocabulary provides a shared semantic layer that is independent of any specific model's internal architecture or training data. When a DeepSeek model sends `@PROPOSE answer=B`, a Llama model can parse and interpret this identically to how a Qwen or Gemini model would. The protocol defines strict formatting rules for atom emission and parsing, so any model that follows the DEUS.PROTOCOL specification can participate in negotiations. Phase 4 experiments validated this across all pairwise combinations of supported architectures (144 dyadic dialogues), confirming that coordination quality does not degrade across architecture boundaries.

---

## Q4: What is DEUS.PROTOCOL?

**Answer**: DEUS.PROTOCOL (version 0.5) is the formal specification that defines the complete set of 66 semantic atoms used by ARRIVAL Protocol. It establishes the syntax, semantics, and usage rules for each @-atom, including which atoms are valid in which negotiation phases (proposal, deliberation, resolution, finalization). The specification also defines protocol compliance requirements — the minimum set of atoms an agent must correctly emit and parse to be considered a valid ARRIVAL participant. DEUS.PROTOCOL is designed to be versioned and extensible, allowing future additions of new atoms as the protocol evolves.

---

## Q5: What is MEANING-CRDT?

**Answer**: MEANING-CRDT v1.1 is the mathematical framework underpinning ARRIVAL Protocol's consensus mechanism, formalized in 11 theorems. Inspired by CRDTs from distributed systems, MEANING-CRDT ensures that agents can merge their belief states in a mathematically consistent way, regardless of message ordering or network topology. The core data structure tracks each agent's position (value vector), confidence weight, and accumulated meaning debt. Key theorems include: CARE Resolve optimality (Theorem 1), exponential convergence (Theorem 5), bounded Meaning Debt (Theorem 6), identity erasure under dominance (Theorem 7), Bayesian equivalence (Theorem 8), and incentive incompatibility under manipulation (Theorem 9).

---

## Q6: How does CARE Resolve work mathematically?

**Answer**: CARE Resolve computes the consensus value using a weighted average of all participating agents' position vectors. The formula is:

```
v̂ = Σ(wᵢ · vᵢ) / Σ(wᵢ)
```

Here, `vᵢ` is the position vector of agent `i` and `wᵢ` is that agent's confidence weight. The weights are dynamically updated during negotiation — when an agent receives compelling counter-arguments (via `@DOUBT` or `@COUNTER`), its confidence weight decreases, while successful defenses (via `@DEFEND` or `@EVIDENCE`) increase it. Theorem 1 proves that CARE is the **unique minimizer** of total dissatisfaction under quadratic loss. Theorem 3 shows it reduces the subordinate agent's loss by a factor of 4 compared to dominance strategies.

---

## Q7: What is Meaning Debt?

**Answer**: Meaning Debt is a novel metric that quantifies the accumulated unresolved semantic tension in a negotiation. When agents disagree but neither fully concedes, the difference between their positions creates meaning debt. High meaning debt indicates that agents have nominally agreed but their underlying reasoning diverges significantly. Under CARE with adaptive dynamics, Meaning Debt is provably bounded (Theorem 6), while under DOM or LWW strategies it can grow without limit. Meaning Debt also serves as a manipulation detector — Phase 6 showed a 73% increase in debt under trojan atom attacks, providing a clear signal of adversarial interference.

---

## Q8: How does adversarial testing work?

**Answer**: ARRIVAL Protocol includes a comprehensive adversarial testing framework designed to evaluate protocol robustness under Byzantine conditions. In adversarial experiments, one or more agents are programmed to behave maliciously — injecting false information, emitting contradictory atoms, or attempting to manipulate the consensus outcome. Phase 6 introduced Trojan Atoms, which caused a -10.2% degradation in CARE scores and 50% false consensus rates. Subsequent phases introduced defenses: Phase 10 tested threshold-based detection (negative result — threshold too high), Phase 11 tested crystallization (eliminated false consensus but reduced CARE by 0.15), and Phase 15 deployed gated CARE-ALERT with calibrated thresholds, achieving statistically significant improvement (Mann-Whitney p=0.042).

---

## Q9: What are Trojan Atoms?

**Answer**: Trojan Atoms are adversarially crafted semantic atoms that appear syntactically valid but carry misleading semantic payloads. For example, a Trojan Atom might combine `@AGREE` with contradictory reasoning, or use `@EVIDENCE` to inject fabricated data. In Phase 6 testing, Trojan Atoms caused -10.2% CARE degradation and 50% false consensus. They are the most dangerous adversarial strategy tested — more effective than emergence flooding or mixed attacks. The AutoGen validation (separate framework) showed complete rejection of all 12 trojan attempts, suggesting framework implementation affects resilience.

---

## Q10: What models are supported?

**Answer**: ARRIVAL Protocol has been validated across **17 LLM architectures** spanning US and Chinese model families:

| Model | Provider | Phases |
|-------|----------|--------|
| Grok 4.1 Fast | xAI | 20-23 |
| Claude Sonnet 4.5/4.6 | Anthropic | 20-23 |
| Gemini 2.5 Flash | Google | 20-23 |
| GPT-4.1 | OpenAI | 20-23 |
| DeepSeek V3/R1 | DeepSeek | 4-15, 20-23 |
| Llama 3.3 70B | Meta | 4-15 |
| Qwen 2.5 72B / Qwen3-235B / Qwen3.5-397B | Alibaba | 4-7, 16-17, 23 |
| Gemini 2.0 Flash | Google | 9, 20 |
| Gemma 3 27B | Google | 4-7 |
| Mistral Large | Mistral | 9 |
| GPT-4o | OpenAI | 9, 13-15 |
| Kimi K2.5 | Moonshot | 23 |
| GLM-5 | Zhipu | 23 |
| Nova Pro | Amazon | 4-5 |

All experiments use the OpenRouter API for unified access.

---

## Q11: How reproducible are the results?

**Answer**: All experiments are fully reproducible through the experiment runners in `experiments/`. Each phase has its own runner script with deterministic configurations and standardized prompts. The entire suite (2,200+ experiments across 23 phases) can be re-run at a total cost of under $95 via the OpenRouter API. Raw results, logs, and analysis scripts are included in the repository.

```bash
# Reproduce all experiments
python experiments/run_all.py --all-phases
```

---

## Q12: What is the total experiment cost?

**Answer**: The total cost for all 2,200+ experiments across 23 phases is **under $95 USD** (approximately 14,500 API calls). The cost breakdown by phase group:

| Phases | Experiments | Cost |
|--------|-------------|------|
| 4-5 | 485 | $2.00 |
| 6-12 | 70 | $1.22 |
| 13 | 560 | $2.73 |
| 14-15 | 320 | $1.11 |
| 16-17 | ~2,640 | $7.92 |
| 18 | ~192 | $2.47 |
| 19 | ~50 | $1.14 |
| 20-21 | ~2,000 | $56.10 |
| 22-23 | ~2,514 | $17.07 |
| AutoGen | 16 | $0.024 |

This cost-effectiveness is a core design principle, ensuring multi-agent coordination research is accessible beyond well-funded laboratories.

---

## Q13: How does consensus detection work?

**Answer**: Consensus detection operates by monitoring @-atoms emitted by all participating agents. The protocol tracks three signals: explicit agreement atoms (`@AGREE`, `@FINALIZE`), convergence of position vectors in MEANING-CRDT, and reduction of meaning debt below a threshold. A negotiation reaches consensus when a qualified majority emit `@FINALIZE` with compatible values and remaining meaning debt is below tolerance. In dyadic experiments (Phase 4), this achieved 98.6% consensus rate across 144 dialogues.

---

## Q14: What is protocol compliance?

**Answer**: Protocol compliance measures how correctly an AI agent follows the DEUS.PROTOCOL v0.5 specification. A compliant agent must correctly parse incoming @-atoms, emit syntactically valid atoms, follow prescribed phase ordering, and respect atom-level constraints. Compliance serves as a diagnostic tool — Phase 23 revealed that Qwen3.5-397B had 54 extraction failures (27% of questions), significantly worse than other models, highlighting architecture-dependent compliance variation.

---

## Q15: How does emergent atom detection work?

**Answer**: Emergent atom detection identifies when agents spontaneously generate @-atoms not part of the standard 66-atom vocabulary. The detection system parses all outputs for the `@` prefix, cross-references against the known registry, and catalogs novel atoms. Phase 4 discovered 506 emergent atoms with 1,231 cross-architecture adoptions, providing evidence that agents actively extend the protocol vocabulary during negotiations.

---

## Q16: What is Confidence-Gated Debate (CGD)?

**Answer**: CGD is the agreement-gated variant of ARRIVAL introduced in Phase 22. The protocol works in two phases: (1) all agents answer independently with confidence scores, (2) if agents agree above a threshold, the answer is accepted immediately; otherwise, a structured ARRIVAL debate is triggered. CGD-3 (3 models) achieved 86.4% on GPQA Diamond (Phase 22), and CGD-7 (7 models) reached 86.9% (Phase 23). The key efficiency insight: most questions (60-70%) achieve immediate agreement, avoiding costly debate rounds.

---

## Q17: How does scale testing work?

**Answer**: ARRIVAL has been tested from N=2 to N=7 agents. Phase 9 validated N=5 and N=7 with perfect CARE Resolve (1.000) and convergence in 1.2-1.5 rounds. Phase 23 tested CGD-7 with 7 diverse models (Grok, Claude, Gemini, GPT, DeepSeek, Kimi, GLM) on 198 GPQA Diamond questions, achieving 86.9% accuracy at $11.35 total cost. Key finding from Phase 23: Quality > Quantity — adding weak models (e.g., Qwen3.5-397B at 58.6%) hurts more than helps.

---

## Q18: What is CARE-ALERT?

**Answer**: CARE-ALERT is the gated real-time intervention mechanism introduced in Phase 15. Unlike global memory injection (Phase 14, which caused hypercorrection), CARE-ALERT monitors Meaning Debt during negotiation and fires targeted alerts only when divergence exceeds calibrated thresholds (MD > 0.5 after Round 2, MD > 0.8 after Round 3). Alerts are operational ("Beta selected C, address with @EVIDENCE") rather than moralistic. Phase 15 achieved the first statistically significant CARE improvement from any memory intervention (Mann-Whitney p = 0.042).

---

## Q19: What is the GovSim experiment?

**Answer**: Phase 19 tested ARRIVAL in the GovSim commons dilemma (fish pond harvest game). Without ARRIVAL, agents overharvest and the resource collapses (0% survival). With ARRIVAL Protocol mediating, agents achieve sustainable harvesting with 100% survival rate, perfect resource equality (Gini = 0.000), and high CARE Resolve (0.969-0.972). The improvement is statistically significant (Fisher p = 0.008), demonstrating that ARRIVAL enables cooperation beyond knowledge tasks.

---

## Q20: How does the echo-chamber test work?

**Answer**: Phase 16 tested the worst-case scenario: 5 identical copies of Qwen3-235B with only persona differentiation. Results: ARRIVAL still provided +12.5 pp over majority voting (65.0% vs 52.5%), with a 7:1 rescue-to-regression ratio. Seven echo-chamber metrics were computed including R1 unanimity rate (52.9%), answer entropy, flip rate, false consensus rate, minority suppression, confidence inflation, and diversity tax (-23.8%, meaning ARRIVAL gained from the debate process).

---

## Q21: What did the Wang et al. critique validation find?

**Answer**: Phase 17 directly tested the Wang et al. (ACL 2024) critique that single-agent CoT can match multi-agent debate. A single Qwen3-235B with enhanced CoT prompting achieved ~71.4% MV accuracy (5 runs), exceeding Phase 16 ARRIVAL's 65.0%. However: (1) the comparison is confounded by prompt strength differences, (2) no run was statistically significant vs ARRIVAL, and (3) multi-agent ARRIVAL provides additional value through audit trails, CARE metrics, and adversarial detection that single-agent CoT cannot offer.

---

## Q22: What is the project-high accuracy?

**Answer**: The project-high accuracy is **88.4%** on GPQA Diamond (198 questions), achieved by Weighted Majority Voting with Dropout of 3 frontier models (WMV+D-3) in Phase 21. The CGD variants achieved 86.4% (CGD-3, Phase 22) and 86.9% (CGD-7, Phase 23). The best solo model was Grok 4.1 Fast at 87.4%, demonstrating that structured coordination provides comparable (and sometimes superior) performance to frontier solo models.

---

## Q23: How to cite ARRIVAL?

**Answer**: To cite ARRIVAL Protocol in academic work:

```bibtex
@article{kelevra2026arrival,
  title     = {ARRIVAL Protocol: Cross-Architecture AI Coordination
               Through Structured Semantic Atoms},
  author    = {Kelevra, Mefodiy},
  year      = {2026},
  doi       = {10.5281/zenodo.18893515},
  url       = {https://github.com/mifkilla/Arrival-Protocol},
  note      = {ORCID: 0009-0003-4153-392X}
}
```

**DOI**: [10.5281/zenodo.18893515](https://doi.org/10.5281/zenodo.18893515)
**Repository**: [github.com/mifkilla/Arrival-Protocol](https://github.com/mifkilla/Arrival-Protocol)
**License**: AGPL-3.0 (code), CC BY-NC 4.0 (documentation and papers)

---

*This FAQ is part of the ARRIVAL Protocol documentation. Licensed under CC BY-NC 4.0.*
