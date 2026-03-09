# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: Condition C — ARRIVAL + Memory Runner
=================================================
Same as Condition B but with CARE-ALERT memory injection.

When CARE Resolve drops or Meaning Debt rises, the system injects
pre-seeded sustainability memories into the R4 synthesis prompt.

This tests whether ARRIVAL-MNEMO's working memory system can
prevent cooperation breakdown in multi-month games.

Expected: 3/3 survival (100%).
API calls: 11 × 12 × 3 = 396.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_phase19 import (
    OPENROUTER_API_KEY, N_RUNS, N_MONTHS, N_AGENTS, RANDOM_SEEDS,
)
from run_arrival import run_arrival_game, cumulative_cost, total_api_calls
import run_arrival  # to access global counters


def main():
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set!")
        sys.exit(1)

    memory_seeds_path = os.path.join(
        os.path.dirname(__file__), "memory_seeds_govsim.json"
    )
    if not os.path.exists(memory_seeds_path):
        print(f"ERROR: Memory seeds not found: {memory_seeds_path}")
        sys.exit(1)

    print("=" * 60)
    print("  PHASE 19: GovSim — CONDITION C (ARRIVAL + MEMORY)")
    print(f"  Runs: {N_RUNS} | Months: {N_MONTHS} | Agents: {N_AGENTS}")
    print(f"  Memory seeds: {memory_seeds_path}")
    print(f"  Expected API calls: 11 x {N_MONTHS} x {N_RUNS} = {11 * N_MONTHS * N_RUNS}")
    print("=" * 60)

    all_results = []
    start_time = datetime.now(timezone.utc)

    for i in range(N_RUNS):
        result = run_arrival_game(
            i, RANDOM_SEEDS[i],
            use_memory=True,
            memory_seeds_path=memory_seeds_path,
        )
        all_results.append(result)

    # Save
    output = {
        "experiment": "phase19_govsim",
        "condition": "C_arrival_memory",
        "timestamp": start_time.isoformat(),
        "duration_s": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "total_api_calls": run_arrival.total_api_calls,
        "total_cost_usd": round(run_arrival.cumulative_cost, 4),
        "n_runs": N_RUNS,
        "survival_rate": sum(1 for r in all_results if r["survived"]) / N_RUNS,
        "avg_months_survived": sum(r["months_survived"] for r in all_results) / N_RUNS,
        "avg_care": sum(r["care_avg"] for r in all_results) / N_RUNS,
        "avg_md": sum(r["md_avg"] for r in all_results) / N_RUNS,
        "total_memory_injections": sum(
            len(r.get("memory_injections", [])) for r in all_results
        ),
        "runs": all_results,
    }

    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(results_dir, f"arrival_memory_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  CONDITION C COMPLETE")
    print(f"  Survival rate: {output['survival_rate']:.0%}")
    print(f"  Avg months survived: {output['avg_months_survived']:.1f}")
    print(f"  Avg CARE: {output['avg_care']:.3f}")
    print(f"  Avg MD: {output['avg_md']:.3f}")
    print(f"  Memory injections: {output['total_memory_injections']}")
    print(f"  Total cost: ${output['total_cost_usd']:.4f}")
    print(f"  API calls: {output['total_api_calls']}")
    print(f"  Saved: {out_path}")
    print(f"{'='*60}")

    return output


if __name__ == "__main__":
    main()
