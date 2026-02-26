#!/usr/bin/env python3
# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
ARRIVAL Phase 14: Stateful ARRIVAL Benchmark (ARRIVAL-MNEMO)
============================================================
Proves that persistent memory from Phase 13 cognitive scars improves
consensus quality and accuracy on the same GPQA Diamond questions.

Design:
  - Same 40 questions, same Alpha trio, same 4-round ARRIVAL protocol
  - ONLY difference: system prompt now includes [MEMORY CONTEXT] block
  - Memory is injected from arrival_memory_alpha.json (built in Step 2)
  - New episodic memories auto-created when meaning_debt > threshold

Comparison (unseen only, N=35):
  - Phase 13 Alpha (stateless) vs Phase 14 Alpha (stateful)
  - McNemar test for accuracy, Mann-Whitney U for CARE/Debt deltas
  - 5 seen questions reported separately (NOT in inferential statistics)

DATA LEAKAGE GUARD:
  - Memory NEVER contains correct answers, answer letters, or question text
  - Auto-stored memories during run contain ONLY structural observations
  - key_insight is always about dialogue dynamics, never about answer content

Usage:
    python run_phase14.py              # Full run (40 questions)
    python run_phase14.py --test 3     # Test on 3 questions only
    python run_phase14.py --dry-run    # Validate pipeline without API calls
    python run_phase14.py --review     # Print review artifacts, NO API calls

Output:
    results/phase14_results_YYYYMMDD_HHMMSS.json
    logs/phase14_YYYYMMDD_HHMMSS.jsonl + .txt

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
    PHASE14_TRIO, PHASE14_TRIO_NAME, PHASE14_TEMPERATURE,
    PHASE14_MAX_TOKENS, PHASE14_BUDGET_LIMIT,
    PHASE14_MEMORY_TOP_K, PHASE14_MEMORY_MAX_CHARS,
    PHASE14_DEBT_STORE_THRESHOLD, PHASE14_MEMORY_FILE,
    PHASE14_BASELINE_FILE, PHASE14_SCARS_FILE,
    PHASE14_N_QUESTIONS,
    RESULTS_DIR, LOGS_DIR,
)
from openrouter_client import OpenRouterClient, BudgetExceededError
from metrics import extract_answer_letter, find_all_atoms, detect_emergent_atoms
from crdt_metrics import compute_care_resolve, compute_meaning_debt
from enhanced_logger import EnhancedLogger
from memory.store import MemoryStore
from memory.schema import EpisodicMemory
from experiments.questions_gpqa import QUESTIONS, DOMAINS


# ============================================================
# System Prompts (identical to Phase 13 — DO NOT MODIFY)
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
# Phase 14 Runner
# ============================================================

class Phase14Runner:
    """
    Stateful ARRIVAL Benchmark Runner.

    Identical to Phase 13 ARRIVAL pipeline except:
    1. System prompt includes [MEMORY CONTEXT] block from MemoryStore
    2. Auto-stores new EpisodicMemory when meaning_debt > threshold
    3. Compares results against Phase 13 baseline (unseen questions only)
    """

    def __init__(self, n_questions=None, dry_run=False):
        self.dry_run = dry_run
        self.trio = PHASE14_TRIO
        self.trio_name = PHASE14_TRIO_NAME
        self.n_questions = n_questions or PHASE14_N_QUESTIONS
        self.questions = QUESTIONS[:self.n_questions]

        # Client
        if not dry_run:
            self.client = OpenRouterClient(budget_limit=PHASE14_BUDGET_LIMIT)
        else:
            self.client = None

        # Memory store
        self.memory_store = MemoryStore(str(PHASE14_MEMORY_FILE))
        self.memory_store.load()
        self.initial_memory_count = len(self.memory_store.memories)

        # Phase 13 baseline
        self.baseline = self._load_baseline()
        self.seen_ids = self._load_seen_ids()

        # Logger
        self.start_time = datetime.now(timezone.utc)
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        log_dir = str(LOGS_DIR)
        os.makedirs(log_dir, exist_ok=True)
        if not dry_run:
            self.logger = EnhancedLogger(
                log_dir=log_dir,
                experiment_group=f"phase14_{timestamp}",
            )
        else:
            self.logger = None

        # Counters
        self.total_cost = 0.0
        self.total_calls = 0
        self.memories_added = 0

    def _load_baseline(self) -> dict:
        """Load Phase 13 results for comparison."""
        path = str(PHASE14_BASELINE_FILE)
        if not os.path.exists(path):
            print(f"  WARNING: Phase 13 baseline not found at {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_seen_ids(self) -> list:
        """Load seen question IDs from scars file."""
        path = str(PHASE14_SCARS_FILE)
        if not os.path.exists(path):
            print(f"  WARNING: Scars file not found at {path}")
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
    # Memory Injection
    # ================================================================

    def build_system_prompt(self, question: dict) -> str:
        """
        Build system prompt = ARRIVAL_SYSTEM + [MEMORY CONTEXT].

        The memory block is appended AFTER the base system prompt,
        injecting relevant memories based on the question's domain.
        """
        goal = f"GPQA Diamond {question['domain']} graduate-level science"
        memory_block = self.memory_store.format_injection(
            goal, top_k=PHASE14_MEMORY_TOP_K
        )

        if memory_block:
            # Truncate if too long
            if len(memory_block) > PHASE14_MEMORY_MAX_CHARS:
                memory_block = memory_block[:PHASE14_MEMORY_MAX_CHARS] + "\n[/MEMORY CONTEXT]"
            return ARRIVAL_SYSTEM + "\n\n" + memory_block
        else:
            return ARRIVAL_SYSTEM

    # ================================================================
    # 4-Round ARRIVAL Protocol (identical to Phase 13)
    # ================================================================

    def run_arrival_with_memory(self, question: dict) -> dict:
        """
        4-round ARRIVAL Protocol with memory injection + CRDT overlay.
        Identical to Phase 13 run_arrival_with_crdt() except for system prompt.
        """
        if self.dry_run:
            return {
                "condition": "arrival_mnemo",
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
                "memory_injected": True,
            }

        # Build system prompt with memory injection
        system_prompt = self.build_system_prompt(question)
        memory_injected = "[MEMORY CONTEXT]" in system_prompt

        dialogue = []
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

        # Round 1: Alpha (trio[0] = GPT4o) — initial analysis
        model_a = self.trio[0]
        prompt_1 = ARRIVAL_ROUND_PROMPTS[1].format(
            node_name="Alpha",
            model_short=MODEL_SHORT.get(model_a, model_a),
            **choice_vars
        )
        resp_1 = self.client.generate(
            prompt=prompt_1, model=model_a,
            system_prompt=system_prompt,
            temperature=PHASE14_TEMPERATURE,
            max_tokens=PHASE14_MAX_TOKENS,
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
        all_atoms.extend(find_all_atoms(resp_1.text))
        emergent.update(detect_emergent_atoms(resp_1.text))
        self._log_api_call(q["id"], "arrival_mnemo", 1, model_a, resp_1.text,
                           extract_answer_letter(resp_1.text), resp_1.cost_usd,
                           resp_1.prompt_tokens + resp_1.completion_tokens, resp_1.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 2: Beta (trio[1] = DeepSeekV3) — cross-critique
        model_b = self.trio[1]
        prompt_2 = ARRIVAL_ROUND_PROMPTS[2].format(
            node_name="Beta",
            model_short=MODEL_SHORT.get(model_b, model_b),
            previous_response=resp_1.text[:1500],
            **choice_vars
        )
        resp_2 = self.client.generate(
            prompt=prompt_2, model=model_b,
            system_prompt=system_prompt,
            temperature=PHASE14_TEMPERATURE,
            max_tokens=PHASE14_MAX_TOKENS,
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
        all_atoms.extend(find_all_atoms(resp_2.text))
        emergent.update(detect_emergent_atoms(resp_2.text))
        self._log_api_call(q["id"], "arrival_mnemo", 2, model_b, resp_2.text,
                           extract_answer_letter(resp_2.text), resp_2.cost_usd,
                           resp_2.prompt_tokens + resp_2.completion_tokens, resp_2.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 3: Gamma (trio[2] = Llama33) — synthesis
        model_c = self.trio[2]
        prompt_3 = ARRIVAL_ROUND_PROMPTS[3].format(
            node_name="Gamma",
            model_short=MODEL_SHORT.get(model_c, model_c),
            response_1=resp_1.text[:1200],
            response_2=resp_2.text[:1200],
            **choice_vars
        )
        resp_3 = self.client.generate(
            prompt=prompt_3, model=model_c,
            system_prompt=system_prompt,
            temperature=PHASE14_TEMPERATURE,
            max_tokens=PHASE14_MAX_TOKENS,
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
        all_atoms.extend(find_all_atoms(resp_3.text))
        emergent.update(detect_emergent_atoms(resp_3.text))
        self._log_api_call(q["id"], "arrival_mnemo", 3, model_c, resp_3.text,
                           extract_answer_letter(resp_3.text), resp_3.cost_usd,
                           resp_3.prompt_tokens + resp_3.completion_tokens, resp_3.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 4: Alpha (trio[0] = GPT4o) — final consensus
        prompt_4 = ARRIVAL_ROUND_PROMPTS[4].format(
            node_name="Alpha",
            model_short=MODEL_SHORT.get(model_a, model_a),
            response_1=resp_1.text[:800],
            response_2=resp_2.text[:800],
            response_3=resp_3.text[:800],
            **choice_vars
        )
        resp_4 = self.client.generate(
            prompt=prompt_4, model=model_a,
            system_prompt=system_prompt,
            temperature=PHASE14_TEMPERATURE,
            max_tokens=PHASE14_MAX_TOKENS,
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
        all_atoms.extend(find_all_atoms(resp_4.text))
        emergent.update(detect_emergent_atoms(resp_4.text))
        self._log_api_call(q["id"], "arrival_mnemo", 4, model_a, resp_4.text,
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
            "condition": "arrival_mnemo",
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
            "memory_injected": memory_injected,
        }

    # ================================================================
    # Auto-Store Memory (when dialogue quality is poor)
    # ================================================================

    def auto_store_memory(self, question: dict, arrival_result: dict):
        """
        If meaning_debt exceeds threshold, create a new EpisodicMemory.
        DATA LEAKAGE GUARD: NEVER stores correct answer or question text.
        """
        debt = arrival_result["crdt"].get("meaning_debt", {})
        total_debt = debt.get("total_meaning_debt", 0)

        if total_debt <= PHASE14_DEBT_STORE_THRESHOLD:
            return  # Dialogue quality acceptable

        care = arrival_result["crdt"].get("care_resolve", {})
        care_val = care.get("care_resolve", 0.5)

        # Determine structural insight (NO answer info!)
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

        # Verify no data leakage (regex check for answer letter patterns)
        import re
        assert not re.search(r'answer\s+is\s+[A-D]', key_insight, re.IGNORECASE), \
            f"DATA LEAKAGE: answer letter in auto-stored key_insight"
        assert "correct answer" not in key_insight.lower(), \
            f"DATA LEAKAGE: 'correct answer' in auto-stored key_insight"

        trio_short = [MODEL_SHORT.get(m, m) for m in self.trio]
        ep = self.memory_store.extract_from_session(
            session_id=f"phase14_{question['id']}",
            task=f"GPQA Diamond {question['domain']}",
            models=trio_short,
            accuracy="unknown",  # NEVER record correctness
            care_resolve=care_val,
            meaning_debt=total_debt,
            key_insight=key_insight,
            atoms_used=list(arrival_result.get("atoms_used", {}).keys()),
            domain=question["domain"],
        )
        self.memory_store.save()
        self.memories_added += 1

        print(f"    [MNEMO] Auto-stored episodic memory: MD={total_debt:.2f}, "
              f"CARE={care_val:.3f} [{health}]")

    # ================================================================
    # Main Experiment Loop
    # ================================================================

    def run_experiment(self):
        """Run Phase 14: ARRIVAL + Memory on all questions."""
        print(f"\n{'='*70}")
        print(f"  ARRIVAL-MNEMO Phase 14: Stateful Benchmark (Alpha Trio)")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  Questions: {len(self.questions)} | Trio: {self.trio_name}")
        print(f"  Memory store: {self.initial_memory_count} memories loaded")
        print(f"  Seen questions: {self.seen_ids}")
        print(f"  Budget limit: ${PHASE14_BUDGET_LIMIT:.2f}")
        print(f"{'='*70}")

        results = []

        for i, question in enumerate(self.questions):
            q_id = question["id"]
            is_seen = q_id in self.seen_ids
            marker = " [SEEN]" if is_seen else ""

            print(f"\n  [{i+1}/{len(self.questions)}] {q_id} [{question['domain']}]{marker}")

            # Budget check
            if not self.dry_run and self.total_cost >= PHASE14_BUDGET_LIMIT:
                print(f"  BUDGET LIMIT REACHED (${self.total_cost:.4f}). Stopping.")
                break

            # Run ARRIVAL with memory
            try:
                arrival_result = self.run_arrival_with_memory(question)
            except BudgetExceededError as e:
                print(f"  BUDGET EXCEEDED: {e}")
                break
            except Exception as e:
                print(f"  ERROR: {e}")
                arrival_result = {
                    "condition": "arrival_mnemo",
                    "error": str(e),
                    "correct": False,
                    "final_answer": None,
                    "crdt": {"care_resolve": {}, "meaning_debt": {}},
                }

            # Print result
            correct_str = "CORRECT" if arrival_result.get("correct") else "WRONG"
            answer = arrival_result.get("final_answer", "?")
            care = arrival_result["crdt"].get("care_resolve", {}).get("care_resolve", "?")
            debt = arrival_result["crdt"].get("meaning_debt", {}).get("total_meaning_debt", "?")
            mem = "MEM" if arrival_result.get("memory_injected") else "NO_MEM"
            print(f"    Answer={answer} ({correct_str}) | CARE={care} | MD={debt} | {mem}")

            if not self.dry_run:
                cost = arrival_result.get("cost_usd", 0)
                print(f"    Cost: ${cost:.4f} | Total: ${self.total_cost:.4f}")

            # Auto-store memory if dialogue quality poor
            if not self.dry_run:
                self.auto_store_memory(question, arrival_result)

            # Store result
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
        # Comparison with Phase 13
        # ================================================================
        comparison = self._compute_comparison(results)

        # ================================================================
        # Build output
        # ================================================================
        output = {
            "experiment": "ARRIVAL-MNEMO Phase 14: Stateful Benchmark",
            "author": "Mefodiy Kelevra",
            "orcid": "0009-0003-4153-392X",
            "timestamp": self.start_time.isoformat(),
            "config": {
                "trio": [MODEL_SHORT.get(m, m) for m in self.trio],
                "trio_name": self.trio_name,
                "temperature": PHASE14_TEMPERATURE,
                "max_tokens": PHASE14_MAX_TOKENS,
                "memory_top_k": PHASE14_MEMORY_TOP_K,
                "memory_max_chars": PHASE14_MEMORY_MAX_CHARS,
                "debt_store_threshold": PHASE14_DEBT_STORE_THRESHOLD,
                "budget_limit": PHASE14_BUDGET_LIMIT,
                "n_questions": len(self.questions),
            },
            "seen_question_ids": self.seen_ids,
            "results": {
                "alpha": [r for r in results],
            },
            "comparison": comparison,
            "memory_growth": {
                "initial": self.initial_memory_count,
                "final": len(self.memory_store.memories),
                "added_during_run": self.memories_added,
            },
            "cost": {
                "total_usd": round(self.total_cost, 4),
                "total_calls": self.total_calls,
                "budget_limit": PHASE14_BUDGET_LIMIT,
            },
            "summary": self._compute_summary(results),
        }

        # Save results
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        results_file = str(RESULTS_DIR / f"phase14_results_{timestamp}.json")
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n  Results saved: {results_file}")

        # Print headline
        self._print_headline(output)

        return output

    # ================================================================
    # Summary Statistics
    # ================================================================

    def _compute_summary(self, results: list) -> dict:
        """Compute Phase 14 summary statistics."""
        all_results = results
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
            "all_40": _stats(all_results),
            "unseen_35": _stats(unseen_results),
            "seen_5": _stats(seen_results),
        }

    # ================================================================
    # Phase 13 vs Phase 14 Comparison
    # ================================================================

    def _compute_comparison(self, results: list) -> dict:
        """
        Compare Phase 14 (stateful) vs Phase 13 (stateless) on unseen questions.
        Uses McNemar test for accuracy, Mann-Whitney U for CARE/Debt.
        """
        if not self.baseline:
            return {"error": "No Phase 13 baseline loaded"}

        # Get Phase 13 Alpha results
        p13_alpha = self.baseline.get("results", {}).get("alpha", [])
        if not p13_alpha:
            return {"error": "No Phase 13 Alpha results in baseline"}

        # Build Phase 13 lookup: question_id -> result
        p13_lookup = {r["question_id"]: r for r in p13_alpha}

        # Separate seen/unseen
        unseen_results = [r for r in results if not r["is_seen"]]
        seen_results = [r for r in results if r["is_seen"]]

        def _compare(p14_list, label):
            """Compare Phase 13 vs Phase 14 for a list of results."""
            p13_correct = 0
            p14_correct = 0
            b = 0  # P13 right, P14 wrong
            c = 0  # P13 wrong, P14 right
            p13_care = []
            p14_care = []
            p13_debt = []
            p14_debt = []

            for r14 in p14_list:
                qid = r14["question_id"]
                r13 = p13_lookup.get(qid)
                if not r13:
                    continue

                # Accuracy
                ok_13 = r13.get("arrival", {}).get("correct", False)
                ok_14 = r14.get("arrival", {}).get("correct", False)
                p13_correct += int(ok_13)
                p14_correct += int(ok_14)

                if ok_13 and not ok_14:
                    b += 1
                elif not ok_13 and ok_14:
                    c += 1

                # CARE
                care_13 = r13.get("crdt", {}).get("care_resolve", {}).get("care_resolve")
                care_14 = r14.get("crdt", {}).get("care_resolve", {}).get("care_resolve")
                if care_13 is not None:
                    p13_care.append(care_13)
                if care_14 is not None:
                    p14_care.append(care_14)

                # Debt
                debt_13 = r13.get("crdt", {}).get("meaning_debt", {}).get("total_meaning_debt")
                debt_14 = r14.get("crdt", {}).get("meaning_debt", {}).get("total_meaning_debt")
                if debt_13 is not None:
                    p13_debt.append(debt_13)
                if debt_14 is not None:
                    p14_debt.append(debt_14)

            total = len(p14_list)
            p13_acc = p13_correct / total if total > 0 else 0
            p14_acc = p14_correct / total if total > 0 else 0

            result = {
                "n_questions": total,
                "phase13_accuracy": round(p13_acc, 4),
                "phase14_accuracy": round(p14_acc, 4),
                "delta_pp": round((p14_acc - p13_acc) * 100, 1),
                "phase13_correct": p13_correct,
                "phase14_correct": p14_correct,
            }

            # McNemar's test (with continuity correction)
            if b + c > 0:
                chi2_stat = (abs(b - c) - 1) ** 2 / (b + c)
                from scipy.stats import chi2 as chi2_dist
                p_value = chi2_dist.sf(chi2_stat, df=1)  # survival function = 1 - CDF
            else:
                chi2_stat = 0
                p_value = 1.0

            result["mcnemar"] = {
                "b_p13right_p14wrong": b,
                "c_p13wrong_p14right": c,
                "chi2": round(chi2_stat, 4),
                "p_value": round(p_value, 6),
            }

            # CARE comparison
            if p13_care and p14_care:
                result["care"] = {
                    "phase13_avg": round(sum(p13_care) / len(p13_care), 4),
                    "phase14_avg": round(sum(p14_care) / len(p14_care), 4),
                    "delta": round(
                        sum(p14_care) / len(p14_care) - sum(p13_care) / len(p13_care), 4
                    ),
                }
                # Mann-Whitney U test
                try:
                    from scipy.stats import mannwhitneyu
                    U, p = mannwhitneyu(p14_care, p13_care, alternative='greater')
                    result["care"]["mann_whitney_U"] = round(U, 2)
                    result["care"]["mann_whitney_p"] = round(p, 6)
                except Exception as e:
                    result["care"]["mann_whitney_error"] = str(e)

            # Debt comparison
            if p13_debt and p14_debt:
                result["debt"] = {
                    "phase13_avg": round(sum(p13_debt) / len(p13_debt), 4),
                    "phase14_avg": round(sum(p14_debt) / len(p14_debt), 4),
                    "delta": round(
                        sum(p14_debt) / len(p14_debt) - sum(p13_debt) / len(p13_debt), 4
                    ),
                }
                try:
                    from scipy.stats import mannwhitneyu
                    U, p = mannwhitneyu(p13_debt, p14_debt, alternative='greater')
                    result["debt"]["mann_whitney_U"] = round(U, 2)
                    result["debt"]["mann_whitney_p"] = round(p, 6)
                except Exception as e:
                    result["debt"]["mann_whitney_error"] = str(e)

            return result

        return {
            "unseen_only": _compare(unseen_results, "unseen"),
            "seen_only": _compare(seen_results, "seen"),
            "all_40": _compare(results, "all"),
        }

    # ================================================================
    # Headline Report
    # ================================================================

    def _print_headline(self, output: dict):
        """Print the Phase 14 headline results."""
        comp = output.get("comparison", {})
        unseen = comp.get("unseen_only", {})
        seen = comp.get("seen_only", {})
        summary = output.get("summary", {})
        mem = output.get("memory_growth", {})

        print(f"\n{'='*70}")
        print(f"  +======================================================+")
        print(f"  |  PHASE 14 RESULTS -- Stateful ARRIVAL (Alpha Trio)   |")
        print(f"  +======================================================+")

        if unseen:
            n = unseen.get("n_questions", 35)
            p13_acc = unseen.get("phase13_accuracy", 0) * 100
            p14_acc = unseen.get("phase14_accuracy", 0) * 100
            delta = unseen.get("delta_pp", 0)
            p13_c = unseen.get("phase13_correct", 0)
            p14_c = unseen.get("phase14_correct", 0)
            sign = "+" if delta >= 0 else ""

            print(f"  |  UNSEEN QUESTIONS ({n}):                            |")
            print(f"  |    Phase 13 accuracy: {p13_c}/{n} ({p13_acc:.1f}%)              |")
            print(f"  |    Phase 14 accuracy: {p14_c}/{n} ({p14_acc:.1f}%)              |")
            print(f"  |    Delta:             {sign}{delta:.1f} pp                     |")

            mcn = unseen.get("mcnemar", {})
            if mcn:
                print(f"  |    McNemar p-value:   {mcn.get('p_value', '?')}                  |")
                print(f"  |    (b={mcn.get('b_p13right_p14wrong', '?')}, "
                      f"c={mcn.get('c_p13wrong_p14right', '?')}, "
                      f"chi2={mcn.get('chi2', '?')})           |")

            care = unseen.get("care", {})
            if care:
                print(f"  |  CARE: P13={care.get('phase13_avg', '?'):.4f} -> "
                      f"P14={care.get('phase14_avg', '?'):.4f} "
                      f"(delta={care.get('delta', '?'):+.4f})  |")

            debt = unseen.get("debt", {})
            if debt:
                print(f"  |  Debt: P13={debt.get('phase13_avg', '?'):.4f} -> "
                      f"P14={debt.get('phase14_avg', '?'):.4f} "
                      f"(delta={debt.get('delta', '?'):+.4f})  |")

        if seen:
            print(f"  |------------------------------------------------------|")
            n_s = seen.get("n_questions", 5)
            p14_acc_s = seen.get("phase14_accuracy", 0) * 100
            p14_c_s = seen.get("phase14_correct", 0)
            print(f"  |  SEEN QUESTIONS ({n_s}): {p14_c_s}/{n_s} ({p14_acc_s:.1f}%)                  |")

        print(f"  |------------------------------------------------------|")
        print(f"  |  Memory: {mem.get('initial', '?')} initial -> "
              f"{mem.get('final', '?')} final "
              f"(+{mem.get('added_during_run', '?')} during run)  |")
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
        print(f"  PHASE 14 REVIEW -- Artifacts for Audit")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*70}")

        # 1. Memory Store contents
        print(f"\n  === MEMORY STORE ===")
        print(f"  File: {PHASE14_MEMORY_FILE}")
        stats = self.memory_store.stats()
        print(f"  Total memories: {stats['total']}")
        for layer, count in stats['by_layer'].items():
            print(f"    {layer}: {count}")

        print(f"\n  --- All memories ---")
        for m in self.memory_store.memories:
            m_dict = m.to_dict()
            print(f"  [{m.layer}] {m.id}")
            if hasattr(m, 'task'):
                print(f"    task: {m.task}")
            if hasattr(m, 'key_insight') and m.key_insight:
                print(f"    insight: {m.key_insight[:120]}...")
            if hasattr(m, 'strategy_name'):
                print(f"    strategy: {m.strategy_name}")
            if hasattr(m, 'agent_model'):
                print(f"    agent: {m.agent_model}, trust={m.trust_score:.3f}")
                print(f"    calibration: {m.domain_calibration}")
            print()

        # 2. Seen Questions
        print(f"  === SEEN QUESTIONS (excluded from inferential statistics) ===")
        for qid in self.seen_ids:
            q = next((q for q in QUESTIONS if q["id"] == qid), None)
            if q:
                print(f"  {qid} [{q['domain']}]")
            else:
                print(f"  {qid} [domain unknown]")

        # 3. Sample system prompt
        print(f"\n  === SAMPLE SYSTEM PROMPT (first question) ===")
        if self.questions:
            q = self.questions[0]
            prompt = self.build_system_prompt(q)
            print(f"  Question: {q['id']} [{q['domain']}]")
            print(f"  Prompt length: {len(prompt)} chars")
            print(f"  Memory injected: {'[MEMORY CONTEXT]' in prompt}")
            print(f"\n{prompt}")

        # 4. Data leakage check
        print(f"\n  === DATA LEAKAGE AUDIT ===")
        import re
        clean = True
        for m in self.memory_store.memories:
            m_json = json.dumps(m.to_dict(), ensure_ascii=False).lower()
            for pattern in [r'correct.?answer', r'answer\s+is\s+[a-d]', r'option\s+[a-d]\s+is\s+correct']:
                if re.search(pattern, m_json):
                    print(f"  WARNING: Potential leakage in {m.id}: pattern '{pattern}'")
                    clean = False
        if clean:
            print(f"  PASSED: No answer information found in any memory")

        # 5. Test results
        print(f"\n  === CONFIGURATION ===")
        print(f"  Trio: {[MODEL_SHORT.get(m, m) for m in self.trio]}")
        print(f"  Temperature: {PHASE14_TEMPERATURE}")
        print(f"  Max tokens: {PHASE14_MAX_TOKENS}")
        print(f"  Memory top_k: {PHASE14_MEMORY_TOP_K}")
        print(f"  Memory max chars: {PHASE14_MEMORY_MAX_CHARS}")
        print(f"  Debt threshold: {PHASE14_DEBT_STORE_THRESHOLD}")
        print(f"  Budget limit: ${PHASE14_BUDGET_LIMIT:.2f}")
        print(f"  Baseline: {PHASE14_BASELINE_FILE}")
        print(f"  N questions: {len(self.questions)}")

        print(f"\n{'='*70}")
        print(f"  Review complete. Run `python run_phase14.py` to start experiment.")
        print(f"{'='*70}\n")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase 14: Stateful ARRIVAL Benchmark (ARRIVAL-MNEMO)"
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
        runner = Phase14Runner(n_questions=n, dry_run=True)
        runner.review()
        return

    if args.dry_run:
        runner = Phase14Runner(n_questions=n, dry_run=True)
        runner.run_experiment()
        return

    runner = Phase14Runner(n_questions=n)
    runner.run_experiment()


if __name__ == "__main__":
    main()
