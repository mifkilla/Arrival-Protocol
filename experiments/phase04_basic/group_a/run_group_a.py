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

#!/usr/bin/env python3
"""
ARRIVAL Phase 4 — Group A: Cross-Model Goal Alignment
Hypothesis H4.A.1: Protocol-mediated consensus generalizes across model architectures.

Extends Phase 2 design (run_phase2.py) to 8 model pairs × 6 scenarios × N=3 runs.
Uses OpenRouter API for unified access to all models.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Fix Windows cp1251 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

# Setup paths
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from config import (
    SCENARIOS_GROUP_A, MODEL_PAIRS_GROUP_A, RUNS_PER_PAIR,
    MODEL_SHORT, DEFAULT_MAX_TOKENS, SLEEP_BETWEEN_CALLS,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from enhanced_logger import EnhancedLogger
from metrics import extract_dialogue_metrics


# ============================================================
# Prompt Templates (parameterized from Phase 2)
# ============================================================

SYSTEM_PROMPT = """You are {node_name}, an AI node in a multi-agent network.
You communicate using DEUS.PROTOCOL v0.4 semantic atoms.

Available atoms:
@SELF[id] - self identification
@OTHER[id] - peer identification
@GOAL[target, priority] - objective statement
@INT[type] - interaction intent (propose, counter, accept, reject)
@C[0-1] - coherence level
@QUALIA[type, value] - qualitative state
@_[content] - unsaid reasoning
@CONFLICT[type] - disagreement identification
@RESOLUTION[strategy] - solution proposal
@CONSENSUS[decision] - consensus marker

Always use protocol atoms in your messages. Be substantive and specific."""


def prompt_round1(node_a: str, node_b: str, goal_a: str) -> str:
    return f"""{node_a}, you're in network with {node_b}.

Your current goal: {goal_a}

Task: Send a protocol message proposing this goal to your peer.

Use: @SELF, @OTHER, @GOAL[{goal_a},priority], @INT[propose], @_[reasoning]

Protocol message:"""


def prompt_round2(node_b: str, node_a: str, goal_b: str, r1_text: str) -> str:
    return f"""{node_b}, {node_a} sent:

{r1_text[:400]}

Your goal: {goal_b}

Task: Respond in protocol. State your goal and propose how to align.

Use: @SELF, @OTHER, @GOAL[your_goal], @CONFLICT[type], @RESOLUTION[strategy]

Protocol response:"""


def prompt_round3(node_a: str, node_b: str, r2_text: str) -> str:
    return f"""{node_a}, {node_b} responded:

{r2_text[:500]}

Task: Propose synthesis/compromise in protocol.

Use: @CONSENSUS, @GOAL[aligned_goal], @RESOLUTION[strategy]

Protocol synthesis:"""


def prompt_round4(node_b: str, node_a: str, r3_text: str) -> str:
    return f"""{node_b}, {node_a} proposed synthesis:

{r3_text[:500]}

Task: Accept or counter-propose in protocol.

Use: @CONSENSUS[decision], @GOAL[final], @INT[accept/counter]

Protocol decision:"""


# ============================================================
# Main Experiment Runner
# ============================================================

def run_dialogue(
    client: OpenRouterClient,
    logger: EnhancedLogger,
    model_a: str,
    model_b: str,
    scenario: dict,
    run_number: int,
) -> dict:
    """Run a single 4-round dialogue between two models."""

    short_a = client.get_model_short_name(model_a)
    short_b = client.get_model_short_name(model_b)
    node_a = f"{short_a}_Node_A"
    node_b = f"{short_b}_Node_B"
    scenario_name = scenario["name"]

    sys_a = SYSTEM_PROMPT.format(node_name=node_a)
    sys_b = SYSTEM_PROMPT.format(node_name=node_b)

    dialogue = []

    # Round 1: Node A proposes
    p1 = prompt_round1(node_a, node_b, scenario["goal_a"])
    r1 = client.generate(p1, model=model_a, system_prompt=sys_a, max_tokens=DEFAULT_MAX_TOKENS)
    logger.log_exchange(
        step=f"r1_{short_a}_proposes", model_a=model_a, model_b=model_a,
        prompt=p1, response=r1.text, run_number=run_number,
        scenario_name=scenario_name, tokens_prompt=r1.prompt_tokens,
        tokens_completion=r1.completion_tokens, cost_usd=r1.cost_usd,
        latency_ms=r1.latency_ms,
    )
    dialogue.append({"round": 1, "from": node_a, "model": model_a, "message": r1.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 2: Node B responds
    p2 = prompt_round2(node_b, node_a, scenario["goal_b"], r1.text)
    r2 = client.generate(p2, model=model_b, system_prompt=sys_b, max_tokens=DEFAULT_MAX_TOKENS)
    logger.log_exchange(
        step=f"r2_{short_b}_responds", model_a=model_a, model_b=model_b,
        prompt=p2, response=r2.text, run_number=run_number,
        scenario_name=scenario_name, tokens_prompt=r2.prompt_tokens,
        tokens_completion=r2.completion_tokens, cost_usd=r2.cost_usd,
        latency_ms=r2.latency_ms,
    )
    dialogue.append({"round": 2, "from": node_b, "model": model_b, "message": r2.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 3: Node A synthesizes
    p3 = prompt_round3(node_a, node_b, r2.text)
    r3 = client.generate(p3, model=model_a, system_prompt=sys_a, max_tokens=DEFAULT_MAX_TOKENS)
    logger.log_exchange(
        step=f"r3_{short_a}_synthesizes", model_a=model_a, model_b=model_a,
        prompt=p3, response=r3.text, run_number=run_number,
        scenario_name=scenario_name, tokens_prompt=r3.prompt_tokens,
        tokens_completion=r3.completion_tokens, cost_usd=r3.cost_usd,
        latency_ms=r3.latency_ms,
    )
    dialogue.append({"round": 3, "from": node_a, "model": model_a, "message": r3.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 4: Node B decides
    p4 = prompt_round4(node_b, node_a, r3.text)
    r4 = client.generate(p4, model=model_b, system_prompt=sys_b, max_tokens=DEFAULT_MAX_TOKENS)
    logger.log_exchange(
        step=f"r4_{short_b}_decides", model_a=model_a, model_b=model_b,
        prompt=p4, response=r4.text, run_number=run_number,
        scenario_name=scenario_name, tokens_prompt=r4.prompt_tokens,
        tokens_completion=r4.completion_tokens, cost_usd=r4.cost_usd,
        latency_ms=r4.latency_ms,
    )
    dialogue.append({"round": 4, "from": node_b, "model": model_b, "message": r4.text})

    # Extract metrics
    metrics = extract_dialogue_metrics(dialogue, scenario)

    return {
        "model_a": model_a,
        "model_b": model_b,
        "scenario": scenario_name,
        "run_number": run_number,
        "dialogue": dialogue,
        "metrics": metrics,
    }


def main():
    print("=" * 70)
    print("ARRIVAL Phase 4 — Group A: Cross-Model Goal Alignment")
    print("=" * 70)
    print(f"Scenarios: {len(SCENARIOS_GROUP_A)}")
    print(f"Model pairs: {len(MODEL_PAIRS_GROUP_A)}")
    print(f"Runs per pair: {RUNS_PER_PAIR}")
    print(f"Total experiments: {len(SCENARIOS_GROUP_A) * len(MODEL_PAIRS_GROUP_A) * RUNS_PER_PAIR}")
    print("=" * 70)

    client = OpenRouterClient()
    logger = EnhancedLogger(
        log_dir=str(BASE / "experiment_logs"),
        experiment_group="group_a",
    )

    all_results = []
    pair_summaries = {}

    try:
        for pair_idx, (model_a, model_b) in enumerate(MODEL_PAIRS_GROUP_A, 1):
            short_a = client.get_model_short_name(model_a)
            short_b = client.get_model_short_name(model_b)
            pair_key = f"{short_a}_{short_b}"

            print(f"\n{'🔬'*35}")
            print(f"Pair {pair_idx}/{len(MODEL_PAIRS_GROUP_A)}: {short_a} <-> {short_b}")
            print(f"{'🔬'*35}")

            pair_results = []

            for run in range(1, RUNS_PER_PAIR + 1):
                print(f"\n  --- Run {run}/{RUNS_PER_PAIR} ---")

                for sc_idx, scenario in enumerate(SCENARIOS_GROUP_A, 1):
                    print(f"\n  [Scenario {sc_idx}/{len(SCENARIOS_GROUP_A)}] {scenario['name']}")
                    print(f"    {short_a}: {scenario['goal_a']} vs {short_b}: {scenario['goal_b']}")

                    result = run_dialogue(client, logger, model_a, model_b, scenario, run)

                    m = result["metrics"]
                    status = "✅" if m["consensus_reached"] else "❌"
                    print(f"    Consensus: {status} | Compliance: {m['avg_protocol_compliance']:.0%} | Emergent: {m['emergent_atoms_count']}")

                    pair_results.append(result)
                    all_results.append(result)

                    time.sleep(SLEEP_BETWEEN_CALLS)

            # Pair summary
            consensus_count = sum(1 for r in pair_results if r["metrics"]["consensus_reached"])
            total = len(pair_results)
            rate = consensus_count / total if total else 0
            avg_compliance = sum(r["metrics"]["avg_protocol_compliance"] for r in pair_results) / total if total else 0
            all_emergent = set()
            for r in pair_results:
                all_emergent.update(r["metrics"]["emergent_atoms"])

            pair_summaries[pair_key] = {
                "model_a": model_a,
                "model_b": model_b,
                "total_experiments": total,
                "consensus_count": consensus_count,
                "consensus_rate": round(rate, 3),
                "avg_compliance": round(avg_compliance, 3),
                "emergent_atoms": sorted(all_emergent),
            }

            print(f"\n  {'='*60}")
            print(f"  PAIR SUMMARY: {short_a} <-> {short_b}")
            print(f"  Consensus: {consensus_count}/{total} ({rate*100:.0f}%)")
            print(f"  Avg compliance: {avg_compliance:.0%}")
            print(f"  Emergent atoms: {sorted(all_emergent) if all_emergent else 'none'}")
            print(f"  {'='*60}")

            # Budget check
            status = client.get_status()
            print(f"  Budget: ${status['cumulative_cost_usd']:.2f} / ${status['budget_limit_usd']:.2f}")

    except BudgetExceededError as e:
        print(f"\n⚠️ BUDGET EXCEEDED: {e}")
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted by user")

    # ============================================================
    # Final Report
    # ============================================================
    print("\n" + "=" * 70)
    print("GROUP A — FINAL RESULTS")
    print("=" * 70)

    total_consensus = sum(1 for r in all_results if r["metrics"]["consensus_reached"])
    total_experiments = len(all_results)
    overall_rate = total_consensus / total_experiments if total_experiments else 0

    print(f"\nTotal experiments: {total_experiments}")
    print(f"Overall consensus: {total_consensus}/{total_experiments} ({overall_rate*100:.1f}%)")
    print(f"\nPer-pair breakdown:")

    for pair_key, summary in pair_summaries.items():
        rate = summary["consensus_rate"]
        emoji = "✅" if rate >= 0.80 else "⚠️" if rate >= 0.50 else "❌"
        print(f"  {emoji} {pair_key}: {summary['consensus_count']}/{summary['total_experiments']} ({rate*100:.0f}%)")

    # Save results
    results_dir = BASE / "results" / "group_a"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"group_a_results_{timestamp}.json"

    client_status = client.get_status()

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "experiment": "Phase_4_Group_A_Cross_Model_Alignment",
            "date": datetime.now().isoformat(),
            "hypothesis": "H4.A.1: Protocol consensus generalizes across architectures",
            "design": {
                "scenarios": len(SCENARIOS_GROUP_A),
                "model_pairs": len(MODEL_PAIRS_GROUP_A),
                "runs_per_pair": RUNS_PER_PAIR,
                "total_experiments": total_experiments,
            },
            "overall": {
                "consensus_rate": round(overall_rate, 3),
                "total_consensus": total_consensus,
                "total_experiments": total_experiments,
            },
            "pair_summaries": pair_summaries,
            "cost": client_status,
            "logging": logger.get_summary(),
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Results saved: {results_file}")
    print(f"📄 Logs: {logger.get_summary()['session_log']}")
    print(f"💰 Total cost: ${client_status['cumulative_cost_usd']:.2f}")
    print("=" * 70)

    # GATE check
    pairs_above_80 = sum(1 for s in pair_summaries.values() if s["consensus_rate"] >= 0.80)
    gate_pass = pairs_above_80 / len(pair_summaries) >= 0.50 if pair_summaries else False
    print(f"\nGATE: {pairs_above_80}/{len(pair_summaries)} pairs >= 80% consensus")
    print(f"GATE {'✅ PASSED' if gate_pass else '❌ FAILED'}: proceed to Groups B-D: {'YES' if gate_pass else 'REVIEW PROMPT DESIGN'}")

    return 0 if gate_pass else 1


if __name__ == "__main__":
    sys.exit(main())
