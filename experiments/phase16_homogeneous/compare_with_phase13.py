# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Phase 16 vs Phase 13: Comparative Analysis
Loads Phase 13 results and Phase 16 results, computes statistical tests
and generates comparison tables.

Usage:
    python compare_with_phase13.py <phase16_results.json>
    python compare_with_phase13.py  # Auto-detect latest results
"""

import sys
import os
import json
import math
import glob
from datetime import datetime

# Fix Windows cp1251 encoding for Unicode output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


def load_phase13_results():
    """Load Phase 13 results from standard location."""
    p13_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "results", "phase_13"
    )
    # Find the results file
    pattern = os.path.join(p13_dir, "phase13_results_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"  ❌ No Phase 13 results found in {p13_dir}")
        return None
    results_file = files[-1]  # Latest
    print(f"  Phase 13: {results_file}")
    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_phase16_results(path=None):
    """Load Phase 16 results."""
    if path:
        results_file = path
    else:
        p16_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        pattern = os.path.join(p16_dir, "phase16_results_*.json")
        files = sorted(glob.glob(pattern))
        if not files:
            print(f"  ❌ No Phase 16 results found in {p16_dir}")
            return None
        results_file = files[-1]

    print(f"  Phase 16: {results_file}")
    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


def fishers_exact_2x2(a, b, c, d):
    """
    Fisher's exact test for 2x2 contingency table.
    Returns p-value (two-sided approximation).

    Table:
        |         | Correct | Wrong |
        | P13     | a       | b     |
        | P16     | c       | d     |
    """
    n = a + b + c + d
    if n == 0:
        return 1.0

    # Log-factorial for exact computation
    def log_fact(k):
        return sum(math.log(i) for i in range(1, k + 1)) if k > 0 else 0.0

    # Hypergeometric probability
    log_p_obs = (
        log_fact(a + b) + log_fact(c + d) + log_fact(a + c) + log_fact(b + d)
        - log_fact(n) - log_fact(a) - log_fact(b) - log_fact(c) - log_fact(d)
    )
    p_obs = math.exp(log_p_obs)

    # Sum probabilities as extreme or more extreme
    p_value = 0.0
    row1 = a + b
    row2 = c + d
    col1 = a + c

    for i in range(min(row1, col1) + 1):
        j = row1 - i
        k = col1 - i
        l = row2 - k
        if j < 0 or k < 0 or l < 0:
            continue

        log_p = (
            log_fact(row1) + log_fact(row2) + log_fact(col1) + log_fact(j + l)
            - log_fact(n) - log_fact(i) - log_fact(j) - log_fact(k) - log_fact(l)
        )
        p_i = math.exp(log_p)

        if p_i <= p_obs * 1.0001:  # Small tolerance for floating point
            p_value += p_i

    return min(1.0, p_value)


def compare(p13_data, p16_data):
    """Run full comparison."""
    print(f"\n{'='*70}")
    print(f"  Phase 16 vs Phase 13: Comparative Analysis")
    print(f"{'='*70}\n")

    # Extract Phase 13 per-trio summaries
    p13_summary = p13_data.get("summary", {})
    p13_per_trio = p13_summary.get("per_trio", {})

    # Phase 16 summary
    p16_summary = p16_data.get("summary", {})
    p16_echo = p16_data.get("echo_chamber_metrics", {})

    # ---- Accuracy Comparison ----
    print(f"  {'Metric':<30} {'P13 Alpha':>12} {'P13 Beta':>12} {'P16 Homo':>12}")
    print(f"  {'-'*66}")

    p13a = p13_per_trio.get("alpha", {})
    p13b = p13_per_trio.get("beta", {})

    metrics = [
        ("Solo accuracy", "solo", "accuracy"),
        ("Majority Vote", "majority_vote", "accuracy"),
        ("ARRIVAL accuracy", "arrival", "accuracy"),
        ("GAIN vs Solo (pp)", "gain_vs_solo_pp", None),
        ("GAIN vs MV (pp)", "gain_vs_mv_pp", None),
    ]

    for label, key, subkey in metrics:
        if subkey:
            v13a = p13a.get(key, {}).get(subkey, 0) * 100
            v13b = p13b.get(key, {}).get(subkey, 0) * 100
            v16 = p16_summary.get(key, {}).get(subkey, 0) * 100
        else:
            v13a = p13a.get(key, 0)
            v13b = p13b.get(key, 0)
            v16 = p16_summary.get(key, 0)

        print(f"  {label:<30} {v13a:>11.1f}% {v13b:>11.1f}% {v16:>11.1f}%")

    # CRDT
    print(f"\n  {'CRDT Metrics':<30} {'P13 Alpha':>12} {'P13 Beta':>12} {'P16 Homo':>12}")
    print(f"  {'-'*66}")

    p13a_crdt = p13a.get("crdt", {})
    p13b_crdt = p13b.get("crdt", {})
    p16_crdt = p16_summary.get("crdt", {})

    care_13a = p13a_crdt.get("avg_care_resolve")
    care_13b = p13b_crdt.get("avg_care_resolve")
    care_16 = p16_crdt.get("avg_care_resolve")

    debt_13a = p13a_crdt.get("avg_meaning_debt")
    debt_13b = p13b_crdt.get("avg_meaning_debt")
    debt_16 = p16_crdt.get("avg_meaning_debt")

    care_13a_s = f"{care_13a:.3f}" if care_13a else "N/A"
    care_13b_s = f"{care_13b:.3f}" if care_13b else "N/A"
    care_16_s = f"{care_16:.3f}" if care_16 else "N/A"
    debt_13a_s = f"{debt_13a:.3f}" if debt_13a else "N/A"
    debt_13b_s = f"{debt_13b:.3f}" if debt_13b else "N/A"
    debt_16_s = f"{debt_16:.3f}" if debt_16 else "N/A"

    print(f"  {'Avg CARE Resolve':<30} {care_13a_s:>12} {care_13b_s:>12} {care_16_s:>12}")
    print(f"  {'Avg Meaning Debt':<30} {debt_13a_s:>12} {debt_13b_s:>12} {debt_16_s:>12}")

    # Echo-chamber metrics (Phase 16 only)
    print(f"\n  Echo-Chamber Metrics (Phase 16 only):")
    print(f"  {'-'*50}")

    echo_items = [
        ("R1 Unanimity Rate", p16_echo.get("r1_agreement", {}).get("r1_agreement_rate", 0) * 100, "%"),
        ("Answer Entropy (norm)", p16_echo.get("answer_entropy", {}).get("normalized_entropy", 0) * 100, "%"),
        ("R1→R2 Flip Rate", p16_echo.get("flip_rate", {}).get("flip_rate", 0) * 100, "%"),
        ("False Consensus Rate", p16_echo.get("false_consensus", {}).get("false_consensus_rate", 0) * 100, "%"),
        ("Minority Suppression", p16_echo.get("minority_suppression", {}).get("minority_suppression_rate", 0) * 100, "%"),
        ("Confidence Inflation", p16_echo.get("confidence_inflation", {}).get("confidence_inflation_ratio", 1.0), "x"),
        ("Diversity Tax", p16_echo.get("diversity_tax", {}).get("diversity_tax_pct", 0), "%"),
    ]

    for label, value, unit in echo_items:
        if unit == "x":
            val_str = f"{value:.2f}x" if value != "inf" else "∞"
        else:
            val_str = f"{value:.1f}{unit}"
        print(f"    {label:<30} {val_str:>10}")

    # ---- Fisher's Exact Test ----
    print(f"\n  Statistical Tests:")
    print(f"  {'-'*50}")

    # Phase 16 ARRIVAL vs Phase 13 Alpha ARRIVAL
    p16_ar_correct = p16_summary.get("arrival", {}).get("correct", 0)
    p16_ar_total = p16_summary.get("arrival", {}).get("total", 0)
    p16_ar_wrong = p16_ar_total - p16_ar_correct

    p13a_ar_correct = p13a.get("arrival", {}).get("correct", 0)
    p13a_ar_total = p13a.get("arrival", {}).get("total", 0)
    p13a_ar_wrong = p13a_ar_total - p13a_ar_correct

    if p13a_ar_total > 0 and p16_ar_total > 0:
        p_val = fishers_exact_2x2(
            p13a_ar_correct, p13a_ar_wrong,
            p16_ar_correct, p16_ar_wrong,
        )
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        print(f"    Fisher's exact (P16 vs P13 Alpha): p = {p_val:.4f} {sig}")
        print(f"      P13 Alpha: {p13a_ar_correct}/{p13a_ar_total}")
        print(f"      P16 Homo:  {p16_ar_correct}/{p16_ar_total}")

    # Phase 16 ARRIVAL vs Phase 13 Beta ARRIVAL
    p13b_ar_correct = p13b.get("arrival", {}).get("correct", 0)
    p13b_ar_total = p13b.get("arrival", {}).get("total", 0)
    p13b_ar_wrong = p13b_ar_total - p13b_ar_correct

    if p13b_ar_total > 0 and p16_ar_total > 0:
        p_val2 = fishers_exact_2x2(
            p13b_ar_correct, p13b_ar_wrong,
            p16_ar_correct, p16_ar_wrong,
        )
        sig2 = "***" if p_val2 < 0.001 else "**" if p_val2 < 0.01 else "*" if p_val2 < 0.05 else "ns"
        print(f"    Fisher's exact (P16 vs P13 Beta):  p = {p_val2:.4f} {sig2}")
        print(f"      P13 Beta:  {p13b_ar_correct}/{p13b_ar_total}")
        print(f"      P16 Homo:  {p16_ar_correct}/{p16_ar_total}")

    print(f"\n{'='*70}")


def main():
    p16_path = sys.argv[1] if len(sys.argv) > 1 else None

    p13_data = load_phase13_results()
    p16_data = load_phase16_results(p16_path)

    if not p13_data or not p16_data:
        print("  Cannot run comparison — missing data.")
        sys.exit(1)

    compare(p13_data, p16_data)


if __name__ == "__main__":
    main()
