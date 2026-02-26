# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
ARRIVAL Phase 13: Hard Benchmark — ARRIVAL vs Solo vs Majority Vote
GPQA Diamond (40 graduate-level questions in physics, chemistry, biology)

Goal: Measure real accuracy GAIN on hard questions where solo accuracy ~40-65%.
Conditions: Solo | Majority Vote | ARRIVAL Protocol (4-round dialogue) + CRDT overlay.

Usage:
    python run_phase13.py                  # Full run (40 questions × 2 trios)
    python run_phase13.py --test 3         # Test on 3 questions only
    python run_phase13.py --trio alpha     # Run only alpha trio
    python run_phase13.py --dry-run        # Validate pipeline without API calls
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime, timedelta
from collections import Counter

# Windows encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    MODEL_SHORT, MODEL_COSTS, KNOWN_ATOMS, SLEEP_BETWEEN_CALLS, MAX_COST_USD,
    PHASE13_TRIOS, PHASE13_TEMPERATURE, PHASE13_MAX_TOKENS, PHASE13_SOLO_MAX_TOKENS,
)
from openrouter_client import OpenRouterClient
from metrics import extract_answer_letter, find_all_atoms, detect_emergent_atoms
from crdt_metrics import compute_care_resolve, compute_meaning_debt
from enhanced_logger import EnhancedLogger
from phase_13.questions_gpqa import QUESTIONS, DOMAINS


# ============================================================
# System Prompts (aligned with Phase 5/7)
# ============================================================

SOLO_SYSTEM = """You are an expert answering a multiple-choice question.
Analyze the question carefully, reason step by step, then state your final answer.
End your response with a clear statement: "The answer is X" where X is A, B, C, or D."""

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
# Phase 13 Runner
# ============================================================

class Phase13Runner:
    def __init__(self, trios=None, n_questions=None, dry_run=False):
        self.dry_run = dry_run
        if not dry_run:
            self.client = OpenRouterClient()
        else:
            self.client = None

        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        self.logger = EnhancedLogger(log_dir, "phase_13_hard_benchmark")

        self.trios = trios or PHASE13_TRIOS
        self.questions = QUESTIONS[:n_questions] if n_questions else QUESTIONS
        self.total_cost = 0.0
        self.total_calls = 0
        self.start_time = datetime.now()

        # Full experiment log — every API call recorded
        self.full_log = []

    def _log_api_call(self, trio_name, question_id, condition, round_num, model, response_text, answer, cost, tokens, latency_ms):
        """Log every single API call for transparency."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "trio": trio_name,
            "question_id": question_id,
            "condition": condition,
            "round": round_num,
            "model": model,
            "model_short": MODEL_SHORT.get(model, model),
            "response_text": response_text,
            "extracted_answer": answer,
            "cost_usd": cost,
            "tokens": tokens,
            "latency_ms": latency_ms,
        }
        self.full_log.append(entry)
        return entry

    def run_solo(self, model: str, question: dict, trio_name: str) -> dict:
        """Single model answers independently."""
        if self.dry_run:
            return {
                "model": model,
                "model_short": MODEL_SHORT.get(model, model),
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
            model=model,
            system_prompt=SOLO_SYSTEM,
            temperature=PHASE13_TEMPERATURE,
            max_tokens=PHASE13_SOLO_MAX_TOKENS,
        )

        self.total_cost += response.cost_usd
        self.total_calls += 1
        answer = extract_answer_letter(response.text)

        self._log_api_call(
            trio_name, question["id"], "solo", 0, model,
            response.text, answer, response.cost_usd,
            response.prompt_tokens + response.completion_tokens,
            response.latency_ms,
        )

        return {
            "model": model,
            "model_short": MODEL_SHORT.get(model, model),
            "answer": answer,
            "correct": answer == question["correct"] if answer else False,
            "response_text": response.text,
            "cost_usd": response.cost_usd,
            "tokens": response.prompt_tokens + response.completion_tokens,
            "latency_ms": response.latency_ms,
        }

    def run_majority_vote(self, trio: list, question: dict, trio_name: str) -> dict:
        """Three models answer independently, majority wins."""
        solo_results = []
        for model in trio:
            result = self.run_solo(model, question, trio_name)
            solo_results.append(result)
            if not self.dry_run:
                time.sleep(SLEEP_BETWEEN_CALLS)

        answers = [r["answer"] for r in solo_results if r["answer"]]
        if not answers:
            majority_answer = None
        else:
            vote_counts = Counter(answers)
            majority_answer = vote_counts.most_common(1)[0][0]

        total_cost = sum(r["cost_usd"] for r in solo_results)

        return {
            "condition": "majority_vote",
            "trio": [MODEL_SHORT.get(m, m) for m in trio],
            "individual_answers": [
                {
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

    def run_arrival_with_crdt(self, trio: list, question: dict, trio_name: str) -> dict:
        """4-round ARRIVAL Protocol + post-hoc CRDT metrics."""
        if self.dry_run:
            return {
                "condition": "arrival_crdt",
                "trio": [MODEL_SHORT.get(m, m) for m in trio],
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

        # Round 1: Model A proposes
        model_a = trio[0]
        prompt_1 = ARRIVAL_ROUND_PROMPTS[1].format(
            node_name="Alpha",
            model_short=MODEL_SHORT.get(model_a, model_a),
            **choice_vars
        )
        resp_1 = self.client.generate(
            prompt=prompt_1, model=model_a,
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE13_TEMPERATURE,
            max_tokens=PHASE13_MAX_TOKENS,
        )
        responses["r1"] = resp_1.text
        total_cost += resp_1.cost_usd
        total_tokens += resp_1.prompt_tokens + resp_1.completion_tokens
        self.total_cost += resp_1.cost_usd
        self.total_calls += 1
        dialogue.append({"round": 1, "from": MODEL_SHORT.get(model_a, model_a), "message": resp_1.text})
        all_atoms.extend(find_all_atoms(resp_1.text))
        emergent.update(detect_emergent_atoms(resp_1.text))
        self._log_api_call(trio_name, q["id"], "arrival", 1, model_a, resp_1.text,
                          extract_answer_letter(resp_1.text), resp_1.cost_usd,
                          resp_1.prompt_tokens + resp_1.completion_tokens, resp_1.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 2: Model B responds
        model_b = trio[1]
        prompt_2 = ARRIVAL_ROUND_PROMPTS[2].format(
            node_name="Beta",
            model_short=MODEL_SHORT.get(model_b, model_b),
            previous_response=resp_1.text[:1500],
            **choice_vars
        )
        resp_2 = self.client.generate(
            prompt=prompt_2, model=model_b,
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE13_TEMPERATURE,
            max_tokens=PHASE13_MAX_TOKENS,
        )
        responses["r2"] = resp_2.text
        total_cost += resp_2.cost_usd
        total_tokens += resp_2.prompt_tokens + resp_2.completion_tokens
        self.total_cost += resp_2.cost_usd
        self.total_calls += 1
        dialogue.append({"round": 2, "from": MODEL_SHORT.get(model_b, model_b), "message": resp_2.text})
        all_atoms.extend(find_all_atoms(resp_2.text))
        emergent.update(detect_emergent_atoms(resp_2.text))
        self._log_api_call(trio_name, q["id"], "arrival", 2, model_b, resp_2.text,
                          extract_answer_letter(resp_2.text), resp_2.cost_usd,
                          resp_2.prompt_tokens + resp_2.completion_tokens, resp_2.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 3: Model C synthesizes
        model_c = trio[2]
        prompt_3 = ARRIVAL_ROUND_PROMPTS[3].format(
            node_name="Gamma",
            model_short=MODEL_SHORT.get(model_c, model_c),
            response_1=resp_1.text[:1200],
            response_2=resp_2.text[:1200],
            **choice_vars
        )
        resp_3 = self.client.generate(
            prompt=prompt_3, model=model_c,
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE13_TEMPERATURE,
            max_tokens=PHASE13_MAX_TOKENS,
        )
        responses["r3"] = resp_3.text
        total_cost += resp_3.cost_usd
        total_tokens += resp_3.prompt_tokens + resp_3.completion_tokens
        self.total_cost += resp_3.cost_usd
        self.total_calls += 1
        dialogue.append({"round": 3, "from": MODEL_SHORT.get(model_c, model_c), "message": resp_3.text})
        all_atoms.extend(find_all_atoms(resp_3.text))
        emergent.update(detect_emergent_atoms(resp_3.text))
        self._log_api_call(trio_name, q["id"], "arrival", 3, model_c, resp_3.text,
                          extract_answer_letter(resp_3.text), resp_3.cost_usd,
                          resp_3.prompt_tokens + resp_3.completion_tokens, resp_3.latency_ms)
        time.sleep(SLEEP_BETWEEN_CALLS)

        # Round 4: Model A finalizes
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
            system_prompt=ARRIVAL_SYSTEM,
            temperature=PHASE13_TEMPERATURE,
            max_tokens=PHASE13_MAX_TOKENS,
        )
        responses["r4"] = resp_4.text
        total_cost += resp_4.cost_usd
        total_tokens += resp_4.prompt_tokens + resp_4.completion_tokens
        self.total_cost += resp_4.cost_usd
        self.total_calls += 1
        dialogue.append({"round": 4, "from": MODEL_SHORT.get(model_a, model_a), "message": resp_4.text})
        all_atoms.extend(find_all_atoms(resp_4.text))
        emergent.update(detect_emergent_atoms(resp_4.text))
        self._log_api_call(trio_name, q["id"], "arrival", 4, model_a, resp_4.text,
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
            "condition": "arrival_crdt",
            "trio": [MODEL_SHORT.get(m, m) for m in trio],
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

    def run_full_experiment(self):
        """Run all conditions for all questions across all trios."""
        print(f"\n{'='*70}")
        print(f"  ARRIVAL CRDT - Phase 13: Hard Benchmark (GPQA Diamond)")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Questions: {len(self.questions)} (GPQA Diamond graduate-level)")
        print(f"  Trios: {list(self.trios.keys())}")
        print(f"  Budget: ${MAX_COST_USD}")
        if self.dry_run:
            print(f"  MODE: DRY RUN (no API calls)")
        print(f"{'='*70}\n")

        # Estimate time
        n_calls = len(self.questions) * len(self.trios) * 7  # 3 solo + 4 arrival
        est_seconds = n_calls * (SLEEP_BETWEEN_CALLS + 3)  # ~3s per API call + sleep
        est_minutes = est_seconds / 60
        print(f"  Estimated: ~{n_calls} API calls, ~{est_minutes:.0f} minutes\n")

        all_trio_results = {}

        for trio_name, trio_models in self.trios.items():
            trio_short = [MODEL_SHORT.get(m, m) for m in trio_models]
            print(f"\n{'─'*70}")
            print(f"  TRIO: {trio_name} = {' + '.join(trio_short)}")
            print(f"{'─'*70}")

            trio_results = []

            for i, question in enumerate(self.questions):
                # Budget check
                if self.total_cost >= MAX_COST_USD * 0.95:
                    print(f"\n  !!! BUDGET WARNING: ${self.total_cost:.2f} / ${MAX_COST_USD} — stopping !!!")
                    break

                q_start = time.time()
                domain_tag = question["domain"][:4].upper()
                print(f"  Q{i+1:02d}/{len(self.questions)} [{domain_tag}] {question['id']}...", end=" ", flush=True)

                # Condition 1: Majority Vote (includes solo)
                majority_result = self.run_majority_vote(trio_models, question, trio_name)

                # Condition 2: ARRIVAL + CRDT
                arrival_result = self.run_arrival_with_crdt(trio_models, question, trio_name)

                # CRDT summary
                care_score = arrival_result["crdt"].get("care_resolve", {}).get("care_resolve")
                debt_total = arrival_result["crdt"].get("meaning_debt", {}).get("total_meaning_debt", 0)
                health = arrival_result["crdt"].get("meaning_debt", {}).get("health_assessment", "?")

                q_time = time.time() - q_start

                result_entry = {
                    "question_id": question["id"],
                    "domain": question["domain"],
                    "difficulty": question["difficulty"],
                    "correct_answer": question["correct"],
                    "trio_name": trio_name,
                    "trio": trio_short,
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

                trio_results.append(result_entry)

                # Status line
                solo_answers = [s["answer"] for s in majority_result["individual_answers"]]
                solo_correct = sum(1 for s in majority_result["individual_answers"] if s["correct"])
                mv_sym = "✓" if majority_result["correct"] else "✗"
                ar_sym = "✓" if arrival_result["correct"] else "✗"
                care_str = f"{care_score:.2f}" if care_score is not None else "N/A"
                print(f"Solo:{solo_correct}/3 MV:{mv_sym} AR:{ar_sym} "
                      f"CARE:{care_str} debt:{debt_total:.1f} [{health}] "
                      f"${self.total_cost:.3f} ({q_time:.0f}s)")

                self.logger.log_event(f"{trio_name}_{question['id']}", result_entry)

            all_trio_results[trio_name] = trio_results

        # ============================================================
        # Compute summary and save
        # ============================================================
        summary = self._compute_summary(all_trio_results)
        self._print_headline(summary)

        # Save results
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "phase_13"
        )
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(results_dir, f"phase13_results_{timestamp}.json")

        output = {
            "experiment": "ARRIVAL CRDT - Phase 13: Hard Benchmark (GPQA Diamond)",
            "started": self.start_time.isoformat(),
            "completed": datetime.now().isoformat(),
            "duration_minutes": round((datetime.now() - self.start_time).total_seconds() / 60, 1),
            "total_questions": len(self.questions),
            "total_api_calls": self.total_calls,
            "total_cost_usd": round(self.total_cost, 4),
            "trios": {name: [MODEL_SHORT.get(m, m) for m in models] for name, models in self.trios.items()},
            "parameters": {
                "temperature": PHASE13_TEMPERATURE,
                "max_tokens_dialogue": PHASE13_MAX_TOKENS,
                "max_tokens_solo": PHASE13_SOLO_MAX_TOKENS,
                "dataset": "GPQA Diamond",
                "dataset_citation": "Rein et al. (2024) arXiv:2311.12022",
            },
            "summary": summary,
            "results": all_trio_results,
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        # Save full API log separately for transparency
        log_file = os.path.join(results_dir, f"phase13_api_log_{timestamp}.json")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.full_log, f, ensure_ascii=False, indent=2)

        print(f"\n  Results saved: {results_file}")
        print(f"  API log saved: {log_file} ({len(self.full_log)} calls)")
        print(f"  Total cost: ${self.total_cost:.4f}")
        print(f"  Duration: {datetime.now() - self.start_time}")
        print(f"{'='*70}")

        return results_file

    def _compute_summary(self, all_trio_results: dict) -> dict:
        """Compute comprehensive summary statistics."""
        summary = {"per_trio": {}, "overall": {}}

        # Flatten all results
        all_results = []
        for trio_name, results in all_trio_results.items():
            all_results.extend(results)

        # Per-trio statistics
        for trio_name, results in all_trio_results.items():
            trio_summary = {}

            # Solo accuracy (per model and average)
            solo_correct_total = 0
            solo_total = 0
            for r in results:
                for s in r["solo"]:
                    if s["correct"]:
                        solo_correct_total += 1
                    solo_total += 1
            trio_summary["solo"] = {
                "correct": solo_correct_total,
                "total": solo_total,
                "accuracy": round(solo_correct_total / solo_total, 4) if solo_total > 0 else 0,
            }

            # MV accuracy
            mv_correct = sum(1 for r in results if r["majority_vote"]["correct"])
            mv_total = len(results)
            trio_summary["majority_vote"] = {
                "correct": mv_correct,
                "total": mv_total,
                "accuracy": round(mv_correct / mv_total, 4) if mv_total > 0 else 0,
            }

            # ARRIVAL accuracy
            ar_correct = sum(1 for r in results if r["arrival"]["correct"])
            ar_total = len(results)
            trio_summary["arrival"] = {
                "correct": ar_correct,
                "total": ar_total,
                "accuracy": round(ar_correct / ar_total, 4) if ar_total > 0 else 0,
            }

            # GAIN
            solo_acc = trio_summary["solo"]["accuracy"]
            mv_acc = trio_summary["majority_vote"]["accuracy"]
            ar_acc = trio_summary["arrival"]["accuracy"]
            trio_summary["gain_vs_solo_pp"] = round((ar_acc - solo_acc) * 100, 1)
            trio_summary["gain_vs_mv_pp"] = round((ar_acc - mv_acc) * 100, 1)

            # CRDT summary
            care_scores = []
            debt_scores = []
            health_counts = {"healthy": 0, "strained": 0, "unhealthy": 0}
            for r in results:
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

            trio_summary["crdt"] = {
                "avg_care_resolve": round(sum(care_scores) / len(care_scores), 4) if care_scores else None,
                "avg_meaning_debt": round(sum(debt_scores) / len(debt_scores), 4) if debt_scores else None,
                "health_counts": health_counts,
            }

            # Per-domain breakdown
            domain_stats = {}
            for domain in DOMAINS:
                domain_results = [r for r in results if r["domain"] == domain]
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
            trio_summary["per_domain"] = domain_stats

            summary["per_trio"][trio_name] = trio_summary

        # Overall statistics (across all trios)
        total_solo_correct = sum(s["per_trio"][t]["solo"]["correct"] for t, s in [(t, summary) for t in summary["per_trio"]])
        total_solo = sum(s["per_trio"][t]["solo"]["total"] for t, s in [(t, summary) for t in summary["per_trio"]])
        total_mv_correct = sum(summary["per_trio"][t]["majority_vote"]["correct"] for t in summary["per_trio"])
        total_mv = sum(summary["per_trio"][t]["majority_vote"]["total"] for t in summary["per_trio"])
        total_ar_correct = sum(summary["per_trio"][t]["arrival"]["correct"] for t in summary["per_trio"])
        total_ar = sum(summary["per_trio"][t]["arrival"]["total"] for t in summary["per_trio"])

        solo_acc = round(total_solo_correct / total_solo, 4) if total_solo > 0 else 0
        mv_acc = round(total_mv_correct / total_mv, 4) if total_mv > 0 else 0
        ar_acc = round(total_ar_correct / total_ar, 4) if total_ar > 0 else 0

        summary["overall"] = {
            "solo_accuracy": solo_acc,
            "mv_accuracy": mv_acc,
            "arrival_accuracy": ar_acc,
            "gain_vs_solo_pp": round((ar_acc - solo_acc) * 100, 1),
            "gain_vs_mv_pp": round((ar_acc - mv_acc) * 100, 1),
            "total_questions": len(self.questions),
            "total_trios": len(self.trios),
            "total_cost_usd": round(self.total_cost, 4),
        }

        # McNemar's test (MV vs ARRIVAL)
        try:
            # Build contingency: both right, MV right AR wrong, MV wrong AR right, both wrong
            b = 0  # MV correct, AR wrong
            c = 0  # MV wrong, AR correct
            for results in all_trio_results.values():
                for r in results:
                    mv_ok = r["majority_vote"]["correct"]
                    ar_ok = r["arrival"]["correct"]
                    if mv_ok and not ar_ok:
                        b += 1
                    elif not mv_ok and ar_ok:
                        c += 1
            # McNemar chi-squared (with continuity correction)
            if b + c > 0:
                chi2 = (abs(b - c) - 1) ** 2 / (b + c)
                # Simple p-value approximation
                import math
                p_value = 1 - 0.5 * (1 + math.erf(math.sqrt(chi2 / 2)))
                # More accurate: use chi2 with 1 df
                # p ≈ exp(-chi2/2) for rough estimate
                p_value = math.exp(-chi2 / 2) if chi2 > 0 else 1.0
            else:
                chi2 = 0
                p_value = 1.0
            summary["overall"]["mcnemar_b_mv_right_ar_wrong"] = b
            summary["overall"]["mcnemar_c_mv_wrong_ar_right"] = c
            summary["overall"]["mcnemar_chi2"] = round(chi2, 4)
            summary["overall"]["mcnemar_p_approx"] = round(p_value, 4)
        except Exception as e:
            summary["overall"]["mcnemar_error"] = str(e)

        return summary

    def _print_headline(self, summary: dict):
        """Print the headline GAIN report."""
        ov = summary["overall"]
        print(f"\n{'='*70}")
        print(f"  ╔══════════════════════════════════════════════════════════╗")
        print(f"  ║  ARRIVAL GAIN REPORT — Phase 13 (GPQA Diamond)         ║")
        print(f"  ╠══════════════════════════════════════════════════════════╣")
        print(f"  ║  Solo accuracy:         {ov['solo_accuracy']*100:5.1f}%                         ║")
        print(f"  ║  Majority Vote:         {ov['mv_accuracy']*100:5.1f}%                         ║")
        print(f"  ║  ARRIVAL Protocol:      {ov['arrival_accuracy']*100:5.1f}%                         ║")
        print(f"  ║  ──────────────────────────────────────────────         ║")
        gain_solo = ov['gain_vs_solo_pp']
        gain_mv = ov['gain_vs_mv_pp']
        sign_s = "+" if gain_solo >= 0 else ""
        sign_m = "+" if gain_mv >= 0 else ""
        print(f"  ║  GAIN vs Solo:         {sign_s}{gain_solo:5.1f} pp                        ║")
        print(f"  ║  GAIN vs MV:           {sign_m}{gain_mv:5.1f} pp                        ║")
        if "mcnemar_p_approx" in ov:
            print(f"  ║  McNemar p-value:       {ov['mcnemar_p_approx']:.4f}                       ║")
        print(f"  ║  Total cost:           ${ov['total_cost_usd']:.4f}                        ║")
        print(f"  ╚══════════════════════════════════════════════════════════╝")

        # Per-trio breakdown
        print(f"\n  Per-trio breakdown:")
        for trio_name, ts in summary["per_trio"].items():
            print(f"    {trio_name}: Solo={ts['solo']['accuracy']*100:.1f}% "
                  f"MV={ts['majority_vote']['accuracy']*100:.1f}% "
                  f"AR={ts['arrival']['accuracy']*100:.1f}% "
                  f"(GAIN: {ts['gain_vs_solo_pp']:+.1f}pp vs solo, "
                  f"{ts['gain_vs_mv_pp']:+.1f}pp vs MV)")

        # Per-domain
        print(f"\n  Per-domain breakdown (across all trios):")
        for trio_name, ts in summary["per_trio"].items():
            for domain, ds in ts.get("per_domain", {}).items():
                print(f"    [{trio_name}] {domain}: Solo={ds['solo_accuracy']*100:.1f}% "
                      f"MV={ds['mv_accuracy']*100:.1f}% AR={ds['arrival_accuracy']*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Phase 13: Hard Benchmark (GPQA Diamond)")
    parser.add_argument("--test", type=int, default=None, help="Number of questions for test run")
    parser.add_argument("--trio", type=str, default=None, help="Run only specific trio (alpha/beta)")
    parser.add_argument("--dry-run", action="store_true", help="Validate pipeline without API calls")
    args = parser.parse_args()

    trios = PHASE13_TRIOS
    if args.trio:
        if args.trio not in PHASE13_TRIOS:
            print(f"Unknown trio: {args.trio}. Available: {list(PHASE13_TRIOS.keys())}")
            sys.exit(1)
        trios = {args.trio: PHASE13_TRIOS[args.trio]}

    runner = Phase13Runner(
        trios=trios,
        n_questions=args.test,
        dry_run=args.dry_run,
    )
    results_file = runner.run_full_experiment()
    print(f"\nResults: {results_file}")


if __name__ == "__main__":
    main()
