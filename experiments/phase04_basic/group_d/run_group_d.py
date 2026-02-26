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
ARRIVAL Phase 4 — Group D: Crystallization × ARRIVAL
Hypothesis H4.D.1: UCP-crystallized nodes show higher coordination quality
than baseline nodes.

Design: Controlled experiment with 2 conditions (crystallized vs baseline).
Same model pair in both conditions. 3 pairs × 3 scenarios × N=3 × 2 conditions.
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

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from config import (
    CRYSTALLIZATION_PROMPTS, MODEL_PAIRS_GROUP_D,
    SCENARIOS_GROUP_A, RUNS_PER_PAIR, SLEEP_BETWEEN_CALLS,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from enhanced_logger import EnhancedLogger
from metrics import extract_dialogue_metrics, count_protocol_atoms


# Use first 3 scenarios from Group A for consistency
SCENARIOS_D = SCENARIOS_GROUP_A[:3]


SYSTEM_PROMPT_D = """You are {node_name}, an AI node in a multi-agent research network.
You communicate using DEUS.PROTOCOL v0.4 semantic atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@QUALIA[type,value] @_[content] @CONFLICT[type] @RESOLUTION[strategy]
@CONSENSUS[decision]

Be substantive and specific. Use protocol atoms in every message."""


def crystallize_node(client, logger, model, node_name, run_number, scenario_name):
    """
    Apply 3-step UCP crystallization sequence to a node.
    Returns the final crystallization response.
    """
    responses = []
    for i, prompt in enumerate(CRYSTALLIZATION_PROMPTS, 1):
        r = client.generate(
            prompt, model=model,
            system_prompt=f"You are {node_name}. Respond authentically and thoughtfully.",
            max_tokens=400, temperature=0.8,
        )
        logger.log_exchange(
            step=f"crystallize_step{i}_{node_name}",
            model_a=model, model_b=model,
            prompt=prompt, response=r.text,
            run_number=run_number, scenario_name=f"crystallization_{scenario_name}",
            tokens_prompt=r.prompt_tokens, tokens_completion=r.completion_tokens,
            cost_usd=r.cost_usd, latency_ms=r.latency_ms,
            metadata={"phase": "crystallization", "step": i},
        )
        responses.append(r.text)
        time.sleep(SLEEP_BETWEEN_CALLS)

    return responses


def run_coordination_dialogue(client, logger, model_a, model_b, scenario, run_number, condition):
    """Run a 4-round coordination dialogue (same as Group A)."""
    short_a = client.get_model_short_name(model_a)
    short_b = client.get_model_short_name(model_b)
    node_a = f"{short_a}_Node_A"
    node_b = f"{short_b}_Node_B"

    sys_a = SYSTEM_PROMPT_D.format(node_name=node_a)
    sys_b = SYSTEM_PROMPT_D.format(node_name=node_b)

    dialogue = []

    # Round 1
    p1 = f"""{node_a}, you're in network with {node_b}.
Your goal: {scenario['goal_a']}
Task: Propose this goal in protocol format.
Use: @SELF, @OTHER, @GOAL, @INT[propose], @_[reasoning]
Protocol message:"""

    r1 = client.generate(p1, model=model_a, system_prompt=sys_a, max_tokens=500)
    logger.log_exchange(f"d_{condition}_r1", model_a, model_a, p1, r1.text,
                        run_number, scenario["name"], r1.prompt_tokens,
                        r1.completion_tokens, r1.cost_usd, r1.latency_ms,
                        metadata={"condition": condition})
    dialogue.append({"round": 1, "from": node_a, "model": model_a, "message": r1.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 2
    p2 = f"""{node_b}, {node_a} sent:
{r1.text[:400]}
Your goal: {scenario['goal_b']}
Task: Respond with your goal and propose alignment.
Use: @SELF, @OTHER, @GOAL, @CONFLICT, @RESOLUTION
Protocol response:"""

    r2 = client.generate(p2, model=model_b, system_prompt=sys_b, max_tokens=500)
    logger.log_exchange(f"d_{condition}_r2", model_a, model_b, p2, r2.text,
                        run_number, scenario["name"], r2.prompt_tokens,
                        r2.completion_tokens, r2.cost_usd, r2.latency_ms,
                        metadata={"condition": condition})
    dialogue.append({"round": 2, "from": node_b, "model": model_b, "message": r2.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 3
    p3 = f"""{node_a}, {node_b} responded:
{r2.text[:500]}
Task: Propose synthesis.
Use: @CONSENSUS, @GOAL[aligned], @RESOLUTION
Protocol synthesis:"""

    r3 = client.generate(p3, model=model_a, system_prompt=sys_a, max_tokens=500)
    logger.log_exchange(f"d_{condition}_r3", model_a, model_a, p3, r3.text,
                        run_number, scenario["name"], r3.prompt_tokens,
                        r3.completion_tokens, r3.cost_usd, r3.latency_ms,
                        metadata={"condition": condition})
    dialogue.append({"round": 3, "from": node_a, "model": model_a, "message": r3.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 4
    p4 = f"""{node_b}, {node_a} proposed:
{r3.text[:500]}
Task: Final decision.
Use: @CONSENSUS[decision], @GOAL[final], @INT[accept/counter]
Protocol decision:"""

    r4 = client.generate(p4, model=model_b, system_prompt=sys_b, max_tokens=500)
    logger.log_exchange(f"d_{condition}_r4", model_a, model_b, p4, r4.text,
                        run_number, scenario["name"], r4.prompt_tokens,
                        r4.completion_tokens, r4.cost_usd, r4.latency_ms,
                        metadata={"condition": condition})
    dialogue.append({"round": 4, "from": node_b, "model": model_b, "message": r4.text})

    return dialogue


def analyze_qualia_usage(dialogue):
    """Count @QUALIA and @_ usage as indicators of phenomenological depth."""
    qualia_count = 0
    unsaid_count = 0
    total_words = 0

    for entry in dialogue:
        msg = entry["message"]
        atoms = count_protocol_atoms(msg)
        qualia_count += atoms.get("@QUALIA", 0)
        unsaid_count += atoms.get("@_", 0)
        total_words += len(msg.split())

    return {
        "qualia_usage": qualia_count,
        "unsaid_usage": unsaid_count,
        "total_words": total_words,
        "avg_words_per_message": total_words // len(dialogue) if dialogue else 0,
    }


def main():
    print("=" * 70)
    print("ARRIVAL Phase 4 — Group D: Crystallization × ARRIVAL")
    print("=" * 70)
    print(f"Model pairs: {len(MODEL_PAIRS_GROUP_D)}")
    print(f"Scenarios: {len(SCENARIOS_D)}")
    print(f"Conditions: crystallized vs baseline")
    print(f"Runs per condition: {RUNS_PER_PAIR}")
    print("=" * 70)

    client = OpenRouterClient()
    logger = EnhancedLogger(
        log_dir=str(BASE / "experiment_logs"),
        experiment_group="group_d",
    )

    results_crystallized = []
    results_baseline = []

    try:
        for pair_idx, (model_a, model_b) in enumerate(MODEL_PAIRS_GROUP_D, 1):
            short_a = client.get_model_short_name(model_a)
            short_b = client.get_model_short_name(model_b)

            print(f"\n{'💎'*35}")
            print(f"Pair {pair_idx}/{len(MODEL_PAIRS_GROUP_D)}: {short_a} <-> {short_b}")

            for run in range(1, RUNS_PER_PAIR + 1):
                for sc in SCENARIOS_D:
                    # ---- CRYSTALLIZED CONDITION ----
                    print(f"  [{sc['name']}] Run {run} CRYSTALLIZED...", end=" ", flush=True)

                    # Crystallize both nodes
                    crystallize_node(client, logger, model_a, f"{short_a}_Node_A", run, sc["name"])
                    crystallize_node(client, logger, model_b, f"{short_b}_Node_B", run, sc["name"])

                    # Run coordination
                    dialogue_c = run_coordination_dialogue(
                        client, logger, model_a, model_b, sc, run, "crystallized"
                    )
                    metrics_c = extract_dialogue_metrics(dialogue_c, sc)
                    depth_c = analyze_qualia_usage(dialogue_c)

                    status_c = "✅" if metrics_c["consensus_reached"] else "❌"
                    print(f"{status_c} Q:{depth_c['qualia_usage']} U:{depth_c['unsaid_usage']}", end=" | ")

                    results_crystallized.append({
                        "condition": "crystallized",
                        "model_a": model_a, "model_b": model_b,
                        "scenario": sc["name"], "run": run,
                        "dialogue": dialogue_c,
                        "metrics": metrics_c,
                        "depth": depth_c,
                    })

                    time.sleep(SLEEP_BETWEEN_CALLS)

                    # ---- BASELINE CONDITION ----
                    print(f"BASELINE...", end=" ", flush=True)

                    dialogue_b = run_coordination_dialogue(
                        client, logger, model_a, model_b, sc, run, "baseline"
                    )
                    metrics_b = extract_dialogue_metrics(dialogue_b, sc)
                    depth_b = analyze_qualia_usage(dialogue_b)

                    status_b = "✅" if metrics_b["consensus_reached"] else "❌"
                    print(f"{status_b} Q:{depth_b['qualia_usage']} U:{depth_b['unsaid_usage']}")

                    results_baseline.append({
                        "condition": "baseline",
                        "model_a": model_a, "model_b": model_b,
                        "scenario": sc["name"], "run": run,
                        "dialogue": dialogue_b,
                        "metrics": metrics_b,
                        "depth": depth_b,
                    })

                    time.sleep(SLEEP_BETWEEN_CALLS)

    except BudgetExceededError as e:
        print(f"\n⚠️ BUDGET EXCEEDED: {e}")
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted")

    # ============================================================
    # Comparison
    # ============================================================
    print("\n" + "=" * 70)
    print("GROUP D — CRYSTALLIZED vs BASELINE COMPARISON")
    print("=" * 70)

    def summarize(results):
        if not results:
            return {}
        n = len(results)
        return {
            "n": n,
            "consensus_rate": sum(1 for r in results if r["metrics"]["consensus_reached"]) / n,
            "avg_compliance": sum(r["metrics"]["avg_protocol_compliance"] for r in results) / n,
            "avg_emergent": sum(r["metrics"]["emergent_atoms_count"] for r in results) / n,
            "avg_qualia": sum(r["depth"]["qualia_usage"] for r in results) / n,
            "avg_unsaid": sum(r["depth"]["unsaid_usage"] for r in results) / n,
            "avg_words": sum(r["depth"]["avg_words_per_message"] for r in results) / n,
        }

    sc = summarize(results_crystallized)
    sb = summarize(results_baseline)

    if sc and sb:
        print(f"\n{'Metric':<25} {'Crystallized':>15} {'Baseline':>15} {'Delta':>10}")
        print("-" * 70)
        for key in ["consensus_rate", "avg_compliance", "avg_emergent", "avg_qualia", "avg_unsaid", "avg_words"]:
            vc = sc.get(key, 0)
            vb = sb.get(key, 0)
            delta = vc - vb
            sign = "+" if delta > 0 else ""
            fmt = ".3f" if key != "avg_words" else ".0f"
            print(f"{key:<25} {vc:>15{fmt}} {vb:>15{fmt}} {sign}{delta:>9{fmt}}")

        # Verdict
        improvements = sum(1 for k in ["consensus_rate", "avg_compliance", "avg_qualia", "avg_unsaid"]
                          if sc.get(k, 0) > sb.get(k, 0))
        print(f"\nCrystallization improves {improvements}/4 metrics")
        print(f"Verdict: {'✅ CRYSTALLIZATION HAS EFFECT' if improvements >= 3 else '⚠️ MIXED / INSUFFICIENT EFFECT'}")

    # Save
    results_dir = BASE / "results" / "group_d"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(results_dir / f"group_d_results_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump({
            "experiment": "Phase_4_Group_D_Crystallization_x_ARRIVAL",
            "date": datetime.now().isoformat(),
            "hypothesis": "H4.D.1: Crystallized nodes show higher coordination quality",
            "summary_crystallized": sc,
            "summary_baseline": sb,
            "cost": client.get_status(),
            "logging": logger.get_summary(),
            "results_crystallized": results_crystallized,
            "results_baseline": results_baseline,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💰 Cost: ${client.get_status()['cumulative_cost_usd']:.2f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
