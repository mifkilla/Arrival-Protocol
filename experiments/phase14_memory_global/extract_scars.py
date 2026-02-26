#!/usr/bin/env python3
"""
Phase 14 Step 1: Extract Cognitive Scars from Phase 13 Alpha Results
=====================================================================
Parses Phase 13 Alpha trio results, computes a composite failure score
for each question, selects the top-5 worst, and extracts structural
"cognitive scars" — data about WHY ARRIVAL failed, without leaking answers.

DATA LEAKAGE GUARD:
- NEVER stores correct answers, answer letters, question text, or choices
- Only stores: question_id, domain, CRDT metrics, atom counts, structural dynamics

Usage:
    python extract_scars.py              # Extract and save scars
    python extract_scars.py --verbose    # Show detailed per-question analysis

Output:
    results/phase14_scars.json

Author: Mefodiy Kelevra
ORCID: 0009-0003-4153-392X
"""

import sys
import os
import json
import argparse

# Fix Windows cp1251 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')
from collections import Counter
from datetime import datetime, timezone

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PHASE14_BASELINE_FILE, PHASE14_SCARS_FILE, RESULTS_DIR
from metrics import find_all_atoms


def load_baseline() -> dict:
    """Load Phase 13 results JSON."""
    path = str(PHASE14_BASELINE_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Phase 13 baseline not found: {path}\n"
            f"Copy from E:\\Arrival CRDT\\results\\phase_13\\phase13_results_*.json"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_alpha_results(baseline: dict) -> list:
    """Extract Alpha trio per-question results from Phase 13."""
    results = baseline.get("results", {})

    # Phase 13 stores results as dict with trio names as keys
    if isinstance(results, dict):
        alpha = results.get("alpha", [])
    elif isinstance(results, list):
        # Fallback: filter by trio_name
        alpha = [r for r in results if r.get("trio_name") == "alpha"]
    else:
        raise ValueError(f"Unexpected results format: {type(results)}")

    if not alpha:
        raise ValueError("No Alpha trio results found in baseline")

    print(f"  Found {len(alpha)} Alpha trio questions")
    return alpha


def compute_composite_score(care_resolve: float, meaning_debt: float) -> float:
    """
    Composite failure score: higher = worse.
    rank = (1 - care_resolve) + meaning_debt / 5.0
    """
    return (1.0 - care_resolve) + (meaning_debt / 5.0)


def classify_round_dynamics(crdt_data: dict) -> str:
    """
    Classify how the dialogue evolved:
    - early_disagreement: Different answers in R1, converged by R4
    - late_flip: Consensus changed after R2
    - persistent_minority: One agent consistently overridden
    - full_agreement: All agents agreed from start
    """
    care = crdt_data.get("care_resolve", {})
    per_agent = care.get("per_agent", {})

    if not per_agent:
        return "unknown"

    # Get per-round positions for each agent
    agents = list(per_agent.keys())
    if len(agents) < 2:
        return "unknown"

    # Collect round-1 positions
    r1_positions = []
    for agent in agents:
        rounds = per_agent[agent]
        if rounds and len(rounds) > 0:
            r1_positions.append(rounds[0].get("position"))

    # Collect final positions
    final_positions = []
    for agent in agents:
        rounds = per_agent[agent]
        if rounds and len(rounds) > 0:
            final_positions.append(rounds[-1].get("position"))

    # Check agreement patterns
    r1_positions_clean = [p for p in r1_positions if p is not None]
    final_positions_clean = [p for p in final_positions if p is not None]

    if not r1_positions_clean or not final_positions_clean:
        return "unknown"

    r1_unanimous = len(set(r1_positions_clean)) == 1
    final_unanimous = len(set(final_positions_clean)) == 1

    if r1_unanimous and final_unanimous:
        return "full_agreement"
    elif not r1_unanimous and final_unanimous:
        return "early_disagreement"
    elif r1_unanimous and not final_unanimous:
        return "late_flip"
    else:
        return "persistent_minority"


def extract_scars(baseline: dict, verbose: bool = False) -> dict:
    """
    Main extraction pipeline.

    Returns:
        {
            "seen_question_ids": [...],
            "all_scores": [...],  # All 40 questions with composite scores
            "scars": [...]        # Top-5 worst questions with full analysis
        }
    """
    alpha_results = extract_alpha_results(baseline)

    # ================================================================
    # Step 1: Compute composite score for ALL questions
    # ================================================================
    all_scores = []
    for r in alpha_results:
        crdt = r.get("crdt", {})
        care = crdt.get("care_resolve", {})
        debt = crdt.get("meaning_debt", {})

        care_val = care.get("care_resolve")
        debt_val = debt.get("total_meaning_debt", 0)

        # Handle None values
        if care_val is None:
            care_val = 0.5  # Neutral default
        if debt_val is None:
            debt_val = 0.0

        composite = compute_composite_score(care_val, debt_val)

        all_scores.append({
            "question_id": r["question_id"],
            "domain": r["domain"],
            "composite_score": round(composite, 4),
            "care_resolve": round(care_val, 4),
            "meaning_debt": round(debt_val, 4),
            "health_assessment": debt.get("health_assessment", "unknown"),
            "arrival_correct": r.get("arrival", {}).get("correct", False),
        })

    # Sort by composite score descending (worst first)
    all_scores.sort(key=lambda x: x["composite_score"], reverse=True)

    if verbose:
        print(f"\n  {'='*70}")
        print(f"  ALL QUESTIONS RANKED BY COMPOSITE FAILURE SCORE")
        print(f"  {'='*70}")
        for i, s in enumerate(all_scores):
            marker = " *** SEEN" if i < 5 else ""
            correct = "OK" if s["arrival_correct"] else "FAIL"
            print(f"  {i+1:2d}. {s['question_id']} [{s['domain']:15s}] "
                  f"score={s['composite_score']:.3f} "
                  f"CARE={s['care_resolve']:.3f} MD={s['meaning_debt']:.3f} "
                  f"[{s['health_assessment']}] {correct}{marker}")

    # ================================================================
    # Step 2: Select Top-5 as SEEN_QUESTIONS
    # ================================================================
    seen = all_scores[:5]
    seen_ids = [s["question_id"] for s in seen]

    print(f"\n  SEEN QUESTIONS (excluded from main statistics):")
    for s in seen:
        print(f"    {s['question_id']} [{s['domain']}] "
              f"composite={s['composite_score']:.3f}")

    # ================================================================
    # Step 3: Extract detailed scars for top-5
    # ================================================================
    scars = []
    for score_entry in seen:
        qid = score_entry["question_id"]

        # Find the full result for this question
        result = next(r for r in alpha_results if r["question_id"] == qid)
        crdt = result.get("crdt", {})
        care = crdt.get("care_resolve", {})
        debt = crdt.get("meaning_debt", {})
        arrival = result.get("arrival", {})

        # Per-agent loss
        per_agent_loss = care.get("per_agent_loss", {})

        # Minority voice (agent with highest loss)
        if per_agent_loss:
            minority_voice = max(per_agent_loss, key=per_agent_loss.get)
            minority_loss = per_agent_loss[minority_voice]
        else:
            minority_voice = "unknown"
            minority_loss = 0.0

        # Round dynamics classification
        round_dynamics = classify_round_dynamics(crdt)

        # Atom counts from transcript (structural info only)
        dialogue = arrival.get("dialogue", [])
        all_atoms_in_dialogue = []
        for msg in dialogue:
            all_atoms_in_dialogue.extend(find_all_atoms(msg.get("message", "")))
        atom_counts = dict(Counter(all_atoms_in_dialogue))

        # Unresolved conflicts
        unresolved = debt.get("unresolved_conflicts", 0)

        # Fairness
        fairness_index = debt.get("fairness_index", None)

        scar = {
            "question_id": qid,
            "domain": score_entry["domain"],
            "composite_score": score_entry["composite_score"],
            "care_resolve": score_entry["care_resolve"],
            "meaning_debt": score_entry["meaning_debt"],
            "health_assessment": score_entry["health_assessment"],
            "arrival_correct": score_entry["arrival_correct"],
            "per_agent_loss": {k: round(v, 4) for k, v in per_agent_loss.items()},
            "minority_voice": minority_voice,
            "minority_loss": round(minority_loss, 4),
            "round_dynamics": round_dynamics,
            "atom_count": atom_counts,
            "unresolved_conflicts": unresolved,
            "fairness_index": round(fairness_index, 4) if fairness_index is not None else None,
            "total_dissatisfaction": care.get("total_dissatisfaction", 0),
            "per_agent_debt": debt.get("per_agent_debt", {}),
        }

        # === DATA LEAKAGE AUDIT ===
        # Verify NO answer information leaked into scar
        assert "correct_answer" not in scar, f"DATA LEAKAGE: correct_answer in scar for {qid}"
        assert "question" not in scar, f"DATA LEAKAGE: question text in scar for {qid}"
        assert "choices" not in scar, f"DATA LEAKAGE: choices in scar for {qid}"

        scars.append(scar)

        if verbose:
            print(f"\n  SCAR: {qid} [{score_entry['domain']}]")
            print(f"    CARE Resolve: {score_entry['care_resolve']:.3f}")
            print(f"    Meaning Debt: {score_entry['meaning_debt']:.3f}")
            print(f"    Health: {score_entry['health_assessment']}")
            print(f"    Minority: {minority_voice} (loss={minority_loss:.3f})")
            print(f"    Dynamics: {round_dynamics}")
            print(f"    Unresolved conflicts: {unresolved}")
            print(f"    Key atoms: {dict(Counter(all_atoms_in_dialogue).most_common(5))}")
            print(f"    Arrival correct: {score_entry['arrival_correct']}")

    return {
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "baseline_file": str(PHASE14_BASELINE_FILE),
        "total_questions": len(alpha_results),
        "n_seen": len(seen_ids),
        "n_unseen": len(alpha_results) - len(seen_ids),
        "seen_question_ids": seen_ids,
        "all_scores": all_scores,
        "scars": scars,
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 14: Extract Cognitive Scars")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"  PHASE 14 — Step 1: Extract Cognitive Scars from Phase 13")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*70}")

    # Load baseline
    print(f"\n  Loading Phase 13 baseline: {PHASE14_BASELINE_FILE}")
    baseline = load_baseline()

    # Extract scars
    result = extract_scars(baseline, verbose=args.verbose)

    # Save
    output_path = str(PHASE14_SCARS_FILE)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n  Saved: {output_path}")
    print(f"  Seen questions: {result['seen_question_ids']}")
    print(f"  Unseen: {result['n_unseen']} questions for comparison")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
