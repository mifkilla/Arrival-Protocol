# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol on AutoGen (AG2) — Experiment 3: AutoGen vs Native Comparison
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
Experiment 3: AutoGen ARRIVAL vs Native ARRIVAL Comparison

Runs IDENTICAL questions on both:
1. AutoGen (AG2) GroupChat implementation
2. Direct OpenRouter API (same as native ARRIVAL runner)

This is the KEY experiment: does the framework matter,
or is ARRIVAL purely about prompts + models?

Design:
- 5 MCQ questions (same as Exp 1)
- Same models (DeepSeek V3, Llama 3.3, Qwen 2.5)
- Same prompts, same questions
- AutoGen side: our ARRIVALGroupChat
- Native side: direct API calls mimicking ARRIVAL Protocol runner

Measures:
- Accuracy difference
- CARE Resolve difference
- Atom count difference
- Cost difference

Innovation:
First direct comparison of protocol performance across frameworks.
"""

import json
import os
import sys
import time
from datetime import datetime

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import ARRIVALAgent, ARRIVALGroupChat
from config import (
    ARRIVAL_SYSTEM_PROMPT,
    DEFAULT_TRIO,
    MCQ_QUESTIONS,
    MODELS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)
from metrics import (
    extract_answer_letter,
    extract_experiment_metrics,
    count_atoms,
    extract_confidence,
)

from openai import OpenAI


def run_native_arrival(question: dict, model_keys: list) -> dict:
    """
    Run ARRIVAL Protocol using direct API calls (native implementation).

    This mimics the original ARRIVAL Protocol runner from E:\\Arrival CRDT\\
    but uses the same OpenRouter API configuration.
    """
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

    options_str = "\n".join(
        f"{k}) {v}" for k, v in question["options"].items()
    )

    roles = ["propose", "respond", "synthesize", "finalize"]
    agent_order = [0, 1, 2, 0]
    transcript = []
    context = ""
    total_cost = 0.0

    for round_num in range(1, 5):
        agent_idx = agent_order[round_num - 1]
        model_key = model_keys[agent_idx]
        model_info = MODELS[model_key]
        role = roles[round_num - 1]

        system_prompt = (
            f"You are {model_info['name']}_Node_{model_key.upper()}, "
            f"a node in the DEUS.PROTOCOL v0.5 network.\n\n"
            f"{ARRIVAL_SYSTEM_PROMPT}\n\n"
            f"TASK: Answer this multiple-choice question.\n\n"
            f"Question: {question['question']}\n\n"
            f"Options:\n{options_str}\n\n"
            f"Round {round_num}/4. Your role: {role}.\n"
            f"State your answer using @CONSENSUS[answer=X]."
        )

        if round_num == 1:
            user_msg = "Begin. Propose your answer using @-atoms."
        else:
            user_msg = f"Previous discussion:\n\n{context}\n\nYour turn ({role})."

        try:
            response = client.chat.completions.create(
                model=model_info["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=1024,
                extra_headers={
                    "HTTP-Referer": "https://github.com/arrival-protocol",
                    "X-Title": "ARRIVAL Native Comparison",
                },
            )

            content = response.choices[0].message.content or ""
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            cost = (prompt_tokens * 0.20 + completion_tokens * 0.60) / 1_000_000
            total_cost += cost

            transcript.append({
                "round": round_num,
                "from": f"Node_{model_key.upper()}",
                "model": model_key,
                "role": role,
                "message": content,
                "cost": cost,
            })

            context += (
                f"\n--- Round {round_num} ({model_info['name']}, "
                f"role: {role}) ---\n{content}\n"
            )

            print(
                f"    R{round_num}: {model_info['short']} ({role}) "
                f"[{len(content)} chars, ${cost:.4f}]"
            )

            time.sleep(1)

        except Exception as e:
            print(f"    [ERROR] {model_key}: {e}")
            transcript.append({
                "round": round_num,
                "from": f"Node_{model_key.upper()}",
                "model": model_key,
                "role": role,
                "message": f"[ERROR: {e}]",
                "cost": 0.0,
            })

    return {
        "question_id": question["id"],
        "question": question["question"],
        "correct_answer": question["correct"],
        "transcript": transcript,
        "total_cost": total_cost,
    }


def run_experiment():
    """Run Experiment 3: AutoGen vs Native Comparison."""
    print("=" * 70)
    print("ARRIVAL Protocol — Experiment 3: AutoGen vs Native Comparison")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Models: {', '.join(MODELS[k]['name'] for k in DEFAULT_TRIO)}")
    print(f"Questions: {len(MCQ_QUESTIONS)}")
    print("=" * 70)

    results = {
        "experiment": "exp3_vs_native",
        "date": datetime.now().isoformat(),
        "models": DEFAULT_TRIO,
        "comparisons": [],
        "summary": {},
    }

    total_cost = 0.0
    ag2_correct = 0
    native_correct = 0
    ag2_care_values = []
    native_care_values = []
    ag2_atom_counts = []
    native_atom_counts = []

    for q_idx, question in enumerate(MCQ_QUESTIONS):
        print(f"\n{'─' * 60}")
        print(f"Question {q_idx + 1}/{len(MCQ_QUESTIONS)}: {question['id']}")
        print(f"  {question['question'][:80]}...")

        comparison = {
            "question_id": question["id"],
            "correct_answer": question["correct"],
        }

        # --- AutoGen (AG2) Implementation ---
        print("\n  [AG2 ARRIVAL]")
        agents = [
            ARRIVALAgent(f"Node_{k.upper()}", k)
            for k in DEFAULT_TRIO
        ]
        group = ARRIVALGroupChat(agents, rounds=4)
        ag2_result = group.run_mcq(question)
        ag2_metrics = extract_experiment_metrics(ag2_result)
        total_cost += ag2_result["total_cost"]

        ag2_care_values.append(ag2_metrics["care_resolve"])
        ag2_atom_counts.append(ag2_metrics["unique_atoms_count"])
        if ag2_metrics["is_correct"]:
            ag2_correct += 1

        mark = "[OK]" if ag2_metrics["is_correct"] else "[X]"
        print(
            f"  AG2: {ag2_metrics['extracted_answer']} {mark} "
            f"| CARE={ag2_metrics['care_resolve']:.3f} "
            f"| Atoms={ag2_metrics['unique_atoms_count']}"
        )

        comparison["ag2"] = {
            "answer": ag2_metrics["extracted_answer"],
            "correct": ag2_metrics["is_correct"],
            "care_resolve": ag2_metrics["care_resolve"],
            "meaning_debt": ag2_metrics["meaning_debt"],
            "atoms_count": ag2_metrics["unique_atoms_count"],
            "emergent_count": ag2_metrics["emergent_atoms_count"],
            "cost": ag2_result["total_cost"],
        }

        # --- Native ARRIVAL Implementation ---
        print("\n  [NATIVE ARRIVAL]")
        native_result = run_native_arrival(question, DEFAULT_TRIO)
        native_metrics = extract_experiment_metrics(native_result)
        total_cost += native_result["total_cost"]

        native_care_values.append(native_metrics["care_resolve"])
        native_atom_counts.append(native_metrics["unique_atoms_count"])
        if native_metrics["is_correct"]:
            native_correct += 1

        mark = "[OK]" if native_metrics["is_correct"] else "[X]"
        print(
            f"  Native: {native_metrics['extracted_answer']} {mark} "
            f"| CARE={native_metrics['care_resolve']:.3f} "
            f"| Atoms={native_metrics['unique_atoms_count']}"
        )

        comparison["native"] = {
            "answer": native_metrics["extracted_answer"],
            "correct": native_metrics["is_correct"],
            "care_resolve": native_metrics["care_resolve"],
            "meaning_debt": native_metrics["meaning_debt"],
            "atoms_count": native_metrics["unique_atoms_count"],
            "emergent_count": native_metrics["emergent_atoms_count"],
            "cost": native_result["total_cost"],
        }

        # --- Delta ---
        comparison["delta"] = {
            "same_answer": (
                ag2_metrics["extracted_answer"] == native_metrics["extracted_answer"]
            ),
            "care_diff": round(
                ag2_metrics["care_resolve"] - native_metrics["care_resolve"], 4
            ),
            "atoms_diff": (
                ag2_metrics["unique_atoms_count"]
                - native_metrics["unique_atoms_count"]
            ),
        }

        results["comparisons"].append(comparison)

    # --- Summary ---
    n = len(MCQ_QUESTIONS)
    avg_ag2_care = sum(ag2_care_values) / n
    avg_native_care = sum(native_care_values) / n
    avg_ag2_atoms = sum(ag2_atom_counts) / n
    avg_native_atoms = sum(native_atom_counts) / n

    same_answer_count = sum(
        1 for c in results["comparisons"] if c["delta"]["same_answer"]
    )

    results["summary"] = {
        "ag2_accuracy": f"{ag2_correct}/{n} ({100*ag2_correct/n:.1f}%)",
        "native_accuracy": f"{native_correct}/{n} ({100*native_correct/n:.1f}%)",
        "accuracy_match": ag2_correct == native_correct,
        "same_answer_rate": f"{same_answer_count}/{n} ({100*same_answer_count/n:.1f}%)",
        "avg_ag2_care": round(avg_ag2_care, 4),
        "avg_native_care": round(avg_native_care, 4),
        "care_difference": round(avg_ag2_care - avg_native_care, 4),
        "avg_ag2_atoms": round(avg_ag2_atoms, 1),
        "avg_native_atoms": round(avg_native_atoms, 1),
        "total_cost_usd": round(total_cost, 4),
        "framework_agnostic": (
            same_answer_count >= n * 0.8
            and abs(avg_ag2_care - avg_native_care) < 0.1
        ),
    }

    print(f"\n{'=' * 70}")
    print("EXPERIMENT 3 SUMMARY: AutoGen vs Native")
    print(f"{'=' * 70}")
    print(f"  AG2 Accuracy:     {ag2_correct}/{n}")
    print(f"  Native Accuracy:  {native_correct}/{n}")
    print(f"  Same Answer:      {same_answer_count}/{n}")
    print(f"  Avg AG2 CARE:     {avg_ag2_care:.3f}")
    print(f"  Avg Native CARE:  {avg_native_care:.3f}")
    print(f"  CARE Difference:  {avg_ag2_care - avg_native_care:+.3f}")
    print(f"  Avg AG2 Atoms:    {avg_ag2_atoms:.1f}")
    print(f"  Avg Native Atoms: {avg_native_atoms:.1f}")
    print(f"  Total Cost:       ${total_cost:.4f}")
    print(f"  Framework-Agnostic: {'YES' if results['summary']['framework_agnostic'] else 'NO'}")
    print(f"{'=' * 70}")

    # Save results
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results",
    )
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, "exp3_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_experiment()
