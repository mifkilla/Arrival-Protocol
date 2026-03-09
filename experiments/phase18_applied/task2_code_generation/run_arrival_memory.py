# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 18 Task 2 — Condition C: ARRIVAL + CARE-ALERT Memory
============================================================
ARRIVAL 4-round protocol with CARE-ALERT gated memory injection.
Shows combined effect of protocol + memory system.

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
    print("  Phase 18 Task 2 — Condition C: ARRIVAL + CARE-ALERT Memory")
    print("=" * 60)

    task_prompt = TASK2_API_PROMPT

    # Memory seeds path
    memory_path = os.path.join(os.path.dirname(__file__), "memory_seeds_api.json")

    print(f"\n  Task prompt length: ~{len(task_prompt)} chars")
    print(f"  Memory seeds: {memory_path}")

    result = run_arrival_4rounds(
        task_prompt=task_prompt,
        use_memory=True,
        memory_seeds_path=memory_path,
        verbose=True,
    )
    result["condition"] = "C_arrival_memory"
    result["task"] = "code_generation"

    # Save result
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "arrival_memory_result.json")
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
