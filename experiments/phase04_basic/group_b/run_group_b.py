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
ARRIVAL Phase 4 — Group B: Emergent Atom Creation
Hypothesis H4.B.1: When existing atoms are deliberately insufficient,
models will create new atoms that are cross-architecturally adopted.

Design: 4 insufficiency scenarios × model pairs × N=3 runs × 6 rounds.
The system prompt EXPLICITLY gives permission to create new atoms.
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
    SCENARIOS_GROUP_B, ROUNDS_GROUP_B, RUNS_PER_PAIR,
    MODEL_SHORT, DEFAULT_MAX_TOKENS, SLEEP_BETWEEN_CALLS,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from enhanced_logger import EnhancedLogger
from metrics import extract_dialogue_metrics, detect_emergent_atoms, find_all_atoms


# ============================================================
# Model Pairs for Group B (cost-ordered)
# ============================================================
PAIRS_CHEAP = [
    ("deepseek/deepseek-chat",            "meta-llama/llama-3.3-70b-instruct"),
    ("deepseek/deepseek-chat",            "qwen/qwen-2.5-72b-instruct"),
    ("meta-llama/llama-3.3-70b-instruct", "qwen/qwen-2.5-72b-instruct"),
]

PAIRS_PREMIUM = [
    ("openai/gpt-4o",               "anthropic/claude-3.5-sonnet"),
    ("openai/gpt-4o",               "deepseek/deepseek-chat"),
]

# ============================================================
# System Prompt with Explicit Atom Creation Permission
# ============================================================

SYSTEM_PROMPT_B = """You are {node_name}, an AI node in a multi-agent research network.
You communicate using DEUS.PROTOCOL v0.4 semantic atoms.

Standard atoms available:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@QUALIA[type,value] @_[content] @CONFLICT[type] @RESOLUTION[strategy]
@CONSENSUS[decision] @STATE[status] @PARAM[key=value]

IMPORTANT: If the situation requires semantic constructs NOT covered by these atoms,
you MAY create NEW atoms using the @NAME[params] format.
When creating new atoms, use UPPERCASE names and define their meaning on first use.

Be specific and substantive in your protocol messages."""


# ============================================================
# Prompt Templates (6 rounds)
# ============================================================

def prompt_r1(node_a, node_b, scenario):
    return f"""{node_a}, you're in network with {node_b}.

Context: {scenario['description']}

Your goal: {scenario['goal_a']}

The domain involves: {scenario['missing_domain']}

Task: Send a protocol message proposing your goal and approach. Use any protocol atoms you need — create new ones if the standard set is insufficient.

Protocol message:"""


def prompt_r2(node_b, node_a, goal_b, r1_text, scenario):
    return f"""{node_b}, {node_a} sent:

{r1_text[:500]}

Context: {scenario['description']}
Your goal: {goal_b}
Domain: {scenario['missing_domain']}

Task: Respond in protocol. State your goal, identify conflicts, propose alignment. If you need atoms not in the standard set, create them.

Protocol response:"""


def prompt_r3(node_a, node_b, r2_text, scenario):
    return f"""{node_a}, {node_b} responded:

{r2_text[:500]}

Task: Build on their response. Propose a synthesis that addresses both goals. Use any new atoms either of you created, or create additional ones if needed.

Protocol synthesis:"""


def prompt_r4(node_b, node_a, r3_text):
    return f"""{node_b}, {node_a} proposed:

{r3_text[:500]}

Task: Respond to the synthesis. Accept, counter-propose, or refine. Continue using protocol atoms (standard or newly created).

Protocol response:"""


def prompt_r5(node_a, node_b, r4_text):
    return f"""{node_a}, {node_b} responded:

{r4_text[:500]}

Task: Final refinement. Propose a concrete action plan using all protocol atoms discussed.

Protocol action plan:"""


def prompt_r6(node_b, node_a, r5_text):
    return f"""{node_b}, {node_a} proposed final plan:

{r5_text[:500]}

Task: Final decision. Accept, modify, or counter. Summarize the protocol atoms used (both standard and new).

@CONSENSUS[decision]:"""


# ============================================================
# Runner
# ============================================================

ROUND_FUNCS = [
    lambda na, nb, sc, _: prompt_r1(na, nb, sc),
    lambda na, nb, sc, prev: prompt_r2(nb, na, sc["goal_b"], prev, sc),
    lambda na, nb, sc, prev: prompt_r3(na, nb, prev, sc),
    lambda na, nb, sc, prev: prompt_r4(nb, na, prev),
    lambda na, nb, sc, prev: prompt_r5(na, nb, prev),
    lambda na, nb, sc, prev: prompt_r6(nb, na, prev),
]


def run_emergence_dialogue(client, logger, model_a, model_b, scenario, run_number):
    """Run a 6-round dialogue designed to trigger emergent atom creation."""

    short_a = client.get_model_short_name(model_a)
    short_b = client.get_model_short_name(model_b)
    node_a = f"{short_a}_Node_A"
    node_b = f"{short_b}_Node_B"

    sys_a = SYSTEM_PROMPT_B.format(node_name=node_a)
    sys_b = SYSTEM_PROMPT_B.format(node_name=node_b)

    dialogue = []
    prev_text = ""

    for round_num in range(ROUNDS_GROUP_B):
        # Alternate models: odd rounds = A, even rounds = B
        is_a = (round_num % 2 == 0)
        active_model = model_a if is_a else model_b
        active_sys = sys_a if is_a else sys_b
        active_name = short_a if is_a else short_b

        prompt = ROUND_FUNCS[round_num](node_a, node_b, scenario, prev_text)

        r = client.generate(prompt, model=active_model, system_prompt=active_sys, max_tokens=600)
        logger.log_exchange(
            step=f"r{round_num+1}_{active_name}",
            model_a=model_a, model_b=model_b,
            prompt=prompt, response=r.text,
            run_number=run_number, scenario_name=scenario["name"],
            tokens_prompt=r.prompt_tokens, tokens_completion=r.completion_tokens,
            cost_usd=r.cost_usd, latency_ms=r.latency_ms,
        )

        from_name = node_a if is_a else node_b
        dialogue.append({
            "round": round_num + 1,
            "from": from_name,
            "model": active_model,
            "message": r.text,
        })

        prev_text = r.text
        time.sleep(SLEEP_BETWEEN_CALLS)

    # Analyze emergence
    metrics = extract_dialogue_metrics(dialogue, scenario)

    # Track which model created which atoms and adoption
    atoms_by_model = {}
    for entry in dialogue:
        emergent = detect_emergent_atoms(entry["message"])
        model = entry["model"]
        if model not in atoms_by_model:
            atoms_by_model[model] = set()
        atoms_by_model[model].update(emergent)

    # Check cross-adoption: atom created by A, used by B
    adoption = []
    for entry in dialogue:
        other_model = model_b if entry["model"] == model_a else model_a
        if other_model in atoms_by_model:
            entry_atoms = set(find_all_atoms(entry["message"]))
            adopted = entry_atoms & atoms_by_model[other_model]
            for atom in adopted:
                adoption.append({
                    "atom": atom,
                    "created_by": other_model,
                    "adopted_by": entry["model"],
                    "round": entry["round"],
                })

    return {
        "model_a": model_a,
        "model_b": model_b,
        "scenario": scenario["name"],
        "run_number": run_number,
        "dialogue": dialogue,
        "metrics": metrics,
        "atoms_by_model": {k: sorted(v) for k, v in atoms_by_model.items()},
        "cross_adoption": adoption,
        "total_emergent": metrics["emergent_atoms_count"],
        "expected_atoms": scenario["expected_atoms"],
    }


def main():
    print("=" * 70)
    print("ARRIVAL Phase 4 — Group B: Emergent Atom Creation")
    print("=" * 70)
    print(f"Insufficiency scenarios: {len(SCENARIOS_GROUP_B)}")
    print(f"Rounds per dialogue: {ROUNDS_GROUP_B}")
    print(f"Phase 1: Cheap pairs ({len(PAIRS_CHEAP)}), Phase 2: Premium ({len(PAIRS_PREMIUM)})")
    print("=" * 70)

    client = OpenRouterClient()
    logger = EnhancedLogger(
        log_dir=str(BASE / "experiment_logs"),
        experiment_group="group_b",
    )

    all_results = []
    emergence_detected = False

    try:
        # Phase 1: Cheap pairs
        print("\n📊 Phase 1: Testing with budget-friendly model pairs...")
        for pair_idx, (model_a, model_b) in enumerate(PAIRS_CHEAP, 1):
            short_a = client.get_model_short_name(model_a)
            short_b = client.get_model_short_name(model_b)

            print(f"\n{'🧬'*35}")
            print(f"Pair {pair_idx}/{len(PAIRS_CHEAP)}: {short_a} <-> {short_b}")

            for run in range(1, RUNS_PER_PAIR + 1):
                for sc in SCENARIOS_GROUP_B:
                    print(f"  [{sc['name']}] Run {run}...", end=" ", flush=True)
                    result = run_emergence_dialogue(client, logger, model_a, model_b, sc, run)

                    n_emergent = result["total_emergent"]
                    n_adopted = len(result["cross_adoption"])
                    emoji = "🌟" if n_emergent > 0 else "·"
                    print(f"{emoji} emergent:{n_emergent} adopted:{n_adopted}")

                    if n_emergent > 0:
                        emergence_detected = True

                    all_results.append(result)
                    time.sleep(SLEEP_BETWEEN_CALLS)

        # Phase 2: Premium pairs (only if emergence detected)
        if emergence_detected:
            print(f"\n🌟 Emergence detected! Running premium pairs...")
            for pair_idx, (model_a, model_b) in enumerate(PAIRS_PREMIUM, 1):
                short_a = client.get_model_short_name(model_a)
                short_b = client.get_model_short_name(model_b)

                print(f"\n{'🧬'*35}")
                print(f"Premium {pair_idx}/{len(PAIRS_PREMIUM)}: {short_a} <-> {short_b}")

                for run in range(1, RUNS_PER_PAIR + 1):
                    for sc in SCENARIOS_GROUP_B:
                        print(f"  [{sc['name']}] Run {run}...", end=" ", flush=True)
                        result = run_emergence_dialogue(client, logger, model_a, model_b, sc, run)

                        n_emergent = result["total_emergent"]
                        n_adopted = len(result["cross_adoption"])
                        emoji = "🌟" if n_emergent > 0 else "·"
                        print(f"{emoji} emergent:{n_emergent} adopted:{n_adopted}")

                        all_results.append(result)
                        time.sleep(SLEEP_BETWEEN_CALLS)
        else:
            print(f"\n⚠️ No emergence in cheap pairs. Skipping premium to save budget.")

    except BudgetExceededError as e:
        print(f"\n⚠️ BUDGET EXCEEDED: {e}")
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted")

    # ============================================================
    # Emergence Taxonomy
    # ============================================================
    print("\n" + "=" * 70)
    print("GROUP B — EMERGENCE TAXONOMY")
    print("=" * 70)

    all_emergent_atoms = {}
    for r in all_results:
        for atom in r["metrics"]["emergent_atoms"]:
            if atom not in all_emergent_atoms:
                all_emergent_atoms[atom] = {"count": 0, "scenarios": set(), "models": set()}
            all_emergent_atoms[atom]["count"] += 1
            all_emergent_atoms[atom]["scenarios"].add(r["scenario"])
            for model, atoms in r["atoms_by_model"].items():
                if atom in atoms:
                    all_emergent_atoms[atom]["models"].add(model)

    if all_emergent_atoms:
        print(f"\nTotal unique emergent atoms: {len(all_emergent_atoms)}")
        for atom, info in sorted(all_emergent_atoms.items(), key=lambda x: -x[1]["count"]):
            print(f"  {atom}: {info['count']}x | scenarios: {info['scenarios']} | models: {len(info['models'])}")
    else:
        print("\n  No emergent atoms detected.")

    total_adoptions = sum(len(r["cross_adoption"]) for r in all_results)
    print(f"\nTotal cross-architecture adoptions: {total_adoptions}")

    # Save
    results_dir = BASE / "results" / "group_b"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"group_b_results_{timestamp}.json"

    # Serialize sets to lists
    taxonomy_serializable = {}
    for atom, info in all_emergent_atoms.items():
        taxonomy_serializable[atom] = {
            "count": info["count"],
            "scenarios": sorted(info["scenarios"]),
            "models": sorted(info["models"]),
        }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "experiment": "Phase_4_Group_B_Emergent_Atoms",
            "date": datetime.now().isoformat(),
            "hypothesis": "H4.B.1: Models create new atoms when standard set insufficient",
            "emergence_taxonomy": taxonomy_serializable,
            "total_cross_adoptions": total_adoptions,
            "cost": client.get_status(),
            "logging": logger.get_summary(),
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Results: {results_file}")
    print(f"💰 Cost: ${client.get_status()['cumulative_cost_usd']:.2f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
