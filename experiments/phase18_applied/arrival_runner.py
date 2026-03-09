# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 18: ARRIVAL Protocol Runner (Shared)
===========================================
Core 4-round ARRIVAL execution logic used by both Task 1 and Task 2.
Handles: R1 (independent), R2 (cross-critique), R3 (CRDT overlay), R4 (synthesis).

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Add parent dirs to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from config_phase18 import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, BUDGET_LIMIT_USD,
    SLEEP_BETWEEN_CALLS, REQUEST_TIMEOUT,
    ARRIVAL_MODELS, MODEL_COSTS, MODEL_SHORT,
    ARRIVAL_SYSTEM_BASE, ARRIVAL_R1_TEMPLATE, ARRIVAL_R2_TEMPLATE, ARRIVAL_R4_TEMPLATE,
    ARRIVAL_TEMPERATURE, ARRIVAL_MAX_TOKENS_R1, ARRIVAL_MAX_TOKENS_R2, ARRIVAL_MAX_TOKENS_R4,
    CARE_ALERT_THRESHOLD,
)

# Import CRDT metrics for Round 3
try:
    from arrival.crdt_metrics import compute_care_resolve, compute_meaning_debt
    HAS_CRDT = True
except ImportError:
    HAS_CRDT = False
    print("  WARNING: arrival.crdt_metrics not available, CRDT overlay will use dummy values")

# Import memory modules for Condition C
try:
    from arrival.memory.schema import memory_from_dict, ProceduralMemory, SemanticMemory, EpisodicMemory
    from arrival.memory.care_alert import should_inject_memory, select_relevant_memories
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False
    print("  WARNING: arrival.memory not available, memory injection will be skipped")


def call_openrouter(prompt: str, model: str, system_prompt: str = "",
                    max_tokens: int = 4096, temperature: float = 0.7) -> Dict[str, Any]:
    """Make a single API call to OpenRouter."""
    api_key = OPENROUTER_API_KEY
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/mifkilla/Arrival-Protocol",
        "X-Title": "ARRIVAL Protocol Phase 18",
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
                print(f"    Rate limited, waiting {retry_after}s (attempt {attempt+1}/3)")
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            data = resp.json()

            text = ""
            choices = data.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")

            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            # Calculate cost
            costs = MODEL_COSTS.get(model, {"input": 1.0, "output": 2.0})
            cost = (prompt_tokens * costs["input"] + completion_tokens * costs["output"]) / 1_000_000

            latency_ms = (time.time() - start_time) * 1000

            return {
                "text": text,
                "model": model,
                "model_short": MODEL_SHORT.get(model, model),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost,
                "latency_ms": latency_ms,
                "success": True,
            }

        except requests.exceptions.RequestException as e:
            if attempt < 2:
                print(f"    Error: {e}, retrying in 5s...")
                time.sleep(5)
            else:
                return {
                    "text": f"ERROR: {e}",
                    "model": model,
                    "model_short": MODEL_SHORT.get(model, model),
                    "prompt_tokens": 0, "completion_tokens": 0,
                    "cost_usd": 0.0, "latency_ms": 0.0,
                    "success": False,
                }

    return {"text": "ERROR: Max retries exceeded", "model": model, "success": False,
            "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "latency_ms": 0.0,
            "model_short": MODEL_SHORT.get(model, model)}


def run_arrival_4rounds(task_prompt: str, use_memory: bool = False,
                        memory_seeds_path: Optional[str] = None,
                        verbose: bool = True) -> Dict[str, Any]:
    """
    Execute full ARRIVAL 4-round protocol.

    Args:
        task_prompt: The task description
        use_memory: Whether to use CARE-ALERT memory injection (Condition C)
        memory_seeds_path: Path to memory seeds JSON (for Condition C)
        verbose: Print progress

    Returns:
        Dict with all round data, metrics, and final answer
    """
    result = {
        "protocol": "ARRIVAL",
        "use_memory": use_memory,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rounds": {},
        "metrics": {},
        "final_answer": "",
        "total_cost_usd": 0.0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_calls": 0,
        "memory_injections": [],
    }

    agent_names = list(ARRIVAL_MODELS.keys())  # alpha, beta, gamma, delta, epsilon

    # ================================================================
    # ROUND 1: Independent Analysis (5 API calls)
    # ================================================================
    if verbose:
        print("\n  === ROUND 1: INDEPENDENT ANALYSIS ===")

    r1_responses = {}
    for agent_name in agent_names:
        agent = ARRIVAL_MODELS[agent_name]
        model_id = agent["model_id"]
        short = MODEL_SHORT.get(model_id, model_id)

        prompt = ARRIVAL_R1_TEMPLATE.format(
            persona=agent["persona"],
            system_base=ARRIVAL_SYSTEM_BASE,
            task_prompt=task_prompt,
        )

        if verbose:
            print(f"    R1 [{short}] calling...", end=" ", flush=True)

        resp = call_openrouter(
            prompt=prompt, model=model_id,
            max_tokens=ARRIVAL_MAX_TOKENS_R1,
            temperature=ARRIVAL_TEMPERATURE,
        )

        r1_responses[agent_name] = resp
        result["total_cost_usd"] += resp["cost_usd"]
        result["total_prompt_tokens"] += resp["prompt_tokens"]
        result["total_completion_tokens"] += resp["completion_tokens"]
        result["total_calls"] += 1

        if verbose:
            print(f"done ({resp['completion_tokens']} tok, ${resp['cost_usd']:.4f})")

        time.sleep(SLEEP_BETWEEN_CALLS)

    result["rounds"]["r1"] = {name: {"text": r["text"], "model": r["model"],
                                      "tokens": r["prompt_tokens"] + r["completion_tokens"],
                                      "cost": r["cost_usd"]}
                              for name, r in r1_responses.items()}

    # ================================================================
    # ROUND 2: Cross-Critique (5 API calls)
    # ================================================================
    if verbose:
        print("\n  === ROUND 2: CROSS-CRITIQUE ===")

    r2_responses = {}
    for agent_name in agent_names:
        agent = ARRIVAL_MODELS[agent_name]
        model_id = agent["model_id"]
        short = MODEL_SHORT.get(model_id, model_id)

        # Build others' R1 responses (truncated)
        others_text = ""
        for other_name in agent_names:
            if other_name != agent_name:
                other_resp = r1_responses[other_name]
                other_short = MODEL_SHORT.get(other_resp["model"], other_resp["model"])
                truncated = other_resp["text"][:3000]
                others_text += f"\n--- {other_name.upper()} ({other_short}) ---\n{truncated}\n"

        prompt = ARRIVAL_R2_TEMPLATE.format(
            persona=agent["persona"],
            system_base=ARRIVAL_SYSTEM_BASE,
            own_r1=r1_responses[agent_name]["text"][:3000],
            others_r1=others_text,
            task_prompt=task_prompt,
        )

        if verbose:
            print(f"    R2 [{short}] critiquing...", end=" ", flush=True)

        resp = call_openrouter(
            prompt=prompt, model=model_id,
            max_tokens=ARRIVAL_MAX_TOKENS_R2,
            temperature=ARRIVAL_TEMPERATURE,
        )

        r2_responses[agent_name] = resp
        result["total_cost_usd"] += resp["cost_usd"]
        result["total_prompt_tokens"] += resp["prompt_tokens"]
        result["total_completion_tokens"] += resp["completion_tokens"]
        result["total_calls"] += 1

        if verbose:
            print(f"done ({resp['completion_tokens']} tok, ${resp['cost_usd']:.4f})")

        time.sleep(SLEEP_BETWEEN_CALLS)

    result["rounds"]["r2"] = {name: {"text": r["text"], "model": r["model"],
                                      "tokens": r["prompt_tokens"] + r["completion_tokens"],
                                      "cost": r["cost_usd"]}
                              for name, r in r2_responses.items()}

    # ================================================================
    # ROUND 3: CRDT Overlay (0 API calls)
    # ================================================================
    if verbose:
        print("\n  === ROUND 3: CRDT OVERLAY ===")

    # Build structured dialogue for CRDT analysis (List[Dict] format)
    dialogue_structured = []
    for name in agent_names:
        dialogue_structured.append({
            "round": 1, "from": name, "message": r1_responses[name]["text"]
        })
    for name in agent_names:
        dialogue_structured.append({
            "round": 2, "from": name, "message": r2_responses[name]["text"]
        })

    if HAS_CRDT:
        try:
            care_result = compute_care_resolve(dialogue_structured, task_type="open")
            care_resolve = care_result.get("care_resolve", 0.5) if isinstance(care_result, dict) else care_result
            md_result = compute_meaning_debt(dialogue_structured)
            meaning_debt = md_result.get("meaning_debt", 0.3) if isinstance(md_result, dict) else md_result
        except Exception as e:
            if verbose:
                print(f"    CRDT computation error: {e}, using defaults")
            care_resolve = 0.5
            meaning_debt = 0.3
    else:
        care_resolve = 0.5
        meaning_debt = 0.3

    result["metrics"]["care_resolve"] = care_resolve
    result["metrics"]["meaning_debt"] = meaning_debt

    if verbose:
        print(f"    CARE Resolve: {care_resolve:.3f}")
        print(f"    Meaning Debt: {meaning_debt:.3f}")

    # ================================================================
    # CARE-ALERT Memory Injection (Condition C only)
    # ================================================================
    memory_injection_text = ""

    if use_memory and memory_seeds_path:
        if verbose:
            print("\n  === CARE-ALERT CHECK ===")

        if care_resolve < CARE_ALERT_THRESHOLD:
            if verbose:
                print(f"    CARE ({care_resolve:.3f}) < threshold ({CARE_ALERT_THRESHOLD}) → INJECTING MEMORY")

            # Load memory seeds
            try:
                with open(memory_seeds_path, "r", encoding="utf-8") as f:
                    seeds_data = json.load(f)

                memories = seeds_data.get("memories", [])
                # Format memories for injection
                injection_parts = ["@CARE.ALERT: Consensus is low. Relevant prior knowledge:"]
                for mem in memories:
                    layer = mem.get("layer", "")
                    if layer == "procedural":
                        injection_parts.append(
                            f"  @MEMORY.PROCEDURAL [{mem.get('strategy_name', '')}]: "
                            f"{mem.get('description', '')} "
                            f"(success_rate={mem.get('success_rate', 0):.0%})"
                        )
                    elif layer == "semantic":
                        injection_parts.append(
                            f"  @MEMORY.SEMANTIC [{mem.get('domain', '')}]: "
                            f"{mem.get('rule', '')}"
                        )
                    elif layer == "episodic":
                        injection_parts.append(
                            f"  @MEMORY.EPISODIC: Past task '{mem.get('task', '')}' → "
                            f"Insight: {mem.get('key_insight', '')}"
                        )

                memory_injection_text = "\n".join(injection_parts)
                result["memory_injections"].append({
                    "trigger": f"CARE={care_resolve:.3f} < {CARE_ALERT_THRESHOLD}",
                    "memories_injected": len(memories),
                    "injection_text": memory_injection_text,
                })

                if verbose:
                    print(f"    Injected {len(memories)} memories")

            except Exception as e:
                if verbose:
                    print(f"    Memory load error: {e}")
        else:
            if verbose:
                print(f"    CARE ({care_resolve:.3f}) >= threshold ({CARE_ALERT_THRESHOLD}) → no injection needed")
    elif use_memory:
        if verbose:
            print("    WARNING: use_memory=True but no memory_seeds_path provided")

    # ================================================================
    # ROUND 4: Final Synthesis (1 API call — Alpha)
    # ================================================================
    if verbose:
        print("\n  === ROUND 4: FINAL SYNTHESIS ===")

    # Compile all R1 and R2 texts
    all_r1_text = ""
    for name in agent_names:
        short = MODEL_SHORT.get(r1_responses[name]["model"], r1_responses[name]["model"])
        all_r1_text += f"\n--- {name.upper()} ({short}) ---\n{r1_responses[name]['text'][:4000]}\n"

    all_r2_text = ""
    for name in agent_names:
        short = MODEL_SHORT.get(r2_responses[name]["model"], r2_responses[name]["model"])
        all_r2_text += f"\n--- {name.upper()} ({short}) ---\n{r2_responses[name]['text'][:3000]}\n"

    # Memory injection section
    memory_section = ""
    if memory_injection_text:
        memory_section = f"\n=== CARE-ALERT MEMORY INJECTION ===\n{memory_injection_text}\n"

    prompt = ARRIVAL_R4_TEMPLATE.format(
        system_base=ARRIVAL_SYSTEM_BASE,
        all_r1=all_r1_text,
        all_r2=all_r2_text,
        memory_injection=memory_section,
        task_prompt=task_prompt,
    )

    alpha_model = ARRIVAL_MODELS["alpha"]["model_id"]
    alpha_short = MODEL_SHORT.get(alpha_model, alpha_model)

    if verbose:
        print(f"    R4 [{alpha_short}] synthesizing...", end=" ", flush=True)

    resp = call_openrouter(
        prompt=prompt, model=alpha_model,
        max_tokens=ARRIVAL_MAX_TOKENS_R4,
        temperature=ARRIVAL_TEMPERATURE,
    )

    result["rounds"]["r4"] = {
        "text": resp["text"],
        "model": resp["model"],
        "tokens": resp["prompt_tokens"] + resp["completion_tokens"],
        "cost": resp["cost_usd"],
    }
    result["final_answer"] = resp["text"]
    result["total_cost_usd"] += resp["cost_usd"]
    result["total_prompt_tokens"] += resp["prompt_tokens"]
    result["total_completion_tokens"] += resp["completion_tokens"]
    result["total_calls"] += 1

    if verbose:
        print(f"done ({resp['completion_tokens']} tok, ${resp['cost_usd']:.4f})")
        print(f"\n  TOTAL: {result['total_calls']} calls, "
              f"{result['total_prompt_tokens'] + result['total_completion_tokens']:,} tokens, "
              f"${result['total_cost_usd']:.4f}")

    return result
