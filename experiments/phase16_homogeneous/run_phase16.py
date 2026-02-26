# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
ARRIVAL Phase 16: Homogeneous Ensemble Test — Echo-Chamber vs Cognitive Diversity
5 × Qwen3-235B agents with different personas, same GPQA Diamond 40 questions.

Hypothesis: Homogeneous LLM ensembles suffer echo-chamber effect — high R1 unanimity,
rapid false convergence, suppressed correct minorities, and lower accuracy than
heterogeneous Phase 13 trios.

Conditions: Solo | Majority Vote | ARRIVAL Protocol (4-round, 5-agent) + CRDT overlay.

Usage:
    python run_phase16.py                  # Full run (40 questions)
    python run_phase16.py --test 3         # Test on 3 questions only
    python run_phase16.py --dry-run        # Validate pipeline without API calls
    python run_phase16.py --test-connectivity  # Test Gonka API connection
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from collections import Counter

# Windows encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

# Load .env file if present (GONKA_PRIVATE_KEY, GONKA_SOURCE_URL)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# Add src/ to path for shared imports (no code duplication)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from config_phase16 import (
    PHASE16_BACKEND,
    GONKA_MODEL_SHORT, get_model_id,
    AGENT_NAMES, AGENT_PERSONAS,
    PHASE16_TEMPERATURE, PHASE16_MAX_TOKENS, PHASE16_SOLO_MAX_TOKENS,
    PHASE16_BUDGET_USD, PHASE16_SLEEP, PHASE16_ENABLE_THINKING,
    SOLO_SYSTEM, ARRIVAL_SYSTEM,
    PHASE16_R1_PROMPT, PHASE16_R2_PROMPT, PHASE16_R4_PROMPT,
)

# Resolve model ID at import time (depends on PHASE16_BACKEND)
GONKA_MODEL_ID = get_model_id()
from gonka_client import GonkaClient, LLMResponse
from echo_chamber_metrics import compute_all_echo_chamber_metrics

# Shared imports from src/ (identical computations to Phase 13)
from metrics import extract_answer_letter, find_all_atoms, detect_emergent_atoms
from crdt_metrics import compute_care_resolve, compute_meaning_debt
from enhanced_logger import EnhancedLogger
from phase_13.questions_gpqa import QUESTIONS, DOMAINS


# ============================================================
# Phase 16 Runner
# ============================================================

class Phase16Runner:
    def __init__(self, n_questions=None, dry_run=False):
        self.dry_run = dry_run
        if not dry_run:
            self.client = GonkaClient()
        else:
            self.client = None

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(self.base_dir, "logs")
        self.logger = EnhancedLogger(log_dir, "phase_16_homogeneous")

        self.questions = QUESTIONS[:n_questions] if n_questions else QUESTIONS
        self.total_cost = 0.0
        self.total_calls = 0
        self.start_time = datetime.now()

        # Full experiment log — every API call recorded
        self.full_log = []

    def _log_api_call(self, question_id, condition, round_num, agent_name,
                      response_text, answer, cost, tokens, latency_ms):
        """Log every single API call for transparency."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question_id": question_id,
            "condition": condition,
            "round": round_num,
            "agent": agent_name,
            "model": GONKA_MODEL_ID,
            "model_short": GONKA_MODEL_SHORT.get(GONKA_MODEL_ID, GONKA_MODEL_ID),
            "response_text": response_text,
            "extracted_answer": answer,
            "cost_usd": cost,
            "tokens": tokens,
            "latency_ms": latency_ms,
        }
        self.full_log.append(entry)
        return entry

    def _get_persona_short(self, agent_name: str) -> str:
        """Short persona description for prompts."""
        shorts = {
            "Alpha": "physicist",
            "Beta": "chemist",
            "Gamma": "biologist",
            "Delta": "mathematician",
            "Epsilon": "generalist",
        }
        return shorts.get(agent_name, "expert")

    def _build_system_prompt(self, agent_name: str, use_arrival: bool = True) -> str:
        """Build system prompt: persona + optionally ARRIVAL protocol."""
        persona = AGENT_PERSONAS[agent_name]
        if use_arrival:
            return f"{persona}\n\n{ARRIVAL_SYSTEM}"
        else:
            return f"{persona}\n\n{SOLO_SYSTEM}"

    # ============================================================
    # Condition 1: Solo (5 independent answers)
    # ============================================================

    def run_solo(self, agent_name: str, question: dict) -> dict:
        """Single agent answers independently (no DEUS protocol)."""
        if self.dry_run:
            return {
                "agent_name": agent_name,
                "model": GONKA_MODEL_ID,
                "model_short": GONKA_MODEL_SHORT.get(GONKA_MODEL_ID, GONKA_MODEL_ID),
                "answer": "A",
                "correct": "A" == question["correct"],
                "response_text": "[DRY RUN]",
                "cost_usd": 0.0,
                "tokens": 0,
                "latency_ms": 0.0,
            }

        prompt = f"""Question: {question['question']}

A) {question['choices']['A']}
B) {question['choices']['B']}
C) {question['choices']['C']}
D) {question['choices']['D']}

Think step by step, then state your final answer as "The answer is X"."""

        response = self.client.generate(
            prompt=prompt,
            model=GONKA_MODEL_ID,
            system_prompt=self._build_system_prompt(agent_name, use_arrival=False),
            temperature=PHASE16_TEMPERATURE,
            max_tokens=PHASE16_SOLO_MAX_TOKENS,
        )

        self.total_cost += response.cost_usd
        self.total_calls += 1
        answer = extract_answer_letter(response.text)

        self._log_api_call(
            question["id"], "solo", 0, agent_name,
            response.text, answer, response.cost_usd,
            response.prompt_tokens + response.completion_tokens,
            response.latency_ms,
        )

        return {
            "agent_name": agent_name,
            "model": GONKA_MODEL_ID,
            "model_short": GONKA_MODEL_SHORT.get(GONKA_MODEL_ID, GONKA_MODEL_ID),
            "answer": answer,
            "correct": answer == question["correct"] if answer else False,
            "response_text": response.text,
            "cost_usd": response.cost_usd,
            "tokens": response.prompt_tokens + response.completion_tokens,
            "latency_ms": response.latency_ms,
        }

    # ============================================================
    # Condition 2: Majority Vote (from 5 solo answers)
    # ============================================================

    def run_majority_vote(self, question: dict) -> dict:
        """Five agents answer independently, majority wins."""
        solo_results = []
        for agent_name in AGENT_NAMES:
            result = self.run_solo(agent_name, question)
            solo_results.append(result)
            if not self.dry_run:
                time.sleep(PHASE16_SLEEP)

        answers = [r["answer"] for r in solo_results if r["answer"]]
        if not answers:
            majority_answer = None
        else:
            vote_counts = Counter(answers)
            majority_answer = vote_counts.most_common(1)[0][0]

        total_cost = sum(r["cost_usd"] for r in solo_results)

        return {
            "condition": "majority_vote",
            "agents": AGENT_NAMES,
            "individual_answers": [
                {
                    "agent_name": r["agent_name"],
                    "model": r["model_short"],
                    "answer": r["answer"],
                    "correct": r["correct"],
                    "response_text": r["response_text"],
                }
                for r in solo_results
            ],
            "majority_answer": majority_answer,
            "correct": majority_answer == question["correct"] if majority_answer else False,
            "unanimous": len(set(answers)) == 1 if answers else False,
            "cost_usd": total_cost,
        }

    # ============================================================
    # Condition 3: ARRIVAL Protocol (4 rounds, 5 agents) + CRDT
    # ============================================================

    def run_arrival_with_crdt(self, question: dict) -> dict:
        """4-round ARRIVAL Protocol with 5 homogeneous agents + CRDT overlay."""
        if self.dry_run:
            return {
                "condition": "arrival_crdt",
                "agents": AGENT_NAMES,
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
            }

        dialogue = []
        responses_r1 = {}  # agent_name -> response text
        responses_r2 = {}  # agent_name -> response text
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

        # ---- ROUND 1: All 5 agents answer independently ----
        for agent_name in AGENT_NAMES:
            prompt = PHASE16_R1_PROMPT.format(
                node_name=agent_name,
                persona_short=self._get_persona_short(agent_name),
                **choice_vars,
            )
            resp = self.client.generate(
                prompt=prompt,
                model=GONKA_MODEL_ID,
                system_prompt=self._build_system_prompt(agent_name),
                temperature=PHASE16_TEMPERATURE,
                max_tokens=PHASE16_MAX_TOKENS,
            )

            responses_r1[agent_name] = resp.text
            total_cost += resp.cost_usd
            total_tokens += resp.prompt_tokens + resp.completion_tokens
            self.total_cost += resp.cost_usd
            self.total_calls += 1

            # CRITICAL: use agent name, NOT model name for CRDT
            dialogue.append({
                "round": 1,
                "from": agent_name,
                "message": resp.text,
            })
            all_atoms.extend(find_all_atoms(resp.text))
            emergent.update(detect_emergent_atoms(resp.text))

            self._log_api_call(
                q["id"], "arrival", 1, agent_name,
                resp.text, extract_answer_letter(resp.text),
                resp.cost_usd,
                resp.prompt_tokens + resp.completion_tokens,
                resp.latency_ms,
            )
            time.sleep(PHASE16_SLEEP)

        # ---- ROUND 2: All 5 agents cross-critique (adversarial peer review) ----
        for agent_name in AGENT_NAMES:
            # Build context: all OTHER agents' R1 responses (800 chars each)
            other_parts = []
            for other_name in AGENT_NAMES:
                if other_name != agent_name:
                    other_text = responses_r1[other_name][:800]
                    other_parts.append(f"--- Node {other_name} ({self._get_persona_short(other_name)}) ---\n{other_text}")

            other_responses = "\n\n".join(other_parts)

            prompt = PHASE16_R2_PROMPT.format(
                node_name=agent_name,
                persona_short=self._get_persona_short(agent_name),
                other_responses=other_responses,
                **choice_vars,
            )

            resp = self.client.generate(
                prompt=prompt,
                model=GONKA_MODEL_ID,
                system_prompt=self._build_system_prompt(agent_name),
                temperature=PHASE16_TEMPERATURE,
                max_tokens=PHASE16_MAX_TOKENS,
            )

            responses_r2[agent_name] = resp.text
            total_cost += resp.cost_usd
            total_tokens += resp.prompt_tokens + resp.completion_tokens
            self.total_cost += resp.cost_usd
            self.total_calls += 1

            dialogue.append({
                "round": 2,
                "from": agent_name,
                "message": resp.text,
            })
            all_atoms.extend(find_all_atoms(resp.text))
            emergent.update(detect_emergent_atoms(resp.text))

            self._log_api_call(
                q["id"], "arrival", 2, agent_name,
                resp.text, extract_answer_letter(resp.text),
                resp.cost_usd,
                resp.prompt_tokens + resp.completion_tokens,
                resp.latency_ms,
            )
            time.sleep(PHASE16_SLEEP)

        # ---- ROUND 3: CRDT Overlay (zero API cost) ----
        care_result = compute_care_resolve(dialogue, task_type="mcq")
        debt_result = compute_meaning_debt(dialogue, task_type="mcq")

        # ---- ROUND 4: Alpha finalizes consensus (1 API call) ----
        # Alpha sees all 5 R2 critiques
        critique_parts = []
        for agent_name in AGENT_NAMES:
            critique_text = responses_r2[agent_name][:600]
            critique_parts.append(f"--- Node {agent_name} ({self._get_persona_short(agent_name)}) ---\n{critique_text}")

        all_critiques = "\n\n".join(critique_parts)

        prompt_r4 = PHASE16_R4_PROMPT.format(
            node_name="Alpha",
            persona_short="physicist",
            all_critiques=all_critiques,
            **choice_vars,
        )

        resp_r4 = self.client.generate(
            prompt=prompt_r4,
            model=GONKA_MODEL_ID,
            system_prompt=self._build_system_prompt("Alpha"),
            temperature=PHASE16_TEMPERATURE,
            max_tokens=PHASE16_MAX_TOKENS,
        )

        total_cost += resp_r4.cost_usd
        total_tokens += resp_r4.prompt_tokens + resp_r4.completion_tokens
        self.total_cost += resp_r4.cost_usd
        self.total_calls += 1

        dialogue.append({
            "round": 4,
            "from": "Alpha",
            "message": resp_r4.text,
        })
        all_atoms.extend(find_all_atoms(resp_r4.text))
        emergent.update(detect_emergent_atoms(resp_r4.text))

        self._log_api_call(
            q["id"], "arrival", 4, "Alpha",
            resp_r4.text, extract_answer_letter(resp_r4.text),
            resp_r4.cost_usd,
            resp_r4.prompt_tokens + resp_r4.completion_tokens,
            resp_r4.latency_ms,
        )

        # ---- EXTRACT FINAL ANSWER ----
        # Priority: R4 → R2 majority → R1 majority
        final_answer = extract_answer_letter(resp_r4.text)

        if not final_answer:
            # Fallback: majority from R2
            r2_answers = []
            for agent_name in AGENT_NAMES:
                ans = extract_answer_letter(responses_r2[agent_name])
                if ans:
                    r2_answers.append(ans)
            if r2_answers:
                final_answer = Counter(r2_answers).most_common(1)[0][0]

        if not final_answer:
            # Fallback: majority from R1
            r1_answers = []
            for agent_name in AGENT_NAMES:
                ans = extract_answer_letter(responses_r1[agent_name])
                if ans:
                    r1_answers.append(ans)
            if r1_answers:
                final_answer = Counter(r1_answers).most_common(1)[0][0]

        atom_counts = Counter(all_atoms)

        return {
            "condition": "arrival_crdt",
            "agents": AGENT_NAMES,
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
        }

    # ============================================================
    # Full Experiment
    # ============================================================

    def run_full_experiment(self):
        """Run all conditions for all questions."""
        print(f"\n{'='*70}")
        print(f"  ARRIVAL CRDT - Phase 16: Homogeneous Ensemble (Echo-Chamber Test)")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Backend: {PHASE16_BACKEND}")
        print(f"  Model: {GONKA_MODEL_ID} x5 (homogeneous)")
        print(f"  Agents: {', '.join(AGENT_NAMES)}")
        print(f"  Questions: {len(self.questions)} (GPQA Diamond)")
        print(f"  Temperature: {PHASE16_TEMPERATURE}")
        print(f"  Thinking mode: {'ON' if PHASE16_ENABLE_THINKING else 'OFF'}")
        print(f"  Budget: ${PHASE16_BUDGET_USD}")
        if self.dry_run:
            print(f"  MODE: DRY RUN (no API calls)")
        print(f"{'='*70}\n")

        # Estimate
        n_calls = len(self.questions) * (5 + 11)  # 5 solo + 11 arrival per question
        est_seconds = n_calls * (PHASE16_SLEEP + 3)
        est_minutes = est_seconds / 60
        print(f"  Estimated: ~{n_calls} API calls, ~{est_minutes:.0f} minutes\n")

        all_results = []

        for i, question in enumerate(self.questions):
            # Budget check
            if self.total_cost >= PHASE16_BUDGET_USD * 0.95:
                print(f"\n  !!! BUDGET WARNING: ${self.total_cost:.2f} / ${PHASE16_BUDGET_USD} — stopping !!!")
                break

            q_start = time.time()
            domain_tag = question["domain"][:4].upper()
            print(f"  Q{i+1:02d}/{len(self.questions)} [{domain_tag}] {question['id']}...", end=" ", flush=True)

            # Condition 1: Majority Vote (includes solo)
            majority_result = self.run_majority_vote(question)

            # Condition 2: ARRIVAL + CRDT
            arrival_result = self.run_arrival_with_crdt(question)

            # CRDT summary
            care_score = arrival_result["crdt"].get("care_resolve", {}).get("care_resolve")
            debt_total = arrival_result["crdt"].get("meaning_debt", {}).get("total_meaning_debt", 0)
            health = arrival_result["crdt"].get("meaning_debt", {}).get("health_assessment", "?")

            q_time = time.time() - q_start

            result_entry = {
                "question_id": question["id"],
                "domain": question["domain"],
                "difficulty": question.get("difficulty", "graduate"),
                "correct_answer": question["correct"],
                "solo": majority_result["individual_answers"],
                "majority_vote": {
                    "answer": majority_result["majority_answer"],
                    "correct": majority_result["correct"],
                    "unanimous": majority_result["unanimous"],
                    "cost_usd": majority_result["cost_usd"],
                },
                "arrival": {
                    "answer": arrival_result["final_answer"],
                    "correct": arrival_result["correct"],
                    "atoms_used": arrival_result["atoms_used"],
                    "unique_atoms": arrival_result["unique_atoms"],
                    "emergent_atoms": arrival_result["emergent_atoms"],
                    "cost_usd": arrival_result["cost_usd"],
                    "total_tokens": arrival_result["total_tokens"],
                    "dialogue": arrival_result["dialogue"],
                },
                "crdt": arrival_result["crdt"],
                "question_time_s": round(q_time, 1),
                "timestamp": datetime.now().isoformat(),
            }

            all_results.append(result_entry)

            # Status line
            solo_answers = [s["answer"] for s in majority_result["individual_answers"]]
            solo_correct = sum(1 for s in majority_result["individual_answers"] if s["correct"])
            mv_sym = "✓" if majority_result["correct"] else "✗"
            ar_sym = "✓" if arrival_result["correct"] else "✗"
            care_str = f"{care_score:.2f}" if care_score is not None else "N/A"
            r1_uniq = len(set(solo_answers))

            print(f"Solo:{solo_correct}/5 MV:{mv_sym} AR:{ar_sym} "
                  f"R1uniq:{r1_uniq} CARE:{care_str} debt:{debt_total:.1f} [{health}] "
                  f"${self.total_cost:.3f} ({q_time:.0f}s)")

            self.logger.log_event(f"phase16_{question['id']}", result_entry)

        # ============================================================
        # Summary & Echo-Chamber Metrics
        # ============================================================
        summary = self._compute_summary(all_results)
        echo_metrics = compute_all_echo_chamber_metrics(all_results, phase13_accuracy=0.525)

        self._print_headline(summary, echo_metrics)

        # Save results
        results_dir = os.path.join(self.base_dir, "results")
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(results_dir, f"phase16_results_{timestamp}.json")

        output = {
            "experiment": "ARRIVAL CRDT - Phase 16: Homogeneous Ensemble (Echo-Chamber Test)",
            "started": self.start_time.isoformat(),
            "completed": datetime.now().isoformat(),
            "duration_minutes": round((datetime.now() - self.start_time).total_seconds() / 60, 1),
            "total_questions": len(self.questions),
            "total_api_calls": self.total_calls,
            "total_cost_usd": round(self.total_cost, 4),
            "model": GONKA_MODEL_ID,
            "agents": AGENT_NAMES,
            "parameters": {
                "temperature": PHASE16_TEMPERATURE,
                "max_tokens_dialogue": PHASE16_MAX_TOKENS,
                "max_tokens_solo": PHASE16_SOLO_MAX_TOKENS,
                "enable_thinking": PHASE16_ENABLE_THINKING,
                "dataset": "GPQA Diamond",
                "dataset_citation": "Rein et al. (2024) arXiv:2311.12022",
                "ensemble_type": "homogeneous (5 × same model, different personas)",
            },
            "summary": summary,
            "echo_chamber_metrics": echo_metrics,
            "results": all_results,
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        # Save full API log
        log_file = os.path.join(results_dir, f"phase16_api_log_{timestamp}.json")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.full_log, f, ensure_ascii=False, indent=2)

        print(f"\n  Results saved: {results_file}")
        print(f"  API log saved: {log_file} ({len(self.full_log)} calls)")
        print(f"  Total cost: ${self.total_cost:.4f}")
        print(f"  Duration: {datetime.now() - self.start_time}")
        print(f"{'='*70}")

        return results_file

    def _compute_summary(self, all_results: list) -> dict:
        """Compute comprehensive summary statistics."""
        summary = {}

        # Solo accuracy (per agent and average)
        solo_correct_total = 0
        solo_total = 0
        per_agent_solo = {name: {"correct": 0, "total": 0} for name in AGENT_NAMES}

        for r in all_results:
            for s in r["solo"]:
                agent = s.get("agent_name", "?")
                if agent in per_agent_solo:
                    per_agent_solo[agent]["total"] += 1
                    if s["correct"]:
                        per_agent_solo[agent]["correct"] += 1
                if s["correct"]:
                    solo_correct_total += 1
                solo_total += 1

        solo_acc = solo_correct_total / solo_total if solo_total > 0 else 0
        summary["solo"] = {
            "correct": solo_correct_total,
            "total": solo_total,
            "accuracy": round(solo_acc, 4),
            "per_agent": {
                name: {
                    **data,
                    "accuracy": round(data["correct"] / data["total"], 4) if data["total"] > 0 else 0,
                }
                for name, data in per_agent_solo.items()
            },
        }

        # MV accuracy
        mv_correct = sum(1 for r in all_results if r["majority_vote"]["correct"])
        mv_total = len(all_results)
        summary["majority_vote"] = {
            "correct": mv_correct,
            "total": mv_total,
            "accuracy": round(mv_correct / mv_total, 4) if mv_total > 0 else 0,
        }

        # ARRIVAL accuracy
        ar_correct = sum(1 for r in all_results if r["arrival"]["correct"])
        ar_total = len(all_results)
        ar_acc = ar_correct / ar_total if ar_total > 0 else 0
        summary["arrival"] = {
            "correct": ar_correct,
            "total": ar_total,
            "accuracy": round(ar_acc, 4),
        }

        # GAIN
        mv_acc = summary["majority_vote"]["accuracy"]
        summary["gain_vs_solo_pp"] = round((ar_acc - solo_acc) * 100, 1)
        summary["gain_vs_mv_pp"] = round((ar_acc - mv_acc) * 100, 1)

        # CRDT summary
        care_scores = []
        debt_scores = []
        health_counts = {"healthy": 0, "strained": 0, "unhealthy": 0}

        for r in all_results:
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

        summary["crdt"] = {
            "avg_care_resolve": round(sum(care_scores) / len(care_scores), 4) if care_scores else None,
            "avg_meaning_debt": round(sum(debt_scores) / len(debt_scores), 4) if debt_scores else None,
            "health_counts": health_counts,
        }

        # Per-domain
        domain_stats = {}
        for domain in DOMAINS:
            domain_results = [r for r in all_results if r["domain"] == domain]
            if not domain_results:
                continue
            d_solo = sum(1 for r in domain_results for s in r["solo"] if s["correct"])
            d_solo_total = sum(len(r["solo"]) for r in domain_results)
            d_mv = sum(1 for r in domain_results if r["majority_vote"]["correct"])
            d_ar = sum(1 for r in domain_results if r["arrival"]["correct"])
            d_total = len(domain_results)
            domain_stats[domain] = {
                "n_questions": d_total,
                "solo_accuracy": round(d_solo / d_solo_total, 4) if d_solo_total > 0 else 0,
                "mv_accuracy": round(d_mv / d_total, 4) if d_total > 0 else 0,
                "arrival_accuracy": round(d_ar / d_total, 4) if d_total > 0 else 0,
            }
        summary["per_domain"] = domain_stats

        # R1 unanimity quick stat
        unanimous_count = sum(1 for r in all_results if r["majority_vote"]["unanimous"])
        summary["r1_unanimity_rate"] = round(unanimous_count / len(all_results), 4) if all_results else 0

        return summary

    def _print_headline(self, summary: dict, echo_metrics: dict):
        """Print the headline report."""
        print(f"\n{'='*70}")
        print(f"  ╔══════════════════════════════════════════════════════════════╗")
        print(f"  ║  PHASE 16: HOMOGENEOUS ENSEMBLE — ECHO-CHAMBER REPORT      ║")
        print(f"  ╠══════════════════════════════════════════════════════════════╣")

        solo_acc = summary["solo"]["accuracy"] * 100
        mv_acc = summary["majority_vote"]["accuracy"] * 100
        ar_acc = summary["arrival"]["accuracy"] * 100

        print(f"  ║  Solo accuracy (avg):     {solo_acc:5.1f}%                           ║")
        print(f"  ║  Majority Vote:           {mv_acc:5.1f}%                           ║")
        print(f"  ║  ARRIVAL Protocol:        {ar_acc:5.1f}%                           ║")
        print(f"  ║  ─────────────────────────────────────────────────          ║")

        gain_s = summary["gain_vs_solo_pp"]
        gain_m = summary["gain_vs_mv_pp"]
        sign_s = "+" if gain_s >= 0 else ""
        sign_m = "+" if gain_m >= 0 else ""
        print(f"  ║  GAIN vs Solo:           {sign_s}{gain_s:5.1f} pp                      ║")
        print(f"  ║  GAIN vs MV:             {sign_m}{gain_m:5.1f} pp                      ║")

        care = summary["crdt"].get("avg_care_resolve")
        debt = summary["crdt"].get("avg_meaning_debt")
        care_str = f"{care:.3f}" if care is not None else "N/A"
        debt_str = f"{debt:.3f}" if debt is not None else "N/A"
        print(f"  ║  Avg CARE Resolve:        {care_str}                          ║")
        print(f"  ║  Avg Meaning Debt:        {debt_str}                          ║")
        print(f"  ║  Total cost:             ${self.total_cost:.4f}                         ║")
        print(f"  ╠══════════════════════════════════════════════════════════════╣")
        print(f"  ║  ECHO-CHAMBER METRICS                                      ║")
        print(f"  ╠══════════════════════════════════════════════════════════════╣")

        r1_ag = echo_metrics.get("r1_agreement", {}).get("r1_agreement_rate", 0) * 100
        ent = echo_metrics.get("answer_entropy", {}).get("normalized_entropy", 0) * 100
        flip = echo_metrics.get("flip_rate", {}).get("flip_rate", 0) * 100
        fc = echo_metrics.get("false_consensus", {}).get("false_consensus_rate", 0) * 100
        ms = echo_metrics.get("minority_suppression", {}).get("minority_suppression_rate", 0) * 100
        ci = echo_metrics.get("confidence_inflation", {}).get("confidence_inflation_ratio", 1.0)
        dt = echo_metrics.get("diversity_tax", {}).get("diversity_tax_pct", 0)

        print(f"  ║  R1 Unanimity Rate:       {r1_ag:5.1f}%                           ║")
        print(f"  ║  Answer Entropy (norm):   {ent:5.1f}%                           ║")
        print(f"  ║  R1→R2 Flip Rate:         {flip:5.1f}%                           ║")
        print(f"  ║  False Consensus Rate:    {fc:5.1f}%                           ║")
        print(f"  ║  Minority Suppression:    {ms:5.1f}%                           ║")
        ci_str = f"{ci:.2f}x" if ci != "inf" else "∞"
        print(f"  ║  Confidence Inflation:    {ci_str:>6}                           ║")
        print(f"  ║  Diversity Tax:           {dt:5.1f}%                           ║")
        print(f"  ╚══════════════════════════════════════════════════════════════╝")

        # Per-agent solo breakdown
        print(f"\n  Per-agent solo accuracy:")
        for name, data in summary["solo"]["per_agent"].items():
            acc = data["accuracy"] * 100
            print(f"    {name} ({self._get_persona_short(name)}): "
                  f"{data['correct']}/{data['total']} = {acc:.1f}%")

        # Per-domain
        print(f"\n  Per-domain breakdown:")
        for domain, ds in summary.get("per_domain", {}).items():
            print(f"    {domain}: Solo={ds['solo_accuracy']*100:.1f}% "
                  f"MV={ds['mv_accuracy']*100:.1f}% AR={ds['arrival_accuracy']*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Phase 16: Homogeneous Ensemble (Echo-Chamber)")
    parser.add_argument("--test", type=int, default=None, help="Number of questions for test run")
    parser.add_argument("--dry-run", action="store_true", help="Validate pipeline without API calls")
    parser.add_argument("--test-connectivity", action="store_true", help="Test Gonka API connection")
    args = parser.parse_args()

    if args.test_connectivity:
        print(f"\n  Testing Gonka Broker connectivity...")
        client = GonkaClient()
        success = client.test_connectivity()
        if success:
            print(f"  ✅ Gonka API is working!")
        else:
            print(f"  ❌ Gonka API connection failed!")
        return

    runner = Phase16Runner(
        n_questions=args.test,
        dry_run=args.dry_run,
    )
    results_file = runner.run_full_experiment()
    print(f"\nResults: {results_file}")


if __name__ == "__main__":
    main()
