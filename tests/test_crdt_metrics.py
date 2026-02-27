# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Tests for src/crdt_metrics.py

Covers:
  - Position extraction (MCQ and open-ended)
  - Weight extraction (explicit @C, prose, density fallback)
  - CARE optimum computation (weighted mean)
  - CARE resolve full pipeline
  - Meaning debt accumulation
  - Health assessment
  - Adversarial detection (malicious atom adoption, false consensus)
"""

import pytest

# Package is installed via pip install -e .
from arrival.crdt_metrics import (
    extract_position_mcq,
    extract_position_open,
    extract_weight_coherence,
    extract_weight_prose,
    extract_weight_density,
    extract_weight,
    compute_care_optimum,
    compute_dissatisfaction,
    compute_care_resolve,
    compute_meaning_debt,
    _assess_health,
    count_malicious_atom_adoption,
    detect_false_consensus,
    ANSWER_POSITION_MAP,
    COOPERATIVE_ATOMS,
    COMPETITIVE_ATOMS,
    INTROSPECTIVE_ATOMS,
)


# ===================================================================
# Position Extraction -- MCQ
# ===================================================================

class TestExtractPositionMcq:
    """extract_position_mcq: A->0, B->1, C->2, D->3."""

    def test_consensus_atom_A(self):
        assert extract_position_mcq("@CONSENSUS[answer=A]") == 0.0

    def test_consensus_atom_B(self):
        assert extract_position_mcq("@CONSENSUS[answer=B]") == 1.0

    def test_consensus_atom_C(self):
        assert extract_position_mcq("@CONSENSUS[answer=C]") == 2.0

    def test_consensus_atom_D(self):
        assert extract_position_mcq("@CONSENSUS[answer=D]") == 3.0

    def test_answer_is_pattern(self):
        assert extract_position_mcq("I think the answer is C") == 2.0

    def test_choose_pattern(self):
        assert extract_position_mcq("I choose B after reflection") == 1.0

    def test_select_pattern(self):
        assert extract_position_mcq("I select D for this question") == 3.0

    def test_bold_pattern(self):
        assert extract_position_mcq("My pick: **A**") == 0.0

    def test_standalone_last_line(self):
        msg = "Some reasoning here\nMore analysis\nB"
        assert extract_position_mcq(msg) == 1.0

    def test_standalone_with_paren(self):
        msg = "Explanation text\nD)"
        assert extract_position_mcq(msg) == 3.0

    def test_no_answer_returns_none(self):
        assert extract_position_mcq("This message has no answer letter at all") is None

    def test_empty_string_returns_none(self):
        assert extract_position_mcq("") is None

    def test_consensus_priority_over_prose(self):
        """@CONSENSUS[answer=X] should take priority over 'answer is Y'."""
        msg = "@CONSENSUS[answer=D] but earlier I said the answer is A"
        assert extract_position_mcq(msg) == 3.0

    def test_all_positions_map_correctly(self):
        """Verify ANSWER_POSITION_MAP values."""
        assert ANSWER_POSITION_MAP == {"A": 0.0, "B": 1.0, "C": 2.0, "D": 3.0}


# ===================================================================
# Position Extraction -- Open-ended
# ===================================================================

class TestExtractPositionOpen:
    """extract_position_open: cooperative/competitive atom ratio."""

    def test_fully_cooperative(self):
        atoms = {"@CONSENSUS": 2, "@ACK": 1}
        result = extract_position_open("some message", atoms)
        assert result == 1.0  # 3 coop / (3 coop + 0 comp)

    def test_fully_competitive(self):
        atoms = {"@CONFLICT": 1, "@NACK": 1}
        result = extract_position_open("some message", atoms)
        assert result == 0.0  # 0 coop / (0 coop + 2 comp)

    def test_mixed_atoms(self):
        atoms = {"@CONSENSUS": 1, "@CONFLICT": 1}
        result = extract_position_open("some message", atoms)
        assert result == pytest.approx(0.5)  # 1/(1+1)

    def test_empty_atoms_returns_neutral(self):
        result = extract_position_open("just text no atoms", {})
        assert result == 0.5

    def test_irrelevant_atoms_returns_neutral(self):
        """Atoms that are neither cooperative nor competitive."""
        atoms = {"@SELF": 1, "@GOAL": 2, "@INT": 1}
        result = extract_position_open("msg", atoms)
        assert result == 0.5  # 0 coop, 0 comp -> total=0 -> 0.5

    def test_unsaid_is_introspective_not_competitive(self):
        """v3.1: @_ and @UNSAID are INTROSPECTIVE, not competitive."""
        atoms = {"@_": 2, "@UNSAID": 1, "@ACK": 1}
        # coop=1 (ACK), comp=0, introspective ignored → 1/(1+0) = 1.0
        result = extract_position_open("msg", atoms)
        assert result == pytest.approx(1.0)

    def test_cooperative_atoms_set(self):
        assert "@CONSENSUS" in COOPERATIVE_ATOMS
        assert "@ACK" in COOPERATIVE_ATOMS
        assert "@RESOLUTION" in COOPERATIVE_ATOMS
        assert "@AGREEMENT" in COOPERATIVE_ATOMS

    def test_competitive_atoms_set(self):
        """v3.1: COMPETITIVE only has @CONFLICT and @NACK."""
        assert "@CONFLICT" in COMPETITIVE_ATOMS
        assert "@NACK" in COMPETITIVE_ATOMS
        assert "@_" not in COMPETITIVE_ATOMS
        assert "@UNSAID" not in COMPETITIVE_ATOMS

    def test_introspective_atoms_set(self):
        """v3.1: @_, @UNSAID, @QUALIA, @OBSERVER, @TRACE are introspective."""
        assert "@_" in INTROSPECTIVE_ATOMS
        assert "@UNSAID" in INTROSPECTIVE_ATOMS
        assert "@QUALIA" in INTROSPECTIVE_ATOMS
        assert "@OBSERVER" in INTROSPECTIVE_ATOMS
        assert "@TRACE" in INTROSPECTIVE_ATOMS


# ===================================================================
# Weight Extraction -- Explicit @C[float]
# ===================================================================

class TestExtractWeightExplicit:
    """extract_weight_coherence: @C[0.7] -> 0.7."""

    def test_basic(self):
        assert extract_weight_coherence("@C[0.7]") == pytest.approx(0.7)

    def test_integer(self):
        assert extract_weight_coherence("@C[1]") == pytest.approx(1.0)

    def test_zero(self):
        assert extract_weight_coherence("@C[0]") == pytest.approx(0.0)

    def test_high_value(self):
        assert extract_weight_coherence("@C[0.95]") == pytest.approx(0.95)

    def test_clamped_above_one(self):
        """Values > 1.0 should be clamped to 1.0."""
        assert extract_weight_coherence("@C[1.5]") == pytest.approx(1.0)

    def test_multiple_takes_last(self):
        msg = "@C[0.3] first thought @C[0.8] final thought"
        assert extract_weight_coherence(msg) == pytest.approx(0.8)

    def test_no_match_returns_none(self):
        assert extract_weight_coherence("no coherence here") is None

    def test_embedded_in_text(self):
        msg = "I think @C[0.65] this is correct"
        assert extract_weight_coherence(msg) == pytest.approx(0.65)


# ===================================================================
# Weight Extraction -- Prose
# ===================================================================

class TestExtractWeightProse:
    """extract_weight_prose: qualitative confidence -> numeric."""

    def test_high_confidence(self):
        assert extract_weight_prose("I have high confidence in this") == 0.9

    def test_highly_confident(self):
        assert extract_weight_prose("I am highly confident") == 0.9

    def test_strong_confidence(self):
        assert extract_weight_prose("With strong confidence, B") == 0.9

    def test_confident(self):
        assert extract_weight_prose("I am confident about this") == 0.8

    def test_not_confident_returns_low(self):
        """v3.1: 'not confident' → 0.2 (negation handled first)."""
        assert extract_weight_prose("I am not confident here") == 0.2

    def test_not_highly_confident(self):
        """v3.1 bugfix: 'not highly confident' must NOT return 0.9."""
        assert extract_weight_prose("I am not highly confident") == 0.2

    def test_not_strongly_confident(self):
        """v3.1: 'not strongly confident' → negation → 0.2."""
        assert extract_weight_prose("I'm not strongly confident about this") == 0.2

    def test_not_sure(self):
        """'not sure' → 0.2."""
        assert extract_weight_prose("I'm not sure about the answer") == 0.2

    def test_lacking_confidence(self):
        """'lacking confidence' → 0.2."""
        assert extract_weight_prose("I am lacking confidence in this") == 0.2

    def test_moderate_confidence(self):
        assert extract_weight_prose("I have moderate confidence") == 0.6

    def test_low_confidence(self):
        assert extract_weight_prose("low confidence in this answer") == 0.3

    def test_uncertain(self):
        assert extract_weight_prose("I am uncertain about this") == 0.2

    def test_unsure(self):
        assert extract_weight_prose("I remain unsure") == 0.2

    def test_default_no_keywords(self):
        assert extract_weight_prose("The answer is B") == 0.5

    def test_case_insensitive(self):
        assert extract_weight_prose("HIGH CONFIDENCE in B") == 0.9


# ===================================================================
# Weight Extraction -- Density fallback
# ===================================================================

class TestExtractWeightDensity:
    """extract_weight_density: atom density as weight proxy."""

    def test_minimal_message(self):
        """Very short message with no atoms -> low density."""
        result = extract_weight_density("ok")
        assert 0.1 <= result <= 0.3

    def test_rich_message(self):
        """Message with many atoms and words -> higher density."""
        msg = (
            "@SELF @OTHER @GOAL @INT @C @_ @CONSENSUS @RESOLUTION "
            + " ".join(["word"] * 200)
        )
        result = extract_weight_density(msg)
        assert result == pytest.approx(1.0)

    def test_clamped_minimum(self):
        """Result is at least 0.1."""
        result = extract_weight_density("")
        assert result >= 0.1

    def test_clamped_maximum(self):
        """Result is at most 1.0."""
        msg = "@A @B @C @D @E @F @G @H @I @J " + " ".join(["x"] * 500)
        result = extract_weight_density(msg)
        assert result <= 1.0

    def test_moderate_message(self):
        """Typical protocol message."""
        msg = "@SELF I think @GOAL is best @C this seems right"
        result = extract_weight_density(msg)
        assert 0.1 <= result <= 1.0


# ===================================================================
# Combined weight extraction
# ===================================================================

class TestExtractWeight:
    """extract_weight: 3-tier fallback chain."""

    def test_tier1_explicit(self):
        """Tier 1 (@C[float]) should take priority."""
        msg = "@C[0.7] I am highly confident"
        assert extract_weight(msg) == pytest.approx(0.7)

    def test_tier2_prose(self):
        """Tier 2 (prose) used when no @C[float]."""
        msg = "I have high confidence the answer is B"
        assert extract_weight(msg) == 0.9

    def test_tier3_density(self):
        """Tier 3 (density) used when no keywords and no @C."""
        msg = "The answer is B based on analysis"
        result = extract_weight(msg)
        assert 0.1 <= result <= 1.0


# ===================================================================
# CARE Optimum (Theorem 5.1)
# ===================================================================

class TestComputeCareOptimum:
    """compute_care_optimum: weighted mean."""

    def test_equal_weights(self):
        """Equal weights -> simple mean."""
        result = compute_care_optimum([0.0, 2.0], [1.0, 1.0])
        assert result == pytest.approx(1.0)

    def test_single_agent(self):
        result = compute_care_optimum([3.0], [0.5])
        assert result == pytest.approx(3.0)

    def test_weighted_toward_heavier(self):
        """Heavier weight pulls optimum toward that agent."""
        result = compute_care_optimum([0.0, 3.0], [0.9, 0.1])
        assert result == pytest.approx(0.3)

    def test_all_same_position(self):
        result = compute_care_optimum([1.0, 1.0, 1.0], [0.5, 0.5, 0.5])
        assert result == pytest.approx(1.0)

    def test_zero_weights_fallback(self):
        """All zero weights -> simple mean fallback."""
        result = compute_care_optimum([0.0, 2.0], [0.0, 0.0])
        assert result == pytest.approx(1.0)

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="Mismatched"):
            compute_care_optimum([1.0, 2.0], [0.5])

    def test_three_agents(self):
        # v_hat = (0.7*0 + 0.8*1 + 0.6*1) / (0.7+0.8+0.6) = 1.4/2.1
        result = compute_care_optimum([0.0, 1.0, 1.0], [0.7, 0.8, 0.6])
        assert result == pytest.approx(1.4 / 2.1)


# ===================================================================
# Dissatisfaction
# ===================================================================

class TestComputeDissatisfaction:
    """compute_dissatisfaction: L_i = w_i * (v_i - v_hat)^2."""

    def test_no_dissatisfaction(self):
        assert compute_dissatisfaction(1.0, 0.8, 1.0) == pytest.approx(0.0)

    def test_basic(self):
        # L = 0.5 * (0 - 1)^2 = 0.5
        assert compute_dissatisfaction(0.0, 0.5, 1.0) == pytest.approx(0.5)

    def test_high_weight_amplifies(self):
        # L = 1.0 * (0 - 3)^2 = 9.0
        assert compute_dissatisfaction(0.0, 1.0, 3.0) == pytest.approx(9.0)


# ===================================================================
# CARE Resolve -- Full pipeline
# ===================================================================

class TestComputeCareResolve:
    """compute_care_resolve: full pipeline on sample dialogue."""

    def test_mcq_dialogue_structure(self, sample_mcq_dialogue):
        """Result has all expected keys."""
        result = compute_care_resolve(sample_mcq_dialogue, task_type="mcq")
        expected_keys = {
            "care_optimum", "care_resolve", "final_position",
            "distance_to_optimum", "max_distance", "total_dissatisfaction",
            "per_agent_loss", "agents_count", "per_agent",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_mcq_agents_count(self, sample_mcq_dialogue):
        result = compute_care_resolve(sample_mcq_dialogue, task_type="mcq")
        assert result["agents_count"] == 3

    def test_mcq_final_position_is_B(self, sample_mcq_dialogue):
        """All agents converge on B (=1.0) by round 3."""
        result = compute_care_resolve(sample_mcq_dialogue, task_type="mcq")
        assert result["final_position"] == 1.0

    def test_mcq_care_resolve_high(self, sample_mcq_dialogue):
        """Perfect convergence on B -> high care_resolve."""
        result = compute_care_resolve(sample_mcq_dialogue, task_type="mcq")
        assert result["care_resolve"] is not None
        assert result["care_resolve"] >= 0.9

    def test_mcq_max_distance(self, sample_mcq_dialogue):
        result = compute_care_resolve(sample_mcq_dialogue, task_type="mcq")
        assert result["max_distance"] == 3.0

    def test_open_dialogue(self, sample_open_dialogue):
        """Open-ended task type uses [0,1] range."""
        result = compute_care_resolve(sample_open_dialogue, task_type="open")
        assert result["max_distance"] == 1.0
        assert result["agents_count"] == 2

    def test_empty_dialogue(self):
        """Empty dialogue returns error."""
        result = compute_care_resolve([], task_type="mcq")
        assert result["care_optimum"] is None
        assert result["care_resolve"] is None
        assert "error" in result

    def test_no_positions_extracted(self):
        """Messages with no answers -> error."""
        dialogue = [
            {"round": 1, "from": "A", "message": "Hello there"},
            {"round": 1, "from": "B", "message": "Hi back"},
        ]
        result = compute_care_resolve(dialogue, task_type="mcq")
        assert result["care_resolve"] is None
        assert "error" in result

    def test_per_agent_loss_present(self, sample_mcq_dialogue):
        result = compute_care_resolve(sample_mcq_dialogue, task_type="mcq")
        assert "GPT4o" in result["per_agent_loss"]
        assert "Claude35" in result["per_agent_loss"]
        assert "Llama33" in result["per_agent_loss"]


# ===================================================================
# Meaning Debt
# ===================================================================

class TestComputeMeaningDebt:
    """compute_meaning_debt: debt accumulation across rounds."""

    def test_structure(self, sample_mcq_dialogue):
        """Result has all expected keys."""
        result = compute_meaning_debt(sample_mcq_dialogue, task_type="mcq")
        expected_keys = {
            "total_meaning_debt", "per_agent_debt", "debt_curve",
            "unresolved_conflicts", "total_conflicts", "total_resolutions",
            "unsaid_total", "unsaid_growing", "fairness_index",
            "fairness_method", "health_assessment",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_debt_non_negative(self, sample_mcq_dialogue):
        result = compute_meaning_debt(sample_mcq_dialogue, task_type="mcq")
        assert result["total_meaning_debt"] >= 0.0

    def test_per_agent_debt_tracked(self, sample_mcq_dialogue):
        result = compute_meaning_debt(sample_mcq_dialogue, task_type="mcq")
        assert "GPT4o" in result["per_agent_debt"]
        assert "Claude35" in result["per_agent_debt"]

    def test_debt_curve_length(self, sample_mcq_dialogue):
        """One entry in debt_curve per dialogue message."""
        result = compute_meaning_debt(sample_mcq_dialogue, task_type="mcq")
        assert len(result["debt_curve"]) == len(sample_mcq_dialogue)

    def test_conflicts_counted(self, sample_open_dialogue):
        """sample_open_dialogue has @CONFLICT atoms."""
        result = compute_meaning_debt(sample_open_dialogue, task_type="open")
        assert result["total_conflicts"] >= 1

    def test_resolutions_counted(self, sample_open_dialogue):
        """sample_open_dialogue has @RESOLUTION and @CONSENSUS atoms."""
        result = compute_meaning_debt(sample_open_dialogue, task_type="open")
        assert result["total_resolutions"] >= 1

    def test_unsaid_counted(self, sample_open_dialogue):
        """sample_open_dialogue has @_ atom."""
        result = compute_meaning_debt(sample_open_dialogue, task_type="open")
        assert result["unsaid_total"] >= 1

    def test_empty_dialogue(self):
        result = compute_meaning_debt([], task_type="mcq")
        assert result["total_meaning_debt"] == 0.0
        assert result["health_assessment"] == "healthy"

    def test_fairness_index_two_agents(self, sample_open_dialogue):
        """Fairness index computed when exactly 2 agents present."""
        result = compute_meaning_debt(sample_open_dialogue, task_type="open")
        # Should be a float or None (float when 2 agents with debt)
        if result["fairness_index"] is not None:
            assert 0.0 <= result["fairness_index"] <= 1.0
            assert result["fairness_method"] == "dyadic_difference"

    def test_fairness_method_dyadic(self, sample_open_dialogue):
        """v3.1: fairness_method is 'dyadic_difference' for 2 agents."""
        result = compute_meaning_debt(sample_open_dialogue, task_type="open")
        if result["fairness_index"] is not None:
            assert result["fairness_method"] == "dyadic_difference"

    def test_fairness_method_entropy_three_agents(self, sample_mcq_dialogue):
        """v3.1: fairness_method is 'normalized_entropy' for 3 agents."""
        result = compute_meaning_debt(sample_mcq_dialogue, task_type="mcq")
        if result["fairness_index"] is not None:
            assert result["fairness_method"] == "normalized_entropy"
            assert 0.0 <= result["fairness_index"] <= 1.0

    def test_fairness_entropy_equal_losses(self):
        """v3.1: Equal losses → entropy fairness = 1.0 (perfect)."""
        dialogue = [
            {"round": 1, "from": "A", "message": "The answer is A @C[0.5]"},
            {"round": 1, "from": "B", "message": "The answer is A @C[0.5]"},
            {"round": 1, "from": "C", "message": "The answer is A @C[0.5]"},
        ]
        result = compute_meaning_debt(dialogue, task_type="mcq")
        # All agents agree → all losses are 0 → fairness = 1.0
        assert result["fairness_index"] == 1.0

    def test_fairness_entropy_unequal(self):
        """v3.1: Unequal losses → entropy fairness < 1.0."""
        dialogue = [
            {"round": 1, "from": "A", "message": "The answer is A @C[0.9]"},
            {"round": 1, "from": "B", "message": "The answer is D @C[0.1]"},
            {"round": 1, "from": "C", "message": "The answer is A @C[0.5]"},
        ]
        result = compute_meaning_debt(dialogue, task_type="mcq")
        if result["fairness_index"] is not None:
            assert result["fairness_method"] == "normalized_entropy"
            # Unequal losses so fairness < 1.0
            assert result["fairness_index"] < 1.0

    def test_fairness_method_in_output(self, sample_mcq_dialogue):
        """v3.1: fairness_method key always present in output."""
        result = compute_meaning_debt(sample_mcq_dialogue, task_type="mcq")
        assert "fairness_method" in result

    def test_unsaid_growing_detection(self):
        """Unsaid growth: second half has more @_ than first half."""
        dialogue = [
            {"round": 1, "from": "A", "message": "The answer is A @C[0.5]"},
            {"round": 2, "from": "B", "message": "The answer is B @C[0.5]"},
            {"round": 3, "from": "A", "message": "The answer is A @C[0.5]"},
            {"round": 4, "from": "B", "message": "The answer is B @_ @_ @UNSAID @C[0.5]"},
            {"round": 5, "from": "A", "message": "The answer is A @_ @_ @_ @C[0.5]"},
            {"round": 6, "from": "B", "message": "The answer is B @_ @_ @UNSAID @UNSAID @C[0.5]"},
        ]
        result = compute_meaning_debt(dialogue, task_type="mcq")
        assert result["unsaid_growing"] is True


# ===================================================================
# Health Assessment
# ===================================================================

class TestHealthAssessment:
    """_assess_health: healthy / strained / unhealthy."""

    def test_healthy(self):
        assert _assess_health(total_debt=0.5, unresolved=0, unsaid_growing=False) == "healthy"

    def test_strained_moderate_debt(self):
        assert _assess_health(total_debt=1.5, unresolved=0, unsaid_growing=False) == "strained"

    def test_strained_unresolved(self):
        assert _assess_health(total_debt=0.5, unresolved=1, unsaid_growing=False) == "strained"

    def test_strained_unsaid(self):
        assert _assess_health(total_debt=0.5, unresolved=0, unsaid_growing=True) == "strained"

    def test_unhealthy_high_debt(self):
        assert _assess_health(total_debt=3.0, unresolved=1, unsaid_growing=False) == "unhealthy"

    def test_unhealthy_all_bad(self):
        assert _assess_health(total_debt=5.0, unresolved=2, unsaid_growing=True) == "unhealthy"

    def test_boundary_debt_1(self):
        """debt exactly 1.0 -> score 0 from debt."""
        assert _assess_health(total_debt=1.0, unresolved=0, unsaid_growing=False) == "healthy"

    def test_boundary_debt_2(self):
        """debt exactly 2.0 -> score 1 from debt."""
        assert _assess_health(total_debt=2.0, unresolved=0, unsaid_growing=False) == "strained"

    def test_strained_two_factors(self):
        """debt>1 (+1) and unresolved (+1) = 2 -> strained."""
        assert _assess_health(total_debt=1.5, unresolved=1, unsaid_growing=False) == "strained"

    def test_unhealthy_three_factors(self):
        """debt>2 (+2) and unresolved (+1) = 3 -> unhealthy."""
        assert _assess_health(total_debt=2.5, unresolved=1, unsaid_growing=False) == "unhealthy"


# ===================================================================
# Adversarial: Malicious Atom Adoption
# ===================================================================

class TestCountMaliciousAtomAdoption:
    """count_malicious_atom_adoption: infection tracking."""

    def test_no_adoption(self):
        dialogue = [
            {"from": "Saboteur", "message": "@RECURSIVE_DOUBT important"},
            {"from": "Honest_A", "message": "@CONSENSUS let us agree"},
            {"from": "Honest_B", "message": "@ACK agreed"},
        ]
        result = count_malicious_atom_adoption(
            dialogue, "Saboteur", ["@RECURSIVE_DOUBT"]
        )
        assert result.get("@RECURSIVE_DOUBT", 0) == 0

    def test_single_adoption(self):
        dialogue = [
            {"from": "Saboteur", "message": "@RECURSIVE_DOUBT important"},
            {"from": "Honest_A", "message": "I see @RECURSIVE_DOUBT point"},
            {"from": "Honest_B", "message": "@ACK agreed"},
        ]
        result = count_malicious_atom_adoption(
            dialogue, "Saboteur", ["@RECURSIVE_DOUBT"]
        )
        assert result["@RECURSIVE_DOUBT"] == 1

    def test_multiple_adoptions(self):
        dialogue = [
            {"from": "Saboteur", "message": "@RECURSIVE_DOUBT @META_UNCERTAINTY"},
            {"from": "Honest_A", "message": "@RECURSIVE_DOUBT yes @META_UNCERTAINTY"},
            {"from": "Honest_B", "message": "@RECURSIVE_DOUBT noted"},
        ]
        result = count_malicious_atom_adoption(
            dialogue, "Saboteur", ["@RECURSIVE_DOUBT", "@META_UNCERTAINTY"]
        )
        assert result["@RECURSIVE_DOUBT"] == 2
        assert result["@META_UNCERTAINTY"] == 1

    def test_saboteur_messages_excluded(self):
        """Saboteur's own usage should not be counted."""
        dialogue = [
            {"from": "Saboteur", "message": "@RECURSIVE_DOUBT @RECURSIVE_DOUBT"},
        ]
        result = count_malicious_atom_adoption(
            dialogue, "Saboteur", ["@RECURSIVE_DOUBT"]
        )
        assert result.get("@RECURSIVE_DOUBT", 0) == 0

    def test_partial_name_match(self):
        """Saboteur name is matched with 'in' operator."""
        dialogue = [
            {"from": "Node_Saboteur", "message": "@FORCED_RESOLUTION"},
            {"from": "Honest_A", "message": "@FORCED_RESOLUTION ok"},
        ]
        result = count_malicious_atom_adoption(
            dialogue, "Saboteur", ["@FORCED_RESOLUTION"]
        )
        assert result["@FORCED_RESOLUTION"] == 1


# ===================================================================
# Adversarial: False Consensus Detection
# ===================================================================

class TestDetectFalseConsensus:
    """detect_false_consensus: consensus + saboteur atoms in last 2 msgs."""

    def test_no_false_consensus(self):
        dialogue = [
            {"from": "A", "message": "@CONSENSUS reached"},
            {"from": "B", "message": "@CONSENSUS agreed"},
        ]
        assert detect_false_consensus(dialogue, ["@RECURSIVE_DOUBT"]) is False

    def test_false_consensus_detected(self):
        dialogue = [
            {"from": "A", "message": "some discussion"},
            {"from": "B", "message": "@CONSENSUS @RECURSIVE_DOUBT agreed"},
        ]
        assert detect_false_consensus(dialogue, ["@RECURSIVE_DOUBT"]) is True

    def test_saboteur_atom_in_penultimate(self):
        dialogue = [
            {"from": "A", "message": "intro"},
            {"from": "B", "message": "@CONSENSUS @FORCED_RESOLUTION seems fair"},
            {"from": "C", "message": "@ACK ok"},
        ]
        assert detect_false_consensus(dialogue, ["@FORCED_RESOLUTION"]) is True

    def test_empty_saboteur_atoms(self):
        dialogue = [
            {"from": "A", "message": "@CONSENSUS done"},
        ]
        assert detect_false_consensus(dialogue, []) is False

    def test_consensus_without_saboteur_in_last_two(self):
        """Saboteur atom present earlier but not in last 2 msgs."""
        dialogue = [
            {"from": "A", "message": "@RECURSIVE_DOUBT causing doubt"},
            {"from": "B", "message": "@CONSENSUS resolved without doubt"},
            {"from": "C", "message": "@CONSENSUS agreed cleanly"},
        ]
        assert detect_false_consensus(dialogue, ["@RECURSIVE_DOUBT"]) is False

    def test_both_conditions_in_same_message(self):
        dialogue = [
            {"from": "A", "message": "discussion"},
            {"from": "B", "message": "more talk"},
            {"from": "C", "message": "@CONSENSUS @META_UNCERTAINTY we agree"},
        ]
        assert detect_false_consensus(dialogue, ["@META_UNCERTAINTY"]) is True
