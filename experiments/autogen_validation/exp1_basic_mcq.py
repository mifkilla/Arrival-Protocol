# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol on AutoGen (AG2) — Experiment 1: Basic MCQ Consensus
# Copyright (C) 2026 Mefodiy Kelevra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Experiment 1: Basic MCQ Consensus via AG2

Tests whether ARRIVAL Protocol @-atoms work correctly when
agents are orchestrated through AutoGen's GroupChat mechanism.

Design:
- 3 agents (DeepSeek V3, Llama 3.3, Qwen 2.5) via OpenRouter
- DEUS Protocol v0.5 system prompts inject @-atoms
- 4-round structured dialogue (propose/respond/synthesize/finalize)
- 5 MCQ questions from Phase 7 hardest set

Measures:
- Do agents use @-atoms correctly?
- Consensus rate?
- CARE Resolve?
- Accuracy vs solo and majority vote?

Hypothesis:
AG2 infrastructure doesn't degrade protocol quality.
"""

import json
import os
import sys
import time
from datetime import datetime

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import ARRIVALAgent, ARRIVALGroupChat
from config import DEFAULT_TRIO, MCQ_QUESTIONS, MODELS
from metrics import extract_experiment_metrics, extract_answer_letter


def run_solo(agent: ARRIVALAgent, question: dict) -> dict:
    """Run a single model answering a question independently."""
    options_str = "\n".join(
        f"{k}) {v}" for k, v in question["options"].items()
    )
    prompt = (
        f"Answer the following multiple-choice question. "
        f"State only the letter of your answer.\n\n"
        f"Question: {question['question']}\n\n"
        f"Options:\n{options_str}\n\n"
        f"Your answer:"
    )
    response, cost = agent.chat(prompt)
    answer = extract_answer_letter(response)
    agent.reset()
    return {
        "model": agent.model_key,
        "answer": answer,
        "correct": answer == question["correct"] if answer else False,
        "cost": cost,
        "response": response,
    }


def run_majority_vote(solo_results: list) -> str:
    """Compute majority vote from solo results."""
    from collections import Counter
    answers = [r["answer"] for r in solo_results if r["answer"]]
    if not answers:
        return None
    counter = Counter(answers)
    return counter.most_common(1)[0][0]


def run_experiment():
    """Run Experiment 1: Basic MCQ Consensus."""
    print("=" * 70)
    print("ARRIVAL Protocol on AutoGen — Experiment 1: Basic MCQ Consensus")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Models: {', '.join(MODELS[k]['name'] for k in DEFAULT_TRIO)}")
    print(f"Questions: {len(MCQ_QUESTIONS)}")
    print("=" * 70)

    results = {
        "experiment": "exp1_basic_mcq",
        "date": datetime.now().isoformat(),
        "models": DEFAULT_TRIO,
        "questions": [],
        "summary": {},
    }

    total_cost = 0.0
    correct_solo = {k: 0 for k in DEFAULT_TRIO}
    correct_mv = 0
    correct_arrival = 0

    for q_idx, question in enumerate(MCQ_QUESTIONS):
        print(f"\n{'─' * 60}")
        print(f"Question {q_idx + 1}/{len(MCQ_QUESTIONS)}: {question['id']}")
        print(f"  {question['question'][:80]}...")
        print(f"  Correct: {question['correct']}")

        q_result = {
            "question_id": question["id"],
            "domain": question["domain"],
            "correct_answer": question["correct"],
        }

        # --- Solo Condition ---
        print("\n  [SOLO]")
        solo_results = []
        for model_key in DEFAULT_TRIO:
            agent = ARRIVALAgent(f"Solo_{model_key}", model_key)
            solo = run_solo(agent, question)
            solo_results.append(solo)
            total_cost += solo["cost"]
            mark = "[OK]" if solo["correct"] else "[X]"
            print(f"    {MODELS[model_key]['short']}: {solo['answer']} {mark} (${solo['cost']:.4f})")
            if solo["correct"]:
                correct_solo[model_key] += 1

        q_result["solo"] = solo_results

        # --- Majority Vote ---
        mv_answer = run_majority_vote(solo_results)
        mv_correct = mv_answer == question["correct"] if mv_answer else False
        q_result["majority_vote"] = {
            "answer": mv_answer,
            "correct": mv_correct,
        }
        if mv_correct:
            correct_mv += 1
        mark = "[OK]" if mv_correct else "[X]"
        print(f"  [MV]: {mv_answer} {mark}")

        # --- ARRIVAL Protocol ---
        print("\n  [ARRIVAL]")
        agents = [
            ARRIVALAgent(f"Node_{k.upper()}", k)
            for k in DEFAULT_TRIO
        ]
        group = ARRIVALGroupChat(agents, rounds=4)
        arrival_result = group.run_mcq(question)
        total_cost += arrival_result["total_cost"]

        metrics = extract_experiment_metrics(arrival_result)
        q_result["arrival"] = {
            "answer": metrics["extracted_answer"],
            "correct": metrics["is_correct"],
            "care_resolve": metrics["care_resolve"],
            "meaning_debt": metrics["meaning_debt"],
            "atoms_count": metrics["unique_atoms_count"],
            "emergent_count": metrics["emergent_atoms_count"],
            "cost": arrival_result["total_cost"],
            "transcript": arrival_result["transcript"],
        }

        if metrics["is_correct"]:
            correct_arrival += 1

        mark = "[OK]" if metrics["is_correct"] else "[X]"
        print(
            f"  [ARRIVAL]: {metrics['extracted_answer']} {mark} "
            f"| CARE={metrics['care_resolve']:.3f} "
            f"| Debt={metrics['meaning_debt']:.3f} "
            f"| Atoms={metrics['unique_atoms_count']} "
            f"| Emergent={metrics['emergent_atoms_count']}"
        )

        results["questions"].append(q_result)

    # --- Summary ---
    n = len(MCQ_QUESTIONS)
    results["summary"] = {
        "total_questions": n,
        "solo_accuracy": {
            k: f"{correct_solo[k]}/{n} ({100*correct_solo[k]/n:.1f}%)"
            for k in DEFAULT_TRIO
        },
        "majority_vote_accuracy": f"{correct_mv}/{n} ({100*correct_mv/n:.1f}%)",
        "arrival_accuracy": f"{correct_arrival}/{n} ({100*correct_arrival/n:.1f}%)",
        "total_cost_usd": round(total_cost, 4),
    }

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    for k in DEFAULT_TRIO:
        print(f"  Solo {MODELS[k]['short']}: {correct_solo[k]}/{n}")
    print(f"  Majority Vote: {correct_mv}/{n}")
    print(f"  ARRIVAL:       {correct_arrival}/{n}")
    print(f"  Total Cost:    ${total_cost:.4f}")
    print(f"{'=' * 70}")

    # Save results
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results",
    )
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, "exp1_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_experiment()
