# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 17: Solo Chain-of-Thought Baseline Experiment

Runs a single Qwen3-235B with enhanced CoT prompting on 40 GPQA Diamond
questions, 5 independent runs each. Compares against Phase 16 ARRIVAL (65%)
and Majority Vote (52.5%) baselines.

Usage:
    export OPENROUTER_API_KEY="sk-or-v1-..."
    python run_phase17.py
"""

import json
import math
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime

# Windows encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config_phase17 import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL_ID,
    MODEL_SHORT,
    N_RUNS_PER_QUESTION,
    TEMPERATURE,
    MAX_TOKENS,
    BUDGET_LIMIT,
    SOLO_COT_SYSTEM,
    PHASE16_ARRIVAL_ACCURACY,
    PHASE16_ARRIVAL_CORRECT,
    PHASE16_ARRIVAL_TOTAL,
    PHASE16_MV_ACCURACY,
)
from questions_gpqa import QUESTIONS


def call_openrouter(question_text: str, run_idx: int) -> dict:
    """Make a single API call to OpenRouter."""
    import requests

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/DreamOS-Network/Arrival-Protocol",
        "X-Title": "ARRIVAL Phase 17 Solo CoT",
    }

    payload = {
        "model": OPENROUTER_MODEL_ID,
        "messages": [
            {"role": "system", "content": SOLO_COT_SYSTEM},
            {"role": "user", "content": question_text},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            cost = (
                usage.get("prompt_tokens", 0) * 0.0000003
                + usage.get("completion_tokens", 0) * 0.0000003
            )
            return {
                "content": content,
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "cost": cost,
            }
        except Exception as e:
            if attempt == 2:
                print(f"    ERROR run {run_idx}: {e}")
                return {"content": "", "tokens_prompt": 0, "tokens_completion": 0, "cost": 0}
            time.sleep(2 ** (attempt + 1))

    return {"content": "", "tokens_prompt": 0, "tokens_completion": 0, "cost": 0}


def extract_answer(text: str) -> str:
    """Extract answer letter from CoT response."""
    if not text:
        return ""
    # Primary: "The answer is X"
    m = re.search(r"[Tt]he answer is\s*[:\.]?\s*([A-D])", text)
    if m:
        return m.group(1)
    # Secondary: "Answer: X"
    m = re.search(r"[Aa]nswer\s*[:\.]?\s*([A-D])", text)
    if m:
        return m.group(1)
    # Tertiary: last standalone A-D
    lines = text.strip().split("\n")
    for line in reversed(lines):
        stripped = line.strip()
        if re.match(r"^[A-D]\.?\s*$", stripped):
            return stripped[0]
    # Final: any standalone letter in last 100 chars
    m = re.search(r"\b([A-D])\b", text[-100:])
    if m:
        return m.group(1)
    return ""


def format_question(q: dict) -> str:
    """Format a GPQA question for the prompt."""
    choices = q["choices"]
    text = f"{q['question']}\n\n"
    for letter in ["A", "B", "C", "D"]:
        text += f"{letter}. {choices[letter]}\n"
    return text


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


def main():
    assert OPENROUTER_API_KEY, (
        "OPENROUTER_API_KEY environment variable is required. "
        "See .env.example for configuration."
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)

    print("=" * 70)
    print("  ARRIVAL Protocol -- Phase 17: Solo CoT Baseline")
    print(f"  Model: {MODEL_SHORT} ({OPENROUTER_MODEL_ID})")
    print(f"  Questions: {len(QUESTIONS)} GPQA Diamond")
    print(f"  Runs per question: {N_RUNS_PER_QUESTION}")
    print(f"  Temperature: {TEMPERATURE}, Max tokens: {MAX_TOKENS}")
    print(f"  Budget limit: ${BUDGET_LIMIT:.2f}")
    print("=" * 70)

    total_cost = 0.0
    total_calls = 0
    all_results = []

    for qi, q in enumerate(QUESTIONS):
        print(f"\n  Q{qi+1}/{len(QUESTIONS)}: {q['id']} [{q['domain']}]")
        q_text = format_question(q)
        runs = []

        for run_idx in range(N_RUNS_PER_QUESTION):
            if total_cost >= BUDGET_LIMIT:
                print(f"  BUDGET EXCEEDED (${total_cost:.2f} >= ${BUDGET_LIMIT:.2f})")
                break

            resp = call_openrouter(q_text, run_idx)
            answer = extract_answer(resp["content"])
            correct = answer == q["correct"]
            total_cost += resp["cost"]
            total_calls += 1

            runs.append({
                "run_idx": run_idx,
                "answer": answer,
                "correct": correct,
                "tokens_prompt": resp["tokens_prompt"],
                "tokens_completion": resp["tokens_completion"],
                "cost": resp["cost"],
                "reasoning_length": len(resp["content"]),
            })

            marker = "+" if correct else "-"
            print(f"    Run {run_idx+1}: {answer} ({marker}) [${resp['cost']:.4f}]", end="")

            # Rate limit courtesy
            time.sleep(0.5)

        print()

        # Majority vote
        answers = [r["answer"] for r in runs if r["answer"]]
        if answers:
            mv_answer = Counter(answers).most_common(1)[0][0]
        else:
            mv_answer = ""
        mv_correct = mv_answer == q["correct"]

        # Best-of-N (oracle)
        oracle_correct = any(r["correct"] for r in runs)

        all_results.append({
            "question_id": q["id"],
            "domain": q["domain"],
            "correct_answer": q["correct"],
            "runs": runs,
            "majority_vote": {"answer": mv_answer, "correct": mv_correct},
            "oracle": {"correct": oracle_correct},
            "per_run_accuracy": sum(1 for r in runs if r["correct"]) / len(runs) if runs else 0,
        })

        if total_cost >= BUDGET_LIMIT:
            print(f"\n  BUDGET LIMIT REACHED: ${total_cost:.2f}")
            break

    # ---- Summary ----
    n_questions = len(all_results)
    solo_correct = sum(sum(1 for r in q["runs"] if r["correct"]) for q in all_results)
    solo_total = sum(len(q["runs"]) for q in all_results)
    mv_correct_count = sum(1 for q in all_results if q["majority_vote"]["correct"])
    oracle_correct_count = sum(1 for q in all_results if q["oracle"]["correct"])

    solo_acc = solo_correct / solo_total if solo_total else 0
    mv_acc = mv_correct_count / n_questions if n_questions else 0
    oracle_acc = oracle_correct_count / n_questions if n_questions else 0

    # Fisher's exact: Solo CoT MV vs ARRIVAL
    p17_correct = mv_correct_count
    p17_wrong = n_questions - mv_correct_count
    p16_correct = PHASE16_ARRIVAL_CORRECT
    p16_wrong = PHASE16_ARRIVAL_TOTAL - p16_correct
    fisher_p = fishers_exact_2x2(p17_correct, p17_wrong, p16_correct, p16_wrong)
    sig = "***" if fisher_p < 0.001 else "**" if fisher_p < 0.01 else "*" if fisher_p < 0.05 else "ns"

    # Fisher's: Solo CoT MV vs Phase 16 MV
    p16_mv_correct = round(PHASE16_MV_ACCURACY * PHASE16_ARRIVAL_TOTAL)
    p16_mv_wrong = PHASE16_ARRIVAL_TOTAL - p16_mv_correct
    fisher_mv_p = fishers_exact_2x2(p17_correct, p17_wrong, p16_mv_correct, p16_mv_wrong)
    sig_mv = "***" if fisher_mv_p < 0.001 else "**" if fisher_mv_p < 0.01 else "*" if fisher_mv_p < 0.05 else "ns"

    summary = {
        "phase": 17,
        "experiment": "Solo CoT Baseline",
        "model": OPENROUTER_MODEL_ID,
        "model_short": MODEL_SHORT,
        "n_questions": n_questions,
        "n_runs_per_question": N_RUNS_PER_QUESTION,
        "temperature": TEMPERATURE,
        "solo": {"accuracy": solo_acc, "correct": solo_correct, "total": solo_total},
        "majority_vote": {"accuracy": mv_acc, "correct": mv_correct_count, "total": n_questions},
        "oracle": {"accuracy": oracle_acc, "correct": oracle_correct_count, "total": n_questions},
        "comparison_with_phase16": {
            "phase16_arrival_accuracy": PHASE16_ARRIVAL_ACCURACY,
            "phase16_mv_accuracy": PHASE16_MV_ACCURACY,
            "solo_cot_mv_vs_arrival": {
                "fisher_p": fisher_p,
                "significance": sig,
                "delta_pp": (mv_acc - PHASE16_ARRIVAL_ACCURACY) * 100,
            },
            "solo_cot_mv_vs_phase16_mv": {
                "fisher_p": fisher_mv_p,
                "significance": sig_mv,
                "delta_pp": (mv_acc - PHASE16_MV_ACCURACY) * 100,
            },
        },
        "cost_usd": total_cost,
        "api_calls": total_calls,
        "timestamp": timestamp,
    }

    # Per-domain breakdown
    domains = {}
    for q in all_results:
        d = q["domain"]
        if d not in domains:
            domains[d] = {"correct": 0, "total": 0}
        domains[d]["total"] += 1
        if q["majority_vote"]["correct"]:
            domains[d]["correct"] += 1
    summary["per_domain"] = {
        d: {"accuracy": v["correct"] / v["total"], **v}
        for d, v in domains.items()
    }

    # Save results
    results_file = os.path.join(results_dir, f"phase17_results_{timestamp}.json")
    output = {"summary": summary, "questions": all_results}
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print report
    print(f"\n{'='*70}")
    print(f"  Phase 17: Solo CoT Baseline — Results")
    print(f"{'='*70}")
    print(f"  Solo per-run accuracy:   {solo_acc*100:.1f}% ({solo_correct}/{solo_total})")
    print(f"  Solo CoT Majority Vote:  {mv_acc*100:.1f}% ({mv_correct_count}/{n_questions})")
    print(f"  Solo CoT Oracle (best):  {oracle_acc*100:.1f}% ({oracle_correct_count}/{n_questions})")
    print(f"  ---")
    print(f"  Phase 16 MV baseline:    {PHASE16_MV_ACCURACY*100:.1f}%")
    print(f"  Phase 16 ARRIVAL:        {PHASE16_ARRIVAL_ACCURACY*100:.1f}%")
    print(f"  ---")
    print(f"  Solo CoT MV vs ARRIVAL:  {'%.1f' % ((mv_acc - PHASE16_ARRIVAL_ACCURACY)*100)} pp, Fisher p={fisher_p:.4f} {sig}")
    print(f"  Solo CoT MV vs P16 MV:   {'%.1f' % ((mv_acc - PHASE16_MV_ACCURACY)*100)} pp, Fisher p={fisher_mv_p:.4f} {sig_mv}")
    print(f"  ---")
    print(f"  Per domain:")
    for d, v in summary["per_domain"].items():
        print(f"    {d:20s} {v['accuracy']*100:.1f}% ({v['correct']}/{v['total']})")
    print(f"  ---")
    print(f"  Cost: ${total_cost:.2f}, API calls: {total_calls}")
    print(f"  Results: {results_file}")
    print(f"{'='*70}")

    return output


if __name__ == "__main__":
    main()
