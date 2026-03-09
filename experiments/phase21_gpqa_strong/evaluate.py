# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 21: Statistical Evaluation — ARRIVAL Strong Trio vs Non-Debate MV

Primary test: McNemar ARRIVAL MV vs Non-Debate MV (same 3 models, debate vs no debate)
This isolates the causal effect of discussion.

Usage:
    python evaluate.py
"""

import json
import os
import sys
import math
from collections import Counter

# Windows encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def wilson_ci(n_success, n_total, z=1.96):
    """Wilson score 95% CI for binomial proportion."""
    if n_total == 0:
        return (0, 0)
    p = n_success / n_total
    denom = 1 + z**2 / n_total
    centre = p + z**2 / (2 * n_total)
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n_total)) / n_total)
    lo = (centre - spread) / denom
    hi = (centre + spread) / denom
    return (round(lo, 4), round(hi, 4))


def mcnemar_test(a, b, c, d):
    """McNemar test with continuity correction. Returns chi2, p-value."""
    # a=both_correct, b=X_correct_Y_wrong, c=X_wrong_Y_correct, d=both_wrong
    if b + c == 0:
        return 0.0, 1.0
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    # chi-square with 1 df: p = 1 - CDF(chi2)
    # Approximate using complementary error function
    p = chi2_to_p(chi2)
    return round(chi2, 4), round(p, 6)


def chi2_to_p(chi2, df=1):
    """Approximate p-value for chi-square test with 1 df."""
    from math import exp, sqrt, pi
    if chi2 <= 0:
        return 1.0
    # Use normal approximation: sqrt(chi2) ~ N(0,1)
    z = sqrt(chi2)
    # Complementary error function approximation
    t = 1.0 / (1.0 + 0.2316419 * z)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    p = 2.0 * poly * exp(-z * z / 2.0) / sqrt(2 * pi)
    return min(max(p, 0.0), 1.0)


def fisher_exact_2x2(a, b, c, d):
    """Fisher's exact test for 2x2 table. Returns p-value (two-sided)."""
    from math import lgamma, exp
    n = a + b + c + d
    def log_hyper(a, b, c, d):
        n = a + b + c + d
        return (lgamma(a+b+1) + lgamma(c+d+1) + lgamma(a+c+1) + lgamma(b+d+1)
                - lgamma(a+1) - lgamma(b+1) - lgamma(c+1) - lgamma(d+1) - lgamma(n+1))

    p_obs = exp(log_hyper(a, b, c, d))
    p_val = 0.0
    row1 = a + b
    row2 = c + d
    col1 = a + c
    col2 = b + d
    for i in range(min(row1, col1) + 1):
        aa = i
        bb = row1 - i
        cc = col1 - i
        dd = row2 - cc
        if bb < 0 or cc < 0 or dd < 0:
            continue
        p_i = exp(log_hyper(aa, bb, cc, dd))
        if p_i <= p_obs + 1e-10:
            p_val += p_i
    return min(round(p_val, 6), 1.0)


def main():
    print("=" * 70)
    print("  Phase 21: Statistical Evaluation")
    print("=" * 70)

    # ---- Load all results ----
    arrival_file = os.path.join(RESULTS_DIR, "arrival_results.json")
    solo_gpt_file = os.path.join(RESULTS_DIR, "solo_gpt41.json")
    solo_gemini_file = os.path.join(RESULTS_DIR, "solo_gemini3flash.json")
    solo_grok_file = os.path.join(RESULTS_DIR, "solo_grok41.json")

    for f_path, label in [
        (arrival_file, "ARRIVAL"),
        (solo_gpt_file, "Solo GPT-4.1"),
        (solo_gemini_file, "Solo Gemini3Flash"),
        (solo_grok_file, "Solo Grok4.1"),
    ]:
        if not os.path.exists(f_path):
            print(f"  ERROR: Missing {label} results: {f_path}")
            return

    with open(arrival_file, "r", encoding="utf-8") as f:
        arrival_data = json.load(f)
    with open(solo_gpt_file, "r", encoding="utf-8") as f:
        solo_gpt = json.load(f)
    with open(solo_gemini_file, "r", encoding="utf-8") as f:
        solo_gemini = json.load(f)
    with open(solo_grok_file, "r", encoding="utf-8") as f:
        solo_grok = json.load(f)

    arrival_qs = {r["question_id"]: r for r in arrival_data["questions"]}
    gpt_qs = {r["question_id"]: r for r in solo_gpt["questions"]}
    gemini_qs = {r["question_id"]: r for r in solo_gemini["questions"]}
    grok_qs = {r["question_id"]: r for r in solo_grok["questions"]}

    # Get all question IDs present in ALL datasets
    all_ids = set(arrival_qs.keys()) & set(gpt_qs.keys()) & set(gemini_qs.keys()) & set(grok_qs.keys())
    all_ids = sorted(all_ids)
    n = len(all_ids)
    print(f"\n  Matched questions across all conditions: {n}")

    # ============================================================
    # 1. Overall Accuracy
    # ============================================================
    print("\n" + "=" * 60)
    print("  1. Overall Accuracy")
    print("=" * 60)

    # ARRIVAL R4 and MV
    ar_r4_correct = sum(1 for qid in all_ids if arrival_qs[qid].get("correct_arrival"))
    ar_mv_correct = sum(1 for qid in all_ids if arrival_qs[qid].get("correct_mv"))

    # Per-model solo accuracy
    gpt_correct = sum(1 for qid in all_ids if gpt_qs[qid].get("correct"))
    gemini_correct = sum(1 for qid in all_ids if gemini_qs[qid].get("correct"))
    grok_correct = sum(1 for qid in all_ids if grok_qs[qid].get("correct"))

    # Non-debate MV: majority vote of 3 solo answers
    nd_mv_correct = 0
    nd_mv_answers = {}
    for qid in all_ids:
        answers = []
        for results_dict in [gpt_qs, gemini_qs, grok_qs]:
            if qid in results_dict and results_dict[qid].get("answer"):
                answers.append(results_dict[qid]["answer"])
        if answers:
            mv_ans = Counter(answers).most_common(1)[0][0]
        else:
            mv_ans = None
        nd_mv_answers[qid] = mv_ans
        correct_ans = arrival_qs[qid]["correct_answer"]
        if mv_ans == correct_ans:
            nd_mv_correct += 1

    # CIs
    ar_r4_ci = wilson_ci(ar_r4_correct, n)
    ar_mv_ci = wilson_ci(ar_mv_correct, n)
    gpt_ci = wilson_ci(gpt_correct, n)
    gemini_ci = wilson_ci(gemini_correct, n)
    grok_ci = wilson_ci(grok_correct, n)
    nd_mv_ci = wilson_ci(nd_mv_correct, n)

    print(f"\n  {'Condition':<25} {'Correct':<10} {'Accuracy':<12} {'95% CI'}")
    print(f"  {'-'*25} {'-'*10} {'-'*12} {'-'*20}")
    print(f"  {'ARRIVAL MV (debate)':<25} {ar_mv_correct}/{n:<7} {ar_mv_correct/n:.1%}         [{ar_mv_ci[0]:.1%}, {ar_mv_ci[1]:.1%}]")
    print(f"  {'ARRIVAL R4 (debate)':<25} {ar_r4_correct}/{n:<7} {ar_r4_correct/n:.1%}         [{ar_r4_ci[0]:.1%}, {ar_r4_ci[1]:.1%}]")
    print(f"  {'Non-Debate MV':<25} {nd_mv_correct}/{n:<7} {nd_mv_correct/n:.1%}         [{nd_mv_ci[0]:.1%}, {nd_mv_ci[1]:.1%}]")
    print(f"  {'Solo GPT-4.1':<25} {gpt_correct}/{n:<7} {gpt_correct/n:.1%}         [{gpt_ci[0]:.1%}, {gpt_ci[1]:.1%}]")
    print(f"  {'Solo Gemini3Flash':<25} {gemini_correct}/{n:<7} {gemini_correct/n:.1%}         [{gemini_ci[0]:.1%}, {gemini_ci[1]:.1%}]")
    print(f"  {'Solo Grok4.1':<25} {grok_correct}/{n:<7} {grok_correct/n:.1%}         [{grok_ci[0]:.1%}, {grok_ci[1]:.1%}]")

    # ============================================================
    # 2. PRIMARY TEST: McNemar ARRIVAL MV vs Non-Debate MV
    # ============================================================
    print("\n" + "=" * 60)
    print("  2. PRIMARY: McNemar ARRIVAL MV vs Non-Debate MV")
    print("  (Same 3 models, debate vs no debate)")
    print("=" * 60)

    # Build contingency table
    both_correct = 0
    ar_wins = 0  # ARRIVAL correct, ND wrong
    nd_wins = 0  # ND correct, ARRIVAL wrong
    both_wrong = 0

    for qid in all_ids:
        ar_ok = arrival_qs[qid].get("correct_mv", False)
        nd_ok = nd_mv_answers[qid] == arrival_qs[qid]["correct_answer"] if nd_mv_answers[qid] else False
        if ar_ok and nd_ok:
            both_correct += 1
        elif ar_ok and not nd_ok:
            ar_wins += 1
        elif not ar_ok and nd_ok:
            nd_wins += 1
        else:
            both_wrong += 1

    chi2, p_val = mcnemar_test(both_correct, ar_wins, nd_wins, both_wrong)

    print(f"\n  Contingency table:")
    print(f"  {'':>25} {'ND correct':>12} {'ND wrong':>12}")
    print(f"  {'ARRIVAL MV correct':>25} {both_correct:>12} {ar_wins:>12} (debate wins)")
    print(f"  {'ARRIVAL MV wrong':>25} {nd_wins:>12} {both_wrong:>12} (debate losses)")
    print(f"\n  McNemar chi2 = {chi2}, p = {p_val}")
    print(f"  Debate wins: {ar_wins}, Debate losses: {nd_wins}, Net: {ar_wins - nd_wins}")
    sig = "SIGNIFICANT (p < 0.05)" if p_val < 0.05 else "NOT significant"
    print(f"  Result: {sig}")

    # ============================================================
    # 3. SECONDARY: McNemar ARRIVAL R4 vs ARRIVAL MV
    # ============================================================
    print("\n" + "=" * 60)
    print("  3. SECONDARY: McNemar ARRIVAL R4 vs ARRIVAL MV")
    print("=" * 60)

    r4_wins = 0  # R4 correct, MV wrong (rescues)
    r4_losses = 0  # R4 wrong, MV correct (regressions)
    r4_mv_both = 0
    r4_mv_neither = 0

    for qid in all_ids:
        r4_ok = arrival_qs[qid].get("correct_arrival", False)
        mv_ok = arrival_qs[qid].get("correct_mv", False)
        if r4_ok and mv_ok:
            r4_mv_both += 1
        elif r4_ok and not mv_ok:
            r4_wins += 1
        elif not r4_ok and mv_ok:
            r4_losses += 1
        else:
            r4_mv_neither += 1

    chi2_r4mv, p_r4mv = mcnemar_test(r4_mv_both, r4_wins, r4_losses, r4_mv_neither)
    print(f"\n  R4 rescues: {r4_wins}, R4 regressions: {r4_losses}, Net: {r4_wins - r4_losses}")
    print(f"  McNemar chi2 = {chi2_r4mv}, p = {p_r4mv}")

    # ============================================================
    # 4. McNemar: ARRIVAL MV vs Solo GPT-4.1 (strongest solo)
    # ============================================================
    print("\n" + "=" * 60)
    print("  4. McNemar: ARRIVAL MV vs Solo GPT-4.1")
    print("=" * 60)

    a4 = sum(1 for qid in all_ids if arrival_qs[qid].get("correct_mv") and gpt_qs[qid].get("correct"))
    b4 = sum(1 for qid in all_ids if arrival_qs[qid].get("correct_mv") and not gpt_qs[qid].get("correct"))
    c4 = sum(1 for qid in all_ids if not arrival_qs[qid].get("correct_mv") and gpt_qs[qid].get("correct"))
    d4 = sum(1 for qid in all_ids if not arrival_qs[qid].get("correct_mv") and not gpt_qs[qid].get("correct"))
    chi2_4, p_4 = mcnemar_test(a4, b4, c4, d4)
    print(f"  ARRIVAL MV wins: {b4}, GPT-4.1 wins: {c4}, Net: {b4 - c4}")
    print(f"  McNemar chi2 = {chi2_4}, p = {p_4}")

    # ============================================================
    # 5. Per-Domain Breakdown
    # ============================================================
    print("\n" + "=" * 60)
    print("  5. Per-Domain Breakdown")
    print("=" * 60)

    domains = {}
    for qid in all_ids:
        d = arrival_qs[qid]["domain"]
        if d not in domains:
            domains[d] = {"n": 0, "ar_mv": 0, "ar_r4": 0, "nd_mv": 0,
                          "gpt": 0, "gemini": 0, "grok": 0}
        domains[d]["n"] += 1
        if arrival_qs[qid].get("correct_mv"): domains[d]["ar_mv"] += 1
        if arrival_qs[qid].get("correct_arrival"): domains[d]["ar_r4"] += 1
        nd_ok = nd_mv_answers[qid] == arrival_qs[qid]["correct_answer"] if nd_mv_answers.get(qid) else False
        if nd_ok: domains[d]["nd_mv"] += 1
        if gpt_qs[qid].get("correct"): domains[d]["gpt"] += 1
        if gemini_qs[qid].get("correct"): domains[d]["gemini"] += 1
        if grok_qs[qid].get("correct"): domains[d]["grok"] += 1

    print(f"\n  {'Domain':<12} {'n':<5} {'AR MV':<8} {'AR R4':<8} {'ND MV':<8} {'GPT':<8} {'Gemini':<8} {'Grok':<8}")
    for d in sorted(domains.keys()):
        v = domains[d]
        n_d = v["n"]
        print(f"  {d:<12} {n_d:<5} "
              f"{v['ar_mv']/n_d:.1%}    {v['ar_r4']/n_d:.1%}    {v['nd_mv']/n_d:.1%}    "
              f"{v['gpt']/n_d:.1%}    {v['gemini']/n_d:.1%}    {v['grok']/n_d:.1%}")

    # ============================================================
    # 6. Per-Model Accuracy within ARRIVAL
    # ============================================================
    print("\n" + "=" * 60)
    print("  6. Per-Model Accuracy within ARRIVAL")
    print("=" * 60)

    r1_correct = sum(1 for qid in all_ids if arrival_qs[qid].get("r1_answer") == arrival_qs[qid]["correct_answer"])
    r2_correct = sum(1 for qid in all_ids if arrival_qs[qid].get("r2_answer") == arrival_qs[qid]["correct_answer"])
    r3_correct = sum(1 for qid in all_ids if arrival_qs[qid].get("r3_answer") == arrival_qs[qid]["correct_answer"])

    print(f"  R1 GPT-4.1:      {r1_correct}/{n} = {r1_correct/n:.1%}")
    print(f"  R2 Gemini3Flash:  {r2_correct}/{n} = {r2_correct/n:.1%}")
    print(f"  R3 Grok4.1:      {r3_correct}/{n} = {r3_correct/n:.1%}")

    # ============================================================
    # 7. Flip Rates
    # ============================================================
    print("\n" + "=" * 60)
    print("  7. Flip Rates (answer changes between rounds)")
    print("=" * 60)

    flips_12 = sum(1 for qid in all_ids
                   if arrival_qs[qid].get("r1_answer") and arrival_qs[qid].get("r2_answer")
                   and arrival_qs[qid]["r1_answer"] != arrival_qs[qid]["r2_answer"])
    flips_23 = sum(1 for qid in all_ids
                   if arrival_qs[qid].get("r2_answer") and arrival_qs[qid].get("r3_answer")
                   and arrival_qs[qid]["r2_answer"] != arrival_qs[qid]["r3_answer"])
    flips_34 = sum(1 for qid in all_ids
                   if arrival_qs[qid].get("r3_answer") and arrival_qs[qid].get("r4_final")
                   and arrival_qs[qid]["r3_answer"] != arrival_qs[qid]["r4_final"])

    print(f"  R1 -> R2: {flips_12}/{n} = {flips_12/n:.1%}")
    print(f"  R2 -> R3: {flips_23}/{n} = {flips_23/n:.1%}")
    print(f"  R3 -> R4: {flips_34}/{n} = {flips_34/n:.1%}")

    # ============================================================
    # 8. CARE Resolve & Meaning Debt
    # ============================================================
    print("\n" + "=" * 60)
    print("  8. CRDT Metrics")
    print("=" * 60)

    care_scores = [arrival_qs[qid].get("care_resolve") for qid in all_ids
                   if arrival_qs[qid].get("care_resolve") is not None]
    debt_scores = [arrival_qs[qid].get("meaning_debt", 0) for qid in all_ids]

    if care_scores:
        avg_care = sum(care_scores) / len(care_scores)
        min_care = min(care_scores)
        max_care = max(care_scores)
        print(f"  CARE Resolve: avg={avg_care:.3f}, min={min_care:.3f}, max={max_care:.3f}")
    if debt_scores:
        avg_debt = sum(debt_scores) / len(debt_scores)
        print(f"  Meaning Debt: avg={avg_debt:.3f}")

    # ============================================================
    # 9. Phase 20 Comparison (Weak vs Strong Trio)
    # ============================================================
    print("\n" + "=" * 60)
    print("  9. Comparison with Phase 20 (Weak Trio)")
    print("=" * 60)

    p20_arrival = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "phase20_gpqa_full", "results", "arrival_results.json")
    if os.path.exists(p20_arrival):
        with open(p20_arrival, "r", encoding="utf-8") as f:
            p20_data = json.load(f)
        p20_qs = {r["question_id"]: r for r in p20_data["questions"]}

        # Match questions
        matched = set(all_ids) & set(p20_qs.keys())
        n_matched = len(matched)

        p20_mv = sum(1 for qid in matched if p20_qs[qid].get("correct_mv"))
        p20_r4 = sum(1 for qid in matched if p20_qs[qid].get("correct_arrival"))
        p21_mv = sum(1 for qid in matched if arrival_qs[qid].get("correct_mv"))
        p21_r4 = sum(1 for qid in matched if arrival_qs[qid].get("correct_arrival"))

        print(f"  Matched questions: {n_matched}")
        print(f"  Phase 20 (weak trio):  MV={p20_mv}/{n_matched}={p20_mv/n_matched:.1%}, R4={p20_r4}/{n_matched}={p20_r4/n_matched:.1%}")
        print(f"  Phase 21 (strong trio): MV={p21_mv}/{n_matched}={p21_mv/n_matched:.1%}, R4={p21_r4}/{n_matched}={p21_r4/n_matched:.1%}")
        print(f"  Delta MV: {(p21_mv-p20_mv)/n_matched:+.1%}, Delta R4: {(p21_r4-p20_r4)/n_matched:+.1%}")
    else:
        print("  Phase 20 results not found.")

    # ============================================================
    # 10. Extraction Quality
    # ============================================================
    print("\n" + "=" * 60)
    print("  10. Extraction Quality")
    print("=" * 60)

    for label, qs_dict in [("ARRIVAL R1", "r1_answer"), ("ARRIVAL R2", "r2_answer"),
                            ("ARRIVAL R3", "r3_answer"), ("ARRIVAL R4", "r4_final")]:
        missing = sum(1 for qid in all_ids if not arrival_qs[qid].get(qs_dict))
        print(f"  {label}: {missing}/{n} missing ({missing/n:.1%})")

    for label, qs_dict in [("Solo GPT-4.1", gpt_qs), ("Solo Gemini3Flash", gemini_qs),
                            ("Solo Grok4.1", grok_qs)]:
        missing = sum(1 for qid in all_ids if not qs_dict[qid].get("answer"))
        print(f"  {label}: {missing}/{n} missing ({missing/n:.1%})")

    # ============================================================
    # 11. Cost Summary
    # ============================================================
    print("\n" + "=" * 60)
    print("  11. Cost Summary")
    print("=" * 60)

    ar_cost = sum(arrival_qs[qid].get("cost_usd", 0) for qid in all_ids)
    gpt_cost = sum(gpt_qs[qid].get("cost_usd", 0) for qid in all_ids)
    gemini_cost = sum(gemini_qs[qid].get("cost_usd", 0) for qid in all_ids)
    grok_cost = sum(grok_qs[qid].get("cost_usd", 0) for qid in all_ids)
    total_cost = ar_cost + gpt_cost + gemini_cost + grok_cost

    print(f"  ARRIVAL:         ${ar_cost:.2f}")
    print(f"  Solo GPT-4.1:    ${gpt_cost:.2f}")
    print(f"  Solo Gemini3FL:  ${gemini_cost:.2f}")
    print(f"  Solo Grok4.1:    ${grok_cost:.2f}")
    print(f"  TOTAL:           ${total_cost:.2f}")

    # ============================================================
    # Save evaluation.json
    # ============================================================
    evaluation = {
        "phase": "Phase 21: ARRIVAL Strong Trio vs Non-Debate MV",
        "n_questions": n,
        "overall_accuracy": {
            "arrival_mv": {"correct": ar_mv_correct, "total": n, "accuracy": round(ar_mv_correct/n, 4), "ci_95": ar_mv_ci},
            "arrival_r4": {"correct": ar_r4_correct, "total": n, "accuracy": round(ar_r4_correct/n, 4), "ci_95": ar_r4_ci},
            "non_debate_mv": {"correct": nd_mv_correct, "total": n, "accuracy": round(nd_mv_correct/n, 4), "ci_95": nd_mv_ci},
            "solo_gpt41": {"correct": gpt_correct, "total": n, "accuracy": round(gpt_correct/n, 4), "ci_95": gpt_ci},
            "solo_gemini3flash": {"correct": gemini_correct, "total": n, "accuracy": round(gemini_correct/n, 4), "ci_95": gemini_ci},
            "solo_grok41": {"correct": grok_correct, "total": n, "accuracy": round(grok_correct/n, 4), "ci_95": grok_ci},
        },
        "primary_test": {
            "comparison": "ARRIVAL MV vs Non-Debate MV",
            "contingency": {
                "both_correct": both_correct,
                "debate_wins": ar_wins,
                "no_debate_wins": nd_wins,
                "both_wrong": both_wrong,
            },
            "mcnemar_chi2": chi2,
            "mcnemar_p": p_val,
            "significant": p_val < 0.05,
            "net_debate_effect": ar_wins - nd_wins,
        },
        "secondary_tests": {
            "r4_vs_mv": {
                "rescues": r4_wins,
                "regressions": r4_losses,
                "net": r4_wins - r4_losses,
                "mcnemar_chi2": chi2_r4mv,
                "mcnemar_p": p_r4mv,
            },
            "arrival_mv_vs_solo_gpt41": {
                "arrival_wins": b4,
                "gpt_wins": c4,
                "net": b4 - c4,
                "mcnemar_chi2": chi2_4,
                "mcnemar_p": p_4,
            },
        },
        "per_domain": {
            d: {
                "n": v["n"],
                "arrival_mv": round(v["ar_mv"]/v["n"], 4),
                "arrival_r4": round(v["ar_r4"]/v["n"], 4),
                "non_debate_mv": round(v["nd_mv"]/v["n"], 4),
                "solo_gpt": round(v["gpt"]/v["n"], 4),
                "solo_gemini": round(v["gemini"]/v["n"], 4),
                "solo_grok": round(v["grok"]/v["n"], 4),
            }
            for d, v in domains.items()
        },
        "within_arrival": {
            "r1_gpt41": round(r1_correct/n, 4),
            "r2_gemini3flash": round(r2_correct/n, 4),
            "r3_grok41": round(r3_correct/n, 4),
        },
        "flip_rates": {
            "r1_r2": round(flips_12/n, 4),
            "r2_r3": round(flips_23/n, 4),
            "r3_r4": round(flips_34/n, 4),
        },
        "crdt_metrics": {
            "avg_care_resolve": round(avg_care, 4) if care_scores else None,
            "avg_meaning_debt": round(avg_debt, 4) if debt_scores else None,
        },
        "cost": {
            "arrival": round(ar_cost, 4),
            "solo_gpt41": round(gpt_cost, 4),
            "solo_gemini3flash": round(gemini_cost, 4),
            "solo_grok41": round(grok_cost, 4),
            "total": round(total_cost, 4),
        },
    }

    eval_file = os.path.join(RESULTS_DIR, "evaluation.json")
    with open(eval_file, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, ensure_ascii=False, indent=2)
    print(f"\n  Evaluation saved: {eval_file}")

    print("\n" + "=" * 70)
    print("  PHASE 21 EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
