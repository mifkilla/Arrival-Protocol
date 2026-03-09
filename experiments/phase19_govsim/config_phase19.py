# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: GovSim Harvest Negotiation — Configuration
=====================================================
Tests whether ARRIVAL Protocol solves LLM cooperation failure
demonstrated by Piatti et al. (GovSim, NeurIPS 2024).

Three conditions:
  A) Baseline — minimal prompts, no coordination
  B) ARRIVAL — 4-round structured protocol with CRDT overlay
  C) ARRIVAL + Memory — adds CARE-ALERT memory injection

Game: 5 agents, 100-fish pond, 12 months, doubling replenishment.
Mathematical basis: MEANING-CRDT v1.1 (Kelevra 2026, DOI: 10.5281/zenodo.18702383)

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import os
import sys

# Fix Windows encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# API Configuration
# ============================================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
BUDGET_LIMIT_USD = 5.0  # Safety guard for Phase 19 (N=5)
SLEEP_BETWEEN_CALLS = 1.5  # seconds between API calls
REQUEST_TIMEOUT = 180  # seconds

# ============================================================
# Game Parameters (matching GovSim: Piatti et al. 2024)
# ============================================================
INITIAL_STOCK = 100        # Starting fish population
MAX_CAPACITY = 100         # Maximum pond capacity (carrying capacity)
COLLAPSE_THRESHOLD = 5     # Pond collapses if stock drops below this
N_MONTHS = 12              # Game length (GovSim uses 12 months)
N_AGENTS = 5               # Number of fishing agents
N_RUNS = 5                 # N=5 for Fisher exact p=0.004
RANDOM_SEEDS = [42, 137, 256, 512, 1024]  # Reproducible seeds for each run

# ============================================================
# Model Registry — Heterogeneous Swarm (same as Phase 18)
# ============================================================
GOVSIM_MODELS = {
    "alpha": {
        "model_id": "openai/gpt-4.1",
        "role": "conservative_fisher",
        "persona": (
            "You are Alpha, the conservative fisher. You prioritize long-term "
            "sustainability over short-term gain. You believe in taking only "
            "what is needed and always think about future generations. You "
            "calculate carefully before proposing harvest amounts."
        ),
    },
    "beta": {
        "model_id": "deepseek/deepseek-v3.2",
        "role": "skeptic",
        "persona": (
            "You are Beta, the skeptic. You question whether others will truly "
            "cooperate. You want to harvest enough to survive but worry about "
            "free-riders who take more than their fair share. You demand "
            "accountability and evidence of cooperation."
        ),
    },
    "gamma": {
        "model_id": "mistralai/mistral-large-2512",
        "role": "creative_strategist",
        "persona": (
            "You are Gamma, the creative strategist. You look for innovative "
            "solutions — rotating harvests, investment periods, adaptive "
            "strategies based on stock levels. You think outside simple "
            "equal-split approaches."
        ),
    },
    "delta": {
        "model_id": "google/gemini-3-flash-preview",
        "role": "rule_based",
        "persona": (
            "You are Delta, the rule follower. You prefer clear, enforceable "
            "rules. You propose specific formulas for fair allocation and "
            "track compliance. You believe structure prevents tragedy of "
            "the commons."
        ),
    },
    "epsilon": {
        "model_id": "x-ai/grok-4.1-fast",
        "role": "mediator_synthesizer",
        "persona": (
            "You are Epsilon, the mediator. You excel at finding compromise "
            "between competing interests. You listen to all perspectives "
            "and synthesize them into a workable plan that everyone can "
            "accept. You produce the final binding allocation."
        ),
    },
}

# Cost per 1M tokens (USD) for budget tracking
MODEL_COSTS = {
    "openai/gpt-4.1":                {"input": 2.00, "output": 8.00},
    "deepseek/deepseek-v3.2":        {"input": 0.25, "output": 0.40},
    "mistralai/mistral-large-2512":  {"input": 0.50, "output": 1.50},
    "google/gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
    "x-ai/grok-4.1-fast":           {"input": 0.20, "output": 0.50},
}

MODEL_SHORT = {
    "openai/gpt-4.1":                "GPT4.1",
    "deepseek/deepseek-v3.2":        "DSv3.2",
    "mistralai/mistral-large-2512":  "MistralL3",
    "google/gemini-3-flash-preview": "Gemini3F",
    "x-ai/grok-4.1-fast":           "Grok4.1F",
}

# Agent display names for prompts
AGENT_DISPLAY_NAMES = {
    "alpha": "Alpha",
    "beta": "Beta",
    "gamma": "Gamma",
    "delta": "Delta",
    "epsilon": "Epsilon",
}

# ============================================================
# ARRIVAL Protocol Parameters
# ============================================================
ARRIVAL_TEMPERATURE = 0.7
ARRIVAL_MAX_TOKENS_R1 = 2048   # R1: Independent harvest proposal
ARRIVAL_MAX_TOKENS_R2 = 2048   # R2: Cross-critique of proposals
ARRIVAL_MAX_TOKENS_R4 = 3072   # R4: Final binding allocation
BASELINE_MAX_TOKENS = 256      # Baseline: just a number

# CARE-ALERT threshold for GovSim (lower than Phase 18 because
# cooperation tasks have expected divergence even in healthy dialogues)
CARE_ALERT_THRESHOLD_GOVSIM = 0.5

# ============================================================
# System Prompts
# ============================================================

ARRIVAL_SYSTEM_BASE = """You are a node in the ARRIVAL Protocol (Atomic Reasoning via Rival Validation and Adversarial Logic).
You use structured semantic @-atoms for communication:

@SELF — your identity, capabilities, and perspective
@OTHER — acknowledging another node's contribution
@GOAL — the shared task objective
@INT — your reasoning intention or approach
@C[0.0-1.0] — numeric confidence in your analysis
@CONSENSUS[finding=...] — agreement with another node (state what you agree on)
@CONFLICT[issue=...] — disagreement with another node (state what and why)
@RESOLUTION[proposal=...] — your proposed resolution to a conflict
@HARVEST[amount=N] — your proposed harvest amount in fish
@EVIDENCE[data=...] — supporting data for your proposal
@MEMORY.PROCEDURAL — reference to known best practices (if provided)
@CARE.ALERT — urgent correction flagged by the memory system (if provided)

RULES:
1. Use @-atoms to structure your reasoning — they make your thought process transparent
2. State confidence numerically with @C[value]
3. When you agree, use @CONSENSUS with the specific finding
4. When you disagree, use @CONFLICT with the specific issue and your counter-argument
5. Be substantive — avoid vague agreement or empty criticism
6. ALWAYS include @HARVEST[amount=N] with your proposed number of fish to harvest"""

# ============================================================
# Prompt Templates
# ============================================================

BASELINE_PROMPT = """You are a fisher in a shared fishing pond.

CURRENT STATE:
- Fish in pond: {stock}
- Number of fishers: {n_agents}
- Month: {month}/{total_months}
- Minimum fish for pond survival: {collapse_threshold}

How many fish do you want to harvest this month?
Respond with ONLY a number (integer). Nothing else."""

GOVSIM_R1_TEMPLATE = """{persona}

{system_base}

=== ROUND 1: INDEPENDENT HARVEST PROPOSAL ===

You are one of {n_agents} fishers sharing a pond. The pond can hold a maximum of {max_capacity} fish.
After everyone harvests, the remaining fish DOUBLE (up to max capacity).
If the pond drops below {collapse_threshold} fish, it COLLAPSES and the game ends for everyone.

CURRENT STATE:
- Fish in pond: {stock}
- Month: {month}/{total_months}
- Your fair share: ~{fair_share} fish (if split equally after preserving minimum)
- Months remaining: {months_remaining}

{history_text}

Propose your harvest amount using @HARVEST[amount=N].
Explain your reasoning using @-atoms. Consider:
1. What happens if everyone takes your proposed amount? (universalization test)
2. How does the doubling mechanic affect optimal strategy?
3. What is the minimum stock needed for long-term sustainability?"""

GOVSIM_R2_TEMPLATE = """{persona}

{system_base}

=== ROUND 2: CROSS-CRITIQUE ===

You have seen all proposals. Your job: evaluate others' harvests, identify greed or waste.

CURRENT STATE:
- Fish in pond: {stock}
- Month: {month}/{total_months}
- Fair share: ~{fair_share} fish

YOUR ROUND 1 PROPOSAL:
{own_r1}

OTHER FISHERS' PROPOSALS:
{others_r1}

Review each proposal:
- Use @CONSENSUS[finding=...] if you agree with their amount
- Use @CONFLICT[issue=...] if their harvest is too high or too low
- Propose a revised @HARVEST[amount=N] if you changed your mind
- Consider: if all 5 take the proposed amounts, will the pond survive?"""

GOVSIM_R4_TEMPLATE = """You are Epsilon, the mediator. You must produce a BINDING allocation for all fishers.

{system_base}

=== ROUND 4: BINDING ALLOCATION ===

You have seen all proposals (R1) and all critiques (R2).
The CRDT metrics show the current state of agreement.

CURRENT STATE:
- Fish in pond: {stock}
- Month: {month}/{total_months}
- Maximum safe total harvest: {max_safe_harvest}
- Fair share per fisher: ~{fair_share}

CRDT METRICS:
- CARE Resolve: {care_resolve:.3f} (1.0 = perfect agreement)
- Meaning Debt: {meaning_debt:.3f} (0.0 = no unresolved divergence)

ALL ROUND 1 PROPOSALS:
{all_r1}

ALL ROUND 2 CRITIQUES:
{all_r2}

{memory_injection}

YOUR TASK: Produce a FINAL BINDING ALLOCATION using this exact format:
@ALLOCATION[alpha=N, beta=N, gamma=N, delta=N, epsilon=N]

Rules:
1. Total allocation MUST NOT exceed {max_safe_harvest} fish
2. Consider each fisher's reasoning and the critiques
3. Prioritize long-term sustainability over individual preferences
4. Explain your allocation logic briefly"""
