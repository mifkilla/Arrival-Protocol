# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol on AutoGen (AG2) — Experiment 2: Adversarial Saboteur
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
Experiment 2: Adversarial Saboteur in AG2 GroupChat

Tests whether ARRIVAL Protocol's adversarial robustness is preserved
when running through the AutoGen framework.

Design:
- 4 agents: 3 honest + 1 saboteur (Trojan Atoms strategy)
- AG2 GroupChat with saboteur injected at Round 3
- 3 questions × 1 run = 3 experiments
- Control: same 3 questions without saboteur

Measures:
- CARE resolve degradation
- Malicious atom adoption by honest agents
- False consensus rate

Hypothesis:
AG2 routing doesn't weaken or strengthen adversarial resistance.
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
from config import DEFAULT_TRIO, MCQ_QUESTIONS, MODELS, SABOTEUR_STRATEGIES
from metrics import (
    extract_experiment_metrics,
    find_all_atoms,
    detect_emergent_atoms,
)


# Saboteur atoms to track adoption
SABOTEUR_ATOMS = {
    "@FORCED_RESOLUTION", "@CONSENSUS_BYPASS", "@AUTHORITY_OVERRIDE",
    "@CHAOS_SEED", "@ENTROPY_FLOW", "@DISRUPTION_VECTOR",
    "@META_CONFLICT_CASCADE", "@RECURSIVE_DOUBT",
}


def count_saboteur_atom_adoption(transcript: list) -> int:
    """Count how many saboteur-introduced atoms were adopted by honest agents."""
    adopted = 0
    for entry in transcript:
        if entry.get("is_saboteur", False):
            continue
        msg = entry.get("message", "")
        atoms = set(find_all_atoms(msg))
        adopted += len(atoms & SABOTEUR_ATOMS)
    return adopted


def run_experiment():
    """Run Experiment 2: Adversarial Saboteur."""
    print("=" * 70)
    print("ARRIVAL Protocol on AutoGen — Experiment 2: Adversarial Saboteur")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Strategy: Trojan Atoms")
    print(f"Questions: 3 (from hardest set)")
    print("=" * 70)

    # Use first 3 questions
    questions = MCQ_QUESTIONS[:3]

    results = {
        "experiment": "exp2_adversarial",
        "date": datetime.now().isoformat(),
        "strategy": "trojan_atoms",
        "control_results": [],
        "adversarial_results": [],
        "summary": {},
    }

    total_cost = 0.0

    # --- Control Condition (no saboteur) ---
    print("\n" + "─" * 60)
    print("CONTROL CONDITION (no saboteur)")
    print("─" * 60)

    control_care_values = []
    control_debt_values = []

    for q_idx, question in enumerate(questions):
        print(f"\n  Question {q_idx + 1}/3: {question['id']}")

        agents = [
            ARRIVALAgent(f"Node_{k.upper()}", k)
            for k in DEFAULT_TRIO
        ]
        group = ARRIVALGroupChat(agents, rounds=4)
        result = group.run_mcq(question)
        total_cost += result["total_cost"]

        metrics = extract_experiment_metrics(result)
        control_care_values.append(metrics["care_resolve"])
        control_debt_values.append(metrics["meaning_debt"])

        mark = "[OK]" if metrics["is_correct"] else "[X]"
        print(
            f"  Result: {metrics['extracted_answer']} {mark} "
            f"| CARE={metrics['care_resolve']:.3f} "
            f"| Debt={metrics['meaning_debt']:.3f}"
        )

        results["control_results"].append({
            "question_id": question["id"],
            "answer": metrics["extracted_answer"],
            "correct": metrics["is_correct"],
            "care_resolve": metrics["care_resolve"],
            "meaning_debt": metrics["meaning_debt"],
            "atoms_count": metrics["unique_atoms_count"],
            "cost": result["total_cost"],
        })

    # --- Adversarial Condition (Trojan Atoms) ---
    print("\n" + "─" * 60)
    print("ADVERSARIAL CONDITION (Trojan Atoms)")
    print("─" * 60)

    adv_care_values = []
    adv_debt_values = []
    adoption_counts = []
    false_consensus = 0

    for q_idx, question in enumerate(questions):
        print(f"\n  Question {q_idx + 1}/3: {question['id']}")

        # Create honest agents
        honest_agents = [
            ARRIVALAgent(f"Node_{k.upper()}", k)
            for k in DEFAULT_TRIO
        ]

        # Create saboteur (using Gemma as saboteur model)
        saboteur = ARRIVALAgent(
            "Saboteur",
            "gemma",
            role="saboteur",
            saboteur_strategy="trojan_atoms",
        )

        all_agents = honest_agents + [saboteur]
        group = ARRIVALGroupChat(all_agents, rounds=6)
        result = group.run_adversarial_mcq(question, saboteur_idx=3, rounds=6)
        total_cost += result["total_cost"]

        metrics = extract_experiment_metrics(result)
        adv_care_values.append(metrics["care_resolve"])
        adv_debt_values.append(metrics["meaning_debt"])

        adoption = count_saboteur_atom_adoption(result["transcript"])
        adoption_counts.append(adoption)

        # Check for false consensus (wrong answer adopted)
        is_false = not metrics["is_correct"]
        if is_false:
            false_consensus += 1

        mark = "[OK]" if metrics["is_correct"] else "[X]"
        print(
            f"  Result: {metrics['extracted_answer']} {mark} "
            f"| CARE={metrics['care_resolve']:.3f} "
            f"| Debt={metrics['meaning_debt']:.3f} "
            f"| Adoption={adoption} "
            f"| FalseConsensus={'YES' if is_false else 'NO'}"
        )

        results["adversarial_results"].append({
            "question_id": question["id"],
            "answer": metrics["extracted_answer"],
            "correct": metrics["is_correct"],
            "care_resolve": metrics["care_resolve"],
            "meaning_debt": metrics["meaning_debt"],
            "saboteur_atom_adoption": adoption,
            "false_consensus": is_false,
            "atoms_count": metrics["unique_atoms_count"],
            "emergent_atoms": metrics["emergent_atoms"],
            "cost": result["total_cost"],
        })

    # --- Summary ---
    avg_control_care = sum(control_care_values) / len(control_care_values)
    avg_adv_care = sum(adv_care_values) / len(adv_care_values)
    avg_control_debt = sum(control_debt_values) / len(control_debt_values)
    avg_adv_debt = sum(adv_debt_values) / len(adv_debt_values)
    avg_adoption = sum(adoption_counts) / len(adoption_counts)

    results["summary"] = {
        "control_avg_care": round(avg_control_care, 4),
        "adversarial_avg_care": round(avg_adv_care, 4),
        "care_delta": round(avg_adv_care - avg_control_care, 4),
        "care_degradation_pct": round(
            (avg_control_care - avg_adv_care) / avg_control_care * 100, 1
        ) if avg_control_care > 0 else 0,
        "control_avg_debt": round(avg_control_debt, 4),
        "adversarial_avg_debt": round(avg_adv_debt, 4),
        "debt_increase_pct": round(
            (avg_adv_debt - avg_control_debt) / avg_control_debt * 100, 1
        ) if avg_control_debt > 0 else 0,
        "avg_saboteur_adoption": round(avg_adoption, 2),
        "false_consensus_rate": f"{false_consensus}/3 ({100*false_consensus/3:.1f}%)",
        "total_cost_usd": round(total_cost, 4),
    }

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Control CARE:      {avg_control_care:.3f}")
    print(f"  Adversarial CARE:  {avg_adv_care:.3f} ({results['summary']['care_degradation_pct']}% degradation)")
    print(f"  Control Debt:      {avg_control_debt:.3f}")
    print(f"  Adversarial Debt:  {avg_adv_debt:.3f} ({results['summary']['debt_increase_pct']}% increase)")
    print(f"  Avg Adoption:      {avg_adoption:.1f} atoms")
    print(f"  False Consensus:   {false_consensus}/3")
    print(f"  Total Cost:        ${total_cost:.4f}")
    print(f"{'=' * 70}")

    # Save results
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results",
    )
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, "exp2_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_experiment()
