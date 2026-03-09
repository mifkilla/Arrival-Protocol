# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 18 Task 2 — Condition B: ARRIVAL (5 models, no memory)
=============================================================
ARRIVAL 4-round protocol generates REST API from specification.
Shows pure protocol effect without memory injection.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from config_phase18 import TASK2_API_PROMPT
from arrival_runner import run_arrival_4rounds


def main():
    print("=" * 60)
    print("  Phase 18 Task 2 — Condition B: ARRIVAL (no memory)")
    print("=" * 60)

    task_prompt = TASK2_API_PROMPT

    print(f"\n  Task prompt length: ~{len(task_prompt)} chars")

    result = run_arrival_4rounds(
        task_prompt=task_prompt,
        use_memory=False,
        verbose=True,
    )
    result["condition"] = "B_arrival"
    result["task"] = "code_generation"

    # Save result
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "arrival_result.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  Result saved: {outpath}")

    # Print final answer preview
    print(f"\n  --- Final synthesis preview (first 500 chars) ---")
    print(result["final_answer"][:500])
    print("  ...")

    return result


if __name__ == "__main__":
    main()
