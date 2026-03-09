# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol -- Phase 15: Gated CARE-ALERT (Real-time Working Memory)
# Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
#
# Real-time divergence detection and operational alert generation.
# Monitors CRDT metrics BETWEEN dialogue rounds and fires @CARE.ALERT
# atoms ONLY when minority voice suppression is detected.
#
# Design principle: Monitor -> Detect -> Intervene
# - NO global memory injection (Phase 14 proved it harmful)
# - NO negative language ("you failed before")
# - NO trust scores or domain calibration (self-fulfilling prophecy)
# - ONLY operational instructions about the CURRENT dialogue

import re
from typing import Dict, List, Tuple, Optional, Any

from arrival.crdt_metrics import (
    extract_position_mcq,
    compute_care_optimum,
    compute_dissatisfaction,
    ANSWER_POSITION_MAP,
)

# Reverse map: float position -> letter
POSITION_LETTER_MAP = {v: k for k, v in ANSWER_POSITION_MAP.items()}


def compute_interim_metrics(
    dialogue: List[Dict], task_type: str = "mcq"
) -> Dict[str, Any]:
    """
    Compute CRDT metrics on a PARTIAL dialogue (2 or 3 messages).

    This is the core monitoring function. Called after R2 and R3
    to detect divergence before it becomes entrenched.

    Args:
        dialogue: List of {"round": int, "from": str, "message": str}
                  Must have at least 2 entries.
        task_type: "mcq" for multiple choice (default)

    Returns:
        Dict with:
        - positions_by_agent: {agent: float_position}
        - position_letters: {agent: "B"} -- MCQ letter per agent
        - divergence: bool -- do positions differ?
        - max_spread: float -- max distance between any two positions
        - interim_md: float -- meaning debt so far
        - interim_care: float -- CARE resolve so far (may be None)
        - n_agents: int -- agents with extractable positions
        - minority_agent: str or None -- agent furthest from consensus
        - minority_loss: float -- that agent's dissatisfaction
    """
    if len(dialogue) < 2:
        return _empty_interim("Need at least 2 messages")

    # Extract positions per agent
    positions_by_agent = {}
    position_letters = {}

    for entry in dialogue:
        agent = entry.get("from", "unknown")
        msg = entry.get("message", "")

        if task_type == "mcq":
            pos = extract_position_mcq(msg)
        else:
            pos = None  # open-ended not supported for alerts

        if pos is not None:
            positions_by_agent[agent] = pos
            letter = POSITION_LETTER_MAP.get(pos, "?")
            position_letters[agent] = letter

    n_agents = len(positions_by_agent)
    if n_agents < 2:
        return _empty_interim("Could not extract positions from 2+ agents")

    # Check divergence
    unique_positions = set(positions_by_agent.values())
    divergence = len(unique_positions) > 1

    # Max spread (distance between furthest positions)
    all_pos = list(positions_by_agent.values())
    max_spread = max(all_pos) - min(all_pos)

    # Compute interim CARE optimum
    positions_list = list(positions_by_agent.values())
    weights = [1.0] * len(positions_list)  # equal weights for interim
    v_hat = compute_care_optimum(positions_list, weights)

    # Compute per-agent dissatisfaction
    per_agent_loss = {}
    for agent, pos in positions_by_agent.items():
        loss = compute_dissatisfaction(pos, 1.0, v_hat)
        per_agent_loss[agent] = round(loss, 4)

    # Meaning debt = sum of all losses
    interim_md = round(sum(per_agent_loss.values()), 4)

    # Identify minority (highest loss)
    minority_agent = None
    minority_loss = 0.0
    if per_agent_loss:
        minority_agent = max(per_agent_loss, key=per_agent_loss.get)
        minority_loss = per_agent_loss[minority_agent]

    # Interim CARE resolve
    # Use the last message's position as "final"
    last_pos = None
    for entry in reversed(dialogue):
        msg = entry.get("message", "")
        if task_type == "mcq":
            last_pos = extract_position_mcq(msg)
        if last_pos is not None:
            break

    interim_care = None
    if last_pos is not None:
        max_distance = 3.0 if task_type == "mcq" else 1.0
        distance = abs(last_pos - v_hat)
        interim_care = round(max(0.0, min(1.0, 1.0 - distance / max_distance)), 4)

    return {
        "positions_by_agent": positions_by_agent,
        "position_letters": position_letters,
        "divergence": divergence,
        "max_spread": max_spread,
        "interim_md": interim_md,
        "interim_care": interim_care,
        "care_optimum": round(v_hat, 4),
        "n_agents": n_agents,
        "per_agent_loss": per_agent_loss,
        "minority_agent": minority_agent,
        "minority_loss": round(minority_loss, 4),
        "error": None,
    }


def _empty_interim(reason: str) -> Dict[str, Any]:
    """Return empty interim metrics with error reason."""
    return {
        "positions_by_agent": {},
        "position_letters": {},
        "divergence": False,
        "max_spread": 0.0,
        "interim_md": 0.0,
        "interim_care": None,
        "care_optimum": None,
        "n_agents": 0,
        "per_agent_loss": {},
        "minority_agent": None,
        "minority_loss": 0.0,
        "error": reason,
    }


def detect_divergence(
    interim: Dict[str, Any],
    md_threshold: float = 0.5,
    round_num: int = 2,
) -> Tuple[bool, str]:
    """
    Decide whether a @CARE.ALERT should fire.

    Trigger conditions (ANY of):
    1. Positions diverge AND interim MD > md_threshold
    2. After R3: 3 different positions (total disagreement)

    Do NOT trigger if:
    - Positions are identical (consensus already forming)
    - Could not extract positions (no data to act on)
    - interim has an error

    Args:
        interim: Output of compute_interim_metrics()
        md_threshold: MD must exceed this to trigger (R2: 0.5, R3: 0.8)
        round_num: Which round just completed (2 or 3)

    Returns:
        (should_fire: bool, reason: str)
    """
    if interim.get("error"):
        return False, f"no_data: {interim['error']}"

    if not interim["divergence"]:
        return False, "positions_agree"

    md = interim["interim_md"]

    # Condition 1: divergence + high MD
    if md > md_threshold:
        return True, f"divergence_high_md: MD={md:.3f} > {md_threshold}"

    # Condition 2: after R3, all 3 agents disagree
    if round_num >= 3 and interim["n_agents"] >= 3:
        unique = len(set(interim["positions_by_agent"].values()))
        if unique >= 3:
            return True, f"total_disagreement: {unique} unique positions"

    return False, f"divergence_low_md: MD={md:.3f} <= {md_threshold}"


def generate_care_alert(
    interim: Dict[str, Any],
    round_num: int,
    escalation: int = 1,
) -> str:
    """
    Generate an operational @CARE.ALERT atom for injection into the prompt.

    Design rules:
    - Operational, not moralistic ("address Beta's reasoning", not "you failed")
    - Contains ONLY current dialogue state (positions, MD)
    - NEVER contains correct answers, question text, or historical data
    - Uses @-atom format (DEUS protocol, models trained to respond)
    - Bounded: Level 1 ~200 chars, Level 2 ~300 chars

    Args:
        interim: Output of compute_interim_metrics()
        round_num: Current round number (2 or 3)
        escalation: 1 = advisory, 2 = escalated

    Returns:
        Alert text string (empty if interim has error)
    """
    if interim.get("error"):
        return ""

    letters = interim["position_letters"]
    md = interim["interim_md"]
    minority = interim.get("minority_agent")

    if escalation == 1:
        # Level 1: Advisory after R2
        # Format: who chose what, MD value, request for evidence
        pos_parts = []
        for agent, letter in letters.items():
            # Use short name for readability
            short = _short_name(agent)
            pos_parts.append(f"{short} selected ({letter})")

        positions_str = ", ".join(pos_parts)

        alert = (
            f"@CARE.ALERT: Position divergence detected. "
            f"{positions_str}. "
            f"Interim MD: {md:.2f}. "
            f"Requesting @EVIDENCE comparison before @CONSENSUS."
        )

    else:
        # Level 2: Escalated after R3
        pos_parts = []
        for agent, letter in letters.items():
            short = _short_name(agent)
            pos_parts.append(f"{short}=({letter})")

        positions_str = ", ".join(pos_parts)

        minority_short = _short_name(minority) if minority else "Unknown"

        alert = (
            f"@CARE.ALERT [ESCALATED]: Divergence persists after {round_num} rounds. "
            f"Positions: {positions_str}. "
            f"Minority: {minority_short}. MD: {md:.2f}. "
            f"Address {minority_short}'s reasoning with @EVIDENCE before @CONSENSUS."
        )

    return alert


def _short_name(agent_id: str) -> str:
    """Convert model ID to short display name."""
    SHORT_MAP = {
        "openai/gpt-4o": "Alpha",
        "deepseek/deepseek-chat": "Beta",
        "meta-llama/llama-3.3-70b-instruct": "Gamma",
    }
    if agent_id in SHORT_MAP:
        return SHORT_MAP[agent_id]
    # Fallback: use last part of model ID
    parts = agent_id.split("/")
    return parts[-1] if parts else agent_id
