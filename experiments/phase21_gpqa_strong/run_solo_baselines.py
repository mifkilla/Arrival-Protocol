# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 21: Solo Baselines for Strong Trio Models

Each of the 3 ARRIVAL models answers 198 GPQA Diamond questions independently.
Single-shot (1 call per question per model), temp=0.3, same prompt.

Computes "non-debate MV" = majority vote of 3 solo answers (without discussion).
This is the CLEAN comparison: same models, debate vs no debate.

Models:
- GPT-4.1 (openai/gpt-4.1)
- Gemini 3 Flash (google/gemini-3-flash-preview)
- Grok 4.1 Fast (x-ai/grok-4.1-fast)

Usage:
    set OPENROUTER_API_KEY=sk-or-v1-...
    python run_solo_baselines.py              # Full run (198 questions, all 3 models)
    python run_solo_baselines.py --test 5     # Pipeline test (5 questions)
    python run_solo_baselines.py --model gpt  # Run only GPT-4.1
"""

import json
import os
import re
import sys
import time
import argparse
from collections import Counter
from datetime import datetime, timedelta

# Windows encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from arrival.metrics import extract_answer_letter

# ============================================================
# Configuration
# ============================================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODELS = {
    "gpt": {
        "id": "openai/gpt-4.1",
        "short": "GPT-4.1",
        "cost_input": 2.00,
        "cost_output": 8.00,
        "results_file": "solo_gpt41.json",
    },
    "gemini": {
        "id": "google/gemini-3-flash-preview",
        "short": "Gemini3Flash",
        "cost_input": 0.50,
        "cost_output": 3.00,
        "results_file": "solo_gemini3flash.json",
    },
    "grok": {
        "id": "x-ai/grok-4.1-fast",
        "short": "Grok4.1",
        "cost_input": 0.60,
        "cost_output": 2.40,
        "results_file": "solo_grok41.json",
    },
}

TEMPERATURE = 0.3
MAX_TOKENS = 2048
BUDGET_LIMIT = 20.0
SLEEP_BETWEEN_CALLS = 1.5  # Slightly less than ARRIVAL (no sequential dependency)

# Solo expert prompt (same as Phase 17 / Phase 20 but without /no_think)
SOLO_SYSTEM = """You are a world-class scientist with deep expertise across physics,
chemistry, biology, and mathematics. You are answering a graduate-level
multiple-choice question from the GPQA Diamond benchmark.

IMPORTANT INSTRUCTIONS:
1. Read the question and all answer choices carefully.
2. Think step by step through the problem.
3. Consider each answer choice systematically.
4. If you are uncertain, reason through by elimination.
5. After your full analysis, state your final answer clearly.

End your response with exactly: "The answer is X" where X is A, B, C, or D."""

# ============================================================
# Load questions (reuse Phase 20 data)
# ============================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase20_gpqa_full", "data")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load_questions():
    path = os.path.join(DATA_DIR, "gpqa_diamond_198.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# API call
# ============================================================
def call_openrouter(prompt: str, model_id: str) -> dict:
    import requests

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/mifkilla/Arrival-Protocol",
        "X-Title": "ARRIVAL Phase 21 Solo",
    }

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SOLO_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }

    for attempt in range(3):
        try:
            start_time = time.time()
            resp = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=180,
            )
            latency_ms = (time.time() - start_time) * 1000

            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"      Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            model_version = data.get("model", model_id)

            tail_snippet = content[-200:] if content else ""

            return {
                "content": content,
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "latency_ms": round(latency_ms, 1),
                "model_version": model_version,
                "tail_snippet": tail_snippet,
            }
        except Exception as e:
            if attempt == 2:
                print(f"      ERROR: {e}")
                return {
                    "content": "", "tokens_prompt": 0, "tokens_completion": 0,
                    "latency_ms": 0, "model_version": model_id, "tail_snippet": "",
                }
            time.sleep(2 ** (attempt + 1))

    return {
        "content": "", "tokens_prompt": 0, "tokens_completion": 0,
        "latency_ms": 0, "model_version": model_id, "tail_snippet": "",
    }


# ============================================================
# Run solo baseline for one model
# ============================================================
def run_solo_model(model_key: str, questions: list, test_mode: bool = False):
    """Run a single model on all questions."""
    model_info = MODELS[model_key]
    model_id = model_info["id"]
    model_short = model_info["short"]
    results_file = os.path.join(RESULTS_DIR, model_info["results_file"])

    # Resume support
    existing_results = []
    done_ids = set()
    if os.path.exists(results_file) and not test_mode:
        with open(results_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_results = existing_data.get("questions", [])
        done_ids = {r["question_id"] for r in existing_results}
        print(f"  RESUMING {model_short}: found {len(existing_results)} completed questions")

    n_total = len(questions)
    n_remaining = sum(1 for q in questions if q["id"] not in done_ids)

    print(f"\n{'='*60}")
    print(f"  Solo Baseline: {model_short} ({model_id})")
    print(f"  Questions: {n_total}, Remaining: {n_remaining}")
    print(f"{'='*60}")

    all_results = list(existing_results)
    total_cost = 0.0
    total_tokens = 0
    extraction_failures = 0
    questions_done = 0
    start_time = time.time()

    for qi, q in enumerate(questions):
        if q["id"] in done_ids:
            continue

        prompt = f"""Question: {q['question']}

A) {q['choices']['A']}
B) {q['choices']['B']}
C) {q['choices']['C']}
D) {q['choices']['D']}"""

        print(f"  [{qi+1}/{n_total}] {q['id']} [{q['domain']}]", end="", flush=True)

        resp = call_openrouter(prompt, model_id)
        answer = extract_answer_letter(resp["content"])
        correct = answer == q["correct"] if answer else False

        # Cost
        pricing_in = model_info["cost_input"]
        pricing_out = model_info["cost_output"]
        cost = (
            resp["tokens_prompt"] * pricing_in / 1_000_000
            + resp["tokens_completion"] * pricing_out / 1_000_000
        )
        total_cost += cost
        total_tokens += resp["tokens_prompt"] + resp["tokens_completion"]
        questions_done += 1

        if not answer:
            extraction_failures += 1

        # Extraction failure check
        if questions_done >= 5:
            failure_rate = extraction_failures / questions_done
            if failure_rate > 0.05:
                print(f"\n  WARNING: {model_short} extraction failure rate {failure_rate:.1%} > 5%!")
                if test_mode:
                    print("  STOPPING!")
                    break

        sym = "+" if correct else "-"
        print(f" {answer or '?'} {sym} ${total_cost:.2f}")

        result = {
            "question_id": q["id"],
            "domain": q["domain"],
            "subdomain": q.get("subdomain", ""),
            "correct_answer": q["correct"],
            "correct_answer_text": q["choices"].get(q["correct"], ""),
            "answer": answer,
            "answer_text": q["choices"].get(answer, "") if answer else "",
            "correct": correct,
            "cost_usd": cost,
            "tokens_prompt": resp["tokens_prompt"],
            "tokens_completion": resp["tokens_completion"],
            "latency_ms": resp["latency_ms"],
            "model_version": resp["model_version"],
            "tail_snippet": resp["tail_snippet"],
        }
        all_results.append(result)

        # Save after each question
        _save_solo_results(results_file, all_results, model_info, total_cost)

        time.sleep(SLEEP_BETWEEN_CALLS)

    # Summary
    n = len(all_results)
    n_correct = sum(1 for r in all_results if r.get("correct"))
    acc = n_correct / n if n else 0
    elapsed = time.time() - start_time

    print(f"\n  {model_short} DONE: {n_correct}/{n} = {acc:.1%}, ${total_cost:.2f}, {timedelta(seconds=int(elapsed))}")
    print(f"  Extraction failures: {extraction_failures}/{questions_done} = {extraction_failures/questions_done:.1%}" if questions_done else "")

    return all_results


def _save_solo_results(filepath, all_results, model_info, total_cost):
    """Save solo results with atomic write."""
    n = len(all_results)
    n_correct = sum(1 for r in all_results if r.get("correct"))

    output = {
        "summary": {
            "phase": "Phase 21: Solo Baseline",
            "model_id": model_info["id"],
            "model_short": model_info["short"],
            "n_questions": n,
            "n_correct": n_correct,
            "accuracy": round(n_correct / n, 4) if n else 0,
            "total_cost_usd": round(total_cost, 4),
        },
        "questions": all_results,
    }

    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, filepath)


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 21: Solo Baselines (3 models)")
    parser.add_argument("--test", type=int, default=None, help="Pipeline test: N questions")
    parser.add_argument("--model", type=str, default=None,
                        choices=["gpt", "gemini", "grok"],
                        help="Run only one model (default: all 3)")
    args = parser.parse_args()

    assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY environment variable is required."

    questions = load_questions()
    if args.test:
        questions = questions[:args.test]
        print(f"\n  *** PIPELINE TEST MODE: {args.test} questions ***\n")

    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Determine which models to run
    if args.model:
        model_keys = [args.model]
    else:
        model_keys = ["gpt", "gemini", "grok"]

    all_solo_results = {}
    for model_key in model_keys:
        results = run_solo_model(model_key, questions, test_mode=bool(args.test))
        all_solo_results[model_key] = results

    # Compute non-debate MV if all 3 models ran
    if len(all_solo_results) == 3 and all(len(v) == len(questions) for v in all_solo_results.values()):
        print("\n" + "=" * 60)
        print("  Computing Non-Debate Majority Vote...")
        print("=" * 60)

        gpt_results = {r["question_id"]: r for r in all_solo_results["gpt"]}
        gemini_results = {r["question_id"]: r for r in all_solo_results["gemini"]}
        grok_results = {r["question_id"]: r for r in all_solo_results["grok"]}

        mv_correct = 0
        mv_results = []
        for q in questions:
            qid = q["id"]
            answers = []
            for results_dict in [gpt_results, gemini_results, grok_results]:
                if qid in results_dict and results_dict[qid].get("answer"):
                    answers.append(results_dict[qid]["answer"])

            if answers:
                mv_answer = Counter(answers).most_common(1)[0][0]
            else:
                mv_answer = None

            correct = mv_answer == q["correct"] if mv_answer else False
            if correct:
                mv_correct += 1

            mv_results.append({
                "question_id": qid,
                "domain": q["domain"],
                "correct_answer": q["correct"],
                "gpt_answer": gpt_results.get(qid, {}).get("answer"),
                "gemini_answer": gemini_results.get(qid, {}).get("answer"),
                "grok_answer": grok_results.get(qid, {}).get("answer"),
                "non_debate_mv": mv_answer,
                "correct": correct,
            })

        n = len(mv_results)
        acc = mv_correct / n if n else 0
        print(f"  Non-Debate MV: {mv_correct}/{n} = {acc:.1%}")

        # Save
        mv_file = os.path.join(RESULTS_DIR, "non_debate_mv.json")
        total_cost = sum(
            sum(r.get("cost_usd", 0) for r in all_solo_results[k])
            for k in all_solo_results
        )
        mv_output = {
            "summary": {
                "phase": "Phase 21: Non-Debate MV",
                "n_questions": n,
                "n_correct": mv_correct,
                "accuracy": round(acc, 4),
                "total_cost_usd": round(total_cost, 4),
                "models": [MODELS[k]["id"] for k in ["gpt", "gemini", "grok"]],
            },
            "questions": mv_results,
        }
        with open(mv_file, "w", encoding="utf-8") as f:
            json.dump(mv_output, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {mv_file}")

    print("\n  All solo baselines complete!")


if __name__ == "__main__":
    main()
