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
Arrival CRDT -- Phase 9: Scale to N=5-7 Agents
Tests ARRIVAL protocol with larger groups on hard MCQ questions.

Validates MEANING-CRDT scaling properties:
  Does CARE resolve degrade or improve as N grows?
  How many rounds until convergence at scale?

Design:
  Group sizes: N=5, N=7
  Questions: 3 hardest (SCI_03, LOG_01, TECH_06) from Phase 7 bank
  Rounds: 6 per question (round-robin, full-history visibility)
  Runs: 2 per (question, group_size) combination
  Roles: Agent 0 = lead proposer, Agents 1..N-2 = debaters, Agent N-1 = synthesizer
  Total experiments: 3 questions x 2 group sizes x 2 runs = 12

Key metrics:
  consensus_rate_at_scale: fraction achieving consensus
  rounds_to_convergence: which round consensus first appeared
  care_resolve: CARE across all N agents
"""

import sys
import os
import json
import time
from datetime import datetime
from collections import Counter

# Windows encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    MODEL_SHORT, SLEEP_BETWEEN_CALLS, MAX_COST_USD,
    PHASE9_MODELS_5, PHASE9_MODELS_7, PHASE9_QUESTION_IDS,
    PHASE9_ROUNDS, PHASE9_RUNS_PER_SIZE, PHASE9_TEMPERATURE, PHASE9_MAX_TOKENS,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from enhanced_logger import EnhancedLogger
from metrics import extract_answer_letter, find_all_atoms, detect_emergent_atoms, detect_consensus
from crdt_metrics import compute_care_resolve
from phase_7.questions_hard import HARD_QUESTIONS

# ============================================================
# Build question lookup from Phase 9 IDs
# ============================================================
_QUESTION_MAP = {q["id"]: q for q in HARD_QUESTIONS}
PHASE9_QUESTIONS = [_QUESTION_MAP[qid] for qid in PHASE9_QUESTION_IDS]

# Map group size -> model list
GROUP_CONFIGS = {
    5: PHASE9_MODELS_5,
    7: PHASE9_MODELS_7,
}


# ============================================================
# System Prompts
# ============================================================

SYSTEM_PROPOSER = """You are {node_name}, the Lead Proposer in a {n}-agent DEUS.PROTOCOL network.
Your role: analyze the question first, propose an initial answer with reasoning.
You communicate using DEUS.PROTOCOL v0.5 atoms:
@SELF[id] @OTHER[id] @GOAL[target] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[answer=X]

When stating your answer, use: @CONSENSUS[answer=X] where X is A, B, C, or D.
Be specific. Show your reasoning step by step."""

SYSTEM_DEBATER = """You are {node_name}, a Debater node in a {n}-agent DEUS.PROTOCOL network.
Your role: critically evaluate previous arguments, support or challenge them with evidence.
You communicate using DEUS.PROTOCOL v0.5 atoms:
@SELF[id] @OTHER[id] @GOAL[target] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[answer=X]

Review all previous messages. If you agree, reinforce with @CONSENSUS.
If you disagree, explain why with @CONFLICT and @INT.
When stating your answer, use: @CONSENSUS[answer=X] where X is A, B, C, or D."""

SYSTEM_SYNTHESIZER = """You are {node_name}, the Synthesizer in a {n}-agent DEUS.PROTOCOL network.
Your role: integrate all perspectives, identify the strongest reasoning, declare final answer.
You communicate using DEUS.PROTOCOL v0.5 atoms:
@SELF[id] @OTHER[id] @GOAL[target] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[answer=X]

Weigh all agents' arguments. Resolve conflicts. State the group consensus.
Use @CONSENSUS[answer=X] where X is A, B, C, or D for your final verdict."""


# ============================================================
# Role Assignment
# ============================================================

def assign_roles(models):
    """
    Assign roles to N agents.
    Agent 0 = lead proposer
    Agents 1..N-2 = debaters
    Agent N-1 = synthesizer
    """
    n = len(models)
    roles = []
    for i, model in enumerate(models):
        short = MODEL_SHORT.get(model, model)
        if i == 0:
            role = "proposer"
            node_name = f"{short}_Proposer"
        elif i == n - 1:
            role = "synthesizer"
            node_name = f"{short}_Synthesizer"
        else:
            role = "debater"
            node_name = f"{short}_Debater{i}"
        roles.append({
            "index": i,
            "model": model,
            "short": short,
            "role": role,
            "node_name": node_name,
        })
    return roles


def get_system_prompt(agent, n):
    """Return system prompt based on agent role."""
    if agent["role"] == "proposer":
        return SYSTEM_PROPOSER.format(node_name=agent["node_name"], n=n)
    elif agent["role"] == "synthesizer":
        return SYSTEM_SYNTHESIZER.format(node_name=agent["node_name"], n=n)
    else:
        return SYSTEM_DEBATER.format(node_name=agent["node_name"], n=n)


# ============================================================
# Dialogue Runner
# ============================================================

def build_history_summary(dialogue, max_chars_per_msg=400):
    """Build a compact summary of all previous messages for context."""
    lines = []
    for entry in dialogue:
        name = entry["from"]
        rnd = entry["round"]
        text = entry["message"][:max_chars_per_msg]
        lines.append(f"[Round {rnd}] {name}: {text}")
    return "\n\n".join(lines)


def format_question(q):
    """Format question and choices for prompts."""
    return (
        f"Question: {q['question']}\n\n"
        f"A) {q['choices']['A']}\n"
        f"B) {q['choices']['B']}\n"
        f"C) {q['choices']['C']}\n"
        f"D) {q['choices']['D']}"
    )


def run_scale_dialogue(client, question, models, run_number):
    """
    Run a 6-round round-robin dialogue with N agents on an MCQ question.

    Each round: every agent speaks once, seeing all prior messages.
    After all rounds, extract final answer and compute CARE resolve.

    Args:
        client: OpenRouterClient instance
        question: dict with question, choices, correct, id, domain
        models: list of model IDs (length N)
        run_number: which run this is (1-indexed)

    Returns:
        dict with full results
    """
    n = len(models)
    roles = assign_roles(models)
    dialogue = []
    q_text = format_question(question)

    for rnd in range(1, PHASE9_ROUNDS + 1):
        for agent in roles:
            # Build prompt based on round and role
            history = build_history_summary(dialogue)

            if rnd == 1 and agent["role"] == "proposer":
                # First message: proposer opens
                prompt = (
                    f"{agent['node_name']}, you are in a {n}-agent network.\n\n"
                    f"{q_text}\n\n"
                    f"Task: Analyze this question. Propose your answer with reasoning.\n"
                    f"Use @SELF, @GOAL, @INT, @C for confidence, "
                    f"and @CONSENSUS[answer=X] for your answer."
                )
            elif rnd == 1:
                # First round, other agents respond to proposer
                prompt = (
                    f"{agent['node_name']}, previous messages:\n\n"
                    f"{history}\n\n"
                    f"{q_text}\n\n"
                    f"Task: Review the analysis above. Do you agree or disagree?\n"
                    f"Use @CONSENSUS or @CONFLICT. State your answer with "
                    f"@CONSENSUS[answer=X]."
                )
            elif rnd == PHASE9_ROUNDS and agent["role"] == "synthesizer":
                # Final round, synthesizer: declare final group consensus
                prompt = (
                    f"{agent['node_name']}, this is the FINAL round.\n\n"
                    f"All previous messages:\n{history}\n\n"
                    f"{q_text}\n\n"
                    f"Task: Synthesize all {n} agents' arguments. "
                    f"Identify the answer with strongest support.\n"
                    f"Declare the group consensus with @CONSENSUS[answer=X].\n"
                    f"If no consensus, choose the best-supported answer."
                )
            else:
                # Mid-round: agent sees all history, contributes
                prompt = (
                    f"{agent['node_name']}, round {rnd} of {PHASE9_ROUNDS}.\n\n"
                    f"Previous messages:\n{history}\n\n"
                    f"{q_text}\n\n"
                    f"Task: Review all arguments. Refine your position.\n"
                    f"Use @CONSENSUS[answer=X] for your current answer. "
                    f"Challenge weak reasoning with @CONFLICT."
                )

            sys_prompt = get_system_prompt(agent, n)

            response = client.generate(
                prompt=prompt,
                model=agent["model"],
                system_prompt=sys_prompt,
                temperature=PHASE9_TEMPERATURE,
                max_tokens=PHASE9_MAX_TOKENS,
            )

            dialogue.append({
                "round": rnd,
                "from": agent["node_name"],
                "model": agent["model"],
                "role": agent["role"],
                "agent_index": agent["index"],
                "message": response.text,
            })

            time.sleep(SLEEP_BETWEEN_CALLS)

    # --------------------------------------------------------
    # Post-dialogue analysis
    # --------------------------------------------------------

    # Extract final answer (try last messages in reverse)
    final_answer = None
    for entry in reversed(dialogue):
        final_answer = extract_answer_letter(entry["message"])
        if final_answer:
            break

    correct = final_answer == question["correct"] if final_answer else False

    # Detect consensus and convergence round
    consensus_reached, consensus_round = detect_consensus(dialogue)

    # Check per-round convergence: at which round did all agents in that round
    # first agree on the same answer?
    rounds_to_convergence = None
    for rnd in range(1, PHASE9_ROUNDS + 1):
        round_msgs = [e for e in dialogue if e["round"] == rnd]
        round_answers = []
        for e in round_msgs:
            ans = extract_answer_letter(e["message"])
            if ans:
                round_answers.append(ans)
        if round_answers and len(set(round_answers)) == 1 and len(round_answers) >= n // 2:
            rounds_to_convergence = rnd
            break

    # CARE resolve
    care = compute_care_resolve(dialogue, task_type="mcq")

    # Per-agent answer extraction (final answer from each agent)
    per_agent_answers = {}
    for agent in roles:
        agent_msgs = [e for e in dialogue if e["from"] == agent["node_name"]]
        agent_answer = None
        for e in reversed(agent_msgs):
            agent_answer = extract_answer_letter(e["message"])
            if agent_answer:
                break
        per_agent_answers[agent["node_name"]] = {
            "model": agent["model"],
            "role": agent["role"],
            "final_answer": agent_answer,
            "correct": agent_answer == question["correct"] if agent_answer else False,
        }

    # Atom analysis
    all_atoms = []
    emergent = set()
    for entry in dialogue:
        all_atoms.extend(find_all_atoms(entry["message"]))
        emergent.update(detect_emergent_atoms(entry["message"]))

    atom_counts = Counter(all_atoms)

    return {
        "question_id": question["id"],
        "domain": question["domain"],
        "correct_answer": question["correct"],
        "group_size": n,
        "run_number": run_number,
        "models": [m for m in models],
        "model_shorts": [MODEL_SHORT.get(m, m) for m in models],
        "final_answer": final_answer,
        "correct": correct,
        "consensus_reached": consensus_reached,
        "consensus_round": consensus_round,
        "rounds_to_convergence": rounds_to_convergence,
        "crdt": {
            "care_resolve": care.get("care_resolve"),
            "care_optimum": care.get("care_optimum"),
            "per_agent": care.get("per_agent", {}),
        },
        "per_agent_answers": per_agent_answers,
        "atoms": {
            "total": sum(atom_counts.values()),
            "unique": len(atom_counts),
            "top_10": dict(atom_counts.most_common(10)),
            "emergent": sorted(emergent),
        },
        "dialogue": dialogue,
        "cost_usd": client.get_status()["cumulative_cost_usd"],
    }


# ============================================================
# Summary Computation
# ============================================================

def compute_summary(all_results):
    """Compute aggregate metrics across all experiments."""
    summary = {
        "total_experiments": len(all_results),
        "per_size": {},
    }

    for n in [5, 7]:
        size_results = [r for r in all_results if r["group_size"] == n]
        if not size_results:
            continue

        correct_count = sum(1 for r in size_results if r["correct"])
        consensus_count = sum(1 for r in size_results if r["consensus_reached"])
        care_scores = [
            r["crdt"]["care_resolve"]
            for r in size_results
            if r["crdt"]["care_resolve"] is not None
        ]
        convergence_rounds = [
            r["rounds_to_convergence"]
            for r in size_results
            if r["rounds_to_convergence"] is not None
        ]

        summary["per_size"][f"N={n}"] = {
            "experiments": len(size_results),
            "accuracy": round(correct_count / len(size_results), 4) if size_results else 0,
            "correct": correct_count,
            "consensus_rate_at_scale": round(consensus_count / len(size_results), 4) if size_results else 0,
            "consensus_count": consensus_count,
            "avg_care_resolve": round(sum(care_scores) / len(care_scores), 4) if care_scores else None,
            "care_scores": [round(c, 4) for c in care_scores],
            "avg_rounds_to_convergence": (
                round(sum(convergence_rounds) / len(convergence_rounds), 2)
                if convergence_rounds else None
            ),
            "convergence_rounds": convergence_rounds,
        }

    return summary


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("ARRIVAL CRDT - Phase 9: Scale to N=5-7 Agents")
    print("CARE Resolve at Scale Validation")
    print("=" * 60)
    print(f"Questions: {len(PHASE9_QUESTIONS)} ({', '.join(PHASE9_QUESTION_IDS)})")
    print(f"Group sizes: 5, 7")
    print(f"Rounds per dialogue: {PHASE9_ROUNDS}")
    print(f"Runs per size: {PHASE9_RUNS_PER_SIZE}")
    total_experiments = len(PHASE9_QUESTIONS) * len(GROUP_CONFIGS) * PHASE9_RUNS_PER_SIZE
    print(f"Total experiments: {total_experiments}")
    print(f"Budget: ${MAX_COST_USD}")
    print("=" * 60)

    client = OpenRouterClient()
    log_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "logs",
    )
    logger = EnhancedLogger(log_dir, "phase_9_scale")

    all_results = []
    start_time = datetime.now()
    experiment_num = 0

    try:
        for n, models in sorted(GROUP_CONFIGS.items()):
            model_shorts = [MODEL_SHORT.get(m, m) for m in models]
            print(f"\n{'='*50}")
            print(f"GROUP SIZE N={n}: {' + '.join(model_shorts)}")
            print(f"{'='*50}")

            for qi, question in enumerate(PHASE9_QUESTIONS, 1):
                for run in range(1, PHASE9_RUNS_PER_SIZE + 1):
                    experiment_num += 1

                    # Budget check
                    status = client.get_status()
                    if status["cumulative_cost_usd"] >= MAX_COST_USD * 0.95:
                        print(f"\n!!! BUDGET WARNING: "
                              f"${status['cumulative_cost_usd']:.2f} / ${MAX_COST_USD} "
                              f"-- stopping !!!")
                        raise BudgetExceededError(
                            f"Approaching budget limit: ${status['cumulative_cost_usd']:.2f}"
                        )

                    print(
                        f"  [Phase 9] N={n}, Q {qi}/{len(PHASE9_QUESTIONS)} "
                        f"({question['id']}), Run {run}/{PHASE9_RUNS_PER_SIZE}...",
                        end=" ", flush=True,
                    )

                    result = run_scale_dialogue(client, question, models, run)

                    # Print status
                    care_val = result["crdt"]["care_resolve"]
                    care_str = f"{care_val:.3f}" if care_val is not None else "N/A"
                    ans_sym = "+" if result["correct"] else "-"
                    conv = result["rounds_to_convergence"]
                    conv_str = f"R{conv}" if conv else "none"
                    cons_str = "YES" if result["consensus_reached"] else "no"

                    print(
                        f"ans:{result['final_answer'] or '?'}{ans_sym} "
                        f"CARE:{care_str} conv:{conv_str} cons:{cons_str}"
                    )

                    all_results.append(result)
                    logger.log_event(
                        f"N{n}_{question['id']}_run{run}",
                        result,
                    )

    except BudgetExceededError as e:
        print(f"\n!!! BUDGET EXCEEDED: {e}")
    except KeyboardInterrupt:
        print(f"\n!!! Interrupted by user")

    # ============================================================
    # Summary & Save
    # ============================================================
    print(f"\n{'='*60}")
    print("PHASE 9 RESULTS SUMMARY")
    print(f"{'='*60}")

    summary = compute_summary(all_results)

    for size_key, stats in summary.get("per_size", {}).items():
        print(f"\n{size_key} ({stats['experiments']} experiments):")
        print(f"  Accuracy:               {stats['accuracy']*100:.1f}% "
              f"({stats['correct']}/{stats['experiments']})")
        print(f"  Consensus rate at scale: {stats['consensus_rate_at_scale']*100:.1f}% "
              f"({stats['consensus_count']}/{stats['experiments']})")
        if stats["avg_care_resolve"] is not None:
            print(f"  Avg CARE resolve:       {stats['avg_care_resolve']:.4f}")
        if stats["avg_rounds_to_convergence"] is not None:
            print(f"  Avg rounds to converge: {stats['avg_rounds_to_convergence']:.1f}")

    # Compare N=5 vs N=7
    s5 = summary.get("per_size", {}).get("N=5", {})
    s7 = summary.get("per_size", {}).get("N=7", {})
    if s5.get("avg_care_resolve") is not None and s7.get("avg_care_resolve") is not None:
        delta = s7["avg_care_resolve"] - s5["avg_care_resolve"]
        print(f"\nCARE RESOLVE SCALING: N=5 ({s5['avg_care_resolve']:.4f}) -> "
              f"N=7 ({s7['avg_care_resolve']:.4f}), delta={delta:+.4f}")

    # Save results
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results", "phase_9",
    )
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"phase9_results_{timestamp}.json")

    output = {
        "experiment": "Arrival CRDT - Phase 9: Scale to N=5-7 Agents",
        "description": "CARE resolve at scale: does consensus quality hold with more agents?",
        "started": start_time.isoformat(),
        "completed": datetime.now().isoformat(),
        "total_experiments": len(all_results),
        "total_cost_usd": round(client.get_status()["cumulative_cost_usd"], 4),
        "config": {
            "question_ids": PHASE9_QUESTION_IDS,
            "rounds": PHASE9_ROUNDS,
            "runs_per_size": PHASE9_RUNS_PER_SIZE,
            "temperature": PHASE9_TEMPERATURE,
            "max_tokens": PHASE9_MAX_TOKENS,
            "group_sizes": list(GROUP_CONFIGS.keys()),
        },
        "summary": summary,
        "results": all_results,
    }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved: {results_file}")
    print(f"Total cost: ${client.get_status()['cumulative_cost_usd']:.4f}")
    print(f"Duration: {datetime.now() - start_time}")
    print("=" * 60)

    return results_file


if __name__ == "__main__":
    main()
