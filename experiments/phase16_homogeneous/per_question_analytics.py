# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2026 Mefodiy Kelevra
# AGPL-3.0-or-later

"""
Phase 16: Per-Question Detailed Analytics
Generates a human-readable report for every question in the experiment.

Usage:
    python per_question_analytics.py [results_file.json]
"""

import sys
import os
import json
import math

# Fix Windows encoding
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_results(path=None):
    if path:
        f = path
    else:
        import glob
        p16_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        files = sorted(glob.glob(os.path.join(p16_dir, "phase16_results_*.json")))
        if not files:
            print("No results found.")
            sys.exit(1)
        f = files[-1]
    print(f"Loading: {f}")
    with open(f, "r", encoding="utf-8") as fh:
        return json.load(fh)


def entropy_bits(answers):
    """Shannon entropy of answer distribution."""
    from collections import Counter
    c = Counter(a for a in answers if a)
    n = sum(c.values())
    if n == 0:
        return 0.0
    return -sum((cnt / n) * math.log2(cnt / n) for cnt in c.values() if cnt > 0)


def answer_distribution(answers):
    """Return dict of answer -> count."""
    from collections import Counter
    return dict(Counter(a for a in answers if a))


def analyze_question(q, idx):
    """Analyze a single question and return formatted string."""
    lines = []
    qid = q["question_id"]
    domain = q["domain"]
    correct = q["correct_answer"]

    lines.append(f"{'='*72}")
    lines.append(f"  Q{idx+1:02d} | {qid} | Domain: {domain} | Correct: {correct}")
    lines.append(f"{'='*72}")

    # --- SOLO ---
    solo_answers = []
    solo_details = []
    for s in q["solo"]:
        agent = s["agent_name"]
        ans = s["answer"] or "?"
        ok = s["correct"]
        solo_answers.append(ans)
        mark = "OK" if ok else "XX"
        solo_details.append(f"    {agent:<10} -> {ans}  [{mark}]")

    solo_correct_count = sum(1 for s in q["solo"] if s["correct"])
    lines.append(f"\n  SOLO ({solo_correct_count}/5 correct):")
    lines.extend(solo_details)

    dist = answer_distribution(solo_answers)
    dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(dist.items(), key=lambda x: -x[1]))
    lines.append(f"    Distribution: {dist_str}")
    lines.append(f"    Entropy: {entropy_bits(solo_answers):.2f} bits")

    # --- MAJORITY VOTE ---
    mv = q["majority_vote"]
    mv_ans = mv["answer"]
    mv_ok = mv["correct"]
    mv_mark = "OK" if mv_ok else "XX"
    mv_unan = "unanimous" if mv.get("unanimous") else "split"
    lines.append(f"\n  MAJORITY VOTE: {mv_ans}  [{mv_mark}]  ({mv_unan})")

    # --- ARRIVAL ---
    ar = q["arrival"]
    ar_ans = ar["answer"]
    ar_ok = ar["correct"]
    ar_mark = "OK" if ar_ok else "XX"
    atoms = ar.get("atoms_used", {})
    n_conflicts = atoms.get("@CONFLICT", 0)
    n_consensus = atoms.get("@CONSENSUS", 0)
    lines.append(f"\n  ARRIVAL: {ar_ans}  [{ar_mark}]")
    lines.append(f"    Atoms: @CONFLICT={n_conflicts}, @CONSENSUS={n_consensus}")
    lines.append(f"    Unique atoms: {ar.get('unique_atoms', 0)}, Cost: ${ar.get('cost_usd', 0):.4f}")

    # Dialogue summary
    dialogue = ar.get("dialogue", [])
    rounds_seen = set()
    for msg in dialogue:
        rounds_seen.add(msg["round"])

    # Track answer changes across rounds
    round_answers = {}
    for msg in dialogue:
        r = msg["round"]
        agent = msg["from"]
        text = msg.get("message", "")
        # Try to extract answer from @CONSENSUS[answer=X]
        import re
        cons = re.findall(r"@CONSENSUS\[answer=([A-D])\]", text)
        if cons:
            if r not in round_answers:
                round_answers[r] = {}
            round_answers[r][agent] = cons[-1]

    if round_answers:
        lines.append(f"    Round answers:")
        for r in sorted(round_answers.keys()):
            ra = round_answers[r]
            parts = [f"{a}:{v}" for a, v in sorted(ra.items())]
            lines.append(f"      R{r}: {', '.join(parts)}")

    # --- CRDT ---
    crdt = q.get("crdt", {})
    care = crdt.get("care_resolve", {})
    debt = crdt.get("meaning_debt", {})

    care_val = care.get("care_resolve") or 0
    debt_val = debt.get("total_meaning_debt") or 0
    health = debt.get("health_assessment") or "?"
    unresolved = debt.get("unresolved_conflicts") or 0
    total_conflicts = debt.get("total_conflicts") or 0
    total_resolutions = debt.get("total_resolutions") or 0
    fairness = debt.get("fairness_index") or 0

    lines.append(f"\n  CRDT Metrics:")
    lines.append(f"    CARE Resolve: {care_val:.3f}")
    lines.append(f"    Meaning Debt: {debt_val:.3f}")
    lines.append(f"    Health: {health}")
    lines.append(f"    Conflicts: {total_conflicts} raised, {total_resolutions} resolved, {unresolved} unresolved")
    lines.append(f"    Fairness Index: {fairness:.3f}")

    # --- OUTCOME ANALYSIS ---
    lines.append(f"\n  OUTCOME:")
    solo_had_correct = solo_correct_count > 0
    mv_right = mv_ok
    ar_right = ar_ok

    if ar_right and not mv_right:
        if solo_had_correct:
            lines.append(f"    >> ARRIVAL RESCUED: MV failed, but ARRIVAL found the right answer")
            lines.append(f"       Solo had correct ({solo_correct_count}/5), protocol amplified minority")
        else:
            lines.append(f"    >> ARRIVAL CREATED: Neither solo nor MV had it, protocol generated new insight!")
    elif ar_right and mv_right:
        lines.append(f"    >> BOTH CORRECT: MV and ARRIVAL both right")
    elif not ar_right and mv_right:
        lines.append(f"    >> ARRIVAL REGRESSED: MV was right but ARRIVAL went wrong")
        lines.append(f"       ARRIVAL chose {ar_ans} instead of {correct}")
    elif not ar_right and not mv_right:
        if solo_had_correct:
            lines.append(f"    >> BOTH FAILED (minority lost): {solo_correct_count}/5 solo agents had it right")
        else:
            lines.append(f"    >> BOTH FAILED: Nobody got it right")

    # Flip detection
    solo_majority = max(dist, key=dist.get) if dist else "?"
    if ar_ans != solo_majority:
        lines.append(f"    >> FLIP: Solo majority was {solo_majority}, ARRIVAL chose {ar_ans}")

    time_s = q.get("question_time_s", 0)
    lines.append(f"\n  Time: {time_s:.0f}s ({time_s/60:.1f} min)")

    return "\n".join(lines)


def generate_summary_table(data):
    """Generate a compact summary table of all 40 questions."""
    results = data["results"]
    lines = []
    lines.append(f"\n{'='*90}")
    lines.append(f"  SUMMARY TABLE: All 40 Questions")
    lines.append(f"{'='*90}")
    lines.append(f"  {'#':<4} {'ID':<10} {'Domain':<16} {'Correct':<8} {'Solo':>5} {'MV':>4} {'ARR':>4} {'CARE':>6} {'Debt':>6} {'Health':<10}")
    lines.append(f"  {'-'*84}")

    stats = {
        "arrival_rescued": 0,
        "arrival_created": 0,
        "arrival_regressed": 0,
        "both_correct": 0,
        "both_failed_minority": 0,
        "both_failed_total": 0,
        "flips": 0,
    }

    for i, q in enumerate(results):
        qid = q["question_id"]
        domain = q["domain"][:14]
        correct = q["correct_answer"]

        solo_correct = sum(1 for s in q["solo"] if s["correct"])
        solo_str = f"{solo_correct}/5"

        mv_ok = q["majority_vote"]["correct"]
        mv_str = "OK" if mv_ok else "XX"

        ar_ok = q["arrival"]["correct"]
        ar_str = "OK" if ar_ok else "XX"

        care = q.get("crdt", {}).get("care_resolve", {}).get("care_resolve") or 0
        debt = q.get("crdt", {}).get("meaning_debt", {}).get("total_meaning_debt") or 0
        health = (q.get("crdt", {}).get("meaning_debt", {}).get("health_assessment") or "?")[:8]

        lines.append(f"  Q{i+1:02d}  {qid:<10} {domain:<16} {correct:<8} {solo_str:>5} {mv_str:>4} {ar_str:>4} {care:>6.3f} {debt:>6.2f} {health:<10}")

        # Stats
        if ar_ok and not mv_ok:
            if solo_correct > 0:
                stats["arrival_rescued"] += 1
            else:
                stats["arrival_created"] += 1
        elif ar_ok and mv_ok:
            stats["both_correct"] += 1
        elif not ar_ok and mv_ok:
            stats["arrival_regressed"] += 1
        elif not ar_ok and not mv_ok:
            if solo_correct > 0:
                stats["both_failed_minority"] += 1
            else:
                stats["both_failed_total"] += 1

        solo_answers = [s["answer"] for s in q["solo"] if s["answer"]]
        if solo_answers:
            from collections import Counter
            solo_maj = Counter(solo_answers).most_common(1)[0][0]
            if q["arrival"]["answer"] != solo_maj:
                stats["flips"] += 1

    lines.append(f"  {'-'*84}")

    # Outcome breakdown
    lines.append(f"\n  OUTCOME BREAKDOWN:")
    lines.append(f"    ARRIVAL rescued (MV wrong, ARRIVAL right, minority had it): {stats['arrival_rescued']}")
    lines.append(f"    ARRIVAL created  (nobody had it, ARRIVAL found it):         {stats['arrival_created']}")
    lines.append(f"    Both correct (MV + ARRIVAL):                                {stats['both_correct']}")
    lines.append(f"    ARRIVAL regressed (MV right, ARRIVAL wrong):                {stats['arrival_regressed']}")
    lines.append(f"    Both failed (minority had correct):                         {stats['both_failed_minority']}")
    lines.append(f"    Both failed (nobody had it):                                {stats['both_failed_total']}")
    lines.append(f"    Total answer flips (ARRIVAL != solo majority):              {stats['flips']}")

    return "\n".join(lines)


def domain_breakdown(data):
    """Per-domain analysis."""
    results = data["results"]
    domains = {}
    for q in results:
        d = q["domain"]
        if d not in domains:
            domains[d] = {"solo_c": 0, "solo_t": 0, "mv_c": 0, "mv_t": 0, "ar_c": 0, "ar_t": 0, "care": [], "debt": []}
        solo_c = sum(1 for s in q["solo"] if s["correct"])
        domains[d]["solo_c"] += solo_c
        domains[d]["solo_t"] += len(q["solo"])
        domains[d]["mv_c"] += int(q["majority_vote"]["correct"])
        domains[d]["mv_t"] += 1
        domains[d]["ar_c"] += int(q["arrival"]["correct"])
        domains[d]["ar_t"] += 1
        care = q.get("crdt", {}).get("care_resolve", {}).get("care_resolve") or 0
        debt = q.get("crdt", {}).get("meaning_debt", {}).get("total_meaning_debt") or 0
        domains[d]["care"].append(care)
        domains[d]["debt"].append(debt)

    lines = []
    lines.append(f"\n{'='*72}")
    lines.append(f"  PER-DOMAIN BREAKDOWN")
    lines.append(f"{'='*72}")
    lines.append(f"  {'Domain':<18} {'N':>3} {'Solo%':>7} {'MV%':>7} {'ARR%':>7} {'CARE':>7} {'Debt':>7}")
    lines.append(f"  {'-'*60}")

    for d in sorted(domains.keys()):
        dd = domains[d]
        n = dd["mv_t"]
        solo_pct = dd["solo_c"] / dd["solo_t"] * 100 if dd["solo_t"] else 0
        mv_pct = dd["mv_c"] / dd["mv_t"] * 100 if dd["mv_t"] else 0
        ar_pct = dd["ar_c"] / dd["ar_t"] * 100 if dd["ar_t"] else 0
        avg_care = sum(dd["care"]) / len(dd["care"]) if dd["care"] else 0
        avg_debt = sum(dd["debt"]) / len(dd["debt"]) if dd["debt"] else 0
        lines.append(f"  {d:<18} {n:>3} {solo_pct:>6.1f}% {mv_pct:>6.1f}% {ar_pct:>6.1f}% {avg_care:>7.3f} {avg_debt:>7.2f}")

    return "\n".join(lines)


def agent_analysis(data):
    """Per-agent breakdown."""
    results = data["results"]
    agents = {}
    for q in results:
        for s in q["solo"]:
            name = s["agent_name"]
            if name not in agents:
                agents[name] = {"correct": 0, "total": 0, "domains": {}}
            agents[name]["total"] += 1
            if s["correct"]:
                agents[name]["correct"] += 1
            d = q["domain"]
            if d not in agents[name]["domains"]:
                agents[name]["domains"][d] = {"correct": 0, "total": 0}
            agents[name]["domains"][d]["total"] += 1
            if s["correct"]:
                agents[name]["domains"][d]["correct"] += 1

    lines = []
    lines.append(f"\n{'='*72}")
    lines.append(f"  PER-AGENT SOLO ACCURACY")
    lines.append(f"{'='*72}")

    for name in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]:
        a = agents.get(name, {"correct": 0, "total": 1, "domains": {}})
        pct = a["correct"] / a["total"] * 100 if a["total"] else 0
        lines.append(f"\n  {name}: {a['correct']}/{a['total']} = {pct:.1f}%")
        for d in sorted(a["domains"].keys()):
            dd = a["domains"][d]
            dpct = dd["correct"] / dd["total"] * 100 if dd["total"] else 0
            lines.append(f"    {d:<18} {dd['correct']}/{dd['total']} = {dpct:.1f}%")

    return "\n".join(lines)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    data = load_results(path)

    results = data["results"]
    summary = data["summary"]

    print(f"\n{'#'*72}")
    print(f"  PHASE 16 HOMOGENEOUS ENSEMBLE: DETAILED PER-QUESTION ANALYTICS")
    print(f"  Model: {data['model']} | Agents: {', '.join(data['agents'])}")
    print(f"  Questions: {data['total_questions']} | API calls: {data['total_api_calls']}")
    print(f"  Cost: ${data['total_cost_usd']:.2f} | Duration: {data['duration_minutes']:.0f} min")
    print(f"{'#'*72}")

    # Headline results
    print(f"\n  HEADLINE RESULTS:")
    print(f"    Solo:    {summary['solo']['accuracy']*100:.1f}%  ({summary['solo']['correct']}/{summary['solo']['total']})")
    print(f"    MV:      {summary['majority_vote']['accuracy']*100:.1f}%  ({summary['majority_vote']['correct']}/{summary['majority_vote']['total']})")
    print(f"    ARRIVAL: {summary['arrival']['accuracy']*100:.1f}%  ({summary['arrival']['correct']}/{summary['arrival']['total']})")
    print(f"    GAIN vs Solo: +{summary['gain_vs_solo_pp']:.1f} pp")
    print(f"    GAIN vs MV:   +{summary['gain_vs_mv_pp']:.1f} pp")

    # Summary table
    print(generate_summary_table(data))

    # Domain breakdown
    print(domain_breakdown(data))

    # Agent analysis
    print(agent_analysis(data))

    # Per-question detailed analysis
    print(f"\n\n{'#'*72}")
    print(f"  DETAILED PER-QUESTION ANALYSIS")
    print(f"{'#'*72}")

    for i, q in enumerate(results):
        print(f"\n{analyze_question(q, i)}")

    print(f"\n{'='*72}")
    print(f"  END OF REPORT")
    print(f"{'='*72}")


if __name__ == "__main__":
    main()
