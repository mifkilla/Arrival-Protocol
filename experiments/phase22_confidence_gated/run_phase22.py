# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 22: Confidence-Gated Debate + Strongest-First Variant (20 questions)

Two conditions tested on the HARDEST 20 questions from Phase 21:

Condition A: "Confidence-Gated Debate" (CGD)
  1. All 3 models answer INDEPENDENTLY (like solo baseline)
  2. If all 3 agree → answer locked (no debate needed)
  3. If 2-1 split → 1 debate round: minority model argues against majority
  4. If 3-way split → full 3-round ARRIVAL debate
  5. NO R4 — use MV after debate

Condition B: "Strongest-First" (SF)
  - Grok → R1 (strongest, 85.4% solo, sets correct anchor)
  - Gemini → R2 (second, 82.3%, critiques strong proposal)
  - GPT-4.1 → R3 (weakest, 66.2%, last — can't anchor others)
  - R4 = Grok (strongest model finalizes)
  Standard 4-round ARRIVAL protocol but with reordered models.

Question selection: 20 questions where Phase 21 ARRIVAL MV was WRONG but
Non-Debate MV was RIGHT (the debate-loss questions), plus any remaining
from questions where both were wrong.

Usage:
    set OPENROUTER_API_KEY=sk-or-v1-...
    python run_phase22.py              # Full run (20 questions, both conditions)
    python run_phase22.py --test 3     # Pipeline test (3 questions)
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

# Same strong trio as Phase 21
MODELS = {
    "gpt": {"id": "openai/gpt-4.1", "short": "GPT-4.1", "cost_input": 2.00, "cost_output": 8.00},
    "gemini": {"id": "google/gemini-3-flash-preview", "short": "Gemini3Flash", "cost_input": 0.50, "cost_output": 3.00},
    "grok": {"id": "x-ai/grok-4.1-fast", "short": "Grok4.1", "cost_input": 0.60, "cost_output": 2.40},
}

MODEL_COSTS = {m["id"]: {"input": m["cost_input"], "output": m["cost_output"]} for m in MODELS.values()}

TEMPERATURE = 0.3
MAX_TOKENS = 2048
BUDGET_LIMIT = 5.0
SLEEP_BETWEEN_CALLS = 2
N_QUESTIONS = 20

# Context truncation limits
R2_CONTEXT_LIMIT = 1500
R3_CONTEXT_LIMIT = 1200
R4_CONTEXT_LIMIT = 800

# ============================================================
# Prompts
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

# Phase 21-style round prompts for Strongest-First
SF_ROUND_PROMPTS = {
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
# Load questions
# ============================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase20_gpqa_full", "data")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load_questions():
    path = os.path.join(DATA_DIR, "gpqa_diamond_198.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def select_questions(all_questions, n=N_QUESTIONS):
    """Select N hardest questions: prioritize debate-loss (ARRIVAL wrong, ND right),
    then both-wrong, then random."""
    # Load Phase 21 results to find debate-loss questions
    p21_arrival = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "phase21_gpqa_strong", "results", "arrival_results.json")
    p21_nd = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "phase21_gpqa_strong", "results", "non_debate_mv.json")

    with open(p21_arrival, "r", encoding="utf-8") as f:
        arrival_data = json.load(f)
    with open(p21_nd, "r", encoding="utf-8") as f:
        nd_data = json.load(f)

    # Build lookup
    arrival_by_id = {q["question_id"]: q for q in arrival_data["questions"]}
    nd_by_id = {q["question_id"]: q for q in nd_data["questions"]}

    debate_loss = []  # ARRIVAL MV wrong, ND MV right
    both_wrong = []   # Both wrong
    debate_win = []   # ARRIVAL MV right, ND MV wrong

    for q in all_questions:
        qid = q["id"]
        ar = arrival_by_id.get(qid, {})
        nd = nd_by_id.get(qid, {})
        ar_correct = ar.get("correct_mv", False)
        nd_correct = nd.get("correct", False)

        if not ar_correct and nd_correct:
            debate_loss.append(q)
        elif not ar_correct and not nd_correct:
            both_wrong.append(q)
        elif ar_correct and not nd_correct:
            debate_win.append(q)

    print(f"  Question selection:")
    print(f"    Debate-loss (AR wrong, ND right): {len(debate_loss)}")
    print(f"    Both-wrong: {len(both_wrong)}")
    print(f"    Debate-win (AR right, ND wrong): {len(debate_win)}")

    # Priority: debate-loss first, then both-wrong, then debate-win
    selected = []
    selected.extend(debate_loss[:n])
    if len(selected) < n:
        selected.extend(both_wrong[:n - len(selected)])
    if len(selected) < n:
        selected.extend(debate_win[:n - len(selected)])

    print(f"    Selected: {len(selected)} questions")
    print(f"    Composition: {sum(1 for q in selected if q in debate_loss)} debate-loss, "
          f"{sum(1 for q in selected if q in both_wrong)} both-wrong, "
          f"{sum(1 for q in selected if q in debate_win)} debate-win")

    return selected[:n]


# ============================================================
# API call (same as Phase 21)
# ============================================================
def call_openrouter(prompt: str, model: str, system_prompt: str) -> dict:
    import requests

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/mifkilla/Arrival-Protocol",
        "X-Title": "ARRIVAL Phase 22",
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
# Condition A: Confidence-Gated Debate (CGD)
# ============================================================
def run_cgd_question(q: dict, total_cost: float) -> dict:
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
    dialogue = []

    # ---- Step 1: All 3 models answer independently ----
    solo_answers = {}
    solo_responses = {}
    model_order = ["grok", "gemini", "gpt"]  # Strongest first for logging

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
        dialogue.append({"round": "solo", "from": m["short"], "message": resp["content"]})
        print(f" {m['short']}:{answer or '?'}", end="", flush=True)
        time.sleep(SLEEP_BETWEEN_CALLS)

    # ---- Step 2: Check agreement ----
    valid_answers = {k: v for k, v in solo_answers.items() if v is not None}
    answer_counts = Counter(valid_answers.values())

    if len(answer_counts) == 0:
        # All None — give up
        final_answer = None
        debate_type = "all_none"
        print(f" [ALL_NONE]", end="", flush=True)

    elif len(answer_counts) == 1 or (answer_counts.most_common(1)[0][1] >= 2 and len(valid_answers) >= 2):
        # Unanimous or 2-1 majority — check if we need debate
        majority_answer = answer_counts.most_common(1)[0][0]
        majority_count = answer_counts.most_common(1)[0][1]

        if majority_count == len(valid_answers):
            # UNANIMOUS — lock answer, no debate
            final_answer = majority_answer
            debate_type = "unanimous"
            print(f" [UNANIMOUS={final_answer}]", end="", flush=True)
        else:
            # 2-1 SPLIT — debate round for minority
            debate_type = "split_2v1"
            minority_models = [k for k, v in valid_answers.items() if v != majority_answer]
            majority_models = [k for k, v in valid_answers.items() if v == majority_answer]

            # Build majority reasoning summary
            majority_reasoning = "\n\n".join([
                f"{MODELS[mk]['short']}: {solo_responses[mk][:800]}"
                for mk in majority_models
            ])

            # Minority model gets to argue
            debate_answers = dict(valid_answers)  # Start with solo answers
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
                dialogue.append({"round": "debate", "from": m["short"], "message": resp["content"]})
                print(f" D:{m['short']}:{new_answer or '?'}", end="", flush=True)
                time.sleep(SLEEP_BETWEEN_CALLS)

            # Final MV after debate
            post_debate = [v for v in debate_answers.values() if v]
            final_answer = Counter(post_debate).most_common(1)[0][0] if post_debate else None
            print(f" [2v1→{final_answer}]", end="", flush=True)
    else:
        # 3-WAY SPLIT — full debate
        debate_type = "split_3way"
        # All 3 models see each other's responses and reconsider
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
            dialogue.append({"round": "debate_3way", "from": m["short"], "message": resp["content"]})
            print(f" D3:{m['short']}:{new_answer or '?'}", end="", flush=True)
            time.sleep(SLEEP_BETWEEN_CALLS)

        post_debate = [v for v in debate_answers.values() if v]
        final_answer = Counter(post_debate).most_common(1)[0][0] if post_debate else None
        print(f" [3way→{final_answer}]", end="", flush=True)

    # CRDT
    care_result = compute_care_resolve(dialogue, task_type="mcq")
    debt_result = compute_meaning_debt(dialogue, task_type="mcq")

    return {
        "question_id": q["id"],
        "domain": q["domain"],
        "correct_answer": q["correct"],
        "condition": "CGD",
        "debate_type": debate_type,
        "solo_grok": solo_answers.get("grok"),
        "solo_gemini": solo_answers.get("gemini"),
        "solo_gpt": solo_answers.get("gpt"),
        "final_answer": final_answer,
        "correct": final_answer == q["correct"] if final_answer else False,
        "care_resolve": care_result.get("care_resolve"),
        "meaning_debt": debt_result.get("total_meaning_debt", 0),
        "cost_usd": q_cost,
        "total_tokens": q_tokens,
        "api_calls": api_calls,
        "dialogue": dialogue,
    }


# ============================================================
# Condition B: Strongest-First (SF)
# ============================================================
def run_sf_question(q: dict, total_cost: float) -> dict:
    """Strongest-First: Grok R1, Gemini R2, GPT R3, R4=Grok."""
    choice_vars = {
        "choice_a": q["choices"]["A"],
        "choice_b": q["choices"]["B"],
        "choice_c": q["choices"]["C"],
        "choice_d": q["choices"]["D"],
        "question": q["question"],
    }

    # Reordered: Grok first, Gemini second, GPT last
    sf_trio = [MODELS["grok"]["id"], MODELS["gemini"]["id"], MODELS["gpt"]["id"]]
    sf_short = [MODELS["grok"]["short"], MODELS["gemini"]["short"], MODELS["gpt"]["short"]]
    sf_names = ["Alpha", "Beta", "Gamma"]
    r4_model = MODELS["grok"]["id"]  # Strongest as finalizer
    r4_short = MODELS["grok"]["short"]

    responses = {}
    q_cost = 0.0
    q_tokens = 0
    dialogue = []

    # Round 1: Grok proposes
    prompt_1 = SF_ROUND_PROMPTS[1].format(node_name=sf_names[0], model_short=sf_short[0], **choice_vars)
    resp_1 = call_openrouter(prompt_1, sf_trio[0], ARRIVAL_SYSTEM)
    responses["r1"] = resp_1["content"]
    q_cost += resp_1["cost"]
    q_tokens += resp_1["tokens_prompt"] + resp_1["tokens_completion"]
    dialogue.append({"round": 1, "from": sf_short[0], "message": resp_1["content"]})
    r1_answer = extract_answer_letter(resp_1["content"])
    print(f" R1:{r1_answer or '?'}", end="", flush=True)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 2: Gemini critiques
    prompt_2 = SF_ROUND_PROMPTS[2].format(
        node_name=sf_names[1], model_short=sf_short[1],
        previous_response=resp_1["content"][:R2_CONTEXT_LIMIT], **choice_vars)
    resp_2 = call_openrouter(prompt_2, sf_trio[1], ARRIVAL_SYSTEM)
    responses["r2"] = resp_2["content"]
    q_cost += resp_2["cost"]
    q_tokens += resp_2["tokens_prompt"] + resp_2["tokens_completion"]
    dialogue.append({"round": 2, "from": sf_short[1], "message": resp_2["content"]})
    r2_answer = extract_answer_letter(resp_2["content"])
    print(f" R2:{r2_answer or '?'}", end="", flush=True)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 3: GPT synthesizes
    prompt_3 = SF_ROUND_PROMPTS[3].format(
        node_name=sf_names[2], model_short=sf_short[2],
        response_1=resp_1["content"][:R3_CONTEXT_LIMIT],
        response_2=resp_2["content"][:R3_CONTEXT_LIMIT], **choice_vars)
    resp_3 = call_openrouter(prompt_3, sf_trio[2], ARRIVAL_SYSTEM)
    responses["r3"] = resp_3["content"]
    q_cost += resp_3["cost"]
    q_tokens += resp_3["tokens_prompt"] + resp_3["tokens_completion"]
    dialogue.append({"round": 3, "from": sf_short[2], "message": resp_3["content"]})
    r3_answer = extract_answer_letter(resp_3["content"])
    print(f" R3:{r3_answer or '?'}", end="", flush=True)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 4: Grok finalizes
    prompt_4 = SF_ROUND_PROMPTS[4].format(
        node_name=sf_names[0], model_short=sf_short[0],
        response_1=resp_1["content"][:R4_CONTEXT_LIMIT],
        response_2=resp_2["content"][:R4_CONTEXT_LIMIT],
        response_3=resp_3["content"][:R4_CONTEXT_LIMIT], **choice_vars)
    resp_4 = call_openrouter(prompt_4, r4_model, ARRIVAL_SYSTEM)
    responses["r4"] = resp_4["content"]
    q_cost += resp_4["cost"]
    q_tokens += resp_4["tokens_prompt"] + resp_4["tokens_completion"]
    dialogue.append({"round": 4, "from": r4_short, "message": resp_4["content"]})

    # Extract answers
    r4_answer = extract_answer_letter(responses["r4"])
    if not r4_answer:
        for rk in ["r3", "r2", "r1"]:
            r4_answer = extract_answer_letter(responses[rk])
            if r4_answer:
                break

    indiv = [r1_answer, r2_answer, r3_answer]
    indiv_valid = [a for a in indiv if a]
    mv_answer = Counter(indiv_valid).most_common(1)[0][0] if indiv_valid else None

    # CRDT
    care_result = compute_care_resolve(dialogue, task_type="mcq")
    debt_result = compute_meaning_debt(dialogue, task_type="mcq")

    print(f" R4:{r4_answer or '?'} MV:{mv_answer or '?'}", end="", flush=True)

    return {
        "question_id": q["id"],
        "domain": q["domain"],
        "correct_answer": q["correct"],
        "condition": "SF",
        "r1_answer": r1_answer, "r1_model": sf_trio[0],
        "r2_answer": r2_answer, "r2_model": sf_trio[1],
        "r3_answer": r3_answer, "r3_model": sf_trio[2],
        "r4_final": r4_answer, "r4_model": r4_model,
        "majority_vote": mv_answer,
        "correct_r4": r4_answer == q["correct"] if r4_answer else False,
        "correct_mv": mv_answer == q["correct"] if mv_answer else False,
        "care_resolve": care_result.get("care_resolve"),
        "meaning_debt": debt_result.get("total_meaning_debt", 0),
        "cost_usd": q_cost,
        "total_tokens": q_tokens,
        "api_calls": 4,
        "dialogue": dialogue,
    }


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 22: CGD + Strongest-First")
    parser.add_argument("--test", type=int, default=None, help="Pipeline test N questions")
    args = parser.parse_args()

    assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY env var required"

    all_questions = load_questions()
    n_q = args.test if args.test else N_QUESTIONS

    if args.test:
        questions = all_questions[:n_q]
        print(f"\n  *** PIPELINE TEST MODE: {n_q} questions ***\n")
    else:
        questions = select_questions(all_questions, n_q)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    total_cost = 0.0
    cgd_results = []
    sf_results = []

    print("=" * 70)
    print("  Phase 22: Confidence-Gated Debate + Strongest-First")
    print(f"  Questions: {len(questions)}")
    print(f"  Budget: ${BUDGET_LIMIT}")
    print("=" * 70)

    for i, q in enumerate(questions):
        if total_cost >= BUDGET_LIMIT:
            print(f"\n  BUDGET LIMIT reached at ${total_cost:.2f}")
            break

        # ---- Condition A: CGD ----
        print(f"\n[{i+1}/{len(questions)}] {q['id']} ({q['domain']}) | CGD:", end="", flush=True)
        cgd_result = run_cgd_question(q, total_cost)
        cgd_results.append(cgd_result)
        total_cost += cgd_result["cost_usd"]
        cgd_correct = "✓" if cgd_result["correct"] else "✗"
        print(f" → {cgd_result['final_answer']}({cgd_correct})"
              f" [{cgd_result['debate_type']}]"
              f" ${cgd_result['cost_usd']:.3f}", flush=True)

        # ---- Condition B: SF ----
        print(f"  {'':>{len(str(i+1))+1+len(str(len(questions)))+3+len(q['id'])+3+len(q['domain'])+4}}SF:", end="", flush=True)
        sf_result = run_sf_question(q, total_cost)
        sf_results.append(sf_result)
        total_cost += sf_result["cost_usd"]
        sf_r4_correct = "✓" if sf_result["correct_r4"] else "✗"
        sf_mv_correct = "✓" if sf_result["correct_mv"] else "✗"
        print(f" → R4:{sf_result['r4_final']}({sf_r4_correct})"
              f" MV:{sf_result['majority_vote']}({sf_mv_correct})"
              f" ${sf_result['cost_usd']:.3f}", flush=True)

        # Running stats
        cgd_acc = sum(1 for r in cgd_results if r["correct"]) / len(cgd_results) * 100
        sf_r4_acc = sum(1 for r in sf_results if r["correct_r4"]) / len(sf_results) * 100
        sf_mv_acc = sum(1 for r in sf_results if r["correct_mv"]) / len(sf_results) * 100
        print(f"  Running: CGD={cgd_acc:.0f}% | SF_R4={sf_r4_acc:.0f}% SF_MV={sf_mv_acc:.0f}%"
              f" | Cost=${total_cost:.2f}", flush=True)

        # Save after every question
        _save_results(cgd_results, sf_results, total_cost, timestamp)

    # Final summary
    print("\n" + "=" * 70)
    print("  PHASE 22 COMPLETE")
    print("=" * 70)
    n = len(cgd_results)
    cgd_correct = sum(1 for r in cgd_results if r["correct"])
    sf_r4_correct = sum(1 for r in sf_results if r["correct_r4"])
    sf_mv_correct = sum(1 for r in sf_results if r["correct_mv"])

    print(f"  CGD:         {cgd_correct}/{n} = {cgd_correct/n*100:.1f}%")
    print(f"  SF R4:       {sf_r4_correct}/{n} = {sf_r4_correct/n*100:.1f}%")
    print(f"  SF MV:       {sf_mv_correct}/{n} = {sf_mv_correct/n*100:.1f}%")
    print(f"  Total cost:  ${total_cost:.2f}")
    print(f"  Total calls: {sum(r['api_calls'] for r in cgd_results) + sum(r['api_calls'] for r in sf_results)}")

    # Debate type breakdown
    dt_counts = Counter(r["debate_type"] for r in cgd_results)
    print(f"\n  CGD debate types: {dict(dt_counts)}")
    for dt in sorted(dt_counts.keys()):
        dt_results = [r for r in cgd_results if r["debate_type"] == dt]
        dt_correct = sum(1 for r in dt_results if r["correct"])
        print(f"    {dt}: {dt_correct}/{len(dt_results)} = {dt_correct/len(dt_results)*100:.1f}%")


def _save_results(cgd_results, sf_results, total_cost, timestamp):
    """Save results after each question."""
    n = len(cgd_results)
    data = {
        "phase": "Phase 22: CGD + Strongest-First",
        "timestamp": timestamp,
        "n_questions": n,
        "summary": {
            "cgd_correct": sum(1 for r in cgd_results if r["correct"]),
            "cgd_accuracy": sum(1 for r in cgd_results if r["correct"]) / n if n else 0,
            "sf_r4_correct": sum(1 for r in sf_results if r["correct_r4"]),
            "sf_r4_accuracy": sum(1 for r in sf_results if r["correct_r4"]) / n if n else 0,
            "sf_mv_correct": sum(1 for r in sf_results if r["correct_mv"]),
            "sf_mv_accuracy": sum(1 for r in sf_results if r["correct_mv"]) / n if n else 0,
            "total_cost": total_cost,
            "total_api_calls": sum(r["api_calls"] for r in cgd_results) + sum(r["api_calls"] for r in sf_results),
        },
        "cgd_results": cgd_results,
        "sf_results": sf_results,
    }

    path = os.path.join(RESULTS_DIR, "phase22_results.json")
    # Remove dialogue from saved copy to keep file size manageable
    save_data = json.loads(json.dumps(data, default=str))
    for r in save_data.get("cgd_results", []):
        r.pop("dialogue", None)
    for r in save_data.get("sf_results", []):
        r.pop("dialogue", None)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
