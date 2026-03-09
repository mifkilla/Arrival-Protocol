#!/usr/bin/env python3
# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 14 Step 2: Initialize ARRIVAL-MNEMO Memory Store
======================================================
Creates the starting memory store for Phase 14 from Phase 13 cognitive scars.

Memory layers populated:
  - 5x EpisodicMemory: One per seen question (structural failure patterns)
  - 2x ProceduralMemory: Meta-strategies derived from failure analysis
  - 3x MetaMemory: Per-agent calibration (GPT4o, DeepSeekV3, Llama33)

DATA LEAKAGE GUARD:
- NEVER stores correct answers, answer letters, question text, or choices
- key_insight contains ONLY structural observations about dialogue dynamics
- Outcome stores health_assessment, NOT correctness

Usage:
    python init_memory_store.py              # Create memory store
    python init_memory_store.py --verbose    # Show detailed output
    python init_memory_store.py --audit      # Audit for data leakage

Output:
    results/arrival_memory_alpha.json

Author: Mefodiy Kelevra
ORCID: 0009-0003-4153-392X
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone

# Fix Windows cp1251 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PHASE14_TRIO, PHASE14_TRIO_NAME, PHASE14_SCARS_FILE,
    PHASE14_MEMORY_FILE, PHASE14_BASELINE_FILE,
    MODEL_SHORT,
)
from memory.store import MemoryStore
from memory.schema import (
    EpisodicMemory, ProceduralMemory, MetaMemory,
)


# ================================================================
# Structural key_insight templates (NO answer information!)
# ================================================================
# These describe WHY the dialogue failed structurally, not WHAT
# the correct answer was.

KEY_INSIGHTS = {
    "GPQA_032": (
        "Biology question: DeepSeekV3 proposed alternative analysis (loss=8.55) "
        "but was persistently overridden by GPT4o and Llama33 without evidence exchange. "
        "No @CONFLICT/@RESOLUTION atoms used. Total dissatisfaction=11.75, "
        "fairness_index=0.69. High GPT4o debt=1.31 suggests rushed consensus."
    ),
    "GPQA_025": (
        "Chemistry question: DeepSeekV3 minority position (loss=8.55) completely "
        "ignored despite persistent disagreement. Llama33 aligned with GPT4o "
        "without independent reasoning. 8 @CONSENSUS atoms but MD=3.41 — "
        "consensus signal was premature. Fairness=0.91 misleading (only 2 agents lost)."
    ),
    "GPQA_012": (
        "Physics question: Both DeepSeekV3 (loss=3.80) and Llama33 (loss=3.60) "
        "had alternative positions but neither was explored. GPT4o had zero loss — "
        "dominated without challenge. Fairness=0.94 hides the fact that "
        "2/3 agents were overridden. Per-agent debt spread across all three."
    ),
    "GPQA_019": (
        "Chemistry question with late_flip dynamics: consensus changed after R2. "
        "Both DeepSeekV3 and Llama33 had equal loss=3.60. All meaning debt (1.93) "
        "concentrated in GPT4o — unusual pattern where dominant agent accumulated "
        "debt. 6 @C atoms suggest high coordination but fairness=0.0."
    ),
    "GPQA_018": (
        "Chemistry question: Dialogue quality was poor despite reaching consensus. "
        "DeepSeekV3 (loss=3.60) and Llama33 (loss=3.20) were persistent minorities. "
        "GPT4o dominated without engaging minority positions — "
        "minority voices with potentially valid reasoning were suppressed."
    ),
}


def load_scars() -> dict:
    """Load Phase 14 scars from extract_scars.py output."""
    path = str(PHASE14_SCARS_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Scars file not found: {path}\n"
            f"Run extract_scars.py first."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_baseline_solo_accuracy() -> dict:
    """
    Extract per-agent solo accuracy from Phase 13 baseline.
    Returns: {agent_name: {domain: accuracy, ..., "_overall": accuracy}}
    """
    path = str(PHASE14_BASELINE_FILE)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    alpha = data["results"]["alpha"]

    from collections import defaultdict
    agent_domain_stats = defaultdict(lambda: defaultdict(lambda: {"total": 0, "correct": 0}))
    agent_total = defaultdict(lambda: {"total": 0, "correct": 0})

    for q in alpha:
        domain = q.get("domain", "unknown")
        solo = q.get("solo", [])
        for s in solo:
            agent = s["model"]
            correct = s.get("correct", False)
            agent_domain_stats[agent][domain]["total"] += 1
            agent_domain_stats[agent][domain]["correct"] += int(correct)
            agent_total[agent]["total"] += 1
            agent_total[agent]["correct"] += int(correct)

    result = {}
    for agent in agent_total:
        t = agent_total[agent]
        overall = t["correct"] / t["total"] if t["total"] > 0 else 0.0
        domain_acc = {}
        for domain, stats in agent_domain_stats[agent].items():
            domain_acc[domain] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        domain_acc["_overall"] = overall
        domain_acc["_total_questions"] = t["total"]
        domain_acc["_total_correct"] = t["correct"]
        result[agent] = domain_acc

    return result


def create_episodic_memories(scars: list) -> list:
    """
    Create 5 EpisodicMemory entries from cognitive scars.
    Each contains ONLY structural observations, NO answer information.
    """
    trio_short = [MODEL_SHORT[m] for m in PHASE14_TRIO]
    memories = []

    for scar in scars:
        qid = scar["question_id"]
        domain = scar["domain"]

        ep = EpisodicMemory(
            session_id=f"phase13_alpha_{qid}",
            task=f"GPQA Diamond {domain}",
            models=trio_short,
            outcome={
                "health": scar["health_assessment"],
                "round_dynamics": scar["round_dynamics"],
                "minority_voice": scar["minority_voice"],
            },
            care_resolve=scar["care_resolve"],
            meaning_debt=scar["meaning_debt"],
            key_insight=KEY_INSIGHTS.get(qid, f"Structural failure in {domain} domain."),
            atoms_used=list(scar.get("atom_count", {}).keys()),
            ttl_days=365,  # Long-lived — critical training data
        )

        # === DATA LEAKAGE AUDIT ===
        ep_dict = ep.to_dict()
        for forbidden_key in ["correct_answer", "question", "choices", "answer"]:
            assert forbidden_key not in ep_dict, \
                f"DATA LEAKAGE: {forbidden_key} found in episodic memory for {qid}"
        assert "correct_answer" not in ep.key_insight.lower(), \
            f"DATA LEAKAGE: 'correct_answer' phrase found in key_insight for {qid}"
        # Check that no single letter answer patterns like "answer is A" appear
        import re
        assert not re.search(r'answer\s+is\s+[A-D]', ep.key_insight, re.IGNORECASE), \
            f"DATA LEAKAGE: answer letter found in key_insight for {qid}"

        memories.append(ep)

    return memories


def create_procedural_memories(scars: list) -> list:
    """
    Create meta-strategies from patterns across all 5 failure scars.
    """
    memories = []

    # Strategy 1: Minority Voice Protection
    # Observation: In 5/5 scars, DeepSeekV3 was the minority voice with loss >= 3.6
    # In 4/5 cases, persistent_minority pattern with zero exploration
    proc_minority = ProceduralMemory(
        strategy_name="minority_voice_protection",
        task_type="GPQA Diamond multi-agent",
        description=(
            "When an agent disagrees (high per_agent_loss), explicitly request "
            "@EVIDENCE before proceeding to @RESOLUTION. In 5/5 observed failures, "
            "the minority voice (DeepSeekV3, avg loss=5.63) was overridden without "
            "evidence exchange. Force at least one round of explicit @CONFLICT + "
            "@EVIDENCE before @CONSENSUS. This prevents premature consensus."
        ),
        success_rate=0.0,  # Not yet validated
        n_trials=5,
        conditions={
            "trigger": "per_agent_loss > 3.0 for any agent",
            "action": "request @EVIDENCE from minority agent before @RESOLUTION",
            "observed_pattern": "persistent_minority in 4/5, late_flip in 1/5",
        },
    )
    memories.append(proc_minority)

    # Strategy 2: Conflict Resolution Before Consensus
    # Observation: High @CONSENSUS count (avg=5.6) with high MD (avg=2.46)
    # means consensus was declared without resolving underlying conflicts
    proc_conflict = ProceduralMemory(
        strategy_name="conflict_resolution_before_consensus",
        task_type="GPQA Diamond multi-agent",
        description=(
            "Ensure all @CONFLICT markers have paired @RESOLUTION before declaring "
            "@CONSENSUS. In observed failures, avg @CONSENSUS=5.6 atoms but "
            "avg Meaning Debt=2.46 — consensus was premature. No @CONFLICT atoms "
            "were used in any of the 5 worst dialogues, suggesting conflicts were "
            "implicit and never surfaced. Agents should explicitly flag disagreements."
        ),
        success_rate=0.0,
        n_trials=5,
        conditions={
            "trigger": "meaning_debt > 1.5 at any dialogue point",
            "action": "pause consensus, request @CONFLICT acknowledgment from all agents",
            "observed_pattern": "0 @CONFLICT atoms in all 5 failure cases",
        },
    )
    memories.append(proc_conflict)

    return memories


def create_meta_memories(solo_accuracy: dict) -> list:
    """
    Create per-agent MetaMemory from Phase 13 solo accuracy data.
    """
    memories = []

    for agent_name, data in solo_accuracy.items():
        domain_cal = {}
        for key, val in data.items():
            if not key.startswith("_"):
                domain_cal[key] = round(val, 4)

        meta = MetaMemory(
            agent_model=agent_name,
            domain_calibration=domain_cal,
            trust_score=round(data.get("_overall", 0.0), 4),
            total_sessions=data.get("_total_questions", 0),
        )
        memories.append(meta)

    return memories


def audit_memory_store(store: MemoryStore) -> bool:
    """
    Audit the memory store for data leakage.
    Returns True if clean, raises AssertionError if leakage detected.
    """
    import re
    forbidden_patterns = [
        r'correct.?answer',
        r'answer\s+is\s+[A-D]',
        r'the\s+answer\s+[A-D]',
        r'option\s+[A-D]\s+is\s+correct',
        r'choose\s+[A-D]',
    ]

    for m in store.memories:
        m_dict = m.to_dict()
        m_json = json.dumps(m_dict, ensure_ascii=False).lower()

        # Check for forbidden keys
        for key in ["correct_answer", "question_text", "choices"]:
            assert key not in m_dict, \
                f"DATA LEAKAGE: key '{key}' found in memory {getattr(m, 'id', '?')}"

        # Check for answer patterns in all text fields
        for pattern in forbidden_patterns:
            match = re.search(pattern, m_json, re.IGNORECASE)
            assert match is None, \
                f"DATA LEAKAGE: pattern '{pattern}' found in memory {getattr(m, 'id', '?')}: {match.group()}"

    return True


def main():
    parser = argparse.ArgumentParser(description="Phase 14: Initialize Memory Store")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    parser.add_argument("--audit", "-a", action="store_true", help="Run data leakage audit only")
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"  PHASE 14 -- Step 2: Initialize ARRIVAL-MNEMO Memory Store")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*70}")

    # ================================================================
    # Load inputs
    # ================================================================
    print(f"\n  Loading scars from: {PHASE14_SCARS_FILE}")
    scars_data = load_scars()
    scars = scars_data["scars"]
    print(f"  Loaded {len(scars)} cognitive scars")

    print(f"\n  Loading Phase 13 solo accuracy from: {PHASE14_BASELINE_FILE}")
    solo_accuracy = load_baseline_solo_accuracy()
    for agent, data in solo_accuracy.items():
        print(f"    {agent}: {data['_total_correct']}/{data['_total_questions']} "
              f"= {data['_overall']:.1%} overall")

    # ================================================================
    # Create memory store
    # ================================================================
    store = MemoryStore(str(PHASE14_MEMORY_FILE))

    # Episodic memories (5x)
    print(f"\n  Creating episodic memories...")
    episodic = create_episodic_memories(scars)
    for ep in episodic:
        store.add(ep)
        if args.verbose:
            print(f"    + {ep.id}: {ep.task} (CARE={ep.care_resolve:.3f}, MD={ep.meaning_debt:.3f})")

    # Procedural memories (2x)
    print(f"  Creating procedural memories...")
    procedural = create_procedural_memories(scars)
    for proc in procedural:
        store.add(proc)
        if args.verbose:
            print(f"    + {proc.id}: {proc.strategy_name}")

    # Meta memories (3x)
    print(f"  Creating meta memories...")
    meta = create_meta_memories(solo_accuracy)
    for m in meta:
        store.add(m)
        if args.verbose:
            print(f"    + {m.id}: {m.agent_model} (trust={m.trust_score:.3f})")

    # ================================================================
    # Data Leakage Audit
    # ================================================================
    print(f"\n  Running data leakage audit...")
    try:
        clean = audit_memory_store(store)
        print(f"  DATA LEAKAGE AUDIT: PASSED (no answer information found)")
    except AssertionError as e:
        print(f"  DATA LEAKAGE AUDIT: FAILED — {e}")
        sys.exit(1)

    # ================================================================
    # Save
    # ================================================================
    store.metadata["total_sessions"] = 5  # 5 seen questions from Phase 13
    store.metadata["experiment"] = "ARRIVAL-MNEMO Phase 14"
    store.metadata["source"] = "Phase 13 Alpha trio cognitive scars"
    store.metadata["data_leakage_audit"] = "passed"
    store.save()

    # ================================================================
    # Summary
    # ================================================================
    stats = store.stats()
    print(f"\n  {'='*70}")
    print(f"  MEMORY STORE SUMMARY")
    print(f"  {'='*70}")
    print(f"  Total memories: {stats['total']}")
    for layer, count in stats['by_layer'].items():
        print(f"    {layer}: {count}")
    print(f"  File: {PHASE14_MEMORY_FILE}")

    # Show sample injection
    if args.verbose:
        print(f"\n  {'='*70}")
        print(f"  SAMPLE MEMORY INJECTION (for 'GPQA Diamond physics' goal)")
        print(f"  {'='*70}")
        injection = store.format_injection("GPQA Diamond physics", top_k=8)
        print(injection)

    # Audit mode: just verify and exit
    if args.audit:
        print(f"\n  Audit complete. Checking injection text for leakage...")
        for m in store.memories:
            injection_text = m.to_injection_text()
            assert "correct answer" not in injection_text.lower(), \
                f"LEAKAGE in injection text of {m.id}"
        print(f"  Injection text audit: PASSED")

    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
