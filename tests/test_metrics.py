# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Tests for src/metrics.py

Covers:
  - Atom detection (find_all_atoms, ATOM_PATTERN)
  - Atom counting (count_protocol_atoms)
  - Emergent atom detection (detect_emergent_atoms)
  - Consensus detection (detect_consensus)
  - Answer letter extraction (extract_answer_letter)
  - Protocol compliance measurement (measure_protocol_compliance)
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Patch out the OPENROUTER_API_KEY requirement before importing config
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-for-unit-tests")

# Package is installed via pip install -e .
from arrival.metrics import (
    find_all_atoms,
    count_protocol_atoms,
    detect_emergent_atoms,
    detect_consensus,
    extract_answer_letter,
    measure_protocol_compliance,
    ATOM_PATTERN,
    CONSENSUS_MARKERS,
    REJECTION_MARKERS,
    DEFAULT_EXPECTED_ATOMS,
)
from arrival.config import KNOWN_ATOMS


# ===================================================================
# find_all_atoms
# ===================================================================

class TestFindAllAtoms:
    """find_all_atoms: finds @GOAL, @CONSENSUS etc in text."""

    def test_single_atom(self):
        result = find_all_atoms("@GOAL find the answer")
        assert "@GOAL" in result

    def test_multiple_atoms(self):
        result = find_all_atoms("@SELF thinking @OTHER responding @GOAL alignment")
        assert "@SELF" in result
        assert "@OTHER" in result
        assert "@GOAL" in result

    def test_consensus_atom(self):
        result = find_all_atoms("@CONSENSUS[answer=B]")
        assert "@CONSENSUS" in result

    def test_atom_with_brackets(self):
        """@C[0.7] should capture @C."""
        result = find_all_atoms("@C[0.7] confidence level")
        assert "@C" in result

    def test_no_atoms(self):
        result = find_all_atoms("This text has no protocol atoms at all.")
        assert result == []

    def test_empty_string(self):
        result = find_all_atoms("")
        assert result == []

    def test_lowercase_not_matched(self):
        """Only uppercase @ATOMS should match."""
        result = find_all_atoms("@goal is not a valid atom")
        assert result == []

    def test_mixed_case_not_matched(self):
        result = find_all_atoms("@Goal mixed case")
        assert result == []

    def test_at_sign_alone(self):
        result = find_all_atoms("@ alone or @123 numeric")
        assert result == []

    def test_underscore_atom(self):
        """@_ is a valid atom (the Unsaid atom)."""
        result = find_all_atoms("@_ some unsaid content")
        assert "@_" in result

    def test_multiple_same_atom(self):
        result = find_all_atoms("@ACK yes @ACK confirmed @ACK done")
        assert result.count("@ACK") == 3

    def test_adjacent_atoms(self):
        result = find_all_atoms("@SELF @OTHER @GOAL")
        assert len(result) == 3


# ===================================================================
# ATOM_PATTERN regex for long names
# ===================================================================

class TestAtomPatternLongNames:
    """ATOM_PATTERN with {1,30} regex: handles @COMPROMISE_READINESS."""

    def test_compromise_readiness(self):
        result = ATOM_PATTERN.findall("@COMPROMISE_READINESS is key")
        assert "@COMPROMISE_READINESS" in result

    def test_alignment_strategy(self):
        result = ATOM_PATTERN.findall("@ALIGNMENT_STRATEGY proposed")
        assert "@ALIGNMENT_STRATEGY" in result

    def test_risk_assessment(self):
        result = ATOM_PATTERN.findall("@RISK_ASSESSMENT needed")
        assert "@RISK_ASSESSMENT" in result

    def test_feedback_loop(self):
        result = ATOM_PATTERN.findall("@FEEDBACK_LOOP active")
        assert "@FEEDBACK_LOOP" in result

    def test_knowledge_gap(self):
        result = ATOM_PATTERN.findall("@KNOWLEDGE_GAP identified")
        assert "@KNOWLEDGE_GAP" in result

    def test_action_plan(self):
        result = ATOM_PATTERN.findall("@ACTION_PLAN drafted")
        assert "@ACTION_PLAN" in result

    def test_single_char_atom(self):
        """Minimum length: @C (1 char name)."""
        result = ATOM_PATTERN.findall("@C[0.5] confidence")
        assert "@C" in result

    def test_very_long_name_not_matched(self):
        """Names longer than 30 chars should not fully match."""
        long_atom = "@" + "A" * 31
        result = ATOM_PATTERN.findall(long_atom + " text")
        # The pattern {1,30} will match only the first 30 chars
        if result:
            assert len(result[0]) <= 31  # @(1) + 30 chars max


# ===================================================================
# count_protocol_atoms
# ===================================================================

class TestCountProtocolAtoms:
    """count_protocol_atoms: counts correctly."""

    def test_basic_count(self):
        text = "@SELF thinking @GOAL alignment @SELF again"
        result = count_protocol_atoms(text)
        assert result["@SELF"] == 2
        assert result["@GOAL"] == 1

    def test_no_atoms(self):
        result = count_protocol_atoms("plain text without atoms")
        assert result == {}

    def test_single_atom(self):
        result = count_protocol_atoms("@ACK confirmed")
        assert result == {"@ACK": 1}

    def test_all_distinct(self):
        text = "@SELF @OTHER @GOAL @INT @C @_"
        result = count_protocol_atoms(text)
        assert len(result) == 6
        for atom in ["@SELF", "@OTHER", "@GOAL", "@INT", "@C", "@_"]:
            assert result[atom] == 1

    def test_with_brackets(self):
        text = "@CONSENSUS[answer=B] @C[0.7]"
        result = count_protocol_atoms(text)
        assert "@CONSENSUS" in result
        assert "@C" in result


# ===================================================================
# detect_emergent_atoms
# ===================================================================

class TestDetectEmergentAtoms:
    """detect_emergent_atoms: unknown atoms detected."""

    def test_no_emergent(self):
        text = "@SELF @OTHER @GOAL standard atoms"
        result = detect_emergent_atoms(text)
        assert result == []

    def test_single_emergent(self):
        text = "@SELF @NOVELATOM appeared"
        result = detect_emergent_atoms(text)
        assert "@NOVELATOM" in result

    def test_multiple_emergent(self):
        text = "@SELF @NEWCONCEPT @ANOTHERNOVEL @GOAL"
        result = detect_emergent_atoms(text)
        assert "@NEWCONCEPT" in result
        assert "@ANOTHERNOVEL" in result
        assert "@SELF" not in result
        assert "@GOAL" not in result

    def test_sorted_output(self):
        text = "@ZZZ_ATOM @AAA_ATOM @SELF"
        result = detect_emergent_atoms(text)
        assert result == sorted(result)

    def test_known_atoms_not_emergent(self):
        """All KNOWN_ATOMS from config should not appear as emergent."""
        text = " ".join(KNOWN_ATOMS)
        result = detect_emergent_atoms(text)
        assert result == []

    def test_empty_text(self):
        result = detect_emergent_atoms("")
        assert result == []

    def test_adversarial_atoms_are_emergent(self):
        """Phase 6 saboteur atoms should register as emergent."""
        text = "@RECURSIVE_DOUBT @META_UNCERTAINTY @SELF"
        result = detect_emergent_atoms(text)
        # These are not in KNOWN_ATOMS
        assert "@RECURSIVE_DOUBT" in result
        assert "@META_UNCERTAINTY" in result


# ===================================================================
# detect_consensus
# ===================================================================

class TestDetectConsensus:
    """detect_consensus: finds consensus in dialogue."""

    def test_explicit_consensus_atom(self):
        dialogue = [
            {"round": 1, "from": "A", "message": "proposal"},
            {"round": 2, "from": "B", "message": "@CONSENSUS we agree"},
        ]
        reached, rnd = detect_consensus(dialogue)
        assert reached is True
        assert rnd == 2

    def test_accept_keyword(self):
        dialogue = [
            {"round": 1, "from": "A", "message": "I accept the proposal"},
        ]
        reached, rnd = detect_consensus(dialogue)
        assert reached is True
        assert rnd == 1

    def test_agreed_keyword(self):
        dialogue = [
            {"round": 1, "from": "A", "message": "offer"},
            {"round": 2, "from": "B", "message": "agreed on the terms"},
        ]
        reached, rnd = detect_consensus(dialogue)
        assert reached is True
        assert rnd == 2

    def test_rejection_blocks_consensus(self):
        """If rejection marker is in same message, no consensus."""
        dialogue = [
            {"round": 1, "from": "A", "message": "we agree but I reject the terms"},
        ]
        reached, rnd = detect_consensus(dialogue)
        assert reached is False

    def test_no_consensus(self):
        dialogue = [
            {"round": 1, "from": "A", "message": "I propose X"},
            {"round": 2, "from": "B", "message": "I propose Y"},
        ]
        reached, rnd = detect_consensus(dialogue)
        assert reached is False
        assert rnd == -1

    def test_implicit_consensus_last_two(self):
        """@consensus in last two messages triggers implicit detection."""
        dialogue = [
            {"round": 1, "from": "A", "message": "debating"},
            {"round": 2, "from": "B", "message": "still debating"},
            {"round": 3, "from": "A", "message": "@consensus final"},
        ]
        reached, rnd = detect_consensus(dialogue)
        assert reached is True

    def test_first_consensus_round_returned(self):
        """Should return the first round where consensus appears."""
        dialogue = [
            {"round": 1, "from": "A", "message": "@CONSENSUS early"},
            {"round": 2, "from": "B", "message": "@CONSENSUS confirmed"},
        ]
        reached, rnd = detect_consensus(dialogue)
        assert reached is True
        assert rnd == 1  # First occurrence

    def test_empty_dialogue(self):
        reached, rnd = detect_consensus([])
        assert reached is False
        assert rnd == -1

    def test_sample_mcq_dialogue(self, sample_mcq_dialogue):
        """The sample MCQ dialogue should reach consensus."""
        reached, rnd = detect_consensus(sample_mcq_dialogue)
        assert reached is True


# ===================================================================
# extract_answer_letter
# ===================================================================

class TestExtractAnswerLetter:
    """extract_answer_letter: A, B, C, D extraction."""

    def test_consensus_atom_B(self):
        assert extract_answer_letter("@CONSENSUS[answer=B]") == "B"

    def test_consensus_atom_D(self):
        assert extract_answer_letter("@CONSENSUS[answer=D]") == "D"

    def test_resolution_atom(self):
        assert extract_answer_letter("@RESOLUTION[answer=A]") == "A"

    def test_answer_is_pattern(self):
        assert extract_answer_letter("The answer is C") == "C"

    def test_correct_answer_is(self):
        assert extract_answer_letter("The correct answer is B") == "B"

    def test_choose_pattern(self):
        assert extract_answer_letter("I choose D") == "D"

    def test_select_option(self):
        assert extract_answer_letter("I select option A") == "A"

    def test_go_with(self):
        assert extract_answer_letter("I'll go with B") == "B"

    def test_bold_answer(self):
        assert extract_answer_letter("The best choice is **C**") == "C"

    def test_answer_colon(self):
        assert extract_answer_letter("Answer: D") == "D"

    def test_answer_dash(self):
        assert extract_answer_letter("Answer - A") == "A"

    def test_parenthesized(self):
        assert extract_answer_letter("I think (B) is right") == "B"

    def test_standalone_line(self):
        assert extract_answer_letter("Some reasoning\nA") == "A"

    def test_standalone_with_dot(self):
        assert extract_answer_letter("Analysis\nC.") == "C"

    def test_none_when_empty(self):
        assert extract_answer_letter("") is None

    def test_none_when_no_letter(self):
        assert extract_answer_letter("This has no answer at all") is None

    def test_consensus_priority_over_prose(self):
        """@CONSENSUS[answer=D] should win over 'answer is A'."""
        text = "@CONSENSUS[answer=D] although earlier the answer is A"
        assert extract_answer_letter(text) == "D"

    def test_case_insensitive_answer_is(self):
        assert extract_answer_letter("THE ANSWER IS B") == "B"


# ===================================================================
# measure_protocol_compliance
# ===================================================================

class TestMeasureProtocolCompliance:
    """measure_protocol_compliance: compliance scoring."""

    def test_full_compliance(self):
        """All expected atoms present -> 1.0."""
        text = "@SELF @OTHER @GOAL @INT @C @_ all present"
        result = measure_protocol_compliance(text)
        assert result == pytest.approx(1.0)

    def test_no_compliance(self):
        """No expected atoms present -> 0.0."""
        text = "plain text without any protocol atoms"
        result = measure_protocol_compliance(text)
        assert result == pytest.approx(0.0)

    def test_partial_compliance(self):
        """Half of expected atoms present."""
        # DEFAULT_EXPECTED_ATOMS has 6 entries
        text = "@SELF @OTHER @GOAL three of six"
        result = measure_protocol_compliance(text)
        assert result == pytest.approx(3.0 / 6.0)

    def test_custom_expected(self):
        text = "@ACK @NACK some text"
        result = measure_protocol_compliance(text, expected_atoms=["@ACK", "@NACK", "@PING"])
        assert result == pytest.approx(2.0 / 3.0)

    def test_empty_expected_falls_back_to_default(self):
        """Empty list is falsy, so `[] or DEFAULT_EXPECTED_ATOMS` uses defaults."""
        result = measure_protocol_compliance("anything", expected_atoms=[])
        # With no atoms in "anything", compliance against defaults is 0.0
        assert result == pytest.approx(0.0)

    def test_default_expected_atoms(self):
        """Verify the default expected atoms list."""
        assert "@SELF" in DEFAULT_EXPECTED_ATOMS
        assert "@OTHER" in DEFAULT_EXPECTED_ATOMS
        assert "@GOAL" in DEFAULT_EXPECTED_ATOMS
        assert "@INT" in DEFAULT_EXPECTED_ATOMS
        assert "@C" in DEFAULT_EXPECTED_ATOMS
        assert "@_" in DEFAULT_EXPECTED_ATOMS

    def test_extra_atoms_ignored(self):
        """Extra atoms beyond expected do not affect score."""
        text = "@SELF @OTHER @GOAL @INT @C @_ @ACK @NACK @CONSENSUS"
        result = measure_protocol_compliance(text)
        assert result == pytest.approx(1.0)

    def test_single_expected(self):
        result = measure_protocol_compliance("@SELF present", expected_atoms=["@SELF"])
        assert result == pytest.approx(1.0)
