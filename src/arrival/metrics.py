# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
ARRIVAL Phase 4: Automated Metrics Extraction
Atom counting, consensus detection, protocol compliance, emergence detection.
"""

import re
from typing import Dict, List, Tuple, Set, Optional

from arrival.config import KNOWN_ATOMS


# ============================================================
# Atom Detection
# ============================================================

# Pattern: @WORD or @WORD[...] — captures the @WORD part
ATOM_PATTERN = re.compile(r'(@[A-Z_]{1,20})(?:\[|[^a-zA-Z]|$)')


def find_all_atoms(text: str) -> List[str]:
    """Find all @ATOM references in text."""
    return ATOM_PATTERN.findall(text)


def count_protocol_atoms(text: str) -> Dict[str, int]:
    """Count each unique @ATOM occurrence in text."""
    atoms = find_all_atoms(text)
    counts: Dict[str, int] = {}
    for atom in atoms:
        counts[atom] = counts.get(atom, 0) + 1
    return counts


def detect_emergent_atoms(text: str) -> List[str]:
    """Find @ATOMS not in the known set of standard atoms."""
    atoms = set(find_all_atoms(text))
    emergent = [a for a in atoms if a not in KNOWN_ATOMS]
    return sorted(emergent)


# ============================================================
# Consensus Detection
# ============================================================

CONSENSUS_MARKERS = [
    "@CONSENSUS",
    "consensus",
    "accept",
    "agreed",
    "agreement reached",
    "we agree",
]

REJECTION_MARKERS = [
    "reject",
    "impasse",
    "disagree",
    "cannot accept",
    "no consensus",
]


def detect_consensus(dialogue: List[Dict]) -> Tuple[bool, int]:
    """
    Detect if consensus was reached in a dialogue.

    Args:
        dialogue: List of {"round": int, "from": str, "message": str}

    Returns:
        (consensus_reached, round_number) — round_number is the first round
        where consensus markers appear. -1 if not reached.
    """
    for entry in dialogue:
        msg = entry.get("message", "").lower()
        round_num = entry.get("round", -1)

        has_consensus = any(m in msg for m in CONSENSUS_MARKERS)
        has_rejection = any(m in msg for m in REJECTION_MARKERS)

        if has_consensus and not has_rejection:
            return True, round_num

    # Check last 2 messages for implicit consensus
    if len(dialogue) >= 2:
        last_two = " ".join(d.get("message", "") for d in dialogue[-2:]).lower()
        if "@consensus" in last_two or ("accept" in last_two and "reject" not in last_two):
            return True, dialogue[-1].get("round", -1)

    return False, -1


# ============================================================
# Protocol Compliance
# ============================================================

DEFAULT_EXPECTED_ATOMS = ["@SELF", "@OTHER", "@GOAL", "@INT", "@C", "@_"]


def measure_protocol_compliance(
    text: str,
    expected_atoms: Optional[List[str]] = None,
) -> float:
    """
    Fraction of expected atoms present in text.

    Returns:
        Float 0.0–1.0
    """
    expected = expected_atoms or DEFAULT_EXPECTED_ATOMS
    found = set(find_all_atoms(text))
    if not expected:
        return 1.0
    hits = sum(1 for a in expected if a in found)
    return hits / len(expected)


# ============================================================
# Full Metrics Extraction
# ============================================================

def extract_dialogue_metrics(
    dialogue: List[Dict],
    scenario: Optional[Dict] = None,
) -> Dict:
    """
    One-call extraction of all metrics for a complete dialogue.

    Args:
        dialogue: List of {"round": int, "from": str, "message": str, ...}
        scenario: Optional scenario dict with "name", "goal_a", "goal_b"

    Returns:
        Dict with all computed metrics.
    """
    consensus_reached, consensus_round = detect_consensus(dialogue)

    # Per-message analysis
    all_atoms: Dict[str, int] = {}
    all_emergent: Set[str] = set()
    compliance_scores: List[float] = []
    total_chars = 0

    for entry in dialogue:
        msg = entry.get("message", "")
        total_chars += len(msg)

        atoms = count_protocol_atoms(msg)
        for k, v in atoms.items():
            all_atoms[k] = all_atoms.get(k, 0) + v

        emergent = detect_emergent_atoms(msg)
        all_emergent.update(emergent)

        compliance = measure_protocol_compliance(msg)
        compliance_scores.append(compliance)

    avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0

    # Goal mentions
    goal_a_mentioned = False
    goal_b_mentioned = False
    if scenario:
        full_text = " ".join(d.get("message", "") for d in dialogue).lower()
        goal_a = scenario.get("goal_a", "").lower().replace("_", " ")
        goal_b = scenario.get("goal_b", "").lower().replace("_", " ")
        goal_a_mentioned = goal_a in full_text or goal_a.replace(" ", "_") in full_text
        goal_b_mentioned = goal_b in full_text or goal_b.replace(" ", "_") in full_text

    return {
        "consensus_reached": consensus_reached,
        "consensus_round": consensus_round,
        "rounds_total": len(dialogue),
        "avg_protocol_compliance": round(avg_compliance, 3),
        "atoms_used": all_atoms,
        "unique_atoms_count": len(all_atoms),
        "emergent_atoms": sorted(all_emergent),
        "emergent_atoms_count": len(all_emergent),
        "total_chars": total_chars,
        "avg_message_length": total_chars // len(dialogue) if dialogue else 0,
        "both_goals_addressed": goal_a_mentioned and goal_b_mentioned,
    }


# ============================================================
# Triad-Specific Metrics (Group C)
# ============================================================

def detect_coalition(dialogue: List[Dict]) -> Tuple[bool, Optional[str]]:
    """
    Detect if two agents aligned against the third.

    Returns:
        (coalition_detected, coalition_description)
    """
    # Count agreement patterns between pairs
    agents = set(d.get("from", "") for d in dialogue)
    if len(agents) < 3:
        return False, None

    agents_list = sorted(agents)
    agreement_counts = {}

    for i, a1 in enumerate(agents_list):
        for a2 in agents_list[i+1:]:
            pair = f"{a1}+{a2}"
            msgs_a1 = [d["message"].lower() for d in dialogue if d.get("from") == a1]
            msgs_a2 = [d["message"].lower() for d in dialogue if d.get("from") == a2]

            # Simple heuristic: count shared vocabulary
            words_a1 = set(" ".join(msgs_a1).split())
            words_a2 = set(" ".join(msgs_a2).split())
            overlap = len(words_a1 & words_a2)
            agreement_counts[pair] = overlap

    if agreement_counts:
        max_pair = max(agreement_counts, key=agreement_counts.get)
        max_val = agreement_counts[max_pair]
        avg_val = sum(agreement_counts.values()) / len(agreement_counts)

        if max_val > avg_val * 1.5:
            return True, f"Coalition: {max_pair} (overlap: {max_val} vs avg {avg_val:.0f})"

    return False, None


def measure_mediator_effectiveness(dialogue: List[Dict], mediator_name: str) -> float:
    """
    How much of the mediator's proposal survived into the final consensus.
    Measured by word overlap between mediator's proposal and final messages.
    """
    mediator_msgs = [d["message"] for d in dialogue if d.get("from") == mediator_name]
    if not mediator_msgs:
        return 0.0

    mediator_words = set(" ".join(mediator_msgs).lower().split())
    final_msgs = [d["message"] for d in dialogue[-2:] if d.get("from") != mediator_name]
    if not final_msgs:
        return 0.0

    final_words = set(" ".join(final_msgs).lower().split())
    if not mediator_words:
        return 0.0

    overlap = len(mediator_words & final_words)
    return round(overlap / len(mediator_words), 3)


# ============================================================
# Phase 5: Answer Extraction (MCQ)
# ============================================================

def extract_answer_letter(text: str) -> Optional[str]:
    """
    Extract A/B/C/D answer letter from model response.
    Uses multiple patterns with priority ordering.

    Returns:
        Single letter 'A', 'B', 'C', or 'D', or None if not found.
    """
    if not text:
        return None

    # Priority 0 (HIGHEST): @CONSENSUS[answer=B] — explicit protocol consensus
    # This MUST be first because protocol text often mentions other options
    # like "Feudalism (A) predated..." which would false-match Pattern 5.
    m = re.search(r'@(?:CONSENSUS|RESOLUTION)\[answer=([A-D])\]', text)
    if m:
        return m.group(1).upper()

    # Pattern 1: Explicit "the answer is X" / "correct answer is X"
    m = re.search(r'(?:the\s+)?(?:correct\s+)?answer\s+is\s*[:\s]*([A-D])\b', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # Pattern 2: "I choose X" / "I select X" / "I'll go with X"
    m = re.search(r"(?:choose|select|pick|go\s+with)\s+(?:option\s+)?([A-D])\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # Pattern 3: Bold answer **B** or __B__
    m = re.search(r'\*\*([A-D])\*\*', text)
    if m:
        return m.group(1).upper()

    # Pattern 4: "Answer: B" or "Answer - B"
    m = re.search(r'answer\s*[:\-]\s*([A-D])\b', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # Pattern 5: @CONSENSUS or @RESOLUTION followed by letter (loose)
    m = re.search(r'@(?:CONSENSUS|RESOLUTION)\s*[\[:\s]*([A-D])\b', text)
    if m:
        return m.group(1).upper()

    # Pattern 6: "(B)" standalone
    m = re.search(r'\(([A-D])\)', text)
    if m:
        return m.group(1).upper()

    # Fallback: last standalone A/B/C/D on its own line
    lines = text.strip().split('\n')
    for line in reversed(lines):
        line_stripped = line.strip()
        if re.match(r'^[A-D]\.?\s*$', line_stripped):
            return line_stripped[0].upper()

    return None
