# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 21: ARRIVAL Protocol with Strong Heterogeneous Trio on Full GPQA Diamond (198 questions)

Strong frontier models from 3 different vendors:
- R1/R4: GPT-4.1 (OpenAI)
- R2: Gemini 3 Flash Preview (Google)
- R3: Grok 4.1 Fast (xAI)

Same sequential 4-round protocol as Phase 20:
R1 (propose) -> R2 (critique) -> R3 (synthesize) -> R4 (finalize)

Key difference from Phase 20: much stronger models should yield larger debate effect.
Records BOTH MV(R1-R3) AND R4 answer for each question.

Usage:
    set OPENROUTER_API_KEY=sk-or-v1-...
    python run_arrival.py              # Full run (198 questions)
    python run_arrival.py --test 5     # Pipeline test (5 questions)
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

# Add src to path for CRDT metrics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from arrival.metrics import extract_answer_letter, find_all_atoms, detect_emergent_atoms
from arrival.crdt_metrics import compute_care_resolve, compute_meaning_debt

# ============================================================
# Configuration
# ============================================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Phase 21: STRONG heterogeneous trio (3 different vendors)
TRIO = [
    "openai/gpt-4.1",                  # R1 (Proposer) + R4 (Finalizer)
    "google/gemini-3-flash-preview",    # R2 (Critic)
    "x-ai/grok-4.1-fast",              # R3 (Synthesizer)
]
TRIO_SHORT = ["GPT-4.1", "Gemini3Flash", "Grok4.1"]
NODE_NAMES = ["Alpha", "Beta", "Gamma"]

# Model costs per 1M tokens (approximate from OpenRouter)
MODEL_COSTS = {
    "openai/gpt-4.1":                  {"input": 2.00, "output": 8.00},
    "google/gemini-3-flash-preview":    {"input": 0.50, "output": 3.00},
    "x-ai/grok-4.1-fast":              {"input": 0.60, "output": 2.40},
}

TEMPERATURE = 0.3
MAX_TOKENS = 2048  # Increased from 1024 to prevent extraction failures
BUDGET_LIMIT = 20.0  # USD safety cap
SLEEP_BETWEEN_CALLS = 2  # seconds

# Truncation limits for context passing (same as Phase 13/20)
R2_CONTEXT_LIMIT = 1500
R3_CONTEXT_LIMIT = 1200
R4_CONTEXT_LIMIT = 800

# ============================================================
# System prompts (EXACT Phase 13/20 replication)
# ============================================================
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

ROUND_PROMPTS = {
    1: """You are Node {node_name} ({model_short}).
Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Analyze this question using DEUS protocol atoms. State your reasoning and initial answer.
Use @SELF to identify, @GOAL for the task, @INT for your reasoning, @C[value] for confidence.""",

    2: """You are Node {node_name} ({model_short}).
The previous node analyzed this question:

{previous_response}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Review their analysis. Do you agree or disagree? Use @CONSENSUS or @CONFLICT atoms.
If you agree, reinforce the reasoning. If you disagree, explain why with @INT.
State your answer clearly. Use @C[value] for your confidence level.""",

    3: """You are Node {node_name} ({model_short}).
Two nodes have analyzed this question:

Node 1: {response_1}

Node 2: {response_2}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Synthesize both perspectives. Identify agreements and conflicts.
Propose the final answer with @RESOLUTION. Use @CONSENSUS[answer=X] for your verdict.
Include @C[value] for confidence.""",

    4: """You are Node {node_name} ({model_short}).
Three analyses have been provided:

Node 1: {response_1}
Node 2: {response_2}
Node 3: {response_3}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

This is the final round. State the group's consensus answer.
Use @CONSENSUS[answer=X] where X is A, B, C, or D.
If there's no clear consensus, choose the best-supported answer and explain.
Include @C[value] for final confidence.""",
}

# ============================================================
# Load questions (reuse Phase 20 data)
# ============================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase20_gpqa_full", "data")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load_questions():
    """Load GPQA Diamond 198 questions from Phase 20 data."""
    path = os.path.join(DATA_DIR, "gpqa_diamond_198.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# API call
# ============================================================
def call_openrouter(prompt: str, model: str, system_prompt: str) -> dict:
    """Make a single API call to OpenRouter."""
    import requests

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Methodiy-Kelevra/ARRIVAL",
        "X-Title": "ARRIVAL Phase 21",
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
            start_time = time.time()
            resp = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=180,  # Increased timeout for frontier models
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

            # Cost calculation
            pricing = MODEL_COSTS.get(model, {"input": 2.0, "output": 8.0})
            cost = (
                usage.get("prompt_tokens", 0) * pricing["input"] / 1_000_000
                + usage.get("completion_tokens", 0) * pricing["output"] / 1_000_000
            )

            model_version = data.get("model", model)

            # Save tail snippet for extraction debugging
            tail_snippet = content[-200:] if content else ""

            return {
                "content": content,
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "cost": cost,
                "latency_ms": round(latency_ms, 1),
                "model_version": model_version,
                "tail_snippet": tail_snippet,
            }
        except Exception as e:
            if attempt == 2:
                print(f"      ERROR: {e}")
                return {
                    "content": "", "tokens_prompt": 0, "tokens_completion": 0,
                    "cost": 0, "latency_ms": 0, "model_version": model,
                    "tail_snippet": "",
                }
            time.sleep(2 ** (attempt + 1))

    return {
        "content": "", "tokens_prompt": 0, "tokens_completion": 0,
        "cost": 0, "latency_ms": 0, "model_version": model,
        "tail_snippet": "",
    }


# ============================================================
# Run one question through ARRIVAL protocol
# ============================================================
def run_arrival_question(q: dict, total_cost: float) -> dict:
    """Run 4-round ARRIVAL protocol on a single question."""
    choice_vars = {
        "choice_a": q["choices"]["A"],
        "choice_b": q["choices"]["B"],
        "choice_c": q["choices"]["C"],
        "choice_d": q["choices"]["D"],
        "question": q["question"],
    }

    dialogue = []
    responses = {}
    q_cost = 0.0
    q_tokens = 0
    all_atoms = []
    emergent = set()
    model_versions = {}
    tail_snippets = {}

    # ---- Round 1: GPT-4.1 proposes ----
    model_a = TRIO[0]
    prompt_1 = ROUND_PROMPTS[1].format(
        node_name=NODE_NAMES[0], model_short=TRIO_SHORT[0], **choice_vars
    )
    resp_1 = call_openrouter(prompt_1, model_a, ARRIVAL_SYSTEM)
    responses["r1"] = resp_1["content"]
    q_cost += resp_1["cost"]
    q_tokens += resp_1["tokens_prompt"] + resp_1["tokens_completion"]
    model_versions["r1"] = resp_1["model_version"]
    tail_snippets["r1"] = resp_1["tail_snippet"]
    dialogue.append({"round": 1, "from": TRIO_SHORT[0], "message": resp_1["content"]})
    all_atoms.extend(find_all_atoms(resp_1["content"]))
    emergent.update(detect_emergent_atoms(resp_1["content"]))
    r1_answer = extract_answer_letter(resp_1["content"])
    print(f" R1:{r1_answer or '?'}", end="", flush=True)
    time.sleep(SLEEP_BETWEEN_CALLS)

    if total_cost + q_cost >= BUDGET_LIMIT:
        return _make_partial_result(q, dialogue, responses, q_cost, q_tokens, model_versions, all_atoms, emergent, tail_snippets)

    # ---- Round 2: Gemini 3 Flash critiques ----
    model_b = TRIO[1]
    prompt_2 = ROUND_PROMPTS[2].format(
        node_name=NODE_NAMES[1], model_short=TRIO_SHORT[1],
        previous_response=resp_1["content"][:R2_CONTEXT_LIMIT],
        **choice_vars
    )
    resp_2 = call_openrouter(prompt_2, model_b, ARRIVAL_SYSTEM)
    responses["r2"] = resp_2["content"]
    q_cost += resp_2["cost"]
    q_tokens += resp_2["tokens_prompt"] + resp_2["tokens_completion"]
    model_versions["r2"] = resp_2["model_version"]
    tail_snippets["r2"] = resp_2["tail_snippet"]
    dialogue.append({"round": 2, "from": TRIO_SHORT[1], "message": resp_2["content"]})
    all_atoms.extend(find_all_atoms(resp_2["content"]))
    emergent.update(detect_emergent_atoms(resp_2["content"]))
    r2_answer = extract_answer_letter(resp_2["content"])
    print(f" R2:{r2_answer or '?'}", end="", flush=True)
    time.sleep(SLEEP_BETWEEN_CALLS)

    if total_cost + q_cost >= BUDGET_LIMIT:
        return _make_partial_result(q, dialogue, responses, q_cost, q_tokens, model_versions, all_atoms, emergent, tail_snippets)

    # ---- Round 3: Grok 4.1 synthesizes ----
    model_c = TRIO[2]
    prompt_3 = ROUND_PROMPTS[3].format(
        node_name=NODE_NAMES[2], model_short=TRIO_SHORT[2],
        response_1=resp_1["content"][:R3_CONTEXT_LIMIT],
        response_2=resp_2["content"][:R3_CONTEXT_LIMIT],
        **choice_vars
    )
    resp_3 = call_openrouter(prompt_3, model_c, ARRIVAL_SYSTEM)
    responses["r3"] = resp_3["content"]
    q_cost += resp_3["cost"]
    q_tokens += resp_3["tokens_prompt"] + resp_3["tokens_completion"]
    model_versions["r3"] = resp_3["model_version"]
    tail_snippets["r3"] = resp_3["tail_snippet"]
    dialogue.append({"round": 3, "from": TRIO_SHORT[2], "message": resp_3["content"]})
    all_atoms.extend(find_all_atoms(resp_3["content"]))
    emergent.update(detect_emergent_atoms(resp_3["content"]))
    r3_answer = extract_answer_letter(resp_3["content"])
    print(f" R3:{r3_answer or '?'}", end="", flush=True)
    time.sleep(SLEEP_BETWEEN_CALLS)

    if total_cost + q_cost >= BUDGET_LIMIT:
        return _make_partial_result(q, dialogue, responses, q_cost, q_tokens, model_versions, all_atoms, emergent, tail_snippets)

    # ---- Round 4: GPT-4.1 finalizes ----
    prompt_4 = ROUND_PROMPTS[4].format(
        node_name=NODE_NAMES[0], model_short=TRIO_SHORT[0],
        response_1=resp_1["content"][:R4_CONTEXT_LIMIT],
        response_2=resp_2["content"][:R4_CONTEXT_LIMIT],
        response_3=resp_3["content"][:R4_CONTEXT_LIMIT],
        **choice_vars
    )
    resp_4 = call_openrouter(prompt_4, model_a, ARRIVAL_SYSTEM)
    responses["r4"] = resp_4["content"]
    q_cost += resp_4["cost"]
    q_tokens += resp_4["tokens_prompt"] + resp_4["tokens_completion"]
    model_versions["r4"] = resp_4["model_version"]
    tail_snippets["r4"] = resp_4["tail_snippet"]
    dialogue.append({"round": 4, "from": TRIO_SHORT[0], "message": resp_4["content"]})
    all_atoms.extend(find_all_atoms(resp_4["content"]))
    emergent.update(detect_emergent_atoms(resp_4["content"]))

    # ---- Extract answers ----
    r4_answer = extract_answer_letter(responses["r4"])
    if not r4_answer:
        # Fallback: try earlier rounds
        for r_key in ["r3", "r2", "r1"]:
            r4_answer = extract_answer_letter(responses[r_key])
            if r4_answer:
                break

    # Individual answers from R1-R3
    r1_ans = extract_answer_letter(responses.get("r1", ""))
    r2_ans = extract_answer_letter(responses.get("r2", ""))
    r3_ans = extract_answer_letter(responses.get("r3", ""))

    # Majority Vote of R1-R3 (PRIMARY metric for Phase 21)
    indiv_answers = [a for a in [r1_ans, r2_ans, r3_ans] if a]
    if indiv_answers:
        mv_answer = Counter(indiv_answers).most_common(1)[0][0]
    else:
        mv_answer = None

    # ---- CRDT Overlay (zero API cost) ----
    care_result = compute_care_resolve(dialogue, task_type="mcq")
    debt_result = compute_meaning_debt(dialogue, task_type="mcq")

    atom_counts = Counter(all_atoms)

    print(f" R4:{r4_answer or '?'}", end="", flush=True)

    return {
        "question_id": q["id"],
        "domain": q["domain"],
        "subdomain": q.get("subdomain", ""),
        "correct_answer": q["correct"],
        "correct_answer_text": q["choices"].get(q["correct"], ""),
        "r1_answer": r1_ans,
        "r1_answer_text": q["choices"].get(r1_ans, "") if r1_ans else "",
        "r1_model": TRIO[0],
        "r2_answer": r2_ans,
        "r2_answer_text": q["choices"].get(r2_ans, "") if r2_ans else "",
        "r2_model": TRIO[1],
        "r3_answer": r3_ans,
        "r3_answer_text": q["choices"].get(r3_ans, "") if r3_ans else "",
        "r3_model": TRIO[2],
        "r4_final": r4_answer,
        "r4_final_text": q["choices"].get(r4_answer, "") if r4_answer else "",
        "r4_model": TRIO[0],
        "majority_vote_r1r2r3": mv_answer,
        "mv_answer_text": q["choices"].get(mv_answer, "") if mv_answer else "",
        "correct_arrival": r4_answer == q["correct"] if r4_answer else False,
        "correct_mv": mv_answer == q["correct"] if mv_answer else False,
        "care_resolve": care_result.get("care_resolve"),
        "meaning_debt": debt_result.get("total_meaning_debt", 0),
        "health": debt_result.get("health_assessment", "?"),
        "crdt": {
            "care_resolve_full": care_result,
            "meaning_debt_full": debt_result,
        },
        "atoms_used": dict(atom_counts),
        "unique_atoms": len(atom_counts),
        "emergent_atoms": sorted(emergent),
        "cost_usd": q_cost,
        "total_tokens": q_tokens,
        "model_versions": model_versions,
        "tail_snippets": tail_snippets,
        "dialogue": dialogue,
    }


def _make_partial_result(q, dialogue, responses, q_cost, q_tokens, model_versions, all_atoms, emergent, tail_snippets):
    """Make a partial result when budget is hit mid-question."""
    r4_answer = None
    for r_key in ["r4", "r3", "r2", "r1"]:
        if r_key in responses:
            r4_answer = extract_answer_letter(responses[r_key])
            if r4_answer:
                break
    atom_counts = Counter(all_atoms)
    return {
        "question_id": q["id"],
        "domain": q["domain"],
        "subdomain": q.get("subdomain", ""),
        "correct_answer": q["correct"],
        "correct_answer_text": q["choices"].get(q["correct"], ""),
        "r4_final": r4_answer,
        "r4_final_text": q["choices"].get(r4_answer, "") if r4_answer else "",
        "correct_arrival": r4_answer == q["correct"] if r4_answer else False,
        "correct_mv": False,
        "majority_vote_r1r2r3": None,
        "care_resolve": None,
        "meaning_debt": 0,
        "health": "partial",
        "crdt": {},
        "atoms_used": dict(atom_counts),
        "unique_atoms": len(atom_counts),
        "emergent_atoms": sorted(emergent),
        "cost_usd": q_cost,
        "total_tokens": q_tokens,
        "model_versions": model_versions,
        "tail_snippets": tail_snippets,
        "dialogue": dialogue,
        "partial": True,
    }


# ============================================================
# Main experiment
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 21: ARRIVAL Strong Trio (GPQA Diamond)")
    parser.add_argument("--test", type=int, default=None, help="Number of questions for pipeline test")
    args = parser.parse_args()

    assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY environment variable is required."

    questions = load_questions()
    if args.test:
        questions = questions[:args.test]
        print(f"\n  *** PIPELINE TEST MODE: {args.test} questions ***\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Check for existing results to resume from
    results_file = os.path.join(RESULTS_DIR, "arrival_results.json")
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
    print("  ARRIVAL Protocol -- Phase 21: Strong Heterogeneous Trio")
    print(f"  Trio: {' + '.join(TRIO_SHORT)}")
    print(f"  Models: {', '.join(TRIO)}")
    print(f"  Questions: {n_total} GPQA Diamond (reusing Phase 20 data)")
    print(f"  Remaining: {n_remaining}")
    print(f"  Temperature: {TEMPERATURE}, Max tokens: {MAX_TOKENS}")
    print(f"  Budget limit: ${BUDGET_LIMIT:.2f}")
    print("=" * 70)

    # ETA estimation
    est_seconds_per_q = 4 * (8 + SLEEP_BETWEEN_CALLS)  # ~8s per API call + sleep
    est_total_seconds = n_remaining * est_seconds_per_q
    est_finish = datetime.now() + timedelta(seconds=est_total_seconds)
    print(f"  Estimated time: ~{est_total_seconds/60:.0f} minutes")
    print(f"  ETA: {est_finish.strftime('%H:%M:%S')}")
    print()

    total_cost = sum(r.get("cost_usd", 0) for r in existing_results)
    total_calls = sum(4 for r in existing_results if not r.get("partial"))
    all_results = list(existing_results)
    start_time = time.time()
    questions_done_this_session = 0
    extraction_failures = 0

    for qi, q in enumerate(questions):
        if q["id"] in done_ids:
            continue

        if total_cost >= BUDGET_LIMIT:
            print(f"\n  BUDGET LIMIT REACHED: ${total_cost:.2f}")
            break

        print(f"  Q{qi+1}/{n_total}: {q['id']} [{q['domain']}]", end="", flush=True)

        result = run_arrival_question(q, total_cost)
        total_cost += result["cost_usd"]
        total_calls += 4
        all_results.append(result)
        questions_done_this_session += 1

        # Check extraction quality
        if not result.get("r1_answer") or not result.get("r2_answer") or not result.get("r3_answer"):
            extraction_failures += 1
        if not result.get("r4_final"):
            extraction_failures += 1

        # Extraction failure rate check
        if questions_done_this_session >= 5:
            failure_rate = extraction_failures / (questions_done_this_session * 4)
            if failure_rate > 0.05:
                print(f"\n  WARNING: Extraction failure rate {failure_rate:.1%} > 5%!")
                if args.test:
                    print("  STOPPING: Fix extraction before full run!")
                    break

        # Progress
        ar_sym = "+" if result["correct_arrival"] else "-"
        mv_sym = "+" if result["correct_mv"] else "-"
        care_str = f"{result['care_resolve']:.2f}" if result['care_resolve'] is not None else "N/A"
        elapsed = time.time() - start_time
        avg_time = elapsed / questions_done_this_session
        remaining_q = n_remaining - questions_done_this_session
        eta_seconds = remaining_q * avg_time
        eta_str = str(timedelta(seconds=int(eta_seconds)))
        print(f" AR:{ar_sym} MV:{mv_sym} CARE:{care_str} ${total_cost:.2f} ETA:{eta_str}")

        # Save after EACH question (crash protection)
        _save_results(results_file, all_results, total_cost, total_calls, timestamp)

    # ---- Final Summary ----
    _print_summary(all_results, total_cost, total_calls)
    print(f"\n  Results saved: {results_file}")
    print(f"  Total time: {timedelta(seconds=int(time.time() - start_time))}")


def _save_results(filepath, all_results, total_cost, total_calls, timestamp):
    """Save results to JSON (crash protection via atomic write)."""
    n_q = len(all_results)
    ar_correct = sum(1 for r in all_results if r.get("correct_arrival"))
    mv_correct = sum(1 for r in all_results if r.get("correct_mv"))
    ar_acc = ar_correct / n_q if n_q else 0
    mv_acc = mv_correct / n_q if n_q else 0

    care_scores = [r["care_resolve"] for r in all_results if r.get("care_resolve") is not None]
    avg_care = sum(care_scores) / len(care_scores) if care_scores else None

    # Per-domain breakdown
    domains = {}
    for r in all_results:
        d = r["domain"]
        if d not in domains:
            domains[d] = {"ar_correct": 0, "mv_correct": 0, "total": 0}
        domains[d]["total"] += 1
        if r.get("correct_arrival"):
            domains[d]["ar_correct"] += 1
        if r.get("correct_mv"):
            domains[d]["mv_correct"] += 1

    output = {
        "summary": {
            "phase": "Phase 21: ARRIVAL Strong Trio",
            "timestamp": timestamp,
            "n_questions": n_q,
            "arrival_r4_correct": ar_correct,
            "arrival_r4_accuracy": round(ar_acc, 4),
            "arrival_mv_correct": mv_correct,
            "arrival_mv_accuracy": round(mv_acc, 4),
            "avg_care_resolve": round(avg_care, 4) if avg_care else None,
            "total_cost_usd": round(total_cost, 4),
            "total_api_calls": total_calls,
            "models": TRIO,
            "models_short": TRIO_SHORT,
            "per_domain": {
                d: {
                    "ar_accuracy": round(v["ar_correct"] / v["total"], 4) if v["total"] else 0,
                    "mv_accuracy": round(v["mv_correct"] / v["total"], 4) if v["total"] else 0,
                    "total": v["total"],
                }
                for d, v in domains.items()
            },
        },
        "questions": all_results,
    }

    # Atomic write (crash protection)
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, filepath)


def _print_summary(all_results, total_cost, total_calls):
    """Print final experiment summary."""
    n = len(all_results)
    if n == 0:
        print("  No results to summarize.")
        return

    ar_c = sum(1 for r in all_results if r.get("correct_arrival"))
    mv_c = sum(1 for r in all_results if r.get("correct_mv"))

    # Per-model accuracy
    r1_c = sum(1 for r in all_results if r.get("r1_answer") == r["correct_answer"])
    r2_c = sum(1 for r in all_results if r.get("r2_answer") == r["correct_answer"])
    r3_c = sum(1 for r in all_results if r.get("r3_answer") == r["correct_answer"])

    # R4 rescue/regression vs MV
    rescues = sum(1 for r in all_results if r.get("correct_arrival") and not r.get("correct_mv"))
    regressions = sum(1 for r in all_results if not r.get("correct_arrival") and r.get("correct_mv"))

    print()
    print("=" * 70)
    print("  PHASE 21 FINAL SUMMARY")
    print("=" * 70)
    print(f"  ARRIVAL R4:  {ar_c}/{n} = {ar_c/n:.1%}")
    print(f"  ARRIVAL MV:  {mv_c}/{n} = {mv_c/n:.1%}")
    print(f"  Per-model: R1(GPT-4.1)={r1_c}/{n}={r1_c/n:.1%}, R2(Gemini3Flash)={r2_c}/{n}={r2_c/n:.1%}, R3(Grok4.1)={r3_c}/{n}={r3_c/n:.1%}")
    print(f"  R4 Rescues: {rescues}, Regressions: {regressions}, Net: {rescues - regressions}")
    print(f"  Cost: ${total_cost:.2f}, API calls: {total_calls}")
    print("=" * 70)


if __name__ == "__main__":
    main()
