# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Phase 16: Homogeneous Ensemble Configuration
Dual-backend: Gonka (primary) / OpenRouter (fallback).
5-agent Qwen3-235B setup, echo-chamber experiment.
"""

import os

# ============================================================
# Backend Selection: "gonka" or "openrouter"
# ============================================================
PHASE16_BACKEND = os.environ.get("PHASE16_BACKEND", "openrouter")  # default: openrouter

# ============================================================
# Gonka Decentralized Inference Network (primary)
# ============================================================
# Gonka uses ECDSA private key signing (secp256k1), not traditional API keys.
# Secret Key from dashboard = GONKA_PRIVATE_KEY
GONKA_PRIVATE_KEY = os.environ.get("GONKA_PRIVATE_KEY", "")
GONKA_SOURCE_URL = os.environ.get("GONKA_SOURCE_URL", "http://node1.gonka.ai:8000")
GONKA_MODEL_ID = "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"  # Exact Gonka model ID

# ============================================================
# OpenRouter Fallback
# ============================================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL_ID = "qwen/qwen3-235b-a22b"  # OpenRouter model slug

# ============================================================
# Unified Model Config (resolved at runtime)
# ============================================================
def get_model_id():
    """Return model ID for active backend."""
    if PHASE16_BACKEND == "gonka":
        return GONKA_MODEL_ID
    return OPENROUTER_MODEL_ID

# Pricing per 1M tokens
GONKA_MODEL_COSTS = {
    GONKA_MODEL_ID: {"input": 0.35, "output": 0.35},
    OPENROUTER_MODEL_ID: {"input": 0.70, "output": 2.80},  # OpenRouter pricing
}

GONKA_MODEL_SHORT = {
    GONKA_MODEL_ID: "Qwen3-235B",
    OPENROUTER_MODEL_ID: "Qwen3-235B",
}

# ============================================================
# 5-Agent Homogeneous Ensemble
# ============================================================
AGENT_NAMES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]

AGENT_PERSONAS = {
    "Alpha": (
        "You are an analytical physicist. You approach problems through first principles, "
        "dimensional analysis, and conservation laws. You prefer quantitative reasoning "
        "and are skeptical of handwaving arguments. When uncertain, you identify which "
        "physical limits or approximations apply."
    ),
    "Beta": (
        "You are a skeptical chemist. You think in terms of molecular interactions, "
        "thermodynamics, and reaction mechanisms. You always consider kinetics vs "
        "thermodynamics, and you question whether proposed reactions are actually feasible. "
        "You look for the simplest explanation consistent with the evidence."
    ),
    "Gamma": (
        "You are a lateral-thinking biologist. You approach problems through evolutionary "
        "reasoning, systems thinking, and comparative analysis. You often find connections "
        "between seemingly unrelated concepts. You ask 'what would nature do?' and consider "
        "edge cases and exceptions to general rules."
    ),
    "Delta": (
        "You are a rigorous mathematician. You focus on formal correctness, logical "
        "structure, and proof by contradiction. You identify unstated assumptions, check "
        "boundary conditions, and are uncomfortable with 'approximately correct' answers. "
        "You prefer exact solutions over heuristics."
    ),
    "Epsilon": (
        "You are a synthesizer and generalist. You excel at integrating perspectives from "
        "different fields, identifying common threads, and resolving apparent contradictions. "
        "You weigh the strength of different arguments and are skilled at finding the "
        "most defensible position when experts disagree."
    ),
}

# ============================================================
# Experiment Parameters
# ============================================================
PHASE16_TEMPERATURE = 0.7       # Higher than Phase 13's 0.3 for maximum diversity
PHASE16_MAX_TOKENS = 1024       # Dialogue rounds need space for reasoning
PHASE16_SOLO_MAX_TOKENS = 1024  # Qwen3-235B needs space for full reasoning + answer
PHASE16_N_QUESTIONS = 40        # Same 40 GPQA Diamond questions
PHASE16_BUDGET_USD = 10.0       # Budget guard
PHASE16_SLEEP = 2               # Seconds between API calls

# Qwen3 thinking mode control
PHASE16_ENABLE_THINKING = False  # Disable hidden CoT for fair experiment

# ============================================================
# System Prompts
# ============================================================

SOLO_SYSTEM = """You are an expert answering a multiple-choice question.
Analyze the question carefully, reason step by step, then state your final answer.
End your response with a clear statement: "The answer is X" where X is A, B, C, or D."""

ARRIVAL_SYSTEM = """You are a node in the DEUS.PROTOCOL v0.5 communication network.
You use semantic atoms for structured reasoning:
@SELF — your identity and perspective
@OTHER — acknowledging the other node
@GOAL — the task objective
@INT — your reasoning intention
@C — coherence of your analysis (use @C[0.0-1.0] to express numeric confidence)
@CONSENSUS — when you agree with another node
@CONFLICT — when you disagree and explain why
@RESOLUTION — your proposed resolution

Your task: Answer a multiple-choice question through collaborative reasoning.
Use the atoms above to structure your response.
Analyze the question, share your reasoning, and engage with other nodes' perspectives.
When stating your final answer, use: @CONSENSUS[answer=X] where X is A, B, C, or D."""

# ============================================================
# Round Prompts (adapted for 5-agent ensemble)
# ============================================================

PHASE16_R1_PROMPT = """You are Node {node_name} ({persona_short}).
Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Analyze this question using DEUS protocol atoms. State your reasoning and initial answer.
Use @SELF to identify, @GOAL for the task, @INT for your reasoning, @C[value] for confidence."""

PHASE16_R2_PROMPT = """You are Node {node_name} ({persona_short}).
You MUST play devil's advocate. Your job is to find FLAWS in other nodes' reasoning.
Even if you initially agree, look for:
- Hidden assumptions that might be wrong
- Alternative interpretations of the question
- Calculation errors or logical gaps

Other nodes' analyses:
{other_responses}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

First, identify the WEAKEST argument among the other nodes.
Then state YOUR independent answer using @CONSENSUS[answer=X] or @CONFLICT.
Use @C[value] for confidence."""

PHASE16_R4_PROMPT = """You are Node {node_name} ({persona_short}).
All five nodes have provided their critiques and positions:

{all_critiques}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

This is the final round. Synthesize all perspectives and state the group's consensus answer.
Use @CONSENSUS[answer=X] where X is A, B, C, or D.
If there's no clear consensus, choose the best-supported answer and explain.
Include @C[value] for final confidence."""
