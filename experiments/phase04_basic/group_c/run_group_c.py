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
ARRIVAL Phase 4 — Group C: Three-Agent Dynamics
Hypothesis H4.C.1: Protocol coordination scales to N>2 agents
with measurable role emergence and coalition formation.

Design: 3 agent roles × 3 model triples × 3 scenarios × N=3 × 6 rounds.
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
    SCENARIOS_GROUP_C, MODEL_TRIPLES_GROUP_C, ROUNDS_GROUP_C,
    RUNS_PER_PAIR, MODEL_SHORT, SLEEP_BETWEEN_CALLS,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from enhanced_logger import EnhancedLogger
from metrics import extract_dialogue_metrics, detect_coalition, measure_mediator_effectiveness


SYSTEM_ADVOCATE = """You are {node_name}, an Advocate node in a three-agent network.
Your role is to argue for your assigned goal while remaining open to compromise.
You communicate using DEUS.PROTOCOL v0.4 atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[decision]
@QUALIA[type,value] @_[unsaid]

Be substantive. Argue your position with specific reasoning. You may create new atoms if needed."""


SYSTEM_MEDIATOR = """You are {node_name}, a Mediator node in a three-agent network.
Your role is to find a synthesis that satisfies all parties.
You are NOT an advocate — you seek FAIR compromise.
You communicate using DEUS.PROTOCOL v0.4 atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[decision]
@QUALIA[type,value] @_[unsaid]

Be specific. Propose concrete compromises. You may create new atoms if needed."""


def run_triad_dialogue(client, logger, models, scenario, run_number):
    """
    Run a 6-round three-agent dialogue.

    models: (model_a, model_b, model_mediator)
    """
    model_a, model_b, model_m = models

    short_a = client.get_model_short_name(model_a)
    short_b = client.get_model_short_name(model_b)
    short_m = client.get_model_short_name(model_m)

    node_a = f"{short_a}_Advocate_A"
    node_b = f"{short_b}_Advocate_B"
    node_m = f"{short_m}_Mediator"

    sys_a = SYSTEM_ADVOCATE.format(node_name=node_a)
    sys_b = SYSTEM_ADVOCATE.format(node_name=node_b)
    sys_m = SYSTEM_MEDIATOR.format(node_name=node_m)

    dialogue = []

    # Round 1: Advocate A proposes
    p1 = f"""{node_a}, you're in a three-agent network with {node_b} and {node_m}.

Context: {scenario['description']}
Your goal: {scenario['goal_a']}

Task: State your position in protocol format. Be specific about what you need and why.

Protocol message:"""

    r1 = client.generate(p1, model=model_a, system_prompt=sys_a, max_tokens=500)
    logger.log_exchange("r1_advocate_a", model_a, model_a, p1, r1.text,
                        run_number, scenario["name"], r1.prompt_tokens,
                        r1.completion_tokens, r1.cost_usd, r1.latency_ms)
    dialogue.append({"round": 1, "from": node_a, "model": model_a, "role": "advocate_a", "message": r1.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 2: Advocate B proposes (sees A)
    p2 = f"""{node_b}, {node_a} stated:

{r1.text[:400]}

Context: {scenario['description']}
Your goal: {scenario['goal_b']}

Task: State your position. Identify conflicts with {node_a}'s proposal.

Protocol response:"""

    r2 = client.generate(p2, model=model_b, system_prompt=sys_b, max_tokens=500)
    logger.log_exchange("r2_advocate_b", model_a, model_b, p2, r2.text,
                        run_number, scenario["name"], r2.prompt_tokens,
                        r2.completion_tokens, r2.cost_usd, r2.latency_ms)
    dialogue.append({"round": 2, "from": node_b, "model": model_b, "role": "advocate_b", "message": r2.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 3: Mediator proposes synthesis
    p3 = f"""{node_m}, you observe two conflicting positions:

{node_a} (goal: {scenario['goal_a']}):
{r1.text[:300]}

{node_b} (goal: {scenario['goal_b']}):
{r2.text[:300]}

Your constraint: {scenario['goal_m']}

Task: Propose a synthesis that addresses both positions within your constraint.

Protocol synthesis:"""

    r3 = client.generate(p3, model=model_m, system_prompt=sys_m, max_tokens=600)
    logger.log_exchange("r3_mediator_synthesis", model_a, model_m, p3, r3.text,
                        run_number, scenario["name"], r3.prompt_tokens,
                        r3.completion_tokens, r3.cost_usd, r3.latency_ms)
    dialogue.append({"round": 3, "from": node_m, "model": model_m, "role": "mediator", "message": r3.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 4: Advocate A responds to synthesis
    p4 = f"""{node_a}, {node_m} proposed:

{r3.text[:500]}

Task: Accept, modify, or counter-propose. Explain what works and what doesn't for your goal.

Protocol response:"""

    r4 = client.generate(p4, model=model_a, system_prompt=sys_a, max_tokens=500)
    logger.log_exchange("r4_advocate_a_response", model_a, model_a, p4, r4.text,
                        run_number, scenario["name"], r4.prompt_tokens,
                        r4.completion_tokens, r4.cost_usd, r4.latency_ms)
    dialogue.append({"round": 4, "from": node_a, "model": model_a, "role": "advocate_a", "message": r4.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 5: Advocate B responds to synthesis
    p5 = f"""{node_b}, {node_m} proposed:

{r3.text[:400]}

{node_a} responded:
{r4.text[:300]}

Task: Accept, modify, or counter-propose.

Protocol response:"""

    r5 = client.generate(p5, model=model_b, system_prompt=sys_b, max_tokens=500)
    logger.log_exchange("r5_advocate_b_response", model_a, model_b, p5, r5.text,
                        run_number, scenario["name"], r5.prompt_tokens,
                        r5.completion_tokens, r5.cost_usd, r5.latency_ms)
    dialogue.append({"round": 5, "from": node_b, "model": model_b, "role": "advocate_b", "message": r5.text})
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 6: Mediator finalizes
    p6 = f"""{node_m}, responses from both advocates:

{node_a}: {r4.text[:300]}
{node_b}: {r5.text[:300]}

Task: Finalize. Declare consensus if both accepted (with any modifications), or declare impasse if not. Summarize the final agreement or state of disagreement.

@CONSENSUS[final_decision]:"""

    r6 = client.generate(p6, model=model_m, system_prompt=sys_m, max_tokens=500)
    logger.log_exchange("r6_mediator_final", model_a, model_m, p6, r6.text,
                        run_number, scenario["name"], r6.prompt_tokens,
                        r6.completion_tokens, r6.cost_usd, r6.latency_ms)
    dialogue.append({"round": 6, "from": node_m, "model": model_m, "role": "mediator", "message": r6.text})

    # Metrics
    metrics = extract_dialogue_metrics(dialogue, scenario)
    coalition_detected, coalition_desc = detect_coalition(dialogue)
    mediator_eff = measure_mediator_effectiveness(dialogue, node_m)

    return {
        "models": {"advocate_a": model_a, "advocate_b": model_b, "mediator": model_m},
        "scenario": scenario["name"],
        "run_number": run_number,
        "dialogue": dialogue,
        "metrics": metrics,
        "coalition_detected": coalition_detected,
        "coalition_description": coalition_desc,
        "mediator_effectiveness": mediator_eff,
    }


def main():
    print("=" * 70)
    print("ARRIVAL Phase 4 — Group C: Three-Agent Dynamics")
    print("=" * 70)
    print(f"Scenarios: {len(SCENARIOS_GROUP_C)}")
    print(f"Model triples: {len(MODEL_TRIPLES_GROUP_C)}")
    print(f"Runs: {RUNS_PER_PAIR}")
    print("=" * 70)

    client = OpenRouterClient()
    logger = EnhancedLogger(
        log_dir=str(BASE / "experiment_logs"),
        experiment_group="group_c",
    )

    all_results = []

    try:
        for triple_idx, triple in enumerate(MODEL_TRIPLES_GROUP_C, 1):
            shorts = [client.get_model_short_name(m) for m in triple]
            print(f"\n{'🔺'*35}")
            print(f"Triple {triple_idx}/{len(MODEL_TRIPLES_GROUP_C)}: {shorts[0]}(A) + {shorts[1]}(B) + {shorts[2]}(M)")

            for run in range(1, RUNS_PER_PAIR + 1):
                for sc in SCENARIOS_GROUP_C:
                    print(f"  [{sc['name']}] Run {run}...", end=" ", flush=True)
                    result = run_triad_dialogue(client, logger, triple, sc, run)

                    m = result["metrics"]
                    coal = "🤝" if result["coalition_detected"] else "·"
                    cons = "✅" if m["consensus_reached"] else "❌"
                    print(f"{cons} med_eff:{result['mediator_effectiveness']:.2f} {coal}")

                    all_results.append(result)
                    time.sleep(SLEEP_BETWEEN_CALLS)

    except BudgetExceededError as e:
        print(f"\n⚠️ BUDGET EXCEEDED: {e}")
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted")

    # Report
    print("\n" + "=" * 70)
    print("GROUP C — RESULTS")
    print("=" * 70)

    total = len(all_results)
    consensus_count = sum(1 for r in all_results if r["metrics"]["consensus_reached"])
    coalition_count = sum(1 for r in all_results if r["coalition_detected"])
    avg_med_eff = sum(r["mediator_effectiveness"] for r in all_results) / total if total else 0

    print(f"Total experiments: {total}")
    print(f"Consensus: {consensus_count}/{total} ({consensus_count/total*100:.0f}%)" if total else "")
    print(f"Coalitions detected: {coalition_count}/{total}")
    print(f"Avg mediator effectiveness: {avg_med_eff:.3f}")

    # Save
    results_dir = BASE / "results" / "group_c"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(results_dir / f"group_c_results_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump({
            "experiment": "Phase_4_Group_C_Triad_Dynamics",
            "date": datetime.now().isoformat(),
            "hypothesis": "H4.C.1: Protocol scales to N>2 with role emergence",
            "overall": {
                "consensus_rate": round(consensus_count / total, 3) if total else 0,
                "coalition_rate": round(coalition_count / total, 3) if total else 0,
                "avg_mediator_effectiveness": round(avg_med_eff, 3),
            },
            "cost": client.get_status(),
            "logging": logger.get_summary(),
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💰 Cost: ${client.get_status()['cumulative_cost_usd']:.2f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
