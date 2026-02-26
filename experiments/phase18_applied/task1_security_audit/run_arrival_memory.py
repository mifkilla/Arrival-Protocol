"""
Phase 18 Task 1 — Condition C: ARRIVAL + CARE-ALERT Memory
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

from config_phase18 import TASK1_AUDIT_PROMPT
from arrival_runner import run_arrival_4rounds


def main():
    print("=" * 60)
    print("  Phase 18 Task 1 — Condition C: ARRIVAL + CARE-ALERT Memory")
    print("=" * 60)

    # Load buggy app code
    buggy_path = os.path.join(os.path.dirname(__file__), "buggy_app.py")
    with open(buggy_path, "r", encoding="utf-8") as f:
        buggy_code = f.read()

    # Build task prompt
    task_prompt = TASK1_AUDIT_PROMPT.format(code=buggy_code)

    # Memory seeds path
    memory_path = os.path.join(os.path.dirname(__file__), "memory_seeds_audit.json")

    print(f"\n  Task prompt length: ~{len(task_prompt)} chars")
    print(f"  Memory seeds: {memory_path}")

    result = run_arrival_4rounds(
        task_prompt=task_prompt,
        use_memory=True,
        memory_seeds_path=memory_path,
        verbose=True,
    )
    result["condition"] = "C_arrival_memory"
    result["task"] = "security_audit"

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
