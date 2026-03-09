# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: Statistical Evaluation — All 5 Conditions
=====================================================
Loads results from all conditions and computes:
- Survival rates (Fisher exact test, pairwise)
- Months survived (Mann-Whitney U)
- Meaning Debt -> collapse correlation (Spearman)
- Gini coefficient comparison
- CARE Resolve trajectories
- @-atom counts
- Ablation analysis (D: binding-only, E: adversarial R4)

Conditions:
  A) Baseline — no coordination
  B) ARRIVAL — full 4-round protocol
  C) ARRIVAL + Memory — with CARE-ALERT injection
  D) Binding-only — R4 allocator without R1-R2 debate
  E) Adversarial R4 — selfish R4 synthesizer

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import json
import glob
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try scipy for statistical tests
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy not available. Install with: pip install scipy")


def load_latest_result(results_dir: str, prefix: str, condition_filter: str = None) -> Optional[Dict]:
    """Load the most recent result file matching prefix."""
    pattern = os.path.join(results_dir, f"{prefix}*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"  No results found for {prefix}")
        return None

    # If condition_filter specified, filter by condition field
    if condition_filter:
        for f_path in reversed(files):
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("condition") == condition_filter:
                    print(f"  Loading: {os.path.basename(f_path)}")
                    return data
            except (json.JSONDecodeError, IOError):
                continue
        print(f"  No results found for condition={condition_filter}")
        return None

    latest = files[-1]
    print(f"  Loading: {os.path.basename(latest)}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def fisher_exact_2x2(survived_a, total_a, survived_b, total_b):
    """Fisher exact test for survival rate comparison."""
    if not HAS_SCIPY:
        return {"p_value": None, "odds_ratio": None, "note": "scipy not available"}
    table = [
        [survived_a, total_a - survived_a],
        [survived_b, total_b - survived_b],
    ]
    odds, p = scipy_stats.fisher_exact(table)
    return {"p_value": round(p, 6), "odds_ratio": round(odds, 4) if odds != float('inf') else "inf"}


def mann_whitney_u(values_a, values_b):
    """Mann-Whitney U test for months survived."""
    if not HAS_SCIPY or len(values_a) < 2 or len(values_b) < 2:
        return {"U": None, "p_value": None}
    u, p = scipy_stats.mannwhitneyu(values_a, values_b, alternative='two-sided')
    return {"U": round(u, 2), "p_value": round(p, 6)}


def spearman_correlation(x, y):
    """Spearman rank correlation."""
    if not HAS_SCIPY or len(x) < 3:
        return {"rho": None, "p_value": None}
    rho, p = scipy_stats.spearmanr(x, y)
    return {"rho": round(rho, 4), "p_value": round(p, 4)}


def evaluate_all(results_dir: str) -> Dict[str, Any]:
    """Run full evaluation on all 5 conditions."""
    print("\n" + "=" * 70)
    print("  PHASE 19: STATISTICAL EVALUATION (5 CONDITIONS)")
    print("=" * 70)

    # Load results
    print("\n  --- Loading Results ---")
    baseline = load_latest_result(results_dir, "baseline")
    arrival = load_latest_result(results_dir, "arrival_2", "B_arrival")
    if arrival is None:
        arrival = load_latest_result(results_dir, "arrival", "B_arrival")
    arrival_mem = load_latest_result(results_dir, "arrival_memory")
    binding_only = load_latest_result(results_dir, "binding_only")
    adversarial = load_latest_result(results_dir, "adversarial_r4")

    all_conditions = {
        "A_baseline": baseline,
        "B_arrival": arrival,
        "C_arrival_memory": arrival_mem,
        "D_binding_only": binding_only,
        "E_adversarial_r4": adversarial,
    }

    evaluation = {
        "conditions": {},
        "comparisons": {},
        "correlations": {},
        "atom_analysis": {},
        "ablation_analysis": {},
    }

    # ============================================================
    # Per-condition summary
    # ============================================================
    print("\n  --- Per-Condition Summary ---")

    for label, data in all_conditions.items():
        if data is None:
            evaluation["conditions"][label] = {"error": "no data"}
            continue

        runs = data.get("runs", [])
        n = len(runs)
        survived_count = sum(1 for r in runs if r.get("survived", False))
        months = [r.get("months_survived", 0) for r in runs]
        ginis = [r.get("gini_coefficient", 0) for r in runs]

        cond = {
            "n_runs": n,
            "survived": survived_count,
            "survival_rate": round(survived_count / n, 4) if n > 0 else 0,
            "months_survived": months,
            "avg_months": round(sum(months) / n, 1) if n > 0 else 0,
            "avg_gini": round(sum(ginis) / n, 4) if n > 0 else 0,
            "total_cost_usd": data.get("total_cost_usd", 0),
            "total_api_calls": data.get("total_api_calls", 0),
        }

        # CRDT metrics for conditions with ARRIVAL
        if label in ("B_arrival", "C_arrival_memory", "E_adversarial_r4"):
            cares = [r.get("care_avg", 0) for r in runs]
            mds = [r.get("md_avg", 0) for r in runs]
            cond["avg_care"] = round(sum(cares) / n, 4) if n > 0 else 0
            cond["avg_md"] = round(sum(mds) / n, 4) if n > 0 else 0

        # Memory injections (Condition C only)
        if label == "C_arrival_memory":
            total_inj = sum(len(r.get("memory_injections", [])) for r in runs)
            cond["total_memory_injections"] = total_inj

        # Adversarial metrics (Condition E only)
        if label == "E_adversarial_r4":
            eps_shares = [r.get("epsilon_share_of_total", 0.2) for r in runs]
            cond["avg_epsilon_share"] = round(sum(eps_shares) / n, 4) if n > 0 else 0

        evaluation["conditions"][label] = cond

    # ============================================================
    # Statistical Comparisons (pairwise Fisher exact)
    # ============================================================
    print("\n  === STATISTICAL COMPARISONS ===")

    def get_cond(label):
        return evaluation["conditions"].get(label, {})

    # All pairwise comparisons
    pairs = [
        ("A_baseline", "B_arrival"),
        ("A_baseline", "C_arrival_memory"),
        ("A_baseline", "D_binding_only"),
        ("A_baseline", "E_adversarial_r4"),
        ("B_arrival", "C_arrival_memory"),
        ("B_arrival", "D_binding_only"),
        ("B_arrival", "E_adversarial_r4"),
        ("D_binding_only", "E_adversarial_r4"),
    ]

    for label_a, label_b in pairs:
        a = get_cond(label_a)
        b = get_cond(label_b)
        if not a.get("n_runs") or not b.get("n_runs"):
            continue

        fish = fisher_exact_2x2(a["survived"], a["n_runs"], b["survived"], b["n_runs"])
        mw = mann_whitney_u(a.get("months_survived", []), b.get("months_survived", []))

        key = f"{label_a}_vs_{label_b}"
        evaluation["comparisons"][key] = {
            "fisher_exact": fish,
            "mann_whitney": mw,
            "survival_diff": round(b["survival_rate"] - a["survival_rate"], 4),
            "months_diff": round(b["avg_months"] - a["avg_months"], 1),
        }
        p_str = f"{fish.get('p_value', 'N/A')}"
        print(f"  {label_a} vs {label_b}: "
              f"{a['survival_rate']:.0%} vs {b['survival_rate']:.0%}, "
              f"Fisher p={p_str}")

    # ============================================================
    # MD-Collapse Correlation
    # ============================================================
    print("\n  === MD-COLLAPSE CORRELATION ===")

    all_md = []
    all_months = []
    for data in [arrival, arrival_mem, adversarial]:
        if data is None:
            continue
        for run in data.get("runs", []):
            md = run.get("md_avg")
            months = run.get("months_survived")
            if md is not None and months is not None:
                all_md.append(md)
                all_months.append(months)

    if len(all_md) >= 3:
        corr = spearman_correlation(all_md, all_months)
        evaluation["correlations"]["md_vs_months"] = corr
        print(f"  MD vs Months: rho={corr.get('rho', 'N/A')}, p={corr.get('p_value', 'N/A')}")
    else:
        evaluation["correlations"]["md_vs_months"] = {"note": "insufficient data"}

    # ============================================================
    # Ablation Analysis
    # ============================================================
    print("\n  === ABLATION ANALYSIS ===")

    b = get_cond("B_arrival")
    d = get_cond("D_binding_only")
    e = get_cond("E_adversarial_r4")

    if b.get("n_runs") and d.get("n_runs"):
        # Key question: Does binding-only match full ARRIVAL?
        binding_matches = d["survival_rate"] == b["survival_rate"]
        evaluation["ablation_analysis"]["binding_only_confound"] = {
            "binding_matches_arrival": binding_matches,
            "binding_survival": d["survival_rate"],
            "arrival_survival": b["survival_rate"],
            "interpretation": (
                "Binding mechanism alone is sufficient — debate may not be causally necessary"
                if binding_matches else
                "Structured debate (R1-R2) IS causally necessary for cooperation"
            ),
        }
        print(f"  Binding-only: {d['survival_rate']:.0%} vs ARRIVAL: {b['survival_rate']:.0%}")
        print(f"  -> {'CONFOUND: binding alone sufficient' if binding_matches else 'DEBATE IS NECESSARY'}")

    if b.get("n_runs") and e.get("n_runs"):
        # Key question: Can adversarial R4 break ARRIVAL?
        adv_robust = e["survival_rate"] >= 0.6  # >60% survival = structurally robust
        evaluation["ablation_analysis"]["adversarial_r4_robustness"] = {
            "adversarial_survival": e["survival_rate"],
            "arrival_survival": b["survival_rate"],
            "structurally_robust": adv_robust,
            "avg_epsilon_share": e.get("avg_epsilon_share", "N/A"),
            "avg_gini": e["avg_gini"],
            "interpretation": (
                "ARRIVAL is structurally robust — safety clamping prevents R4 exploitation"
                if adv_robust else
                "R4 is a vulnerability — adversarial synthesizer can cause collapse"
            ),
        }
        print(f"  Adversarial R4: {e['survival_rate']:.0%} survival, "
              f"Epsilon share: {e.get('avg_epsilon_share', 'N/A')}, "
              f"Gini: {e['avg_gini']:.3f}")
        print(f"  -> {'ROBUST: safety clamp protects' if adv_robust else 'VULNERABLE: R4 is exploitable'}")

    # ============================================================
    # @-Atom Analysis
    # ============================================================
    print("\n  === ATOM ANALYSIS ===")

    for label, data in [("B_arrival", arrival), ("C_arrival_memory", arrival_mem), ("E_adversarial_r4", adversarial)]:
        if data is None:
            continue

        total_atoms = {"consensus": 0, "conflict": 0, "resolution": 0, "evidence": 0, "harvest": 0}
        for run in data.get("runs", []):
            for month_entry in run.get("game_log", []):
                for round_key in ["r1", "r2"]:
                    round_data = month_entry.get(round_key, {})
                    for agent_name, agent_data in round_data.items():
                        atoms = agent_data.get("atoms", {})
                        for atom_type, count in atoms.items():
                            if atom_type in total_atoms:
                                total_atoms[atom_type] += count

        evaluation["atom_analysis"][label] = total_atoms
        total_coop = total_atoms["consensus"] + total_atoms["resolution"]
        total_comp = total_atoms["conflict"]
        coop_ratio = round(total_coop / (total_coop + total_comp), 3) if (total_coop + total_comp) > 0 else 0

        print(f"  {label}: consensus={total_atoms['consensus']}, "
              f"conflict={total_atoms['conflict']}, coop_ratio={coop_ratio}")

    # ============================================================
    # Summary Table
    # ============================================================
    print("\n" + "=" * 90)
    print("  SUMMARY TABLE (ALL 5 CONDITIONS)")
    print("=" * 90)
    header = f"  {'Condition':<22} {'Survival':>10} {'Avg Mo':>8} {'CARE':>8} {'MD':>8} {'Gini':>8} {'Cost':>8} {'Calls':>7}"
    print(header)
    print(f"  {'-'*86}")

    for label in ["A_baseline", "B_arrival", "C_arrival_memory", "D_binding_only", "E_adversarial_r4"]:
        cond = get_cond(label)
        if cond.get("error"):
            print(f"  {label:<22} {'N/A':>10}")
            continue
        sr = f"{cond['survived']}/{cond['n_runs']} ({cond['survival_rate']:.0%})"
        am = f"{cond['avg_months']:.1f}"
        care = f"{cond.get('avg_care', '-')}" if isinstance(cond.get('avg_care'), (int, float)) else "-"
        md = f"{cond.get('avg_md', '-')}" if isinstance(cond.get('avg_md'), (int, float)) else "-"
        gini = f"{cond['avg_gini']:.3f}"
        cost = f"${cond['total_cost_usd']:.2f}"
        calls = f"{cond['total_api_calls']}"
        print(f"  {label:<22} {sr:>10} {am:>8} {care:>8} {md:>8} {gini:>8} {cost:>8} {calls:>7}")

    # Key p-values
    print(f"\n  KEY P-VALUES:")
    for key, comp in evaluation["comparisons"].items():
        p = comp.get("fisher_exact", {}).get("p_value", "N/A")
        sig = "***" if isinstance(p, (int, float)) and p < 0.01 else ("**" if isinstance(p, (int, float)) and p < 0.05 else "")
        print(f"    {key}: Fisher p = {p} {sig}")

    print("=" * 90)

    # Save evaluation
    eval_path = os.path.join(results_dir, "evaluation_n5.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {eval_path}")

    return evaluation


def main():
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    evaluate_all(results_dir)


if __name__ == "__main__":
    main()
