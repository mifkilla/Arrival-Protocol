# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 17: Solo Chain-of-Thought Baseline

Purpose: Address Wang et al. (ACL 2024) critique that single-agent + strong
prompts can match multi-agent systems. We run a SINGLE Qwen3-235B with
enhanced CoT prompting on the SAME 40 GPQA Diamond questions used in
Phase 16, then compare: Solo CoT vs Majority Vote (52.5%) vs ARRIVAL (65%).

Design:
    - 5 independent runs per question (same as 5 agents in Phase 16)
    - Majority vote across 5 runs → Solo CoT Majority Vote accuracy
    - Best-of-5 → Solo CoT oracle accuracy
    - Same model, same temperature, same questions
    - Stronger CoT prompt than Phase 16 solo (explicit step-by-step reasoning)
"""

import os

# ---------- Model ----------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL_ID = "qwen/qwen3-235b-a22b"
MODEL_SHORT = "Qwen3-235B"

# ---------- Experiment parameters ----------
N_RUNS_PER_QUESTION = 5      # Match Phase 16's 5 agents
TEMPERATURE = 0.7            # Same as Phase 16
MAX_TOKENS = 1024            # Same as Phase 16
BUDGET_LIMIT = 2.0           # USD safety cap

# ---------- CoT System Prompt ----------
# This is deliberately STRONGER than Phase 16's solo prompt to give
# the single-agent baseline the best possible chance (fair comparison).
SOLO_COT_SYSTEM = """You are a world-class scientist with deep expertise across physics, \
chemistry, biology, and mathematics. You are answering a graduate-level \
multiple-choice question from the GPQA Diamond benchmark.

IMPORTANT INSTRUCTIONS:
1. Read the question and all answer choices carefully.
2. Think step by step through the problem. Show your complete reasoning chain.
3. Consider each answer choice systematically — explain why it is or is not correct.
4. If you are uncertain, reason through by elimination.
5. After your full analysis, state your final answer clearly.

End your response with exactly: "The answer is X" where X is A, B, C, or D."""

# ---------- Phase 16 baselines for comparison ----------
PHASE16_SOLO_ACCURACY = 0.415     # 83/200 (5 agents × 40 questions)
PHASE16_MV_ACCURACY = 0.525       # 21/40
PHASE16_ARRIVAL_ACCURACY = 0.650  # 26/40
PHASE16_ARRIVAL_CORRECT = 26
PHASE16_ARRIVAL_TOTAL = 40
