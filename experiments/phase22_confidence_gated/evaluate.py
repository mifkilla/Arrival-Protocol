# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 22 Evaluation: CGD vs Phase 21 baselines

Compares CGD results with:
1. Phase 21 ARRIVAL MV (debate, same models)
2. Phase 21 Non-Debate MV (solo, same models)
3. Phase 21 individual solo baselines
4. Phase 21 Grok-weighted MV (computed from existing data)

Statistical tests: McNemar, Wilson CI, per-domain breakdown.

Usage:
    python evaluate.py                    # Evaluate full run
    python evaluate.py --test-only        # Evaluate 20-question test
"""

import json
import os
import sys
import math
import argparse
from collections import Counter

# Windows encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
P21_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "phase21_gpqa_strong", "results")


# ============================================================
# Statistical utilities
# ============================================================
def wilson_ci(n_correct, n_total, z=1.96):
    """Wilson score interval for 95% CI."""
    if n_total == 0:
        return (0.0, 0.0)
    p = n_correct / n_total
    denom = 1 + z**2 / n_total
    centre = p + z**2 / (2 * n_total)
    adj = z * math.sqrt(p * (1 - p) / n_total + z**2 / (4 * n_total**2))
    lower = max(0, (centre - adj) / denom)
    upper = min(1, (centre + adj) / denom)
    return (round(lower, 4), round(upper, 4))


def mcnemar_test(a, b, c, d):
    """McNemar's test on 2x2 contingency table.
    a = both correct, b = method1 correct & method2 wrong,
    c = method1 wrong & method2 correct, d = both wrong.
    Returns (chi2, p_value, significant)."""
    if b + c == 0:
        return (0.0, 1.0, False)
    chi2 = (b - c) ** 2 / (b + c)
    # One-tailed approximation from chi-squared distribution with 1 df
    from math import exp, sqrt, pi
    # Use survival function approximation for chi2 with 1 df
    p_value = _chi2_sf(chi2, 1)
    return (round(chi2, 4), round(p_value, 6), p_value < 0.05)


def _chi2_sf(x, k=1):
    """Survival function (1 - CDF) for chi-squared distribution, k=1."""
    if x <= 0:
        return 1.0
    # For k=1: P(X > x) = 2 * (1 - Phi(sqrt(x)))
    z = math.sqrt(x)
    return 2 * (1 - _normal_cdf(z))


def _normal_cdf(x):
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ============================================================
# Main evaluation
# ============================================================
def evaluate_full():
    """Evaluate CGD full run vs Phase 21 baselines."""
    # Load CGD results
    cgd_path = os.path.join(RESULTS_DIR, "cgd_full_results.json")
    with open(cgd_path, "r", encoding="utf-8") as f:
        cgd_data = json.load(f)
    cgd_results = cgd_data["questions"]
    cgd_by_id = {r["question_id"]: r for r in cgd_results}

    # Load Phase 21 results
    with open(os.path.join(P21_DIR, "arrival_results.json"), "r", encoding="utf-8") as f:
        p21_arrival = json.load(f)
    p21_arrival_by_id = {r["question_id"]: r for r in p21_arrival["questions"]}

    with open(os.path.join(P21_DIR, "non_debate_mv.json"), "r", encoding="utf-8") as f:
        p21_nd = json.load(f)
    p21_nd_by_id = {r["question_id"]: r for r in p21_nd["questions"]}

    # Load solo baselines
    solo_files = {
        "solo_gpt": "solo_gpt41.json",
        "solo_gemini": "solo_gemini3flash.json",
        "solo_grok": "solo_grok41.json",
    }
    solo_by_id = {}
    for key, fname in solo_files.items():
        path = os.path.join(P21_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        solo_by_id[key] = {r["question_id"]: r for r in data["questions"]}

    # Build unified dataset
    all_qids = sorted(cgd_by_id.keys())
    n = len(all_qids)

    print(f"=" * 70)
    print(f"  Phase 22 Evaluation: CGD vs Phase 21 Baselines")
    print(f"  Questions: {n}")
    print(f"=" * 70)

    # ---- Accuracy computation ----
    cgd_correct = sum(1 for qid in all_qids if cgd_by_id[qid]["correct"])
    arrival_mv_correct = sum(1 for qid in all_qids
                              if p21_arrival_by_id.get(qid, {}).get("correct_mv", False))
    arrival_r4_correct = sum(1 for qid in all_qids
                              if p21_arrival_by_id.get(qid, {}).get("correct_r4", False))
    nd_mv_correct = sum(1 for qid in all_qids
                         if p21_nd_by_id.get(qid, {}).get("correct", False))
    solo_gpt_correct = sum(1 for qid in all_qids
                            if solo_by_id["solo_gpt"].get(qid, {}).get("correct", False))
    solo_gemini_correct = sum(1 for qid in all_qids
                               if solo_by_id["solo_gemini"].get(qid, {}).get("correct", False))
    solo_grok_correct = sum(1 for qid in all_qids
                             if solo_by_id["solo_grok"].get(qid, {}).get("correct", False))

    # Grok-weighted MV from Phase 21 solo data
    grok_weighted_correct = 0
    for qid in all_qids:
        gpt_ans = solo_by_id["solo_gpt"].get(qid, {}).get("answer")
        gem_ans = solo_by_id["solo_gemini"].get(qid, {}).get("answer")
        grok_ans = solo_by_id["solo_grok"].get(qid, {}).get("answer")
        correct_ans = cgd_by_id[qid]["correct_answer"]

        # Weighted: Grok=2, others=1
        votes = Counter()
        if gpt_ans: votes[gpt_ans] += 1
        if gem_ans: votes[gem_ans] += 1
        if grok_ans: votes[grok_ans] += 2
        if votes:
            winner = votes.most_common(1)[0][0]
            if winner == correct_ans:
                grok_weighted_correct += 1

    # Oracle (any model gets it right in CGD solo phase)
    oracle_correct = 0
    for qid in all_qids:
        r = cgd_by_id[qid]
        if any(r.get(f"solo_{m}") == r["correct_answer"] for m in ["grok", "gemini", "gpt"]):
            oracle_correct += 1

    print("\n  Overall Accuracy:")
    methods = [
        ("CGD (Phase 22)", cgd_correct),
        ("Non-Debate MV (Phase 21)", nd_mv_correct),
        ("ARRIVAL MV (Phase 21)", arrival_mv_correct),
        ("ARRIVAL R4 (Phase 21)", arrival_r4_correct),
        ("Grok-weighted MV", grok_weighted_correct),
        ("Solo Grok 4.1", solo_grok_correct),
        ("Solo Gemini 3 Flash", solo_gemini_correct),
        ("Solo GPT-4.1", solo_gpt_correct),
        ("Oracle (any model)", oracle_correct),
    ]

    for name, correct in methods:
        ci = wilson_ci(correct, n)
        acc = correct / n * 100
        print(f"    {name:30s}: {correct:3d}/{n} = {acc:5.1f}%  [{ci[0]*100:.1f}%, {ci[1]*100:.1f}%]")

    # ---- McNemar tests ----
    print("\n  McNemar Tests:")

    # CGD vs Non-Debate MV (PRIMARY)
    a, b, c, d_val = 0, 0, 0, 0
    for qid in all_qids:
        cgd_ok = cgd_by_id[qid]["correct"]
        nd_ok = p21_nd_by_id.get(qid, {}).get("correct", False)
        if cgd_ok and nd_ok: a += 1
        elif cgd_ok and not nd_ok: b += 1
        elif not cgd_ok and nd_ok: c += 1
        else: d_val += 1

    chi2, p, sig = mcnemar_test(a, b, c, d_val)
    print(f"\n    CGD vs Non-Debate MV (PRIMARY):")
    print(f"      Both correct: {a}, CGD wins: {b}, ND wins: {c}, Both wrong: {d_val}")
    print(f"      McNemar chi2={chi2}, p={p} {'**SIGNIFICANT**' if sig else '(ns)'}")
    print(f"      Net CGD effect: {b - c:+d}")

    # CGD vs ARRIVAL MV
    a2, b2, c2, d2 = 0, 0, 0, 0
    for qid in all_qids:
        cgd_ok = cgd_by_id[qid]["correct"]
        ar_ok = p21_arrival_by_id.get(qid, {}).get("correct_mv", False)
        if cgd_ok and ar_ok: a2 += 1
        elif cgd_ok and not ar_ok: b2 += 1
        elif not cgd_ok and ar_ok: c2 += 1
        else: d2 += 1

    chi2_2, p2, sig2 = mcnemar_test(a2, b2, c2, d2)
    print(f"\n    CGD vs ARRIVAL MV (debate):")
    print(f"      Both correct: {a2}, CGD wins: {b2}, AR wins: {c2}, Both wrong: {d2}")
    print(f"      McNemar chi2={chi2_2}, p={p2} {'**SIGNIFICANT**' if sig2 else '(ns)'}")
    print(f"      Net CGD effect: {b2 - c2:+d}")

    # CGD vs Grok-weighted MV
    a3, b3, c3, d3 = 0, 0, 0, 0
    for qid in all_qids:
        cgd_ok = cgd_by_id[qid]["correct"]
        gpt_ans = solo_by_id["solo_gpt"].get(qid, {}).get("answer")
        gem_ans = solo_by_id["solo_gemini"].get(qid, {}).get("answer")
        grok_ans = solo_by_id["solo_grok"].get(qid, {}).get("answer")
        correct_ans = cgd_by_id[qid]["correct_answer"]
        votes = Counter()
        if gpt_ans: votes[gpt_ans] += 1
        if gem_ans: votes[gem_ans] += 1
        if grok_ans: votes[grok_ans] += 2
        gw_ok = votes.most_common(1)[0][0] == correct_ans if votes else False
        if cgd_ok and gw_ok: a3 += 1
        elif cgd_ok and not gw_ok: b3 += 1
        elif not cgd_ok and gw_ok: c3 += 1
        else: d3 += 1

    chi2_3, p3, sig3 = mcnemar_test(a3, b3, c3, d3)
    print(f"\n    CGD vs Grok-weighted MV:")
    print(f"      Both correct: {a3}, CGD wins: {b3}, GW wins: {c3}, Both wrong: {d3}")
    print(f"      McNemar chi2={chi2_3}, p={p3} {'**SIGNIFICANT**' if sig3 else '(ns)'}")
    print(f"      Net CGD effect: {b3 - c3:+d}")

    # ---- Per-domain ----
    print("\n  Per-Domain Accuracy:")
    for domain in ["Physics", "Chemistry", "Biology"]:
        dom_qids = [qid for qid in all_qids if cgd_by_id[qid]["domain"] == domain]
        if not dom_qids:
            continue
        dn = len(dom_qids)
        cgd_d = sum(1 for qid in dom_qids if cgd_by_id[qid]["correct"])
        nd_d = sum(1 for qid in dom_qids if p21_nd_by_id.get(qid, {}).get("correct", False))
        ar_d = sum(1 for qid in dom_qids if p21_arrival_by_id.get(qid, {}).get("correct_mv", False))
        grok_d = sum(1 for qid in dom_qids if solo_by_id["solo_grok"].get(qid, {}).get("correct", False))

        print(f"    {domain} (n={dn}):")
        print(f"      CGD:     {cgd_d}/{dn} = {cgd_d/dn*100:.1f}%")
        print(f"      ND MV:   {nd_d}/{dn} = {nd_d/dn*100:.1f}%")
        print(f"      AR MV:   {ar_d}/{dn} = {ar_d/dn*100:.1f}%")
        print(f"      Grok:    {grok_d}/{dn} = {grok_d/dn*100:.1f}%")

    # ---- Debate type analysis ----
    print("\n  CGD Debate Type Analysis:")
    dt_counter = Counter(r["debate_type"] for r in cgd_results)
    for dt in sorted(dt_counter.keys()):
        dt_results = [r for r in cgd_results if r["debate_type"] == dt]
        dt_correct = sum(1 for r in dt_results if r["correct"])
        print(f"    {dt}: {dt_correct}/{len(dt_results)} = {dt_correct/len(dt_results)*100:.1f}%"
              f" ({len(dt_results)} questions, {len(dt_results)/n*100:.0f}%)")

    # ---- Extraction bug analysis ----
    print("\n  Extraction Bug Analysis:")
    extraction_bugs = []
    for r in cgd_results:
        solo_answers = {
            "grok": r.get("solo_grok"),
            "gemini": r.get("solo_gemini"),
            "gpt": r.get("solo_gpt"),
        }
        none_models = [m for m, a in solo_answers.items() if a is None or a == "None"]
        if none_models:
            is_unanimous_bug = (r["debate_type"] == "unanimous" and len(none_models) > 0)
            extraction_bugs.append({
                "question_id": r["question_id"],
                "domain": r["domain"],
                "debate_type": r["debate_type"],
                "none_models": none_models,
                "final_answer": r["final_answer"],
                "correct_answer": r["correct_answer"],
                "correct": r["correct"],
                "unanimous_on_fewer": is_unanimous_bug,
            })

    if extraction_bugs:
        print(f"    Found {len(extraction_bugs)} questions with extraction failures:")
        for bug in extraction_bugs:
            status = "OK" if bug["correct"] else "WRONG"
            flag = " [UNANIMOUS_BUG]" if bug["unanimous_on_fewer"] else ""
            print(f"      {bug['question_id']} ({bug['domain']}): {bug['debate_type']} "
                  f"| None in: {bug['none_models']} -> {bug['final_answer']} [{status}]{flag}")

        # Accuracy excluding extraction bugs
        bug_ids = {b["question_id"] for b in extraction_bugs}
        clean_n = n - len(bug_ids)
        clean_correct = sum(1 for qid in all_qids
                           if qid not in bug_ids and cgd_by_id[qid]["correct"])
        if clean_n > 0:
            print(f"    Accuracy WITHOUT extraction bugs: {clean_correct}/{clean_n} = "
                  f"{clean_correct/clean_n*100:.1f}% (vs {cgd_correct/n*100:.1f}% with)")
    else:
        print(f"    No extraction failures found (0 None answers)")
        extraction_bugs = []

    # ---- Minority-was-right analysis ----
    print("\n  Minority-Was-Right Analysis:")
    minority_analysis = []
    minority_right_count = 0
    minority_total = 0

    for r in cgd_results:
        if r["debate_type"] == "unanimous":
            continue

        solo_answers = {
            "grok": r.get("solo_grok"),
            "gemini": r.get("solo_gemini"),
            "gpt": r.get("solo_gpt"),
        }
        correct_ans = r["correct_answer"]

        if r["debate_type"] == "split_2v1":
            # Find minority model (the one that disagrees)
            ans_counts = Counter(v for v in solo_answers.values() if v)
            if len(ans_counts) >= 2:
                minority_ans = ans_counts.most_common()[-1][0]
                minority_models = [m for m, a in solo_answers.items() if a == minority_ans]
                majority_ans = ans_counts.most_common()[0][0]
                majority_models = [m for m, a in solo_answers.items() if a == majority_ans]

                minority_correct = (minority_ans == correct_ans)
                majority_correct = (majority_ans == correct_ans)
                minority_total += 1
                if minority_correct:
                    minority_right_count += 1

                minority_analysis.append({
                    "question_id": r["question_id"],
                    "domain": r["domain"],
                    "debate_type": "split_2v1",
                    "minority_model": minority_models[0] if minority_models else "unknown",
                    "minority_answer": minority_ans,
                    "minority_correct": minority_correct,
                    "majority_answer": majority_ans,
                    "majority_models": majority_models,
                    "majority_correct": majority_correct,
                    "final_answer": r["final_answer"],
                    "final_correct": r["correct"],
                    "correct_answer": correct_ans,
                })

        elif r["debate_type"] == "split_3way":
            # All three different — track which model was right
            for model, ans in solo_answers.items():
                if ans == correct_ans:
                    minority_analysis.append({
                        "question_id": r["question_id"],
                        "domain": r["domain"],
                        "debate_type": "split_3way",
                        "minority_model": model,
                        "minority_answer": ans,
                        "minority_correct": True,
                        "majority_answer": None,
                        "majority_models": [],
                        "majority_correct": False,
                        "final_answer": r["final_answer"],
                        "final_correct": r["correct"],
                        "correct_answer": correct_ans,
                    })
                    break
            else:
                # No model was right (oracle fail in 3-way)
                minority_analysis.append({
                    "question_id": r["question_id"],
                    "domain": r["domain"],
                    "debate_type": "split_3way",
                    "minority_model": "none",
                    "minority_answer": None,
                    "minority_correct": False,
                    "majority_answer": None,
                    "majority_models": [],
                    "majority_correct": False,
                    "final_answer": r["final_answer"],
                    "final_correct": r["correct"],
                    "correct_answer": correct_ans,
                })

    if minority_total > 0:
        print(f"    Split 2v1 questions: {minority_total}")
        print(f"    Minority was right: {minority_right_count}/{minority_total} = "
              f"{minority_right_count/minority_total*100:.1f}%")

        # Per-model minority stats
        model_minority = Counter()
        model_minority_right = Counter()
        for item in minority_analysis:
            if item["debate_type"] == "split_2v1":
                model_minority[item["minority_model"]] += 1
                if item["minority_correct"]:
                    model_minority_right[item["minority_model"]] += 1
        print(f"    Per-model as minority (2v1):")
        for model in ["grok", "gemini", "gpt"]:
            total_m = model_minority.get(model, 0)
            right_m = model_minority_right.get(model, 0)
            if total_m > 0:
                print(f"      {model}: minority {total_m}x, right {right_m}x ({right_m/total_m*100:.0f}%)")

        # Cases where minority was right but lost debate
        lost_debates = [m for m in minority_analysis
                       if m["minority_correct"] and not m["final_correct"]]
        if lost_debates:
            print(f"    Minority RIGHT but LOST debate: {len(lost_debates)} questions:")
            for item in lost_debates:
                print(f"      {item['question_id']} ({item['domain']}): "
                      f"{item['minority_model']}:{item['minority_answer']} was right, "
                      f"final={item['final_answer']}")

    # ---- Cost comparison ----
    cgd_cost = cgd_data["summary"]["total_cost_usd"]
    cgd_calls = cgd_data["summary"]["total_api_calls"]

    print(f"\n  Cost Comparison:")
    print(f"    CGD:           ${cgd_cost:.2f} ({cgd_calls} calls)")
    print(f"    Phase 21 ARRIVAL: $4.89 (792 calls)")
    print(f"    Phase 21 Solo:    $4.74 (594 calls)")
    print(f"    CGD per-question: ${cgd_cost/n:.4f}")

    # ---- Save evaluation ----
    evaluation = {
        "phase": "Phase 22 Evaluation: CGD vs Phase 21",
        "n_questions": n,
        "overall_accuracy": {
            "cgd": {"correct": cgd_correct, "total": n, "accuracy": round(cgd_correct/n, 4),
                     "ci_95": list(wilson_ci(cgd_correct, n))},
            "non_debate_mv": {"correct": nd_mv_correct, "total": n,
                               "accuracy": round(nd_mv_correct/n, 4),
                               "ci_95": list(wilson_ci(nd_mv_correct, n))},
            "arrival_mv": {"correct": arrival_mv_correct, "total": n,
                            "accuracy": round(arrival_mv_correct/n, 4),
                            "ci_95": list(wilson_ci(arrival_mv_correct, n))},
            "arrival_r4": {"correct": arrival_r4_correct, "total": n,
                            "accuracy": round(arrival_r4_correct/n, 4),
                            "ci_95": list(wilson_ci(arrival_r4_correct, n))},
            "grok_weighted_mv": {"correct": grok_weighted_correct, "total": n,
                                  "accuracy": round(grok_weighted_correct/n, 4),
                                  "ci_95": list(wilson_ci(grok_weighted_correct, n))},
            "solo_grok": {"correct": solo_grok_correct, "total": n,
                           "accuracy": round(solo_grok_correct/n, 4),
                           "ci_95": list(wilson_ci(solo_grok_correct, n))},
            "solo_gemini": {"correct": solo_gemini_correct, "total": n,
                             "accuracy": round(solo_gemini_correct/n, 4),
                             "ci_95": list(wilson_ci(solo_gemini_correct, n))},
            "solo_gpt": {"correct": solo_gpt_correct, "total": n,
                          "accuracy": round(solo_gpt_correct/n, 4),
                          "ci_95": list(wilson_ci(solo_gpt_correct, n))},
            "oracle": {"correct": oracle_correct, "total": n,
                        "accuracy": round(oracle_correct/n, 4)},
        },
        "mcnemar_tests": {
            "cgd_vs_nd_mv": {
                "both_correct": a, "cgd_wins": b, "nd_wins": c, "both_wrong": d_val,
                "chi2": chi2, "p_value": p, "significant": sig,
                "net_cgd_effect": b - c,
            },
            "cgd_vs_arrival_mv": {
                "both_correct": a2, "cgd_wins": b2, "ar_wins": c2, "both_wrong": d2,
                "chi2": chi2_2, "p_value": p2, "significant": sig2,
                "net_cgd_effect": b2 - c2,
            },
            "cgd_vs_grok_weighted": {
                "both_correct": a3, "cgd_wins": b3, "gw_wins": c3, "both_wrong": d3,
                "chi2": chi2_3, "p_value": p3, "significant": sig3,
                "net_cgd_effect": b3 - c3,
            },
        },
        "debate_types": {dt: {"n": len([r for r in cgd_results if r["debate_type"] == dt]),
                               "correct": sum(1 for r in cgd_results if r["debate_type"] == dt and r["correct"]),
                               "accuracy": round(sum(1 for r in cgd_results if r["debate_type"] == dt and r["correct"])
                                                  / len([r for r in cgd_results if r["debate_type"] == dt]), 4)}
                          for dt in set(r["debate_type"] for r in cgd_results)},
        "cost": {
            "cgd": {"total": cgd_cost, "per_question": round(cgd_cost / n, 4), "api_calls": cgd_calls},
            "phase21_arrival": {"total": 4.89, "per_question": round(4.89/198, 4), "api_calls": 792},
            "phase21_solo": {"total": 4.74, "per_question": round(4.74/198, 4), "api_calls": 594},
        },
        "extraction_bugs": {
            "count": len(extraction_bugs),
            "bugs": extraction_bugs,
            "accuracy_without_bugs": round(clean_correct / clean_n, 4) if extraction_bugs and clean_n > 0 else None,
        },
        "minority_analysis": {
            "split_2v1_total": minority_total,
            "minority_right_count": minority_right_count,
            "minority_right_rate": round(minority_right_count / minority_total, 4) if minority_total > 0 else None,
            "details": minority_analysis,
        },
    }

    eval_path = os.path.join(RESULTS_DIR, "evaluation.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {eval_path}")


def evaluate_test():
    """Evaluate 20-question test run."""
    path = os.path.join(RESULTS_DIR, "phase22_results.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"=" * 70)
    print(f"  Phase 22 Test Evaluation (20 hardest questions)")
    print(f"=" * 70)

    n = data["n_questions"]
    s = data["summary"]
    print(f"\n  CGD:     {s['cgd_correct']}/{n} = {s['cgd_accuracy']*100:.1f}%")
    print(f"  SF R4:   {s['sf_r4_correct']}/{n} = {s['sf_r4_accuracy']*100:.1f}%")
    print(f"  SF MV:   {s['sf_mv_correct']}/{n} = {s['sf_mv_accuracy']*100:.1f}%")
    print(f"  Cost:    ${s['total_cost']:.2f}")

    # CGD debate types
    dt_counts = Counter(r["debate_type"] for r in data["cgd_results"])
    for dt in sorted(dt_counts.keys()):
        dt_results = [r for r in data["cgd_results"] if r["debate_type"] == dt]
        dt_correct = sum(1 for r in dt_results if r["correct"])
        print(f"  {dt}: {dt_correct}/{len(dt_results)} = {dt_correct/len(dt_results)*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Phase 22 Evaluation")
    parser.add_argument("--test-only", action="store_true", help="Evaluate only 20-question test")
    args = parser.parse_args()

    if args.test_only:
        evaluate_test()
    else:
        evaluate_full()


if __name__ == "__main__":
    main()
