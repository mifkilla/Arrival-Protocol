# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 23 Evaluation: Statistical analysis of CGD-7 results (7 models).

Computes:
  1. Per-model solo accuracy ranking
  2. Simple MV vs Weighted MV vs CGD-7
  3. McNemar test: CGD-7 vs Phase 22 CGD (3 models)
  4. Oracle ceiling analysis
  5. Minority-was-right analysis (per model)
  6. Cross-vendor diversity analysis (Chinese 4 vs American 3)
  7. Cost efficiency analysis
  8. Per-domain breakdown

Usage:
    python evaluate.py
    python evaluate.py --cgd7 results/cgd7_results.json
    python evaluate.py --phase22 ../phase22_confidence_gated/results/cgd_full_results.json
"""

import json
import os
import sys
import argparse
from collections import Counter

# Windows encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
PHASE22_RESULTS = os.path.join(SCRIPT_DIR, "..", "phase22_confidence_gated", "results", "cgd_full_results.json")

MODEL_KEYS = ["grok", "gemini", "qwen", "deepseek", "glm", "kimi", "claude"]

# Vendor classification
VENDOR_GROUPS = {
    "american": ["grok", "gemini", "claude"],       # xAI, Google, Anthropic
    "chinese": ["qwen", "deepseek", "glm", "kimi"], # Alibaba, DeepSeek, Zhipu, Moonshot
}

MODEL_INFO = {
    "grok": {"vendor": "xAI", "country": "US", "short": "Grok4.1"},
    "gemini": {"vendor": "Google", "country": "US", "short": "Gemini3Flash"},
    "qwen": {"vendor": "Alibaba", "country": "CN", "short": "Qwen3.5-397B"},
    "deepseek": {"vendor": "DeepSeek", "country": "CN", "short": "DeepSeekV3.2"},
    "glm": {"vendor": "Zhipu AI", "country": "CN", "short": "GLM5"},
    "kimi": {"vendor": "Moonshot AI", "country": "CN", "short": "KimiK2.5"},
    "claude": {"vendor": "Anthropic", "country": "US", "short": "ClaudeSonnet4.6"},
}


def mcnemar_test(correct_a, correct_b, n):
    """McNemar test for paired binary data. Returns chi2, p-value."""
    # Build contingency table
    both_correct = sum(a and b for a, b in zip(correct_a, correct_b))
    a_only = sum(a and not b for a, b in zip(correct_a, correct_b))
    b_only = sum(not a and b for a, b in zip(correct_a, correct_b))
    both_wrong = sum(not a and not b for a, b in zip(correct_a, correct_b))

    # McNemar chi-squared (with continuity correction)
    if a_only + b_only == 0:
        return 0.0, 1.0, {"both_correct": both_correct, "a_only": a_only,
                           "b_only": b_only, "both_wrong": both_wrong}

    chi2 = (abs(a_only - b_only) - 1) ** 2 / (a_only + b_only)

    # Chi-squared p-value (1 df) approximation
    import math
    if chi2 == 0:
        p = 1.0
    else:
        # Simple approximation for chi2 with 1 df
        p = math.erfc(math.sqrt(chi2 / 2))

    return chi2, p, {"both_correct": both_correct, "a_only": a_only,
                      "b_only": b_only, "both_wrong": both_wrong}


def evaluate_cgd7(cgd7_path, phase22_path=None):
    """Full evaluation of CGD-7 results."""
    with open(cgd7_path, "r", encoding="utf-8") as f:
        cgd7 = json.load(f)

    results = cgd7["questions"]
    weights = cgd7.get("weights", {})
    n = len(results)

    print("=" * 70)
    print(f"  PHASE 23 CGD-7 EVALUATION")
    print(f"  {n} questions, {len(MODEL_KEYS)} models")
    print("=" * 70)

    # ============================================================
    # 1. Per-model solo accuracy
    # ============================================================
    print("\n1. PER-MODEL SOLO ACCURACY")
    print("-" * 50)
    model_acc = {}
    for mk in MODEL_KEYS:
        correct = sum(1 for r in results if r.get(f"solo_{mk}") == r["correct_answer"])
        nones = sum(1 for r in results if r.get(f"solo_{mk}") is None)
        acc = correct / n if n else 0
        model_acc[mk] = {"correct": correct, "total": n, "accuracy": acc, "nones": nones}

    # Sort by accuracy
    ranked = sorted(model_acc.items(), key=lambda x: -x[1]["accuracy"])
    for rank, (mk, info) in enumerate(ranked, 1):
        mi = MODEL_INFO[mk]
        flag = "US" if mi["country"] == "US" else "CN"
        none_str = f" ({info['nones']} None)" if info["nones"] else ""
        weight_str = f" w={weights.get(mk, 0):.3f}" if weights else ""
        print(f"  #{rank} {mi['short']:20s} [{flag}] {info['correct']}/{n} = {info['accuracy']*100:.1f}%{none_str}{weight_str}")

    # ============================================================
    # 2. Voting strategies comparison
    # ============================================================
    print("\n2. VOTING STRATEGIES COMPARISON")
    print("-" * 50)

    # a) Simple MV (unweighted)
    simple_mv_correct = 0
    simple_mv_answers = []
    for r in results:
        votes = [r.get(f"solo_{mk}") for mk in MODEL_KEYS if r.get(f"solo_{mk}")]
        mv = Counter(votes).most_common(1)[0][0] if votes else None
        simple_mv_answers.append(mv)
        if mv == r["correct_answer"]:
            simple_mv_correct += 1

    # b) Weighted MV
    weighted_mv_correct = 0
    weighted_mv_answers = []
    for r in results:
        vote_scores = Counter()
        for mk in MODEL_KEYS:
            ans = r.get(f"solo_{mk}")
            if ans:
                vote_scores[ans] += weights.get(mk, 0.5)
        wmv = vote_scores.most_common(1)[0][0] if vote_scores else None
        weighted_mv_answers.append(wmv)
        if wmv == r["correct_answer"]:
            weighted_mv_correct += 1

    # c) CGD-7
    cgd7_correct = sum(1 for r in results if r["correct"])

    # d) Best solo
    best_mk = ranked[0][0]
    best_solo_correct = model_acc[best_mk]["correct"]

    # e) Oracle
    oracle_correct = sum(
        1 for r in results
        if r["correct_answer"] in [r.get(f"solo_{mk}") for mk in MODEL_KEYS]
    )

    strategies = [
        ("Best solo ({})".format(MODEL_INFO[best_mk]["short"]), best_solo_correct),
        ("Simple MV ({} models)".format(len(MODEL_KEYS)), simple_mv_correct),
        ("Weighted MV ({} models)".format(len(MODEL_KEYS)), weighted_mv_correct),
        ("CGD-7 (debate on disagreement)", cgd7_correct),
        ("Oracle (any model correct)", oracle_correct),
    ]

    for name, correct in strategies:
        print(f"  {name:45s}: {correct}/{n} = {correct/n*100:.1f}%")

    # ============================================================
    # 3. Debate type breakdown
    # ============================================================
    print("\n3. DEBATE TYPE BREAKDOWN")
    print("-" * 50)
    dt_counts = Counter(r["debate_type"] for r in results)
    for dt, count in dt_counts.most_common():
        dt_results = [r for r in results if r["debate_type"] == dt]
        dt_correct = sum(1 for r in dt_results if r["correct"])
        print(f"  {dt:25s}: {count:3d} ({count/n*100:.0f}%) | {dt_correct}/{count} = {dt_correct/count*100:.1f}% acc")

    # ============================================================
    # 4. Cross-vendor diversity analysis
    # ============================================================
    print("\n4. CROSS-VENDOR DIVERSITY (Chinese vs American)")
    print("-" * 50)

    for group, models in VENDOR_GROUPS.items():
        grp_oracle = sum(
            1 for r in results
            if r["correct_answer"] in [r.get(f"solo_{mk}") for mk in models]
        )
        grp_mv = 0
        for r in results:
            votes = [r.get(f"solo_{mk}") for mk in models if r.get(f"solo_{mk}")]
            mv = Counter(votes).most_common(1)[0][0] if votes else None
            if mv == r["correct_answer"]:
                grp_mv += 1
        print(f"  {group.upper():10s} ({len(models)} models):")
        print(f"    Oracle: {grp_oracle}/{n} = {grp_oracle/n*100:.1f}%")
        print(f"    MV:     {grp_mv}/{n} = {grp_mv/n*100:.1f}%")
        for mk in models:
            mi = MODEL_INFO[mk]
            acc = model_acc[mk]["accuracy"]
            print(f"      {mi['short']:20s}: {acc*100:.1f}%")

    # Diversity metric: how often do groups disagree?
    cross_diversity = 0
    same_diversity = 0
    for r in results:
        us_votes = [r.get(f"solo_{mk}") for mk in VENDOR_GROUPS["american"] if r.get(f"solo_{mk}")]
        cn_votes = [r.get(f"solo_{mk}") for mk in VENDOR_GROUPS["chinese"] if r.get(f"solo_{mk}")]
        if us_votes and cn_votes:
            us_mv = Counter(us_votes).most_common(1)[0][0]
            cn_mv = Counter(cn_votes).most_common(1)[0][0]
            if us_mv != cn_mv:
                cross_diversity += 1

    print(f"\n  Cross-vendor disagreement: {cross_diversity}/{n} = {cross_diversity/n*100:.1f}%")
    print(f"  (US-MV != CN-MV on these questions)")

    # ============================================================
    # 5. Minority-was-right analysis
    # ============================================================
    print("\n5. MINORITY-WAS-RIGHT ANALYSIS")
    print("-" * 50)
    for mk in MODEL_KEYS:
        minority_correct = 0
        minority_total = 0
        for r in results:
            solo_ans = r.get(f"solo_{mk}")
            if solo_ans is None:
                continue
            # Was this model in the minority?
            all_votes = [r.get(f"solo_{m}") for m in MODEL_KEYS if r.get(f"solo_{m}")]
            mv = Counter(all_votes).most_common(1)[0][0] if all_votes else None
            if solo_ans != mv:
                minority_total += 1
                if solo_ans == r["correct_answer"]:
                    minority_correct += 1
        mi = MODEL_INFO[mk]
        if minority_total > 0:
            print(f"  {mi['short']:20s}: minority {minority_total} times, correct {minority_correct} ({minority_correct/minority_total*100:.0f}%)")
        else:
            print(f"  {mi['short']:20s}: never in minority")

    # ============================================================
    # 6. Per-domain breakdown
    # ============================================================
    print("\n6. PER-DOMAIN BREAKDOWN")
    print("-" * 50)
    domains = sorted(set(r["domain"] for r in results))
    for dom in domains:
        dom_results = [r for r in results if r["domain"] == dom]
        dom_n = len(dom_results)
        dom_correct = sum(1 for r in dom_results if r["correct"])
        # Per-model in this domain
        model_strs = []
        for mk in MODEL_KEYS:
            mc = sum(1 for r in dom_results if r.get(f"solo_{mk}") == r["correct_answer"])
            model_strs.append(f"{MODEL_INFO[mk]['short'][:4]}={mc/dom_n*100:.0f}%")
        print(f"  {dom:15s}: CGD={dom_correct}/{dom_n}={dom_correct/dom_n*100:.1f}% | {' '.join(model_strs)}")

    # ============================================================
    # 7. McNemar vs Phase 22
    # ============================================================
    if phase22_path and os.path.exists(phase22_path):
        print("\n7. McNEMAR TEST: CGD-7 vs Phase 22 CGD (3 models)")
        print("-" * 50)

        with open(phase22_path, "r", encoding="utf-8") as f:
            p22 = json.load(f)

        p22_results = p22["questions"]
        p22_by_id = {r["question_id"]: r for r in p22_results}

        # Align by question_id
        aligned_cgd7 = []
        aligned_p22 = []
        for r in results:
            qid = r["question_id"]
            if qid in p22_by_id:
                aligned_cgd7.append(r["correct"])
                aligned_p22.append(p22_by_id[qid]["correct"])

        n_aligned = len(aligned_cgd7)
        if n_aligned > 0:
            cgd7_acc = sum(aligned_cgd7) / n_aligned
            p22_acc = sum(aligned_p22) / n_aligned

            chi2, p, table = mcnemar_test(aligned_cgd7, aligned_p22, n_aligned)

            print(f"  Aligned questions: {n_aligned}")
            print(f"  Phase 22 CGD (3 models): {sum(aligned_p22)}/{n_aligned} = {p22_acc*100:.1f}%")
            print(f"  Phase 23 CGD-7 (7 models): {sum(aligned_cgd7)}/{n_aligned} = {cgd7_acc*100:.1f}%")
            print(f"  Improvement: +{(cgd7_acc - p22_acc)*100:.1f}pp")
            print(f"  McNemar chi2={chi2:.3f}, p={p:.4f}")
            print(f"  Contingency: both_correct={table['both_correct']}, "
                  f"only_CGD7={table['a_only']}, only_P22={table['b_only']}, "
                  f"both_wrong={table['both_wrong']}")

            sig = "SIGNIFICANT" if p < 0.05 else "not significant"
            print(f"  Result: {sig} (p {'<' if p < 0.05 else '>'} 0.05)")

    # ============================================================
    # 8. Cost analysis
    # ============================================================
    print("\n8. COST ANALYSIS")
    print("-" * 50)
    total_cost = sum(r.get("cost_usd", 0) for r in results)
    total_calls = sum(r.get("api_calls", 0) for r in results)
    cost_per_q = total_cost / n if n else 0
    print(f"  Total cost: ${total_cost:.2f}")
    print(f"  Total API calls: {total_calls}")
    print(f"  Cost per question: ${cost_per_q:.3f}")
    print(f"  Cost per correct answer: ${total_cost / cgd7_correct:.3f}" if cgd7_correct else "  N/A")

    # ============================================================
    # Save evaluation
    # ============================================================
    eval_data = {
        "phase": "Phase 23 Evaluation",
        "n_questions": n,
        "per_model_accuracy": {mk: model_acc[mk] for mk in MODEL_KEYS},
        "strategies": {name: {"correct": c, "total": n, "accuracy": round(c/n, 4)} for name, c in strategies},
        "debate_breakdown": {
            dt: {"n": count, "correct": sum(1 for r in results if r["debate_type"] == dt and r["correct"]),
                 "accuracy": round(sum(1 for r in results if r["debate_type"] == dt and r["correct"]) / count, 4)}
            for dt, count in dt_counts.items()
        },
        "cross_vendor": {
            group: {
                "models": models,
                "oracle": sum(1 for r in results if r["correct_answer"] in [r.get(f"solo_{mk}") for mk in models]),
                "oracle_accuracy": round(sum(1 for r in results if r["correct_answer"] in [r.get(f"solo_{mk}") for mk in models]) / n, 4),
            }
            for group, models in VENDOR_GROUPS.items()
        },
        "cross_vendor_disagreement": cross_diversity,
        "cost": {"total_usd": round(total_cost, 4), "per_question": round(cost_per_q, 4), "total_calls": total_calls},
    }

    eval_path = os.path.join(RESULTS_DIR, "evaluation.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)
    print(f"\n  Evaluation saved to: {eval_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 23 Evaluation")
    parser.add_argument("--cgd7", type=str, default=os.path.join(RESULTS_DIR, "cgd7_results.json"))
    parser.add_argument("--phase22", type=str, default=PHASE22_RESULTS)
    args = parser.parse_args()

    if not os.path.exists(args.cgd7):
        # Try solo baselines instead
        solo_path = os.path.join(RESULTS_DIR, "solo_baselines_20q.json")
        if os.path.exists(solo_path):
            print(f"CGD-7 results not found. Evaluating solo baselines from: {solo_path}")
            evaluate_solo_baselines(solo_path)
            return
        print(f"ERROR: No results found at {args.cgd7}")
        sys.exit(1)

    evaluate_cgd7(args.cgd7, args.phase22)


def evaluate_solo_baselines(path):
    """Quick evaluation of solo baselines only."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data["questions"]
    n = len(results)
    summary = data.get("summary", {})

    print("=" * 70)
    print(f"  SOLO BASELINES EVALUATION ({n} questions)")
    print("=" * 70)

    per_model = summary.get("per_model", {})
    ranked = sorted(per_model.items(), key=lambda x: -x[1].get("accuracy", 0))
    for rank, (mk, info) in enumerate(ranked, 1):
        mi = MODEL_INFO.get(mk, {"short": mk, "country": "?"})
        flag = "US" if mi.get("country") == "US" else "CN"
        print(f"  #{rank} {mi['short']:20s} [{flag}] {info['correct']}/{n} = {info['accuracy']*100:.1f}%")

    print(f"\n  Simple MV: {summary.get('mv_correct', '?')}/{n} = {summary.get('mv_accuracy', 0)*100:.1f}%")
    print(f"  Oracle:    {summary.get('oracle_correct', '?')}/{n} = {summary.get('oracle_accuracy', 0)*100:.1f}%")


if __name__ == "__main__":
    main()
