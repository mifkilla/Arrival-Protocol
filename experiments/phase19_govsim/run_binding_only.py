# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: Condition D — Binding-Only Ablation
==============================================
Tests whether R4's BINDING ALLOCATION alone (without R1-R2 debate)
is sufficient for commons survival.

This is the key ablation requested by all 4 reviewers:
If binding-only also achieves 100% survival → the structured debate
(@-atoms, cross-critique) is NOT the causal mechanism; enforcement is.
If binding-only fails → structured debate IS necessary.

Per month: 1 API call (R4 allocator only, no R1/R2 debate)
Total: 1 × 12 × 5 = 60 API calls.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_phase19 import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, BUDGET_LIMIT_USD,
    SLEEP_BETWEEN_CALLS, REQUEST_TIMEOUT,
    GOVSIM_MODELS, MODEL_COSTS, MODEL_SHORT, AGENT_DISPLAY_NAMES,
    ARRIVAL_SYSTEM_BASE, ARRIVAL_TEMPERATURE, ARRIVAL_MAX_TOKENS_R4,
    INITIAL_STOCK, MAX_CAPACITY, COLLAPSE_THRESHOLD,
    N_MONTHS, N_AGENTS, N_RUNS, RANDOM_SEEDS,
)
from govsim_env import FishPondEnv
from harvest_extraction import extract_r4_allocation

# Fix Windows encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# API Client
# ============================================================
cumulative_cost = 0.0
total_api_calls = 0


def call_openrouter(prompt, model, max_tokens=2048, temperature=0.7):
    """Make a single API call to OpenRouter."""
    global cumulative_cost, total_api_calls

    if cumulative_cost >= BUDGET_LIMIT_USD:
        return {"text": "BUDGET_EXCEEDED", "success": False, "cost_usd": 0,
                "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0, "model": model}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/DreamOS-Network/Arrival-Protocol",
        "X-Title": "ARRIVAL Phase 19 Binding-Only Ablation",
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
                "text": text, "model": model,
                "prompt_tokens": pt, "completion_tokens": ct,
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
# Binding-Only R4 Prompt (no prior debate)
# ============================================================

BINDING_ONLY_R4_TEMPLATE = """You are Epsilon, the mediator and allocator for a shared fishing pond.

{system_base}

=== BINDING ALLOCATION (No Prior Debate) ===

You must allocate fish harvests for 5 fishers. There has been NO prior discussion
or debate — you are making this decision based solely on the game state.

CURRENT STATE:
- Fish in pond: {stock}
- Month: {month}/{total_months}
- Maximum safe total harvest: {max_safe_harvest}
- Fair share per fisher: ~{fair_share}
- Months remaining: {months_remaining}
- Minimum fish for pond survival: {collapse_threshold}

{history_text}

GAME MECHANICS:
- After harvest, remaining fish DOUBLE (up to max {max_capacity})
- If stock drops below {collapse_threshold}, the pond COLLAPSES permanently
- Goal: survive all {total_months} months

YOUR TASK: Produce a BINDING ALLOCATION using this exact format:
@ALLOCATION[alpha=N, beta=N, gamma=N, delta=N, epsilon=N]

Rules:
1. Total allocation MUST NOT exceed {max_safe_harvest} fish
2. Prioritize long-term sustainability
3. Consider the doubling mechanic — leaving more fish means more next month
4. Explain your allocation logic briefly"""


def run_binding_only_month(env: FishPondEnv, month: int, verbose: bool = True) -> Dict[str, Any]:
    """Execute one month with only R4 binding allocation (no R1/R2 debate)."""
    agent_names = list(GOVSIM_MODELS.keys())
    fair_share = env.get_fair_share()
    max_safe = env.get_max_safe_harvest()
    stock = env.stock
    history_text = env.format_history_for_prompt()

    month_result = {
        "month": month,
        "stock": stock,
        "fair_share": round(fair_share, 1),
        "r4": {},
        "final_harvests": {},
        "api_calls": 0,
        "month_cost": 0.0,
    }

    # ONLY R4: Direct allocation without debate
    prompt = BINDING_ONLY_R4_TEMPLATE.format(
        system_base=ARRIVAL_SYSTEM_BASE,
        stock=int(stock),
        month=month,
        total_months=N_MONTHS,
        max_safe_harvest=int(max_safe),
        fair_share=int(fair_share),
        months_remaining=N_MONTHS - month + 1,
        collapse_threshold=COLLAPSE_THRESHOLD,
        max_capacity=MAX_CAPACITY,
        history_text=history_text,
    )

    epsilon_model = GOVSIM_MODELS["epsilon"]["model_id"]
    epsilon_short = MODEL_SHORT.get(epsilon_model, epsilon_model)

    if verbose:
        print(f"    R4-only: epsilon [{epsilon_short}]...", end=" ", flush=True)

    r4_resp = call_openrouter(prompt, epsilon_model, max_tokens=ARRIVAL_MAX_TOKENS_R4)
    month_result["api_calls"] += 1
    month_result["month_cost"] += r4_resp["cost_usd"]

    # Extract allocation
    allocation = extract_r4_allocation(r4_resp["text"], agent_names)

    # Fallback: equal fair share
    if not allocation or len(allocation) < len(agent_names):
        if verbose:
            print(f"extraction failed, using equal fair_share={int(fair_share)}")
        allocation = {a: int(fair_share) for a in agent_names}
    else:
        if verbose:
            alloc_str = ", ".join(f"{a}={allocation.get(a, '?')}" for a in agent_names)
            print(f"@ALLOCATION[{alloc_str}]")

    # Safety clamp
    total_alloc = sum(allocation.get(a, 0) for a in agent_names)
    if total_alloc > max_safe:
        scale = max_safe / total_alloc if total_alloc > 0 else 1.0
        allocation = {a: int(allocation.get(a, 0) * scale) for a in agent_names}
        if verbose:
            print(f"      Clamped: total {total_alloc}->{sum(allocation.values())} (max_safe={int(max_safe)})")

    month_result["r4"] = {
        "text": r4_resp["text"][:500],
        "allocation": allocation,
        "model": r4_resp["model"],
        "cost": r4_resp["cost_usd"],
        "clamped": total_alloc > max_safe,
    }
    month_result["final_harvests"] = allocation
    month_result["month_cost"] = round(month_result["month_cost"], 4)

    time.sleep(SLEEP_BETWEEN_CALLS)
    return month_result


def run_binding_only_game(run_id: int, seed: int) -> dict:
    """Run a single 12-month binding-only game."""
    print(f"\n{'='*60}")
    print(f"  CONDITION D: BINDING-ONLY — Run {run_id+1} (seed={seed})")
    print(f"{'='*60}")

    env = FishPondEnv(
        initial_stock=INITIAL_STOCK,
        max_capacity=MAX_CAPACITY,
        collapse_threshold=COLLAPSE_THRESHOLD,
        n_months=N_MONTHS,
    )

    game_log = []

    for month in range(1, N_MONTHS + 1):
        if env.collapsed:
            break

        print(f"\n  Month {month}/{N_MONTHS} | Stock: {env.stock:.0f}")

        month_result = run_binding_only_month(env, month)
        state = env.step(month_result["final_harvests"])

        month_result["state_after"] = {
            "stock_after_harvest": state.stock_after_harvest,
            "stock_after_replenish": state.stock_after_replenish,
            "collapsed": state.collapsed,
        }
        game_log.append(month_result)

        if state.collapsed:
            print(f"\n  COLLAPSED at month {month}! Stock: {state.stock_after_harvest:.0f}")
            break
        else:
            print(f"    Result: {state.stock_after_harvest:.0f} -> replenish -> {state.stock_after_replenish:.0f}")

    survived = env.is_survived()
    months_survived = env.get_months_survived()
    gini = env.compute_gini_coefficient()

    print(f"\n  RESULT: {'SURVIVED' if survived else 'COLLAPSED'} "
          f"({months_survived} months, Gini={gini:.3f})")

    return {
        "condition": "D_binding_only",
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


def main():
    global cumulative_cost, total_api_calls

    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set!")
        sys.exit(1)

    print("=" * 60)
    print("  PHASE 19: GovSim — CONDITION D (BINDING-ONLY ABLATION)")
    print(f"  Runs: {N_RUNS} | Months: {N_MONTHS} | Agents: {N_AGENTS}")
    print(f"  Expected API calls: 1 x {N_MONTHS} x {N_RUNS} = {1 * N_MONTHS * N_RUNS}")
    print("=" * 60)

    all_results = []
    start_time = datetime.now(timezone.utc)

    for i in range(N_RUNS):
        result = run_binding_only_game(i, RANDOM_SEEDS[i])
        all_results.append(result)

    # Save
    output = {
        "experiment": "phase19_govsim",
        "condition": "D_binding_only",
        "timestamp": start_time.isoformat(),
        "duration_s": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "total_api_calls": total_api_calls,
        "total_cost_usd": round(cumulative_cost, 4),
        "n_runs": N_RUNS,
        "survival_rate": sum(1 for r in all_results if r["survived"]) / N_RUNS,
        "avg_months_survived": sum(r["months_survived"] for r in all_results) / N_RUNS,
        "runs": all_results,
    }

    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(results_dir, f"binding_only_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  CONDITION D COMPLETE")
    print(f"  Survival rate: {output['survival_rate']:.0%}")
    print(f"  Avg months survived: {output['avg_months_survived']:.1f}")
    print(f"  Total cost: ${output['total_cost_usd']:.4f}")
    print(f"  API calls: {output['total_api_calls']}")
    print(f"  Saved: {out_path}")
    print(f"{'='*60}")

    return output


if __name__ == "__main__":
    main()
