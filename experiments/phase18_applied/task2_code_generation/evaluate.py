# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 18 Task 2: Code Generation Evaluation
=============================================
Extracts generated app.py from each condition's response,
then runs test_suite_phase18.py against it.

Score = tests_passed / 15

Usage:
    python evaluate.py

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import json
import os
import re
import sys
import subprocess
import tempfile
import shutil

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
TEST_SUITE = os.path.join(os.path.dirname(__file__), "test_suite_phase18.py")


def extract_code_blocks(text: str) -> dict:
    """Extract Python code blocks from LLM response."""
    # Pattern: ```python ... ``` or ```py ... ```
    pattern = r'```(?:python|py)?\s*\n(.*?)```'
    blocks = re.findall(pattern, text, re.DOTALL)

    result = {"app": None, "test": None}

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Identify if this is the app or test file
        if "FastAPI" in block or "from fastapi" in block or "@app." in block:
            if result["app"] is None or len(block) > len(result["app"]):
                result["app"] = block
        elif "def test_" in block or "import pytest" in block:
            if result["test"] is None or len(block) > len(result["test"]):
                result["test"] = block

    # If we couldn't distinguish, take the two largest blocks
    if result["app"] is None and len(blocks) >= 1:
        blocks_sorted = sorted(blocks, key=len, reverse=True)
        result["app"] = blocks_sorted[0]
        if len(blocks_sorted) > 1:
            result["test"] = blocks_sorted[1]

    return result


def run_tests_against_app(app_code: str) -> dict:
    """
    Write app.py to a temp directory, copy test suite there, run pytest.
    Returns dict with tests_passed, tests_failed, tests_total, output.
    """
    tmpdir = tempfile.mkdtemp(prefix="phase18_eval_")

    try:
        # Write the generated app
        app_path = os.path.join(tmpdir, "app.py")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(app_code)

        # Copy our test suite
        test_path = os.path.join(tmpdir, "test_suite_phase18.py")
        shutil.copy2(TEST_SUITE, test_path)

        # Run pytest
        env = os.environ.copy()
        env["PYTHONPATH"] = tmpdir

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short", "--no-header", "-q"],
            capture_output=True, text=True, timeout=60, cwd=tmpdir, env=env,
        )

        output = proc.stdout + "\n" + proc.stderr

        # Parse results
        # pytest output like: "8 passed, 7 failed"
        passed = 0
        failed = 0
        errors = 0

        # Look for summary line
        for line in output.split("\n"):
            match = re.search(r'(\d+) passed', line)
            if match:
                passed = int(match.group(1))
            match = re.search(r'(\d+) failed', line)
            if match:
                failed = int(match.group(1))
            match = re.search(r'(\d+) error', line)
            if match:
                errors = int(match.group(1))

        return {
            "tests_passed": passed,
            "tests_failed": failed,
            "tests_errors": errors,
            "tests_total": passed + failed + errors,
            "score": passed / 15 if passed + failed + errors > 0 else 0.0,
            "output": output[:5000],  # Truncate for storage
            "returncode": proc.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "tests_passed": 0, "tests_failed": 0, "tests_errors": 15,
            "tests_total": 15, "score": 0.0,
            "output": "TIMEOUT: Tests took longer than 60 seconds",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "tests_passed": 0, "tests_failed": 0, "tests_errors": 15,
            "tests_total": 15, "score": 0.0,
            "output": f"ERROR: {e}",
            "returncode": -1,
        }
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def evaluate_condition(result_path: str) -> dict:
    """Evaluate a single condition's generated code."""
    if not os.path.exists(result_path):
        return {"error": f"Result file not found: {result_path}"}

    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    response = result.get("response", result.get("final_answer", ""))

    # Extract code
    code_blocks = extract_code_blocks(response)

    if not code_blocks["app"]:
        return {
            "condition": result.get("condition", "unknown"),
            "error": "Could not extract app.py code from response",
            "tests_passed": 0, "tests_total": 15, "score": 0.0,
        }

    # Run tests
    test_results = run_tests_against_app(code_blocks["app"])

    evaluation = {
        "condition": result.get("condition", "unknown"),
        "code_extracted": True,
        "app_code_lines": len(code_blocks["app"].split("\n")),
        "test_code_extracted": code_blocks["test"] is not None,
        **test_results,
        "prompt_tokens": result.get("prompt_tokens", result.get("total_prompt_tokens", 0)),
        "completion_tokens": result.get("completion_tokens", result.get("total_completion_tokens", 0)),
        "cost_usd": result.get("cost_usd", result.get("total_cost_usd", 0)),
        "total_calls": result.get("total_calls", 1),
    }

    # CRDT metrics if available
    if "metrics" in result:
        evaluation["care_resolve"] = result["metrics"].get("care_resolve")
        evaluation["meaning_debt"] = result["metrics"].get("meaning_debt")

    if "memory_injections" in result and result["memory_injections"]:
        evaluation["memory_injected"] = True
    else:
        evaluation["memory_injected"] = False

    return evaluation


def main():
    print("=" * 60)
    print("  Phase 18 Task 2: Code Generation — EVALUATION")
    print("=" * 60)

    conditions = [
        ("A_solo", os.path.join(RESULTS_DIR, "solo_result.json")),
        ("B_arrival", os.path.join(RESULTS_DIR, "arrival_result.json")),
        ("C_arrival_memory", os.path.join(RESULTS_DIR, "arrival_memory_result.json")),
    ]

    evaluations = []
    for label, path in conditions:
        print(f"\n  --- Evaluating {label} ---")
        ev = evaluate_condition(path)
        evaluations.append(ev)

        if "error" in ev and ev.get("tests_passed", -1) < 0:
            print(f"    {ev['error']}")
            continue

        print(f"    Tests passed: {ev.get('tests_passed', 0)}/15 ({ev.get('score', 0):.0%})")
        print(f"    Code lines: {ev.get('app_code_lines', 'N/A')}")
        print(f"    Tokens: {ev.get('prompt_tokens', 0) + ev.get('completion_tokens', 0):,}")
        print(f"    Cost: ${ev.get('cost_usd', 0):.4f}")
        if ev.get("care_resolve") is not None:
            print(f"    CARE Resolve: {ev['care_resolve']:.3f}")
        if ev.get("memory_injected"):
            print(f"    Memory injected: Yes")

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY TABLE")
    print("=" * 60)
    print(f"\n  {'Metric':<25} {'A:Solo':>10} {'B:ARRIVAL':>10} {'C:ARR+Mem':>10}")
    print(f"  {'-'*55}")

    for metric in ["tests_passed", "score", "cost_usd", "total_calls"]:
        vals = []
        for ev in evaluations:
            v = ev.get(metric, "N/A")
            if metric == "cost_usd" and isinstance(v, (int, float)):
                vals.append(f"${v:.4f}")
            elif metric == "score" and isinstance(v, (int, float)):
                vals.append(f"{v:.0%}")
            else:
                vals.append(str(v))
        print(f"  {metric:<25} {vals[0]:>10} {vals[1]:>10} {vals[2]:>10}")

    # Save
    eval_path = os.path.join(RESULTS_DIR, "evaluation.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluations, f, indent=2, ensure_ascii=False)
    print(f"\n  Evaluation saved: {eval_path}")

    return evaluations


if __name__ == "__main__":
    main()
