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
Arrival CRDT — Phase 7: Hard Questions Subset
15 hardest questions (3 per domain) selected from Phase 5's 50-question bank.
Selection criteria: harder difficulty, tricky distractors, reasoning required.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PHASE7_QUESTION_IDS
from phase_5.questions import QUESTIONS, DOMAINS

# Build lookup
_QUESTION_MAP = {q["id"]: q for q in QUESTIONS}

HARD_QUESTIONS = [_QUESTION_MAP[qid] for qid in PHASE7_QUESTION_IDS]

def validate_hard_questions():
    """Verify hard question set integrity."""
    assert len(HARD_QUESTIONS) == 15, f"Expected 15, got {len(HARD_QUESTIONS)}"
    for domain in DOMAINS:
        domain_qs = [q for q in HARD_QUESTIONS if q["domain"] == domain]
        assert len(domain_qs) == 3, f"Expected 3 for {domain}, got {len(domain_qs)}"
    print(f"All {len(HARD_QUESTIONS)} hard questions validated across {len(DOMAINS)} domains.")

if __name__ == "__main__":
    validate_hard_questions()
    for q in HARD_QUESTIONS:
        print(f"  {q['id']} ({q['domain']}, {q['difficulty']}): {q['question'][:60]}...")
