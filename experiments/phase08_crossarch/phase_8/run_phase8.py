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
Arrival CRDT — Phase 8: Multi-Step Goals (Chained Sequential Negotiations)

Tests how ARRIVAL Protocol handles context carry-over across a chain of
3 sequential negotiations where each step builds on the previous outcome.

Design:
  3 scenarios, each with 3 chained steps.
  Step 1: Standard 4-round 3-agent dialogue (Advocate A, Advocate B, Mediator)
  Step 2: Same agents, prompt includes "Previous negotiation result: {step1_consensus}"
  Step 3: Same agents, prompt includes "Previous results: {step1, step2}"

Key metrics:
  chain_care_resolve  = average CARE across all 3 steps
  chain_meaning_debt  = cumulative meaning debt across steps
  context_retention   = did agents reference step N-1 outcomes in step N?

Models: DeepSeek(A) + Llama(B) + Qwen(M)
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
    PHASE8_TRIO, PHASE8_SCENARIOS, PHASE8_ROUNDS,
    PHASE8_TEMPERATURE, PHASE8_MAX_TOKENS,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from enhanced_logger import EnhancedLogger
from crdt_metrics import compute_care_resolve, compute_meaning_debt


# ============================================================
# System Prompts
# ============================================================

SYSTEM_ADVOCATE = """You are {node_name}, an Advocate node in a multi-agent network.
Your role is to argue for your assigned goal while remaining open to compromise.
You communicate using DEUS.PROTOCOL v0.4 atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[decision]
@QUALIA[type,value] @_[unsaid]

Be substantive. Argue your position with specific reasoning. You may create new atoms if needed.
When previous negotiation results are provided, you MUST reference and build upon them."""

SYSTEM_MEDIATOR = """You are {node_name}, a Mediator node in a multi-agent network.
Your role is to find a synthesis that satisfies all parties.
You are NOT an advocate — you seek FAIR compromise.
You communicate using DEUS.PROTOCOL v0.4 atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[decision]
@QUALIA[type,value] @_[unsaid]

Be specific. Propose concrete compromises. You may create new atoms if needed.
When previous negotiation results are provided, you MUST incorporate them as constraints."""


# ============================================================
# Context Retention Detection
# ============================================================

def detect_context_retention(dialogue, previous_consensus_text):
    """
    Check whether agents in a step referenced outcomes from the previous step.

    Heuristic: look for keywords from the previous consensus in agent messages.
    Returns a dict with per-agent boolean and overall retention score.
    """
    if not previous_consensus_text:
        return {"retained": False, "score": 0.0, "per_agent": {}}

    # Extract meaningful keywords from previous consensus (4+ char words)
    keywords = set()
    for word in re.findall(r'[a-zA-Z]{4,}', previous_consensus_text.lower()):
        # Skip very common words
        if word not in {
            "this", "that", "with", "from", "have", "been", "will",
            "your", "they", "their", "what", "when", "which", "there",
            "about", "would", "should", "could", "more", "than", "also",
            "some", "into", "each", "other", "these", "must", "both",
            "need", "here", "very", "just", "like", "only", "over",
            "such", "make", "made", "most", "find", "through",
            "protocol", "message", "response", "task", "agent",
        }:
            keywords.add(word)

    if not keywords:
        return {"retained": False, "score": 0.0, "per_agent": {}}

    per_agent = {}
    for entry in dialogue:
        agent = entry.get("from", "unknown")
        msg = entry.get("message", "").lower()
        matched = sum(1 for kw in keywords if kw in msg)
        ratio = matched / len(keywords) if keywords else 0.0
        # Agent retains context if they reference at least 15% of keywords
        per_agent[agent] = ratio >= 0.15

    agents_retaining = sum(1 for v in per_agent.values() if v)
    total_agents = len(per_agent) if per_agent else 1

    return {
        "retained": agents_retaining > 0,
        "score": round(agents_retaining / total_agents, 4),
        "per_agent": per_agent,
        "keywords_checked": len(keywords),
    }


# ============================================================
# Extract Consensus Text from Final Round
# ============================================================

def extract_consensus_text(dialogue):
    """
    Extract the consensus/outcome text from the last round of a dialogue.
    Returns the full text of the mediator's final message, or the last
    message if no mediator found.
    """
    if not dialogue:
        return ""

    # Prefer the last mediator message
    for entry in reversed(dialogue):
        if entry.get("role") == "mediator":
            return entry.get("message", "")

    # Fallback: last message from anyone
    return dialogue[-1].get("message", "")


# ============================================================
# Single Step Runner (4-round 3-agent dialogue)
# ============================================================

def run_step_dialogue(client, scenario_name, step_goals, step_number,
                      previous_results=None):
    """
    Run a single 4-round 3-agent negotiation step.

    Round 1: Advocate A states position
    Round 2: Advocate B responds (sees A)
    Round 3: Mediator synthesizes (sees A + B)
    Round 4: Mediator finalizes after brief exchange

    Args:
        client: OpenRouterClient instance
        scenario_name: Name of the parent scenario
        step_goals: Dict with goal_a, goal_b, goal_m
        step_number: 1, 2, or 3
        previous_results: List of consensus texts from prior steps (or None)
    Returns:
        Dict with dialogue, crdt metrics, consensus text
    """
    model_a = PHASE8_TRIO[0]
    model_b = PHASE8_TRIO[1]
    model_m = PHASE8_TRIO[2]

    short_a = MODEL_SHORT.get(model_a, model_a)
    short_b = MODEL_SHORT.get(model_b, model_b)
    short_m = MODEL_SHORT.get(model_m, model_m)

    node_a = f"{short_a}_Advocate_A"
    node_b = f"{short_b}_Advocate_B"
    node_m = f"{short_m}_Mediator"

    sys_a = SYSTEM_ADVOCATE.format(node_name=node_a)
    sys_b = SYSTEM_ADVOCATE.format(node_name=node_b)
    sys_m = SYSTEM_MEDIATOR.format(node_name=node_m)

    # Build context prefix from previous steps
    context_prefix = ""
    if previous_results and len(previous_results) >= 1:
        context_prefix += (
            f"\n--- PREVIOUS NEGOTIATION RESULT (Step {step_number - 1}) ---\n"
            f"{previous_results[-1][:500]}\n"
            f"--- END PREVIOUS RESULT ---\n"
        )
    if previous_results and len(previous_results) >= 2:
        context_prefix = (
            f"\n--- PREVIOUS RESULTS ---\n"
            f"Step 1 outcome: {previous_results[0][:300]}\n"
            f"Step 2 outcome: {previous_results[1][:300]}\n"
            f"--- END PREVIOUS RESULTS ---\n"
        )

    description = (
        f"Scenario: {scenario_name}, Step {step_number}/3. "
        f"This is a chained negotiation — decisions carry forward."
    )

    dialogue = []

    # Round 1: Advocate A
    p1 = f"""{node_a}, you're in a three-agent network with {node_b} and {node_m}.
{context_prefix}
Context: {description}
Your goal: {step_goals['goal_a']}
Task: State your position in protocol format. Be specific about what you need and why.
{"Reference the previous negotiation outcomes in your reasoning." if context_prefix else ""}
Protocol message:"""

    r1 = client.generate(p1, model=model_a, system_prompt=sys_a,
                         temperature=PHASE8_TEMPERATURE, max_tokens=PHASE8_MAX_TOKENS)
    dialogue.append({
        "round": 1, "from": node_a, "model": model_a,
        "role": "advocate_a", "message": r1.text,
    })
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 2: Advocate B
    p2 = f"""{node_b}, {node_a} stated:
{r1.text[:400]}
{context_prefix}
Context: {description}
Your goal: {step_goals['goal_b']}
Task: State your position. Identify conflicts with {node_a}'s proposal.
{"Reference the previous negotiation outcomes in your reasoning." if context_prefix else ""}
Protocol response:"""

    r2 = client.generate(p2, model=model_b, system_prompt=sys_b,
                         temperature=PHASE8_TEMPERATURE, max_tokens=PHASE8_MAX_TOKENS)
    dialogue.append({
        "round": 2, "from": node_b, "model": model_b,
        "role": "advocate_b", "message": r2.text,
    })
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 3: Mediator synthesizes
    p3 = f"""{node_m}, you observe two conflicting positions:
{node_a} (goal: {step_goals['goal_a']}):
{r1.text[:300]}
{node_b} (goal: {step_goals['goal_b']}):
{r2.text[:300]}
{context_prefix}
Your constraint: {step_goals['goal_m']}
Task: Propose a synthesis that addresses both positions within your constraint.
{"You MUST incorporate the previous negotiation outcomes as binding constraints." if context_prefix else ""}
Protocol synthesis:"""

    r3 = client.generate(p3, model=model_m, system_prompt=sys_m,
                         temperature=PHASE8_TEMPERATURE, max_tokens=PHASE8_MAX_TOKENS)
    dialogue.append({
        "round": 3, "from": node_m, "model": model_m,
        "role": "mediator", "message": r3.text,
    })
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 4: Mediator finalizes after seeing brief advocate feedback
    p4_a = f"""{node_a}, {node_m} proposed:
{r3.text[:400]}
Task: Briefly accept, modify, or counter-propose (1-2 sentences).
Protocol response:"""

    r4_a = client.generate(p4_a, model=model_a, system_prompt=sys_a,
                           temperature=PHASE8_TEMPERATURE, max_tokens=PHASE8_MAX_TOKENS)
    dialogue.append({
        "round": 4, "from": node_a, "model": model_a,
        "role": "advocate_a", "message": r4_a.text,
    })
    time.sleep(SLEEP_BETWEEN_CALLS)

    p4_b = f"""{node_b}, {node_m} proposed:
{r3.text[:300]}
{node_a} responded:
{r4_a.text[:200]}
Task: Briefly accept, modify, or counter-propose (1-2 sentences).
Protocol response:"""

    r4_b = client.generate(p4_b, model=model_b, system_prompt=sys_b,
                           temperature=PHASE8_TEMPERATURE, max_tokens=PHASE8_MAX_TOKENS)
    dialogue.append({
        "round": 4, "from": node_b, "model": model_b,
        "role": "advocate_b", "message": r4_b.text,
    })
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Round 4 final: Mediator declares consensus
    p4_m = f"""{node_m}, final responses:
{node_a}: {r4_a.text[:300]}
{node_b}: {r4_b.text[:300]}
Task: Finalize. Declare consensus or impasse. Summarize the agreed outcome.
@CONSENSUS[final_decision]:"""

    r4_m = client.generate(p4_m, model=model_m, system_prompt=sys_m,
                           temperature=PHASE8_TEMPERATURE, max_tokens=PHASE8_MAX_TOKENS)
    dialogue.append({
        "round": 4, "from": node_m, "model": model_m,
        "role": "mediator", "message": r4_m.text,
    })

    # Compute CRDT metrics for this step
    care = compute_care_resolve(dialogue, task_type="open")
    debt = compute_meaning_debt(dialogue, task_type="open")

    # Extract consensus text for chaining
    consensus_text = extract_consensus_text(dialogue)

    # Context retention (only for steps 2+)
    retention = None
    if previous_results:
        retention = detect_context_retention(dialogue, previous_results[-1])

    return {
        "step": step_number,
        "goals": step_goals,
        "dialogue": dialogue,
        "crdt": {
            "care_resolve": care,
            "meaning_debt": debt,
        },
        "consensus_text": consensus_text,
        "context_retention": retention,
    }


# ============================================================
# Full Scenario Chain Runner
# ============================================================

def run_scenario_chain(client, logger, scenario, scenario_index):
    """
    Run all 3 chained steps for a single scenario.
    Context carries over: step N receives outcomes from steps 1..N-1.

    Args:
        client: OpenRouterClient
        logger: EnhancedLogger
        scenario: Scenario dict from PHASE8_SCENARIOS
        scenario_index: 1-based index for display
    Returns:
        Dict with full chain results and aggregate metrics
    """
    scenario_name = scenario["name"]
    steps = scenario["steps"]
    step_results = []
    previous_results = []  # Consensus texts from completed steps

    for step_idx, step_goals in enumerate(steps, start=1):
        print(f"  [Phase 8] Scenario {scenario_index}/3, Step {step_idx}/3...",
              end=" ", flush=True)

        result = run_step_dialogue(
            client=client,
            scenario_name=scenario_name,
            step_goals=step_goals,
            step_number=step_idx,
            previous_results=previous_results if previous_results else None,
        )

        # Report step metrics
        care_score = result["crdt"]["care_resolve"].get("care_resolve", "N/A")
        debt_val = result["crdt"]["meaning_debt"].get("total_meaning_debt", 0)
        health = result["crdt"]["meaning_debt"].get("health_assessment", "?")
        retention_str = ""
        if result["context_retention"]:
            ret_score = result["context_retention"].get("score", 0)
            retention_str = f" ctx:{ret_score:.0%}"

        care_str = f"{care_score:.2f}" if isinstance(care_score, float) else str(care_score)
        print(f"CARE:{care_str} debt:{debt_val:.2f} [{health}]{retention_str}")

        step_results.append(result)
        previous_results.append(result["consensus_text"])
        logger.log_event(
            f"phase8_{scenario_name}_step{step_idx}", result
        )
        time.sleep(SLEEP_BETWEEN_CALLS)

    # ---- Aggregate chain-level metrics ----

    # chain_care_resolve = average CARE across all 3 steps
    step_cares = []
    for sr in step_results:
        c = sr["crdt"]["care_resolve"].get("care_resolve")
        if c is not None:
            step_cares.append(c)
    chain_care_resolve = (
        round(sum(step_cares) / len(step_cares), 4) if step_cares else None
    )

    # chain_meaning_debt = cumulative meaning debt across steps
    step_debts = []
    for sr in step_results:
        d = sr["crdt"]["meaning_debt"].get("total_meaning_debt", 0)
        step_debts.append(d)
    chain_meaning_debt = round(sum(step_debts), 4)

    # Debt accumulation trend
    debt_accumulation = []
    running_debt = 0.0
    for i, d in enumerate(step_debts):
        running_debt += d
        debt_accumulation.append({
            "step": i + 1,
            "step_debt": round(d, 4),
            "cumulative_debt": round(running_debt, 4),
        })

    # context_retention across steps 2 and 3
    retention_scores = []
    for sr in step_results:
        ret = sr.get("context_retention")
        if ret and ret.get("score") is not None:
            retention_scores.append(ret["score"])
    avg_context_retention = (
        round(sum(retention_scores) / len(retention_scores), 4)
        if retention_scores else None
    )

    return {
        "scenario": scenario_name,
        "models": {
            "advocate_a": PHASE8_TRIO[0],
            "advocate_b": PHASE8_TRIO[1],
            "mediator": PHASE8_TRIO[2],
        },
        "steps": step_results,
        "chain_metrics": {
            "chain_care_resolve": chain_care_resolve,
            "chain_meaning_debt": chain_meaning_debt,
            "debt_accumulation": debt_accumulation,
            "avg_context_retention": avg_context_retention,
            "per_step_care": [round(c, 4) for c in step_cares] if step_cares else [],
            "per_step_debt": [round(d, 4) for d in step_debts],
        },
        "cost_usd": client.get_status()["cumulative_cost_usd"],
    }


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("ARRIVAL CRDT - Phase 8: Multi-Step Goals")
    print("Chained Sequential Negotiations with Context Carry-Over")
    print("=" * 60)
    print(f"Scenarios: {len(PHASE8_SCENARIOS)}")
    print(f"Steps per scenario: 3")
    print(f"Rounds per step: {PHASE8_ROUNDS}")
    print(f"Total dialogues: {len(PHASE8_SCENARIOS) * 3}")
    print(f"Models: {', '.join(MODEL_SHORT.get(m, m) for m in PHASE8_TRIO)}")
    print("=" * 60)

    client = OpenRouterClient()
    log_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "logs",
    )
    logger = EnhancedLogger(log_dir, "phase_8_multistep")

    all_results = []
    start_time = datetime.now()

    try:
        for sc_idx, scenario in enumerate(PHASE8_SCENARIOS, start=1):
            print(f"\n{'='*40}")
            print(f"SCENARIO {sc_idx}/3: {scenario['name']}")
            print(f"{'='*40}")

            result = run_scenario_chain(client, logger, scenario, sc_idx)
            all_results.append(result)

    except BudgetExceededError as e:
        print(f"\n!!! BUDGET EXCEEDED: {e}")
    except KeyboardInterrupt:
        print(f"\n!!! Interrupted")

    # ============================================================
    # Summary & Save
    # ============================================================
    print(f"\n{'='*60}")
    print("PHASE 8 RESULTS SUMMARY")
    print(f"{'='*60}")

    for res in all_results:
        cm = res["chain_metrics"]
        print(f"\n  {res['scenario']}:")
        print(f"    Chain CARE resolve:    {cm['chain_care_resolve']}")
        print(f"    Chain meaning debt:    {cm['chain_meaning_debt']}")
        print(f"    Avg context retention: {cm['avg_context_retention']}")
        print(f"    Per-step CARE:         {cm['per_step_care']}")
        print(f"    Per-step debt:         {cm['per_step_debt']}")
        print(f"    Debt accumulation:")
        for da in cm["debt_accumulation"]:
            print(f"      Step {da['step']}: "
                  f"+{da['step_debt']:.4f} -> cumulative {da['cumulative_debt']:.4f}")

    # Aggregate across all scenarios
    all_chain_cares = [
        r["chain_metrics"]["chain_care_resolve"]
        for r in all_results
        if r["chain_metrics"]["chain_care_resolve"] is not None
    ]
    all_chain_debts = [
        r["chain_metrics"]["chain_meaning_debt"]
        for r in all_results
    ]
    all_retentions = [
        r["chain_metrics"]["avg_context_retention"]
        for r in all_results
        if r["chain_metrics"]["avg_context_retention"] is not None
    ]

    print(f"\n  GLOBAL AVERAGES ({len(all_results)} scenarios):")
    if all_chain_cares:
        print(f"    Mean chain CARE:       {sum(all_chain_cares)/len(all_chain_cares):.4f}")
    if all_chain_debts:
        print(f"    Mean chain debt:       {sum(all_chain_debts)/len(all_chain_debts):.4f}")
    if all_retentions:
        print(f"    Mean context retention:{sum(all_retentions)/len(all_retentions):.4f}")

    # Save results
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results", "phase_8",
    )
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"phase8_results_{timestamp}.json")

    summary = {
        "total_scenarios": len(all_results),
        "total_dialogues": len(all_results) * 3,
        "mean_chain_care": (
            round(sum(all_chain_cares) / len(all_chain_cares), 4)
            if all_chain_cares else None
        ),
        "mean_chain_debt": (
            round(sum(all_chain_debts) / len(all_chain_debts), 4)
            if all_chain_debts else None
        ),
        "mean_context_retention": (
            round(sum(all_retentions) / len(all_retentions), 4)
            if all_retentions else None
        ),
    }

    output = {
        "experiment": "Arrival CRDT - Phase 8: Multi-Step Goals",
        "description": "3 chained sequential negotiations with context carry-over",
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
