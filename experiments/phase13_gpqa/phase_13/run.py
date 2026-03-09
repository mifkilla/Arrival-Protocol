# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Wrapper to run Phase 13 GPQA Diamond experiment.

Requires OPENROUTER_API_KEY environment variable to be set.
See .env.example in the repository root for configuration.
"""
import os
import sys

# Verify API key is set (never hardcode secrets!)
assert os.environ.get("OPENROUTER_API_KEY"), (
    "OPENROUTER_API_KEY environment variable is required. "
    "See .env.example for configuration."
)

# Import and run
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_phase13 import main
main()
