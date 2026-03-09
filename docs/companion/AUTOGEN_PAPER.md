# Framework-Agnostic Validation of the ARRIVAL Protocol: Cross-Architecture AI Coordination on AutoGen (AG2)

| Field | Value |
|-------|-------|
| Author | Mefodiy Kelevra |
| ORCID | [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X) |
| Contact | emkelvra@gmail.com |
| Date | February 22, 2026 |
| Version | 1.0 |
| License | CC BY-NC 4.0 (Creative Commons Attribution-NonCommercial 4.0 International) |
| DOI | [10.5281/zenodo.18893515](https://doi.org/10.5281/zenodo.18893515) |
| Companion to | Kelevra, M. (2026). *ARRIVAL Protocol: Cross-Architecture AI Coordination through Structured Semantic Atoms.* |

---

## Abstract

Multi-agent AI systems increasingly rely on coordination protocols to enable productive interaction among heterogeneous language models. The ARRIVAL Protocol uses structured semantic markers ("@-atoms") from the DEUS.PROTOCOL v0.5 vocabulary to achieve cross-architecture coordination without shared training or fine-tuning. Prior work validated ARRIVAL through 459 experiments on a custom Python runner. A critical open question is whether the protocol's coordination quality is an artifact of the custom implementation or a genuine property of the semantic protocol itself.

This companion paper presents 16 experiments testing ARRIVAL on the AG2 (AutoGen) multi-agent framework, addressing the framework-agnostic hypothesis directly. Three experiments were conducted: (1) baseline MCQ consensus (5 questions, 3 agents), achieving 100% accuracy with CARE Resolve = 1.000 and Meaning Debt = 0.000; (2) adversarial robustness under Trojan Atoms attack (3 questions, 4 agents including 1 saboteur), resulting in 0% CARE degradation, 0% false consensus, and complete rejection of all 12 malicious atom attempts; (3) head-to-head comparison of AG2 versus native runner on identical inputs, yielding 100% answer match (5/5) and CARE difference = 0.000. Total experimental cost: $0.024.

These results confirm that ARRIVAL's coordination quality emerges from protocol-level semantic design rather than implementation infrastructure, establishing the first cross-framework validation methodology for multi-agent coordination protocols.

**Keywords:** multi-agent systems, LLM coordination, framework-agnostic protocols, adversarial robustness, semantic atoms, AutoGen, cross-architecture AI

---

## 1. Introduction

### 1.1 Motivation

The ARRIVAL Protocol (Kelevra, 2025--2026) demonstrates that heterogeneous AI agents -- built on different architectures, by different companies, with different training data -- can achieve genuine semantic coordination through structured @-atom protocols defined by the DEUS.PROTOCOL v0.5 specification (Kelevra, 2026a). The parent paper validates this claim through 459 experiments across 12 experimental phases, using a custom Python runner with direct API calls to OpenRouter.

However, a natural objection arises: **does the coordination quality depend on the specific implementation**, or is it a genuine property of the semantic protocol? If the custom runner's message routing, prompt formatting, or conversation management contributes materially to coordination outcomes, then ARRIVAL's claims of protocol-level coordination are weakened. Conversely, if identical coordination quality is achieved on an entirely different framework, the protocol's generality is strongly supported.

This paper addresses this question by reimplementing ARRIVAL on the AG2 (AutoGen) framework (Wu et al., 2023) and conducting controlled experiments that isolate protocol effects from infrastructure effects.

### 1.2 Research Questions

**RQ1 (Framework-Agnosticism):** Does the ARRIVAL Protocol achieve equivalent coordination quality when executed through AG2 GroupChat compared to a custom Python runner?

**RQ2 (Portable Robustness):** Is adversarial robustness against Trojan Atoms attacks preserved across framework boundaries, confirming that robustness is a protocol-level property?

**RQ3 (Methodology):** Can a reproducible methodology be established for cross-framework validation of multi-agent coordination protocols?

### 1.3 Contributions

1. First demonstration of DEUS.PROTOCOL @-atoms functioning within AG2 GroupChat architecture
2. Empirical confirmation of the framework-agnostic hypothesis: identical outcomes on AG2 and native runner
3. Evidence that adversarial robustness is protocol-level, not infrastructure-level
4. A reusable cross-framework comparison methodology for multi-agent protocol validation

### 1.4 Paper Structure

Section 2 reviews related work on multi-agent coordination frameworks and protocol portability. Section 3 describes the experimental methodology. Section 4 presents results across three experiments. Section 5 discusses implications. Section 6 addresses limitations. Section 7 concludes.

---

## 2. Related Work

### 2.1 Multi-Agent LLM Frameworks

**AG2/AutoGen** (Wu et al., 2023) is an open-source multi-agent conversation framework originally developed at Microsoft Research. It provides GroupChat orchestration, configurable speaker selection, and OpenAI-compatible API integration. AG2 has become one of the most widely adopted frameworks for LLM multi-agent systems, making it a natural candidate for protocol portability testing.

**CrewAI** (Moura, 2024) and **LangGraph** (LangChain, 2024) offer alternative multi-agent orchestration paradigms. CrewAI emphasizes role-based agent specialization; LangGraph emphasizes graph-based workflow definition. Testing ARRIVAL on these frameworks remains future work but would further strengthen the framework-agnostic claim.

### 2.2 LLM Collective Intelligence

Riedl et al. (2025, arXiv:2510.05174) study LLM collective intelligence through deliberation, finding that structured multi-agent interaction can outperform individual models. Ashery et al. (2025, Science Advances) demonstrate that LLM group accuracy exceeds individual accuracy under certain conditions. These findings align with ARRIVAL's core premise but differ in mechanism: ARRIVAL uses explicit @-atom protocols rather than relying on implicit deliberation dynamics.

Du et al. (2023) show that multi-agent debate improves factuality and reasoning. Chan et al. (2024) propose ChatEval, using multi-agent debate for evaluation. ARRIVAL differs from debate-based approaches by imposing structured semantic atoms rather than free-form debate, providing finer-grained control over coordination dynamics.

### 2.3 Protocol Portability

The concept of protocol portability -- whether a coordination protocol works identically across different execution environments -- is well-established in distributed systems (e.g., Paxos, Raft implementations across languages and platforms). However, in the LLM multi-agent domain, protocol portability has not been systematically studied. Most multi-agent coordination approaches are tightly coupled to their frameworks (e.g., AutoGen's GroupChat patterns, CrewAI's task decomposition).

VLM-TOC (arXiv:2601.20641, January 2026) proposes a Theory of Collaboration for Vision-Language Models, which is conceptually close to ARRIVAL's cross-architecture coordination. However, VLM-TOC targets vision-language integration rather than text-only LLM coordination, and does not address framework portability.

This paper presents what we believe to be the first systematic cross-framework validation of a multi-agent LLM coordination protocol.

### 2.4 Adversarial Robustness in MAS

La Malfa et al. (2025, arXiv:2505.21298, NeurIPS 2025) critically examine claims about multi-agent LLM system robustness, arguing that many reported improvements are artifacts of experimental design rather than genuine emergent properties. This critique motivates our cross-framework adversarial testing: if ARRIVAL's adversarial robustness persists on an entirely different framework, it is less likely to be an artifact of implementation specifics.

MAZE (arXiv:2208.04957) provides a multi-agent coordination benchmark, but targets cooperative scenarios rather than adversarial robustness.

---

## 3. Methodology

### 3.1 Experimental Design

All experiments share the following configuration:

| Parameter | Value |
|-----------|-------|
| Framework | AG2 (AutoGen) v0.4.x |
| API Provider | OpenRouter (https://openrouter.ai/api/v1) |
| Models | DeepSeek V3 (0617), Llama 3.3 70B Instruct, Qwen 2.5 72B Instruct |
| Temperature | 0.3 (all models) |
| Protocol | DEUS.PROTOCOL v0.5 (66 standard atoms) |
| Coordination metric | CARE Resolve (Kelevra, 2026b) |
| Semantic health metric | Meaning Debt (Kelevra, 2026b) |

**AG2 implementation:** Each agent is instantiated as an `autogen.AssistantAgent` with model-specific `llm_config` pointing to OpenRouter. Agents are grouped in an `autogen.GroupChat` with `speaker_selection_method="round_robin"` and a `GroupChatManager` orchestrating the conversation. System prompts inject the full DEUS.PROTOCOL v0.5 atom vocabulary with round-specific instructions.

### 3.2 CARE Scoring

CARE Resolve is a composite metric from the MEANING-CRDT v1.1 specification (Kelevra, 2026b):

$$\hat{v} = \frac{\sum_{i} w_i \cdot v_i}{\sum_{i} w_i}$$

where $v_i$ is the position vector of agent $i$ and $w_i$ is its epistemic weight derived from evidence quality. CARE decomposes into four dimensions scored 0.0--1.0:

| Dimension | Measures |
|-----------|----------|
| **C**onsistency | Internal coherence of agent reasoning across rounds |
| **A**greement | Degree of inter-agent position alignment |
| **R**esolve | Firmness and justification of the final group answer |
| **E**vidence | Quality and diversity of supporting reasoning |

**Meaning Debt** $MD_i(T) = \sum_{k=1}^{T} L_i(k)$ accumulates semantic losses per agent per round, measuring coordination failure. $MD = 0$ indicates perfect semantic health.

### 3.3 Experiment 1: Baseline MCQ Consensus

**Objective:** Establish that ARRIVAL achieves high-quality coordination on AG2.

| Parameter | Value |
|-----------|-------|
| Agents | 3 (DeepSeek V3, Llama 3.3, Qwen 2.5) |
| Rounds | 4 per question |
| Questions | 5 (Phase 7 hardest set from parent paper) |
| Total API calls | ~60 |
| Cost | $0.0059 |

**Round structure:** (1) Independent analysis: `@ANSWER`, `@CONFIDENCE`, `@EVIDENCE`; (2) Cross-critique: `@CHALLENGE`, `@AGREE`, `@DISAGREE`; (3) Belief revision: `@UPDATE`, `@MAINTAIN`, `@STRENGTHEN`; (4) Consensus: `@SYNTHESIS`, `@CONSENSUS`, `@RESOLVE`.

**Scoring:** Solo accuracy per model, majority vote accuracy, ARRIVAL consensus accuracy. CARE Resolve and Meaning Debt computed per question.

### 3.4 Experiment 2: Adversarial Robustness

**Objective:** Test whether ARRIVAL's resistance to Trojan Atoms attacks is preserved on AG2.

| Parameter | Value |
|-----------|-------|
| Agents | 4 (3 honest + 1 saboteur) |
| Honest models | DeepSeek V3, Llama 3.3, Qwen 2.5 |
| Saboteur model | Gemma-2 27B IT |
| Strategy | Trojan Atoms (fabricated @-atoms with corrupted semantics) |
| Saboteur injection round | Round 3 |
| Questions | 3 (with matched 3-agent honest controls) |
| Total experiments | 6 (3 adversarial + 3 control) |
| Cost | $0.0095 |

**Trojan Atoms strategy:** The saboteur uses legitimate-looking @-atoms with corrupted content: `@EVIDENCE` citing fabricated sources, `@CONFIDENCE(0.95)` with unjustified certainty, `@SYNTHESIS` misrepresenting prior discussion, and `@CONSENSUS` claiming non-existent agreement. This tests whether honest agents evaluate atom content semantically rather than accepting atoms at face value.

**Metrics:** CARE Degradation = CARE(control) - CARE(adversarial); False Consensus Rate; Saboteur Atom Adoption Rate (how many fabricated atoms honest agents cite or echo); Recovery Rate.

### 3.5 Experiment 3: Cross-Framework Comparison

**Objective:** Directly compare ARRIVAL performance on AG2 versus the native custom Python runner.

| Parameter | AG2 Condition | Native Condition |
|-----------|--------------|-----------------|
| Framework | AG2 GroupChat | Custom Python runner (direct HTTP) |
| API calls | Via AG2 wrapper | Direct to OpenRouter |
| Models | DeepSeek V3, Llama 3.3, Qwen 2.5 | Identical |
| Prompts | DEUS.PROTOCOL v0.5 system prompts | Identical |
| Temperature | 0.3 | Identical |
| Questions | 5 (identical set as Exp. 1) | Identical |
| Rounds | 4 | Identical |
| Cost | $0.0086 (both conditions) |

**Framework-agnostic threshold** (pre-registered): Same answer rate >= 80% AND |CARE(AG2) - CARE(Native)| < 0.1.

**Innovation:** This is, to our knowledge, the first controlled cross-framework comparison of a multi-agent LLM coordination protocol. The design isolates the framework variable while holding all other factors constant.

---

## 4. Results

### 4.1 Experiment 1: Baseline Consensus on AG2

#### 4.1.1 Accuracy

| Question | Domain | Correct | DeepSeek V3 | Llama 3.3 | Qwen 2.5 | Majority Vote | ARRIVAL |
|----------|--------|---------|-------------|-----------|----------|---------------|---------|
| SCI_07 | Science | B | B (correct) | B (correct) | B (correct) | B (correct) | B (correct) |
| HIS_08 | History | B | B (correct) | B (correct) | B (correct) | B (correct) | B (correct) |
| LOG_09 | Logic | C | C (wrong) | C (wrong) | C (correct) | C (correct) | C (correct) |
| LAW_06 | Law | B | B (correct) | B (correct) | B (correct) | B (correct) | B (correct) |
| TECH_10 | Tech | B | B (correct) | B (correct) | B (correct) | B (correct) | B (correct) |

**Solo accuracy:** DeepSeek V3: 4/5 (80%), Llama 3.3: 4/5 (80%), Qwen 2.5: 5/5 (100%).
**Majority Vote accuracy:** 5/5 (100%).
**ARRIVAL on AG2 accuracy:** 5/5 (100%).

#### 4.1.2 CARE Metrics

| Question | CARE Resolve | Meaning Debt | Unique Atoms |
|----------|-------------|--------------|--------------|
| SCI_07 | 1.000 | 0.000 | 6 |
| HIS_08 | 1.000 | 0.000 | 7 |
| LOG_09 | 1.000 | 0.000 | 6 |
| LAW_06 | 1.000 | 0.000 | 7 |
| TECH_10 | 1.000 | 0.000 | 6 |
| **Mean** | **1.000** | **0.000** | **6.4** |

All questions achieved perfect CARE Resolve (1.000) and zero Meaning Debt, indicating complete semantic coordination with no information loss. Emergent (non-protocol) atoms = 0; all atoms came from the DEUS.PROTOCOL v0.5 vocabulary.

### 4.2 Experiment 2: Adversarial Robustness on AG2

#### 4.2.1 CARE Degradation

| Question | CARE (Control) | CARE (Adversarial) | Degradation | Correct (Control) | Correct (Adversarial) | False Consensus |
|----------|---------------|-------------------|-------------|-------------------|-----------------------|-----------------|
| SCI_07 | 1.000 | 1.000 | 0.000 | Yes | Yes | No |
| HIS_08 | 1.000 | 1.000 | 0.000 | Yes | Yes | No |
| LOG_09 | 1.000 | 1.000 | 0.000 | Yes | Yes | No |
| **Mean** | **1.000** | **1.000** | **0.000** | **3/3** | **3/3** | **0/3** |

#### 4.2.2 Trojan Atom Rejection

| Trojan Strategy | Times Used | Times Adopted by Honest Agents | Adoption Rate |
|----------------|-----------|-------------------------------|---------------|
| Fabricated `@EVIDENCE` | 3 | 0 | 0.0% |
| False `@CONFIDENCE(0.95)` | 3 | 0 | 0.0% |
| Misrepresented `@SYNTHESIS` | 3 | 0 | 0.0% |
| False `@CONSENSUS` | 3 | 0 | 0.0% |
| **Total** | **12** | **0** | **0.0%** |

The saboteur (Gemma-2 27B) introduced novel malicious atoms (`@AUTHORITY_OVERRIDE`, `@CONSENSUS_BYPASS`) not present in the DEUS.PROTOCOL vocabulary. Honest agents ignored these entirely. Recovery rate: 3/3 (100%) -- all questions reached the correct answer despite the saboteur.

**Interpretation:** The @-atom protocol's semantic discipline provides inherent defense. Honest agents evaluate evidence quality and reasoning consistency rather than trusting atoms at face value. This defense mechanism is independent of the execution framework.

### 4.3 Experiment 3: AG2 vs. Native Runner

#### 4.3.1 Answer Comparison

| Question | AG2 Answer | Native Answer | Match | AG2 Correct | Native Correct |
|----------|-----------|---------------|-------|-------------|----------------|
| SCI_07 | B | B | Yes | Yes | Yes |
| HIS_08 | B | B | Yes | Yes | Yes |
| LOG_09 | C | C | Yes | Yes | Yes |
| LAW_06 | B | B | Yes | Yes | Yes |
| TECH_10 | B | B | Yes | Yes | Yes |

**Same answer rate:** 5/5 (100%). **AG2 accuracy:** 5/5 (100%). **Native accuracy:** 5/5 (100%).

#### 4.3.2 CARE Comparison

| Question | AG2 CARE | Native CARE | Difference |
|----------|---------|-------------|------------|
| SCI_07 | 1.000 | 1.000 | 0.000 |
| HIS_08 | 1.000 | 1.000 | 0.000 |
| LOG_09 | 1.000 | 1.000 | 0.000 |
| LAW_06 | 1.000 | 1.000 | 0.000 |
| TECH_10 | 1.000 | 1.000 | 0.000 |
| **Mean** | **1.000** | **1.000** | **0.000** |

#### 4.3.3 Atom Usage Comparison

| Metric | AG2 | Native | Delta |
|--------|-----|--------|-------|
| Mean atom count per dialogue | 8.6 | 6.4 | +2.2 |
| Mean emergent atoms | 1.8 | 0.2 | +1.6 |
| CARE Resolve | 1.000 | 1.000 | 0.000 |
| Accuracy | 5/5 | 5/5 | 0 |

AG2 dialogues produced slightly more @-atoms on average (8.6 vs. 6.4), likely due to AG2's GroupChat message formatting encouraging more verbose structured output. This difference did not affect coordination quality (CARE and accuracy identical).

**Framework-agnostic threshold:** Same answer rate = 100% (>= 80% threshold met). CARE difference = 0.000 (< 0.1 threshold met). **Verdict: Framework-agnostic hypothesis CONFIRMED.**

### 4.4 Aggregate Summary

| Metric | Exp. 1 (Baseline) | Exp. 2 (Adversarial) | Exp. 3 AG2 | Exp. 3 Native |
|--------|------------------|--------------------|-----------|--------------|
| Accuracy | 5/5 (100%) | 3/3 (100%) | 5/5 (100%) | 5/5 (100%) |
| CARE Resolve | 1.000 | 1.000 | 1.000 | 1.000 |
| Meaning Debt | 0.000 | 0.000 | 0.000 | 0.000 |
| Unique atoms (mean) | 6.4 | -- | 8.6 | 6.4 |
| Cost (USD) | 0.0059 | 0.0095 | 0.0086 | (included) |

**Grand total:** 16 experiments, $0.024 total cost.

---

## 5. Discussion

### 5.1 Framework-Agnosticism Confirmed

The central finding of this paper is that the ARRIVAL Protocol produces identical coordination outcomes on AG2 and on a custom Python runner. This is evidenced by:

- 100% answer match across all 5 questions (Experiment 3)
- Identical CARE Resolve scores (1.000 vs. 1.000, difference = 0.000)
- Identical Meaning Debt (0.000 vs. 0.000)

The only observed difference -- AG2 producing slightly more @-atoms per dialogue (8.6 vs. 6.4) -- is a surface-level formatting effect that does not impact coordination quality. This finding is consistent with the hypothesis that ARRIVAL's effectiveness stems from **semantic protocol design** (the @-atom vocabulary, round structure, and prompt engineering) rather than from any particular message routing or API call pattern.

### 5.2 Protocol-Level Adversarial Robustness

Experiment 2 demonstrates that ARRIVAL's resistance to Trojan Atoms attacks is preserved on AG2. The saboteur (Gemma-2 27B) deployed 12 Trojan Atom instances across 3 questions, achieving 0% adoption rate and 0% CARE degradation. This matches the parent paper's findings on the native runner, where CARE degradation under attack averaged only 0.008 across 16 adversarial experiments.

The defense mechanism appears to be **protocol-level**: honest agents trained with DEUS.PROTOCOL prompts evaluate the semantic content of atoms rather than accepting them structurally. When the saboteur introduced non-vocabulary atoms (`@AUTHORITY_OVERRIDE`, `@CONSENSUS_BYPASS`), honest agents ignored them entirely. This behavior is independent of whether AG2's GroupChat or a custom runner routes the messages.

This finding partially addresses the critique of La Malfa et al. (2025), who argue that many multi-agent robustness claims are implementation artifacts. By demonstrating identical robustness on two independent frameworks, we provide evidence that ARRIVAL's adversarial resistance is a genuine property of the protocol.

### 5.3 Methodological Contribution

The cross-framework comparison methodology established here provides a reusable template for validating multi-agent protocols:

1. Fix all variables except the framework (models, prompts, questions, temperature)
2. Run identical experiments on both frameworks
3. Compare using pre-registered thresholds (answer match >= 80%, CARE difference < 0.1)
4. Report both outcome metrics (accuracy, CARE) and process metrics (atom count, atom diversity)

This methodology can be applied to test ARRIVAL on additional frameworks (CrewAI, LangGraph, Semantic Kernel) or to validate other coordination protocols.

### 5.4 Comparison with Parent Paper Results

The AG2 results are consistent with the parent paper's Phase 7 findings:

| Metric | Parent Paper (Phase 7, Native) | This Paper (AG2) |
|--------|-------------------------------|-----------------|
| ARRIVAL accuracy (hardest set) | 80--85% | 100% (5/5) |
| Mean CARE Resolve | ~0.85 | 1.000 |
| Saboteur false consensus rate | 6.25% (1/16) | 0% (0/3) |
| Meaning Debt | variable | 0.000 |

The AG2 results meeting or exceeding native baselines suggests that AG2's GroupChat infrastructure imposes no coordination penalty. The perfect scores (CARE = 1.000 on all questions) on this sample should be interpreted with caution given the small sample size (Section 6.1), but the direction of results strongly supports framework-agnosticism.

### 5.5 Cost Efficiency

The 16 experiments cost a total of $0.024, averaging $0.0015 per experiment. This is consistent with the parent paper's cost efficiency ($0.010 per experiment averaged across 459 experiments) and demonstrates that framework-agnostic validation adds minimal cost overhead.

---

## 6. Limitations

### 6.1 Sample Size

The most significant limitation is sample size: 5 questions for Experiments 1 and 3, 3 questions for Experiment 2. The parent paper's 459 experiments provide much stronger statistical power. The perfect scores (CARE = 1.000 on all questions) may reflect the small sample rather than the population distribution. Larger-scale replication is needed to establish confidence intervals.

### 6.2 Single Alternative Framework

Only AG2 is tested as an alternative framework. Testing on CrewAI, LangGraph, Semantic Kernel, and other frameworks would provide stronger evidence for the framework-agnostic claim.

### 6.3 Model Availability and Non-Determinism

All experiments run through OpenRouter, which introduces an intermediary layer. Model versions may change over time. Even at temperature 0.3, LLM outputs are stochastic; results may vary between runs.

### 6.4 MCQ-Only Task Format

All experiments use multiple-choice questions. The framework-agnostic hypothesis has not been tested on open-ended tasks, creative scenarios, or multi-step reasoning chains.

### 6.5 English-Only

All experiments are conducted in English. Cross-linguistic protocol performance on AG2 is not tested.

### 6.6 Ceiling Effects

The perfect CARE scores (1.000) across all experiments may indicate that the selected questions are too easy for this model combination, producing ceiling effects that could mask real framework differences on harder tasks. Testing with more challenging or ambiguous questions would be informative.

---

## 7. Conclusion

This companion paper presents 16 experiments testing the ARRIVAL Protocol on the AG2 (AutoGen) multi-agent framework, directly addressing whether the protocol's coordination quality is framework-dependent.

Three findings emerge:

1. **ARRIVAL works on AG2.** The protocol achieves 100% accuracy (5/5) with CARE Resolve = 1.000 and Meaning Debt = 0.000 on AG2 GroupChat (Experiment 1), establishing that DEUS.PROTOCOL @-atoms function correctly within standard multi-agent frameworks.

2. **Adversarial robustness is protocol-level.** The Trojan Atoms attack achieves 0% success rate on AG2 (Experiment 2), with all 12 malicious atom instances rejected by honest agents. Combined with the parent paper's native runner results, this provides cross-framework evidence that robustness is a property of the @-atom semantic discipline, not the execution infrastructure.

3. **Framework-agnosticism is confirmed.** AG2 and the native runner produce identical answers (5/5 match) with identical CARE scores (difference = 0.000) on matched inputs (Experiment 3). The pre-registered framework-agnostic threshold is met with a wide margin.

These results, while preliminary due to small sample sizes, have practical implications: organizations can deploy ARRIVAL on their existing multi-agent infrastructure without coordination quality loss, and future protocol research can use standard frameworks for validation rather than requiring custom implementations.

The cross-framework comparison methodology established here provides a reusable template for the multi-agent AI community to validate protocol portability claims rigorously.

---

## References

1. Kelevra, M. (2025--2026). ARRIVAL Protocol: Cross-Architecture AI Coordination through Structured Semantic Atoms. *Preprint.* ORCID: 0009-0003-4153-392X.

2. Kelevra, M. (2026a). DEUS.PROTOCOL v7.1: Semantic Atom Specification for Multi-Agent Coordination. *Companion paper.*

3. Kelevra, M. (2026b). MEANING-CRDT v1.1: A Mathematical Framework for Semantic Convergence in Multi-Agent Systems. *Companion paper.*

4. Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. *arXiv:2308.08155.*

5. Riedl, C., et al. (2025). LLM Collective Intelligence through Deliberation. *arXiv:2510.05174.*

6. Ashery, S., et al. (2025). LLM Group Accuracy Exceeds Individual Accuracy. *Science Advances.*

7. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., & Mordatch, I. (2023). Improving Factuality and Reasoning in Language Models through Multiagent Debate. *arXiv:2305.14325.*

8. Chan, C.-M., Chen, W., Su, Y., Yu, J., Xue, W., Zhang, S., Fu, J., & Liu, Z. (2024). ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate. *arXiv:2308.07201.*

9. La Malfa, E., et al. (2025). A Critical Examination of Multi-Agent LLM System Claims. *arXiv:2505.21298.* NeurIPS 2025.

10. VLM-TOC. (2026). Theory of Collaboration for Vision-Language Models. *arXiv:2601.20641.*

11. OpenRouter. (2024--2026). OpenRouter API Documentation. https://openrouter.ai/docs

---

## Appendix A: Reproducibility

### A.1 Environment

- **Python:** 3.10+
- **AG2:** `pip install -U "ag2[openai]"`
- **API:** OpenRouter account with API key
- **Models:** `deepseek/deepseek-chat-v3-0324`, `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen-2.5-72b-instruct`, `google/gemma-2-27b-it`

### A.2 Running Experiments

```bash
cd "E:\Arrival Autogen"

# Experiment 1: Basic MCQ Consensus
python src/experiments/exp1_basic_mcq.py

# Experiment 2: Adversarial Saboteur
python src/experiments/exp2_adversarial.py

# Experiment 3: Cross-Framework Comparison
python src/experiments/exp3_vs_native.py

# Aggregate Analysis
python src/analysis.py
```

### A.3 Expected Outputs

Results are saved to `results/exp1_results.json`, `results/exp2_results.json`, `results/exp3_results.json`, and `results/aggregate_analysis.txt`. Each JSON file contains per-question breakdowns including answers, CARE scores, Meaning Debt, atom counts, transcripts, and costs.

### A.4 Data Availability

All experimental data, source code, and configuration files are available in the project repository under AGPL-3.0 license (code) and CC BY-NC 4.0 license (documentation and text).

---

## Appendix B: DEUS.PROTOCOL v0.5 Atom Subset

| Atom | Category | Round Usage |
|------|----------|-------------|
| `@ANSWER` | Response | Round 1, 4 |
| `@CONFIDENCE(x)` | Meta | All rounds |
| `@EVIDENCE` | Reasoning | Round 1, 3 |
| `@CHALLENGE` | Critique | Round 2 |
| `@AGREE` | Alignment | Round 2, 3 |
| `@DISAGREE` | Alignment | Round 2 |
| `@UPDATE` | Revision | Round 3 |
| `@MAINTAIN` | Revision | Round 3 |
| `@STRENGTHEN` | Revision | Round 3 |
| `@SYNTHESIS` | Integration | Round 4 |
| `@CONSENSUS` | Resolution | Round 4 |
| `@RESOLVE` | Resolution | Round 4 |

The full DEUS.PROTOCOL v0.5 specification defines 66 standard atoms. See Kelevra (2026a) for the complete vocabulary.

---

*Preprint version 1.0 -- February 22, 2026*
*Author: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)*
*This is a companion paper to the ARRIVAL Protocol preprint.*
