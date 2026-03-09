# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 23 Step 1: Solo Baselines for 7 Models

Runs each model independently on N questions (default 20) to establish
per-model accuracy weights for the weighted CGD voting scheme.

Models: Grok 4.1, Gemini 3 Flash, Qwen3.5 397B, DeepSeek V3.2,
        GLM-5, Kimi K2.5, Claude Sonnet 4.6

Usage:
    set OPENROUTER_API_KEY=sk-or-v1-key1,sk-or-v1-key2
    python run_solo_baselines.py              # 20 questions (calibration)
    python run_solo_baselines.py --n 198      # Full 198 questions
    python run_solo_baselines.py --test 5     # Pipeline test (5 questions)
"""

import json
import os
import re
import sys
import time
import argparse
from collections import Counter
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
# Dual API keys for rate limit resilience
API_KEYS = [k.strip() for k in os.environ.get("OPENROUTER_API_KEY", "").split(",") if k.strip()]
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_key_index = 0
_key_lock = threading.Lock()

def _next_api_key():
    """Round-robin across available API keys (thread-safe)."""
    global _key_index
    if not API_KEYS:
        return ""
    with _key_lock:
        key = API_KEYS[_key_index % len(API_KEYS)]
        _key_index += 1
    return key

MODELS = {
    "grok": {
        "id": "x-ai/grok-4.1-fast",
        "short": "Grok4.1",
        "cost_input": 0.60, "cost_output": 2.40,
        "disable_reasoning": False,
    },
    "gemini": {
        "id": "google/gemini-3-flash-preview",
        "short": "Gemini3Flash",
        "cost_input": 0.50, "cost_output": 3.00,
        "disable_reasoning": False,
    },
    "qwen": {
        "id": "qwen/qwen3.5-397b-a17b",
        "short": "Qwen3.5-397B",
        "cost_input": 0.40, "cost_output": 2.40,
        "disable_reasoning": True,
    },
    "deepseek": {
        "id": "deepseek/deepseek-v3.2",
        "short": "DeepSeekV3.2",
        "cost_input": 0.25, "cost_output": 0.40,
        "disable_reasoning": True,
    },
    "glm": {
        "id": "z-ai/glm-5",
        "short": "GLM5",
        "cost_input": 0.80, "cost_output": 2.56,
        "disable_reasoning": True,
    },
    "kimi": {
        "id": "moonshotai/kimi-k2.5",
        "short": "KimiK2.5",
        "cost_input": 0.45, "cost_output": 2.20,
        "disable_reasoning": True,
    },
    "claude": {
        "id": "anthropic/claude-sonnet-4.6",
        "short": "ClaudeSonnet4.6",
        "cost_input": 3.00, "cost_output": 15.00,
        "disable_reasoning": False,
    },
}

MODEL_COSTS = {m["id"]: {"input": m["cost_input"], "output": m["cost_output"]} for m in MODELS.values()}

TEMPERATURE = 0.3
MAX_TOKENS = 2048
BUDGET_LIMIT = 25.0
SLEEP_BETWEEN_CALLS = 1.0

# ============================================================
# Prompts
# ============================================================
SOLO_PROMPT = """You are a world-class scientist with deep expertise across physics,
chemistry, biology, and mathematics. You are answering a graduate-level
multiple-choice question from the GPQA Diamond benchmark.

IMPORTANT INSTRUCTIONS:
1. Read the question and all answer choices carefully.
2. Think step by step through the problem.
3. Consider each answer choice systematically.
4. If you are uncertain, reason through by elimination.
5. After your full analysis, state your final answer clearly.

End your response with exactly: "The answer is X" where X is A, B, C, or D.

Question: {question}

A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}"""

STRICT_RETRY_PROMPT = """You previously attempted to answer this question but your response
could not be parsed. Please answer again.

You MUST end your response with exactly one of:
"The answer is A"
"The answer is B"
"The answer is C"
"The answer is D"

Question: {question}

A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}"""

SYSTEM_PROMPT = "You are a world-class scientist."

# ============================================================
# Load questions
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
def call_openrouter(prompt: str, model_key: str, system_prompt: str) -> dict:
    import requests

    m = MODELS[model_key]
    model_id = m["id"]
    api_key = _next_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Methodiy-Kelevra/ARRIVAL",
        "X-Title": "ARRIVAL Phase 23 Solo Baselines",
    }

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }

    # Disable reasoning/thinking for models that support it
    if m.get("disable_reasoning"):
        payload["reasoning"] = {"enabled": False}

    for attempt in range(3):
        try:
            start = time.time()
            resp = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=180,
            )
            latency_ms = (time.time() - start) * 1000

            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"      Rate limited ({model_id}), waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code != 200:
                print(f"      HTTP {resp.status_code} for {model_id}: {resp.text[:200]}")
                if attempt == 2:
                    return _empty_response(model_id)
                time.sleep(2 ** (attempt + 1))
                continue

            data = resp.json()

            if "error" in data:
                print(f"      API error for {model_id}: {data['error']}")
                if attempt == 2:
                    return _empty_response(model_id)
                time.sleep(2 ** (attempt + 1))
                continue

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            pricing = MODEL_COSTS.get(model_id, {"input": 2.0, "output": 8.0})
            cost = (
                usage.get("prompt_tokens", 0) * pricing["input"] / 1_000_000
                + usage.get("completion_tokens", 0) * pricing["output"] / 1_000_000
            )

            return {
                "content": content,
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "cost": cost,
                "latency_ms": round(latency_ms, 1),
                "model_version": data.get("model", model_id),
            }
        except Exception as e:
            if attempt == 2:
                print(f"      ERROR ({model_id}): {e}")
                return _empty_response(model_id)
            time.sleep(2 ** (attempt + 1))

    return _empty_response(model_id)


def _empty_response(model_id):
    return {"content": "", "tokens_prompt": 0, "tokens_completion": 0,
            "cost": 0, "latency_ms": 0, "model_version": model_id}


# ============================================================
# Run solo for one question across all models
# ============================================================
_print_lock = threading.Lock()


def _call_single_model(mk, choice_vars):
    """Call a single model (designed for thread pool). Returns (mk, answer, cost, tokens, api_calls)."""
    m = MODELS[mk]
    prompt = SOLO_PROMPT.format(**choice_vars)
    resp = call_openrouter(prompt, mk, SYSTEM_PROMPT)
    answer = extract_answer_letter(resp["content"])
    cost = resp["cost"]
    tokens = resp["tokens_prompt"] + resp["tokens_completion"]
    api_calls = 1

    # Extraction retry if None
    if answer is None and resp["content"]:
        with _print_lock:
            print(f" {m['short'][:6]}:retry", end="", flush=True)
        retry_prompt = STRICT_RETRY_PROMPT.format(**choice_vars)
        resp2 = call_openrouter(retry_prompt, mk, SYSTEM_PROMPT)
        answer = extract_answer_letter(resp2["content"])
        cost += resp2["cost"]
        tokens += resp2["tokens_prompt"] + resp2["tokens_completion"]
        api_calls += 1

    with _print_lock:
        print(f" {m['short'][:6]}:{answer or '?'}", end="", flush=True)

    return mk, answer, cost, tokens, api_calls


def run_solo_question(q: dict) -> dict:
    choice_vars = {
        "choice_a": q["choices"]["A"],
        "choice_b": q["choices"]["B"],
        "choice_c": q["choices"]["C"],
        "choice_d": q["choices"]["D"],
        "question": q["question"],
    }
    q_cost = 0.0
    q_tokens = 0
    api_calls = 0
    solo_answers = {}

    model_order = ["grok", "gemini", "qwen", "deepseek", "glm", "kimi", "claude"]

    # Parallel: all 7 models answer simultaneously
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(_call_single_model, mk, choice_vars): mk
            for mk in model_order
        }
        for future in as_completed(futures):
            mk, answer, cost, tokens, calls = future.result()
            solo_answers[mk] = answer
            q_cost += cost
            q_tokens += tokens
            api_calls += calls

    # Compute majority vote (simple)
    valid = {k: v for k, v in solo_answers.items() if v is not None}
    if valid:
        mv_answer = Counter(valid.values()).most_common(1)[0][0]
    else:
        mv_answer = None

    correct_answer = q["correct"]
    result = {
        "question_id": q["id"],
        "domain": q["domain"],
        "correct_answer": correct_answer,
    }
    for mk in model_order:
        result[f"solo_{mk}"] = solo_answers.get(mk)
    result.update({
        "mv_answer": mv_answer,
        "mv_correct": mv_answer == correct_answer if mv_answer else False,
        "cost_usd": q_cost,
        "total_tokens": q_tokens,
        "api_calls": api_calls,
    })
    return result


# ============================================================
# Save results (atomic write)
# ============================================================
def _save_results(results, total_cost, timestamp, filename):
    n = len(results)

    # Per-model accuracy
    model_keys = list(MODELS.keys())
    per_model = {}
    for mk in model_keys:
        field = f"solo_{mk}"
        correct = sum(1 for r in results if r[field] == r["correct_answer"])
        none_count = sum(1 for r in results if r[field] is None)
        per_model[mk] = {
            "model_id": MODELS[mk]["id"],
            "short": MODELS[mk]["short"],
            "correct": correct,
            "total": n,
            "accuracy": round(correct / n, 4) if n else 0,
            "none_count": none_count,
        }

    # MV accuracy
    mv_correct = sum(1 for r in results if r["mv_correct"])

    # Domain breakdown
    domains = set(r["domain"] for r in results)
    domain_acc = {}
    for dom in domains:
        dom_results = [r for r in results if r["domain"] == dom]
        dom_correct = sum(1 for r in dom_results if r["mv_correct"])
        domain_acc[dom] = {"n": len(dom_results), "correct": dom_correct,
                           "accuracy": round(dom_correct / len(dom_results), 4)}

    # Oracle (any model correct)
    oracle_correct = 0
    for r in results:
        answers = [r[f"solo_{mk}"] for mk in model_keys]
        if r["correct_answer"] in answers:
            oracle_correct += 1

    data = {
        "phase": "Phase 23: Solo Baselines (7 models)",
        "timestamp": timestamp,
        "n_questions": n,
        "models": {mk: MODELS[mk]["id"] for mk in model_keys},
        "summary": {
            "per_model": per_model,
            "mv_correct": mv_correct,
            "mv_accuracy": round(mv_correct / n, 4) if n else 0,
            "oracle_correct": oracle_correct,
            "oracle_accuracy": round(oracle_correct / n, 4) if n else 0,
            "total_cost_usd": round(total_cost, 4),
            "total_api_calls": sum(r["api_calls"] for r in results),
            "per_domain": domain_acc,
        },
        "questions": results,
    }

    path = os.path.join(RESULTS_DIR, filename)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 23: Solo Baselines (7 models)")
    parser.add_argument("--test", type=int, default=None, help="Pipeline test N questions")
    parser.add_argument("--n", type=int, default=20, help="Number of questions (default 20)")
    args = parser.parse_args()

    n_models = len(MODELS)
    model_keys = list(MODELS.keys())

    assert API_KEYS, "OPENROUTER_API_KEY env var required (comma-separated for multiple keys)"
    print(f"  API keys loaded: {len(API_KEYS)} key(s)")

    all_questions = load_questions()

    if args.test:
        questions = all_questions[:args.test]
        filename = "solo_baselines_test.json"
        print(f"\n  *** PIPELINE TEST: {args.test} questions ***\n")
    else:
        questions = all_questions[:args.n]
        filename = f"solo_baselines_{args.n}q.json"
        print(f"\n  Solo baselines: {len(questions)} questions, {n_models} models\n")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Resume support — but invalidate old results if model set changed
    results_path = os.path.join(RESULTS_DIR, filename)
    existing_results = []
    done_ids = set()
    if os.path.exists(results_path) and not args.test:
        with open(results_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        # Check if model set matches
        old_models = set(existing_data.get("models", {}).keys())
        new_models = set(model_keys)
        if old_models == new_models:
            existing_results = existing_data.get("questions", [])
            done_ids = {r["question_id"] for r in existing_results}
            print(f"  RESUMING: found {len(existing_results)} completed questions")
        else:
            print(f"  Model set changed ({old_models} -> {new_models}), starting fresh")

    total_cost = sum(r.get("cost_usd", 0) for r in existing_results)
    results = list(existing_results)
    n_remaining = sum(1 for q in questions if q["id"] not in done_ids)

    print("=" * 70)
    print(f"  Phase 23: Solo Baselines — {len(questions)} questions × {n_models} models")
    print(f"  Models: {', '.join(MODELS[mk]['short'] for mk in model_keys)}")
    print(f"  Remaining: {n_remaining}, Budget: ${BUDGET_LIMIT}")
    print("=" * 70)

    start_time = time.time()
    questions_done = 0

    for i, q in enumerate(questions):
        if q["id"] in done_ids:
            continue

        if total_cost >= BUDGET_LIMIT:
            print(f"\n  BUDGET LIMIT reached at ${total_cost:.2f}")
            break

        print(f"\n[{i+1}/{len(questions)}] {q['id']} ({q['domain']}):", end="", flush=True)
        result = run_solo_question(q)
        results.append(result)
        total_cost += result["cost_usd"]
        questions_done += 1

        # Count per-question correctness
        n_models_correct = sum(1 for mk in model_keys if result.get(f"solo_{mk}") == result["correct_answer"])
        mv_mark = "+" if result["mv_correct"] else "-"
        print(f" MV={result['mv_answer']}{mv_mark} ({n_models_correct}/{n_models} correct) ${result['cost_usd']:.3f}")

        # Running stats
        n = len(results)
        mv_acc = sum(1 for r in results if r["mv_correct"]) / n * 100

        if i % 5 == 4 or i == len(questions) - 1:
            elapsed = time.time() - start_time
            eta = elapsed / questions_done * n_remaining - elapsed if questions_done > 0 else 0

            # Per-model running accuracy
            model_accs = []
            for mk in model_keys:
                field = f"solo_{mk}"
                acc = sum(1 for r in results if r.get(field) == r["correct_answer"]) / n * 100
                model_accs.append(f"{MODELS[mk]['short'][:6]}={acc:.0f}%")

            print(f"  [{n}/{len(questions)}] MV={mv_acc:.1f}% | {' '.join(model_accs)} | Cost=${total_cost:.2f} ETA={timedelta(seconds=max(0, int(eta)))}")

        # Save after every question
        _save_results(results, total_cost, timestamp, filename)

    # Final summary
    print("\n" + "=" * 70)
    print("  PHASE 23 SOLO BASELINES — COMPLETE")
    print("=" * 70)

    n = len(results)

    print(f"\n  Per-model accuracy ({n} questions):")
    for mk in model_keys:
        field = f"solo_{mk}"
        correct = sum(1 for r in results if r.get(field) == r["correct_answer"])
        none_count = sum(1 for r in results if r.get(field) is None)
        print(f"    {MODELS[mk]['short']:20s}: {correct}/{n} = {correct/n*100:.1f}%"
              + (f"  ({none_count} extraction failures)" if none_count else ""))

    mv_correct = sum(1 for r in results if r["mv_correct"])
    print(f"\n  Simple MV ({n_models} models): {mv_correct}/{n} = {mv_correct/n*100:.1f}%")

    oracle = sum(1 for r in results if r["correct_answer"] in [r.get(f"solo_{mk}") for mk in model_keys])
    print(f"  Oracle (any correct): {oracle}/{n} = {oracle/n*100:.1f}%")

    print(f"\n  Total cost: ${total_cost:.2f}")
    print(f"  Total calls: {sum(r['api_calls'] for r in results)}")
    elapsed = time.time() - start_time
    print(f"  Runtime: {timedelta(seconds=int(elapsed))}")


if __name__ == "__main__":
    main()
