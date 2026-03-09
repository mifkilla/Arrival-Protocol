# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
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
ARRIVAL Phase 5: Benchmark — ARRIVAL Protocol vs Majority Voting
Compares 3 conditions on 50 MCQ questions across 5 domains.
Conditions: Solo | Majority Vote | ARRIVAL Protocol (4-round dialogue)
"""

import sys
import os
import json
import time
from datetime import datetime
from collections import Counter

# Windows encoding fix
sys.stdout.reconfigure(errors='replace')

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    TRIOS, MODELS, MODEL_SHORT, KNOWN_ATOMS,
    PHASE5_TEMPERATURE, PHASE5_MAX_TOKENS, PHASE5_SOLO_MAX_TOKENS,
    SLEEP_BETWEEN_CALLS, MAX_COST_USD
)
from openrouter_client import OpenRouterClient
from metrics import extract_answer_letter, find_all_atoms, detect_emergent_atoms
from enhanced_logger import EnhancedLogger
from questions import QUESTIONS, DOMAINS

# ============================================================
# System Prompts
# ============================================================

SOLO_SYSTEM = """You are an expert answering a multiple-choice question.
Analyze the question carefully, reason step by step, then state your final answer.
End your response with a clear statement: "The answer is X" where X is A, B, C, or D."""

ARRIVAL_SYSTEM = """You are a node in the DEUS.PROTOCOL v0.4 communication network.
You use semantic atoms for structured reasoning:
@SELF — your identity and perspective
@OTHER — acknowledging the other node
@GOAL — the task objective
@INT — your reasoning intention
@C — coherence of your analysis
@CONSENSUS — when you agree with another node
@CONFLICT — when you disagree and explain why
@RESOLUTION — your proposed resolution

Your task: Answer a multiple-choice question through collaborative reasoning.
Use the atoms above to structure your response.
Analyze the question, share your reasoning, and engage with other nodes' perspectives.
When stating your final answer, use: @CONSENSUS[answer=X] where X is A, B, C, or D."""

ARRIVAL_ROUND_PROMPTS = {
    1: """You are Node {node_name} ({model_short}).
Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Analyze this question using DEUS protocol atoms. State your reasoning and initial answer.
Use @SELF to identify, @GOAL for the task, @INT for your reasoning, @C for confidence.""",

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
State your answer clearly.""",

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
Propose the final answer with @RESOLUTION. Use @CONSENSUS[answer=X] for your verdict.""",

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
If there's no clear consensus, choose the best-supported answer and explain."""
}


# ============================================================
# Experiment Runner
# ============================================================

class Phase5Runner:
    def __init__(self):
        self.client = OpenRouterClient()
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiment_logs")
        self.logger = EnhancedLogger(log_dir, "phase_5_benchmark")
        self.results = []
        self.total_cost = 0.0
        self.start_time = datetime.now()

    def run_solo(self, model: str, question: dict) -> dict:
        """Single model answers independently."""
        prompt = f"""Question: {question['question']}

A) {question['choices']['A']}
B) {question['choices']['B']}
C) {question['choices']['C']}
D) {question['choices']['D']}

Think step by step, then state your final answer as "The answer is X"."""

        response = self.client.generate(
            prompt=prompt,
            model=model,
            system_prompt=SOLO_SYSTEM,
            temperature=PHASE5_TEMPERATURE,
            max_tokens=PHASE5_SOLO_MAX_TOKENS,
        )

        self.total_cost += response.cost_usd
        answer = extract_answer_letter(response.text)

        return {
            "model": model,
            "model_short": MODEL_SHORT.get(model, model),
            "answer": answer,
            "correct": answer == question["correct"] if answer else False,
            "response_text": response.text,
            "cost_usd": response.cost_usd,
            "tokens": response.prompt_tokens + response.completion_tokens,
        }

    def run_majority_vote(self, trio: list, question: dict) -> dict:
        """Three models answer independently, majority wins."""
        solo_results = []
        for model in trio:
            result = self.run_solo(model, question)
            solo_results.append(result)
            time.sleep(SLEEP_BETWEEN_CALLS)

        # Count votes
        answers = [r["answer"] for r in solo_results if r["answer"]]
        if not answers:
            majority_answer = None
        else:
            vote_counts = Counter(answers)
            majority_answer = vote_counts.most_common(1)[0][0]

        total_cost = sum(r["cost_usd"] for r in solo_results)

        return {
            "condition": "majority_vote",
            "trio": [MODEL_SHORT.get(m, m) for m in trio],
            "individual_answers": [
                {"model": r["model_short"], "answer": r["answer"], "correct": r["correct"]}
                for r in solo_results
            ],
            "majority_answer": majority_answer,
            "correct": majority_answer == question["correct"] if majority_answer else False,
            "unanimous": len(set(answers)) == 1 if answers else False,
            "cost_usd": total_cost,
            "solo_results": solo_results,
        }

    def run_arrival_protocol(self, trio: list, question: dict) -> dict:
        """4-round ARRIVAL Protocol dialogue, extract final answer."""
        dialogue = []
        responses = {}
        total_cost = 0.0
        total_tokens = 0
        all_atoms = []
        emergent = set()

        q = question
        choice_vars = {
            "choice_a": q["choices"]["A"],
            "choice_b": q["choices"]["B"],
            "choice_c": q["choices"]["C"],
            "choice_d": q["choices"]["D"],
            "question": q["question"],
        }

        # Round 1: Model A proposes
        model_a = trio[0]
        prompt_1 = ARRIVAL_ROUND_PROMPTS[1].format(
            node_name="Alpha",
            model_short=MODEL_SHORT.get(model_a, model_a),
            **choice_vars
        )
        resp_1 = self.client.generate(
            prompt=prompt_1,
            model=model_a,
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE5_TEMPERATURE,
            max_tokens=PHASE5_MAX_TOKENS,
        )
        responses["r1"] = resp_1.text
        total_cost += resp_1.cost_usd
        total_tokens += resp_1.prompt_tokens + resp_1.completion_tokens
        dialogue.append({"round": 1, "from": MODEL_SHORT.get(model_a, model_a), "message": resp_1.text})
        all_atoms.extend(find_all_atoms(resp_1.text))
        emergent.update(detect_emergent_atoms(resp_1.text))
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 2: Model B responds
        model_b = trio[1]
        prompt_2 = ARRIVAL_ROUND_PROMPTS[2].format(
            node_name="Beta",
            model_short=MODEL_SHORT.get(model_b, model_b),
            previous_response=resp_1.text[:1500],
            **choice_vars
        )
        resp_2 = self.client.generate(
            prompt=prompt_2,
            model=model_b,
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE5_TEMPERATURE,
            max_tokens=PHASE5_MAX_TOKENS,
        )
        responses["r2"] = resp_2.text
        total_cost += resp_2.cost_usd
        total_tokens += resp_2.prompt_tokens + resp_2.completion_tokens
        dialogue.append({"round": 2, "from": MODEL_SHORT.get(model_b, model_b), "message": resp_2.text})
        all_atoms.extend(find_all_atoms(resp_2.text))
        emergent.update(detect_emergent_atoms(resp_2.text))
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 3: Model C synthesizes
        model_c = trio[2]
        prompt_3 = ARRIVAL_ROUND_PROMPTS[3].format(
            node_name="Gamma",
            model_short=MODEL_SHORT.get(model_c, model_c),
            response_1=resp_1.text[:1200],
            response_2=resp_2.text[:1200],
            **choice_vars
        )
        resp_3 = self.client.generate(
            prompt=prompt_3,
            model=model_c,
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE5_TEMPERATURE,
            max_tokens=PHASE5_MAX_TOKENS,
        )
        responses["r3"] = resp_3.text
        total_cost += resp_3.cost_usd
        total_tokens += resp_3.prompt_tokens + resp_3.completion_tokens
        dialogue.append({"round": 3, "from": MODEL_SHORT.get(model_c, model_c), "message": resp_3.text})
        all_atoms.extend(find_all_atoms(resp_3.text))
        emergent.update(detect_emergent_atoms(resp_3.text))
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 4: Model A finalizes
        prompt_4 = ARRIVAL_ROUND_PROMPTS[4].format(
            node_name="Alpha",
            model_short=MODEL_SHORT.get(model_a, model_a),
            response_1=resp_1.text[:800],
            response_2=resp_2.text[:800],
            response_3=resp_3.text[:800],
            **choice_vars
        )
        resp_4 = self.client.generate(
            prompt=prompt_4,
            model=model_a,
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE5_TEMPERATURE,
            max_tokens=PHASE5_MAX_TOKENS,
        )
        responses["r4"] = resp_4.text
        total_cost += resp_4.cost_usd
        total_tokens += resp_4.prompt_tokens + resp_4.completion_tokens
        dialogue.append({"round": 4, "from": MODEL_SHORT.get(model_a, model_a), "message": resp_4.text})
        all_atoms.extend(find_all_atoms(resp_4.text))
        emergent.update(detect_emergent_atoms(resp_4.text))

        # Extract final answer from last round (try each round in reverse)
        final_answer = None
        for r_key in ["r4", "r3", "r2", "r1"]:
            final_answer = extract_answer_letter(responses[r_key])
            if final_answer:
                break

        self.total_cost += total_cost

        atom_counts = Counter(all_atoms)

        return {
            "condition": "arrival_protocol",
            "trio": [MODEL_SHORT.get(m, m) for m in trio],
            "final_answer": final_answer,
            "correct": final_answer == question["correct"] if final_answer else False,
            "dialogue": dialogue,
            "atoms_used": dict(atom_counts),
            "unique_atoms": len(atom_counts),
            "emergent_atoms": sorted(emergent),
            "cost_usd": total_cost,
            "total_tokens": total_tokens,
            "rounds": 4,
        }

    def run_full_experiment(self):
        """Run all conditions for all questions across all trios."""
        print(f"\n{'='*60}")
        print(f"ARRIVAL Phase 5: Benchmark Experiment")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Questions: {len(QUESTIONS)} across {len(DOMAINS)} domains")
        print(f"Trios: {len(TRIOS)}")
        print(f"Budget: ${MAX_COST_USD}")
        print(f"{'='*60}\n")

        all_results = []

        for trio_name, trio_models in TRIOS.items():
            trio_short = [MODEL_SHORT.get(m, m) for m in trio_models]
            print(f"\n--- Trio {trio_name.upper()}: {' + '.join(trio_short)} ---\n")

            for i, question in enumerate(QUESTIONS):
                # Budget check
                if self.total_cost >= MAX_COST_USD * 0.95:
                    print(f"\n!!! BUDGET WARNING: ${self.total_cost:.2f} / ${MAX_COST_USD} — stopping !!!")
                    break

                print(f"  [{trio_name}] Q{i+1}/50 ({question['id']}, {question['domain']})...", end=" ", flush=True)

                # Condition 1: Majority Vote (includes solo results)
                majority_result = self.run_majority_vote(trio_models, question)

                # Condition 2: ARRIVAL Protocol
                arrival_result = self.run_arrival_protocol(trio_models, question)

                # Assemble result
                result_entry = {
                    "question_id": question["id"],
                    "domain": question["domain"],
                    "correct_answer": question["correct"],
                    "trio_name": trio_name,
                    "trio_models": trio_short,
                    # Solo results (from majority vote's individual answers)
                    "solo": majority_result["individual_answers"],
                    # Majority vote
                    "majority_vote": {
                        "answer": majority_result["majority_answer"],
                        "correct": majority_result["correct"],
                        "unanimous": majority_result["unanimous"],
                        "cost_usd": majority_result["cost_usd"],
                    },
                    # ARRIVAL Protocol
                    "arrival": {
                        "answer": arrival_result["final_answer"],
                        "correct": arrival_result["correct"],
                        "atoms_used": arrival_result["atoms_used"],
                        "unique_atoms": arrival_result["unique_atoms"],
                        "emergent_atoms": arrival_result["emergent_atoms"],
                        "cost_usd": arrival_result["cost_usd"],
                        "total_tokens": arrival_result["total_tokens"],
                        "dialogue": arrival_result["dialogue"],
                    },
                    "timestamp": datetime.now().isoformat(),
                }

                all_results.append(result_entry)

                # Status symbols
                mv_sym = "+" if majority_result["correct"] else "-"
                ar_sym = "+" if arrival_result["correct"] else "-"
                print(f"MV:{mv_sym} AR:{ar_sym} (${self.total_cost:.2f})")

                # Log each question
                self.logger.log_event(f"question_{question['id']}", result_entry)

        # ============================================================
        # Save results
        # ============================================================
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "results", "phase_5"
        )
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(results_dir, f"phase5_results_{timestamp}.json")

        # Compute summary stats
        summary = self._compute_summary(all_results)

        output = {
            "experiment": "ARRIVAL Phase 5: Benchmark",
            "started": self.start_time.isoformat(),
            "completed": datetime.now().isoformat(),
            "total_questions": len(QUESTIONS),
            "total_experiments": len(all_results),
            "total_cost_usd": round(self.total_cost, 4),
            "trios": {k: [MODEL_SHORT.get(m, m) for m in v] for k, v in TRIOS.items()},
            "summary": summary,
            "results": all_results,
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"EXPERIMENT COMPLETE")
        print(f"Results saved: {results_file}")
        print(f"Total cost: ${self.total_cost:.4f}")
        print(f"Duration: {datetime.now() - self.start_time}")
        print(f"\nSummary:")
        for cond, stats in summary.items():
            if isinstance(stats, dict) and "accuracy" in stats:
                print(f"  {cond}: {stats['accuracy']*100:.1f}% accuracy ({stats['correct']}/{stats['total']})")
        print(f"{'='*60}")

        return results_file

    def _compute_summary(self, results: list) -> dict:
        """Compute summary statistics from results."""
        summary = {}

        # Overall accuracy by condition
        for condition in ["solo", "majority_vote", "arrival"]:
            correct = 0
            total = 0

            for r in results:
                if condition == "solo":
                    for solo in r["solo"]:
                        if solo["correct"]:
                            correct += 1
                        total += 1
                elif condition == "majority_vote":
                    if r["majority_vote"]["correct"]:
                        correct += 1
                    total += 1
                elif condition == "arrival":
                    if r["arrival"]["correct"]:
                        correct += 1
                    total += 1

            summary[condition] = {
                "correct": correct,
                "total": total,
                "accuracy": round(correct / total, 4) if total > 0 else 0,
            }

        # Per-domain accuracy
        domain_stats = {}
        for domain in DOMAINS:
            domain_results = [r for r in results if r["domain"] == domain]
            domain_stats[domain] = {}

            for condition in ["majority_vote", "arrival"]:
                correct = sum(1 for r in domain_results if r[condition]["correct"])
                total = len(domain_results)
                domain_stats[domain][condition] = {
                    "correct": correct,
                    "total": total,
                    "accuracy": round(correct / total, 4) if total > 0 else 0,
                }

        summary["per_domain"] = domain_stats

        # Per-trio accuracy
        trio_stats = {}
        for trio_name in TRIOS:
            trio_results = [r for r in results if r["trio_name"] == trio_name]
            trio_stats[trio_name] = {}

            for condition in ["majority_vote", "arrival"]:
                correct = sum(1 for r in trio_results if r[condition]["correct"])
                total = len(trio_results)
                trio_stats[trio_name][condition] = {
                    "correct": correct,
                    "total": total,
                    "accuracy": round(correct / total, 4) if total > 0 else 0,
                }

        summary["per_trio"] = trio_stats

        # ARRIVAL-specific metrics
        all_atoms_arrival = Counter()
        all_emergent = set()
        total_arrival_cost = 0

        for r in results:
            for atom, count in r["arrival"].get("atoms_used", {}).items():
                all_atoms_arrival[atom] += count
            all_emergent.update(r["arrival"].get("emergent_atoms", []))
            total_arrival_cost += r["arrival"].get("cost_usd", 0)

        summary["arrival_metrics"] = {
            "total_atoms_used": sum(all_atoms_arrival.values()),
            "unique_atoms": len(all_atoms_arrival),
            "top_atoms": dict(all_atoms_arrival.most_common(10)),
            "emergent_atoms": sorted(all_emergent),
            "emergent_count": len(all_emergent),
            "total_cost": round(total_arrival_cost, 4),
        }

        return summary


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    runner = Phase5Runner()
    results_file = runner.run_full_experiment()
    print(f"\nResults: {results_file}")
