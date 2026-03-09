# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 20: Solo Chain-of-Thought Baseline (Full GPQA Diamond, 198 questions)

Replicates Phase 17 methodology on the full dataset:
- Model: Qwen3-235B (qwen/qwen3-235b-a22b)
- 5 independent runs per question, majority vote
- /no_think suffix to disable reasoning tokens
- Crash protection: saves after EACH question, resumes from last saved

Usage:
    set OPENROUTER_API_KEY=sk-or-v1-...
    python run_solo_cot.py              # Full run (198 questions)
    python run_solo_cot.py --test 5     # Pipeline test (5 questions)
"""

import json
import math
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

# ============================================================
# Configuration
# ============================================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_ID = "qwen/qwen3-235b-a22b"
MODEL_SHORT = "Qwen3-235B"

N_RUNS_PER_QUESTION = 5
TEMPERATURE = 0.7
MAX_TOKENS = 2048
BUDGET_LIMIT = 8.0  # USD safety cap for solo CoT
SLEEP_BETWEEN_CALLS = 0.5  # seconds

SOLO_COT_SYSTEM = """You are a world-class scientist with deep expertise across physics, \
chemistry, biology, and mathematics. You are answering a graduate-level \
multiple-choice question from the GPQA Diamond benchmark.

IMPORTANT INSTRUCTIONS:
1. Read the question and all answer choices carefully.
2. Think step by step through the problem. Show your complete reasoning chain.
3. Consider each answer choice systematically — explain why it is or is not correct.
4. If you are uncertain, reason through by elimination.
5. After your full analysis, state your final answer clearly.

End your response with exactly: "The answer is X" where X is A, B, C, or D."""

# Phase 13 baselines for consistency check
PHASE13_ARRIVAL_ACCURACY = 0.638  # 51/80 (alpha trio: 26/40)
PHASE13_MV_ACCURACY = 0.425       # 34/80 (alpha trio: 21/40)

# ============================================================
# Load questions
# ============================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load_questions():
    """Load GPQA Diamond 198 questions from JSON."""
    path = os.path.join(DATA_DIR, "gpqa_diamond_198.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# API call
# ============================================================
def call_openrouter(question_text: str, run_idx: int) -> dict:
    """Make a single API call to OpenRouter with /no_think suffix."""
    import requests

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Methodiy-Kelevra/ARRIVAL",
        "X-Title": "ARRIVAL Phase 20 Solo CoT",
    }

    # Append /no_think to disable reasoning tokens (saves ~50x cost)
    user_content = question_text + "\n\n/no_think"

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": SOLO_COT_SYSTEM},
            {"role": "user", "content": user_content},
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
                timeout=120,
            )
            latency_ms = (time.time() - start_time) * 1000

            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            # Cost calculation (Qwen3-235B: $0.455/1M in, $1.82/1M out)
            cost = (
                usage.get("prompt_tokens", 0) * 0.455 / 1_000_000
                + usage.get("completion_tokens", 0) * 1.82 / 1_000_000
            )

            # Extract model version from response
            model_version = data.get("model", MODEL_ID)

            return {
                "content": content,
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "tokens_reasoning": usage.get("reasoning_tokens", 0),
                "cost": cost,
                "latency_ms": round(latency_ms, 1),
                "model_version": model_version,
            }
        except Exception as e:
            if attempt == 2:
                print(f"    ERROR run {run_idx}: {e}")
                return {
                    "content": "", "tokens_prompt": 0, "tokens_completion": 0,
                    "tokens_reasoning": 0, "cost": 0, "latency_ms": 0,
                    "model_version": MODEL_ID,
                }
            time.sleep(2 ** (attempt + 1))

    return {
        "content": "", "tokens_prompt": 0, "tokens_completion": 0,
        "tokens_reasoning": 0, "cost": 0, "latency_ms": 0,
        "model_version": MODEL_ID,
    }


# ============================================================
# Answer extraction (Phase 17 replication)
# ============================================================
def extract_answer(text: str) -> str:
    """Extract answer letter from CoT response. Comprehensive cascade."""
    if not text:
        return ""

    # P1: "The answer is X" / "correct answer is X"
    m = re.search(r'(?:the\s+)?(?:correct\s+)?answer\s+is\s*[:\s]*([A-D])\b', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # P2: "I choose/select/pick X" / "I'll go with X"
    m = re.search(r"(?:choose|select|pick|go\s+with)\s+(?:option\s+)?([A-D])\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # P3: "Answer: X" or "Answer - X"
    m = re.search(r'answer\s*[:\-]\s*([A-D])\b', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # P4: Bold **B** or __B__
    m = re.search(r'\*\*([A-D])\*\*', text)
    if m:
        return m.group(1).upper()

    # P5: "Option X" at end, or "option (X)"
    m = re.search(r'option\s*\(?([A-D])\)?\s*$', text.strip(), re.IGNORECASE | re.MULTILINE)
    if m:
        return m.group(1).upper()

    # P6: "(X)" standalone on a line, or near end
    matches = re.findall(r'\(([A-D])\)', text)
    if matches:
        return matches[-1].upper()

    # P7: Last standalone A-D on its own line
    lines = text.strip().split("\n")
    for line in reversed(lines):
        stripped = line.strip()
        if re.match(r'^[A-D]\.?\s*$', stripped):
            return stripped[0].upper()

    # P8: "X." or "X)" at the start of the last few lines
    for line in reversed(lines[-5:]):
        stripped = line.strip()
        m = re.match(r'^([A-D])[.)\s]', stripped)
        if m and len(stripped) < 20:
            return m.group(1).upper()

    # P9: \boxed{X} (LaTeX common in math-oriented models)
    m = re.search(r'\\boxed\{([A-D])\}', text)
    if m:
        return m.group(1).upper()

    # P10: last A/B/C/D word-boundary in last 200 chars
    m = re.search(r'\b([A-D])\b', text[-200:])
    if m:
        return m.group(1).upper()

    return ""


def format_question(q: dict) -> str:
    """Format a GPQA question for the prompt."""
    choices = q["choices"]
    text = f"{q['question']}\n\n"
    for letter in ["A", "B", "C", "D"]:
        text += f"{letter}. {choices[letter]}\n"
    return text


# ============================================================
# Fisher's exact test
# ============================================================
def fishers_exact_2x2(a, b, c, d):
    """Fisher's exact test for 2x2 contingency table (two-sided)."""
    n = a + b + c + d
    if n == 0:
        return 1.0

    def log_fact(k):
        return sum(math.log(i) for i in range(1, k + 1)) if k > 0 else 0.0

    log_p_obs = (
        log_fact(a + b) + log_fact(c + d) + log_fact(a + c) + log_fact(b + d)
        - log_fact(n) - log_fact(a) - log_fact(b) - log_fact(c) - log_fact(d)
    )
    p_obs = math.exp(log_p_obs)

    p_value = 0.0
    row1, row2, col1 = a + b, c + d, a + c

    for i in range(min(row1, col1) + 1):
        j = row1 - i
        k = col1 - i
        l_val = row2 - k
        if j < 0 or k < 0 or l_val < 0:
            continue
        log_p = (
            log_fact(row1) + log_fact(row2) + log_fact(col1) + log_fact(j + l_val)
            - log_fact(n) - log_fact(i) - log_fact(j) - log_fact(k) - log_fact(l_val)
        )
        p_i = math.exp(log_p)
        if p_i <= p_obs * 1.0001:
            p_value += p_i

    return min(1.0, p_value)


# ============================================================
# Main experiment
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 20: Solo CoT Baseline (GPQA Diamond)")
    parser.add_argument("--test", type=int, default=None, help="Number of questions for pipeline test")
    args = parser.parse_args()

    assert OPENROUTER_API_KEY, (
        "OPENROUTER_API_KEY environment variable is required. "
        "See .env.example for configuration."
    )

    questions = load_questions()
    if args.test:
        questions = questions[:args.test]
        print(f"\n  *** PIPELINE TEST MODE: {args.test} questions ***\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Check for existing results to resume from
    results_file = os.path.join(RESULTS_DIR, "solo_cot_results.json")
    existing_results = []
    if os.path.exists(results_file) and not args.test:
        with open(results_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_results = existing_data.get("questions", [])
        done_ids = {r["question_id"] for r in existing_results}
        print(f"  RESUMING: found {len(existing_results)} completed questions")
    else:
        done_ids = set()

    n_total = len(questions)
    n_remaining = sum(1 for q in questions if q["id"] not in done_ids)

    print("=" * 70)
    print("  ARRIVAL Protocol -- Phase 20: Solo CoT Baseline")
    print(f"  Model: {MODEL_SHORT} ({MODEL_ID})")
    print(f"  Questions: {n_total} GPQA Diamond")
    print(f"  Remaining: {n_remaining}")
    print(f"  Runs per question: {N_RUNS_PER_QUESTION}")
    print(f"  Temperature: {TEMPERATURE}, Max tokens: {MAX_TOKENS}")
    print(f"  Budget limit: ${BUDGET_LIMIT:.2f}")
    print(f"  /no_think: ENABLED (reasoning tokens disabled)")
    print("=" * 70)

    # ETA estimation
    est_seconds_per_q = N_RUNS_PER_QUESTION * (3 + SLEEP_BETWEEN_CALLS)  # ~3s per API call
    est_total_seconds = n_remaining * est_seconds_per_q
    est_finish = datetime.now() + timedelta(seconds=est_total_seconds)
    print(f"  Estimated time: ~{est_total_seconds/60:.0f} minutes")
    print(f"  ETA: {est_finish.strftime('%H:%M:%S')}")
    print()

    total_cost = sum(
        sum(r["cost"] for r in q.get("runs", []))
        for q in existing_results
    )
    total_calls = sum(len(q.get("runs", [])) for q in existing_results)
    all_results = list(existing_results)
    start_time = time.time()
    questions_done_this_session = 0

    for qi, q in enumerate(questions):
        if q["id"] in done_ids:
            continue

        print(f"  Q{qi+1}/{n_total}: {q['id']} [{q['domain']}]", end="", flush=True)
        q_text = format_question(q)
        runs = []

        for run_idx in range(N_RUNS_PER_QUESTION):
            if total_cost >= BUDGET_LIMIT:
                print(f"\n  BUDGET EXCEEDED (${total_cost:.2f} >= ${BUDGET_LIMIT:.2f})")
                break

            resp = call_openrouter(q_text, run_idx)
            answer = extract_answer(resp["content"])
            correct = answer == q["correct"]
            total_cost += resp["cost"]
            total_calls += 1

            # Save both letter and text of chosen answer for consistency check
            chosen_text = q["choices"].get(answer, "") if answer else ""

            runs.append({
                "run_idx": run_idx,
                "answer": answer,
                "answer_text": chosen_text,
                "correct": correct,
                "tokens_prompt": resp["tokens_prompt"],
                "tokens_completion": resp["tokens_completion"],
                "tokens_reasoning": resp["tokens_reasoning"],
                "cost": resp["cost"],
                "latency_ms": resp["latency_ms"],
                "model_version": resp["model_version"],
                "reasoning_length": len(resp["content"]),
                "tail_snippet": resp["content"][-300:] if resp["content"] else "",
            })

            marker = "+" if correct else "-"
            print(f" {answer}({marker})", end="", flush=True)

            time.sleep(SLEEP_BETWEEN_CALLS)

        # Majority vote
        answers = [r["answer"] for r in runs if r["answer"]]
        if answers:
            mv_answer = Counter(answers).most_common(1)[0][0]
        else:
            mv_answer = ""
        mv_correct = mv_answer == q["correct"]

        # Best-of-N (oracle)
        oracle_correct = any(r["correct"] for r in runs)

        # Save chosen answer text for majority vote too
        mv_answer_text = q["choices"].get(mv_answer, "") if mv_answer else ""

        result_entry = {
            "question_id": q["id"],
            "domain": q["domain"],
            "subdomain": q.get("subdomain", ""),
            "correct_answer": q["correct"],
            "correct_answer_text": q["choices"].get(q["correct"], ""),
            "runs": runs,
            "majority_vote": {
                "answer": mv_answer,
                "answer_text": mv_answer_text,
                "correct": mv_correct,
            },
            "oracle": {"correct": oracle_correct},
            "per_run_accuracy": sum(1 for r in runs if r["correct"]) / len(runs) if runs else 0,
        }

        all_results.append(result_entry)
        questions_done_this_session += 1

        # Progress
        mv_sym = "+" if mv_correct else "-"
        elapsed = time.time() - start_time
        avg_time = elapsed / questions_done_this_session
        remaining_q = n_remaining - questions_done_this_session
        eta_seconds = remaining_q * avg_time
        eta_str = str(timedelta(seconds=int(eta_seconds)))
        print(f" MV:{mv_answer}({mv_sym}) ${total_cost:.2f} ETA:{eta_str}")

        # Save after EACH question (crash protection)
        _save_results(results_file, all_results, total_cost, total_calls, timestamp)

        if total_cost >= BUDGET_LIMIT:
            print(f"\n  BUDGET LIMIT REACHED: ${total_cost:.2f}")
            break

    # ---- Final Summary ----
    _print_summary(all_results, total_cost, total_calls)
    print(f"\n  Results saved: {results_file}")
    print(f"  Total time: {timedelta(seconds=int(time.time() - start_time))}")


def _save_results(filepath, all_results, total_cost, total_calls, timestamp):
    """Save results to JSON (crash protection)."""
    n_questions = len(all_results)
    solo_correct = sum(sum(1 for r in q["runs"] if r["correct"]) for q in all_results)
    solo_total = sum(len(q["runs"]) for q in all_results)
    mv_correct_count = sum(1 for q in all_results if q["majority_vote"]["correct"])
    oracle_correct_count = sum(1 for q in all_results if q["oracle"]["correct"])

    solo_acc = solo_correct / solo_total if solo_total else 0
    mv_acc = mv_correct_count / n_questions if n_questions else 0
    oracle_acc = oracle_correct_count / n_questions if n_questions else 0

    # Per-domain breakdown
    domains = {}
    for q in all_results:
        d = q["domain"]
        if d not in domains:
            domains[d] = {"correct": 0, "total": 0}
        domains[d]["total"] += 1
        if q["majority_vote"]["correct"]:
            domains[d]["correct"] += 1
    per_domain = {
        d: {"accuracy": v["correct"] / v["total"] if v["total"] else 0, **v}
        for d, v in domains.items()
    }

    summary = {
        "phase": 20,
        "experiment": "Solo CoT Baseline (Full GPQA Diamond)",
        "model": MODEL_ID,
        "model_short": MODEL_SHORT,
        "n_questions": n_questions,
        "n_runs_per_question": N_RUNS_PER_QUESTION,
        "temperature": TEMPERATURE,
        "no_think": True,
        "solo": {"accuracy": solo_acc, "correct": solo_correct, "total": solo_total},
        "majority_vote": {"accuracy": mv_acc, "correct": mv_correct_count, "total": n_questions},
        "oracle": {"accuracy": oracle_acc, "correct": oracle_correct_count, "total": n_questions},
        "per_domain": per_domain,
        "cost_usd": total_cost,
        "api_calls": total_calls,
        "timestamp": timestamp,
        "last_updated": datetime.now().isoformat(),
    }

    output = {"summary": summary, "questions": all_results}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def _print_summary(all_results, total_cost, total_calls):
    """Print final summary report."""
    n_questions = len(all_results)
    solo_correct = sum(sum(1 for r in q["runs"] if r["correct"]) for q in all_results)
    solo_total = sum(len(q["runs"]) for q in all_results)
    mv_correct_count = sum(1 for q in all_results if q["majority_vote"]["correct"])
    oracle_correct_count = sum(1 for q in all_results if q["oracle"]["correct"])

    solo_acc = solo_correct / solo_total if solo_total else 0
    mv_acc = mv_correct_count / n_questions if n_questions else 0
    oracle_acc = oracle_correct_count / n_questions if n_questions else 0

    print(f"\n{'='*70}")
    print(f"  Phase 20: Solo CoT Baseline -- Final Results")
    print(f"{'='*70}")
    print(f"  Solo per-run accuracy:   {solo_acc*100:.1f}% ({solo_correct}/{solo_total})")
    print(f"  Solo CoT Majority Vote:  {mv_acc*100:.1f}% ({mv_correct_count}/{n_questions})")
    print(f"  Solo CoT Oracle (best):  {oracle_acc*100:.1f}% ({oracle_correct_count}/{n_questions})")
    print(f"  ---")

    # Per-domain
    domains = {}
    for q in all_results:
        d = q["domain"]
        if d not in domains:
            domains[d] = {"correct": 0, "total": 0}
        domains[d]["total"] += 1
        if q["majority_vote"]["correct"]:
            domains[d]["correct"] += 1

    print(f"  Per domain:")
    for d, v in sorted(domains.items()):
        acc = v["correct"] / v["total"] if v["total"] else 0
        print(f"    {d:20s} {acc*100:.1f}% ({v['correct']}/{v['total']})")
    print(f"  ---")
    print(f"  Cost: ${total_cost:.2f}, API calls: {total_calls}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
