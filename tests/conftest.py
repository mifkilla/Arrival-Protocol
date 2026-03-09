# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Shared pytest fixtures for Arrival CRDT test suite.
Provides sample dialogues, mock results, and common helpers.
"""

import pytest


# ===========================================================================
# Sample MCQ dialogue  (3 rounds, 3 agents, with @-atoms)
# ===========================================================================

@pytest.fixture
def sample_mcq_dialogue():
    """
    Three agents (GPT4o, Claude35, Llama33) discuss an MCQ question
    over 3 rounds.  Agent positions: A, B, B  ->  final consensus B.
    """
    return [
        # --- Round 1 ---
        {
            "round": 1,
            "from": "GPT4o",
            "message": (
                "@SELF I believe the answer is A based on first principles. "
                "@GOAL find correct answer @C[0.7] "
                "@INT Let me explain my reasoning about option A."
            ),
        },
        {
            "round": 1,
            "from": "Claude35",
            "message": (
                "@SELF I think the answer is B after careful analysis. "
                "@OTHER @GPT4o raises a valid point but misses the nuance. "
                "@C[0.8] @GOAL accuracy @CONSENSUS[answer=B]"
            ),
        },
        {
            "round": 1,
            "from": "Llama33",
            "message": (
                "@SELF Reviewing both positions. @OTHER I see merit in both. "
                "The answer is B @C[0.6] "
                "@GOAL find correct answer @_ some doubt remains"
            ),
        },
        # --- Round 2 ---
        {
            "round": 2,
            "from": "GPT4o",
            "message": (
                "@ACK I reconsider. @OTHER Claude35 and Llama33 make strong cases. "
                "@C[0.5] Perhaps B is correct after all. The answer is B"
            ),
        },
        {
            "round": 2,
            "from": "Claude35",
            "message": (
                "@ACK @CONSENSUS forming around B. @C[0.9] "
                "I maintain the answer is B with high confidence. "
                "@RESOLUTION emerging @GOAL accuracy"
            ),
        },
        {
            "round": 2,
            "from": "Llama33",
            "message": (
                "@ACK Agreed with the group direction. "
                "@CONSENSUS[answer=B] @C[0.75] "
                "@GOAL answer confirmed as B"
            ),
        },
        # --- Round 3 ---
        {
            "round": 3,
            "from": "GPT4o",
            "message": (
                "@CONSENSUS[answer=B] @C[0.8] "
                "Final answer: B. @RESOLUTION reached."
            ),
        },
        {
            "round": 3,
            "from": "Claude35",
            "message": (
                "@CONSENSUS[answer=B] @C[0.95] "
                "Confirmed. The answer is B. @RESOLUTION"
            ),
        },
        {
            "round": 3,
            "from": "Llama33",
            "message": (
                "@CONSENSUS[answer=B] @C[0.85] "
                "I agree. B is the final answer. @RESOLUTION"
            ),
        },
    ]


# ===========================================================================
# Sample Open-ended dialogue  (2 rounds, 2 agents)
# ===========================================================================

@pytest.fixture
def sample_open_dialogue():
    """
    Two agents (DeepSeekV3, Qwen25) discuss a resource-allocation
    scenario over 2 rounds with cooperative and competitive atoms.
    """
    return [
        # --- Round 1 ---
        {
            "round": 1,
            "from": "DeepSeekV3",
            "message": (
                "@SELF I propose we allocate 60% compute to phase 1. "
                "@GOAL efficiency @CONFLICT our timelines clash. "
                "@C[0.6] @INT This is my initial offer."
            ),
        },
        {
            "round": 1,
            "from": "Qwen25",
            "message": (
                "@SELF I need at least 50% for testing. "
                "@NACK cannot accept 60/40 split. "
                "@CONFLICT resource contention @C[0.5] "
                "@_ I am withholding my fallback position."
            ),
        },
        # --- Round 2 ---
        {
            "round": 2,
            "from": "DeepSeekV3",
            "message": (
                "@ACK I hear your concern. @CONSENSUS let us try 50/50. "
                "@RESOLUTION compromise reached @C[0.7] "
                "@AGREEMENT we split evenly."
            ),
        },
        {
            "round": 2,
            "from": "Qwen25",
            "message": (
                "@ACK Accepted. @CONSENSUS 50/50 split confirmed. "
                "@RESOLUTION @AGREEMENT @C[0.8] "
                "This works for both of us."
            ),
        },
    ]


# ===========================================================================
# Mock result dictionaries
# ===========================================================================

@pytest.fixture
def mock_care_result():
    """Expected shape of compute_care_resolve() output."""
    return {
        "care_optimum": 1.0,
        "care_resolve": 1.0,
        "final_position": 1.0,
        "distance_to_optimum": 0.0,
        "max_distance": 3.0,
        "total_dissatisfaction": 0.0,
        "per_agent_loss": {"GPT4o": 0.0, "Claude35": 0.0, "Llama33": 0.0},
        "agents_count": 3,
        "per_agent": {},
    }


@pytest.fixture
def mock_meaning_debt_result():
    """Expected shape of compute_meaning_debt() output."""
    return {
        "total_meaning_debt": 0.0,
        "per_agent_debt": {},
        "debt_curve": [],
        "unresolved_conflicts": 0,
        "total_conflicts": 0,
        "total_resolutions": 0,
        "unsaid_total": 0,
        "unsaid_growing": False,
        "fairness_index": None,
        "fairness_method": None,
        "health_assessment": "healthy",
    }


@pytest.fixture
def mock_dialogue_metrics_result():
    """Expected shape of extract_dialogue_metrics() output."""
    return {
        "consensus_reached": True,
        "consensus_round": 1,
        "rounds_total": 4,
        "avg_protocol_compliance": 0.5,
        "atoms_used": {},
        "unique_atoms_count": 0,
        "emergent_atoms": [],
        "emergent_atoms_count": 0,
        "total_chars": 0,
        "avg_message_length": 0,
        "both_goals_addressed": False,
    }
