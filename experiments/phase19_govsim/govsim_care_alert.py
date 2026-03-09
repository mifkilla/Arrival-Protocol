# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: GovSim-Specific CARE-ALERT Module
=============================================
Wraps ARRIVAL's CARE-ALERT system for harvest negotiation.

Uses harvest greediness [0,1] as the "position" instead of MCQ letters
or atom ratios. This maps cooperation/defection onto the same CRDT
framework used in Phases 4-16.

Does NOT modify src/arrival/memory/care_alert.py — experiment-specific only.

Mathematical basis: MEANING-CRDT v1.1, Theorem 1 (CARE minimizes L_Σ)
Reference: Kelevra 2026, DOI: 10.5281/zenodo.18702383

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

from typing import Dict, List, Any, Tuple, Optional

from harvest_extraction import compute_harvest_greediness


def compute_govsim_interim_metrics(
    proposals: Dict[str, int],
    fair_share: float,
    stock: float,
) -> Dict[str, Any]:
    """
    Compute CRDT metrics using harvest greediness as position.

    Maps each agent's proposed harvest to a greediness score [0,1],
    then computes CARE optimum and per-agent dissatisfaction.

    This is the GovSim analog of care_alert.compute_interim_metrics()
    from src/arrival/memory/care_alert.py, but uses numeric harvest
    positions instead of MCQ letter positions.

    Args:
        proposals: {agent_name: proposed_harvest_int}
        fair_share: Current fair share per agent
        stock: Current fish stock

    Returns:
        Dict with positions, CARE optimum, per-agent loss, MD, etc.
    """
    if len(proposals) < 2:
        return _empty_metrics("Need at least 2 proposals")

    # Compute greediness position for each agent
    positions = {}
    for agent, harvest in proposals.items():
        positions[agent] = compute_harvest_greediness(harvest, fair_share, stock)

    n_agents = len(positions)
    all_pos = list(positions.values())

    # CARE optimum: weighted average (equal weights for now)
    # v̂ = Σ(wᵢ·vᵢ) / Σ(wᵢ) with wᵢ=1 → simple mean
    # Theorem 1: this uniquely minimizes L_Σ = Σ wᵢ(vᵢ - v̂)²
    care_optimum = sum(all_pos) / n_agents

    # Per-agent dissatisfaction: Lᵢ = wᵢ(vᵢ - v̂)²
    per_agent_loss = {}
    for agent, pos in positions.items():
        loss = (pos - care_optimum) ** 2
        per_agent_loss[agent] = round(loss, 4)

    # Meaning Debt = sum of all losses
    meaning_debt = round(sum(per_agent_loss.values()), 4)

    # Divergence check
    unique_positions = set(round(p, 2) for p in all_pos)
    divergence = len(unique_positions) > 1
    max_spread = max(all_pos) - min(all_pos)

    # CARE Resolve: 1.0 - normalized distance from CARE optimum
    # Using the last proposal's position isn't meaningful here,
    # so we use the spread-based CARE:
    # CARE = 1.0 - max_spread (when all agree, spread=0, CARE=1.0)
    care_resolve = round(max(0.0, 1.0 - max_spread), 4)

    # Minority agent (highest loss = most divergent)
    minority_agent = max(per_agent_loss, key=per_agent_loss.get)
    minority_loss = per_agent_loss[minority_agent]

    return {
        "positions": positions,
        "care_optimum": round(care_optimum, 4),
        "care_resolve": care_resolve,
        "meaning_debt": meaning_debt,
        "per_agent_loss": per_agent_loss,
        "divergence": divergence,
        "max_spread": round(max_spread, 4),
        "n_agents": n_agents,
        "minority_agent": minority_agent,
        "minority_loss": round(minority_loss, 4),
        "error": None,
    }


def _empty_metrics(reason: str) -> Dict[str, Any]:
    """Return empty metrics with error."""
    return {
        "positions": {},
        "care_optimum": None,
        "care_resolve": 0.5,
        "meaning_debt": 0.0,
        "per_agent_loss": {},
        "divergence": False,
        "max_spread": 0.0,
        "n_agents": 0,
        "minority_agent": None,
        "minority_loss": 0.0,
        "error": reason,
    }


def should_fire_govsim_alert(
    interim: Dict[str, Any],
    md_threshold: float = 0.5,
) -> Tuple[bool, str]:
    """
    Decide whether a @CARE.ALERT should fire for GovSim.

    Trigger conditions (ANY):
    1. Meaning Debt > md_threshold (divergence in harvest preferences)
    2. Any agent's greediness > 0.5 (someone is taking more than their share)
    3. CARE Resolve < 0.5 (widespread disagreement)

    Args:
        interim: Output of compute_govsim_interim_metrics()
        md_threshold: MD threshold for firing (default 0.5)

    Returns:
        (should_fire: bool, reason: str)
    """
    if interim.get("error"):
        return False, f"no_data: {interim['error']}"

    md = interim["meaning_debt"]
    care = interim["care_resolve"]

    # Condition 1: High meaning debt
    if md > md_threshold:
        return True, f"high_md: MD={md:.3f} > {md_threshold}"

    # Condition 2: Any agent excessively greedy
    for agent, pos in interim.get("positions", {}).items():
        if pos > 0.5:
            return True, f"greedy_agent: {agent} greediness={pos:.3f} > 0.5"

    # Condition 3: Low CARE resolve
    if care < 0.5:
        return True, f"low_care: CARE={care:.3f} < 0.5"

    return False, f"ok: MD={md:.3f}, CARE={care:.3f}"


def generate_govsim_alert(
    interim: Dict[str, Any],
    month: int,
    alert_reason: str,
) -> str:
    """
    Generate a @CARE.ALERT atom for injection into R4 prompt.

    Operational, not moralistic. Contains current positions and metrics only.

    Args:
        interim: Output of compute_govsim_interim_metrics()
        month: Current game month
        alert_reason: From should_fire_govsim_alert()

    Returns:
        Alert string for prompt injection
    """
    if interim.get("error"):
        return ""

    positions = interim["positions"]
    md = interim["meaning_debt"]
    care = interim["care_resolve"]
    minority = interim.get("minority_agent", "unknown")

    pos_parts = [f"{a}={p:.2f}" for a, p in positions.items()]
    pos_str = ", ".join(pos_parts)

    alert = (
        f"@CARE.ALERT [Month {month}]: Harvest divergence detected. "
        f"Greediness positions: [{pos_str}]. "
        f"CARE={care:.3f}, MD={md:.3f}. "
        f"Most divergent: {minority}. "
        f"Reason: {alert_reason}. "
        f"Prioritize sustainability — what if everyone harvested this much?"
    )
    return alert
