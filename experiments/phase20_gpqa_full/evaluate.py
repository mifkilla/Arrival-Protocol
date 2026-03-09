# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 20: Statistical Evaluation

Compares ARRIVAL vs Solo CoT on full GPQA Diamond (198 questions).
- McNemar test (ARRIVAL R4 vs MV of R1-R3)
- McNemar test (ARRIVAL R4 vs Solo CoT MV)
- Fisher exact test (backup)
- Per-domain breakdown
- Rescue/regression rates
- 40-question consistency check with Phase 13 (by question TEXT, not letter)
- Wilson score confidence intervals

Usage:
    python evaluate.py
"""

import json
import math
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# Phase 13 data for consistency check
PHASE13_QUESTIONS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "phase13_gpqa", "phase_13", "questions_gpqa.py"
)


# ============================================================
# Statistical tests
# ============================================================
def mcnemar_test(b, c):
    """McNemar's test with continuity correction. b=MV_right_AR_wrong, c=MV_wrong_AR_right."""
    if b + c == 0:
        return {"chi2": 0, "p_value": 1.0, "significant": False}
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    # chi2 with 1 df: p = erfc(sqrt(chi2/2))
    p_value = math.erfc(math.sqrt(chi2 / 2))
    return {
        "chi2": round(chi2, 4),
        "p_value": round(p_value, 6),
        "b_right_wrong": b,
        "c_wrong_right": c,
        "significant_005": p_value < 0.05,
        "significant_001": p_value < 0.01,
    }


def fisher_exact_2x2(a, b, c, d):
    """Fisher's exact test for 2x2 contingency table (two-sided)."""
    n = a + b + c + d
    if n == 0:
        return 1.0

    def log_fact(k):
        return sum(math.log(i) for i in range(1, k + 1)) if k > 0 else 0.0

    log_p_obs = (
        log_fact(a + b) + log_fact(c + d) + log_fact(a + c) + log_fact(b + d)
        - log_fact(n) - log_fact(a) - log_fact(b) - log_fact(c) - log_fact(d)
    )
    p_obs = math.exp(log_p_obs)
    p_value = 0.0
    row1, row2, col1 = a + b, c + d, a + c
    for i in range(min(row1, col1) + 1):
        j = row1 - i
        k = col1 - i
        l_val = row2 - k
        if j < 0 or k < 0 or l_val < 0:
            continue
        log_p = (
            log_fact(row1) + log_fact(row2) + log_fact(col1) + log_fact(j + l_val)
            - log_fact(n) - log_fact(i) - log_fact(j) - log_fact(k) - log_fact(l_val)
        )
        p_i = math.exp(log_p)
        if p_i <= p_obs * 1.0001:
            p_value += p_i
    return min(1.0, round(p_value, 6))


def wilson_ci(k, n, z=1.96):
    """Wilson score confidence interval for binomial proportion."""
    if n == 0:
        return (0, 0)
    p_hat = k / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return (round(max(0, center - spread), 4), round(min(1, center + spread), 4))


# ============================================================
# Load Phase 13 questions for consistency check
# ============================================================
def load_phase13_questions():
    """Load Phase 13's 40 questions by parsing questions_gpqa.py."""
    try:
        # Import from module
        p13_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "phase13_gpqa"
        )
        sys.path.insert(0, p13_dir)
        from phase_13.questions_gpqa import QUESTIONS as P13_QUESTIONS
        return P13_QUESTIONS
    except ImportError:
        print("  WARNING: Could not load Phase 13 questions for consistency check")
        return []


def match_questions_by_text(p13_questions, p20_arrival, p20_solo):
    """Match Phase 13 questions to Phase 20 results by question text.
    Returns list of matched questions with both Phase 13 and Phase 20 answers."""
    matched = []
    # Build text->result lookups for Phase 20
    p20_arrival_by_text = {}
    for r in p20_arrival:
        # Use first 200 chars of question text as key (enough for unique matching)
        key = r.get("question_text", "")[:200] if "question_text" in r else ""
        p20_arrival_by_text[key] = r

    p20_solo_by_text = {}
    for r in p20_solo:
        key = r.get("question_text", "")[:200] if "question_text" in r else ""
        p20_solo_by_text[key] = r

    # Also try matching by question_id patterns
    p20_arrival_by_id = {r["question_id"]: r for r in p20_arrival}
    p20_solo_by_id = {r["question_id"]: r for r in p20_solo}

    for p13q in p13_questions:
        p13_text = p13q["question"][:200]
        p13_correct_letter = p13q["correct"]
        p13_correct_text = p13q["choices"].get(p13_correct_letter, "")

        # Try text match first, then ID match
        ar_result = p20_arrival_by_text.get(p13_text)
        solo_result = p20_solo_by_text.get(p13_text)

        # Fallback: search all P20 results for question text overlap
        if ar_result is None:
            for r in p20_arrival:
                # Match by checking if correct answer text matches
                if r.get("correct_answer_text", "").strip() == p13_correct_text.strip():
                    # Double-check with question text similarity
                    ar_result = r
                    break

        if solo_result is None:
            for r in p20_solo:
                if r.get("correct_answer_text", "").strip() == p13_correct_text.strip():
                    solo_result = r
                    break

        if ar_result or solo_result:
            matched.append({
                "p13_id": p13q["id"],
                "p13_domain": p13q["domain"],
                "p13_correct_text": p13_correct_text,
                "p20_arrival_correct": ar_result.get("correct_arrival") if ar_result else None,
                "p20_mv_correct": ar_result.get("correct_mv") if ar_result else None,
                "p20_solo_mv_correct": solo_result.get("majority_vote", {}).get("correct") if solo_result else None,
            })

    return matched


# ============================================================
# Main evaluation
# ============================================================
def main():
    # Load results
    arrival_path = os.path.join(RESULTS_DIR, "arrival_results.json")
    solo_path = os.path.join(RESULTS_DIR, "solo_cot_results.json")

    if not os.path.exists(arrival_path):
        print(f"ERROR: {arrival_path} not found. Run run_arrival.py first.")
        return
    if not os.path.exists(solo_path):
        print(f"ERROR: {solo_path} not found. Run run_solo_cot.py first.")
        return

    with open(arrival_path, "r", encoding="utf-8") as f:
        arrival_data = json.load(f)
    with open(solo_path, "r", encoding="utf-8") as f:
        solo_data = json.load(f)

    ar_questions = arrival_data["questions"]
    solo_questions = solo_data["questions"]

    print("=" * 70)
    print("  ARRIVAL Protocol -- Phase 20: Statistical Evaluation")
    print("=" * 70)
    print(f"  ARRIVAL results: {len(ar_questions)} questions")
    print(f"  Solo CoT results: {len(solo_questions)} questions")

    # ---- Build comparison table ----
    # Match ARRIVAL and Solo results by question_id
    solo_by_id = {q["question_id"]: q for q in solo_questions}
    matched_ids = [q["question_id"] for q in ar_questions if q["question_id"] in solo_by_id]
    n_matched = len(matched_ids)
    print(f"  Matched questions: {n_matched}")

    # ---- 1. ARRIVAL R4 accuracy ----
    ar_correct = sum(1 for q in ar_questions if q.get("correct_arrival"))
    ar_n = len(ar_questions)
    ar_acc = ar_correct / ar_n if ar_n else 0
    ar_ci = wilson_ci(ar_correct, ar_n)

    # ---- 2. MV of R1-R3 accuracy ----
    mv_correct = sum(1 for q in ar_questions if q.get("correct_mv"))
    mv_acc = mv_correct / ar_n if ar_n else 0
    mv_ci = wilson_ci(mv_correct, ar_n)

    # ---- 3. Solo CoT MV accuracy ----
    solo_mv_correct = sum(1 for q in solo_questions if q.get("majority_vote", {}).get("correct"))
    solo_n = len(solo_questions)
    solo_mv_acc = solo_mv_correct / solo_n if solo_n else 0
    solo_ci = wilson_ci(solo_mv_correct, solo_n)

    # ---- 4. Solo CoT per-run accuracy ----
    solo_run_correct = sum(
        sum(1 for r in q.get("runs", []) if r.get("correct"))
        for q in solo_questions
    )
    solo_run_total = sum(len(q.get("runs", [])) for q in solo_questions)
    solo_run_acc = solo_run_correct / solo_run_total if solo_run_total else 0

    # ---- 5. Solo CoT oracle ----
    solo_oracle_correct = sum(1 for q in solo_questions if q.get("oracle", {}).get("correct"))
    solo_oracle_acc = solo_oracle_correct / solo_n if solo_n else 0

    print(f"\n  ---- ACCURACY ----")
    print(f"  ARRIVAL R4:          {ar_acc*100:.1f}% ({ar_correct}/{ar_n})  95% CI: [{ar_ci[0]*100:.1f}%, {ar_ci[1]*100:.1f}%]")
    print(f"  ARRIVAL MV (R1-R3):  {mv_acc*100:.1f}% ({mv_correct}/{ar_n})  95% CI: [{mv_ci[0]*100:.1f}%, {mv_ci[1]*100:.1f}%]")
    print(f"  Solo CoT MV:         {solo_mv_acc*100:.1f}% ({solo_mv_correct}/{solo_n})  95% CI: [{solo_ci[0]*100:.1f}%, {solo_ci[1]*100:.1f}%]")
    print(f"  Solo CoT per-run:    {solo_run_acc*100:.1f}% ({solo_run_correct}/{solo_run_total})")
    print(f"  Solo CoT oracle:     {solo_oracle_acc*100:.1f}% ({solo_oracle_correct}/{solo_n})")

    # ---- McNemar: ARRIVAL R4 vs MV R1-R3 ----
    # Paired on the same questions
    b_mv_right_ar_wrong = 0  # MV correct, ARRIVAL wrong
    c_mv_wrong_ar_right = 0  # MV wrong, ARRIVAL correct (rescues)
    a_both_right = 0
    d_both_wrong = 0
    for q in ar_questions:
        mv_ok = q.get("correct_mv", False)
        ar_ok = q.get("correct_arrival", False)
        if mv_ok and ar_ok:
            a_both_right += 1
        elif mv_ok and not ar_ok:
            b_mv_right_ar_wrong += 1
        elif not mv_ok and ar_ok:
            c_mv_wrong_ar_right += 1
        else:
            d_both_wrong += 1

    mcnemar_ar_mv = mcnemar_test(b_mv_right_ar_wrong, c_mv_wrong_ar_right)

    print(f"\n  ---- McNEMAR: ARRIVAL R4 vs MV (R1-R3) ----")
    print(f"  Both correct:    {a_both_right}")
    print(f"  MV right, AR wrong (regressions):  {b_mv_right_ar_wrong}")
    print(f"  MV wrong, AR right (rescues):      {c_mv_wrong_ar_right}")
    print(f"  Both wrong:      {d_both_wrong}")
    print(f"  McNemar chi2:    {mcnemar_ar_mv['chi2']}")
    print(f"  McNemar p:       {mcnemar_ar_mv['p_value']}")
    sig = "***" if mcnemar_ar_mv['p_value'] < 0.001 else "**" if mcnemar_ar_mv['p_value'] < 0.01 else "*" if mcnemar_ar_mv['p_value'] < 0.05 else "ns"
    print(f"  Significance:    {sig}")

    # ---- McNemar: ARRIVAL R4 vs Solo CoT MV ----
    b2 = 0  # Solo right, ARRIVAL wrong
    c2 = 0  # Solo wrong, ARRIVAL right
    a2 = 0
    d2 = 0
    for qid in matched_ids:
        ar_q = next(q for q in ar_questions if q["question_id"] == qid)
        solo_q = solo_by_id[qid]
        ar_ok = ar_q.get("correct_arrival", False)
        solo_ok = solo_q.get("majority_vote", {}).get("correct", False)
        if solo_ok and ar_ok:
            a2 += 1
        elif solo_ok and not ar_ok:
            b2 += 1
        elif not solo_ok and ar_ok:
            c2 += 1
        else:
            d2 += 1

    mcnemar_ar_solo = mcnemar_test(b2, c2)

    print(f"\n  ---- McNEMAR: ARRIVAL R4 vs Solo CoT MV ----")
    print(f"  Both correct:           {a2}")
    print(f"  Solo right, AR wrong:   {b2}")
    print(f"  Solo wrong, AR right:   {c2}")
    print(f"  Both wrong:             {d2}")
    print(f"  McNemar chi2:           {mcnemar_ar_solo['chi2']}")
    print(f"  McNemar p:              {mcnemar_ar_solo['p_value']}")
    sig2 = "***" if mcnemar_ar_solo['p_value'] < 0.001 else "**" if mcnemar_ar_solo['p_value'] < 0.01 else "*" if mcnemar_ar_solo['p_value'] < 0.05 else "ns"
    print(f"  Significance:           {sig2}")

    # ---- Fisher exact tests (backup) ----
    fisher_ar_mv = fisher_exact_2x2(ar_correct, ar_n - ar_correct, mv_correct, ar_n - mv_correct)
    fisher_ar_solo = fisher_exact_2x2(ar_correct, ar_n - ar_correct, solo_mv_correct, solo_n - solo_mv_correct)

    print(f"\n  ---- FISHER EXACT (backup) ----")
    print(f"  ARRIVAL vs MV:    p={fisher_ar_mv}")
    print(f"  ARRIVAL vs Solo:  p={fisher_ar_solo}")

    # ---- Rescue and regression rates ----
    rescue_rate = c_mv_wrong_ar_right / (ar_n - mv_correct) if (ar_n - mv_correct) > 0 else 0
    regression_rate = b_mv_right_ar_wrong / mv_correct if mv_correct > 0 else 0

    print(f"\n  ---- RESCUE / REGRESSION ----")
    print(f"  Rescues (MV wrong -> AR right):    {c_mv_wrong_ar_right} ({rescue_rate*100:.1f}% of MV errors)")
    print(f"  Regressions (MV right -> AR wrong):{b_mv_right_ar_wrong} ({regression_rate*100:.1f}% of MV successes)")

    # ---- Per-domain breakdown ----
    domains = {}
    for q in ar_questions:
        d = q["domain"]
        if d not in domains:
            domains[d] = {"ar": 0, "mv": 0, "total": 0}
        domains[d]["total"] += 1
        if q.get("correct_arrival"):
            domains[d]["ar"] += 1
        if q.get("correct_mv"):
            domains[d]["mv"] += 1

    solo_domains = {}
    for q in solo_questions:
        d = q["domain"]
        if d not in solo_domains:
            solo_domains[d] = {"correct": 0, "total": 0}
        solo_domains[d]["total"] += 1
        if q.get("majority_vote", {}).get("correct"):
            solo_domains[d]["correct"] += 1

    print(f"\n  ---- PER-DOMAIN ----")
    print(f"  {'Domain':20s} {'AR R4':>8s} {'MV R1-3':>8s} {'Solo MV':>8s} {'n':>5s}")
    for d in sorted(set(list(domains.keys()) + list(solo_domains.keys()))):
        ar_a = domains.get(d, {}).get("ar", 0) / domains.get(d, {}).get("total", 1) * 100
        mv_a = domains.get(d, {}).get("mv", 0) / domains.get(d, {}).get("total", 1) * 100
        solo_a = solo_domains.get(d, {}).get("correct", 0) / solo_domains.get(d, {}).get("total", 1) * 100
        n_d = domains.get(d, {}).get("total", 0)
        print(f"  {d:20s} {ar_a:7.1f}% {mv_a:7.1f}% {solo_a:7.1f}% {n_d:5d}")

    # ---- CARE metrics ----
    care_scores = [q["care_resolve"] for q in ar_questions if q.get("care_resolve") is not None]
    debt_scores = [q["meaning_debt"] for q in ar_questions if q.get("meaning_debt") is not None]
    avg_care = sum(care_scores) / len(care_scores) if care_scores else 0
    avg_debt = sum(debt_scores) / len(debt_scores) if debt_scores else 0

    print(f"\n  ---- CRDT METRICS ----")
    print(f"  Avg CARE Resolve:    {avg_care:.3f}")
    print(f"  Avg Meaning Debt:    {avg_debt:.3f}")

    # ---- R1->R2->R3 flip rates ----
    flip_r1r2 = 0
    flip_r2r3 = 0
    flip_r3r4 = 0
    for q in ar_questions:
        r1 = q.get("r1_answer")
        r2 = q.get("r2_answer")
        r3 = q.get("r3_answer")
        r4 = q.get("r4_final")
        if r1 and r2 and r1 != r2:
            flip_r1r2 += 1
        if r2 and r3 and r2 != r3:
            flip_r2r3 += 1
        if r3 and r4 and r3 != r4:
            flip_r3r4 += 1

    print(f"\n  ---- FLIP RATES ----")
    print(f"  R1->R2 flips:  {flip_r1r2}/{ar_n} ({flip_r1r2/ar_n*100:.1f}%)")
    print(f"  R2->R3 flips:  {flip_r2r3}/{ar_n} ({flip_r2r3/ar_n*100:.1f}%)")
    print(f"  R3->R4 flips:  {flip_r3r4}/{ar_n} ({flip_r3r4/ar_n*100:.1f}%)")

    # ---- 40-question consistency check ----
    print(f"\n  ---- 40-QUESTION CONSISTENCY CHECK (Phase 13) ----")
    p13_questions = load_phase13_questions()
    if p13_questions:
        print(f"  Phase 13 questions loaded: {len(p13_questions)}")
        matched = match_questions_by_text(p13_questions, ar_questions, solo_questions)
        print(f"  Matched with Phase 20: {len(matched)}")

        if matched:
            p20_ar_correct = sum(1 for m in matched if m.get("p20_arrival_correct"))
            p20_mv_correct = sum(1 for m in matched if m.get("p20_mv_correct"))
            p20_solo_correct = sum(1 for m in matched if m.get("p20_solo_mv_correct"))
            n_m = len(matched)

            p20_ar_acc = p20_ar_correct / n_m if n_m else 0
            p20_mv_acc = p20_mv_correct / n_m if n_m else 0
            p20_solo_acc = p20_solo_correct / n_m if n_m else 0

            # Phase 13 Alpha trio: AR=63.8% -> 26/40 on alpha trio
            p13_ar_acc = 0.650  # 26/40 alpha trio
            p13_mv_acc = 0.525  # 21/40 alpha trio

            delta_ar = abs(p20_ar_acc - p13_ar_acc) * 100
            delta_mv = abs(p20_mv_acc - p13_mv_acc) * 100

            print(f"  Phase 20 ARRIVAL on subset:  {p20_ar_acc*100:.1f}% ({p20_ar_correct}/{n_m})")
            print(f"  Phase 20 MV on subset:       {p20_mv_acc*100:.1f}% ({p20_mv_correct}/{n_m})")
            print(f"  Phase 20 Solo MV on subset:  {p20_solo_acc*100:.1f}% ({p20_solo_correct}/{n_m})")
            print(f"  Phase 13 ARRIVAL (alpha):    {p13_ar_acc*100:.1f}%")
            print(f"  Phase 13 MV (alpha):         {p13_mv_acc*100:.1f}%")
            print(f"  Delta ARRIVAL:               {delta_ar:.1f} pp {'WARNING' if delta_ar > 15 else 'OK'} {'CRITICAL' if delta_ar > 25 else ''}")
            print(f"  Delta MV:                    {delta_mv:.1f} pp {'WARNING' if delta_mv > 15 else 'OK'} {'CRITICAL' if delta_mv > 25 else ''}")
    else:
        print("  SKIPPED: Could not load Phase 13 questions")

    # ---- Cost summary ----
    ar_cost = arrival_data.get("summary", {}).get("cost_usd", 0)
    solo_cost = solo_data.get("summary", {}).get("cost_usd", 0)

    print(f"\n  ---- COST SUMMARY ----")
    print(f"  ARRIVAL total:     ${ar_cost:.2f}")
    print(f"  Solo CoT total:    ${solo_cost:.2f}")
    print(f"  Grand total:       ${ar_cost + solo_cost:.2f}")
    print(f"  ARRIVAL per-q:     ${ar_cost / ar_n:.4f}" if ar_n else "  ARRIVAL per-q:     N/A")
    print(f"  Solo CoT per-q:    ${solo_cost / solo_n:.4f}" if solo_n else "  Solo CoT per-q:    N/A")

    # ---- Save evaluation ----
    evaluation = {
        "phase": 20,
        "timestamp": datetime.now().isoformat(),
        "n_arrival": ar_n,
        "n_solo": solo_n,
        "n_matched": n_matched,
        "accuracy": {
            "arrival_r4": {"value": ar_acc, "correct": ar_correct, "total": ar_n, "ci_95": ar_ci},
            "arrival_mv": {"value": mv_acc, "correct": mv_correct, "total": ar_n, "ci_95": mv_ci},
            "solo_cot_mv": {"value": solo_mv_acc, "correct": solo_mv_correct, "total": solo_n, "ci_95": solo_ci},
            "solo_cot_per_run": {"value": solo_run_acc, "correct": solo_run_correct, "total": solo_run_total},
            "solo_cot_oracle": {"value": solo_oracle_acc, "correct": solo_oracle_correct, "total": solo_n},
        },
        "mcnemar_arrival_vs_mv": mcnemar_ar_mv,
        "mcnemar_arrival_vs_solo": mcnemar_ar_solo,
        "fisher_arrival_vs_mv": fisher_ar_mv,
        "fisher_arrival_vs_solo": fisher_ar_solo,
        "contingency_arrival_vs_mv": {
            "both_correct": a_both_right, "mv_right_ar_wrong": b_mv_right_ar_wrong,
            "mv_wrong_ar_right": c_mv_wrong_ar_right, "both_wrong": d_both_wrong,
        },
        "contingency_arrival_vs_solo": {
            "both_correct": a2, "solo_right_ar_wrong": b2,
            "solo_wrong_ar_right": c2, "both_wrong": d2,
        },
        "rescue_rate": rescue_rate,
        "regression_rate": regression_rate,
        "flip_rates": {
            "r1_r2": flip_r1r2 / ar_n if ar_n else 0,
            "r2_r3": flip_r2r3 / ar_n if ar_n else 0,
            "r3_r4": flip_r3r4 / ar_n if ar_n else 0,
        },
        "crdt": {
            "avg_care_resolve": avg_care,
            "avg_meaning_debt": avg_debt,
        },
        "per_domain": {
            d: {
                "arrival_accuracy": domains.get(d, {}).get("ar", 0) / domains.get(d, {}).get("total", 1),
                "mv_accuracy": domains.get(d, {}).get("mv", 0) / domains.get(d, {}).get("total", 1),
                "solo_accuracy": solo_domains.get(d, {}).get("correct", 0) / solo_domains.get(d, {}).get("total", 1),
                "n": domains.get(d, {}).get("total", 0),
            }
            for d in sorted(set(list(domains.keys()) + list(solo_domains.keys())))
        },
        "cost": {
            "arrival_usd": ar_cost,
            "solo_cot_usd": solo_cost,
            "total_usd": ar_cost + solo_cost,
        },
    }

    eval_path = os.path.join(RESULTS_DIR, "evaluation.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)

    print(f"\n  Evaluation saved: {eval_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
