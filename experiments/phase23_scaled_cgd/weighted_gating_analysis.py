# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 23 Analysis 2: Weighted Gating with Threshold
Recomputes CGD from existing data — no new API calls.
"""
import json, sys
from collections import Counter

with open("experiments/phase23_scaled_cgd/results/cgd7_results.json") as f:
    data = json.load(f)
    results = data["questions"]

ALL = ['grok','gemini','qwen','deepseek','glm','kimi','claude']

# Solo accuracies on 198q
solo_acc = {}
solo_correct = {}
for m in ALL:
    c = sum(1 for q in results if q.get("solo_" + m) == q['correct_answer'])
    solo_acc[m] = c / len(results)
    solo_correct[m] = c

print("=== SOLO ACCURACIES (198q) ===")
for m in sorted(solo_acc, key=lambda x: -solo_acc[x]):
    pct = solo_acc[m] * 100
    print("  %12s: %d/198 = %.1f%%" % (m, solo_correct[m], pct))

def weighted_mv(question, models, weights, use_debate=False):
    score = {}
    for m in models:
        if use_debate and question.get("debate_" + m) is not None:
            v = question["debate_" + m]
        else:
            v = question.get("solo_" + m)
        if v is not None:
            w = weights.get(m, 0)
            score[v] = score.get(v, 0) + w
    if not score:
        return None
    return max(score, key=score.get)

def simple_mv(question, models, use_debate=False):
    votes = []
    for m in models:
        if use_debate and question.get("debate_" + m) is not None:
            v = question["debate_" + m]
        else:
            v = question.get("solo_" + m)
        if v is not None:
            votes.append(v)
    if not votes:
        return None
    return Counter(votes).most_common(1)[0][0]

def cgd_answer(question, models, weights=None, use_weights=False):
    """CGD-like: lock on high agreement, debate on low agreement."""
    solo_votes = []
    for m in models:
        v = question.get("solo_" + m)
        if v is not None:
            solo_votes.append((m, v))

    if not solo_votes:
        return None

    n = len(solo_votes)
    vote_counts = Counter(v for _, v in solo_votes)
    top_answer, top_count = vote_counts.most_common(1)[0]

    # Lock if at most 1 dissenter (same as Phase 22/23 logic scaled)
    lock_threshold = n - 1

    if top_count >= lock_threshold:
        # LOCKED — use solo majority (weighted or not)
        if use_weights and weights:
            return weighted_mv(question, models, weights, use_debate=False)
        return top_answer
    else:
        # DEBATED — use debate answers if available
        if use_weights and weights:
            return weighted_mv(question, models, weights, use_debate=True)
        return simple_mv(question, models, use_debate=True)


# =====================================================
# THRESHOLD SWEEP
# =====================================================
thresholds = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]

print()
print("=" * 85)
print("=== ANALYSIS 2: WEIGHTED GATING — THRESHOLD SWEEP ===")
print("=" * 85)

summary_rows = []

for thresh in thresholds:
    active = [m for m in ALL if solo_acc[m] >= thresh]
    excluded = [m for m in ALL if solo_acc[m] < thresh]

    if len(active) < 1:
        continue

    weights_raw = {m: solo_acc[m] for m in active}

    # Simple MV
    mv_c = sum(1 for q in results if simple_mv(q, active) == q['correct_answer'])

    # Weighted MV (solo only)
    wmv_c = sum(1 for q in results if weighted_mv(q, active, weights_raw) == q['correct_answer'])

    # Weighted MV (with debate)
    wmv_d_c = sum(1 for q in results if weighted_mv(q, active, weights_raw, use_debate=True) == q['correct_answer'])

    # CGD (unweighted)
    cgd_c = sum(1 for q in results if cgd_answer(q, active) == q['correct_answer'])

    # CGD (weighted)
    cgd_w_c = sum(1 for q in results if cgd_answer(q, active, weights_raw, use_weights=True) == q['correct_answer'])

    # Oracle
    oracle_c = sum(1 for q in results if any(q.get("solo_" + m) == q['correct_answer'] for m in active))

    excl_str = ", ".join(excluded) if excluded else "none"

    print()
    print("--- Threshold: %.0f%% | Active: %d models | Excluded: %s ---" % (thresh*100, len(active), excl_str))
    print("  Active:  %s" % ", ".join("%s(%.1f%%)" % (m, solo_acc[m]*100) for m in active))
    print()
    print("  Simple MV-%d:         %d/198 = %.1f%%" % (len(active), mv_c, mv_c/198*100))
    print("  Weighted MV (solo):   %d/198 = %.1f%%" % (wmv_c, wmv_c/198*100))
    print("  Weighted MV (debate): %d/198 = %.1f%%" % (wmv_d_c, wmv_d_c/198*100))
    print("  CGD-%d (unweighted):  %d/198 = %.1f%%" % (len(active), cgd_c, cgd_c/198*100))
    print("  CGD-%d (weighted):    %d/198 = %.1f%%" % (len(active), cgd_w_c, cgd_w_c/198*100))
    print("  Oracle:               %d/198 = %.1f%%" % (oracle_c, oracle_c/198*100))

    summary_rows.append({
        'thresh': thresh,
        'n': len(active),
        'excl': excl_str,
        'mv': mv_c,
        'wmv': wmv_c,
        'wmv_d': wmv_d_c,
        'cgd': cgd_c,
        'cgd_w': cgd_w_c,
        'oracle': oracle_c,
    })

# =====================================================
# SUMMARY TABLE
# =====================================================
print()
print("=" * 85)
print("=== SUMMARY TABLE: All Thresholds ===")
print("=" * 85)
print()
hdr = "  Thresh  Models  Excluded     MV    WMV   WMV+D   CGD   CGD-W  Oracle"
print(hdr)
print("  " + "-" * (len(hdr) - 2))

for r in summary_rows:
    print("  %5.0f%%  %4d    %-12s %3d    %3d    %3d    %3d    %3d    %3d" % (
        r['thresh']*100, r['n'], r['excl'][:12],
        r['mv'], r['wmv'], r['wmv_d'], r['cgd'], r['cgd_w'], r['oracle']
    ))

# Reference lines
print()
print("  Reference:")
print("    Grok solo:     173/198 = 87.4%%")
print("    CGD-7 original: 172/198 = 86.9%%")
print("    MV-7 original:  170/198 = 85.9%%")
print("    Oracle-7:       191/198 = 96.5%%")


# =====================================================
# DETAILED: 65% THRESHOLD (user's request)
# =====================================================
print()
print("=" * 85)
print("=== DETAILED: 65%% THRESHOLD (User requested) ===")
print("=" * 85)

thresh = 0.65
active = [m for m in ALL if solo_acc[m] >= thresh]
excluded = [m for m in ALL if solo_acc[m] < thresh]
weights_raw = {m: solo_acc[m] for m in active}

print()
print("Active models (%d):" % len(active))
for m in active:
    print("  %s: %.1f%% (weight=%.3f)" % (m, solo_acc[m]*100, solo_acc[m]))
print("Excluded (%d):" % len(excluded))
for m in excluded:
    print("  %s: %.1f%% (weight=0)" % (m, solo_acc[m]*100))
print()

# Track disagreements between CGD-7 and CGD-6-gated
disagreements = []
cgd7_c = 0
cgd6g_c = 0
cgd6gw_c = 0

for q in results:
    ca = q['correct_answer']
    cgd7_ans = q.get('final_answer')
    cgd6g_ans = cgd_answer(q, active)
    cgd6gw_ans = cgd_answer(q, active, weights_raw, use_weights=True)

    if cgd7_ans == ca:
        cgd7_c += 1
    if cgd6g_ans == ca:
        cgd6g_c += 1
    if cgd6gw_ans == ca:
        cgd6gw_c += 1

    if cgd6g_ans != cgd7_ans:
        disagreements.append({
            'qid': q['question_id'],
            'domain': q.get('domain', '?'),
            'correct': ca,
            'cgd7': cgd7_ans,
            'cgd6g': cgd6g_ans,
            'cgd6g_right': cgd6g_ans == ca,
            'cgd7_right': cgd7_ans == ca,
        })

print("=== COMPARISON (65%% threshold) ===")
print()
print("  Method                     Correct  Accuracy")
print("  -------------------------  -------  --------")
print("  Grok solo                  173/198   87.4%%")
print("  CGD-6 gated (unweighted)   %d/198   %.1f%%" % (cgd6g_c, cgd6g_c/198*100))
print("  CGD-6 gated (weighted)     %d/198   %.1f%%" % (cgd6gw_c, cgd6gw_c/198*100))
print("  CGD-7 (original)           %d/198   %.1f%%" % (cgd7_c, cgd7_c/198*100))
print()

print("=== WHERE GATED CGD-6 DIFFERS FROM CGD-7 (%d questions) ===" % len(disagreements))
gained = sum(1 for d in disagreements if d['cgd6g_right'] and not d['cgd7_right'])
lost = sum(1 for d in disagreements if not d['cgd6g_right'] and d['cgd7_right'])
both_wrong = sum(1 for d in disagreements if not d['cgd6g_right'] and not d['cgd7_right'])
print("  GAINED (cgd7 wrong -> cgd6g right): %d" % gained)
print("  LOST   (cgd7 right -> cgd6g wrong): %d" % lost)
print("  SWAP   (both wrong, diff answer):   %d" % both_wrong)
print("  Net change: %+d" % (gained - lost))
print()

for d in disagreements:
    if d['cgd6g_right'] and not d['cgd7_right']:
        tag = "GAINED"
    elif not d['cgd6g_right'] and d['cgd7_right']:
        tag = "LOST  "
    else:
        tag = "SWAP  "
    print("  Q%-4s [%-10s] correct=%s cgd7=%s cgd6g=%s  %s" % (
        str(d['qid']), d['domain'], d['correct'], d['cgd7'], d['cgd6g'], tag))

# =====================================================
# PER-DOMAIN for 65% gated
# =====================================================
print()
print("=== PER-DOMAIN: 65%% Threshold ===")

domains = {}
for q in results:
    d = q.get('domain', 'Unknown')
    if d not in domains:
        domains[d] = {'n': 0, 'cgd7': 0, 'cgd6g': 0, 'cgd6gw': 0, 'grok': 0}
    domains[d]['n'] += 1
    ca = q['correct_answer']
    if q.get('final_answer') == ca:
        domains[d]['cgd7'] += 1
    if cgd_answer(q, active) == ca:
        domains[d]['cgd6g'] += 1
    if cgd_answer(q, active, weights_raw, use_weights=True) == ca:
        domains[d]['cgd6gw'] += 1
    if q.get('solo_grok') == ca:
        domains[d]['grok'] += 1

print()
print("  %-12s %4s %8s %8s %8s %8s" % ("Domain", "N", "CGD-7", "CGD-6g", "CGD-6gw", "Grok"))
print("  " + "-" * 48)
for d in sorted(domains):
    v = domains[d]
    print("  %-12s %4d %7.1f%% %7.1f%% %7.1f%% %7.1f%%" % (
        d, v['n'],
        v['cgd7']/v['n']*100,
        v['cgd6g']/v['n']*100,
        v['cgd6gw']/v['n']*100,
        v['grok']/v['n']*100,
    ))

# =====================================================
# KEY FINDING: optimal threshold
# =====================================================
print()
print("=" * 85)
print("=== KEY FINDINGS ===")
print("=" * 85)
print()

best = max(summary_rows, key=lambda r: r['cgd'])
print("1. BEST CGD (unweighted): threshold=%.0f%%, %d models, %d/198 = %.1f%%" % (
    best['thresh']*100, best['n'], best['cgd'], best['cgd']/198*100))

best_w = max(summary_rows, key=lambda r: r['cgd_w'])
print("2. BEST CGD (weighted):   threshold=%.0f%%, %d models, %d/198 = %.1f%%" % (
    best_w['thresh']*100, best_w['n'], best_w['cgd_w'], best_w['cgd_w']/198*100))

best_wmv = max(summary_rows, key=lambda r: r['wmv_d'])
print("3. BEST WMV+debate:       threshold=%.0f%%, %d models, %d/198 = %.1f%%" % (
    best_wmv['thresh']*100, best_wmv['n'], best_wmv['wmv_d'], best_wmv['wmv_d']/198*100))

print()
print("4. At 65%% threshold (user-specified):")
r65 = [r for r in summary_rows if r['thresh'] == 0.65][0]
print("   - Qwen excluded (58.6%% < 65%%)")
print("   - CGD-6 unweighted: %d/198 = %.1f%%" % (r65['cgd'], r65['cgd']/198*100))
print("   - CGD-6 weighted:   %d/198 = %.1f%%" % (r65['cgd_w'], r65['cgd_w']/198*100))
print("   - Grok solo:        173/198 = 87.4%%")
print("   - Verdict: %s" % (
    "CGD-6 TIES Grok solo" if r65['cgd'] == 173 else
    "CGD-6 BEATS Grok solo (+%.1f pp)" % ((r65['cgd'] - 173)/198*100) if r65['cgd'] > 173 else
    "Grok solo still wins (-%.1f pp)" % ((173 - r65['cgd'])/198*100)
))

print()
print("5. Weighting effect:")
for r in summary_rows:
    delta = r['cgd_w'] - r['cgd']
    if delta != 0:
        print("   %.0f%% threshold: weighted %s %d vs unweighted %d (%+d)" % (
            r['thresh']*100,
            "helps" if delta > 0 else "hurts",
            r['cgd_w'], r['cgd'], delta))

print()
print("DONE.")
