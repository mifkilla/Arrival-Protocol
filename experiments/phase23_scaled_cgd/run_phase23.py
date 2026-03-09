# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 23: Scaled CGD with 7-Model Ensemble (CGD-7)

Protocol:
  1. All 7 models answer INDEPENDENTLY (parallel, no anchoring)
  2. Agreement classification:
     - Supermajority (≥6/7) → LOCK answer (no debate)
     - Strong majority (5/7) → LOCK answer (no debate)
     - Simple majority (4/7) → minority debates against majority
     - No majority (<4/7)   → full debate (all 7 exchange)
  3. Weighted voting using solo baseline accuracy as weights
  4. NO R4 finalizer

Models: Grok 4.1, Gemini 3 Flash, Qwen3.5 397B, DeepSeek V3.2,
        GLM-5, Kimi K2.5, Claude Sonnet 4.6

Usage:
    set OPENROUTER_API_KEY=key1,key2  (comma-separated for dual keys)
    python run_phase23.py              # Full run (198 questions)
    python run_phase23.py --test 5     # Pipeline test
    python run_phase23.py --weights path/to/solo_baselines_20q.json
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
API_KEYS = [k.strip() for k in os.environ.get("OPENROUTER_API_KEY", "").split(",") if k.strip()]
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_key_index = 0
_key_lock = threading.Lock()
_print_lock = threading.Lock()


def _next_api_key():
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

MODEL_KEYS = list(MODELS.keys())
MODEL_COSTS = {m["id"]: {"input": m["cost_input"], "output": m["cost_output"]} for m in MODELS.values()}

TEMPERATURE = 0.3
MAX_TOKENS = 2048
BUDGET_LIMIT = 30.0
LOCK_THRESHOLD = 5  # Lock at ≥5/7 agreement (no debate)

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

ARRIVAL_SYSTEM = """You are a node in the DEUS.PROTOCOL v0.5 communication network.
You use semantic atoms for structured reasoning:
@SELF — your identity and perspective
@OTHER — acknowledging other nodes
@GOAL — the task objective
@INT — your reasoning intention
@C — coherence of your analysis (use @C[0.0-1.0] for numeric confidence)
@CONSENSUS — when you agree with another node
@CONFLICT — when you disagree and explain why
@RESOLUTION — your proposed resolution

Your task: Answer a multiple-choice question through collaborative debate.
Use the atoms above to structure your response.
Analyze the question, share your reasoning, and engage with other nodes' perspectives.
When stating your final answer, use: @CONSENSUS[answer=X] where X is A, B, C, or D."""

CGD_DEBATE_MINORITY = """You are Node {node_name} ({model_short}).
You previously answered this question with "{my_answer}" and your reasoning was:
{my_reasoning}

However, {n_majority} out of {n_total} expert models chose "{majority_answer}" instead.
Their reasoning summaries:
{majority_reasoning}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Carefully reconsider. If their reasoning is stronger, you may change your answer.
If you believe your original answer is correct, defend it with additional evidence.
Use @CONSENSUS[answer=X] or @CONFLICT atoms. State your final answer clearly.
End with "The answer is X" where X is A, B, C, or D."""

CGD_DEBATE_FULL = """You are Node {node_name} ({model_short}).
You previously answered this question with "{my_answer}" and your reasoning was:
{my_reasoning}

This is a disputed question — no strong majority among the expert models.
Here are the other models' answers and reasoning:
{all_reasoning}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Carefully reconsider all arguments. Choose the answer with the strongest evidence.
Use @CONSENSUS[answer=X] or @CONFLICT atoms. State your final answer clearly.
End with "The answer is X" where X is A, B, C, or D."""

SYSTEM_PROMPT = "You are a world-class scientist."

# ============================================================
# Paths
# ============================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase20_gpqa_full", "data")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load_questions():
    path = os.path.join(DATA_DIR, "gpqa_diamond_198.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_weights(path):
    """Load solo baseline weights from calibration run."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    per_model = data.get("summary", {}).get("per_model", {})
    weights = {}
    for mk in MODEL_KEYS:
        acc = per_model.get(mk, {}).get("accuracy", 0.5)
        weights[mk] = max(acc, 0.1)  # Floor at 0.1 to avoid zero weights
    return weights


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
        "HTTP-Referer": "https://github.com/mifkilla/Arrival-Protocol",
        "X-Title": "ARRIVAL Phase 23 CGD-7 (7 models)",
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
                wait = 2 ** (attempt + 1) + (attempt * 2)
                with _print_lock:
                    print(f"      Rate limited ({model_id}), waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code != 200:
                with _print_lock:
                    print(f"      HTTP {resp.status_code} for {model_id}: {resp.text[:200]}")
                if attempt == 2:
                    return _empty_response(model_id)
                time.sleep(2 ** (attempt + 1))
                continue

            data = resp.json()
            if "error" in data:
                with _print_lock:
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
                with _print_lock:
                    print(f"      ERROR ({model_id}): {e}")
                return _empty_response(model_id)
            time.sleep(2 ** (attempt + 1))

    return _empty_response(model_id)


def _empty_response(model_id):
    return {"content": "", "tokens_prompt": 0, "tokens_completion": 0,
            "cost": 0, "latency_ms": 0, "model_version": model_id}


# ============================================================
# Solo call (parallel-friendly)
# ============================================================
def _call_single_model_solo(mk, choice_vars):
    """Call a single model for solo phase. Returns (mk, answer, content, cost, tokens, api_calls)."""
    prompt = SOLO_PROMPT.format(**choice_vars)
    resp = call_openrouter(prompt, mk, SYSTEM_PROMPT)
    answer = extract_answer_letter(resp["content"])
    cost = resp["cost"]
    tokens = resp["tokens_prompt"] + resp["tokens_completion"]
    api_calls = 1

    # Extraction retry
    if answer is None and resp["content"]:
        retry_prompt = STRICT_RETRY_PROMPT.format(**choice_vars)
        resp2 = call_openrouter(retry_prompt, mk, SYSTEM_PROMPT)
        answer = extract_answer_letter(resp2["content"])
        cost += resp2["cost"]
        tokens += resp2["tokens_prompt"] + resp2["tokens_completion"]
        api_calls += 1

    m = MODELS[mk]
    with _print_lock:
        print(f" {m['short'][:6]}:{answer or '?'}", end="", flush=True)

    return mk, answer, resp["content"], cost, tokens, api_calls


# ============================================================
# CGD-7 Protocol
# ============================================================
def run_cgd7_question(q: dict, weights: dict) -> dict:
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

    # ---- Phase 1: All 7 models answer independently (PARALLEL) ----
    solo_answers = {}
    solo_contents = {}

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(_call_single_model_solo, mk, choice_vars): mk
            for mk in MODEL_KEYS
        }
        for future in as_completed(futures):
            mk, answer, content, cost, tokens, calls = future.result()
            solo_answers[mk] = answer
            solo_contents[mk] = content
            q_cost += cost
            q_tokens += tokens
            api_calls += calls

    # ---- Phase 2: Agreement classification ----
    valid_answers = {k: v for k, v in solo_answers.items() if v is not None}
    n_valid = len(valid_answers)
    answer_counts = Counter(valid_answers.values())

    if not answer_counts:
        debate_type = "all_none"
        final_answer = None
        debate_answers = {}
        with _print_lock:
            print(f" [ALL_NONE]", end="", flush=True)
    else:
        majority_answer = answer_counts.most_common(1)[0][0]
        majority_count = answer_counts.most_common(1)[0][1]

        if majority_count >= LOCK_THRESHOLD:
            # LOCK — ≥5/7 agree
            if majority_count == n_valid:
                debate_type = "unanimous"
            elif majority_count >= 6:
                debate_type = "supermajority"
            else:
                debate_type = "strong_majority"
            final_answer = majority_answer
            debate_answers = {}
            with _print_lock:
                print(f" [{debate_type}={final_answer}({majority_count}/7)]", end="", flush=True)

        elif majority_count == 4:
            # Simple majority (4v3) — minority debates
            debate_type = "simple_majority_4v3"
            minority_models = [k for k, v in valid_answers.items() if v != majority_answer]
            majority_models = [k for k, v in valid_answers.items() if v == majority_answer]

            majority_reasoning = "\n\n".join([
                f"{MODELS[mk]['short']} (chose {majority_answer}): {solo_contents[mk][:600]}"
                for mk in majority_models
            ])

            debate_answers = dict(valid_answers)  # Start with solo answers

            # Only minority models debate (parallel)
            def _debate_minority(mk):
                m = MODELS[mk]
                prompt = CGD_DEBATE_MINORITY.format(
                    node_name=m["short"], model_short=m["short"],
                    my_answer=solo_answers[mk],
                    my_reasoning=solo_contents[mk][:600],
                    n_majority=len(majority_models),
                    n_total=len(MODEL_KEYS),
                    majority_answer=majority_answer,
                    majority_reasoning=majority_reasoning[:2000],
                    **choice_vars
                )
                resp = call_openrouter(prompt, mk, ARRIVAL_SYSTEM)
                new_answer = extract_answer_letter(resp["content"])
                with _print_lock:
                    print(f" D:{m['short'][:6]}:{new_answer or '?'}", end="", flush=True)
                return mk, new_answer, resp["cost"], resp["tokens_prompt"] + resp["tokens_completion"]

            with ThreadPoolExecutor(max_workers=len(minority_models)) as executor:
                debate_futures = [executor.submit(_debate_minority, mk) for mk in minority_models]
                for f in as_completed(debate_futures):
                    mk, new_ans, d_cost, d_tokens = f.result()
                    if new_ans:
                        debate_answers[mk] = new_ans
                    q_cost += d_cost
                    q_tokens += d_tokens
                    api_calls += 1

            # Weighted vote post-debate
            final_answer = _weighted_vote(debate_answers, weights)
            with _print_lock:
                print(f" [minority->{final_answer}]", end="", flush=True)

        else:
            # No clear majority (<4) — full debate for all 7
            debate_type = f"no_majority_{majority_count}v"
            debate_answers = {}

            all_reasoning = "\n\n".join([
                f"{MODELS[mk]['short']} (chose {solo_answers[mk]}): {solo_contents[mk][:400]}"
                for mk in MODEL_KEYS if solo_answers.get(mk)
            ])

            def _debate_full(mk):
                m = MODELS[mk]
                prompt = CGD_DEBATE_FULL.format(
                    node_name=m["short"], model_short=m["short"],
                    my_answer=solo_answers[mk] or "unknown",
                    my_reasoning=solo_contents.get(mk, "")[:400],
                    all_reasoning=all_reasoning[:3000],
                    **choice_vars
                )
                resp = call_openrouter(prompt, mk, ARRIVAL_SYSTEM)
                new_answer = extract_answer_letter(resp["content"])
                with _print_lock:
                    print(f" Df:{m['short'][:6]}:{new_answer or '?'}", end="", flush=True)
                return mk, new_answer, resp["cost"], resp["tokens_prompt"] + resp["tokens_completion"]

            with ThreadPoolExecutor(max_workers=7) as executor:
                debate_futures = [executor.submit(_debate_full, mk) for mk in MODEL_KEYS]
                for f in as_completed(debate_futures):
                    mk, new_ans, d_cost, d_tokens = f.result()
                    debate_answers[mk] = new_ans or solo_answers.get(mk)
                    q_cost += d_cost
                    q_tokens += d_tokens
                    api_calls += 1

            final_answer = _weighted_vote(debate_answers, weights)
            with _print_lock:
                print(f" [full->{final_answer}]", end="", flush=True)

    correct = final_answer == q["correct"] if final_answer else False

    return {
        "question_id": q["id"],
        "domain": q["domain"],
        "correct_answer": q["correct"],
        **{f"solo_{mk}": solo_answers.get(mk) for mk in MODEL_KEYS},
        "debate_type": debate_type,
        **{f"debate_{mk}": debate_answers.get(mk) for mk in MODEL_KEYS},
        "final_answer": final_answer,
        "correct": correct,
        "cost_usd": q_cost,
        "total_tokens": q_tokens,
        "api_calls": api_calls,
    }


def _weighted_vote(answers: dict, weights: dict) -> str:
    """Weighted majority vote. Returns winning answer letter."""
    vote_scores = Counter()
    for mk, ans in answers.items():
        if ans:
            vote_scores[ans] += weights.get(mk, 0.5)
    if vote_scores:
        return vote_scores.most_common(1)[0][0]
    return None


# ============================================================
# Save results (atomic write)
# ============================================================
def _save_results(results, total_cost, timestamp, weights):
    n = len(results)
    n_correct = sum(1 for r in results if r["correct"])

    # Debate type breakdown
    dt_counts = Counter(r["debate_type"] for r in results)
    dt_acc = {}
    for dt in dt_counts:
        dt_results = [r for r in results if r["debate_type"] == dt]
        dt_correct = sum(1 for r in dt_results if r["correct"])
        dt_acc[dt] = {"n": len(dt_results), "correct": dt_correct,
                       "accuracy": round(dt_correct / len(dt_results), 4)}

    # Per-model solo accuracy
    per_model = {}
    for mk in MODEL_KEYS:
        correct = sum(1 for r in results if r.get(f"solo_{mk}") == r["correct_answer"])
        none_count = sum(1 for r in results if r.get(f"solo_{mk}") is None)
        per_model[mk] = {
            "model_id": MODELS[mk]["id"],
            "short": MODELS[mk]["short"],
            "correct": correct, "total": n,
            "accuracy": round(correct / n, 4) if n else 0,
            "none_count": none_count,
        }

    # Simple MV (unweighted)
    simple_mv_correct = 0
    for r in results:
        votes = [r.get(f"solo_{mk}") for mk in MODEL_KEYS if r.get(f"solo_{mk}")]
        if votes:
            mv = Counter(votes).most_common(1)[0][0]
            if mv == r["correct_answer"]:
                simple_mv_correct += 1

    # Weighted MV (from solos only)
    weighted_mv_correct = 0
    for r in results:
        wmv = _weighted_vote({mk: r.get(f"solo_{mk}") for mk in MODEL_KEYS}, weights)
        if wmv == r["correct_answer"]:
            weighted_mv_correct += 1

    # Oracle
    oracle_correct = sum(
        1 for r in results
        if r["correct_answer"] in [r.get(f"solo_{mk}") for mk in MODEL_KEYS]
    )

    # Domain breakdown
    domains = set(r["domain"] for r in results)
    domain_acc = {}
    for dom in domains:
        dom_results = [r for r in results if r["domain"] == dom]
        dom_correct = sum(1 for r in dom_results if r["correct"])
        domain_acc[dom] = {"n": len(dom_results), "correct": dom_correct,
                           "accuracy": round(dom_correct / len(dom_results), 4)}

    data = {
        "phase": "Phase 23: CGD-7 (7-model ensemble)",
        "timestamp": timestamp,
        "n_questions": n,
        "models": {mk: MODELS[mk]["id"] for mk in MODEL_KEYS},
        "weights": weights,
        "summary": {
            "cgd7_correct": n_correct,
            "cgd7_accuracy": round(n_correct / n, 4) if n else 0,
            "simple_mv_correct": simple_mv_correct,
            "simple_mv_accuracy": round(simple_mv_correct / n, 4) if n else 0,
            "weighted_mv_correct": weighted_mv_correct,
            "weighted_mv_accuracy": round(weighted_mv_correct / n, 4) if n else 0,
            "oracle_correct": oracle_correct,
            "oracle_accuracy": round(oracle_correct / n, 4) if n else 0,
            "total_cost_usd": round(total_cost, 4),
            "total_api_calls": sum(r["api_calls"] for r in results),
            "debate_types": dt_acc,
            "per_model_solo": per_model,
            "per_domain": domain_acc,
        },
        "questions": results,
    }

    path = os.path.join(RESULTS_DIR, "cgd7_results.json")
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 23: CGD-7 (7-model ensemble)")
    parser.add_argument("--test", type=int, default=None, help="Pipeline test N questions")
    parser.add_argument("--weights", type=str, default=None,
                        help="Path to solo baselines JSON (for model weights)")
    args = parser.parse_args()

    assert API_KEYS, "OPENROUTER_API_KEY env var required (comma-separated for multiple)"
    print(f"  API keys loaded: {len(API_KEYS)} key(s)")

    # Load weights
    if args.weights:
        weights = load_weights(args.weights)
        print(f"  Weights loaded from: {args.weights}")
    else:
        # Auto-detect from results/
        auto_paths = [
            os.path.join(RESULTS_DIR, "solo_baselines_20q.json"),
            os.path.join(RESULTS_DIR, "solo_baselines_198q.json"),
        ]
        weights = None
        for p in auto_paths:
            if os.path.exists(p):
                weights = load_weights(p)
                print(f"  Weights auto-loaded from: {p}")
                break
        if weights is None:
            print("  WARNING: No weights file found. Using equal weights (0.5 each).")
            weights = {mk: 0.5 for mk in MODEL_KEYS}

    for mk in MODEL_KEYS:
        print(f"    {MODELS[mk]['short']:20s}: weight={weights[mk]:.3f}")

    all_questions = load_questions()

    if args.test:
        questions = all_questions[:args.test]
        filename_hint = "test"
        print(f"\n  *** PIPELINE TEST: {args.test} questions ***\n")
    else:
        questions = all_questions
        filename_hint = "full"
        print(f"\n  Full CGD-7 run: {len(questions)} questions × 7 models\n")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Resume support
    results_path = os.path.join(RESULTS_DIR, "cgd7_results.json")
    existing_results = []
    done_ids = set()
    if os.path.exists(results_path) and not args.test:
        with open(results_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_results = existing_data.get("questions", [])
        done_ids = {r["question_id"] for r in existing_results}
        print(f"  RESUMING: found {len(existing_results)} completed questions")

    total_cost = sum(r.get("cost_usd", 0) for r in existing_results)
    results = list(existing_results)
    n_remaining = sum(1 for q in questions if q["id"] not in done_ids)

    print("=" * 70)
    print(f"  Phase 23: CGD-7 — {len(questions)} questions × {len(MODEL_KEYS)} models")
    print(f"  Models: {', '.join(MODELS[mk]['short'] for mk in MODEL_KEYS)}")
    print(f"  Lock threshold: ≥{LOCK_THRESHOLD}/{len(MODEL_KEYS)} | Debate: <{LOCK_THRESHOLD}/{len(MODEL_KEYS)}")
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
        result = run_cgd7_question(q, weights)
        results.append(result)
        total_cost += result["cost_usd"]
        questions_done += 1

        mark = "+" if result["correct"] else "-"
        n_models = len(MODEL_KEYS)
        n_solo_correct = sum(1 for mk in MODEL_KEYS if result.get(f"solo_{mk}") == result["correct_answer"])
        print(f" {mark} ({n_solo_correct}/{n_models}solo) ${result['cost_usd']:.3f}")

        # Progress report every 5 questions
        n = len(results)
        cgd_acc = sum(1 for r in results if r["correct"]) / n * 100

        if i % 5 == 4 or i == len(questions) - 1:
            elapsed = time.time() - start_time
            eta = elapsed / questions_done * n_remaining - elapsed if questions_done > 0 else 0

            # Per-model solo acc (running)
            model_accs = []
            for mk in MODEL_KEYS:
                acc = sum(1 for r in results if r.get(f"solo_{mk}") == r["correct_answer"]) / n * 100
                model_accs.append(f"{MODELS[mk]['short'][:4]}={acc:.0f}%")

            # Debate breakdown
            dt = Counter(r["debate_type"] for r in results)
            dt_str = " ".join(f"{k}:{v}" for k, v in dt.most_common(4))

            print(f"  [{n}/{len(questions)}] CGD={cgd_acc:.1f}% | {' '.join(model_accs)}")
            print(f"  Debate: {dt_str} | Cost=${total_cost:.2f} ETA={timedelta(seconds=max(0, int(eta)))}")

        # Save after every question
        _save_results(results, total_cost, timestamp, weights)

    # ---- Final Summary ----
    print("\n" + "=" * 70)
    print("  PHASE 23 CGD-7 — COMPLETE")
    print("=" * 70)

    n = len(results)
    n_correct = sum(1 for r in results if r["correct"])
    print(f"\n  CGD-7 accuracy: {n_correct}/{n} = {n_correct/n*100:.1f}%")

    # Per-model solo
    print(f"\n  Per-model solo accuracy:")
    for mk in MODEL_KEYS:
        correct = sum(1 for r in results if r.get(f"solo_{mk}") == r["correct_answer"])
        print(f"    {MODELS[mk]['short']:20s}: {correct}/{n} = {correct/n*100:.1f}%")

    # Simple MV
    smv = 0
    for r in results:
        votes = [r.get(f"solo_{mk}") for mk in MODEL_KEYS if r.get(f"solo_{mk}")]
        if votes and Counter(votes).most_common(1)[0][0] == r["correct_answer"]:
            smv += 1
    print(f"\n  Simple MV: {smv}/{n} = {smv/n*100:.1f}%")

    # Weighted MV
    wmv = 0
    for r in results:
        w = _weighted_vote({mk: r.get(f"solo_{mk}") for mk in MODEL_KEYS}, weights)
        if w == r["correct_answer"]:
            wmv += 1
    print(f"  Weighted MV: {wmv}/{n} = {wmv/n*100:.1f}%")

    # CGD-7
    print(f"  CGD-7: {n_correct}/{n} = {n_correct/n*100:.1f}%")

    # Oracle
    oracle = sum(1 for r in results if r["correct_answer"] in [r.get(f"solo_{mk}") for mk in MODEL_KEYS])
    print(f"  Oracle: {oracle}/{n} = {oracle/n*100:.1f}%")

    # Debate breakdown
    print(f"\n  Debate type breakdown:")
    dt_counts = Counter(r["debate_type"] for r in results)
    for dt, count in dt_counts.most_common():
        dt_results = [r for r in results if r["debate_type"] == dt]
        dt_correct = sum(1 for r in dt_results if r["correct"])
        print(f"    {dt:25s}: {count} ({dt_correct}/{count} = {dt_correct/count*100:.1f}%)")

    print(f"\n  Total cost: ${total_cost:.2f}")
    print(f"  Total API calls: {sum(r['api_calls'] for r in results)}")
    elapsed = time.time() - start_time
    print(f"  Runtime: {timedelta(seconds=int(elapsed))}")


if __name__ == "__main__":
    main()
