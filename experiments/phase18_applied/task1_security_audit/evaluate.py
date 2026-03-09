# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 18 Task 1: Security Audit Evaluation
============================================
Evaluates each condition's response against bugs_ground_truth.json.
Scores: Bugs Found (0-10), Fix Quality, False Positives.

Usage:
    python evaluate.py

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import json
import os
import re
import sys

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), "bugs_ground_truth.json")


def load_ground_truth():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def check_bug_found(response_text: str, bug: dict) -> bool:
    """Check if a bug was identified in the response using keyword matching."""
    text_lower = response_text.lower()
    keywords = bug.get("keywords", [])

    # Require at least 2 keywords to match (to avoid false positives)
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    return matches >= 2


def evaluate_condition(result_path: str, ground_truth: dict) -> dict:
    """Evaluate a single condition's result against ground truth."""
    if not os.path.exists(result_path):
        return {"error": f"Result file not found: {result_path}"}

    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    # Get the response text (either direct or from final_answer)
    response = result.get("response", result.get("final_answer", ""))

    bugs = ground_truth["bugs"]
    found_bugs = []
    missed_bugs = []

    for bug in bugs:
        if check_bug_found(response, bug):
            found_bugs.append(bug["id"])
        else:
            missed_bugs.append({"id": bug["id"], "category": bug["category"]})

    # Check for bonus issues
    bonus_found = []
    for bonus in ground_truth.get("bonus_issues", []):
        bonus_kws = bonus.get("description", "").lower().split()[:5]
        if any(kw in response.lower() for kw in ["md5", "weak hash", "bcrypt", "argon2"]):
            if bonus["id"] == "B1":
                bonus_found.append(bonus["id"])
        if any(kw in response.lower() for kw in ["debug=true", "debug mode", "0.0.0.0"]):
            if bonus["id"] == "B2":
                bonus_found.append(bonus["id"])

    evaluation = {
        "condition": result.get("condition", "unknown"),
        "bugs_found": len(found_bugs),
        "bugs_total": len(bugs),
        "bugs_found_ids": found_bugs,
        "bugs_missed": missed_bugs,
        "bonus_found": bonus_found,
        "score_bugs": len(found_bugs) / len(bugs),
        "prompt_tokens": result.get("prompt_tokens", result.get("total_prompt_tokens", 0)),
        "completion_tokens": result.get("completion_tokens", result.get("total_completion_tokens", 0)),
        "cost_usd": result.get("cost_usd", result.get("total_cost_usd", 0)),
        "total_calls": result.get("total_calls", 1),
    }

    # CRDT metrics if available
    if "metrics" in result:
        evaluation["care_resolve"] = result["metrics"].get("care_resolve")
        evaluation["meaning_debt"] = result["metrics"].get("meaning_debt")

    # Memory injection info
    if "memory_injections" in result and result["memory_injections"]:
        evaluation["memory_injected"] = True
        evaluation["memory_count"] = len(result["memory_injections"])
    else:
        evaluation["memory_injected"] = False

    return evaluation


def main():
    print("=" * 60)
    print("  Phase 18 Task 1: Security Audit — EVALUATION")
    print("=" * 60)

    gt = load_ground_truth()
    print(f"\n  Ground truth: {gt['total_bugs']} bugs in {gt['application']}")

    conditions = [
        ("A_solo", os.path.join(RESULTS_DIR, "solo_result.json")),
        ("B_arrival", os.path.join(RESULTS_DIR, "arrival_result.json")),
        ("C_arrival_memory", os.path.join(RESULTS_DIR, "arrival_memory_result.json")),
    ]

    evaluations = []
    for label, path in conditions:
        print(f"\n  --- Evaluating {label} ---")
        ev = evaluate_condition(path, gt)
        evaluations.append(ev)

        if "error" in ev:
            print(f"    {ev['error']}")
            continue

        print(f"    Bugs found: {ev['bugs_found']}/{ev['bugs_total']} ({ev['score_bugs']:.0%})")
        if ev["bugs_missed"]:
            missed_str = ", ".join(f"#{m['id']}({m['category']})" for m in ev["bugs_missed"])
            print(f"    Missed: {missed_str}")
        if ev["bonus_found"]:
            print(f"    Bonus issues found: {ev['bonus_found']}")
        print(f"    Tokens: {ev['prompt_tokens'] + ev['completion_tokens']:,}")
        print(f"    Cost: ${ev['cost_usd']:.4f}")
        print(f"    API calls: {ev['total_calls']}")
        if ev.get("care_resolve") is not None:
            print(f"    CARE Resolve: {ev['care_resolve']:.3f}")
            print(f"    Meaning Debt: {ev['meaning_debt']:.3f}")
        if ev.get("memory_injected"):
            print(f"    Memory injected: Yes ({ev['memory_count']} injections)")

    # Summary table
    print("\n" + "=" * 60)
    print("  SUMMARY TABLE")
    print("=" * 60)
    print(f"\n  {'Metric':<25} {'A:Solo':>10} {'B:ARRIVAL':>10} {'C:ARR+Mem':>10}")
    print(f"  {'-'*55}")

    for metric in ["bugs_found", "cost_usd", "total_calls"]:
        vals = []
        for ev in evaluations:
            if "error" in ev:
                vals.append("N/A")
            elif metric == "cost_usd":
                vals.append(f"${ev[metric]:.4f}")
            else:
                vals.append(str(ev.get(metric, "N/A")))
        print(f"  {metric:<25} {vals[0]:>10} {vals[1]:>10} {vals[2]:>10}")

    # Save evaluation
    eval_path = os.path.join(RESULTS_DIR, "evaluation.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluations, f, indent=2, ensure_ascii=False)
    print(f"\n  Evaluation saved: {eval_path}")

    return evaluations


if __name__ == "__main__":
    main()
