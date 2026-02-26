# ARRIVAL-MNEMO: Memory Store — Load, Save, Query, Merge
# Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
#
# File-based memory store using JSON. Supports:
# - Load/Save to disk
# - Add/Remove memories
# - Query by layer, domain, relevance
# - TTL expiration
# - Utility scoring for forgetting
# - CRDT-compatible merge

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from .schema import (
    Memory, EpisodicMemory, ProceduralMemory, SemanticMemory, MetaMemory,
    memory_from_dict, _now_iso, _hash,
)


class MemoryStore:
    """
    Persistent memory store for ARRIVAL-MNEMO.

    Stores memories as a JSON file on disk. Supports load, save,
    add, query, merge, and forgetting operations.

    Usage:
        store = MemoryStore("path/to/memory.json")
        store.load()
        store.add(EpisodicMemory(session_id="s1", task="MCQ", ...))
        relevant = store.query(goal="logic questions", top_k=5)
        store.save()
    """

    VERSION = "1.1"

    def __init__(self, filepath: str = "arrival_memory.json"):
        self.filepath = Path(filepath)
        self.memories: List[Memory] = []
        self.metadata: Dict[str, Any] = {
            "version": self.VERSION,
            "protocol": "DEUS.PROTOCOL v0.5",
            "created": _now_iso(),
            "last_modified": _now_iso(),
            "total_sessions": 0,
        }

    # ================================================================
    # Persistence: Load / Save
    # ================================================================

    def load(self) -> "MemoryStore":
        """Load memories from JSON file. Creates empty store if file doesn't exist."""
        if not self.filepath.exists():
            print(f"  [MNEMO] No existing memory at {self.filepath}. Starting fresh.")
            return self

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.metadata = data.get("metadata", self.metadata)
        raw_memories = data.get("memories", [])
        self.memories = [memory_from_dict(m) for m in raw_memories]

        print(f"  [MNEMO] Loaded {len(self.memories)} memories from {self.filepath}")
        return self

    def save(self) -> None:
        """Save all memories to JSON file."""
        self.metadata["last_modified"] = _now_iso()
        self.metadata["total_memories"] = len(self.memories)
        self.metadata["by_layer"] = self._count_by_layer()

        data = {
            "metadata": self.metadata,
            "memories": [m.to_dict() for m in self.memories],
        }

        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  [MNEMO] Saved {len(self.memories)} memories to {self.filepath}")

    # ================================================================
    # CRUD Operations
    # ================================================================

    def add(self, memory: Memory) -> None:
        """Add a memory to the store. Deduplicates by ID."""
        existing_ids = {m.id for m in self.memories}
        if memory.id in existing_ids:
            # Update existing
            self.memories = [m if m.id != memory.id else memory for m in self.memories]
        else:
            self.memories.append(memory)

    def remove(self, memory_id: str) -> bool:
        """Remove a memory by ID. Returns True if found and removed."""
        before = len(self.memories)
        self.memories = [m for m in self.memories if m.id != memory_id]
        return len(self.memories) < before

    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a specific memory by ID."""
        for m in self.memories:
            if m.id == memory_id:
                return m
        return None

    # ================================================================
    # Query & Filter
    # ================================================================

    def query_by_layer(self, layer: str) -> List[Memory]:
        """Get all memories of a specific layer."""
        return [m for m in self.memories if m.layer == layer]

    def query_by_domain(self, domain: str) -> List[Memory]:
        """Get semantic memories for a specific domain."""
        return [
            m for m in self.memories
            if isinstance(m, SemanticMemory) and m.domain == domain
        ]

    def query_by_agent(self, agent_model: str) -> List[MetaMemory]:
        """Get meta memories for a specific agent."""
        return [
            m for m in self.memories
            if isinstance(m, MetaMemory) and m.agent_model == agent_model
        ]

    def query_relevant(self, goal: str, top_k: int = 10) -> List[Memory]:
        """
        Query memories relevant to a goal using keyword matching.

        This is a simple keyword-based relevance scorer. For production,
        replace with embedding-based cosine similarity.
        """
        goal_lower = goal.lower()
        goal_words = set(goal_lower.split())

        scored = []
        for m in self.memories:
            score = self._relevance_score(m, goal_words, goal_lower)
            if score > 0:
                scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:top_k]]

    def _relevance_score(self, m: Memory, goal_words: set, goal_lower: str) -> float:
        """Simple keyword-based relevance scoring."""
        text = ""
        if isinstance(m, EpisodicMemory):
            text = f"{m.task} {m.key_insight}".lower()
        elif isinstance(m, ProceduralMemory):
            text = f"{m.task_type} {m.strategy_name} {m.description}".lower()
        elif isinstance(m, SemanticMemory):
            text = f"{m.domain} {m.rule}".lower()
        elif isinstance(m, MetaMemory):
            text = f"{m.agent_model} {' '.join(m.domain_calibration.keys())}".lower()

        if not text:
            return 0.0

        text_words = set(text.split())
        overlap = goal_words & text_words
        if not overlap:
            return 0.0

        score = len(overlap) / max(len(goal_words), 1)

        # Boost for high-confidence memories
        if hasattr(m, "confidence"):
            score *= (0.5 + 0.5 * m.confidence)
        if hasattr(m, "care_resolve"):
            score *= (0.5 + 0.5 * m.care_resolve)

        return score

    # ================================================================
    # Injection: Format memories for system prompt
    # ================================================================

    def format_injection(self, goal: str, top_k: int = 8) -> str:
        """
        Generate a memory injection block for a system prompt.

        Returns a [MEMORY CONTEXT] block with the most relevant memories
        formatted as @MEMORY.* atoms.
        """
        relevant = self.query_relevant(goal, top_k=top_k)

        if not relevant:
            return ""

        lines = ["[MEMORY CONTEXT]",
                 "You have access to memories from previous sessions:",
                 ""]

        for m in relevant:
            lines.append(m.to_injection_text())
            lines.append("")

        lines.append("[/MEMORY CONTEXT]")
        return "\n".join(lines)

    # ================================================================
    # Extraction: Parse new memories from session results
    # ================================================================

    def extract_from_session(
        self,
        session_id: str,
        task: str,
        models: List[str],
        accuracy: str,
        care_resolve: float,
        meaning_debt: float,
        key_insight: str = "",
        atoms_used: List[str] = None,
        domain: str = "",
    ) -> EpisodicMemory:
        """
        Create an EpisodicMemory from session results and add to store.
        Also updates MetaMemory calibration and may create SemanticMemory.
        """
        ep = EpisodicMemory(
            session_id=session_id,
            task=task,
            models=models,
            outcome={"accuracy": accuracy, "care": care_resolve},
            care_resolve=care_resolve,
            meaning_debt=meaning_debt,
            key_insight=key_insight,
            atoms_used=atoms_used or [],
            transcript_hash=_hash(session_id + task),
        )
        self.add(ep)
        self.metadata["total_sessions"] = self.metadata.get("total_sessions", 0) + 1

        # Auto-update meta-memory for each model
        for model in models:
            self._update_meta(model, domain, care_resolve)

        return ep

    def _update_meta(self, model: str, domain: str, care_resolve: float):
        """Update agent calibration based on session result."""
        existing = self.query_by_agent(model)
        if existing:
            meta = existing[0]
            meta.total_sessions += 1
            if domain:
                old_cal = meta.domain_calibration.get(domain, 0.5)
                # Exponential moving average
                meta.domain_calibration[domain] = 0.8 * old_cal + 0.2 * care_resolve
            meta.trust_score = 0.9 * meta.trust_score + 0.1 * care_resolve
            meta.last_calibration = _now_iso()
        else:
            meta = MetaMemory(
                agent_model=model,
                domain_calibration={domain: care_resolve} if domain else {},
                trust_score=care_resolve,
                total_sessions=1,
            )
            self.add(meta)

    # ================================================================
    # Forgetting: Utility-based memory eviction
    # ================================================================

    def forget(self, threshold: float = 0.15) -> int:
        """
        Remove low-utility memories.
        Returns count of memories forgotten.
        """
        before = len(self.memories)
        surviving = []

        for m in self.memories:
            score = self._utility_score(m)
            if score >= threshold:
                surviving.append(m)

        forgotten = before - len(surviving)
        self.memories = surviving

        if forgotten > 0:
            print(f"  [MNEMO] Forgot {forgotten} low-utility memories (threshold={threshold})")

        return forgotten

    def expire_ttl(self) -> int:
        """Remove expired episodic memories. Returns count removed."""
        before = len(self.memories)
        self.memories = [
            m for m in self.memories
            if not (isinstance(m, EpisodicMemory) and m.is_expired())
        ]
        expired = before - len(self.memories)
        if expired > 0:
            print(f"  [MNEMO] Expired {expired} episodic memories past TTL")
        return expired

    def _utility_score(self, m: Memory) -> float:
        """
        Compute utility score for a memory.
        score = 0.25*recency + 0.30*frequency_proxy + 0.25*relevance_proxy + 0.20*validation
        """
        now = datetime.now(timezone.utc)

        # Recency (0-1, decays over 90 days)
        created_str = getattr(m, "created", "") or getattr(m, "last_calibration", "")
        if created_str:
            try:
                created_dt = datetime.fromisoformat(created_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                age_days = (now - created_dt).days
                recency = max(0, 1.0 - age_days / 90)
            except (ValueError, TypeError):
                recency = 0.5
        else:
            recency = 0.5

        # Frequency proxy (based on data richness)
        if isinstance(m, EpisodicMemory):
            freq = min(1.0, len(m.atoms_used) / 10)
        elif isinstance(m, ProceduralMemory):
            freq = min(1.0, m.n_trials / 20)
        elif isinstance(m, SemanticMemory):
            freq = min(1.0, m.evidence_count / 5)
        elif isinstance(m, MetaMemory):
            freq = min(1.0, m.total_sessions / 10)
        else:
            freq = 0.5

        # Relevance proxy (quality indicators)
        if hasattr(m, "care_resolve"):
            relevance = m.care_resolve
        elif hasattr(m, "confidence"):
            relevance = m.confidence
        elif hasattr(m, "success_rate"):
            relevance = m.success_rate
        elif hasattr(m, "trust_score"):
            relevance = m.trust_score
        else:
            relevance = 0.5

        # Validation (is it well-supported?)
        if isinstance(m, SemanticMemory):
            validation = min(1.0, m.evidence_count / 3)
        elif isinstance(m, ProceduralMemory):
            validation = m.success_rate
        elif isinstance(m, MetaMemory):
            validation = min(1.0, m.total_sessions / 5)
        else:
            validation = 0.5

        score = 0.25 * recency + 0.30 * freq + 0.25 * relevance + 0.20 * validation
        return score

    # ================================================================
    # Merge: CRDT-compatible memory merging
    # ================================================================

    def merge(self, other: "MemoryStore") -> int:
        """
        CRDT-merge another MemoryStore into this one.
        For conflicting IDs: keep the one with higher utility.
        Returns count of new memories added.
        """
        my_ids = {m.id: m for m in self.memories}
        added = 0

        for m in other.memories:
            if m.id not in my_ids:
                self.memories.append(m)
                added += 1
            else:
                # Conflict: keep higher utility
                my_score = self._utility_score(my_ids[m.id])
                their_score = other._utility_score(m)
                if their_score > my_score:
                    self.memories = [
                        x if x.id != m.id else m for x in self.memories
                    ]

        if added > 0:
            print(f"  [MNEMO] Merged {added} new memories from external store")

        return added

    # ================================================================
    # Stats & Diagnostics
    # ================================================================

    def _count_by_layer(self) -> Dict[str, int]:
        counts = {}
        for m in self.memories:
            layer = m.layer
            counts[layer] = counts.get(layer, 0) + 1
        return counts

    def stats(self) -> Dict[str, Any]:
        """Return store statistics."""
        by_layer = self._count_by_layer()
        return {
            "total": len(self.memories),
            "by_layer": by_layer,
            "version": self.VERSION,
            "total_sessions": self.metadata.get("total_sessions", 0),
        }

    def summary(self) -> str:
        """Human-readable summary."""
        s = self.stats()
        lines = [
            f"ARRIVAL-MNEMO Store v{s['version']}",
            f"  Total memories: {s['total']}",
            f"  Sessions tracked: {s['total_sessions']}",
        ]
        for layer, count in s["by_layer"].items():
            lines.append(f"  {layer}: {count}")
        return "\n".join(lines)
