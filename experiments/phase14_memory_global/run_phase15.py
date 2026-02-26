#!/usr/bin/env python3
# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
ARRIVAL Phase 15: Gated CARE-ALERT (Real-time Working Memory)
=============================================================
Replaces global static memory injection (Phase 14) with real-time
monitoring and conditional @CARE.ALERT injection.

Key insight from Phase 14:
  - Global memory injection BEFORE dialogue triggers HYPERCORRECTION
  - Models warned about past failures become anxious and break consensus
  - Memory creation works; memory DELIVERY was the problem

Phase 15 design: Monitor -> Detect -> Intervene
  - System prompt is CLEAN (identical to Phase 13, NO memory block)
  - After R2: compute interim CRDT metrics, fire Level 1 alert if divergence
  - After R3: compute again, fire Level 2 alert if divergence persists
  - Alerts are OPERATIONAL ("Beta selected C, address with @EVIDENCE"),
    not MORALISTIC ("you failed before, be careful")

Comparison (3-way): Phase 13 (stateless) vs Phase 14 (static memory) vs Phase 15 (gated alert)

Usage:
    python run_phase15.py              # Full run (40 questions)
    python run_phase15.py --test 3     # Test on 3 questions only
    python run_phase15.py --dry-run    # Validate pipeline without API calls
    python run_phase15.py --review     # Print review artifacts, NO API calls

Output:
    results/phase15_results_YYYYMMDD_HHMMSS.json
    logs/phase15_YYYYMMDD_HHMMSS.jsonl + .txt

Author: Mefodiy Kelevra
ORCID: 0009-0003-4153-392X
"""

import sys
import os
import json
import time
import math
import argparse
from datetime import datetime, timezone
from collections import Counter

# Windows encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    MODEL_SHORT, KNOWN_ATOMS, SLEEP_BETWEEN_CALLS,
    PHASE15_TRIO, PHASE15_TRIO_NAME, PHASE15_TEMPERATURE,
    PHASE15_MAX_TOKENS, PHASE15_BUDGET_LIMIT,
    PHASE15_ALERT_MD_THRESHOLD_R2, PHASE15_ALERT_MD_THRESHOLD_R3,
    PHASE15_DEBT_STORE_THRESHOLD, PHASE15_MEMORY_FILE,
    PHASE15_BASELINE_P13, PHASE15_BASELINE_P14,
    PHASE15_N_QUESTIONS,
    RESULTS_DIR, LOGS_DIR,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from metrics import extract_answer_letter, find_all_atoms, detect_emergent_atoms
from crdt_metrics import compute_care_resolve, compute_meaning_debt
from enhanced_logger import EnhancedLogger
from memory.store import MemoryStore
from memory.schema import EpisodicMemory
from care_alert import compute_interim_metrics, detect_divergence, generate_care_alert
from experiments.questions_gpqa import QUESTIONS, DOMAINS


# ============================================================
# System Prompt (CLEAN — identical to Phase 13, NO MEMORY)
# ============================================================

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

ARRIVAL_ROUND_PROMPTS = {
    1: """You are Node {node_name} ({model_short}).
Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Analyze this question using DEUS protocol atoms. State your reasoning and initial answer.
Use @SELF to identify, @GOAL for the task, @INT for your reasoning, @C[value] for confidence.""",

    2: """You are Node {node_name} ({model_short}).
The previous node analyzed this question:

{previous_response}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Review their analysis. Do you agree or disagree? Use @CONSENSUS or @CONFLICT atoms.
If you agree, reinforce the reasoning. If you disagree, explain why with @INT.
State your answer clearly. Use @C[value] for your confidence level.""",

    3: """You are Node {node_name} ({model_short}).
Two nodes have analyzed this question:

Node 1: {response_1}

Node 2: {response_2}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

Synthesize both perspectives. Identify agreements and conflicts.
Propose the final answer with @RESOLUTION. Use @CONSENSUS[answer=X] for your verdict.
Include @C[value] for confidence.""",

    4: """You are Node {node_name} ({model_short}).
Three analyses have been provided:

Node 1: {response_1}
Node 2: {response_2}
Node 3: {response_3}

Question: {question}

Choices:
A) {choice_a}
B) {choice_b}
C) {choice_c}
D) {choice_d}

This is the final round. State the group's consensus answer.
Use @CONSENSUS[answer=X] where X is A, B, C, or D.
If there's no clear consensus, choose the best-supported answer and explain.
Include @C[value] for final confidence."""
}


# ============================================================
# Phase 15 Runner
# ============================================================

class Phase15Runner:
    """
    Gated CARE-ALERT Runner.

    Differences from Phase 14:
    1. System prompt is CLEAN (no [MEMORY CONTEXT])
    2. After R2/R3: compute interim metrics and detect divergence
    3. If divergence detected: append @CARE.ALERT to user prompt (not system prompt)
    4. 3-way comparison: P13 vs P14 vs P15
    5. Alert statistics tracked per-question
    """

    def __init__(self, n_questions=None, dry_run=False):
        self.dry_run = dry_run
        self.trio = PHASE15_TRIO
        self.trio_name = PHASE15_TRIO_NAME
        self.n_questions = n_questions or PHASE15_N_QUESTIONS
        self.questions = QUESTIONS[:self.n_questions]

        # Client
        if not dry_run:
            self.client = OpenRouterClient(budget_limit=PHASE15_BUDGET_LIMIT)
        else:
            self.client = None

        # Memory store (for auto-store ONLY — NOT for injection)
        self.memory_store = MemoryStore(str(PHASE15_MEMORY_FILE))
        if os.path.exists(str(PHASE15_MEMORY_FILE)):
            self.memory_store.load()
        self.initial_memory_count = len(self.memory_store.memories)

        # Baselines
        self.baseline_p13 = self._load_baseline(str(PHASE15_BASELINE_P13), "Phase 13")
        self.baseline_p14 = self._load_baseline(str(PHASE15_BASELINE_P14), "Phase 14")

        # Seen question IDs (from Phase 14 scars)
        self.seen_ids = self._load_seen_ids()

        # Logger
        self.start_time = datetime.now(timezone.utc)
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        log_dir = str(LOGS_DIR)
        os.makedirs(log_dir, exist_ok=True)
        if not dry_run:
            self.logger = EnhancedLogger(
                log_dir=log_dir,
                experiment_group=f"phase15_{timestamp}",
            )
        else:
            self.logger = None

        # Counters
        self.total_cost = 0.0
        self.total_calls = 0
        self.memories_added = 0
        self.alerts_r2 = 0
        self.alerts_r3 = 0

    def _load_baseline(self, path: str, label: str) -> dict:
        """Load baseline results for comparison."""
        if not os.path.exists(path):
            print(f"  WARNING: {label} baseline not found at {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_seen_ids(self) -> list:
        """Load seen question IDs from Phase 14 scars."""
        from config import PHASE14_SCARS_FILE
        path = str(PHASE14_SCARS_FILE)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            scars = json.load(f)
        return scars.get("seen_question_ids", [])

    def _log_api_call(self, question_id, condition, round_num, model, response_text,
                      answer, cost, tokens, latency_ms):
        """Log API call to JSONL."""
        if self.logger:
            self.logger.log_event("api_call", {
                "question_id": question_id,
                "condition": condition,
                "round": round_num,
                "model": MODEL_SHORT.get(model, model),
                "answer": answer,
                "cost_usd": cost,
                "tokens": tokens,
                "latency_ms": round(latency_ms, 1),
                "response_length": len(response_text),
            })

    # ================================================================
    # System Prompt — CLEAN (no memory injection)
    # ================================================================

    def build_system_prompt(self) -> str:
        """
        Build system prompt. Phase 15: ALWAYS clean, no memory block.
        This is the ONLY difference from Phase 14's build_system_prompt.
        """
        return ARRIVAL_SYSTEM

    # ================================================================
    # 4-Round ARRIVAL Protocol with Gated CARE-ALERT
    # ================================================================

    def run_arrival_with_alert(self, question: dict) -> dict:
        """
        4-round ARRIVAL Protocol with real-time CARE-ALERT.

        Structure:
        R1 (Alpha) -> clean prompt
        R2 (Beta)  -> clean prompt
           CHECKPOINT #1: compute_interim_metrics, detect_divergence
        R3 (Gamma) -> prompt + alert_1 (if fired)
           CHECKPOINT #2: compute_interim_metrics, detect_divergence
        R4 (Alpha) -> prompt + alert_2 (if fired)
        """
        if self.dry_run:
            return {
                "condition": "arrival_care_alert",
                "trio": [MODEL_SHORT.get(m, m) for m in self.trio],
                "final_answer": "A",
                "correct": "A" == question["correct"],
                "dialogue": [],
                "atoms_used": {},
                "unique_atoms": 0,
                "emergent_atoms": [],
                "cost_usd": 0.0,
                "total_tokens": 0,
                "rounds": 4,
                "crdt": {"care_resolve": {}, "meaning_debt": {}},
                "memory_injected": False,
                "alert_fired_r2": False,
                "alert_fired_r3": False,
                "alert_text_r2": "",
                "alert_text_r3": "",
                "interim_r2": {},
                "interim_r3": {},
            }

        system_prompt = self.build_system_prompt()

        dialogue = []
        dialogue_raw = []  # With model IDs (not short names) for care_alert
        responses = {}
        total_cost = 0.0
        total_tokens = 0
        all_atoms = []
        emergent = set()

        q = question
        choice_vars = {
            "choice_a": q["choices"]["A"],
            "choice_b": q["choices"]["B"],
            "choice_c": q["choices"]["C"],
            "choice_d": q["choices"]["D"],
            "question": q["question"],
        }

        model_a = self.trio[0]
        model_b = self.trio[1]
        model_c = self.trio[2]

        # ---- Round 1: Alpha (GPT4o) — initial analysis ----
        prompt_1 = ARRIVAL_ROUND_PROMPTS[1].format(
            node_name="Alpha",
            model_short=MODEL_SHORT.get(model_a, model_a),
            **choice_vars
        )
        resp_1 = self.client.generate(
            prompt=prompt_1, model=model_a,
            system_prompt=system_prompt,
            temperature=PHASE15_TEMPERATURE,
            max_tokens=PHASE15_MAX_TOKENS,
        )
        responses["r1"] = resp_1.text
        total_cost += resp_1.cost_usd
        total_tokens += resp_1.prompt_tokens + resp_1.completion_tokens
        self.total_cost += resp_1.cost_usd
        self.total_calls += 1
        dialogue.append({
            "round": 1,
            "from": MODEL_SHORT.get(model_a, model_a),
            "message": resp_1.text,
        })
        dialogue_raw.append({
            "round": 1,
            "from": model_a,
            "message": resp_1.text,
        })
        all_atoms.extend(find_all_atoms(resp_1.text))
        emergent.update(detect_emergent_atoms(resp_1.text))
        self._log_api_call(q["id"], "arrival_care_alert", 1, model_a, resp_1.text,
                           extract_answer_letter(resp_1.text), resp_1.cost_usd,
                           resp_1.prompt_tokens + resp_1.completion_tokens, resp_1.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # ---- Round 2: Beta (DeepSeekV3) — cross-critique ----
        prompt_2 = ARRIVAL_ROUND_PROMPTS[2].format(
            node_name="Beta",
            model_short=MODEL_SHORT.get(model_b, model_b),
            previous_response=resp_1.text[:1500],
            **choice_vars
        )
        resp_2 = self.client.generate(
            prompt=prompt_2, model=model_b,
            system_prompt=system_prompt,
            temperature=PHASE15_TEMPERATURE,
            max_tokens=PHASE15_MAX_TOKENS,
        )
        responses["r2"] = resp_2.text
        total_cost += resp_2.cost_usd
        total_tokens += resp_2.prompt_tokens + resp_2.completion_tokens
        self.total_cost += resp_2.cost_usd
        self.total_calls += 1
        dialogue.append({
            "round": 2,
            "from": MODEL_SHORT.get(model_b, model_b),
            "message": resp_2.text,
        })
        dialogue_raw.append({
            "round": 2,
            "from": model_b,
            "message": resp_2.text,
        })
        all_atoms.extend(find_all_atoms(resp_2.text))
        emergent.update(detect_emergent_atoms(resp_2.text))
        self._log_api_call(q["id"], "arrival_care_alert", 2, model_b, resp_2.text,
                           extract_answer_letter(resp_2.text), resp_2.cost_usd,
                           resp_2.prompt_tokens + resp_2.completion_tokens, resp_2.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # ╔══════════════════════════════════════════════════════════╗
        # ║  CHECKPOINT #1 (after R2, zero API cost)               ║
        # ║  Monitor → Detect → Intervene (if needed)              ║
        # ╚══════════════════════════════════════════════════════════╝
        interim_r2 = compute_interim_metrics(dialogue_raw[:2])
        triggered_r2, reason_r2 = detect_divergence(
            interim_r2,
            md_threshold=PHASE15_ALERT_MD_THRESHOLD_R2,
            round_num=2,
        )
        alert_r2 = ""
        if triggered_r2:
            alert_r2 = generate_care_alert(interim_r2, round_num=2, escalation=1)
            self.alerts_r2 += 1
            print(f"    [ALERT R2] {reason_r2}")
            print(f"    [ALERT R2] {alert_r2[:120]}...")

        # ---- Round 3: Gamma (Llama33) — synthesis ----
        prompt_3 = ARRIVAL_ROUND_PROMPTS[3].format(
            node_name="Gamma",
            model_short=MODEL_SHORT.get(model_c, model_c),
            response_1=resp_1.text[:1200],
            response_2=resp_2.text[:1200],
            **choice_vars
        )
        # Append alert to user prompt if fired
        if alert_r2:
            prompt_3 += "\n\n" + alert_r2

        resp_3 = self.client.generate(
            prompt=prompt_3, model=model_c,
            system_prompt=system_prompt,
            temperature=PHASE15_TEMPERATURE,
            max_tokens=PHASE15_MAX_TOKENS,
        )
        responses["r3"] = resp_3.text
        total_cost += resp_3.cost_usd
        total_tokens += resp_3.prompt_tokens + resp_3.completion_tokens
        self.total_cost += resp_3.cost_usd
        self.total_calls += 1
        dialogue.append({
            "round": 3,
            "from": MODEL_SHORT.get(model_c, model_c),
            "message": resp_3.text,
        })
        dialogue_raw.append({
            "round": 3,
            "from": model_c,
            "message": resp_3.text,
        })
        all_atoms.extend(find_all_atoms(resp_3.text))
        emergent.update(detect_emergent_atoms(resp_3.text))
        self._log_api_call(q["id"], "arrival_care_alert", 3, model_c, resp_3.text,
                           extract_answer_letter(resp_3.text), resp_3.cost_usd,
                           resp_3.prompt_tokens + resp_3.completion_tokens, resp_3.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # ╔══════════════════════════════════════════════════════════╗
        # ║  CHECKPOINT #2 (after R3, zero API cost)               ║
        # ║  Monitor → Detect → Intervene (if divergence persists) ║
        # ╚══════════════════════════════════════════════════════════╝
        interim_r3 = compute_interim_metrics(dialogue_raw[:3])
        triggered_r3, reason_r3 = detect_divergence(
            interim_r3,
            md_threshold=PHASE15_ALERT_MD_THRESHOLD_R3,
            round_num=3,
        )
        alert_r3 = ""
        if triggered_r3:
            alert_r3 = generate_care_alert(interim_r3, round_num=3, escalation=2)
            self.alerts_r3 += 1
            print(f"    [ALERT R3] {reason_r3}")
            print(f"    [ALERT R3] {alert_r3[:120]}...")

        # ---- Round 4: Alpha (GPT4o) — final consensus ----
        prompt_4 = ARRIVAL_ROUND_PROMPTS[4].format(
            node_name="Alpha",
            model_short=MODEL_SHORT.get(model_a, model_a),
            response_1=resp_1.text[:800],
            response_2=resp_2.text[:800],
            response_3=resp_3.text[:800],
            **choice_vars
        )
        # Append alert to user prompt if fired
        if alert_r3:
            prompt_4 += "\n\n" + alert_r3

        resp_4 = self.client.generate(
            prompt=prompt_4, model=model_a,
            system_prompt=system_prompt,
            temperature=PHASE15_TEMPERATURE,
            max_tokens=PHASE15_MAX_TOKENS,
        )
        responses["r4"] = resp_4.text
        total_cost += resp_4.cost_usd
        total_tokens += resp_4.prompt_tokens + resp_4.completion_tokens
        self.total_cost += resp_4.cost_usd
        self.total_calls += 1
        dialogue.append({
            "round": 4,
            "from": MODEL_SHORT.get(model_a, model_a),
            "message": resp_4.text,
        })
        dialogue_raw.append({
            "round": 4,
            "from": model_a,
            "message": resp_4.text,
        })
        all_atoms.extend(find_all_atoms(resp_4.text))
        emergent.update(detect_emergent_atoms(resp_4.text))
        self._log_api_call(q["id"], "arrival_care_alert", 4, model_a, resp_4.text,
                           extract_answer_letter(resp_4.text), resp_4.cost_usd,
                           resp_4.prompt_tokens + resp_4.completion_tokens, resp_4.latency_ms)

        # Extract final answer (prefer later rounds)
        final_answer = None
        for r_key in ["r4", "r3", "r2", "r1"]:
            final_answer = extract_answer_letter(responses[r_key])
            if final_answer:
                break

        atom_counts = Counter(all_atoms)

        # ---- CRDT OVERLAY (zero API cost) ----
        care_result = compute_care_resolve(dialogue, task_type="mcq")
        debt_result = compute_meaning_debt(dialogue, task_type="mcq")

        return {
            "condition": "arrival_care_alert",
            "trio": [MODEL_SHORT.get(m, m) for m in self.trio],
            "final_answer": final_answer,
            "correct": final_answer == question["correct"] if final_answer else False,
            "dialogue": dialogue,
            "atoms_used": dict(atom_counts),
            "unique_atoms": len(atom_counts),
            "emergent_atoms": sorted(emergent),
            "cost_usd": total_cost,
            "total_tokens": total_tokens,
            "rounds": 4,
            "crdt": {
                "care_resolve": care_result,
                "meaning_debt": debt_result,
            },
            "memory_injected": False,  # ALWAYS False in Phase 15
            "alert_fired_r2": triggered_r2,
            "alert_fired_r3": triggered_r3,
            "alert_text_r2": alert_r2,
            "alert_text_r3": alert_r3,
            "alert_reason_r2": reason_r2,
            "alert_reason_r3": reason_r3,
            "interim_r2": interim_r2,
            "interim_r3": interim_r3,
        }

    # ================================================================
    # Auto-Store Memory (diagnostic — NOT for injection)
    # ================================================================

    def auto_store_memory(self, question: dict, arrival_result: dict):
        """
        If meaning_debt exceeds threshold, create a new EpisodicMemory.
        DATA LEAKAGE GUARD: NEVER stores correct answer or question text.
        """
        debt = arrival_result["crdt"].get("meaning_debt", {})
        total_debt = debt.get("total_meaning_debt", 0)

        if total_debt <= PHASE15_DEBT_STORE_THRESHOLD:
            return

        care = arrival_result["crdt"].get("care_resolve", {})
        care_val = care.get("care_resolve", 0.5)

        per_agent_loss = care.get("per_agent_loss", {})
        if per_agent_loss:
            minority = max(per_agent_loss, key=per_agent_loss.get)
            minority_loss = per_agent_loss[minority]
        else:
            minority = "unknown"
            minority_loss = 0.0

        health = debt.get("health_assessment", "unknown")

        key_insight = (
            f"High MD ({total_debt:.2f}) in {question['domain']}. "
            f"Minority voice: {minority} (loss={minority_loss:.2f}). "
            f"Health: {health}. CARE={care_val:.3f}."
        )

        # Verify no data leakage
        import re
        assert not re.search(r'answer\s+is\s+[A-D]', key_insight, re.IGNORECASE), \
            f"DATA LEAKAGE: answer letter in auto-stored key_insight"

        trio_short = [MODEL_SHORT.get(m, m) for m in self.trio]
        self.memory_store.extract_from_session(
            session_id=f"phase15_{question['id']}",
            task=f"GPQA Diamond {question['domain']}",
            models=trio_short,
            accuracy="unknown",
            care_resolve=care_val,
            meaning_debt=total_debt,
            key_insight=key_insight,
            atoms_used=list(arrival_result.get("atoms_used", {}).keys()),
            domain=question["domain"],
        )
        self.memory_store.save()
        self.memories_added += 1

        print(f"    [MNEMO] Auto-stored: MD={total_debt:.2f}, CARE={care_val:.3f} [{health}]")

    # ================================================================
    # Main Experiment Loop
    # ================================================================

    def run_experiment(self):
        """Run Phase 15: ARRIVAL with Gated CARE-ALERT."""
        print(f"\n{'='*70}")
        print(f"  ARRIVAL Phase 15: Gated CARE-ALERT (Alpha Trio)")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  Questions: {len(self.questions)} | Trio: {self.trio_name}")
        print(f"  Alert thresholds: R2>{PHASE15_ALERT_MD_THRESHOLD_R2}, "
              f"R3>{PHASE15_ALERT_MD_THRESHOLD_R3}")
        print(f"  System prompt: CLEAN (no memory injection)")
        print(f"  Seen questions: {self.seen_ids}")
        print(f"  Budget limit: ${PHASE15_BUDGET_LIMIT:.2f}")
        print(f"{'='*70}")

        results = []

        for i, question in enumerate(self.questions):
            q_id = question["id"]
            is_seen = q_id in self.seen_ids
            marker = " [SEEN]" if is_seen else ""

            print(f"\n  [{i+1}/{len(self.questions)}] {q_id} [{question['domain']}]{marker}")

            # Budget check
            if not self.dry_run and self.total_cost >= PHASE15_BUDGET_LIMIT:
                print(f"  BUDGET LIMIT REACHED (${self.total_cost:.4f}). Stopping.")
                break

            # Run ARRIVAL with CARE-ALERT
            try:
                arrival_result = self.run_arrival_with_alert(question)
            except BudgetExceededError as e:
                print(f"  BUDGET EXCEEDED: {e}")
                break
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
                arrival_result = {
                    "condition": "arrival_care_alert",
                    "error": str(e),
                    "correct": False,
                    "final_answer": None,
                    "crdt": {"care_resolve": {}, "meaning_debt": {}},
                    "alert_fired_r2": False,
                    "alert_fired_r3": False,
                    "alert_text_r2": "",
                    "alert_text_r3": "",
                    "interim_r2": {},
                    "interim_r3": {},
                }

            # Print result
            correct_str = "CORRECT" if arrival_result.get("correct") else "WRONG"
            answer = arrival_result.get("final_answer", "?")
            care = arrival_result["crdt"].get("care_resolve", {}).get("care_resolve", "?")
            debt = arrival_result["crdt"].get("meaning_debt", {}).get("total_meaning_debt", "?")
            a_r2 = "ALERT" if arrival_result.get("alert_fired_r2") else "-"
            a_r3 = "ALERT" if arrival_result.get("alert_fired_r3") else "-"
            print(f"    Answer={answer} ({correct_str}) | CARE={care} | MD={debt} | R2:{a_r2} R3:{a_r3}")

            if not self.dry_run:
                cost = arrival_result.get("cost_usd", 0)
                print(f"    Cost: ${cost:.4f} | Total: ${self.total_cost:.4f}")

            # Auto-store memory if dialogue quality poor
            if not self.dry_run:
                self.auto_store_memory(question, arrival_result)

            result = {
                "question_id": q_id,
                "domain": question["domain"],
                "is_seen": is_seen,
                "arrival": arrival_result,
                "crdt": arrival_result.get("crdt", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            results.append(result)

        # ================================================================
        # 3-Way Comparison
        # ================================================================
        comparison = self._compute_comparison(results)

        # ================================================================
        # Alert Statistics
        # ================================================================
        alert_stats = self._compute_alert_stats(results)

        # ================================================================
        # Build output
        # ================================================================
        output = {
            "experiment": "ARRIVAL Phase 15: Gated CARE-ALERT",
            "author": "Mefodiy Kelevra",
            "orcid": "0009-0003-4153-392X",
            "timestamp": self.start_time.isoformat(),
            "config": {
                "trio": [MODEL_SHORT.get(m, m) for m in self.trio],
                "trio_name": self.trio_name,
                "temperature": PHASE15_TEMPERATURE,
                "max_tokens": PHASE15_MAX_TOKENS,
                "alert_md_threshold_r2": PHASE15_ALERT_MD_THRESHOLD_R2,
                "alert_md_threshold_r3": PHASE15_ALERT_MD_THRESHOLD_R3,
                "debt_store_threshold": PHASE15_DEBT_STORE_THRESHOLD,
                "budget_limit": PHASE15_BUDGET_LIMIT,
                "n_questions": len(self.questions),
                "system_prompt": "CLEAN (no memory injection)",
            },
            "seen_question_ids": self.seen_ids,
            "results": {
                "alpha": results,
            },
            "comparison": comparison,
            "alert_statistics": alert_stats,
            "memory_growth": {
                "initial": self.initial_memory_count,
                "final": len(self.memory_store.memories),
                "added_during_run": self.memories_added,
            },
            "cost": {
                "total_usd": round(self.total_cost, 4),
                "total_calls": self.total_calls,
                "budget_limit": PHASE15_BUDGET_LIMIT,
            },
            "summary": self._compute_summary(results),
        }

        # Save results
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        results_file = str(RESULTS_DIR / f"phase15_results_{timestamp}.json")
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n  Results saved: {results_file}")

        # Save memory store
        self.memory_store.save()

        # Print headline
        self._print_headline(output)

        return output

    # ================================================================
    # Alert Statistics
    # ================================================================

    def _compute_alert_stats(self, results: list) -> dict:
        """Compute alert firing statistics."""
        total = len(results)
        r2_fired = sum(1 for r in results if r["arrival"].get("alert_fired_r2", False))
        r3_fired = sum(1 for r in results if r["arrival"].get("alert_fired_r3", False))
        any_alert = sum(
            1 for r in results
            if r["arrival"].get("alert_fired_r2", False) or r["arrival"].get("alert_fired_r3", False)
        )

        # Accuracy when alerted vs not
        alerted = [r for r in results
                   if r["arrival"].get("alert_fired_r2") or r["arrival"].get("alert_fired_r3")]
        not_alerted = [r for r in results
                       if not r["arrival"].get("alert_fired_r2") and not r["arrival"].get("alert_fired_r3")]

        def _acc(rlist):
            if not rlist:
                return None
            return round(sum(1 for r in rlist if r["arrival"].get("correct", False)) / len(rlist), 4)

        def _avg_care(rlist):
            if not rlist:
                return None
            scores = [r["crdt"].get("care_resolve", {}).get("care_resolve")
                      for r in rlist]
            scores = [s for s in scores if s is not None]
            return round(sum(scores) / len(scores), 4) if scores else None

        def _avg_debt(rlist):
            if not rlist:
                return None
            scores = [r["crdt"].get("meaning_debt", {}).get("total_meaning_debt")
                      for r in rlist]
            scores = [s for s in scores if s is not None]
            return round(sum(scores) / len(scores), 4) if scores else None

        return {
            "total_questions": total,
            "questions_with_any_alert": any_alert,
            "alert_rate": round(any_alert / total, 4) if total > 0 else 0,
            "alerts_after_r2": r2_fired,
            "alerts_after_r3": r3_fired,
            "accuracy_when_alerted": _acc(alerted),
            "accuracy_when_not_alerted": _acc(not_alerted),
            "n_alerted": len(alerted),
            "n_not_alerted": len(not_alerted),
            "care_when_alerted": _avg_care(alerted),
            "care_when_not_alerted": _avg_care(not_alerted),
            "debt_when_alerted": _avg_debt(alerted),
            "debt_when_not_alerted": _avg_debt(not_alerted),
        }

    # ================================================================
    # Summary Statistics
    # ================================================================

    def _compute_summary(self, results: list) -> dict:
        """Compute Phase 15 summary statistics."""
        seen_results = [r for r in results if r["is_seen"]]
        unseen_results = [r for r in results if not r["is_seen"]]

        def _stats(rlist):
            if not rlist:
                return {}
            correct = sum(1 for r in rlist if r["arrival"].get("correct", False))
            total = len(rlist)
            care_scores = []
            debt_scores = []
            health_counts = {"healthy": 0, "strained": 0, "unhealthy": 0}

            for r in rlist:
                crdt = r.get("crdt", {})
                care = crdt.get("care_resolve", {})
                debt = crdt.get("meaning_debt", {})
                if care.get("care_resolve") is not None:
                    care_scores.append(care["care_resolve"])
                if debt.get("total_meaning_debt") is not None:
                    debt_scores.append(debt["total_meaning_debt"])
                h = debt.get("health_assessment", "healthy")
                if h in health_counts:
                    health_counts[h] += 1

            return {
                "correct": correct,
                "total": total,
                "accuracy": round(correct / total, 4) if total > 0 else 0,
                "avg_care_resolve": round(sum(care_scores) / len(care_scores), 4) if care_scores else None,
                "avg_meaning_debt": round(sum(debt_scores) / len(debt_scores), 4) if debt_scores else None,
                "health_counts": health_counts,
            }

        return {
            "all_40": _stats(results),
            "unseen_35": _stats(unseen_results),
            "seen_5": _stats(seen_results),
        }

    # ================================================================
    # 3-Way Comparison: Phase 13 vs Phase 14 vs Phase 15
    # ================================================================

    def _compute_comparison(self, results: list) -> dict:
        """Compare Phase 15 against Phase 13 and Phase 14."""

        def _get_lookup(baseline: dict) -> dict:
            alpha = baseline.get("results", {}).get("alpha", [])
            return {r["question_id"]: r for r in alpha}

        p13_lookup = _get_lookup(self.baseline_p13) if self.baseline_p13 else {}
        p14_lookup = _get_lookup(self.baseline_p14) if self.baseline_p14 else {}
        p15_lookup = {r["question_id"]: r for r in results}

        unseen_results = [r for r in results if not r["is_seen"]]
        seen_results = [r for r in results if r["is_seen"]]

        def _pairwise(label_a, lookup_a, label_b, lookup_b, p_list):
            """Compare two phases on a subset of questions."""
            a_correct = 0
            b_correct = 0
            b_count = 0  # P_a right, P_b wrong
            c_count = 0  # P_a wrong, P_b right
            a_care, b_care = [], []
            a_debt, b_debt = [], []

            for r in p_list:
                qid = r["question_id"]
                ra = lookup_a.get(qid)
                rb = lookup_b.get(qid)
                if not ra or not rb:
                    continue

                ok_a = ra.get("arrival", {}).get("correct", False)
                ok_b = rb.get("arrival", {}).get("correct", False)
                a_correct += int(ok_a)
                b_correct += int(ok_b)
                if ok_a and not ok_b:
                    b_count += 1
                elif not ok_a and ok_b:
                    c_count += 1

                ca = ra.get("crdt", {}).get("care_resolve", {}).get("care_resolve")
                cb = rb.get("crdt", {}).get("care_resolve", {}).get("care_resolve")
                if ca is not None:
                    a_care.append(ca)
                if cb is not None:
                    b_care.append(cb)

                da = ra.get("crdt", {}).get("meaning_debt", {}).get("total_meaning_debt")
                db = rb.get("crdt", {}).get("meaning_debt", {}).get("total_meaning_debt")
                if da is not None:
                    a_debt.append(da)
                if db is not None:
                    b_debt.append(db)

            total = len(p_list)
            a_acc = a_correct / total if total > 0 else 0
            b_acc = b_correct / total if total > 0 else 0

            result = {
                "n_questions": total,
                f"{label_a}_accuracy": round(a_acc, 4),
                f"{label_b}_accuracy": round(b_acc, 4),
                "delta_pp": round((b_acc - a_acc) * 100, 1),
                f"{label_a}_correct": a_correct,
                f"{label_b}_correct": b_correct,
            }

            # McNemar's test
            if b_count + c_count > 0:
                chi2_stat = (abs(b_count - c_count) - 1) ** 2 / (b_count + c_count)
                from scipy.stats import chi2 as chi2_dist
                p_value = chi2_dist.sf(chi2_stat, df=1)
            else:
                chi2_stat = 0
                p_value = 1.0

            result["mcnemar"] = {
                f"b_{label_a}right_{label_b}wrong": b_count,
                f"c_{label_a}wrong_{label_b}right": c_count,
                "chi2": round(chi2_stat, 4),
                "p_value": round(p_value, 6),
            }

            # CARE
            if a_care and b_care:
                result["care"] = {
                    f"{label_a}_avg": round(sum(a_care) / len(a_care), 4),
                    f"{label_b}_avg": round(sum(b_care) / len(b_care), 4),
                    "delta": round(sum(b_care) / len(b_care) - sum(a_care) / len(a_care), 4),
                }
                try:
                    from scipy.stats import mannwhitneyu
                    U, p = mannwhitneyu(b_care, a_care, alternative='greater')
                    result["care"]["mann_whitney_U"] = round(U, 2)
                    result["care"]["mann_whitney_p"] = round(p, 6)
                except Exception as e:
                    result["care"]["mann_whitney_error"] = str(e)

            # Debt
            if a_debt and b_debt:
                result["debt"] = {
                    f"{label_a}_avg": round(sum(a_debt) / len(a_debt), 4),
                    f"{label_b}_avg": round(sum(b_debt) / len(b_debt), 4),
                    "delta": round(sum(b_debt) / len(b_debt) - sum(a_debt) / len(a_debt), 4),
                }
                try:
                    from scipy.stats import mannwhitneyu
                    U, p = mannwhitneyu(a_debt, b_debt, alternative='greater')
                    result["debt"]["mann_whitney_U"] = round(U, 2)
                    result["debt"]["mann_whitney_p"] = round(p, 6)
                except Exception as e:
                    result["debt"]["mann_whitney_error"] = str(e)

            return result

        comp = {"unseen_only": {}, "seen_only": {}, "all_40": {}}

        # P13 vs P15
        if p13_lookup:
            comp["unseen_only"]["p13_vs_p15"] = _pairwise(
                "p13", p13_lookup, "p15", p15_lookup, unseen_results)
            comp["seen_only"]["p13_vs_p15"] = _pairwise(
                "p13", p13_lookup, "p15", p15_lookup, seen_results)
            comp["all_40"]["p13_vs_p15"] = _pairwise(
                "p13", p13_lookup, "p15", p15_lookup, results)

        # P14 vs P15
        if p14_lookup:
            comp["unseen_only"]["p14_vs_p15"] = _pairwise(
                "p14", p14_lookup, "p15", p15_lookup, unseen_results)
            comp["seen_only"]["p14_vs_p15"] = _pairwise(
                "p14", p14_lookup, "p15", p15_lookup, seen_results)
            comp["all_40"]["p14_vs_p15"] = _pairwise(
                "p14", p14_lookup, "p15", p15_lookup, results)

        # P13 vs P14 (for reference)
        if p13_lookup and p14_lookup:
            comp["unseen_only"]["p13_vs_p14"] = _pairwise(
                "p13", p13_lookup, "p14", p14_lookup, unseen_results)

        return comp

    # ================================================================
    # Headline Report
    # ================================================================

    def _print_headline(self, output: dict):
        """Print Phase 15 headline results."""
        comp = output.get("comparison", {})
        unseen = comp.get("unseen_only", {})
        alert_stats = output.get("alert_statistics", {})
        summary = output.get("summary", {})
        mem = output.get("memory_growth", {})

        print(f"\n{'='*70}")
        print(f"  +======================================================+")
        print(f"  |  PHASE 15 RESULTS -- Gated CARE-ALERT (Alpha Trio)   |")
        print(f"  +======================================================+")

        # P13 vs P15 (primary comparison)
        p13v15 = unseen.get("p13_vs_p15", {})
        if p13v15:
            n = p13v15.get("n_questions", 35)
            p13_acc = p13v15.get("p13_accuracy", 0) * 100
            p15_acc = p13v15.get("p15_accuracy", 0) * 100
            delta = p13v15.get("delta_pp", 0)
            sign = "+" if delta >= 0 else ""

            print(f"  |  UNSEEN ({n}): P13 vs P15                           |")
            print(f"  |    P13 accuracy: {p13v15.get('p13_correct', '?')}/{n} ({p13_acc:.1f}%)                 |")
            print(f"  |    P15 accuracy: {p13v15.get('p15_correct', '?')}/{n} ({p15_acc:.1f}%)                 |")
            print(f"  |    Delta:        {sign}{delta:.1f} pp                          |")

            mcn = p13v15.get("mcnemar", {})
            if mcn:
                print(f"  |    McNemar p:    {mcn.get('p_value', '?')}                       |")

            care = p13v15.get("care", {})
            if care:
                print(f"  |  CARE: P13={care.get('p13_avg', '?')} -> "
                      f"P15={care.get('p15_avg', '?')} "
                      f"(delta={care.get('delta', 0):+.4f})    |")

            debt = p13v15.get("debt", {})
            if debt:
                print(f"  |  Debt: P13={debt.get('p13_avg', '?')} -> "
                      f"P15={debt.get('p15_avg', '?')} "
                      f"(delta={debt.get('delta', 0):+.4f})    |")

        # P14 vs P15
        p14v15 = unseen.get("p14_vs_p15", {})
        if p14v15:
            print(f"  |------------------------------------------------------|")
            delta14 = p14v15.get("delta_pp", 0)
            sign14 = "+" if delta14 >= 0 else ""
            print(f"  |  P14 vs P15: {sign14}{delta14:.1f} pp (McNemar p={p14v15.get('mcnemar', {}).get('p_value', '?')})")

        # Alert statistics
        print(f"  |------------------------------------------------------|")
        print(f"  |  ALERT STATISTICS                                    |")
        print(f"  |    Rate: {alert_stats.get('alert_rate', 0)*100:.0f}% "
              f"({alert_stats.get('questions_with_any_alert', 0)}/{alert_stats.get('total_questions', 0)} questions)              |")
        print(f"  |    R2 alerts: {alert_stats.get('alerts_after_r2', 0)} | "
              f"R3 alerts: {alert_stats.get('alerts_after_r3', 0)}                    |")

        acc_a = alert_stats.get("accuracy_when_alerted")
        acc_na = alert_stats.get("accuracy_when_not_alerted")
        if acc_a is not None and acc_na is not None:
            print(f"  |    Acc (alerted):     {acc_a*100:.1f}% "
                  f"(n={alert_stats.get('n_alerted', 0)})                  |")
            print(f"  |    Acc (not alerted): {acc_na*100:.1f}% "
                  f"(n={alert_stats.get('n_not_alerted', 0)})                 |")

        print(f"  |------------------------------------------------------|")
        print(f"  |  Memory: +{mem.get('added_during_run', 0)} auto-stored (diagnostic only)   |")
        print(f"  |  Cost: ${output.get('cost', {}).get('total_usd', 0):.4f} "
              f"({output.get('cost', {}).get('total_calls', 0)} API calls)           |")
        print(f"  +======================================================+")
        print(f"{'='*70}\n")

    # ================================================================
    # Review Mode (no API calls)
    # ================================================================

    def review(self):
        """Print review artifacts for user audit. NO API calls."""
        print(f"\n{'='*70}")
        print(f"  PHASE 15 REVIEW -- Artifacts for Audit")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*70}")

        # 1. System prompt
        print(f"\n  === SYSTEM PROMPT ===")
        prompt = self.build_system_prompt()
        print(f"  Length: {len(prompt)} chars")
        print(f"  Contains [MEMORY CONTEXT]: {'[MEMORY CONTEXT]' in prompt}")
        print(f"\n{prompt}")

        # 2. Alert thresholds
        print(f"\n  === CARE-ALERT CONFIGURATION ===")
        print(f"  MD threshold after R2: {PHASE15_ALERT_MD_THRESHOLD_R2}")
        print(f"  MD threshold after R3: {PHASE15_ALERT_MD_THRESHOLD_R3}")
        print(f"  Debt store threshold:  {PHASE15_DEBT_STORE_THRESHOLD}")

        # 3. Baselines
        print(f"\n  === BASELINES ===")
        print(f"  Phase 13: {PHASE15_BASELINE_P13} (exists: {os.path.exists(str(PHASE15_BASELINE_P13))})")
        print(f"  Phase 14: {PHASE15_BASELINE_P14} (exists: {os.path.exists(str(PHASE15_BASELINE_P14))})")

        # 4. Configuration
        print(f"\n  === CONFIGURATION ===")
        print(f"  Trio: {[MODEL_SHORT.get(m, m) for m in self.trio]}")
        print(f"  Temperature: {PHASE15_TEMPERATURE}")
        print(f"  Max tokens: {PHASE15_MAX_TOKENS}")
        print(f"  Budget limit: ${PHASE15_BUDGET_LIMIT:.2f}")
        print(f"  N questions: {len(self.questions)}")
        print(f"  Seen IDs: {self.seen_ids}")

        # 5. Sample alert
        print(f"\n  === SAMPLE ALERT (simulated divergence) ===")
        sample_interim = {
            "positions_by_agent": {
                "openai/gpt-4o": 1.0,
                "deepseek/deepseek-chat": 2.0,
            },
            "position_letters": {
                "openai/gpt-4o": "B",
                "deepseek/deepseek-chat": "C",
            },
            "divergence": True,
            "max_spread": 1.0,
            "interim_md": 0.72,
            "interim_care": 0.67,
            "care_optimum": 1.5,
            "n_agents": 2,
            "per_agent_loss": {
                "openai/gpt-4o": 0.25,
                "deepseek/deepseek-chat": 0.25,
            },
            "minority_agent": "deepseek/deepseek-chat",
            "minority_loss": 0.25,
            "error": None,
        }
        alert_l1 = generate_care_alert(sample_interim, round_num=2, escalation=1)
        print(f"  Level 1: {alert_l1}")

        sample_interim_3 = dict(sample_interim)
        sample_interim_3["positions_by_agent"]["meta-llama/llama-3.3-70b-instruct"] = 1.0
        sample_interim_3["position_letters"]["meta-llama/llama-3.3-70b-instruct"] = "B"
        sample_interim_3["n_agents"] = 3
        sample_interim_3["interim_md"] = 1.23
        alert_l2 = generate_care_alert(sample_interim_3, round_num=3, escalation=2)
        print(f"  Level 2: {alert_l2}")

        print(f"\n{'='*70}")
        print(f"  Review complete. Run `python run_phase15.py` to start.")
        print(f"{'='*70}\n")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase 15: Gated CARE-ALERT (Real-time Working Memory)"
    )
    parser.add_argument("--test", type=int, default=None,
                        help="Number of questions for test run")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate pipeline without API calls")
    parser.add_argument("--review", action="store_true",
                        help="Print review artifacts, NO API calls")
    args = parser.parse_args()

    n = args.test if args.test else None

    if args.review:
        runner = Phase15Runner(n_questions=n, dry_run=True)
        runner.review()
        return

    if args.dry_run:
        runner = Phase15Runner(n_questions=n, dry_run=True)
        runner.run_experiment()
        return

    runner = Phase15Runner(n_questions=n)
    runner.run_experiment()


if __name__ == "__main__":
    main()
