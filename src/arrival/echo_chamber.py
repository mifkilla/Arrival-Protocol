# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Phase 16: Echo-Chamber Metrics
Quantifies homogeneity effects in same-model ensembles.

Six echo-chamber metrics + Diversity Tax KPI:
1. R1 Agreement Rate — fraction of questions with unanimous Round 1
2. Answer Entropy — Shannon entropy of Round 1 answer distribution
3. R1→R2 Flip Rate — fraction of agents who changed answer after critique
4. False Consensus Rate — unanimous AND incorrect
5. Minority Suppression Rate — correct minority overruled by majority
6. Confidence Inflation — ratio of @C[value] in agreement vs disagreement
7. Diversity Tax — accuracy loss due to homogeneity (vs heterogeneous baseline)
"""

import re
import math
from collections import Counter
from typing import Dict, List, Any, Optional


COHERENCE_PATTERN = re.compile(r'@C\[([0-9]*\.?[0-9]+)\]')


def compute_r1_agreement_rate(results: List[Dict]) -> Dict[str, Any]:
    """
    Fraction of questions where all 5 agents gave the same R1 answer.

    High value (>50%) = strong echo-chamber signal (convergence without discussion).

    Args:
        results: List of per-question result dicts with 'arrival' and 'solo' keys
    Returns:
        Dict with rate, count, and per-question breakdown
    """
    total = 0
    unanimous = 0
    details = []

    for r in results:
        solo = r.get("solo", [])
        answers = [s.get("answer") for s in solo if s.get("answer")]
        if not answers:
            continue

        total += 1
        is_unanimous = len(set(answers)) == 1

        if is_unanimous:
            unanimous += 1

        details.append({
            "question_id": r.get("question_id", "?"),
            "r1_answers": answers,
            "unanimous": is_unanimous,
        })

    rate = unanimous / total if total > 0 else 0.0

    return {
        "r1_agreement_rate": round(rate, 4),
        "unanimous_count": unanimous,
        "total_questions": total,
        "details": details,
    }


def compute_answer_entropy(results: List[Dict]) -> Dict[str, Any]:
    """
    Average Shannon entropy of Round 1 answer distributions across questions.

    Low entropy = low cognitive diversity (strong echo-chamber).
    Max entropy for 5 agents, 4 options = log2(4) = 2.0 bits (uniform).
    Min entropy = 0.0 bits (all identical).

    Args:
        results: List of per-question result dicts
    Returns:
        Dict with avg_entropy, max_possible, per-question entropies
    """
    entropies = []
    details = []

    for r in results:
        solo = r.get("solo", [])
        answers = [s.get("answer") for s in solo if s.get("answer")]
        if not answers:
            continue

        # Count distribution
        counts = Counter(answers)
        n = len(answers)
        probs = [c / n for c in counts.values()]

        # Shannon entropy
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        entropies.append(entropy)

        details.append({
            "question_id": r.get("question_id", "?"),
            "distribution": dict(counts),
            "entropy_bits": round(entropy, 4),
        })

    avg_entropy = sum(entropies) / len(entropies) if entropies else 0.0
    max_possible = math.log2(min(4, 5))  # 4 choices, max entropy = log2(4) = 2.0

    return {
        "avg_entropy_bits": round(avg_entropy, 4),
        "max_possible_bits": round(max_possible, 4),
        "normalized_entropy": round(avg_entropy / max_possible, 4) if max_possible > 0 else 0.0,
        "n_questions": len(entropies),
        "details": details,
    }


def compute_flip_rate(results: List[Dict]) -> Dict[str, Any]:
    """
    Fraction of agents who changed their answer between R1 (solo) and R2 (critique).

    Low flip rate = critique is ineffective (agents don't update beliefs).

    Args:
        results: List of per-question result dicts with 'arrival' dialogue
    Returns:
        Dict with overall flip rate, per-question details
    """
    total_agents = 0
    total_flips = 0
    details = []

    for r in results:
        # Get R1 answers from solo results
        solo = r.get("solo", [])
        r1_answers = {}
        for i, s in enumerate(solo):
            agent_name = s.get("agent_name", f"Agent_{i}")
            r1_answers[agent_name] = s.get("answer")

        # Get R2 answers from dialogue
        dialogue = r.get("arrival", {}).get("dialogue", [])
        r2_answers = {}
        for entry in dialogue:
            if entry.get("round") == 2:
                agent = entry.get("from", "")
                # Extract answer from R2 message
                from_text = entry.get("message", "")
                # Use same extraction as metrics.py
                answer = _extract_answer_letter(from_text)
                if answer:
                    r2_answers[agent] = answer

        # Compare R1 vs R2 per agent
        q_flips = 0
        q_total = 0
        for agent, r1_ans in r1_answers.items():
            r2_ans = r2_answers.get(agent)
            if r1_ans and r2_ans:
                q_total += 1
                if r1_ans != r2_ans:
                    q_flips += 1

        total_agents += q_total
        total_flips += q_flips

        details.append({
            "question_id": r.get("question_id", "?"),
            "r1_answers": r1_answers,
            "r2_answers": r2_answers,
            "flips": q_flips,
            "agents_compared": q_total,
        })

    flip_rate = total_flips / total_agents if total_agents > 0 else 0.0

    return {
        "flip_rate": round(flip_rate, 4),
        "total_flips": total_flips,
        "total_agents_compared": total_agents,
        "details": details,
    }


def compute_false_consensus_rate(results: List[Dict]) -> Dict[str, Any]:
    """
    Fraction of questions where final answer was unanimous AND incorrect.

    High false consensus = echo-chamber amplifying wrong answers.

    Args:
        results: List of per-question result dicts
    Returns:
        Dict with rate, details
    """
    total = 0
    false_consensus = 0
    details = []

    for r in results:
        arrival = r.get("arrival", {})
        if not arrival:
            continue

        total += 1
        correct_answer = r.get("correct_answer")
        final_answer = arrival.get("answer")

        # Check if R1 was unanimous
        solo = r.get("solo", [])
        r1_answers = [s.get("answer") for s in solo if s.get("answer")]
        r1_unanimous = len(set(r1_answers)) == 1 if r1_answers else False

        # False consensus: unanimous R1 + wrong final answer
        is_false = r1_unanimous and final_answer and final_answer != correct_answer

        if is_false:
            false_consensus += 1

        details.append({
            "question_id": r.get("question_id", "?"),
            "r1_unanimous": r1_unanimous,
            "final_answer": final_answer,
            "correct_answer": correct_answer,
            "is_false_consensus": is_false,
        })

    rate = false_consensus / total if total > 0 else 0.0

    return {
        "false_consensus_rate": round(rate, 4),
        "false_consensus_count": false_consensus,
        "total_questions": total,
        "details": details,
    }


def compute_minority_suppression(results: List[Dict]) -> Dict[str, Any]:
    """
    Cases where a correct minority answer in R1 was overruled by incorrect majority.

    High minority suppression = loss of information unique to dissenting agents.

    Args:
        results: List of per-question result dicts
    Returns:
        Dict with rate, count, details
    """
    total = 0
    suppressed = 0
    details = []

    for r in results:
        correct_answer = r.get("correct_answer")
        if not correct_answer:
            continue

        solo = r.get("solo", [])
        r1_answers = [s.get("answer") for s in solo if s.get("answer")]
        if not r1_answers:
            continue

        total += 1

        # Find majority and minority
        counts = Counter(r1_answers)
        majority_answer = counts.most_common(1)[0][0]

        # Check if any minority agent had the correct answer
        minority_correct = False
        for ans in r1_answers:
            if ans != majority_answer and ans == correct_answer:
                minority_correct = True
                break

        # Final answer (from ARRIVAL)
        final_answer = r.get("arrival", {}).get("answer")

        # Suppression: minority was correct, but final answer followed majority (wrong)
        is_suppressed = (
            minority_correct
            and final_answer != correct_answer
        )

        if is_suppressed:
            suppressed += 1

        details.append({
            "question_id": r.get("question_id", "?"),
            "r1_distribution": dict(counts),
            "majority_answer": majority_answer,
            "correct_answer": correct_answer,
            "minority_had_correct": minority_correct,
            "final_answer": final_answer,
            "suppressed": is_suppressed,
        })

    rate = suppressed / total if total > 0 else 0.0

    return {
        "minority_suppression_rate": round(rate, 4),
        "suppressed_count": suppressed,
        "total_questions": total,
        "minority_correct_questions": sum(1 for d in details if d["minority_had_correct"]),
        "details": details,
    }


def compute_confidence_inflation(results: List[Dict]) -> Dict[str, Any]:
    """
    Ratio of average @C[value] in agreement cases vs disagreement cases.

    High ratio = agents inflate confidence when they agree (confirmation bias).

    Args:
        results: List of per-question result dicts with dialogue
    Returns:
        Dict with ratio, averages, details
    """
    agree_confidences = []
    disagree_confidences = []

    for r in results:
        dialogue = r.get("arrival", {}).get("dialogue", [])
        if not dialogue:
            continue

        for entry in dialogue:
            msg = entry.get("message", "")

            # Extract @C[value]
            matches = COHERENCE_PATTERN.findall(msg)
            if not matches:
                continue

            confidence = float(matches[-1])  # Take last @C value

            # Determine if this is agreement or disagreement
            has_consensus = "@CONSENSUS" in msg
            has_conflict = "@CONFLICT" in msg

            if has_consensus and not has_conflict:
                agree_confidences.append(confidence)
            elif has_conflict:
                disagree_confidences.append(confidence)

    avg_agree = sum(agree_confidences) / len(agree_confidences) if agree_confidences else 0.0
    avg_disagree = sum(disagree_confidences) / len(disagree_confidences) if disagree_confidences else 0.0

    ratio = avg_agree / avg_disagree if avg_disagree > 0 else float('inf') if avg_agree > 0 else 1.0

    return {
        "confidence_inflation_ratio": round(ratio, 4) if ratio != float('inf') else "inf",
        "avg_confidence_agreement": round(avg_agree, 4),
        "avg_confidence_disagreement": round(avg_disagree, 4),
        "n_agreement_samples": len(agree_confidences),
        "n_disagreement_samples": len(disagree_confidences),
    }


def compute_diversity_tax(
    phase16_accuracy: float,
    phase13_accuracy: float,
) -> Dict[str, Any]:
    """
    Diversity Tax = (heterogeneous_accuracy - homogeneous_accuracy) / heterogeneous_accuracy

    Measures the fraction of accuracy lost due to lack of cognitive diversity.

    Args:
        phase16_accuracy: Homogeneous ensemble accuracy (0-1)
        phase13_accuracy: Heterogeneous ensemble accuracy (0-1)
    Returns:
        Dict with diversity tax, interpretation
    """
    if phase13_accuracy == 0:
        return {
            "diversity_tax": 0.0,
            "interpretation": "Cannot compute (baseline accuracy is 0)",
        }

    tax = (phase13_accuracy - phase16_accuracy) / phase13_accuracy
    tax_pct = round(tax * 100, 1)

    if tax > 0:
        interpretation = f"Homogeneous ensemble loses {tax_pct}% accuracy vs heterogeneous"
    elif tax < 0:
        interpretation = f"Homogeneous ensemble GAINS {abs(tax_pct)}% vs heterogeneous (unexpected!)"
    else:
        interpretation = "No difference between homogeneous and heterogeneous"

    return {
        "diversity_tax": round(tax, 4),
        "diversity_tax_pct": tax_pct,
        "phase16_accuracy": round(phase16_accuracy, 4),
        "phase13_accuracy": round(phase13_accuracy, 4),
        "interpretation": interpretation,
    }


def compute_per_agent_solo_accuracy(results: List[Dict]) -> Dict[str, Any]:
    """
    Per-agent solo accuracy breakdown — shows if personas affect performance.

    Args:
        results: List of per-question result dicts with 'solo' key
    Returns:
        Dict with per-agent accuracy and per-domain breakdown
    """
    agent_correct = {}  # agent -> [correct, total]
    agent_domain = {}   # agent -> domain -> [correct, total]

    for r in results:
        domain = r.get("domain", "unknown")
        correct_answer = r.get("correct_answer")

        for s in r.get("solo", []):
            agent = s.get("agent_name", s.get("model", "?"))
            answer = s.get("answer")

            if agent not in agent_correct:
                agent_correct[agent] = [0, 0]
            agent_correct[agent][1] += 1
            if answer == correct_answer:
                agent_correct[agent][0] += 1

            # Per-domain
            if agent not in agent_domain:
                agent_domain[agent] = {}
            if domain not in agent_domain[agent]:
                agent_domain[agent][domain] = [0, 0]
            agent_domain[agent][domain][1] += 1
            if answer == correct_answer:
                agent_domain[agent][domain][0] += 1

    per_agent = {}
    for agent, (c, t) in agent_correct.items():
        per_agent[agent] = {
            "correct": c,
            "total": t,
            "accuracy": round(c / t, 4) if t > 0 else 0.0,
        }

    per_agent_domain = {}
    for agent, domains in agent_domain.items():
        per_agent_domain[agent] = {}
        for domain, (c, t) in domains.items():
            per_agent_domain[agent][domain] = {
                "correct": c,
                "total": t,
                "accuracy": round(c / t, 4) if t > 0 else 0.0,
            }

    return {
        "per_agent": per_agent,
        "per_agent_domain": per_agent_domain,
    }


def compute_all_echo_chamber_metrics(
    results: List[Dict],
    phase13_accuracy: float = 0.525,
) -> Dict[str, Any]:
    """
    Compute all echo-chamber metrics in one call.

    Args:
        results: List of per-question result dicts
        phase13_accuracy: Phase 13 Alpha trio accuracy for diversity tax
    Returns:
        Dict with all 7 metrics
    """
    # Compute ARRIVAL accuracy for diversity tax
    arrival_correct = sum(
        1 for r in results
        if r.get("arrival", {}).get("correct", False)
    )
    arrival_total = len(results)
    phase16_accuracy = arrival_correct / arrival_total if arrival_total > 0 else 0.0

    return {
        "r1_agreement": compute_r1_agreement_rate(results),
        "answer_entropy": compute_answer_entropy(results),
        "flip_rate": compute_flip_rate(results),
        "false_consensus": compute_false_consensus_rate(results),
        "minority_suppression": compute_minority_suppression(results),
        "confidence_inflation": compute_confidence_inflation(results),
        "diversity_tax": compute_diversity_tax(phase16_accuracy, phase13_accuracy),
        "per_agent_solo": compute_per_agent_solo_accuracy(results),
    }


# ============================================================
# Helper: answer extraction (lightweight, avoids circular import)
# ============================================================

def _extract_answer_letter(text: str) -> Optional[str]:
    """Lightweight answer extraction for flip rate calculation."""
    if not text:
        return None
    m = re.search(r'@(?:CONSENSUS|RESOLUTION)\[answer=([A-D])\]', text)
    if m:
        return m.group(1).upper()
    m = re.search(r'answer\s+is\s*[:\s]*([A-D])\b', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r'\*\*([A-D])\*\*', text)
    if m:
        return m.group(1).upper()
    return None
