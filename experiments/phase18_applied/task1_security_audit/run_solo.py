# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 18 Task 1 — Condition A: Solo Claude Sonnet 4.5
=====================================================
Single model analyzes buggy_app.py for security vulnerabilities.
One prompt → one response. Baseline for comparison.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from config_phase18 import (
    SOLO_MODEL, SOLO_SYSTEM, SOLO_MAX_TOKENS, SOLO_TEMPERATURE,
    TASK1_AUDIT_PROMPT, MODEL_SHORT,
)
from arrival_runner import call_openrouter


def main():
    print("=" * 60)
    print("  Phase 18 Task 1 — Condition A: SOLO (Claude Sonnet 4.5)")
    print("=" * 60)

    # Load buggy app code
    buggy_path = os.path.join(os.path.dirname(__file__), "buggy_app.py")
    with open(buggy_path, "r", encoding="utf-8") as f:
        buggy_code = f.read()

    # Build prompt
    prompt = TASK1_AUDIT_PROMPT.format(code=buggy_code)
    short = MODEL_SHORT.get(SOLO_MODEL, SOLO_MODEL)

    print(f"\n  Model: {SOLO_MODEL} ({short})")
    print(f"  Prompt length: ~{len(prompt)} chars")
    print(f"  Calling API...", end=" ", flush=True)

    resp = call_openrouter(
        prompt=prompt,
        model=SOLO_MODEL,
        system_prompt=SOLO_SYSTEM,
        max_tokens=SOLO_MAX_TOKENS,
        temperature=SOLO_TEMPERATURE,
    )

    print(f"done!")
    print(f"  Tokens: {resp['prompt_tokens']} in + {resp['completion_tokens']} out")
    print(f"  Cost: ${resp['cost_usd']:.4f}")
    print(f"  Latency: {resp['latency_ms']:.0f}ms")

    result = {
        "condition": "A_solo",
        "task": "security_audit",
        "model": SOLO_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response": resp["text"],
        "prompt_tokens": resp["prompt_tokens"],
        "completion_tokens": resp["completion_tokens"],
        "cost_usd": resp["cost_usd"],
        "latency_ms": resp["latency_ms"],
        "success": resp["success"],
    }

    # Save result
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "solo_result.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  Result saved: {outpath}")

    # Print first 500 chars of response
    print(f"\n  --- Response preview (first 500 chars) ---")
    print(resp["text"][:500])
    print("  ...")

    return result


if __name__ == "__main__":
    main()
