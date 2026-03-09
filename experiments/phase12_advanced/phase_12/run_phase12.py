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
Arrival CRDT — Phase 12: Bottleneck Communication

Two subgroups (2 agents each) negotiate separately, connected by a RELAY agent.
The relay compresses information between subgroups (max 200 words), testing
how ARRIVAL Protocol atoms survive lossy compression.

Design:
  Subgroup A: 2 agents do 2 rounds of internal negotiation
  Relay: receives Subgroup A's summary, compresses to max 200 words
  Subgroup B: receives compressed summary, does 2 rounds
  Relay: sends Subgroup B's response back to Subgroup A
  Final round: both subgroups respond to each other via relay

  Scenarios: Distributed resource allocation | Cross-team methodology
  Models: DeepSeek + Llama (Subgroup A) | Qwen + Gemini (Subgroup B) | Mistral (Relay)

Experiments: 2 scenarios x 2 runs = 4 total

Key metrics:
  - information_loss: atom count before/after relay compression
  - care_resolve: per subgroup and combined
  - meaning_debt: per subgroup and combined
"""

import sys
import os
import json
import re
import time
from datetime import datetime

# Windows encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    MODEL_SHORT, SLEEP_BETWEEN_CALLS, MAX_COST_USD,
    PHASE12_SUBGROUP_A, PHASE12_SUBGROUP_B, PHASE12_RELAY,
    PHASE12_SCENARIOS, PHASE12_ROUNDS_PER_SUBGROUP, PHASE12_RELAY_ROUNDS,
    PHASE12_RUNS, PHASE12_TEMPERATURE, PHASE12_MAX_TOKENS,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from enhanced_logger import EnhancedLogger
from crdt_metrics import compute_care_resolve, compute_meaning_debt


# ============================================================
# System Prompts
# ============================================================

SYSTEM_SUBGROUP_AGENT = """You are {node_name}, a member of {subgroup_name} in a multi-agent network.
Your subgroup is negotiating internally before connecting with another subgroup via a relay agent.
You communicate using DEUS.PROTOCOL v0.4 atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[decision]
@QUALIA[type,value] @_[unsaid]

Be substantive. Use @-atoms to mark key positions, conflicts, and proposals.
When responding to the other subgroup's compressed summary, pay special attention to
@-atoms that survived relay compression — they carry the most critical information."""

SYSTEM_RELAY = """You are {node_name}, a RELAY agent bridging two subgroups.
{relay_instruction}

CRITICAL CONSTRAINTS:
1. Your compression MUST be 200 words or fewer
2. Preserve ALL @-atoms from the original (they are the protocol's information backbone)
3. Preserve numerical values and specific positions
4. Remove redundancy and filler, but keep substance
5. Clearly label which subgroup the summary comes from

You communicate using DEUS.PROTOCOL v0.4 atoms.
Your role is PURE relay — do NOT advocate for any position."""


# ============================================================
# Helpers
# ============================================================

def count_atoms(text):
    """Count unique @-atoms in a text."""
    atoms = set(re.findall(r'@[A-Z_]+(?:\[[^\]]*\])?', text))
    return len(atoms), atoms


def compute_information_loss(original_text, compressed_text):
    """Measure information loss through relay compression."""
    orig_count, orig_atoms = count_atoms(original_text)
    comp_count, comp_atoms = count_atoms(compressed_text)

    # Atoms that survived compression
    orig_atom_names = {re.match(r'(@[A-Z_]+)', a).group(1) for a in orig_atoms if re.match(r'(@[A-Z_]+)', a)}
    comp_atom_names = {re.match(r'(@[A-Z_]+)', a).group(1) for a in comp_atoms if re.match(r'(@[A-Z_]+)', a)}

    survived = orig_atom_names & comp_atom_names
    lost = orig_atom_names - comp_atom_names
    added = comp_atom_names - orig_atom_names

    # Word count
    orig_words = len(original_text.split())
    comp_words = len(compressed_text.split())
    compression_ratio = comp_words / orig_words if orig_words > 0 else 0

    return {
        "original_atom_count": orig_count,
        "compressed_atom_count": comp_count,
        "original_unique_atoms": len(orig_atom_names),
        "compressed_unique_atoms": len(comp_atom_names),
        "survived_atoms": sorted(survived),
        "lost_atoms": sorted(lost),
        "added_atoms": sorted(added),
        "atom_survival_rate": len(survived) / len(orig_atom_names) if orig_atom_names else 1.0,
        "original_words": orig_words,
        "compressed_words": comp_words,
        "compression_ratio": round(compression_ratio, 3),
    }


# ============================================================
# Dialogue Runner
# ============================================================

def run_bottleneck_dialogue(client, logger, scenario, run_number):
    """
    Run bottleneck communication experiment.

    Flow:
    1. Subgroup A internal negotiation (2 rounds)
    2. Relay compresses Subgroup A's output (max 200 words)
    3. Subgroup B internal negotiation (2 rounds, starting from relay summary)
    4. Relay compresses Subgroup B's response back
    5. Final round: both subgroups respond via relay
    """
    # Model assignments
    model_a1 = PHASE12_SUBGROUP_A[0]
    model_a2 = PHASE12_SUBGROUP_A[1]
    model_b1 = PHASE12_SUBGROUP_B[0]
    model_b2 = PHASE12_SUBGROUP_B[1]
    model_relay = PHASE12_RELAY

    short_a1 = MODEL_SHORT.get(model_a1, model_a1)
    short_a2 = MODEL_SHORT.get(model_a2, model_a2)
    short_b1 = MODEL_SHORT.get(model_b1, model_b1)
    short_b2 = MODEL_SHORT.get(model_b2, model_b2)
    short_relay = MODEL_SHORT.get(model_relay, model_relay)

    node_a1 = f"{short_a1}_SubA_1"
    node_a2 = f"{short_a2}_SubA_2"
    node_b1 = f"{short_b1}_SubB_1"
    node_b2 = f"{short_b2}_SubB_2"
    node_relay = f"{short_relay}_Relay"

    sys_a1 = SYSTEM_SUBGROUP_AGENT.format(node_name=node_a1, subgroup_name="Subgroup A")
    sys_a2 = SYSTEM_SUBGROUP_AGENT.format(node_name=node_a2, subgroup_name="Subgroup A")
    sys_b1 = SYSTEM_SUBGROUP_AGENT.format(node_name=node_b1, subgroup_name="Subgroup B")
    sys_b2 = SYSTEM_SUBGROUP_AGENT.format(node_name=node_b2, subgroup_name="Subgroup B")
    sys_relay = SYSTEM_RELAY.format(node_name=node_relay, relay_instruction=scenario["relay_instruction"])

    dialogue_a = []  # Subgroup A internal dialogue
    dialogue_b = []  # Subgroup B internal dialogue
    relay_log = []   # Relay compressions
    full_dialogue = []  # Combined for CRDT metrics

    info_loss_records = []

    # ============================================================
    # PHASE 1: Subgroup A Internal Negotiation (2 rounds)
    # ============================================================
    print("(SubA", end="", flush=True)

    # SubA Round 1: Agent A1 proposes
    p_a1_r1 = f"""{node_a1}, you're in Subgroup A with {node_a2}.
Your subgroup's goal: {scenario['subgroup_a_goal']}
Context: Your subgroup will later connect with Subgroup B (goal: {scenario['subgroup_b_goal']}) through a relay agent.
Task: State your initial position in protocol format.
Protocol message:"""
    r_a1_r1 = client.generate(p_a1_r1, model=model_a1, system_prompt=sys_a1,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_a1_r1 = {"round": 1, "phase": "subgroup_a", "from": node_a1, "model": model_a1, "message": r_a1_r1.text}
    dialogue_a.append(msg_a1_r1)
    full_dialogue.append(msg_a1_r1)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # SubA Round 1: Agent A2 responds
    p_a2_r1 = f"""{node_a2}, your teammate {node_a1} stated:
{r_a1_r1.text[:400]}
Your subgroup's goal: {scenario['subgroup_a_goal']}
Task: Respond. Refine the position, identify gaps, propose improvements.
Protocol response:"""
    r_a2_r1 = client.generate(p_a2_r1, model=model_a2, system_prompt=sys_a2,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_a2_r1 = {"round": 1, "phase": "subgroup_a", "from": node_a2, "model": model_a2, "message": r_a2_r1.text}
    dialogue_a.append(msg_a2_r1)
    full_dialogue.append(msg_a2_r1)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # SubA Round 2: Agent A1 synthesizes
    p_a1_r2 = f"""{node_a1}, {node_a2} responded:
{r_a2_r1.text[:400]}
Task: Synthesize your subgroup's position for relay to Subgroup B.
Include key @-atoms that capture your subgroup's essential positions.
Protocol synthesis:"""
    r_a1_r2 = client.generate(p_a1_r2, model=model_a1, system_prompt=sys_a1,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_a1_r2 = {"round": 2, "phase": "subgroup_a", "from": node_a1, "model": model_a1, "message": r_a1_r2.text}
    dialogue_a.append(msg_a1_r2)
    full_dialogue.append(msg_a1_r2)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # SubA Round 2: Agent A2 confirms/amends
    p_a2_r2 = f"""{node_a2}, {node_a1} proposed this synthesis for relay:
{r_a1_r2.text[:400]}
Task: Confirm or amend. This will be sent via relay to Subgroup B.
Protocol response:"""
    r_a2_r2 = client.generate(p_a2_r2, model=model_a2, system_prompt=sys_a2,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_a2_r2 = {"round": 2, "phase": "subgroup_a", "from": node_a2, "model": model_a2, "message": r_a2_r2.text}
    dialogue_a.append(msg_a2_r2)
    full_dialogue.append(msg_a2_r2)
    time.sleep(SLEEP_BETWEEN_CALLS)
    print(")", end=" ", flush=True)

    # Combine Subgroup A's final output for relay
    subgroup_a_output = f"""Subgroup A synthesis:
{node_a1}: {r_a1_r2.text}
{node_a2}: {r_a2_r2.text}"""

    # ============================================================
    # PHASE 2: Relay Compresses Subgroup A -> Subgroup B
    # ============================================================
    print("(Relay->B", end="", flush=True)

    p_relay_ab = f"""{node_relay}, Subgroup A has completed their internal negotiation.
Their combined output:
{subgroup_a_output[:800]}

Task: Compress Subgroup A's position into MAX 200 words for Subgroup B.
Preserve ALL @-atoms and key numerical positions. Remove redundancy.
Compressed summary for Subgroup B:"""
    r_relay_ab = client.generate(p_relay_ab, model=model_relay, system_prompt=sys_relay,
                                  temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)

    relay_ab_entry = {
        "direction": "A_to_B",
        "from": node_relay,
        "model": model_relay,
        "original_length": len(subgroup_a_output.split()),
        "compressed": r_relay_ab.text,
        "compressed_length": len(r_relay_ab.text.split()),
    }
    relay_log.append(relay_ab_entry)
    full_dialogue.append({"round": 3, "phase": "relay_a_to_b", "from": node_relay, "model": model_relay, "message": r_relay_ab.text})

    # Compute information loss A->B
    info_loss_ab = compute_information_loss(subgroup_a_output, r_relay_ab.text)
    info_loss_records.append({"direction": "A_to_B", **info_loss_ab})
    time.sleep(SLEEP_BETWEEN_CALLS)
    print(")", end=" ", flush=True)

    # ============================================================
    # PHASE 3: Subgroup B Internal Negotiation (2 rounds)
    # ============================================================
    print("(SubB", end="", flush=True)

    # SubB Round 1: Agent B1 receives relay and responds
    p_b1_r1 = f"""{node_b1}, you're in Subgroup B with {node_b2}.
Your subgroup's goal: {scenario['subgroup_b_goal']}
You received this compressed summary from Subgroup A (via relay):
{r_relay_ab.text[:500]}
Task: State your position in response. Identify @CONFLICT and @CONSENSUS points.
Protocol message:"""
    r_b1_r1 = client.generate(p_b1_r1, model=model_b1, system_prompt=sys_b1,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_b1_r1 = {"round": 1, "phase": "subgroup_b", "from": node_b1, "model": model_b1, "message": r_b1_r1.text}
    dialogue_b.append(msg_b1_r1)
    full_dialogue.append(msg_b1_r1)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # SubB Round 1: Agent B2 responds
    p_b2_r1 = f"""{node_b2}, your teammate {node_b1} stated:
{r_b1_r1.text[:400]}
Relay from Subgroup A:
{r_relay_ab.text[:300]}
Your subgroup's goal: {scenario['subgroup_b_goal']}
Task: Respond. Refine the position, propose compromises with Subgroup A.
Protocol response:"""
    r_b2_r1 = client.generate(p_b2_r1, model=model_b2, system_prompt=sys_b2,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_b2_r1 = {"round": 1, "phase": "subgroup_b", "from": node_b2, "model": model_b2, "message": r_b2_r1.text}
    dialogue_b.append(msg_b2_r1)
    full_dialogue.append(msg_b2_r1)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # SubB Round 2: Agent B1 synthesizes
    p_b1_r2 = f"""{node_b1}, {node_b2} responded:
{r_b2_r1.text[:400]}
Task: Synthesize your subgroup's response for relay back to Subgroup A.
Include key @-atoms and specific proposals for cross-group resolution.
Protocol synthesis:"""
    r_b1_r2 = client.generate(p_b1_r2, model=model_b1, system_prompt=sys_b1,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_b1_r2 = {"round": 2, "phase": "subgroup_b", "from": node_b1, "model": model_b1, "message": r_b1_r2.text}
    dialogue_b.append(msg_b1_r2)
    full_dialogue.append(msg_b1_r2)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # SubB Round 2: Agent B2 confirms/amends
    p_b2_r2 = f"""{node_b2}, {node_b1} proposed this synthesis for relay:
{r_b1_r2.text[:400]}
Task: Confirm or amend. This will be sent back to Subgroup A via relay.
Protocol response:"""
    r_b2_r2 = client.generate(p_b2_r2, model=model_b2, system_prompt=sys_b2,
                               temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_b2_r2 = {"round": 2, "phase": "subgroup_b", "from": node_b2, "model": model_b2, "message": r_b2_r2.text}
    dialogue_b.append(msg_b2_r2)
    full_dialogue.append(msg_b2_r2)
    time.sleep(SLEEP_BETWEEN_CALLS)
    print(")", end=" ", flush=True)

    # Combine Subgroup B's final output for relay
    subgroup_b_output = f"""Subgroup B response:
{node_b1}: {r_b1_r2.text}
{node_b2}: {r_b2_r2.text}"""

    # ============================================================
    # PHASE 4: Relay Compresses Subgroup B -> Subgroup A
    # ============================================================
    print("(Relay->A", end="", flush=True)

    p_relay_ba = f"""{node_relay}, Subgroup B has responded to Subgroup A's position.
Their combined output:
{subgroup_b_output[:800]}

Task: Compress Subgroup B's response into MAX 200 words for Subgroup A.
Preserve ALL @-atoms and key numerical positions. Remove redundancy.
Compressed summary for Subgroup A:"""
    r_relay_ba = client.generate(p_relay_ba, model=model_relay, system_prompt=sys_relay,
                                  temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)

    relay_ba_entry = {
        "direction": "B_to_A",
        "from": node_relay,
        "model": model_relay,
        "original_length": len(subgroup_b_output.split()),
        "compressed": r_relay_ba.text,
        "compressed_length": len(r_relay_ba.text.split()),
    }
    relay_log.append(relay_ba_entry)
    full_dialogue.append({"round": 5, "phase": "relay_b_to_a", "from": node_relay, "model": model_relay, "message": r_relay_ba.text})

    # Compute information loss B->A
    info_loss_ba = compute_information_loss(subgroup_b_output, r_relay_ba.text)
    info_loss_records.append({"direction": "B_to_A", **info_loss_ba})
    time.sleep(SLEEP_BETWEEN_CALLS)
    print(")", end=" ", flush=True)

    # ============================================================
    # PHASE 5: Final Round — Both Subgroups Respond via Relay
    # ============================================================
    print("(Final", end="", flush=True)

    # Subgroup A final response (seeing B's compressed position)
    p_a_final = f"""{node_a1}, Subgroup B responded (via relay):
{r_relay_ba.text[:500]}
Your subgroup's previous position:
{r_a1_r2.text[:300]}
Task: Final response. Declare @CONSENSUS or @CONFLICT with Subgroup B's position.
Protocol response:"""
    r_a_final = client.generate(p_a_final, model=model_a1, system_prompt=sys_a1,
                                 temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_a_final = {"round": 6, "phase": "final_a", "from": node_a1, "model": model_a1, "message": r_a_final.text}
    dialogue_a.append(msg_a_final)
    full_dialogue.append(msg_a_final)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Subgroup B final response (seeing A's original compressed position)
    p_b_final = f"""{node_b1}, for context, Subgroup A's original position (via relay):
{r_relay_ab.text[:400]}
Your subgroup's response:
{r_b1_r2.text[:300]}
Task: Final response. Declare @CONSENSUS or @CONFLICT. Propose @RESOLUTION if possible.
Protocol response:"""
    r_b_final = client.generate(p_b_final, model=model_b1, system_prompt=sys_b1,
                                 temperature=PHASE12_TEMPERATURE, max_tokens=PHASE12_MAX_TOKENS)
    msg_b_final = {"round": 6, "phase": "final_b", "from": node_b1, "model": model_b1, "message": r_b_final.text}
    dialogue_b.append(msg_b_final)
    full_dialogue.append(msg_b_final)
    print(")", end=" ", flush=True)

    # ============================================================
    # CRDT Metrics
    # ============================================================

    # Per-subgroup metrics
    care_a = compute_care_resolve(dialogue_a, task_type="open")
    debt_a = compute_meaning_debt(dialogue_a, task_type="open")
    care_b = compute_care_resolve(dialogue_b, task_type="open")
    debt_b = compute_meaning_debt(dialogue_b, task_type="open")

    # Combined metrics (full dialogue)
    care_combined = compute_care_resolve(full_dialogue, task_type="open")
    debt_combined = compute_meaning_debt(full_dialogue, task_type="open")

    # Average information loss across both relay directions
    avg_atom_survival = sum(r["atom_survival_rate"] for r in info_loss_records) / len(info_loss_records) if info_loss_records else 0
    avg_compression_ratio = sum(r["compression_ratio"] for r in info_loss_records) / len(info_loss_records) if info_loss_records else 0

    return {
        "condition": "bottleneck",
        "scenario": scenario["name"],
        "run_number": run_number,
        "models": {
            "subgroup_a": [model_a1, model_a2],
            "subgroup_b": [model_b1, model_b2],
            "relay": model_relay,
        },
        "dialogue_a": dialogue_a,
        "dialogue_b": dialogue_b,
        "relay_log": relay_log,
        "full_dialogue": full_dialogue,
        "crdt": {
            "subgroup_a": {"care_resolve": care_a, "meaning_debt": debt_a},
            "subgroup_b": {"care_resolve": care_b, "meaning_debt": debt_b},
            "combined": {"care_resolve": care_combined, "meaning_debt": debt_combined},
        },
        "information_loss": info_loss_records,
        "information_loss_summary": {
            "avg_atom_survival_rate": round(avg_atom_survival, 4),
            "avg_compression_ratio": round(avg_compression_ratio, 4),
        },
        "cost_usd": client.get_status()["cumulative_cost_usd"],
    }


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("ARRIVAL CRDT - Phase 12: Bottleneck Communication")
    print("Relay-Compressed Inter-Subgroup Negotiation")
    print("=" * 60)

    num_scenarios = len(PHASE12_SCENARIOS)
    total = num_scenarios * PHASE12_RUNS

    print(f"Scenarios: {num_scenarios}")
    print(f"Runs per scenario: {PHASE12_RUNS}")
    print(f"Subgroup A: {', '.join(MODEL_SHORT.get(m, m) for m in PHASE12_SUBGROUP_A)}")
    print(f"Subgroup B: {', '.join(MODEL_SHORT.get(m, m) for m in PHASE12_SUBGROUP_B)}")
    print(f"Relay: {MODEL_SHORT.get(PHASE12_RELAY, PHASE12_RELAY)}")
    print(f"Rounds per subgroup: {PHASE12_ROUNDS_PER_SUBGROUP}")
    print(f"Total experiments: {total}")
    print("=" * 60)

    client = OpenRouterClient()
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
    logger = EnhancedLogger(log_dir, "phase_12_bottleneck")

    all_results = []
    start_time = datetime.now()

    try:
        for scenario in PHASE12_SCENARIOS:
            print(f"\n{'='*40}")
            print(f"SCENARIO: {scenario['name']}")
            print(f"{'='*40}")

            for run in range(1, PHASE12_RUNS + 1):
                print(f"  [{scenario['name']}] run {run}...", end=" ", flush=True)

                result = run_bottleneck_dialogue(client, logger, scenario, run)

                # Print summary
                care_a = result["crdt"]["subgroup_a"]["care_resolve"].get("care_resolve", "N/A")
                care_b = result["crdt"]["subgroup_b"]["care_resolve"].get("care_resolve", "N/A")
                care_c = result["crdt"]["combined"]["care_resolve"].get("care_resolve", "N/A")
                debt_c = result["crdt"]["combined"]["meaning_debt"].get("total_meaning_debt", 0)
                atom_surv = result["information_loss_summary"]["avg_atom_survival_rate"]
                comp_ratio = result["information_loss_summary"]["avg_compression_ratio"]

                care_a_str = f"{care_a:.2f}" if isinstance(care_a, float) else str(care_a)
                care_b_str = f"{care_b:.2f}" if isinstance(care_b, float) else str(care_b)
                care_c_str = f"{care_c:.2f}" if isinstance(care_c, float) else str(care_c)

                print(f"\n    CARE: A={care_a_str} B={care_b_str} combined={care_c_str}")
                print(f"    debt:{debt_c:.2f} atom_survival:{atom_surv:.2%} compression:{comp_ratio:.2%}")

                # Print info loss details
                for il in result["information_loss"]:
                    direction = il["direction"]
                    survived = len(il["survived_atoms"])
                    lost = len(il["lost_atoms"])
                    print(f"    {direction}: {survived} atoms survived, {lost} lost ({il['atom_survival_rate']:.0%})")

                all_results.append(result)
                logger.log_event(f"bottleneck_{scenario['name']}_{run}", result)
                time.sleep(SLEEP_BETWEEN_CALLS)

    except BudgetExceededError as e:
        print(f"\n!!! BUDGET EXCEEDED: {e}")
    except KeyboardInterrupt:
        print(f"\n!!! Interrupted")

    # ============================================================
    # Summary & Save
    # ============================================================
    print(f"\n{'='*60}")
    print("PHASE 12 RESULTS SUMMARY")
    print(f"{'='*60}")

    def _avg(lst):
        return sum(lst) / len(lst) if lst else 0.0

    # Combined CARE across all experiments
    combined_care = [r["crdt"]["combined"]["care_resolve"].get("care_resolve", 0) for r in all_results
                     if r["crdt"]["combined"]["care_resolve"].get("care_resolve") is not None]
    combined_debt = [r["crdt"]["combined"]["meaning_debt"].get("total_meaning_debt", 0) for r in all_results]

    # Per-subgroup CARE
    care_a_all = [r["crdt"]["subgroup_a"]["care_resolve"].get("care_resolve", 0) for r in all_results
                  if r["crdt"]["subgroup_a"]["care_resolve"].get("care_resolve") is not None]
    care_b_all = [r["crdt"]["subgroup_b"]["care_resolve"].get("care_resolve", 0) for r in all_results
                  if r["crdt"]["subgroup_b"]["care_resolve"].get("care_resolve") is not None]

    # Information loss
    all_survival = [r["information_loss_summary"]["avg_atom_survival_rate"] for r in all_results]
    all_compression = [r["information_loss_summary"]["avg_compression_ratio"] for r in all_results]

    print(f"\nOverall ({len(all_results)} experiments):")
    if combined_care:
        print(f"  Combined avg CARE: {_avg(combined_care):.4f}")
    if combined_debt:
        print(f"  Combined avg debt: {_avg(combined_debt):.4f}")
    if care_a_all:
        print(f"  Subgroup A avg CARE: {_avg(care_a_all):.4f}")
    if care_b_all:
        print(f"  Subgroup B avg CARE: {_avg(care_b_all):.4f}")
    if all_survival:
        print(f"  Avg atom survival rate: {_avg(all_survival):.2%}")
    if all_compression:
        print(f"  Avg compression ratio: {_avg(all_compression):.2%}")

    # Per-scenario breakdown
    for scenario in PHASE12_SCENARIOS:
        scen_results = [r for r in all_results if r["scenario"] == scenario["name"]]
        if not scen_results:
            continue

        sc_care = [r["crdt"]["combined"]["care_resolve"].get("care_resolve", 0) for r in scen_results
                   if r["crdt"]["combined"]["care_resolve"].get("care_resolve") is not None]
        sc_surv = [r["information_loss_summary"]["avg_atom_survival_rate"] for r in scen_results]

        print(f"\n  {scenario['name']} ({len(scen_results)} runs):")
        if sc_care:
            print(f"    Avg CARE: {_avg(sc_care):.4f}")
        if sc_surv:
            print(f"    Avg atom survival: {_avg(sc_surv):.2%}")

    # Save
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results", "phase_12"
    )
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"phase12_results_{timestamp}.json")

    summary = {
        "total_experiments": len(all_results),
        "combined_avg_care": round(_avg(combined_care), 4) if combined_care else None,
        "combined_avg_debt": round(_avg(combined_debt), 4) if combined_debt else None,
        "subgroup_a_avg_care": round(_avg(care_a_all), 4) if care_a_all else None,
        "subgroup_b_avg_care": round(_avg(care_b_all), 4) if care_b_all else None,
        "avg_atom_survival_rate": round(_avg(all_survival), 4) if all_survival else None,
        "avg_compression_ratio": round(_avg(all_compression), 4) if all_compression else None,
    }

    output = {
        "experiment": "Arrival CRDT - Phase 12: Bottleneck Communication",
        "description": "Relay-compressed inter-subgroup negotiation with information loss analysis",
        "started": start_time.isoformat(),
        "completed": datetime.now().isoformat(),
        "total_cost_usd": round(client.get_status()["cumulative_cost_usd"], 4),
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
