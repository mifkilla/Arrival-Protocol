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
Recompute Phase 5 results with fixed answer extraction.

The original extract_answer_letter() failed to parse @CONSENSUS[answer=B] format.
This script re-extracts answers from saved dialogue without re-running API calls.
"""

import json
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(errors='replace')

from metrics import extract_answer_letter


def recompute(input_path: str) -> dict:
    """Re-extract answers from existing ARRIVAL dialogues."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Recomputing {len(data['results'])} results...")
    print(f"Original ARRIVAL accuracy: {data['summary']['arrival']['accuracy']:.1%}")
    print()

    fixed_correct = 0
    extraction_fixed = 0
    still_none = 0

    for r in data['results']:
        correct_answer = r['correct_answer']

        # Re-extract from last round of ARRIVAL dialogue
        last_msg = r['arrival']['dialogue'][-1]['message']
        new_answer = extract_answer_letter(last_msg)

        # If still None, try all rounds (sometimes answer appears earlier)
        if new_answer is None:
            for turn in reversed(r['arrival']['dialogue']):
                new_answer = extract_answer_letter(turn['message'])
                if new_answer is not None:
                    break

        old_answer = r['arrival']['answer']
        r['arrival']['answer'] = new_answer
        r['arrival']['correct'] = (new_answer == correct_answer)

        if r['arrival']['correct']:
            fixed_correct += 1

        if old_answer is None and new_answer is not None:
            extraction_fixed += 1

        if new_answer is None:
            still_none += 1
            print(f"  WARNING: {r['question_id']} still None after fix")

    # Recompute summary
    total = len(data['results'])
    data['summary']['arrival']['correct'] = fixed_correct
    data['summary']['arrival']['accuracy'] = fixed_correct / total

    # Recompute per-domain
    for domain in data['summary']['per_domain']:
        domain_results = [r for r in data['results'] if r['domain'] == domain]
        domain_correct = sum(1 for r in domain_results if r['arrival']['correct'])
        data['summary']['per_domain'][domain]['arrival']['correct'] = domain_correct
        data['summary']['per_domain'][domain]['arrival']['accuracy'] = domain_correct / len(domain_results)

    # Recompute per-trio
    for trio_name in data['summary']['per_trio']:
        trio_results = [r for r in data['results'] if r['trio_name'] == trio_name]
        trio_correct = sum(1 for r in trio_results if r['arrival']['correct'])
        data['summary']['per_trio'][trio_name]['arrival']['correct'] = trio_correct
        data['summary']['per_trio'][trio_name]['arrival']['accuracy'] = trio_correct / len(trio_results)

    # Add recomputation metadata
    data['recomputed'] = {
        'timestamp': datetime.now().isoformat(),
        'reason': 'Fixed extract_answer_letter() to parse @CONSENSUS[answer=X] format',
        'extraction_fixed': extraction_fixed,
        'still_none': still_none,
        'original_accuracy': 0.30,
        'fixed_accuracy': fixed_correct / total,
    }

    print(f"\n=== RECOMPUTATION RESULTS ===")
    print(f"Extraction fixed: {extraction_fixed} answers recovered")
    print(f"Still None: {still_none}")
    print(f"Original accuracy: 30.0%")
    print(f"Fixed accuracy: {fixed_correct/total:.1%}")
    print()
    print(f"Per-trio:")
    for trio_name, trio_data in data['summary']['per_trio'].items():
        print(f"  {trio_name}: MV={trio_data['majority_vote']['accuracy']:.0%} | ARRIVAL={trio_data['arrival']['accuracy']:.0%}")
    print()
    print(f"Per-domain:")
    for domain, domain_data in data['summary']['per_domain'].items():
        print(f"  {domain}: MV={domain_data['majority_vote']['accuracy']:.0%} | ARRIVAL={domain_data['arrival']['accuracy']:.0%}")

    return data


if __name__ == '__main__':
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(parent, "results", "phase_5")

    # Find latest results file
    files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json')])
    if not files:
        print("No results files found!")
        sys.exit(1)

    input_path = os.path.join(results_dir, files[-1])
    print(f"Input: {input_path}")

    data = recompute(input_path)

    # Save recomputed results
    output_name = f"phase5_results_recomputed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path = os.path.join(results_dir, output_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved: {output_path}")
