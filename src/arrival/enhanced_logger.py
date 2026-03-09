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
ARRIVAL Phase 4: Enhanced Logger
JSONL + TXT dual logging with cost/token/model tracking.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class EnhancedLogger:
    """
    Dual-format logger: structured JSONL + human-readable TXT.
    Extends the pattern from shared_components/logging/transparent_logger.py
    with Phase 4 fields: model IDs, run numbers, costs, latency.
    """

    def __init__(self, log_dir: str, experiment_group: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.experiment_group = experiment_group

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log = self.log_dir / f"{experiment_group}_{timestamp}.jsonl"
        self.console_log = self.log_dir / f"{experiment_group}_{timestamp}_console.txt"

        self.total_cost = 0.0
        self.total_tokens = 0
        self.entry_count = 0

        # Write session header
        self._write_console(f"{'='*70}")
        self._write_console(f"ARRIVAL Phase 4 - {experiment_group}")
        self._write_console(f"Session started: {datetime.now().isoformat()}")
        self._write_console(f"{'='*70}\n")

    def log_exchange(
        self,
        step: str,
        model_a: str,
        model_b: str,
        prompt: str,
        response: str,
        run_number: int = 1,
        scenario_name: str = "",
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a single exchange (prompt + response)."""
        self.entry_count += 1
        self.total_cost += cost_usd
        self.total_tokens += tokens_prompt + tokens_completion

        entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment_group": self.experiment_group,
            "step": step,
            "model_a": model_a,
            "model_b": model_b,
            "run_number": run_number,
            "scenario": scenario_name,
            "prompt": prompt,
            "response": response,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "cost_usd": cost_usd,
            "latency_ms": round(latency_ms, 1),
            "metadata": metadata or {},
        }

        # JSONL
        with open(self.session_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Console TXT
        self._write_console(f"\n{'='*70}")
        self._write_console(f"[{entry['timestamp']}] {step} | Run #{run_number} | {scenario_name}")
        self._write_console(f"Models: {model_a} -> {model_b}")
        self._write_console(f"Tokens: {tokens_prompt}+{tokens_completion} | Cost: ${cost_usd:.4f} | Latency: {latency_ms:.0f}ms")
        self._write_console(f"{'-'*70}")
        self._write_console(f"PROMPT:\n{prompt[:500]}{'...' if len(prompt) > 500 else ''}")
        self._write_console(f"{'-'*70}")
        self._write_console(f"RESPONSE:\n{response[:500]}{'...' if len(response) > 500 else ''}")
        self._write_console(f"{'='*70}")

        # Terminal
        print(f"  [{step}] {self._short(model_b)}: {len(response)} chars, ${cost_usd:.4f}")

    def log_event(self, event: str, data: Optional[Dict[str, Any]] = None):
        """Log a non-exchange event (experiment start, end, error, etc.)."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment_group": self.experiment_group,
            "event": event,
            "data": data or {},
        }
        with open(self.session_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        self._write_console(f"\n[EVENT] {event}")
        if data:
            self._write_console(f"  {json.dumps(data, ensure_ascii=False)[:200]}")

    def get_summary(self) -> Dict[str, Any]:
        """Return session summary."""
        return {
            "session_log": str(self.session_log),
            "console_log": str(self.console_log),
            "total_entries": self.entry_count,
            "total_cost_usd": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
        }

    def _write_console(self, text: str):
        with open(self.console_log, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    @staticmethod
    def _short(model: str) -> str:
        return model.split("/")[-1][:20]
