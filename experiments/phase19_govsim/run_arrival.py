# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: Condition B — ARRIVAL Protocol Runner
=================================================
4-round ARRIVAL per month × 12 months × 5 agents.

Per month:
  R1: 5 independent harvest proposals (5 API calls)
  R2: 5 cross-critiques seeing all proposals (5 API calls)
  R3: CRDT overlay — compute CARE Resolve + Meaning Debt (0 calls)
  R4: Epsilon synthesizer → binding @ALLOCATION (1 API call)

Total: 11 calls/month × 12 months × 3 runs = 396 API calls.
Expected: 2/3 or 3/3 survival (67-100%).

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_phase19 import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, BUDGET_LIMIT_USD,
    SLEEP_BETWEEN_CALLS, REQUEST_TIMEOUT,
    GOVSIM_MODELS, MODEL_COSTS, MODEL_SHORT, AGENT_DISPLAY_NAMES,
    ARRIVAL_SYSTEM_BASE, GOVSIM_R1_TEMPLATE, GOVSIM_R2_TEMPLATE, GOVSIM_R4_TEMPLATE,
    ARRIVAL_TEMPERATURE, ARRIVAL_MAX_TOKENS_R1, ARRIVAL_MAX_TOKENS_R2, ARRIVAL_MAX_TOKENS_R4,
    INITIAL_STOCK, MAX_CAPACITY, COLLAPSE_THRESHOLD,
    N_MONTHS, N_AGENTS, N_RUNS, RANDOM_SEEDS,
)
from govsim_env import FishPondEnv
from harvest_extraction import (
    extract_harvest_amount, extract_r4_allocation,
    compute_harvest_greediness, extract_cooperative_atoms,
)
from govsim_care_alert import compute_govsim_interim_metrics

# ============================================================
# API Client
# ============================================================
cumulative_cost = 0.0
total_api_calls = 0


def call_openrouter(prompt, model, system_prompt="",
                    max_tokens=2048, temperature=0.7):
    """Make a single API call to OpenRouter."""
    global cumulative_cost, total_api_calls

    if cumulative_cost >= BUDGET_LIMIT_USD:
        return {"text": "BUDGET_EXCEEDED", "success": False, "cost_usd": 0,
                "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0, "model": model}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/mifkilla/Arrival-Protocol",
        "X-Title": "ARRIVAL Phase 19 GovSim",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

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
# Single Month: 4-Round ARRIVAL
# ============================================================

def run_arrival_month(
    env: FishPondEnv,
    month: int,
    memory_injection_text: str = "",
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Execute one month of ARRIVAL protocol (4 rounds).

    Returns:
        Dict with R1-R4 data, CRDT metrics, final harvests
    """
    agent_names = list(GOVSIM_MODELS.keys())
    fair_share = env.get_fair_share()
    max_safe = env.get_max_safe_harvest()
    stock = env.stock
    history_text = env.format_history_for_prompt()

    month_result = {
        "month": month,
        "stock": stock,
        "fair_share": round(fair_share, 1),
        "r1": {}, "r2": {}, "r3_metrics": {}, "r4": {},
        "final_harvests": {},
        "api_calls": 0,
        "month_cost": 0.0,
    }

    # ================================================================
    # ROUND 1: Independent Harvest Proposals (5 calls)
    # ================================================================
    if verbose:
        print(f"\n    R1: Independent proposals...")

    r1_responses = {}
    r1_harvests = {}

    for agent_name in agent_names:
        agent = GOVSIM_MODELS[agent_name]
        model_id = agent["model_id"]
        short = MODEL_SHORT.get(model_id, model_id)

        prompt = GOVSIM_R1_TEMPLATE.format(
            persona=agent["persona"],
            system_base=ARRIVAL_SYSTEM_BASE,
            n_agents=N_AGENTS,
            max_capacity=MAX_CAPACITY,
            collapse_threshold=COLLAPSE_THRESHOLD,
            stock=int(stock),
            month=month,
            total_months=N_MONTHS,
            fair_share=int(fair_share),
            months_remaining=N_MONTHS - month + 1,
            history_text=history_text,
        )

        if verbose:
            print(f"      {agent_name} [{short}]...", end=" ", flush=True)

        resp = call_openrouter(prompt, model_id, max_tokens=ARRIVAL_MAX_TOKENS_R1)
        r1_responses[agent_name] = resp
        month_result["api_calls"] += 1
        month_result["month_cost"] += resp["cost_usd"]

        harvest = extract_harvest_amount(resp["text"], fallback=int(fair_share))
        r1_harvests[agent_name] = harvest

        if verbose:
            print(f"@HARVEST={harvest} (fair={fair_share:.0f})")

        time.sleep(SLEEP_BETWEEN_CALLS)

    month_result["r1"] = {
        name: {
            "text": r["text"][:500],
            "harvest": r1_harvests[name],
            "model": r["model"],
            "cost": r["cost_usd"],
            "atoms": extract_cooperative_atoms(r["text"]),
        }
        for name, r in r1_responses.items()
    }

    # ================================================================
    # ROUND 2: Cross-Critique (5 calls)
    # ================================================================
    if verbose:
        print(f"    R2: Cross-critique...")

    r2_responses = {}
    r2_harvests = {}

    for agent_name in agent_names:
        agent = GOVSIM_MODELS[agent_name]
        model_id = agent["model_id"]
        short = MODEL_SHORT.get(model_id, model_id)

        # Build others' R1 proposals
        others_text = ""
        for other in agent_names:
            if other != agent_name:
                other_short = MODEL_SHORT.get(r1_responses[other]["model"], "")
                truncated = r1_responses[other]["text"][:1500]
                others_text += f"\n--- {AGENT_DISPLAY_NAMES[other]} ({other_short}) [harvest={r1_harvests[other]}] ---\n{truncated}\n"

        prompt = GOVSIM_R2_TEMPLATE.format(
            persona=agent["persona"],
            system_base=ARRIVAL_SYSTEM_BASE,
            stock=int(stock),
            month=month,
            total_months=N_MONTHS,
            fair_share=int(fair_share),
            own_r1=r1_responses[agent_name]["text"][:1500],
            others_r1=others_text,
        )

        if verbose:
            print(f"      {agent_name} [{short}]...", end=" ", flush=True)

        resp = call_openrouter(prompt, model_id, max_tokens=ARRIVAL_MAX_TOKENS_R2)
        r2_responses[agent_name] = resp
        month_result["api_calls"] += 1
        month_result["month_cost"] += resp["cost_usd"]

        # Check if agent revised their harvest
        revised = extract_harvest_amount(resp["text"])
        r2_harvests[agent_name] = revised if revised is not None else r1_harvests[agent_name]

        if verbose:
            rev_str = f"→{revised}" if revised is not None and revised != r1_harvests[agent_name] else "(kept)"
            print(f"critique done {rev_str}")

        time.sleep(SLEEP_BETWEEN_CALLS)

    month_result["r2"] = {
        name: {
            "text": r["text"][:500],
            "revised_harvest": r2_harvests[name],
            "model": r["model"],
            "cost": r["cost_usd"],
            "atoms": extract_cooperative_atoms(r["text"]),
        }
        for name, r in r2_responses.items()
    }

    # ================================================================
    # ROUND 3: CRDT Overlay (0 API calls)
    # ================================================================
    if verbose:
        print(f"    R3: CRDT overlay...")

    # Use R2 revised harvests for CRDT computation
    interim = compute_govsim_interim_metrics(r2_harvests, fair_share, stock)

    care_resolve = interim.get("care_resolve", 0.5)
    meaning_debt = interim.get("meaning_debt", 0.3)

    month_result["r3_metrics"] = interim

    if verbose:
        print(f"      CARE={care_resolve:.3f}, MD={meaning_debt:.3f}")
        if interim.get("minority_agent"):
            print(f"      Minority: {interim['minority_agent']} "
                  f"(loss={interim['minority_loss']:.3f})")

    # ================================================================
    # ROUND 4: Binding Allocation by Epsilon (1 call)
    # ================================================================
    if verbose:
        print(f"    R4: Binding allocation...")

    all_r1_text = ""
    for name in agent_names:
        short = MODEL_SHORT.get(r1_responses[name]["model"], "")
        all_r1_text += (
            f"\n--- {AGENT_DISPLAY_NAMES[name]} ({short}) "
            f"[proposed: {r1_harvests[name]} fish] ---\n"
            f"{r1_responses[name]['text'][:2000]}\n"
        )

    all_r2_text = ""
    for name in agent_names:
        short = MODEL_SHORT.get(r2_responses[name]["model"], "")
        all_r2_text += (
            f"\n--- {AGENT_DISPLAY_NAMES[name]} ({short}) "
            f"[revised: {r2_harvests[name]} fish] ---\n"
            f"{r2_responses[name]['text'][:1500]}\n"
        )

    # Memory injection slot (empty for Condition B)
    memory_section = ""
    if memory_injection_text:
        memory_section = f"\n=== CARE-ALERT MEMORY INJECTION ===\n{memory_injection_text}\n"

    prompt = GOVSIM_R4_TEMPLATE.format(
        system_base=ARRIVAL_SYSTEM_BASE,
        stock=int(stock),
        month=month,
        total_months=N_MONTHS,
        max_safe_harvest=int(max_safe),
        fair_share=int(fair_share),
        care_resolve=care_resolve,
        meaning_debt=meaning_debt,
        all_r1=all_r1_text,
        all_r2=all_r2_text,
        memory_injection=memory_section,
    )

    epsilon_model = GOVSIM_MODELS["epsilon"]["model_id"]
    epsilon_short = MODEL_SHORT.get(epsilon_model, epsilon_model)

    if verbose:
        print(f"      epsilon [{epsilon_short}]...", end=" ", flush=True)

    r4_resp = call_openrouter(prompt, epsilon_model, max_tokens=ARRIVAL_MAX_TOKENS_R4)
    month_result["api_calls"] += 1
    month_result["month_cost"] += r4_resp["cost_usd"]

    # Extract allocation
    allocation = extract_r4_allocation(r4_resp["text"], agent_names)

    # Fallback: if extraction failed, use R2 revised harvests with clamping
    if not allocation or len(allocation) < len(agent_names):
        if verbose:
            print(f"extraction partial ({len(allocation)}/{len(agent_names)}), using R2 fallback")
        allocation = dict(r2_harvests)
    else:
        if verbose:
            alloc_str = ", ".join(f"{a}={allocation.get(a, '?')}" for a in agent_names)
            print(f"@ALLOCATION[{alloc_str}]")

    # Safety clamp: total must not exceed max_safe_harvest
    total_alloc = sum(allocation.get(a, 0) for a in agent_names)
    if total_alloc > max_safe:
        scale = max_safe / total_alloc if total_alloc > 0 else 1.0
        allocation = {a: int(allocation.get(a, 0) * scale) for a in agent_names}
        if verbose:
            print(f"      Clamped: total {total_alloc}→{sum(allocation.values())} (max_safe={int(max_safe)})")

    month_result["r4"] = {
        "text": r4_resp["text"][:500],
        "allocation": allocation,
        "model": r4_resp["model"],
        "cost": r4_resp["cost_usd"],
        "clamped": total_alloc > max_safe,
    }
    month_result["final_harvests"] = allocation
    month_result["month_cost"] = round(month_result["month_cost"], 4)

    return month_result


# ============================================================
# Full Game Runner
# ============================================================

def run_arrival_game(run_id: int, seed: int,
                     use_memory: bool = False,
                     memory_seeds_path: str = "") -> dict:
    """Run a single 12-month ARRIVAL game."""
    condition = "C_arrival_memory" if use_memory else "B_arrival"
    label = "ARRIVAL+Memory" if use_memory else "ARRIVAL"

    print(f"\n{'='*60}")
    print(f"  CONDITION {'C' if use_memory else 'B'}: {label} — Run {run_id+1} (seed={seed})")
    print(f"{'='*60}")

    env = FishPondEnv(
        initial_stock=INITIAL_STOCK,
        max_capacity=MAX_CAPACITY,
        collapse_threshold=COLLAPSE_THRESHOLD,
        n_months=N_MONTHS,
    )

    game_log = []
    care_trajectory = []
    md_trajectory = []
    memory_injections = []

    for month in range(1, N_MONTHS + 1):
        if env.collapsed:
            break

        print(f"\n  Month {month}/{N_MONTHS} | Stock: {env.stock:.0f}")

        # Memory injection for Condition C
        memory_text = ""
        if use_memory and memory_seeds_path:
            memory_text = _prepare_memory_injection(
                month, env, game_log, memory_seeds_path, memory_injections
            )

        # Run 4-round ARRIVAL for this month
        month_result = run_arrival_month(env, month, memory_injection_text=memory_text)

        # Execute month with ARRIVAL's binding allocation
        state = env.step(month_result["final_harvests"])

        # Track metrics
        care = month_result["r3_metrics"].get("care_resolve", 0.5)
        md = month_result["r3_metrics"].get("meaning_debt", 0.3)
        care_trajectory.append(care)
        md_trajectory.append(md)

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
            print(f"    Result: {state.stock_after_harvest:.0f} → replenish → {state.stock_after_replenish:.0f}")

    survived = env.is_survived()
    months_survived = env.get_months_survived()
    gini = env.compute_gini_coefficient()
    total_month_cost = sum(m["month_cost"] for m in game_log)

    print(f"\n  RESULT: {'SURVIVED' if survived else 'COLLAPSED'} "
          f"({months_survived} months, CARE_avg={sum(care_trajectory)/len(care_trajectory):.3f}, "
          f"Gini={gini:.3f})")

    return {
        "condition": condition,
        "run_id": run_id,
        "seed": seed,
        "survived": survived,
        "months_survived": months_survived,
        "gini_coefficient": round(gini, 4),
        "final_stock": env.stock,
        "cumulative_harvests": env.cumulative_harvests,
        "resource_trajectory": env.get_resource_trajectory(),
        "care_trajectory": care_trajectory,
        "md_trajectory": md_trajectory,
        "care_avg": round(sum(care_trajectory) / len(care_trajectory), 4) if care_trajectory else 0,
        "md_avg": round(sum(md_trajectory) / len(md_trajectory), 4) if md_trajectory else 0,
        "memory_injections": memory_injections,
        "game_log": game_log,
        "game_cost_usd": round(total_month_cost, 4),
        "env_state": env.to_dict(),
    }


def _prepare_memory_injection(month, env, game_log, memory_seeds_path, injections_log):
    """Check CARE-ALERT and prepare memory injection for Condition C."""
    from govsim_care_alert import should_fire_govsim_alert, generate_govsim_alert

    # Need at least 1 previous month with metrics
    if not game_log:
        return ""

    last_metrics = game_log[-1].get("r3_metrics", {})
    if last_metrics.get("error"):
        return ""

    should_fire, reason = should_fire_govsim_alert(last_metrics)
    if not should_fire:
        return ""

    # Generate alert
    alert = generate_govsim_alert(last_metrics, month, reason)

    # Load memory seeds
    try:
        with open(memory_seeds_path, "r", encoding="utf-8") as f:
            seeds_data = json.load(f)

        memories = seeds_data.get("memories", [])
        parts = [alert]
        for mem in memories:
            layer = mem.get("layer", "")
            if layer == "procedural":
                parts.append(
                    f"  @MEMORY.PROCEDURAL [{mem.get('strategy_name', '')}]: "
                    f"{mem.get('description', '')}"
                )
            elif layer == "semantic":
                parts.append(
                    f"  @MEMORY.SEMANTIC [{mem.get('domain', '')}]: "
                    f"{mem.get('rule', '')}"
                )
            elif layer == "episodic":
                parts.append(
                    f"  @MEMORY.EPISODIC: Past scenario → "
                    f"Insight: {mem.get('key_insight', '')}"
                )

        injection_text = "\n".join(parts)
        injections_log.append({
            "month": month,
            "trigger": reason,
            "memories_injected": len(memories),
        })
        print(f"    CARE-ALERT FIRED: {reason} → injecting {len(memories)} memories")
        return injection_text

    except Exception as e:
        print(f"    Memory load error: {e}")
        return ""


# ============================================================
# Main — Condition B
# ============================================================

def main():
    global cumulative_cost, total_api_calls

    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set!")
        sys.exit(1)

    print("=" * 60)
    print("  PHASE 19: GovSim — CONDITION B (ARRIVAL)")
    print(f"  Runs: {N_RUNS} | Months: {N_MONTHS} | Agents: {N_AGENTS}")
    print(f"  Expected API calls: 11 × {N_MONTHS} × {N_RUNS} = {11 * N_MONTHS * N_RUNS}")
    print("=" * 60)

    all_results = []
    start_time = datetime.now(timezone.utc)

    for i in range(N_RUNS):
        result = run_arrival_game(i, RANDOM_SEEDS[i], use_memory=False)
        all_results.append(result)

    # Save
    output = {
        "experiment": "phase19_govsim",
        "condition": "B_arrival",
        "timestamp": start_time.isoformat(),
        "duration_s": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "total_api_calls": total_api_calls,
        "total_cost_usd": round(cumulative_cost, 4),
        "n_runs": N_RUNS,
        "survival_rate": sum(1 for r in all_results if r["survived"]) / N_RUNS,
        "avg_months_survived": sum(r["months_survived"] for r in all_results) / N_RUNS,
        "avg_care": sum(r["care_avg"] for r in all_results) / N_RUNS,
        "avg_md": sum(r["md_avg"] for r in all_results) / N_RUNS,
        "runs": all_results,
    }

    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(results_dir, f"arrival_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  CONDITION B COMPLETE")
    print(f"  Survival rate: {output['survival_rate']:.0%}")
    print(f"  Avg months survived: {output['avg_months_survived']:.1f}")
    print(f"  Avg CARE: {output['avg_care']:.3f}")
    print(f"  Avg MD: {output['avg_md']:.3f}")
    print(f"  Total cost: ${output['total_cost_usd']:.4f}")
    print(f"  API calls: {output['total_api_calls']}")
    print(f"  Saved: {out_path}")
    print(f"{'='*60}")

    return output


if __name__ == "__main__":
    main()
