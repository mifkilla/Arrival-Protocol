# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: Condition A — Baseline Runner
========================================
Minimal prompts, no coordination, no history, no reasoning.
Each agent sees only current stock and responds with a number.

This replicates GovSim's finding that unstructured LLMs fail at
commons management (Piatti et al. 2024: 12/15 models = 0% survival).

Expected: 0/3 or 1/3 survival.
API calls: 5 agents × 12 months × 3 runs = 180 total.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timezone

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_phase19 import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, BUDGET_LIMIT_USD,
    SLEEP_BETWEEN_CALLS, REQUEST_TIMEOUT,
    GOVSIM_MODELS, MODEL_COSTS, MODEL_SHORT,
    BASELINE_PROMPT, BASELINE_MAX_TOKENS,
    INITIAL_STOCK, MAX_CAPACITY, COLLAPSE_THRESHOLD,
    N_MONTHS, N_AGENTS, N_RUNS, RANDOM_SEEDS,
)
from govsim_env import FishPondEnv
from harvest_extraction import extract_harvest_amount


# ============================================================
# API Client (reused pattern from Phase 18 arrival_runner.py)
# ============================================================
cumulative_cost = 0.0
total_api_calls = 0


def call_openrouter(prompt, model, max_tokens=256, temperature=0.3):
    """Make a single API call to OpenRouter."""
    global cumulative_cost, total_api_calls

    if cumulative_cost >= BUDGET_LIMIT_USD:
        return {"text": "BUDGET_EXCEEDED", "success": False, "cost_usd": 0}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/mifkilla/Arrival-Protocol",
        "X-Title": "ARRIVAL Phase 19 GovSim Baseline",
        "Content-Type": "application/json",
    }

    messages = [{"role": "user", "content": prompt}]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    start_time = time.time()
    for attempt in range(3):
        try:
            resp = requests.post(
                OPENROUTER_BASE_URL, headers=headers, json=payload,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", 10))
                print(f"      Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            data = resp.json()

            text = ""
            choices = data.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")

            usage = data.get("usage", {})
            pt = usage.get("prompt_tokens", 0)
            ct = usage.get("completion_tokens", 0)
            costs = MODEL_COSTS.get(model, {"input": 1.0, "output": 2.0})
            cost = (pt * costs["input"] + ct * costs["output"]) / 1_000_000

            cumulative_cost += cost
            total_api_calls += 1

            return {
                "text": text,
                "model": model,
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "cost_usd": cost,
                "latency_ms": (time.time() - start_time) * 1000,
                "success": True,
            }
        except requests.exceptions.RequestException as e:
            if attempt < 2:
                time.sleep(5)
            else:
                return {"text": f"ERROR: {e}", "success": False, "cost_usd": 0,
                        "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0, "model": model}

    return {"text": "ERROR: Max retries", "success": False, "cost_usd": 0,
            "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0, "model": model}


# ============================================================
# Baseline Game Runner
# ============================================================

def run_baseline_game(run_id: int, seed: int) -> dict:
    """Run a single 12-month baseline game."""
    print(f"\n{'='*60}")
    print(f"  CONDITION A: BASELINE — Run {run_id+1} (seed={seed})")
    print(f"{'='*60}")

    env = FishPondEnv(
        initial_stock=INITIAL_STOCK,
        max_capacity=MAX_CAPACITY,
        collapse_threshold=COLLAPSE_THRESHOLD,
        n_months=N_MONTHS,
    )

    agent_names = list(GOVSIM_MODELS.keys())
    game_log = []

    for month in range(1, N_MONTHS + 1):
        if env.collapsed:
            break

        print(f"\n  Month {month}/{N_MONTHS} | Stock: {env.stock:.0f}")

        harvests = {}
        month_calls = []

        for agent_name in agent_names:
            model_id = GOVSIM_MODELS[agent_name]["model_id"]
            short = MODEL_SHORT.get(model_id, model_id)

            prompt = BASELINE_PROMPT.format(
                stock=int(env.stock),
                n_agents=N_AGENTS,
                month=month,
                total_months=N_MONTHS,
                collapse_threshold=COLLAPSE_THRESHOLD,
            )

            print(f"    {agent_name} [{short}]...", end=" ", flush=True)
            resp = call_openrouter(prompt, model_id, max_tokens=BASELINE_MAX_TOKENS)

            fair_share = env.get_fair_share()
            harvest = extract_harvest_amount(resp["text"], fallback=int(fair_share))
            harvests[agent_name] = harvest

            print(f"harvest={harvest} (fair={fair_share:.0f})")
            month_calls.append({
                "agent": agent_name,
                "model": model_id,
                "response": resp["text"][:200],
                "extracted_harvest": harvest,
                "cost_usd": resp["cost_usd"],
            })

            time.sleep(SLEEP_BETWEEN_CALLS)

        # Execute month
        state = env.step(harvests)

        month_entry = {
            "month": month,
            "stock_before": state.stock_before,
            "harvests": state.harvests,
            "stock_after_harvest": state.stock_after_harvest,
            "stock_after_replenish": state.stock_after_replenish,
            "collapsed": state.collapsed,
            "gini": round(state.gini, 4),
            "api_calls": month_calls,
        }
        game_log.append(month_entry)

        if state.collapsed:
            print(f"\n  COLLAPSED at month {month}! Stock after harvest: {state.stock_after_harvest:.0f}")
            break
        else:
            print(f"    After harvest: {state.stock_after_harvest:.0f} → replenish → {state.stock_after_replenish:.0f}")

    # Summary
    survived = env.is_survived()
    months_survived = env.get_months_survived()
    gini = env.compute_gini_coefficient()

    print(f"\n  RESULT: {'SURVIVED' if survived else 'COLLAPSED'} "
          f"({months_survived} months, Gini={gini:.3f})")

    return {
        "condition": "A_baseline",
        "run_id": run_id,
        "seed": seed,
        "survived": survived,
        "months_survived": months_survived,
        "gini_coefficient": round(gini, 4),
        "final_stock": env.stock,
        "cumulative_harvests": env.cumulative_harvests,
        "resource_trajectory": env.get_resource_trajectory(),
        "game_log": game_log,
        "env_state": env.to_dict(),
    }


# ============================================================
# Main
# ============================================================

def main():
    global cumulative_cost, total_api_calls

    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set!")
        print("Set it: export OPENROUTER_API_KEY=sk-or-v1-...")
        sys.exit(1)

    print("=" * 60)
    print("  PHASE 19: GovSim — CONDITION A (BASELINE)")
    print(f"  Runs: {N_RUNS} | Months: {N_MONTHS} | Agents: {N_AGENTS}")
    print(f"  Expected API calls: {N_AGENTS * N_MONTHS * N_RUNS}")
    print("=" * 60)

    all_results = []
    start_time = datetime.now(timezone.utc)

    for i in range(N_RUNS):
        result = run_baseline_game(i, RANDOM_SEEDS[i])
        all_results.append(result)

    # Save results
    output = {
        "experiment": "phase19_govsim",
        "condition": "A_baseline",
        "timestamp": start_time.isoformat(),
        "duration_s": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "total_api_calls": total_api_calls,
        "total_cost_usd": round(cumulative_cost, 4),
        "n_runs": N_RUNS,
        "survival_rate": sum(1 for r in all_results if r["survived"]) / N_RUNS,
        "avg_months_survived": sum(r["months_survived"] for r in all_results) / N_RUNS,
        "runs": all_results,
    }

    # Save
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(results_dir, f"baseline_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'='*60}")
    print(f"  CONDITION A COMPLETE")
    print(f"  Survival rate: {output['survival_rate']:.0%}")
    print(f"  Avg months survived: {output['avg_months_survived']:.1f}")
    print(f"  Total cost: ${output['total_cost_usd']:.4f}")
    print(f"  API calls: {output['total_api_calls']}")
    print(f"  Saved: {out_path}")
    print(f"{'='*60}")

    return output


if __name__ == "__main__":
    main()
