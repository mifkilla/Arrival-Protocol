# ARRIVAL-MNEMO: Memory Schema Definitions
# Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
#
# Defines the four memory layer data structures:
# Episodic, Procedural, Semantic, Meta

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, timezone
import hashlib
import json


def _hash(data: str) -> str:
    """Generate a short SHA-256 hash for content addressing."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def _now_iso() -> str:
    """UTC timestamp in ISO format with Z suffix (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class EpisodicMemory:
    """Session-level memory: what happened in a specific dialogue."""
    id: str = ""
    session_id: str = ""
    timestamp: str = ""
    task: str = ""
    models: List[str] = field(default_factory=list)
    outcome: Dict[str, Any] = field(default_factory=dict)
    care_resolve: float = 0.0
    meaning_debt: float = 0.0
    key_insight: str = ""
    atoms_used: List[str] = field(default_factory=list)
    transcript_hash: str = ""
    ttl_days: int = 30
    created: str = ""
    layer: str = "episodic"

    def __post_init__(self):
        if not self.created:
            self.created = _now_iso()
        if not self.id:
            self.id = f"ep_{_hash(self.session_id + self.task + self.created)}"

    def is_expired(self) -> bool:
        created_dt = datetime.fromisoformat(self.created.rstrip("Z")).replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > created_dt + timedelta(days=self.ttl_days)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_injection_text(self) -> str:
        """Format for injection into system prompt."""
        return (
            f"@MEMORY.EPISODIC [session={self.session_id}]: "
            f"Task '{self.task}' → {self.outcome}. "
            f"CARE={self.care_resolve:.3f}, MD={self.meaning_debt:.3f}. "
            f"Insight: {self.key_insight}"
        )


@dataclass
class ProceduralMemory:
    """Strategy-level memory: what approaches work."""
    id: str = ""
    strategy_name: str = ""
    task_type: str = ""
    description: str = ""
    success_rate: float = 0.0
    n_trials: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)
    created: str = ""
    last_used: str = ""
    layer: str = "procedural"

    def __post_init__(self):
        if not self.created:
            self.created = _now_iso()
        if not self.id:
            self.id = f"proc_{_hash(self.strategy_name + self.task_type)}"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_injection_text(self) -> str:
        return (
            f"@MEMORY.PROCEDURAL [{self.strategy_name}]: "
            f"For '{self.task_type}' tasks — {self.description} "
            f"(success_rate={self.success_rate:.0%}, n={self.n_trials})"
        )


@dataclass
class SemanticMemory:
    """Knowledge-level memory: learned facts and rules."""
    id: str = ""
    domain: str = ""
    rule: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    source_sessions: List[str] = field(default_factory=list)
    created: str = ""
    last_updated: str = ""
    layer: str = "semantic"

    def __post_init__(self):
        if not self.created:
            self.created = _now_iso()
        if not self.last_updated:
            self.last_updated = self.created
        if not self.id:
            self.id = f"sem_{_hash(self.domain + self.rule)}"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_injection_text(self) -> str:
        return (
            f"@MEMORY.SEMANTIC [domain={self.domain}]: "
            f"{self.rule} "
            f"(confidence={self.confidence:.2f}, evidence_count={self.evidence_count})"
        )


@dataclass
class MetaMemory:
    """Agent calibration and trust data."""
    id: str = ""
    agent_model: str = ""
    domain_calibration: Dict[str, float] = field(default_factory=dict)
    trust_score: float = 0.0
    total_sessions: int = 0
    last_calibration: str = ""
    layer: str = "meta"

    def __post_init__(self):
        if not self.last_calibration:
            self.last_calibration = _now_iso()
        if not self.id:
            self.id = f"meta_{_hash(self.agent_model)}"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_injection_text(self) -> str:
        cal_str = ", ".join(f"{k}={v:.2f}" for k, v in self.domain_calibration.items())
        return (
            f"@MEMORY.META [agent={self.agent_model}]: "
            f"trust={self.trust_score:.2f}, calibration=[{cal_str}]"
        )


# Type alias for any memory
Memory = EpisodicMemory | ProceduralMemory | SemanticMemory | MetaMemory

MEMORY_CLASSES = {
    "episodic": EpisodicMemory,
    "procedural": ProceduralMemory,
    "semantic": SemanticMemory,
    "meta": MetaMemory,
}


def memory_from_dict(data: dict) -> Memory:
    """Reconstruct a Memory object from a dictionary."""
    layer = data.get("layer", "episodic")
    cls = MEMORY_CLASSES.get(layer, EpisodicMemory)
    # Filter to only known fields
    valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return cls(**filtered)
