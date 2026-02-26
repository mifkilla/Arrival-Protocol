"""
Phase 18: Applied Experiment Configuration
============================================
Compares Solo (Claude Sonnet 4.5) vs ARRIVAL (5 heterogeneous models)
vs ARRIVAL + CARE-ALERT Memory on two practical tasks:
  Task 1: Security Audit (analytical)
  Task 2: REST API Code Generation (constructive)

ARRIVAL Protocol: 4 rounds × 5 models + 1 synthesis = 11 API calls per condition.
Three conditions: A (Solo), B (ARRIVAL), C (ARRIVAL + Memory).

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
BUDGET_LIMIT_USD = 5.0  # Safety guard for Phase 18
SLEEP_BETWEEN_CALLS = 1.5  # seconds between API calls
REQUEST_TIMEOUT = 180  # seconds

# ============================================================
# Model Registry — Phase 18
# ============================================================

# Condition A: Solo baseline
SOLO_MODEL = "anthropic/claude-sonnet-4.5"

# Conditions B & C: ARRIVAL heterogeneous swarm
ARRIVAL_MODELS = {
    "alpha": {
        "model_id": "openai/gpt-4.1",
        "role": "analyst",
        "persona": (
            "You are Alpha, the primary analyst. You approach problems "
            "systematically, breaking them into components and analyzing each "
            "with rigorous logical reasoning. You prioritize correctness and "
            "completeness over speed."
        ),
    },
    "beta": {
        "model_id": "deepseek/deepseek-v3.2",
        "role": "skeptic",
        "persona": (
            "You are Beta, the skeptic. You challenge assumptions, look for "
            "edge cases, and question whether proposed solutions actually work. "
            "You are particularly good at finding flaws others miss."
        ),
    },
    "gamma": {
        "model_id": "mistralai/mistral-large-2512",
        "role": "lateral_thinker",
        "persona": (
            "You are Gamma, the lateral thinker. You approach problems from "
            "unexpected angles, drawing connections across domains. You often "
            "find creative solutions that others overlook."
        ),
    },
    "delta": {
        "model_id": "google/gemini-3-flash-preview",
        "role": "rigorous",
        "persona": (
            "You are Delta, the rigorous verifier. You focus on formal "
            "correctness, checking every detail against specifications and "
            "best practices. You catch subtle errors in logic and implementation."
        ),
    },
    "epsilon": {
        "model_id": "x-ai/grok-4.1-fast",
        "role": "synthesizer",
        "persona": (
            "You are Epsilon, the synthesizer. You excel at combining insights "
            "from multiple perspectives into a coherent whole. You identify "
            "the strongest arguments and build consensus."
        ),
    },
}

# Cost per 1M tokens (USD) for budget tracking
MODEL_COSTS = {
    "anthropic/claude-sonnet-4.5":       {"input": 3.00, "output": 15.00},
    "openai/gpt-4.1":                    {"input": 2.00, "output": 8.00},
    "deepseek/deepseek-v3.2":            {"input": 0.25, "output": 0.40},
    "mistralai/mistral-large-2512":      {"input": 0.50, "output": 1.50},
    "google/gemini-3-flash-preview":     {"input": 0.50, "output": 3.00},
    "x-ai/grok-4.1-fast":               {"input": 0.20, "output": 0.50},
}

MODEL_SHORT = {
    "anthropic/claude-sonnet-4.5":       "Claude4.5S",
    "openai/gpt-4.1":                    "GPT4.1",
    "deepseek/deepseek-v3.2":            "DSv3.2",
    "mistralai/mistral-large-2512":      "MistralL3",
    "google/gemini-3-flash-preview":     "Gemini3F",
    "x-ai/grok-4.1-fast":               "Grok4.1F",
}

# ============================================================
# ARRIVAL Protocol Parameters
# ============================================================
ARRIVAL_TEMPERATURE = 0.7
ARRIVAL_MAX_TOKENS_R1 = 4096   # Round 1: Independent analysis
ARRIVAL_MAX_TOKENS_R2 = 3072   # Round 2: Cross-critique
ARRIVAL_MAX_TOKENS_R4 = 6144   # Round 4: Final synthesis
SOLO_MAX_TOKENS = 8192         # Solo gets generous token budget
SOLO_TEMPERATURE = 0.3         # Solo uses lower temperature for consistency

# CARE-ALERT threshold for memory injection (Condition C)
CARE_ALERT_THRESHOLD = 0.7  # Inject memory when CARE < this value

# ============================================================
# ARRIVAL System Prompts
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
@MEMORY.PROCEDURAL — reference to known best practices (if provided)
@CARE.ALERT — urgent correction flagged by the memory system (if provided)

RULES:
1. Use @-atoms to structure your reasoning — they make your thought process transparent
2. State confidence numerically with @C[value]
3. When you agree, use @CONSENSUS with the specific finding
4. When you disagree, use @CONFLICT with the specific issue and your counter-argument
5. Be substantive — avoid vague agreement or empty criticism"""

ARRIVAL_R1_TEMPLATE = """{persona}

{system_base}

=== ROUND 1: INDEPENDENT ANALYSIS ===
Analyze the following task independently. Do NOT refer to other nodes (you haven't seen their work yet).
Structure your response using @-atoms.

TASK:
{task_prompt}"""

ARRIVAL_R2_TEMPLATE = """{persona}

{system_base}

=== ROUND 2: CROSS-CRITIQUE ===
You have seen the independent analyses from all other nodes.
Your job: find weaknesses, validate strengths, use @CONSENSUS and @CONFLICT atoms.

YOUR ROUND 1 ANALYSIS:
{own_r1}

OTHER NODES' ANALYSES:
{others_r1}

TASK (for reference):
{task_prompt}

Critique the other analyses. What did they miss? What did they get right?
Use @CONSENSUS[finding=...] for agreements, @CONFLICT[issue=...] for disagreements."""

ARRIVAL_R4_TEMPLATE = """You are Alpha, the lead synthesizer for this ARRIVAL session.

{system_base}

=== ROUND 4: FINAL SYNTHESIS ===
You have all Round 1 analyses and all Round 2 cross-critiques.
Your job: produce the DEFINITIVE final answer by integrating the strongest arguments.

ALL ROUND 1 ANALYSES:
{all_r1}

ALL ROUND 2 CRITIQUES:
{all_r2}

{memory_injection}

TASK (for reference):
{task_prompt}

Synthesize the best answer. Resolve any @CONFLICT items.
Give a comprehensive, well-structured final response."""

# ============================================================
# Solo System Prompt
# ============================================================

SOLO_SYSTEM = """You are an expert software engineer performing a thorough analysis.
Approach the task systematically:
1. Read and understand the full context
2. Analyze step by step
3. Be comprehensive — don't skip details
4. Structure your response clearly
5. State your confidence in your findings

You have no collaborators — your analysis must be complete on its own."""

# ============================================================
# Task-specific prompts
# ============================================================

TASK1_AUDIT_PROMPT = """SECURITY & CODE AUDIT TASK

Below is a Python web application (Flask-based). It contains multiple intentional bugs and security vulnerabilities.

Your task:
1. Identify ALL bugs and security vulnerabilities
2. For each bug: explain WHAT it is, WHERE it is (line/function), WHY it's dangerous
3. Provide a CORRECTED code snippet for each bug
4. Rate the severity of each bug (Critical/High/Medium/Low)

Be thorough — there are at least 10 distinct issues.

=== APPLICATION CODE ===
{code}
=== END CODE ==="""

TASK2_API_PROMPT = """REST API IMPLEMENTATION TASK

Implement a complete REST API using FastAPI for a todo-list task manager.

REQUIREMENTS:
- CRUD operations for tasks (each task has: id, title, description, priority, status, due_date, tags)
- Pydantic models for input validation
- Pagination with limit/offset parameters
- Filtering by status, priority, and tags
- Sorting by any field (ascending/descending)
- Search by title and description (case-insensitive substring match)
- Proper error handling (404 for missing tasks, 422 for validation errors)
- In-memory storage (Python dict, no database needed)
- Include a complete test file using pytest + httpx

CONSTRAINTS:
- priority must be one of: "low", "medium", "high", "critical"
- status must be one of: "todo", "in_progress", "done", "cancelled"
- due_date format: YYYY-MM-DD (optional field)
- tags: list of strings (optional, default empty)
- id: auto-incrementing integer starting from 1
- Default sort: by id ascending
- Default pagination: limit=20, offset=0

Provide the COMPLETE implementation in a single response:
1. `app.py` — the FastAPI application
2. `test_api.py` — comprehensive test suite

Use proper Python type hints throughout."""
