# ARRIVAL-MNEMO: Persistent Memory Architecture for Cross-Architecture AI Coordination

**A Companion Paper to the ARRIVAL Protocol**

---

**Author**: Mefodiy Kelevra

ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)

**Date**: March 4, 2026

**Version**: 3.0

**License**: CC BY-NC 4.0 (text), AGPL-3.0-or-later (code)

**DOI**: [10.5281/zenodo.18893515](https://doi.org/10.5281/zenodo.18893515)

**Companion to**: ARRIVAL Protocol v2.0 (DOI: [10.5281/zenodo.18893515](https://doi.org/10.5281/zenodo.18893515))

**Mathematical Foundation**: MEANING-CRDT v1.1 (DOI: 10.5281/zenodo.18702383)

---

## Abstract

The ARRIVAL Protocol enables cross-architecture AI-to-AI coordination through
structured semantic @-atoms (DEUS.PROTOCOL v0.5), validated across 2,200+
experiments. However, a critical limitation persists: all coordination
knowledge is lost between sessions. We present ARRIVAL-MNEMO, a persistent
memory architecture extending the protocol with four memory layers (Episodic,
Procedural, Semantic, Meta), a @MEMORY.* atom family, and MEMORY-CRDT v1.1 ---
a formal specification for cross-temporal memory synchronization using the same
CARE Resolve mathematics that powers real-time dialogue convergence.

We conducted three experimental phases. Phase 14 reveals a negative result:
naive keyword-based global memory injection DEGRADES accuracy by -5.7 pp
(McNemar p=0.724) on GPQA Diamond, discovering the hypercorrection effect in
LLM ensembles --- a cognitive bias previously documented only in humans. Phase
15 introduces CARE-ALERT, a gated real-time intervention system that restores
baseline accuracy while achieving the first statistically significant
improvement in all ARRIVAL experiments: CARE Resolve is significantly higher
than under global injection (Mann-Whitney p=0.042).

Key findings: (1) memory creation via auto-logging is solved; (2) global
pre-session injection triggers hypercorrection; (3) gated real-time
intervention avoids hypercorrection while improving consensus quality;
(4) specific memory helps but generic memory hurts AI coordination.

**Keywords**: AI coordination, persistent memory, CRDT, semantic atoms,
multi-agent systems, hypercorrection, CARE-ALERT

---

## 1. Introduction

### 1.1. The Amnesia Problem

Modern AI coordination protocols operate in a fundamentally amnesiac mode.
When a multi-agent session ends, all accumulated knowledge vanishes. The
agents retain no recollection of which strategies worked, which information
sources proved reliable, or how their peers typically behave. Every new
session starts from absolute zero.

The ARRIVAL Protocol (Kelevra, 2026a) demonstrates that cross-architecture
AI agents can achieve structured coordination through semantic @-atoms, with
results validated across 2,200+ experiments, 23 phases, and 17 LLM
architectures. But this coordination knowledge exists only in log files,
inaccessible to future sessions.

### 1.2. Research Questions

This paper addresses three research questions:

**RQ1**: What memory architecture enables persistent learning across sessions
for AI coordination protocols while maintaining compatibility with the @-atom
communication framework?

**RQ2**: Can the CRDT mathematics used for real-time dialogue convergence
(CARE Resolve) be extended to cross-temporal memory synchronization?

**RQ3**: Does memory injection improve coordination quality (accuracy,
consensus strength) compared to memoryless baselines?

### 1.3. Contributions

1. **Four-layer memory taxonomy** (Episodic, Procedural, Semantic, Meta) with
   @MEMORY.* atoms extending DEUS.PROTOCOL v0.5.
2. **MEMORY-CRDT v1.1**: Formal specification for memory synchronization using
   utility-weighted LWW-Register CRDT with convergence guarantees.
3. **Hypercorrection discovery**: Global pre-session memory injection degrades
   LLM ensemble performance --- a cognitive bias previously documented only
   in humans.
4. **CARE-ALERT system**: Gated real-time intervention achieving the first
   statistically significant improvement across all ARRIVAL experiments
   (Mann-Whitney p=0.042).

---

## 2. Related Work

**Retrieval-Augmented Generation** (Lewis et al., 2020) retrieves relevant
documents to augment generation but operates at the document level without
structured memory layers or cross-agent synchronization.

**MemGPT** (Packer et al., 2023) introduces hierarchical memory management
for LLMs with main context and external storage but targets single-agent
scenarios without multi-agent coordination considerations.

**Generative Agents** (Park et al., 2023) implement memory streams for
simulated social agents with reflection and planning but focus on narrative
coherence rather than structured coordination protocols.

**MEANING-CRDT v1.1** (Kelevra, 2026b) introduced CARE Resolve for real-time
dialogue synchronization in the ARRIVAL Protocol. MEMORY-CRDT extends this
mathematical framework to the temporal dimension.

**Conflict-Free Replicated Data Types** (Shapiro et al., 2011) provide formal
guarantees for distributed data convergence. Our adaptation replaces physical
timestamps with utility scores, maintaining CRDT properties while enabling
value-based conflict resolution.

---

## 3. Architecture

### 3.1. Four Memory Layers

ARRIVAL-MNEMO organizes persistent knowledge into four layers, each serving
a distinct cognitive function:

**Episodic Memory** stores session-level records: what task was performed,
which models participated, what outcome was achieved, and what CARE Resolve
score was observed. TTL: 7--30 days (adaptive). Captures the "what happened"
dimension.

**Procedural Memory** stores validated strategies: approaches that work for
specific task types, with success rates and trial counts. Persistence requires
n_trials >= 3. Captures the "how to act" dimension.

**Semantic Memory** stores derived knowledge: rules, facts, and calibration
data extracted from multiple sessions. Persistence requires evidence_count >= 3.
Captures the "what is true" dimension.

**Meta Memory** stores agent calibration: trust scores, domain-specific
accuracy, and behavioral patterns for each model. Updated via exponential
moving average. Captures the "who to trust" dimension.

### 3.2. @MEMORY.* Atom Family

Nine new atoms extend DEUS.PROTOCOL v0.5:

| Atom | Function |
|------|----------|
| `@MEMORY.EPISODIC` | Reference/inject session-level memory |
| `@MEMORY.PROCEDURAL` | Reference/inject strategy-level memory |
| `@MEMORY.SEMANTIC` | Reference/inject knowledge-level memory |
| `@MEMORY.META` | Reference/inject calibration data |
| `@MEMORY.INJECT` | Request memory injection during session |
| `@MEMORY.STORE` | Request memory persistence after session |
| `@MEMORY.FORGET` | Flag memory for eviction |
| `@MEMORY.CONFLICT` | Signal contradicting memories |
| `@MEMORY.MERGE` | Request memory consolidation |

### 3.3. Injection Protocol

Memory injection follows a seven-step pipeline:

1. **LOAD**: Read memory store from persistent storage (JSON)
2. **FILTER**: Select memories relevant to current @GOAL using keyword
   matching (MVP) or embedding similarity (production)
3. **FORMAT**: Convert selected memories to @MEMORY.* atom notation
4. **INJECT**: Append formatted memories to agent system prompts as
   `[MEMORY CONTEXT]` block
5. **RUN**: Execute ARRIVAL dialogue with memory-augmented agents
6. **EXTRACT**: Create new Episodic memories from session results;
   update Meta memories with calibration data
7. **MERGE**: Integrate new memories into the store using MEMORY-CRDT

---

## 4. MEMORY-CRDT v1.1

### 4.1. From Dialogue to Memory

MEANING-CRDT merges divergent agent positions within a dialogue:

    v_hat = SUM(w_i * v_i) / SUM(w_i)

MEMORY-CRDT applies the same principle across time. When two memory stores
conflict, the merge operation selects the higher-utility version:

    m_hat = argmax_{m in {m_1, m_2}} u(m)

where u(m) is the utility function:

    u(m) = 0.25 * recency + 0.30 * frequency + 0.25 * quality + 0.20 * validation

### 4.2. Utility Components

- **recency(m)** = max(0, 1.0 - age_days / 90). Linear decay over 90-day window.
- **frequency(m)** = min(1.0, access_count / N_layer). N varies by layer:
  Episodic=10, Procedural=20, Semantic=5, Meta=10.
- **quality(m)** = layer-specific: care_resolve (Episodic), success_rate
  (Procedural), confidence (Semantic), trust_score (Meta).
- **validation(m)** = evidence strength, layer-dependent.

### 4.3. CRDT Properties

The merge operation is a **Last-Writer-Wins Register** (LWW-Register) CRDT
where the "timestamp" is replaced by utility score:

- **Commutativity**: MERGE(S1, S2) = MERGE(S2, S1). Utility comparison
  is symmetric.
- **Associativity**: MERGE(MERGE(S1, S2), S3) = MERGE(S1, MERGE(S2, S3)).
  Max-wins is associative.
- **Idempotency**: MERGE(S, S) = S. Merging with self produces no change.

### 4.4. Memory Debt

Analogous to Meaning Debt, Memory Debt measures unresolved inconsistency:

    MmD = SUM(u_i * conflict(m_i)) / SUM(u_i)

where conflict(m) = 1.0 (contradiction), 0.5 (partial overlap), or
0.0 (no conflict). Low MmD indicates a consistent memory store.

### 4.5. Convergence

**Theorem (Memory Convergence)**: Given a sequence of sessions {s_1, ..., s_n}
each producing memory updates, the memory store converges to a stable state
as n -> infinity, provided: (1) the forgetting function removes memories with
utility below threshold theta; (2) the merge function resolves conflicts via
utility maximization; (3) the consolidation function extracts patterns into
semantic memories.

**Proof sketch**: The utility function is bounded [0,1]. Forgetting
monotonically reduces store size for low-utility memories. Merge is a CRDT
join operation (monotonic in the lattice of memory sets ordered by inclusion).
Together, these form a bounded monotonic system that must converge.

### 4.6. Relationship to MEANING-CRDT

| Property | MEANING-CRDT | MEMORY-CRDT |
|----------|-------------|-------------|
| Domain | Dialogue positions | Memory entries |
| Temporal scope | Within a session | Across sessions |
| Weight function | Coherence (agreement) | Utility (value) |
| Merge granularity | Per-round | Per-session |
| Convergence target | Consensus position | Consistent memory |
| Debt metric | Meaning Debt | Memory Debt |
| CRDT type | State-based (GCounter-like) | State-based (LWW-Register) |

**Unifying principle**: Both CRDTs implement weighted convergence under
conflict, applied at different temporal scales.

---

## 5. Pilot Experiment (Phase 14a)

### 5.1. Design

A controlled experiment with 10 MCQ questions across 5 domains (science,
history, logic, law, technology). Models: DeepSeek V3, Llama 3.3 70B,
Qwen 2.5 72B. Three conditions: Seed (build memory), Control (no memory),
Treatment (memory injection).

### 5.2. Results

| Condition | Accuracy | Avg CARE | Cost |
|-----------|----------|----------|------|
| Seed | 3/5 (60%) | 0.850 | $0.008 |
| Control (no memory) | 4/5 (80%) | 0.750 | $0.008 |
| Treatment (memory) | **5/5 (100%)** | **0.850** | $0.010 |

Memory injection corrected the one control error, improved CARE by +13.3%,
and increased atom density by +8.6%. Total cost: $0.026.

---

## 6. Phase 14: Large-Scale Validation (Negative Result)

### 6.1. Design

To test generalizability, we scaled to GPQA Diamond --- 40 graduate-level
science questions (Rein et al., 2023). Alpha trio: GPT-4o + DeepSeek-V3 +
Llama-3.3-70B-Instruct. Memory store: 5 episodic (cognitive scars from
Phase 13 worst dialogues), 2 procedural (meta-strategies), 3 meta (per-agent
domain calibration). Keyword-based retrieval, top-8 injection, 800-char limit.

Data leakage guard: no correct answers, answer letters, question text, or
choices stored. Only structural observations about dialogue dynamics.

### 6.2. Results

| Metric | Phase 13 (N=35) | Phase 14 (N=35) | Delta | p-value |
|--------|----------------|----------------|-------|---------|
| Accuracy | 20/35 (57.1%) | 18/35 (51.4%) | -5.7 pp | McNemar p=0.724 |
| CARE Resolve | 0.966 | 0.916 | -0.050 | M-W p=0.985 |
| Meaning Debt | 0.196 | 0.433 | +0.237 | M-W p=0.994 |

Memory injection did not improve accuracy. The trend is negative but not
statistically significant.

### 6.3. The Hypercorrection Effect

Analysis of auto-stored cognitive scars reveals the failure mechanism.
When told "in past chemistry sessions, DeepSeekV3 was suppressed," GPT-4o
begins second-guessing its own correct answers on ALL chemistry questions,
not just the specific ones where suppression occurred. This parallels the
well-documented human cognitive bias: pre-task warnings about past mistakes
increase anxiety and worsen performance.

LLM ensembles empirically exhibit this classic human pattern: they need
correction DURING the process, not warnings BEFORE it.

### 6.4. Implications

1. **Memory creation is solved**: Auto-logging perfectly captures who was
   suppressed, in which domain, and by how much.
2. **Memory delivery via global injection fails**: Static pre-session
   injection of generic memories degrades performance on novel tasks.
3. **Specific memory helps, generic memory hurts**: Seen questions improved
   (+20 pp); unseen degraded because keyword retrieval injected noise.

---

## 7. Phase 15: Gated CARE-ALERT Validation

### 7.1. Architecture

Phase 14's negative result motivates a paradigm shift from global injection
to real-time intervention. Three independent reviewer analyses converged on
the same diagnosis: correct agents in-process, not before; use a scalpel,
not carpet bombing; gated injection with operational rules, not moralistic
warnings.

**Monitor -> Detect -> Intervene**:

    R1 (Alpha: GPT4o)   -> clean prompt, no memory
    R2 (Beta: DeepSeekV3) -> clean prompt, no memory
        CHECKPOINT #1: compute_interim_metrics([R1, R2])
        Divergence? MD > 0.5? -> Level 1 @CARE.ALERT
    R3 (Gamma: Llama33) -> prompt + alert_1 (if fired)
        CHECKPOINT #2: compute_interim_metrics([R1, R2, R3])
        Divergence? MD > 0.8? -> Level 2 ESCALATED
    R4 (Alpha: GPT4o)   -> prompt + alert_2 (if fired)

**Alert design**: Operational, not moralistic ("Beta selected C, address with
@EVIDENCE" --- NOT "you failed before"). Current state only. Never contains
correct answers, historical data, or trust scores. Clean system prompt,
identical to Phase 13 baseline.

### 7.2. Results: Unseen Questions (N=35)

| Metric | Phase 13 | Phase 14 | Phase 15 | Delta P13->P15 |
|--------|----------|----------|----------|----------------|
| Accuracy | 57.1% | 51.4% | **57.1%** | +0.0 pp |
| CARE | 0.966 | 0.916 | **0.948** | -0.018 |
| Meaning Debt | 0.196 | 0.433 | 0.452 | +0.256 |

Phase 15 restores accuracy to the Phase 13 baseline. The -5.7 pp degradation
from global injection is fully eliminated.

### 7.3. Results: Seen Questions (N=5)

| Metric | Phase 13 | Phase 14 | Phase 15 |
|--------|----------|----------|----------|
| Accuracy | 20% | 40% | **60%** |
| CARE | 0.539 | 0.635 | **0.746** |
| Meaning Debt | 2.455 | 1.944 | **1.602** |

Monotonic improvement across all three metrics through all three phases.

### 7.4. Results: All 40 Questions

| Metric | Phase 13 | Phase 14 | Phase 15 |
|--------|----------|----------|----------|
| Accuracy | 52.5% | 50.0% | **57.5%** |
| CARE | 0.913 | 0.881 | **0.923** |

**CARE Resolve P14 vs P15 (N=40): Mann-Whitney p=0.042 (significant at
alpha=0.05)** --- the first statistically significant result across all
ARRIVAL experiments.

### 7.5. Alert Statistics

Alerts fired on 7/40 questions (17.5%). Accuracy with alert: 57.1% (4/7).
Accuracy without alert: 57.6% (19/33). CARE with alert: 0.968; without:
0.914. The alert does not harm accuracy and CARE is HIGHER when alerts fire.

### 7.6. Minority Voice Protection

Three examples of successful minority voice protection:

- **GPQA_009**: Beta (DeepSeek) correct, Alpha (GPT-4o) wrong. Alert fired,
  final answer followed Beta. CORRECT.
- **GPQA_038**: Gamma (Llama) correct, Alpha+Beta wrong. Alert fired, final
  answer followed Gamma. CORRECT.
- **GPQA_003**: Beta correct against Alpha. Alert fired. CORRECT.

Without alerts, these minority voices would have been suppressed.

### 7.7. Analysis

**Finding 1**: Gated alerts avoid hypercorrection. Phase 14 injected memory
into 100% of questions -> -5.7 pp. Phase 15 alerted on 17.5% -> +0.0 pp.

**Finding 2**: First significant CARE improvement (Mann-Whitney p=0.042).
Gated intervention actively improves consensus quality.

**Finding 3**: Precision targeting works. The 17.5% alert rate demonstrates
intervention only when needed.

**Finding 4**: Memory delivery was the problem, not memory itself. The
three-phase progression confirms:
- Phase 13: Baseline (stateless) -> 57.1%
- Phase 14: Global injection -> 51.4% (-5.7 pp, hypercorrection)
- Phase 15: Gated CARE-ALERT -> 57.1% (baseline restored, CARE significant)

---

## 8. Discussion

### 8.1. The CRDT Unification

The most significant theoretical contribution is the unification of
dialogue-level and memory-level synchronization under the same mathematical
framework. CARE Resolve operates at two temporal scales:

- **Intra-session** (MEANING-CRDT): Merging agent positions in real-time
- **Inter-session** (MEMORY-CRDT): Merging memory states across time

This suggests a general principle: weighted convergence under conflict is a
universal primitive for multi-agent coordination, applicable from
millisecond-level token generation to month-level knowledge accumulation.

### 8.2. Cognitive Bias in LLM Ensembles

The hypercorrection discovery (Phase 14) has implications beyond memory
systems. If LLM ensembles exhibit human-like cognitive biases under
pre-session priming, other known human biases may also manifest:
anchoring effects (confirmed in Phases 20-21 of the parent protocol),
groupthink (measurable via echo-chamber metrics), and confirmation bias.

### 8.3. Design Principles for AI Memory

1. **Create liberally, inject surgically**: Auto-log everything; inject
   only on detected divergence.
2. **Operational over moralistic**: Tell agents what IS happening, not what
   they SHOULD do.
3. **Current state only**: Never transmit historical failures or trust
   scores to agents.
4. **Gated intervention**: Monitor -> Detect -> Intervene beats
   blanket pre-loading.

---

## 9. Limitations

1. N=40 (35 unseen) --- insufficient power for small effects
2. Single agent trio tested --- only Alpha configuration
3. Non-significant primary accuracy result (match != equivalence proof)
4. Keyword retrieval (MVP) --- no semantic similarity
5. No consolidation implemented (Episodic -> Semantic)
6. MD thresholds (0.5, 0.8) set a priori without optimization
7. Single run --- no repeated measurements
8. Cooperative-only scope --- no adversarial memory poisoning tested

---

## 10. Conclusion

ARRIVAL-MNEMO extends the ARRIVAL Protocol with persistent memory, enabling
AI coordination systems that learn across sessions. The four-layer
architecture provides structured knowledge organization while MEMORY-CRDT v1.1
ensures consistent synchronization using the same mathematics that powers
real-time dialogue convergence.

The three-phase experimental progression reveals fundamental principles about
memory delivery in LLM ensembles: global pre-session injection triggers
hypercorrection (-5.7 pp), while gated real-time CARE-ALERT intervention
restores baseline accuracy and achieves the first statistically significant
CARE improvement (Mann-Whitney p=0.042). The system alerts on only 17.5% of
questions, demonstrating precision targeting over carpet bombing.

Total project cost across all phases: $1.17. The entire investigation ---
from architecture design through negative result discovery to validated
real-time intervention --- cost less than $1.20.

---

## References

1. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., & Mordatch, I. (2023).
   Improving Factuality and Reasoning in Language Models through Multiagent
   Debate. arXiv:2305.14325.

2. Kelevra, M. (2026a). ARRIVAL Protocol: Cross-Architecture AI-to-AI
   Coordination Through Structured Semantic Atoms. Preprint.

3. Kelevra, M. (2026b). MEANING-CRDT v1.1: Mathematical Foundation for
   Semantic Conflict Resolution. DOI: 10.5281/zenodo.18702383.

4. Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-Augmented
   Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.

5. Packer, C., Wooders, S., Lin, K., et al. (2023). MemGPT: Towards LLMs
   as Operating Systems. arXiv:2310.08560.

6. Park, J. S., O'Brien, J. C., Cai, C. J., et al. (2023). Generative
   Agents: Interactive Simulacra of Human Behavior. UIST 2023.

7. Rein, D., Hou, B. L., Stickland, A. C., et al. (2023). GPQA: A
   Graduate-Level Google-Proof Q&A Benchmark. arXiv:2311.12022.

8. Shapiro, M., Preguica, N., Baquero, C., & Zawirski, M. (2011).
   Conflict-free Replicated Data Types. SSS 2011.

9. Tulving, E. (1972). Episodic and Semantic Memory. In: Organization of
   Memory. Academic Press.

---

## Appendix A: Memory Store Schema

```python
@dataclass
class EpisodicMemory:
    id: str              # Content-addressed hash
    session_id: str      # Source session identifier
    timestamp: str       # ISO 8601
    task: str            # Task description
    models: List[str]    # Participating models
    outcome: Dict        # {accuracy, care_resolve}
    care_resolve: float  # CARE Resolve score (0.0-1.0)
    meaning_debt: float  # Meaning Debt score
    key_insight: str     # Human-readable summary
    atoms_used: List     # @-atoms observed in session
    ttl_days: int = 30   # Time-to-live
    layer: str = "episodic"

@dataclass
class ProceduralMemory:
    id: str
    strategy_name: str   # Identifier
    task_type: str       # Domain/task category
    description: str     # Strategy description
    success_rate: float  # Observed success rate
    n_trials: int        # Number of trials
    layer: str = "procedural"

@dataclass
class SemanticMemory:
    id: str
    domain: str          # Knowledge domain
    content: str         # Derived knowledge
    confidence: float    # Confidence score
    evidence_count: int  # Supporting evidence
    layer: str = "semantic"

@dataclass
class MetaMemory:
    id: str
    agent_id: str        # Model identifier
    trust_score: float   # Overall trust
    domain_scores: Dict  # Per-domain calibration
    total_sessions: int  # Experience count
    layer: str = "meta"
```

## Appendix B: CARE-ALERT Format Example

```
@CARE.ALERT [Level 1 — Divergence Detected]
After Round 2, agents hold different positions:
- Alpha (GPT-4o): selected answer C
- Beta (DeepSeek-V3): selected answer A
Interim Meaning Debt: 0.72

Please address divergence with @EVIDENCE and @COUNTER.
Consider whether Beta's position has merit before finalizing.
```

## Appendix C: MEMORY-CRDT Formal Properties

**Commutativity**: For any memories m1, m2 with the same ID:
  max(u(m1), u(m2)) = max(u(m2), u(m1))

**Associativity**: For any three stores A, B, C:
  merge(merge(A,B), C) = merge(A, merge(B,C))
  because max is associative and set union is associative.

**Idempotency**: For any store A:
  merge(A, A) = A because for every memory m in A,
  max(u(m), u(m)) = u(m), and A UNION A = A.
