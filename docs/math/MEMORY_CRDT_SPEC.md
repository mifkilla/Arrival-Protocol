# MEMORY-CRDT v1.1 Specification

**Cross-Temporal Memory Synchronization for ARRIVAL Protocol**

Authors: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
Date: February 22, 2026
Status: Draft Specification
License: CC BY-NC 4.0

---

## Abstract

MEMORY-CRDT v1.1 extends the MEANING-CRDT mathematics (CARE Resolve) from
real-time dialogue synchronization to cross-temporal memory synchronization.
The core insight: if weighted vector averaging can merge divergent agent
positions during a dialogue, the same operation can merge divergent memory
states across sessions, agents, and time.

This specification defines the formal properties, merge operations, and
convergence guarantees for persistent memory in the ARRIVAL Protocol.

---

## 1. Background: MEANING-CRDT v1.1

MEANING-CRDT (from ARRIVAL CRDT v2.0) defines **CARE Resolve** — a
Conflict-Aware Resolution Engine that merges multiple agent positions
into a single resolved value:

```
CARE Resolve (Dialogue):
  v̂ = Σᵢ(wᵢ · vᵢ) / Σᵢ(wᵢ)

  where:
    vᵢ = position vector of agent i (semantic embedding or scalar)
    wᵢ = coherence weight of agent i (0.0 to 1.0)
    v̂  = resolved consensus position
```

**Meaning Debt** measures unresolved divergence:

```
  MD = Σᵢ wᵢ · ‖vᵢ - v̂‖ / Σᵢ wᵢ
```

These operations satisfy CRDT properties: commutativity, associativity,
idempotency, and monotonic convergence.

---

## 2. Extension: MEMORY-CRDT

### 2.1. Core Mapping

| Dialogue CRDT | Memory CRDT |
|--------------|-------------|
| Agent position vᵢ | Memory entry mᵢ |
| Coherence weight wᵢ | Utility score uᵢ |
| Resolved position v̂ | Merged memory m̂ |
| Meaning Debt MD | Memory Debt MmD |
| Round of dialogue | Session (temporal unit) |
| Agent identity | Memory source (agent × session) |

### 2.2. Memory Utility Score

The utility score replaces coherence weight. It measures how valuable
a memory is for retention:

```
uᵢ = α · recency(mᵢ) + β · frequency(mᵢ) + γ · quality(mᵢ) + δ · validation(mᵢ)

Default weights: α=0.25, β=0.30, γ=0.25, δ=0.20
```

Where:
- **recency(m)** = max(0, 1.0 - age_days / 90)
  - Linear decay over 90-day window
  - Recently created memories have higher utility

- **frequency(m)** = min(1.0, access_count / N_layer)
  - N_layer varies by memory type:
    - Episodic: N = 10 (atom count proxy)
    - Procedural: N = 20 (trial count)
    - Semantic: N = 5 (evidence count)
    - Meta: N = 10 (session count)

- **quality(m)** = layer-specific quality indicator
  - Episodic: care_resolve (0.0–1.0)
  - Procedural: success_rate (0.0–1.0)
  - Semantic: confidence (0.0–1.0)
  - Meta: trust_score (0.0–1.0)

- **validation(m)** = evidence strength
  - Episodic: 0.5 (default, not validated)
  - Procedural: success_rate
  - Semantic: min(1.0, evidence_count / 3)
  - Meta: min(1.0, total_sessions / 5)

### 2.3. Memory Merge Operation

Given two memory stores S₁ and S₂, the merge operation produces S₃:

```
MERGE(S₁, S₂) → S₃

For each memory ID across both stores:
  Case 1: ID exists only in S₁ → include in S₃
  Case 2: ID exists only in S₂ → include in S₃
  Case 3: ID exists in both (conflict) →
    if u(S₁[id]) ≥ u(S₂[id]):
      S₃[id] = S₁[id]
    else:
      S₃[id] = S₂[id]
```

This is a **Last-Writer-Wins Register** (LWW-Register) CRDT where the
"timestamp" is replaced by utility score. This guarantees:

- **Commutativity**: MERGE(S₁, S₂) = MERGE(S₂, S₁)
  - Utility comparison is symmetric
- **Associativity**: MERGE(MERGE(S₁, S₂), S₃) = MERGE(S₁, MERGE(S₂, S₃))
  - Max-wins is associative
- **Idempotency**: MERGE(S, S) = S
  - Merging with self produces no change

### 2.4. Memory Debt

Analogous to Meaning Debt, Memory Debt measures unresolved inconsistency
in the memory store:

```
MmD = Σᵢ uᵢ · conflict(mᵢ) / Σᵢ uᵢ

where conflict(mᵢ) = {
  1.0  if mᵢ contradicts another memory in the store
  0.5  if mᵢ partially overlaps with a different memory
  0.0  if mᵢ has no conflicts
}
```

Low Memory Debt (MmD → 0) indicates a consistent, well-maintained memory store.
High Memory Debt (MmD → 1) indicates contradictions requiring resolution.

### 2.5. Convergence Properties

**Theorem (Memory Convergence)**: Given a sequence of sessions
{s₁, s₂, ..., sₙ} each producing memory updates, the memory store
converges to a stable state as n → ∞, provided:

1. The forgetting function removes memories with utility below threshold θ
2. The merge function resolves conflicts via utility maximization
3. The consolidation function extracts patterns into semantic memories

**Proof sketch**: The utility function is bounded [0, 1]. The forgetting
function monotonically reduces store size for low-utility memories.
The merge function is a CRDT join operation (monotonic in the lattice of
memory sets ordered by inclusion). The consolidation function is monotonic
in semantic density. Together, these form a bounded monotonic system
that must converge.

---

## 3. Formal Definition

### 3.1. Memory State

A Memory State is a tuple:

```
MS = (M, μ, T)

where:
  M = {m₁, m₂, ..., mₙ} — set of memory entries
  μ : M → [0,1]          — utility function
  T = session counter     — monotonically increasing timestamp
```

### 3.2. Operations

**Store** (add new memory):
```
STORE(MS, m) → MS'
  where MS'.M = MS.M ∪ {m}
        MS'.T = MS.T + 1
```

**Forget** (remove low-utility memories):
```
FORGET(MS, θ) → MS'
  where MS'.M = {m ∈ MS.M | μ(m) ≥ θ}
```

**Inject** (select relevant memories for a goal):
```
INJECT(MS, goal, k) → [m₁, m₂, ..., mₖ]
  where mᵢ are the top-k memories by relevance(m, goal)
  ordered by μ(m) × similarity(m, goal)
```

**Merge** (combine two memory states):
```
MERGE(MS₁, MS₂) → MS₃
  where MS₃.M = MS₁.M ∪ MS₂.M  (with conflict resolution by max utility)
        MS₃.T = max(MS₁.T, MS₂.T) + 1
```

**Consolidate** (extract patterns from episodic to semantic):
```
CONSOLIDATE(MS, domain, min_count) → MS'
  Let E = {m ∈ MS.M | m.layer = "episodic" ∧ m.domain = domain}
  If |E| ≥ min_count:
    Let pattern = summarize(E)
    Let s = SemanticMemory(domain, pattern, confidence=avg_care(E), evidence=|E|)
    MS'.M = MS.M ∪ {s}
```

### 3.3. State Lattice

Memory states form a join-semilattice under the MERGE operation:

```
(MS₁ ⊔ MS₂).M = MS₁.M ∪ MS₂.M  (with max-utility conflict resolution)
```

The bottom element ⊥ is the empty memory state.
The partial order is defined by set inclusion with utility ordering.

---

## 4. Relationship to MEANING-CRDT

| Property | MEANING-CRDT | MEMORY-CRDT |
|----------|-------------|-------------|
| Domain | Dialogue positions | Memory entries |
| Temporal scope | Within a session | Across sessions |
| Weight function | Coherence (agreement) | Utility (value) |
| Merge granularity | Per-round | Per-session |
| Convergence target | Consensus position | Consistent memory |
| Debt metric | Meaning Debt | Memory Debt |
| CRDT type | State-based (GCounter-like) | State-based (LWW-Register) |

**Key difference**: MEANING-CRDT operates on continuous vector spaces
(agent positions in semantic space). MEMORY-CRDT operates on discrete
memory entries with utility-based selection. Both use weighted averaging
as the core merge primitive.

**Unifying principle**: Both CRDTs implement the same abstract pattern —
**weighted convergence under conflict** — applied at different temporal scales.

---

## 5. Implementation

### 5.1. Python Reference Implementation

The reference implementation is in `src/memory/store.py`.

Key methods mapping to formal operations:

| Formal Operation | Python Method | Notes |
|-----------------|---------------|-------|
| STORE | `store.add(memory)` | Deduplicates by ID |
| FORGET | `store.forget(threshold)` | Removes below threshold |
| INJECT | `store.format_injection(goal, top_k)` | Keyword relevance |
| MERGE | `store.merge(other_store)` | Max-utility conflict resolution |
| μ(m) | `store._utility_score(m)` | Four-component formula |
| CONSOLIDATE | Not yet implemented | Roadmap Phase 4 |

### 5.2. Utility Score Implementation

```python
def _utility_score(self, m: Memory) -> float:
    recency = max(0, 1.0 - age_days / 90)
    frequency = min(1.0, access_metric / N_layer)
    quality = getattr(m, quality_attr, 0.5)
    validation = evidence_strength(m)

    return 0.25 * recency + 0.30 * frequency + 0.25 * quality + 0.20 * validation
```

### 5.3. Merge Implementation

```python
def merge(self, other: MemoryStore) -> int:
    my_ids = {m.id: m for m in self.memories}
    added = 0

    for m in other.memories:
        if m.id not in my_ids:
            self.memories.append(m)
            added += 1
        else:
            # CRDT conflict resolution: max utility wins
            if other._utility_score(m) > self._utility_score(my_ids[m.id]):
                self.memories = [x if x.id != m.id else m for x in self.memories]

    return added
```

---

## 6. Limitations and Future Work

### 6.1. Current Limitations

1. **Keyword retrieval**: MVP uses word overlap, not semantic similarity.
   Production requires embedding-based retrieval.

2. **No vector clocks**: Simplified from full CRDT vector clocks to
   utility-based comparison. Sufficient for single-file storage,
   insufficient for distributed multi-agent memory networks.

3. **No consolidation**: Episodic → Semantic consolidation is specified
   but not implemented. Requires NLP summarization.

4. **Conflict detection**: Currently implicit (ID collision). Production
   needs content-level contradiction detection.

5. **Static injection**: Memory injected only at session start. Production
   needs runtime injection via @MEMORY.INJECT atoms.

### 6.2. Future Extensions

1. **Distributed MEMORY-CRDT**: Full vector clock implementation for
   multi-agent memory networks where each agent maintains local state.

2. **Embedding versioning**: Track which embedding model version was used
   for each memory entry (per DeepSeek R1 recommendation).

3. **Energy-based eviction**: Replace fixed utility formula with
   energy model: `score = recompute_cost / storage_cost`
   (per DeepSeek R1 recommendation).

4. **Adaptive weights**: Learn optimal α, β, γ, δ weights via
   reinforcement learning from memory usage patterns.

5. **Memory Graphs**: Add relational links between memories
   (e.g., "Strategy X depends on Rule Y") for dependency-aware forgetting.

---

## 7. Verification Criteria

The MEMORY-CRDT implementation can be verified by checking:

1. **Commutativity**: `merge(A, B).memories == merge(B, A).memories`
2. **Idempotency**: `merge(A, A).memories == A.memories`
3. **Monotonicity**: `|merge(A, B).memories| ≥ max(|A.memories|, |B.memories|)`
   (before forgetting)
4. **Convergence**: After sufficient sessions, Memory Debt approaches 0
5. **Utility ordering**: Higher-utility memories survive forgetting;
   lower-utility memories are evicted first

---

## References

1. Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011).
   "Conflict-free Replicated Data Types." SSS 2011.

2. ARRIVAL Protocol v2.0 — Kelevra, M. (2026). MEANING-CRDT v1.1.

3. DEUS.PROTOCOL v0.5 — 66 standard semantic atoms.
