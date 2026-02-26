# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Arrival CRDT -- Unified Experiment Runner

Run any combination of experimental phases from a single entry point.
Tracks cumulative cost across all phases, enforces budget limits,
provides progress reporting, and generates a summary report.

Usage:
    python run_all.py --phases all --budget 10.0
    python run_all.py --phases 8,9,10 --budget 2.0
    python run_all.py --phases 6,7 --dry-run
    python run_all.py --phases 4 --budget 0.50
"""

import argparse
import importlib
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Windows encoding fix -- replace unencodable chars instead of crashing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

# Add src/ to path so all modules resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RESULTS_DIR, LOGS_DIR, MAX_COST_USD

# ============================================================
# Phase Registry
# ============================================================
# Each entry maps a phase number to its runner module path,
# human-readable name, and estimated cost in USD.
# Module paths are dot-separated relative to src/.

AVAILABLE_PHASES = {
    4: {
        "module": "group_a.run_group_a",
        "name": "Group A: Goal Alignment",
        "estimated_cost": 0.50,
    },
    5: {
        "module": "phase_5.run_phase5",
        "name": "Phase 5: Benchmark",
        "estimated_cost": 0.30,
    },
    6: {
        "module": "phase_6.run_phase6",
        "name": "Phase 6: Adversarial",
        "estimated_cost": 0.54,
    },
    7: {
        "module": "phase_7.run_phase7",
        "name": "Phase 7: Quick Benchmark",
        "estimated_cost": 0.16,
    },
    8: {
        "module": "phase_8.run_phase8",
        "name": "Phase 8: Multi-Step Goals",
        "estimated_cost": 0.10,
    },
    9: {
        "module": "phase_9.run_phase9",
        "name": "Phase 9: Scale N=5-7",
        "estimated_cost": 0.15,
    },
    10: {
        "module": "phase_10.run_phase10",
        "name": "Phase 10: Adaptive Defense",
        "estimated_cost": 0.08,
    },
    11: {
        "module": "phase_11.run_phase11",
        "name": "Phase 11: Crystallization",
        "estimated_cost": 0.05,
    },
    12: {
        "module": "phase_12.run_phase12",
        "name": "Phase 12: Bottleneck",
        "estimated_cost": 0.10,
    },
}


# ============================================================
# Helpers
# ============================================================

def format_cost(usd: float) -> str:
    """Format a dollar amount for display."""
    return f"${usd:.4f}"


def load_phase_module(module_path: str):
    """
    Dynamically import a phase runner module.

    Args:
        module_path: Dot-separated module path (e.g. "group_a.run_group_a").

    Returns:
        The imported module object.

    Raises:
        ImportError: If the module cannot be found or loaded.
    """
    return importlib.import_module(module_path)


def get_phase_main(module):
    """
    Locate the callable entry point in a phase runner module.

    Looks for, in order: main(), run(), run_phase().
    Returns the callable or None if no entry point is found.
    """
    for name in ("main", "run", "run_phase"):
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    return None


# ============================================================
# Dry-run cost estimator
# ============================================================

def estimate_costs(phases: list[int]) -> float:
    """
    Print estimated cost breakdown and return total estimate.

    Args:
        phases: Ordered list of phase numbers to estimate.

    Returns:
        Total estimated cost in USD.
    """
    print("=" * 70)
    print("DRY RUN -- Cost Estimate (no API calls will be made)")
    print("=" * 70)

    total = 0.0
    for phase_num in phases:
        info = AVAILABLE_PHASES[phase_num]
        cost = info["estimated_cost"]
        total += cost
        print(f"  Phase {phase_num:>2}: {info['name']:<35} ~{format_cost(cost)}")

    print("-" * 70)
    print(f"  {'TOTAL ESTIMATED':<40} ~{format_cost(total)}")
    print("=" * 70)
    return total


# ============================================================
# Phase runner with budget guard
# ============================================================

def run_phase(
    phase_num: int,
    phase_info: dict,
    cumulative_cost: float,
    budget: float,
) -> dict:
    """
    Import and execute a single phase's runner module.

    Args:
        phase_num: Integer phase identifier (e.g. 8).
        phase_info: Dict with keys 'module', 'name', 'estimated_cost'.
        cumulative_cost: Total USD spent so far across all prior phases.
        budget: Maximum USD allowed for the entire run.

    Returns:
        A dict with keys:
            - phase: int
            - name: str
            - status: "success" | "failed" | "skipped" | "budget_exceeded"
            - exit_code: int or None
            - cost_usd: float (cost incurred during this phase)
            - duration_s: float
            - error: str or None
    """
    result = {
        "phase": phase_num,
        "name": phase_info["name"],
        "status": "pending",
        "exit_code": None,
        "cost_usd": 0.0,
        "duration_s": 0.0,
        "error": None,
    }

    # Budget pre-check: stop if remaining budget is too low
    remaining = budget - cumulative_cost
    if remaining <= 0:
        result["status"] = "budget_exceeded"
        result["error"] = (
            f"Budget exhausted: {format_cost(cumulative_cost)} spent "
            f"of {format_cost(budget)} limit"
        )
        return result

    # Warn if remaining budget is less than estimated cost
    if remaining < phase_info["estimated_cost"]:
        print(
            f"  WARNING: Remaining budget {format_cost(remaining)} is below "
            f"estimated cost {format_cost(phase_info['estimated_cost'])} "
            f"for {phase_info['name']}. Proceeding anyway..."
        )

    start_time = time.time()

    try:
        # Dynamic import
        print(f"  Loading module: {phase_info['module']}...")
        module = load_phase_module(phase_info["module"])

        # Find entry point
        main_fn = get_phase_main(module)
        if main_fn is None:
            result["status"] = "failed"
            result["error"] = (
                f"No entry point found in {phase_info['module']}. "
                f"Expected one of: main(), run(), run_phase()"
            )
            return result

        # Execute the phase
        exit_code = main_fn()
        result["exit_code"] = exit_code if isinstance(exit_code, int) else 0
        result["status"] = "success" if result["exit_code"] == 0 else "failed"

    except ImportError as e:
        result["status"] = "skipped"
        result["error"] = f"Module not found: {e}"

    except Exception as e:
        result["status"] = "failed"
        result["error"] = f"{type(e).__name__}: {e}"
        # Print full traceback for debugging
        traceback.print_exc()

    finally:
        result["duration_s"] = round(time.time() - start_time, 2)

    # Try to read cost from the OpenRouterClient that the phase module used.
    # Phases typically create their own client; we look for it as a module-level
    # variable or attempt get_status() on known locations.
    phase_cost = _extract_phase_cost(phase_info["module"])
    result["cost_usd"] = phase_cost

    return result


def _extract_phase_cost(module_path: str) -> float:
    """
    Attempt to read cumulative cost from an already-imported phase module.

    Phase runners typically instantiate an OpenRouterClient as a local
    variable inside main(). Since we cannot reliably introspect that,
    we fall back to checking the openrouter_client module's global state
    if it was shared. This is best-effort.

    Returns:
        Estimated cost for this phase, or 0.0 if unavailable.
    """
    try:
        mod = sys.modules.get(module_path)
        if mod is None:
            return 0.0
        # Check for a module-level 'client' attribute
        client = getattr(mod, "client", None)
        if client is not None and hasattr(client, "get_status"):
            status = client.get_status()
            return status.get("cumulative_cost_usd", 0.0)
    except Exception:
        pass
    return 0.0


# ============================================================
# Summary report
# ============================================================

def generate_summary(
    results: list[dict],
    budget: float,
    wall_start: datetime,
    wall_end: datetime,
) -> dict:
    """
    Generate and print a summary report for the entire run.

    Args:
        results: List of per-phase result dicts from run_phase().
        budget: The budget limit that was configured.
        wall_start: Datetime when the run began.
        wall_end: Datetime when the run finished.

    Returns:
        Summary dict (also written to disk as JSON).
    """
    total_cost = sum(r["cost_usd"] for r in results)
    total_duration = sum(r["duration_s"] for r in results)
    wall_duration = (wall_end - wall_start).total_seconds()

    succeeded = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    skipped = [r for r in results if r["status"] == "skipped"]
    budget_stopped = [r for r in results if r["status"] == "budget_exceeded"]

    summary = {
        "timestamp": wall_end.isoformat(),
        "wall_clock_s": round(wall_duration, 2),
        "total_phase_duration_s": round(total_duration, 2),
        "total_cost_usd": round(total_cost, 6),
        "budget_usd": budget,
        "budget_remaining_usd": round(budget - total_cost, 6),
        "phases_requested": len(results),
        "phases_succeeded": len(succeeded),
        "phases_failed": len(failed),
        "phases_skipped": len(skipped),
        "phases_budget_stopped": len(budget_stopped),
        "per_phase": results,
    }

    # Print report
    print("\n")
    print("=" * 70)
    print("ARRIVAL CRDT -- Unified Run Summary")
    print("=" * 70)
    print(f"  Started:      {wall_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Finished:     {wall_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Wall clock:   {wall_duration:.1f}s")
    print(f"  Budget:       {format_cost(budget)}")
    print(f"  Total cost:   {format_cost(total_cost)}")
    print(f"  Remaining:    {format_cost(budget - total_cost)}")
    print("-" * 70)
    print(f"  Succeeded:    {len(succeeded)}")
    print(f"  Failed:       {len(failed)}")
    print(f"  Skipped:      {len(skipped)}")
    print(f"  Budget stop:  {len(budget_stopped)}")
    print("-" * 70)

    for r in results:
        status_icon = {
            "success": "[OK]",
            "failed": "[FAIL]",
            "skipped": "[SKIP]",
            "budget_exceeded": "[BUDGET]",
            "pending": "[???]",
        }.get(r["status"], "[???]")

        line = (
            f"  Phase {r['phase']:>2} {status_icon:<10} "
            f"{r['name']:<35} "
            f"{r['duration_s']:>7.1f}s  "
            f"{format_cost(r['cost_usd'])}"
        )
        print(line)

        if r["error"]:
            # Truncate long errors for display
            err_display = r["error"][:120]
            print(f"           -> {err_display}")

    print("=" * 70)

    # Save to disk
    report_dir = RESULTS_DIR / "run_all"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"summary_{wall_end.strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n  Report saved: {report_path}")
    except Exception as e:
        print(f"\n  WARNING: Could not save report: {e}")

    return summary


# ============================================================
# CLI argument parsing
# ============================================================

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace with attributes: phases, budget, dry_run.
    """
    parser = argparse.ArgumentParser(
        description="ARRIVAL CRDT -- Unified Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_all.py --phases all --budget 10.0\n"
            "  python run_all.py --phases 8,9,10 --budget 2.0\n"
            "  python run_all.py --phases 6,7 --dry-run\n"
            "  python run_all.py --phases 4\n"
        ),
    )
    parser.add_argument(
        "--phases",
        type=str,
        default="all",
        help=(
            'Comma-separated phase numbers to run (e.g. "8,9,10") '
            'or "all" to run every registered phase. '
            f"Available: {sorted(AVAILABLE_PHASES.keys())}"
        ),
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=MAX_COST_USD,
        help=f"Maximum total USD to spend across all phases (default: {MAX_COST_USD})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Estimate costs without making any API calls",
    )

    args = parser.parse_args(argv)
    return args


def resolve_phases(phases_str: str) -> list[int]:
    """
    Parse the --phases argument into an ordered list of phase numbers.

    Args:
        phases_str: Either "all" or a comma-separated string like "8,9,10".

    Returns:
        Sorted list of valid phase numbers.

    Raises:
        ValueError: If any requested phase is not in AVAILABLE_PHASES.
    """
    if phases_str.strip().lower() == "all":
        return sorted(AVAILABLE_PHASES.keys())

    requested = []
    for token in phases_str.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            num = int(token)
        except ValueError:
            raise ValueError(
                f"Invalid phase identifier: '{token}'. "
                f"Expected integer or 'all'."
            )
        if num not in AVAILABLE_PHASES:
            raise ValueError(
                f"Unknown phase: {num}. "
                f"Available phases: {sorted(AVAILABLE_PHASES.keys())}"
            )
        if num not in requested:
            requested.append(num)

    if not requested:
        raise ValueError("No phases specified. Use --phases all or --phases 8,9,10")

    return sorted(requested)


# ============================================================
# Main
# ============================================================

def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for the unified experiment runner.

    Args:
        argv: Optional argument list for testing. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 if all requested phases succeeded, 1 otherwise.
    """
    args = parse_args(argv)

    # Resolve phase list
    try:
        phases = resolve_phases(args.phases)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    budget = args.budget

    # Header
    print("=" * 70)
    print("ARRIVAL CRDT -- Unified Experiment Runner")
    print("=" * 70)
    print(f"  Phases:   {phases}")
    print(f"  Budget:   {format_cost(budget)}")
    print(f"  Dry run:  {args.dry_run}")
    print(f"  Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Dry run mode: just show estimates
    if args.dry_run:
        total_estimate = estimate_costs(phases)
        if total_estimate > budget:
            print(
                f"\n  WARNING: Estimated cost {format_cost(total_estimate)} "
                f"exceeds budget {format_cost(budget)}"
            )
            print("  Some phases may be skipped at runtime due to budget limits.")
        else:
            print(
                f"\n  Estimate is within budget "
                f"({format_cost(total_estimate)} / {format_cost(budget)})"
            )
        return 0

    # Ensure output directories exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Execute phases
    wall_start = datetime.now()
    results = []
    cumulative_cost = 0.0
    budget_exceeded = False

    for idx, phase_num in enumerate(phases, 1):
        phase_info = AVAILABLE_PHASES[phase_num]

        print(f"\n{'=' * 70}")
        print(
            f"[Phase {phase_num}] "
            f"({idx}/{len(phases)}) "
            f"{phase_info['name']}"
        )
        print(
            f"  Budget remaining: {format_cost(budget - cumulative_cost)} | "
            f"Estimated cost: ~{format_cost(phase_info['estimated_cost'])} | "
            f"Spent so far: {format_cost(cumulative_cost)}"
        )
        print("=" * 70)

        # Check budget before starting
        if budget_exceeded or cumulative_cost >= budget:
            budget_exceeded = True
            print(
                f"  STOPPING: Budget limit {format_cost(budget)} reached "
                f"(spent: {format_cost(cumulative_cost)})"
            )
            results.append({
                "phase": phase_num,
                "name": phase_info["name"],
                "status": "budget_exceeded",
                "exit_code": None,
                "cost_usd": 0.0,
                "duration_s": 0.0,
                "error": f"Budget exhausted before phase start",
            })
            continue

        # Run the phase
        result = run_phase(phase_num, phase_info, cumulative_cost, budget)
        results.append(result)

        # Update cumulative cost
        cumulative_cost += result["cost_usd"]

        # Progress line
        status_label = result["status"].upper()
        print(
            f"\n  [Phase {phase_num}] {status_label} "
            f"in {result['duration_s']:.1f}s "
            f"({format_cost(result['cost_usd'])} this phase, "
            f"{format_cost(cumulative_cost)} total)"
        )

        if result["status"] == "failed":
            print(f"  ERROR: {result['error']}")
            print("  Continuing to next phase...")

        if result["status"] == "budget_exceeded":
            budget_exceeded = True

        # Check if we overran the budget during execution
        if cumulative_cost >= budget:
            budget_exceeded = True
            print(
                f"\n  BUDGET LIMIT REACHED: "
                f"{format_cost(cumulative_cost)} >= {format_cost(budget)}"
            )

    # Generate summary
    wall_end = datetime.now()
    summary = generate_summary(results, budget, wall_start, wall_end)

    # Determine exit code
    all_ok = all(
        r["status"] in ("success", "skipped")
        for r in results
        if r["status"] != "budget_exceeded"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
