# PoC: Compare token usage WITH and WITHOUT token limits
# Purpose: Verify whether our $2.73 cost was "artificially low" due to token limits
#
# Test: 5 questions × 1 trio (beta) × 7 calls = 35 API calls
# Condition A: max_tokens=512/1024 (Phase 13 original)
# Condition B: max_tokens=4096/4096 (no practical limit)

import sys
import os
import json
import time
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API key must be set in environment before running:
# export OPENROUTER_API_KEY="sk-or-v1-..."
assert os.environ.get("OPENROUTER_API_KEY"), "Set OPENROUTER_API_KEY env var before running"

from config import (
    MODEL_SHORT, MODEL_COSTS, KNOWN_ATOMS, SLEEP_BETWEEN_CALLS,
    PHASE13_TRIOS, PHASE13_TEMPERATURE,
)
from openrouter_client import OpenRouterClient
from metrics import extract_answer_letter
from phase_13.questions_gpqa import QUESTIONS

# Use only beta trio and first 5 questions
TRIO = PHASE13_TRIOS["beta"]
QUESTIONS_SUBSET = QUESTIONS[:3]

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

# Count system prompt tokens (rough: 1 token ~ 4 chars)
SOLO_SYS_CHARS = len(SOLO_SYSTEM)
ARRIVAL_SYS_CHARS = len(ARRIVAL_SYSTEM)
print(f"System prompt sizes:")
print(f"  SOLO:    {SOLO_SYS_CHARS} chars ~ {SOLO_SYS_CHARS//4} tokens")
print(f"  ARRIVAL: {ARRIVAL_SYS_CHARS} chars ~ {ARRIVAL_SYS_CHARS//4} tokens")
print()


def run_condition(label, solo_max, dialogue_max):
    """Run 5 questions with given token limits."""
    client = OpenRouterClient()
    results = []
    total_cost = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_calls = 0

    print(f"\n{'='*60}")
    print(f"  CONDITION: {label}")
    print(f"  solo_max_tokens={solo_max}, dialogue_max_tokens={dialogue_max}")
    print(f"{'='*60}")

    for i, q in enumerate(QUESTIONS_SUBSET):
        q_start = time.time()
        choice_vars = {
            "question": q["question"],
            "choice_a": q["choices"]["A"],
            "choice_b": q["choices"]["B"],
            "choice_c": q["choices"]["C"],
            "choice_d": q["choices"]["D"],
        }
        q_prompt_tokens = 0
        q_completion_tokens = 0
        q_cost = 0.0

        # --- 3 Solo calls ---
        for model in TRIO:
            solo_prompt = f"""Question: {q['question']}

A) {q['choices']['A']}
B) {q['choices']['B']}
C) {q['choices']['C']}
D) {q['choices']['D']}

Analyze step by step and give your final answer."""

            resp = client.generate(
                prompt=solo_prompt, model=model,
                system_prompt=SOLO_SYSTEM,
                temperature=PHASE13_TEMPERATURE,
                max_tokens=solo_max,
            )
            q_prompt_tokens += resp.prompt_tokens
            q_completion_tokens += resp.completion_tokens
            q_cost += resp.cost_usd
            total_calls += 1
            time.sleep(SLEEP_BETWEEN_CALLS)

        # --- 4 ARRIVAL rounds (simplified: just R1-R4) ---
        prev_responses = []
        for round_num in range(1, 5):
            model = TRIO[(round_num - 1) % 3]

            if round_num == 1:
                prompt = f"""You are Node Alpha ({MODEL_SHORT.get(model, model)}).
Question: {q['question']}

Choices:
A) {q['choices']['A']}
B) {q['choices']['B']}
C) {q['choices']['C']}
D) {q['choices']['D']}

Analyze this question using DEUS protocol atoms. State your reasoning and initial answer.
Use @SELF to identify, @GOAL for the task, @INT for your reasoning, @C[value] for confidence."""
            elif round_num == 2:
                prompt = f"""You are Node Beta ({MODEL_SHORT.get(model, model)}).
The previous node analyzed this question:

{prev_responses[-1][:2000]}

Question: {q['question']}

Choices:
A) {q['choices']['A']}
B) {q['choices']['B']}
C) {q['choices']['C']}
D) {q['choices']['D']}

Review their analysis. Do you agree or disagree? Use @CONSENSUS or @CONFLICT atoms.
State your answer clearly. Use @C[value] for your confidence level."""
            elif round_num == 3:
                prompt = f"""You are Node Gamma ({MODEL_SHORT.get(model, model)}).
Two nodes have analyzed this question:

Node 1: {prev_responses[0][:1500]}

Node 2: {prev_responses[1][:1500]}

Question: {q['question']}

Choices:
A) {q['choices']['A']}
B) {q['choices']['B']}
C) {q['choices']['C']}
D) {q['choices']['D']}

Synthesize both perspectives. Propose the final answer with @RESOLUTION."""
            else:
                prompt = f"""You are Node Alpha ({MODEL_SHORT.get(model, model)}).
Three analyses have been provided:

Node 1: {prev_responses[0][:1000]}
Node 2: {prev_responses[1][:1000]}
Node 3: {prev_responses[2][:1000]}

Question: {q['question']}

Choices:
A) {q['choices']['A']}
B) {q['choices']['B']}
C) {q['choices']['C']}
D) {q['choices']['D']}

This is the final round. State the group's consensus answer.
Use @CONSENSUS[answer=X] where X is A, B, C, or D."""

            resp = client.generate(
                prompt=prompt, model=model,
                system_prompt=ARRIVAL_SYSTEM,
                temperature=PHASE13_TEMPERATURE,
                max_tokens=dialogue_max,
            )
            prev_responses.append(resp.text)
            q_prompt_tokens += resp.prompt_tokens
            q_completion_tokens += resp.completion_tokens
            q_cost += resp.cost_usd
            total_calls += 1
            time.sleep(SLEEP_BETWEEN_CALLS)

        total_cost += q_cost
        total_prompt_tokens += q_prompt_tokens
        total_completion_tokens += q_completion_tokens

        q_time = time.time() - q_start
        print(f"  Q{i+1}: prompt={q_prompt_tokens:,} compl={q_completion_tokens:,} "
              f"total={q_prompt_tokens+q_completion_tokens:,} cost=${q_cost:.4f} ({q_time:.0f}s)")

        results.append({
            "question": q["id"],
            "prompt_tokens": q_prompt_tokens,
            "completion_tokens": q_completion_tokens,
            "total_tokens": q_prompt_tokens + q_completion_tokens,
            "cost_usd": q_cost,
        })

    avg_prompt = total_prompt_tokens / len(QUESTIONS_SUBSET)
    avg_compl = total_completion_tokens / len(QUESTIONS_SUBSET)
    avg_cost = total_cost / len(QUESTIONS_SUBSET)

    print(f"\n  SUMMARY ({label}):")
    print(f"    Total prompt tokens:     {total_prompt_tokens:,}")
    print(f"    Total completion tokens:  {total_completion_tokens:,}")
    print(f"    Total tokens:            {total_prompt_tokens + total_completion_tokens:,}")
    print(f"    Total cost:              ${total_cost:.4f}")
    print(f"    Avg tokens/question:     {(total_prompt_tokens + total_completion_tokens) / len(QUESTIONS_SUBSET):,.0f}")
    print(f"    Avg cost/question:       ${avg_cost:.4f}")
    print(f"    Avg completion/question: {avg_compl:,.0f}")
    print(f"    API calls:               {total_calls}")

    # System prompt overhead calculation
    # 3 solo calls use SOLO_SYSTEM, 4 arrival calls use ARRIVAL_SYSTEM per question
    solo_sys_tokens = SOLO_SYS_CHARS // 4  # rough estimate
    arrival_sys_tokens = ARRIVAL_SYS_CHARS // 4
    sys_overhead_per_q = 3 * solo_sys_tokens + 4 * arrival_sys_tokens
    total_sys_overhead = sys_overhead_per_q * len(QUESTIONS_SUBSET)
    pct = total_sys_overhead / total_prompt_tokens * 100 if total_prompt_tokens > 0 else 0

    print(f"\n    System prompt overhead:")
    print(f"      Per question:  ~{sys_overhead_per_q} tokens")
    print(f"      Total:         ~{total_sys_overhead} tokens")
    print(f"      % of prompts:  ~{pct:.1f}%")

    return {
        "label": label,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_cost": total_cost,
        "per_question": results,
        "calls": total_calls,
    }


def main():
    print("="*60)
    print("  PoC: Token Limit Impact on ARRIVAL Cost")
    print(f"  {len(QUESTIONS_SUBSET)} questions x 1 trio (beta) x 2 conditions")
    print("="*60)

    # Condition A: Original Phase 13 limits
    result_limited = run_condition("LIMITED (Phase 13 original)",
                                   solo_max=512, dialogue_max=1024)

    print("\n" + "="*60)
    print("  Waiting 10s before unlimited condition...")
    print("="*60)
    time.sleep(10)

    # Condition B: No practical limit
    result_unlimited = run_condition("UNLIMITED (max_tokens=4096)",
                                     solo_max=4096, dialogue_max=4096)

    # ============================================================
    # COMPARISON
    # ============================================================
    print("\n" + "="*60)
    print("  COMPARISON: LIMITED vs UNLIMITED")
    print("="*60)

    lim = result_limited
    unlim = result_unlimited

    print(f"\n  {'Metric':<30} {'LIMITED':>12} {'UNLIMITED':>12} {'Ratio':>8}")
    print(f"  {'-'*62}")
    print(f"  {'Prompt tokens':<30} {lim['total_prompt_tokens']:>12,} {unlim['total_prompt_tokens']:>12,} {unlim['total_prompt_tokens']/max(lim['total_prompt_tokens'],1):>7.2f}x")
    print(f"  {'Completion tokens':<30} {lim['total_completion_tokens']:>12,} {unlim['total_completion_tokens']:>12,} {unlim['total_completion_tokens']/max(lim['total_completion_tokens'],1):>7.2f}x")
    total_lim = lim['total_prompt_tokens'] + lim['total_completion_tokens']
    total_unlim = unlim['total_prompt_tokens'] + unlim['total_completion_tokens']
    print(f"  {'Total tokens':<30} {total_lim:>12,} {total_unlim:>12,} {total_unlim/max(total_lim,1):>7.2f}x")
    print(f"  {'Total cost':<30} ${lim['total_cost']:>11.4f} ${unlim['total_cost']:>11.4f} {unlim['total_cost']/max(lim['total_cost'],0.001):>7.2f}x")

    # Extrapolate to 40 questions
    lim_40 = lim['total_cost'] / len(QUESTIONS_SUBSET) * 40 * 2  # x2 for both trios
    unlim_40 = unlim['total_cost'] / len(QUESTIONS_SUBSET) * 40 * 2
    print(f"\n  Extrapolated to full Phase 13 (40q x 2 trios):")
    print(f"    LIMITED:   ${lim_40:.2f}")
    print(f"    UNLIMITED: ${unlim_40:.2f}")
    print(f"    Difference: ${unlim_40 - lim_40:.2f} ({(unlim_40/max(lim_40,0.001)-1)*100:.0f}% more)")

    # System prompt % of total
    solo_sys = SOLO_SYS_CHARS // 4
    arrival_sys = ARRIVAL_SYS_CHARS // 4
    sys_per_q = 3 * solo_sys + 4 * arrival_sys
    sys_total = sys_per_q * len(QUESTIONS_SUBSET)

    print(f"\n  System prompt overhead as % of prompt tokens:")
    print(f"    LIMITED:   {sys_total/max(lim['total_prompt_tokens'],1)*100:.1f}%")
    print(f"    UNLIMITED: {sys_total/max(unlim['total_prompt_tokens'],1)*100:.1f}%")

    print(f"\n  CONCLUSION:")
    ratio = unlim['total_cost'] / max(lim['total_cost'], 0.001)
    if ratio < 1.3:
        print(f"    Token limits had MINIMAL impact ({ratio:.2f}x). Models naturally stop early.")
        print(f"    The critic's argument about 'artificially low cost' is NOT supported.")
    elif ratio < 2.0:
        print(f"    Token limits had MODERATE impact ({ratio:.2f}x). Cost increases but remains low.")
        print(f"    System prompt overhead is still a small fraction of total.")
    else:
        print(f"    Token limits had SIGNIFICANT impact ({ratio:.2f}x). Cost roughly doubles+.")
        print(f"    However, check if accuracy changed — longer != better.")

    # Save results
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results", "phase_13"
    )
    out = {
        "experiment": "PoC: Token limit impact",
        "timestamp": datetime.now().isoformat(),
        "questions": len(QUESTIONS_SUBSET),
        "limited": result_limited,
        "unlimited": result_unlimited,
        "comparison": {
            "cost_ratio": ratio,
            "token_ratio": total_unlim / max(total_lim, 1),
            "extrapolated_limited_40q": lim_40,
            "extrapolated_unlimited_40q": unlim_40,
        }
    }
    outfile = os.path.join(results_dir, f"poc_token_limit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(outfile, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Results saved: {outfile}")


if __name__ == "__main__":
    main()
