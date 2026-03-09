# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 22b: Confidence-Gated Debate on FULL GPQA Diamond (198 questions)

Runs CGD protocol on ALL 198 questions for full-scale validation.
CGD showed 17/20 = 85.0% on the hardest 20 questions in Phase 22.

CGD Protocol:
  1. All 3 models answer INDEPENDENTLY (no anchoring)
  2. If unanimous → answer locked (no debate)
  3. If 2-1 split → minority debates against majority (1 round)
  4. If 3-way split → all 3 debate (3 rounds)
  5. NO R4 — final answer = MV after debate

Transparency: Each API call is independent, no context from previous
experiments. Models do not see Phase 21 results or any prior answers.

Usage:
    set OPENROUTER_API_KEY=sk-or-v1-...
    python run_cgd_full.py              # Full run (198 questions)
    python run_cgd_full.py --test 5     # Pipeline test (5 questions)
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
    "gpt": {"id": "openai/gpt-4.1", "short": "GPT-4.1", "cost_input": 2.00, "cost_output": 8.00},
    "gemini": {"id": "google/gemini-3-flash-preview", "short": "Gemini3Flash", "cost_input": 0.50, "cost_output": 3.00},
    "grok": {"id": "x-ai/grok-4.1-fast", "short": "Grok4.1", "cost_input": 0.60, "cost_output": 2.40},
}

MODEL_COSTS = {m["id"]: {"input": m["cost_input"], "output": m["cost_output"]} for m in MODELS.values()}

TEMPERATURE = 0.3
MAX_TOKENS = 2048
BUDGET_LIMIT = 15.0  # Higher budget for 198 questions
SLEEP_BETWEEN_CALLS = 1.5  # Slightly faster for bulk run

# ============================================================
# Prompts (identical to Phase 22 test)
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

ARRIVAL_SYSTEM = """You are a node in the DEUS.PROTOCOL v0.5 communication network.
You use semantic atoms for structured reasoning:
@SELF — your identity and perspective
@OTHER — acknowledging the other node
@GOAL — the task objective
@INT — your reasoning intention
@C — coherence of your analysis (use @C[0.0-1.0] to express numeric confidence)
@CONSENSUS — when you agree with another node
@CONFLICT — when you disagree and explain why
@RESOLUTION — your proposed resolution

Your task: Answer a multiple-choice question through collaborative reasoning.
Use the atoms above to structure your response.
Analyze the question, share your reasoning, and engage with other nodes' perspectives.
When stating your final answer, use: @CONSENSUS[answer=X] where X is A, B, C, or D."""

CGD_DEBATE_PROMPT = """You are Node {node_name} ({model_short}).
You previously answered this question with "{my_answer}" and your reasoning was:
{my_reasoning}

However, {n_others} other expert(s) chose "{majority_answer}" instead.
Their reasoning:
{other_reasoning}

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
def call_openrouter(prompt: str, model: str, system_prompt: str) -> dict:
    import requests

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Methodiy-Kelevra/ARRIVAL",
        "X-Title": "ARRIVAL Phase 22b CGD Full",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }

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
                print(f"      Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            pricing = MODEL_COSTS.get(model, {"input": 2.0, "output": 8.0})
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
                "model_version": data.get("model", model),
            }
        except Exception as e:
            if attempt == 2:
                print(f"      ERROR: {e}")
                return {"content": "", "tokens_prompt": 0, "tokens_completion": 0,
                        "cost": 0, "latency_ms": 0, "model_version": model}
            time.sleep(2 ** (attempt + 1))

    return {"content": "", "tokens_prompt": 0, "tokens_completion": 0,
            "cost": 0, "latency_ms": 0, "model_version": model}


# ============================================================
# CGD Protocol
# ============================================================
def run_cgd_question(q: dict) -> dict:
    """Confidence-Gated Debate: solo first, debate only on disagreement."""
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

    # ---- Step 1: All 3 models answer independently ----
    solo_answers = {}
    solo_responses = {}
    model_order = ["grok", "gemini", "gpt"]

    for mk in model_order:
        m = MODELS[mk]
        prompt = SOLO_PROMPT.format(**choice_vars)
        resp = call_openrouter(prompt, m["id"], "You are a world-class scientist.")
        answer = extract_answer_letter(resp["content"])
        solo_answers[mk] = answer
        solo_responses[mk] = resp["content"]
        q_cost += resp["cost"]
        q_tokens += resp["tokens_prompt"] + resp["tokens_completion"]
        api_calls += 1
        print(f" {m['short']}:{answer or '?'}", end="", flush=True)
        time.sleep(SLEEP_BETWEEN_CALLS)

    # ---- Step 2: Check agreement ----
    valid_answers = {k: v for k, v in solo_answers.items() if v is not None}
    answer_counts = Counter(valid_answers.values())

    if len(answer_counts) == 0:
        final_answer = None
        debate_type = "all_none"
        print(f" [ALL_NONE]", end="", flush=True)

    elif len(answer_counts) == 1 or (answer_counts.most_common(1)[0][1] >= 2 and len(valid_answers) >= 2):
        majority_answer = answer_counts.most_common(1)[0][0]
        majority_count = answer_counts.most_common(1)[0][1]

        if majority_count == len(valid_answers):
            # UNANIMOUS — lock
            final_answer = majority_answer
            debate_type = "unanimous"
            print(f" [U={final_answer}]", end="", flush=True)
        else:
            # 2-1 SPLIT — minority debates
            debate_type = "split_2v1"
            minority_models = [k for k, v in valid_answers.items() if v != majority_answer]
            majority_models = [k for k, v in valid_answers.items() if v == majority_answer]

            majority_reasoning = "\n\n".join([
                f"{MODELS[mk]['short']}: {solo_responses[mk][:800]}"
                for mk in majority_models
            ])

            debate_answers = dict(valid_answers)
            for mk in minority_models:
                m = MODELS[mk]
                debate_prompt = CGD_DEBATE_PROMPT.format(
                    node_name=m["short"], model_short=m["short"],
                    my_answer=solo_answers[mk],
                    my_reasoning=solo_responses[mk][:800],
                    n_others=len(majority_models),
                    majority_answer=majority_answer,
                    other_reasoning=majority_reasoning[:1500],
                    **choice_vars
                )
                resp = call_openrouter(debate_prompt, m["id"], ARRIVAL_SYSTEM)
                new_answer = extract_answer_letter(resp["content"])
                if new_answer:
                    debate_answers[mk] = new_answer
                q_cost += resp["cost"]
                q_tokens += resp["tokens_prompt"] + resp["tokens_completion"]
                api_calls += 1
                print(f" D:{m['short']}:{new_answer or '?'}", end="", flush=True)
                time.sleep(SLEEP_BETWEEN_CALLS)

            post_debate = [v for v in debate_answers.values() if v]
            final_answer = Counter(post_debate).most_common(1)[0][0] if post_debate else None
            print(f" [2v1->{final_answer}]", end="", flush=True)
    else:
        # 3-WAY SPLIT — full debate
        debate_type = "split_3way"
        debate_answers = {}
        for mk in model_order:
            m = MODELS[mk]
            others = {k: v for k, v in solo_responses.items() if k != mk}
            other_text = "\n\n".join([
                f"{MODELS[k]['short']} (chose {solo_answers[k]}): {v[:600]}"
                for k, v in others.items()
            ])
            debate_prompt = CGD_DEBATE_PROMPT.format(
                node_name=m["short"], model_short=m["short"],
                my_answer=solo_answers[mk],
                my_reasoning=solo_responses[mk][:600],
                n_others=2,
                majority_answer="different answers",
                other_reasoning=other_text[:1500],
                **choice_vars
            )
            resp = call_openrouter(debate_prompt, m["id"], ARRIVAL_SYSTEM)
            new_answer = extract_answer_letter(resp["content"])
            debate_answers[mk] = new_answer or solo_answers[mk]
            q_cost += resp["cost"]
            q_tokens += resp["tokens_prompt"] + resp["tokens_completion"]
            api_calls += 1
            print(f" D3:{m['short']}:{new_answer or '?'}", end="", flush=True)
            time.sleep(SLEEP_BETWEEN_CALLS)

        post_debate = [v for v in debate_answers.values() if v]
        final_answer = Counter(post_debate).most_common(1)[0][0] if post_debate else None
        print(f" [3way->{final_answer}]", end="", flush=True)

    correct = final_answer == q["correct"] if final_answer else False

    return {
        "question_id": q["id"],
        "domain": q["domain"],
        "correct_answer": q["correct"],
        "correct_answer_text": q["choices"].get(q["correct"], ""),
        "solo_grok": solo_answers.get("grok"),
        "solo_gemini": solo_answers.get("gemini"),
        "solo_gpt": solo_answers.get("gpt"),
        "debate_type": debate_type,
        "final_answer": final_answer,
        "final_answer_text": q["choices"].get(final_answer, "") if final_answer else "",
        "correct": correct,
        "cost_usd": q_cost,
        "total_tokens": q_tokens,
        "api_calls": api_calls,
    }


# ============================================================
# Save results (atomic write)
# ============================================================
def _save_results(results, total_cost, timestamp):
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

    # Domain breakdown
    domains = set(r["domain"] for r in results)
    domain_acc = {}
    for dom in domains:
        dom_results = [r for r in results if r["domain"] == dom]
        dom_correct = sum(1 for r in dom_results if r["correct"])
        domain_acc[dom] = {"n": len(dom_results), "correct": dom_correct,
                           "accuracy": round(dom_correct / len(dom_results), 4)}

    data = {
        "phase": "Phase 22b: CGD Full (198 questions)",
        "timestamp": timestamp,
        "n_questions": n,
        "summary": {
            "n_correct": n_correct,
            "accuracy": round(n_correct / n, 4) if n else 0,
            "total_cost_usd": round(total_cost, 4),
            "total_api_calls": sum(r["api_calls"] for r in results),
            "debate_types": dt_acc,
            "per_domain": domain_acc,
        },
        "questions": results,
    }

    path = os.path.join(RESULTS_DIR, "cgd_full_results.json")
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 22b: CGD Full (198 questions)")
    parser.add_argument("--test", type=int, default=None, help="Pipeline test N questions")
    args = parser.parse_args()

    assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY env var required"

    all_questions = load_questions()
    if args.test:
        questions = all_questions[:args.test]
        print(f"\n  *** PIPELINE TEST MODE: {args.test} questions ***\n")
    else:
        questions = all_questions
        print(f"\n  Full run: {len(questions)} questions\n")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Resume support
    results_path = os.path.join(RESULTS_DIR, "cgd_full_results.json")
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
    print("  Phase 22b: Confidence-Gated Debate — Full GPQA Diamond")
    print(f"  Questions: {len(questions)}, Remaining: {n_remaining}")
    print(f"  Budget: ${BUDGET_LIMIT}")
    print("=" * 70)

    start_time = time.time()
    questions_done = 0

    for i, q in enumerate(questions):
        if q["id"] in done_ids:
            continue

        if total_cost >= BUDGET_LIMIT:
            print(f"\n  BUDGET LIMIT reached at ${total_cost:.2f}")
            break

        print(f"\n[{i+1}/{len(questions)}] {q['id']} ({q['domain']}) CGD:", end="", flush=True)
        result = run_cgd_question(q)
        results.append(result)
        total_cost += result["cost_usd"]
        questions_done += 1

        mark = "+" if result["correct"] else "-"
        print(f" -> {result['final_answer']}{mark} ${result['cost_usd']:.3f}", flush=True)

        # Running stats every question
        n = len(results)
        n_correct = sum(1 for r in results if r["correct"])
        acc = n_correct / n * 100

        if i % 10 == 9 or i == len(questions) - 1:
            dt_counts = Counter(r["debate_type"] for r in results)
            elapsed = time.time() - start_time
            eta = elapsed / questions_done * n_remaining - elapsed if questions_done > 0 else 0
            print(f"  [{n}/{len(questions)}] Acc={acc:.1f}% Cost=${total_cost:.2f}"
                  f" Types={dict(dt_counts)} ETA={timedelta(seconds=max(0, int(eta)))}")

        # Save after every question
        _save_results(results, total_cost, timestamp)

    # Final summary
    print("\n" + "=" * 70)
    print("  PHASE 22b CGD FULL — COMPLETE")
    print("=" * 70)
    n = len(results)
    n_correct = sum(1 for r in results if r["correct"])
    print(f"  CGD accuracy: {n_correct}/{n} = {n_correct/n*100:.1f}%")
    print(f"  Total cost:   ${total_cost:.2f}")
    print(f"  Total calls:  {sum(r['api_calls'] for r in results)}")
    elapsed = time.time() - start_time
    print(f"  Runtime:      {timedelta(seconds=int(elapsed))}")

    # Debate type breakdown
    dt_counts = Counter(r["debate_type"] for r in results)
    print(f"\n  Debate types: {dict(dt_counts)}")
    for dt in sorted(dt_counts.keys()):
        dt_results = [r for r in results if r["debate_type"] == dt]
        dt_correct = sum(1 for r in dt_results if r["correct"])
        print(f"    {dt}: {dt_correct}/{len(dt_results)} = {dt_correct/len(dt_results)*100:.1f}%")

    # Domain breakdown
    for domain in ["Physics", "Chemistry", "Biology"]:
        dom_results = [r for r in results if r["domain"] == domain]
        if dom_results:
            dom_correct = sum(1 for r in dom_results if r["correct"])
            print(f"  {domain}: {dom_correct}/{len(dom_results)} = {dom_correct/len(dom_results)*100:.1f}%")


if __name__ == "__main__":
    main()
