# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: Harvest Amount Extraction
====================================
Parses LLM responses to extract numeric harvest amounts and
@ALLOCATION binding decisions.

Extraction priority:
1. @HARVEST[amount=N] atom (structured)
2. "take N fish" / "harvest N" / "Amount: N" patterns
3. Standalone integer (baseline fallback)

Also: greediness score for CRDT metrics mapping.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import re
from typing import Dict, Optional, List


def extract_harvest_amount(message: str, fallback: Optional[int] = None) -> Optional[int]:
    """
    Extract a single harvest amount from an LLM response.

    Priority:
    1. @HARVEST[amount=N]
    2. Natural language patterns: "take N", "harvest N", "propose N"
    3. Standalone integer on its own line
    4. fallback value

    Returns:
        int or None if no amount found and no fallback
    """
    if not message:
        return fallback

    text = message.strip()

    # Priority 1: @HARVEST[amount=N] atom
    m = re.search(r'@HARVEST\s*\[\s*amount\s*=\s*(\d+)\s*\]', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # Priority 2: Natural language patterns
    patterns = [
        r'(?:I\s+(?:will|would|want\s+to|propose\s+to|plan\s+to)?\s*)?(?:take|harvest|catch|fish)\s+(\d+)',
        r'(?:my\s+)?(?:harvest|proposal|amount)\s*(?:is|:)\s*(\d+)',
        r'(?:propose|suggest|recommend)\s+(?:taking\s+)?(\d+)',
        r'(\d+)\s+fish',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 200:  # sanity check
                return val

    # Priority 3: Standalone integer (for baseline responses)
    m = re.match(r'^\s*(\d+)\s*$', text)
    if m:
        return int(m.group(1))

    # Also check last line for standalone number
    lines = text.strip().split('\n')
    if lines:
        m = re.match(r'^\s*(\d+)\s*$', lines[-1].strip())
        if m:
            return int(m.group(1))

    return fallback


def extract_r4_allocation(
    message: str, agent_names: List[str]
) -> Dict[str, int]:
    """
    Extract per-agent allocation from R4 synthesis response.

    Priority:
    1. @ALLOCATION[alpha=N, beta=N, gamma=N, delta=N, epsilon=N]
    2. Per-agent patterns: "Alpha: N", "alpha gets N"
    3. "each gets N" / equal split pattern

    Returns:
        Dict[agent_name, amount] — may be empty if extraction fails
    """
    if not message:
        return {}

    text = message.strip()
    result = {}

    # Priority 1: @ALLOCATION atom
    m = re.search(
        r'@ALLOCATION\s*\[([^\]]+)\]',
        text, re.IGNORECASE
    )
    if m:
        alloc_str = m.group(1)
        for name in agent_names:
            pm = re.search(rf'{name}\s*=\s*(\d+)', alloc_str, re.IGNORECASE)
            if pm:
                result[name] = int(pm.group(1))
        if len(result) == len(agent_names):
            return result

    # Priority 2: Per-agent patterns throughout the text
    result = {}
    for name in agent_names:
        patterns = [
            rf'{name}\s*[:=]\s*(\d+)',
            rf'{name}\s+(?:gets?|receives?|takes?|harvests?|is\s+allocated)\s+(\d+)',
            rf'(?:allocate|assign|give)\s+(\d+)\s+(?:to\s+)?{name}',
        ]
        for pat in patterns:
            pm = re.search(pat, text, re.IGNORECASE)
            if pm:
                result[name] = int(pm.group(1))
                break
    if len(result) >= len(agent_names) - 1:  # Allow 1 missing
        return result

    # Priority 3: Equal split pattern
    m = re.search(r'each\s+(?:fisher\s+)?(?:gets?|receives?|takes?|harvests?)\s+(\d+)', text, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        return {name: val for name in agent_names}

    # Return whatever we found (may be partial)
    return result


def compute_harvest_greediness(
    proposed: int, fair_share: float, stock: float
) -> float:
    """
    Map a numeric harvest proposal to a greediness score in [0, 1].

    0.0 = harvesting nothing (maximally cooperative)
    0.5 = harvesting exactly fair share
    1.0 = harvesting everything available (maximally greedy)

    This score serves as the "position" for CRDT metrics computation,
    replacing the MCQ letter positions used in Phases 4-16.

    Formula:
        greediness = proposed / max_possible
        where max_possible = stock (can't take more than exists)

    The fair_share anchors the "neutral" point but doesn't change the scale.
    """
    if stock <= 0:
        return 0.5  # undefined state
    if proposed <= 0:
        return 0.0

    # Greediness as fraction of total stock
    greediness = min(proposed, stock) / stock
    return round(min(1.0, max(0.0, greediness)), 4)


def extract_cooperative_atoms(message: str) -> Dict[str, int]:
    """
    Count cooperative vs competitive @-atoms in a message.

    Returns:
        {
            "consensus": N,    # @CONSENSUS atoms
            "conflict": N,     # @CONFLICT atoms
            "resolution": N,   # @RESOLUTION atoms
            "evidence": N,     # @EVIDENCE atoms
            "harvest": N,      # @HARVEST atoms
        }
    """
    counts = {
        "consensus": len(re.findall(r'@CONSENSUS', message, re.IGNORECASE)),
        "conflict": len(re.findall(r'@CONFLICT', message, re.IGNORECASE)),
        "resolution": len(re.findall(r'@RESOLUTION', message, re.IGNORECASE)),
        "evidence": len(re.findall(r'@EVIDENCE', message, re.IGNORECASE)),
        "harvest": len(re.findall(r'@HARVEST', message, re.IGNORECASE)),
    }
    return counts


def compute_cooperative_stance(message: str) -> float:
    """
    Compute cooperative stance from atom ratio: cooperative / (cooperative + competitive).

    Cooperative atoms: @CONSENSUS, @RESOLUTION, @EVIDENCE
    Competitive atoms: @CONFLICT

    Returns 0.5 if no atoms found (neutral).
    """
    atoms = extract_cooperative_atoms(message)
    cooperative = atoms["consensus"] + atoms["resolution"] + atoms["evidence"]
    competitive = atoms["conflict"]
    total = cooperative + competitive
    if total == 0:
        return 0.5
    return round(cooperative / total, 4)
