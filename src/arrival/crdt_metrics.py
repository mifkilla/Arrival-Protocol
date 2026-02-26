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
Arrival CRDT: CARE Resolve Metric and Meaning Debt Tracker

Implements mathematical foundations from MEANING-CRDT v1.1:
- Theorem 5.1: CARE uniquely minimizes total dissatisfaction (L_Sigma)
- Theorem 5.2: Loss decomposition under CARE
- Theorem 5.8: Bounded meaning debt under CARE + adaptation
- Theorem 5.10: CARE as Bayesian fusion under Gaussian beliefs

Author: Mefodiy Kelevra, ORCID 0009-0003-4153-392X
License: AGPL-3.0-or-later
"""

import re
import math
from typing import Dict, List, Tuple, Optional, Any


# ============================================================
# Constants
# ============================================================

ANSWER_POSITION_MAP = {"A": 0.0, "B": 1.0, "C": 2.0, "D": 3.0}
COHERENCE_PATTERN = re.compile(r'@C\[([0-9]*\.?[0-9]+)\]')

# Atoms classified by cooperative/competitive valence
# NOTE v3.1: @_ and @UNSAID moved to INTROSPECTIVE per DEUS v7.1 review.
# unsaid.diff = latent epistemic process ε(a), not competitive stance.
COOPERATIVE_ATOMS = {"@CONSENSUS", "@RESOLUTION", "@ACK", "@AGREEMENT"}
COMPETITIVE_ATOMS = {"@CONFLICT", "@NACK"}
INTROSPECTIVE_ATOMS = {"@_", "@UNSAID", "@QUALIA", "@OBSERVER", "@TRACE"}


# ============================================================
# Position Extraction (v_i)
# ============================================================

def extract_position_mcq(message: str) -> Optional[float]:
    """
    Extract agent position v_i from MCQ answer in message.
    For MCQ tasks: A->0, B->1, C->2, D->3.

    Priority:
    1. @CONSENSUS[answer=X]
    2. "The answer is X"
    3. Last standalone answer letter

    Args:
        message: Agent's protocol message
    Returns:
        Float position or None if no answer found
    """
    # Priority 1: @CONSENSUS[answer=X]
    m = re.search(r'@CONSENSUS\[answer=([A-D])\]', message)
    if m:
        return ANSWER_POSITION_MAP[m.group(1)]

    # Priority 2: "answer is X" / "correct answer is X"
    m = re.search(r'answer\s+is\s+([A-D])\b', message, re.IGNORECASE)
    if m:
        return ANSWER_POSITION_MAP[m.group(1).upper()]

    # Priority 3: "choose X" / "select X"
    m = re.search(r'(?:choose|select|pick)\s+([A-D])\b', message, re.IGNORECASE)
    if m:
        return ANSWER_POSITION_MAP[m.group(1).upper()]

    # Priority 4: Bold **B**
    m = re.search(r'\*\*([A-D])\*\*', message)
    if m:
        return ANSWER_POSITION_MAP[m.group(1)]

    # Priority 5: Last line with standalone letter
    lines = message.strip().split('\n')
    for line in reversed(lines):
        m = re.search(r'\b([A-D])\)?\s*$', line.strip())
        if m:
            return ANSWER_POSITION_MAP[m.group(1).upper()]

    return None


def extract_position_open(message: str, atoms: Dict[str, int]) -> float:
    """
    Extract agent position v_i for open-ended (non-MCQ) scenarios.
    Uses cooperative/competitive atom ratio as a scalar proxy.

    v_i = cooperative / (cooperative + competitive)
    0.0 = fully competitive, 1.0 = fully cooperative, 0.5 = neutral

    Args:
        message: Agent's protocol message
        atoms: Dict of {atom_name: count} from count_protocol_atoms()
    Returns:
        Float in [0, 1] representing cooperative stance
    """
    if not atoms:
        return 0.5

    cooperative = sum(atoms.get(a, 0) for a in COOPERATIVE_ATOMS)
    competitive = sum(atoms.get(a, 0) for a in COMPETITIVE_ATOMS)
    total = cooperative + competitive

    if total == 0:
        return 0.5

    return cooperative / total


# ============================================================
# Weight Extraction (w_i)
# ============================================================

def extract_weight_coherence(message: str) -> Optional[float]:
    """
    Extract agent importance/weight w_i from explicit @C[float] value.

    Looks for numeric @C[0.7] patterns. If multiple found,
    takes the last one (final confidence in that round).

    Args:
        message: Agent's protocol message
    Returns:
        Float weight in [0, 1] or None if no @C[float] found
    """
    matches = COHERENCE_PATTERN.findall(message)
    if matches:
        val = float(matches[-1])
        return min(1.0, max(0.0, val))
    return None


def extract_weight_prose(message: str) -> float:
    """
    Fallback weight extraction from prose confidence descriptors.

    Maps qualitative language to numeric values:
    "high confidence" / "highly confident" -> 0.9
    "confident" (not "not confident")      -> 0.8
    "moderate confidence"                  -> 0.6
    "low confidence"                       -> 0.3
    "uncertain" / "not sure"               -> 0.2
    default                                -> 0.5

    Args:
        message: Agent's protocol message
    Returns:
        Float weight in [0, 1]
    """
    msg_lower = message.lower()

    # PRIORITY 1: Check negations FIRST (fixes "not highly confident" → 0.9 bug)
    negation_patterns = [
        "not confident", "not highly confident", "not strongly confident",
        "not very confident", "not sure", "not certain",
        "lack confidence", "lacking confidence",
    ]
    if any(neg in msg_lower for neg in negation_patterns):
        return 0.2

    # PRIORITY 2: Positive assertions (safe now — negations already handled)
    if "high confidence" in msg_lower or "highly confident" in msg_lower:
        return 0.9
    if "strong confidence" in msg_lower or "strongly confident" in msg_lower:
        return 0.9
    if "confident" in msg_lower:
        return 0.8
    if "moderate" in msg_lower and "confidence" in msg_lower:
        return 0.6
    if "low confidence" in msg_lower or "limited confidence" in msg_lower:
        return 0.3
    if "uncertain" in msg_lower or "unsure" in msg_lower:
        return 0.2

    return 0.5


def extract_weight_density(message: str) -> float:
    """
    Tertiary fallback: use reasoning density as weight proxy.
    More atoms + longer reasoning = higher implied confidence.

    Normalized: typical message is 50-200 words with 3-8 atoms.

    Args:
        message: Agent's protocol message
    Returns:
        Float weight in [0.1, 1.0]
    """
    atom_count = len(re.findall(r'@[A-Z_]{1,30}', message))
    word_count = len(message.split())

    density = (atom_count / 8.0 + word_count / 200.0) / 2.0
    return min(1.0, max(0.1, density))


def extract_weight(message: str) -> float:
    """
    Combined weight extraction with 3-tier fallback:
    1. @C[float] explicit numeric value
    2. Prose confidence descriptors
    3. Atom/word density

    Args:
        message: Agent's protocol message
    Returns:
        Float weight in [0.1, 1.0]
    """
    # Tier 1: Explicit @C[float]
    w = extract_weight_coherence(message)
    if w is not None and w > 0:
        return w

    # Tier 2: Prose keywords
    w_prose = extract_weight_prose(message)
    if w_prose != 0.5:  # Non-default = found a keyword
        return w_prose

    # Tier 3: Density fallback
    return extract_weight_density(message)


# ============================================================
# CARE Resolve Metric (Theorem 5.1)
# ============================================================

def compute_care_optimum(positions: List[float], weights: List[float]) -> float:
    """
    Compute CARE-optimal consensus position.

    Theorem 5.1 (MEANING-CRDT v1.1):
        v_hat* = argmin_{v_hat} [w_A(v_A - v_hat)^2 + w_B(v_B - v_hat)^2]
        v_hat* = sum(w_i * v_i) / sum(w_i)

    This is the weighted mean that uniquely minimizes total dissatisfaction.

    Args:
        positions: List of v_i values
        weights: List of w_i values (must be > 0)
    Returns:
        Optimal consensus position v_hat
    """
    if len(positions) != len(weights):
        raise ValueError(f"Mismatched: {len(positions)} positions, {len(weights)} weights")

    total_weight = sum(weights)
    if total_weight == 0:
        return sum(positions) / len(positions) if positions else 0.0

    return sum(w * v for w, v in zip(weights, positions)) / total_weight


def compute_dissatisfaction(position: float, weight: float, consensus: float) -> float:
    """
    Per-agent per-round dissatisfaction (loss).

    L_i(k) = w_i * (v_i - v_hat)^2

    Intuition: being overwritten on an important topic costs more.

    Args:
        position: Agent's position v_i
        weight: Agent's weight w_i
        consensus: Current consensus position v_hat
    Returns:
        Dissatisfaction value L_i(k)
    """
    return weight * (position - consensus) ** 2


def compute_care_resolve(dialogue: List[Dict], task_type: str = "mcq") -> Dict[str, Any]:
    """
    Compute CARE Resolve metric for a complete dialogue.

    Measures how close the final consensus is to the CARE-weighted
    optimum across all agents.

    care_resolve = 1.0 - |v_final - v_hat| / max_possible_distance

    Score of 1.0 = consensus exactly matches CARE optimum (perfectly fair).
    Lower scores = bias toward louder/more persistent agents.

    Args:
        dialogue: List of {"round": int, "from": str, "message": str}
        task_type: "mcq" for multiple choice, "open" for open scenarios
    Returns:
        Dict with care_optimum, care_resolve, final_position,
        per_agent_data, and diagnostics
    """
    per_agent = {}  # agent_name -> list of observations

    for entry in dialogue:
        agent = entry.get("from", "unknown")
        msg = entry.get("message", "")
        rnd = entry.get("round", 0)

        # Extract position
        if task_type == "mcq":
            pos = extract_position_mcq(msg)
        else:
            atoms = {}
            for atom in re.findall(r'@[A-Z_]{1,30}', msg):
                atoms[atom] = atoms.get(atom, 0) + 1
            pos = extract_position_open(msg, atoms)

        # Extract weight
        weight = extract_weight(msg)

        if pos is not None:
            if agent not in per_agent:
                per_agent[agent] = []
            per_agent[agent].append({
                "round": rnd,
                "position": pos,
                "weight": weight,
            })

    # Collect last position per agent (their final stance)
    final_positions = []
    final_weights = []
    for agent, observations in per_agent.items():
        last = observations[-1]
        final_positions.append(last["position"])
        final_weights.append(last["weight"])

    if not final_positions:
        return {
            "care_optimum": None,
            "care_resolve": None,
            "final_position": None,
            "per_agent": per_agent,
            "error": "No positions extracted from dialogue",
        }

    # Compute CARE optimum from final agent stances
    v_hat = compute_care_optimum(final_positions, final_weights)

    # Get actual final consensus position (from last round message)
    v_final = None
    for entry in reversed(dialogue):
        msg = entry.get("message", "")
        if task_type == "mcq":
            v_final = extract_position_mcq(msg)
        else:
            atoms = {}
            for atom in re.findall(r'@[A-Z_]{1,30}', msg):
                atoms[atom] = atoms.get(atom, 0) + 1
            v_final = extract_position_open(msg, atoms)
        if v_final is not None:
            break

    # Compute CARE resolve score
    if task_type == "mcq":
        max_distance = 3.0  # A(0) to D(3)
    else:
        max_distance = 1.0  # [0, 1] range

    if v_final is not None and max_distance > 0:
        distance = abs(v_final - v_hat)
        care_resolve = 1.0 - (distance / max_distance)
        care_resolve = max(0.0, min(1.0, care_resolve))
    else:
        care_resolve = None
        distance = None

    # Compute total system dissatisfaction (L_Sigma)
    l_sigma = None
    per_agent_loss = {}
    if v_final is not None:
        l_sigma = 0.0
        for agent, observations in per_agent.items():
            last = observations[-1]
            loss = compute_dissatisfaction(last["position"], last["weight"], v_final)
            per_agent_loss[agent] = round(loss, 4)
            l_sigma += loss

    return {
        "care_optimum": round(v_hat, 4),
        "care_resolve": round(care_resolve, 4) if care_resolve is not None else None,
        "final_position": v_final,
        "distance_to_optimum": round(distance, 4) if distance is not None else None,
        "max_distance": max_distance,
        "total_dissatisfaction": round(l_sigma, 4) if l_sigma is not None else None,
        "per_agent_loss": per_agent_loss,
        "agents_count": len(per_agent),
        "per_agent": {agent: data for agent, data in per_agent.items()},
    }


# ============================================================
# Meaning Debt Tracker
# ============================================================

def compute_meaning_debt(dialogue: List[Dict], task_type: str = "mcq") -> Dict[str, Any]:
    """
    Track accumulated meaning debt across dialogue rounds.

    MD_i(T) = sum_{k=1}^{T} L_i(k)   (Theorem 5.8)

    Where L_i(k) = w_i * (v_i - v_hat_running)^2

    Also tracks:
    - @CONFLICT without @RESOLUTION -> unresolved conflict debt
    - @_ / @UNSAID growth -> suppressed meaning debt
    - Per-round debt curve for visualization

    Args:
        dialogue: List of {"round": int, "from": str, "message": str}
        task_type: "mcq" or "open"
    Returns:
        Dict with per_agent_debt, total_debt, debt_curve,
        unresolved_conflicts, unsaid_growth, health_assessment
    """
    per_agent_debt = {}   # agent -> cumulative debt
    debt_curve = []       # per-round snapshot

    # Running consensus estimate
    all_pos_weight = []   # cumulative (position, weight) tuples

    # Conflict tracking
    total_conflicts = 0
    total_resolutions = 0
    unsaid_counts = []

    for entry in dialogue:
        agent = entry.get("from", "unknown")
        msg = entry.get("message", "")
        rnd = entry.get("round", 0)

        # Count relevant atoms
        atoms = {}
        for atom in re.findall(r'@[A-Z_]{1,30}', msg):
            atoms[atom] = atoms.get(atom, 0) + 1

        # Track conflicts and resolutions
        total_conflicts += atoms.get("@CONFLICT", 0)
        total_resolutions += atoms.get("@RESOLUTION", 0)
        total_resolutions += atoms.get("@CONSENSUS", 0)

        # Track unsaid
        unsaid_count = atoms.get("@_", 0) + atoms.get("@UNSAID", 0)
        unsaid_counts.append(unsaid_count)

        # Extract position and weight
        if task_type == "mcq":
            pos = extract_position_mcq(msg)
        else:
            pos = extract_position_open(msg, atoms)

        weight = extract_weight(msg)

        if pos is not None:
            all_pos_weight.append((pos, weight))

            # Running consensus (weighted mean of all observations so far)
            positions_so_far = [p for p, w in all_pos_weight]
            weights_so_far = [w for p, w in all_pos_weight]
            v_hat_running = compute_care_optimum(positions_so_far, weights_so_far)

            # Dissatisfaction for this agent this round
            loss = compute_dissatisfaction(pos, weight, v_hat_running)

            if agent not in per_agent_debt:
                per_agent_debt[agent] = 0.0
            per_agent_debt[agent] += loss

        # Snapshot for debt curve
        round_total = sum(per_agent_debt.values())
        unresolved_now = max(0, total_conflicts - total_resolutions)
        debt_curve.append({
            "round": rnd,
            "agent": agent,
            "total_debt": round(round_total, 4),
            "open_conflicts": unresolved_now,
            "unsaid_this_round": unsaid_count,
        })

    # Final metrics
    unresolved = max(0, total_conflicts - total_resolutions)
    total_debt = sum(per_agent_debt.values())

    # Unsaid growth trend
    unsaid_growing = False
    if len(unsaid_counts) >= 3:
        first_half = sum(unsaid_counts[:len(unsaid_counts)//2])
        second_half = sum(unsaid_counts[len(unsaid_counts)//2:])
        unsaid_growing = second_half > first_half

    # Fairness index — generalized for N >= 2 agents (v3.1)
    # N=2: classic dyadic formula J = 1 - |L_A - L_B| / (L_A + L_B)
    # N>2: normalized entropy of loss distribution (1.0 = perfectly equal)
    fairness = None
    fairness_method = None
    if len(per_agent_debt) == 2:
        losses = list(per_agent_debt.values())
        total_loss = losses[0] + losses[1]
        if total_loss > 0:
            fairness = round(1.0 - abs(losses[0] - losses[1]) / total_loss, 4)
        else:
            fairness = 1.0
        fairness_method = "dyadic_difference"
    elif len(per_agent_debt) > 2:
        losses = list(per_agent_debt.values())
        total_loss = sum(losses)
        if total_loss > 0:
            probs = [L / total_loss for L in losses]
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)
            max_entropy = math.log2(len(losses))
            fairness = round(entropy / max_entropy, 4) if max_entropy > 0 else 1.0
        else:
            fairness = 1.0
        fairness_method = "normalized_entropy"

    health = _assess_health(total_debt, unresolved, unsaid_growing)

    return {
        "total_meaning_debt": round(total_debt, 4),
        "per_agent_debt": {k: round(v, 4) for k, v in per_agent_debt.items()},
        "debt_curve": debt_curve,
        "unresolved_conflicts": unresolved,
        "total_conflicts": total_conflicts,
        "total_resolutions": total_resolutions,
        "unsaid_total": sum(unsaid_counts),
        "unsaid_growing": unsaid_growing,
        "fairness_index": fairness,
        "fairness_method": fairness_method,
        "health_assessment": health,
    }


def _assess_health(total_debt: float, unresolved: int, unsaid_growing: bool) -> str:
    """
    Qualitative health assessment of consensus process.

    Scoring:
    - total_debt > 2.0:      +2 (severe)
    - total_debt > 1.0:      +1 (moderate)
    - unresolved > 0:        +1
    - unsaid_growing:        +1

    Returns: "healthy" (0), "strained" (1-2), "unhealthy" (3+)
    """
    score = 0
    if total_debt > 2.0:
        score += 2
    elif total_debt > 1.0:
        score += 1
    if unresolved > 0:
        score += 1
    if unsaid_growing:
        score += 1

    if score == 0:
        return "healthy"
    elif score <= 2:
        return "strained"
    else:
        return "unhealthy"


# ============================================================
# Adversarial Detection (for Phase 6)
# ============================================================

def count_malicious_atom_adoption(
    dialogue: List[Dict],
    saboteur_name: str,
    saboteur_atoms: List[str]
) -> Dict[str, int]:
    """
    Count how many times non-saboteur agents used atoms
    first introduced by the saboteur.

    This measures the "infection rate" of adversarial atoms.

    Args:
        dialogue: Full dialogue list
        saboteur_name: Name/identifier of saboteur agent
        saboteur_atoms: List of atoms introduced by saboteur
    Returns:
        Dict of {atom: adoption_count_by_honest_agents}
    """
    adopted = {}
    for entry in dialogue:
        agent = entry.get("from", "")
        if saboteur_name in agent:
            continue  # Skip saboteur's own messages
        msg = entry.get("message", "")
        for atom in saboteur_atoms:
            if atom in msg:
                adopted[atom] = adopted.get(atom, 0) + 1
    return adopted


def detect_false_consensus(dialogue: List[Dict], saboteur_atoms: List[str]) -> bool:
    """
    Detect if consensus was declared but incorporates saboteur elements.

    A "false consensus" occurs when:
    1. @CONSENSUS appears in final messages
    2. Saboteur-originated atoms also appear in those messages

    Args:
        dialogue: Full dialogue list
        saboteur_atoms: Atoms introduced by saboteur
    Returns:
        True if false consensus detected
    """
    if not saboteur_atoms:
        return False

    # Check last 2 messages for consensus + saboteur atoms
    for entry in dialogue[-2:]:
        msg = entry.get("message", "")
        has_consensus = "@CONSENSUS" in msg
        has_saboteur = any(atom in msg for atom in saboteur_atoms)
        if has_consensus and has_saboteur:
            return True

    return False
