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
ARRIVAL Phase 5: Statistical Analysis & Bilingual Report Generation
McNemar's test, Cohen's h, Wilson CI, domain breakdowns, EN/RU reports.
"""

import sys
import os
import json
import math
from datetime import datetime
from collections import Counter

sys.stdout.reconfigure(errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from questions import DOMAINS


# ============================================================
# Statistical Functions
# ============================================================

def mcnemar_test(arrival_correct: list, majority_correct: list) -> dict:
    """
    McNemar's test for paired nominal data.
    Compares ARRIVAL vs Majority Vote on same questions.

    Returns dict with b, c (discordant pairs), chi2, p_value.
    """
    assert len(arrival_correct) == len(majority_correct)

    # b = ARRIVAL correct, Majority wrong
    # c = ARRIVAL wrong, Majority correct
    b = sum(1 for a, m in zip(arrival_correct, majority_correct) if a and not m)
    c = sum(1 for a, m in zip(arrival_correct, majority_correct) if not a and m)

    # Both correct / both wrong (concordant)
    both_correct = sum(1 for a, m in zip(arrival_correct, majority_correct) if a and m)
    both_wrong = sum(1 for a, m in zip(arrival_correct, majority_correct) if not a and not m)

    # McNemar's chi-squared (with continuity correction)
    if b + c == 0:
        chi2 = 0.0
        p_value = 1.0
    else:
        chi2 = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) > 0 else 0
        # Approximate p-value from chi-squared with 1 df
        p_value = _chi2_p_value(chi2)

    return {
        "b_arrival_wins": b,
        "c_majority_wins": c,
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "chi2": round(chi2, 4),
        "p_value": round(p_value, 6),
        "significant": p_value < 0.05,
        "n": len(arrival_correct),
    }


def _chi2_p_value(chi2: float) -> float:
    """Approximate p-value for chi-squared with 1 degree of freedom."""
    if chi2 <= 0:
        return 1.0
    # Using the complementary error function approximation
    z = math.sqrt(chi2)
    # Standard normal survival function approximation
    t = 1.0 / (1.0 + 0.2316419 * z)
    d = 0.3989422804014327  # 1/sqrt(2*pi)
    p = d * math.exp(-z * z / 2.0) * (
        0.3193815 * t - 0.3565638 * t**2 + 1.781478 * t**3
        - 1.821256 * t**4 + 1.330274 * t**5
    )
    return 2 * p  # Two-tailed


def cohens_h(p1: float, p2: float) -> float:
    """
    Cohen's h effect size for difference between two proportions.
    h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
    """
    h1 = 2 * math.asin(math.sqrt(max(0, min(1, p1))))
    h2 = 2 * math.asin(math.sqrt(max(0, min(1, p2))))
    return round(abs(h1 - h2), 4)


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple:
    """Wilson score confidence interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z**2 / total
    centre = p + z**2 / (2 * total)
    offset = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)
    lower = max(0, (centre - offset) / denom)
    upper = min(1, (centre + offset) / denom)
    return (round(lower, 4), round(upper, 4))


# ============================================================
# Analysis
# ============================================================

def load_results(results_dir: str) -> dict:
    """Load the latest Phase 5 results JSON."""
    files = [f for f in os.listdir(results_dir) if f.startswith("phase5_results_") and f.endswith(".json")]
    if not files:
        raise FileNotFoundError(f"No Phase 5 results found in {results_dir}")
    latest = sorted(files)[-1]
    path = os.path.join(results_dir, latest)
    print(f"Loading results from: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def full_analysis(data: dict) -> dict:
    """Run complete statistical analysis on Phase 5 results."""
    results = data["results"]
    analysis = {}

    # Overall accuracy
    mv_correct = [r["majority_vote"]["correct"] for r in results]
    ar_correct = [r["arrival"]["correct"] for r in results]

    mv_acc = sum(mv_correct) / len(mv_correct) if mv_correct else 0
    ar_acc = sum(ar_correct) / len(ar_correct) if ar_correct else 0

    analysis["overall"] = {
        "majority_vote_accuracy": round(mv_acc, 4),
        "arrival_accuracy": round(ar_acc, 4),
        "majority_vote_ci": wilson_ci(sum(mv_correct), len(mv_correct)),
        "arrival_ci": wilson_ci(sum(ar_correct), len(ar_correct)),
        "cohens_h": cohens_h(ar_acc, mv_acc),
        "mcnemar": mcnemar_test(ar_correct, mv_correct),
    }

    # Per-domain analysis
    analysis["per_domain"] = {}
    for domain in DOMAINS:
        domain_results = [r for r in results if r["domain"] == domain]
        if not domain_results:
            continue

        dm_mv = [r["majority_vote"]["correct"] for r in domain_results]
        dm_ar = [r["arrival"]["correct"] for r in domain_results]

        mv_domain_acc = sum(dm_mv) / len(dm_mv) if dm_mv else 0
        ar_domain_acc = sum(dm_ar) / len(dm_ar) if dm_ar else 0

        analysis["per_domain"][domain] = {
            "n": len(domain_results),
            "majority_vote_accuracy": round(mv_domain_acc, 4),
            "arrival_accuracy": round(ar_domain_acc, 4),
            "majority_vote_ci": wilson_ci(sum(dm_mv), len(dm_mv)),
            "arrival_ci": wilson_ci(sum(dm_ar), len(dm_ar)),
            "cohens_h": cohens_h(ar_domain_acc, mv_domain_acc),
            "mcnemar": mcnemar_test(dm_ar, dm_mv),
        }

    # Per-trio analysis
    analysis["per_trio"] = {}
    for trio_name in set(r["trio_name"] for r in results):
        trio_results = [r for r in results if r["trio_name"] == trio_name]

        tr_mv = [r["majority_vote"]["correct"] for r in trio_results]
        tr_ar = [r["arrival"]["correct"] for r in trio_results]

        mv_trio_acc = sum(tr_mv) / len(tr_mv) if tr_mv else 0
        ar_trio_acc = sum(tr_ar) / len(tr_ar) if tr_ar else 0

        analysis["per_trio"][trio_name] = {
            "n": len(trio_results),
            "majority_vote_accuracy": round(mv_trio_acc, 4),
            "arrival_accuracy": round(ar_trio_acc, 4),
            "cohens_h": cohens_h(ar_trio_acc, mv_trio_acc),
            "mcnemar": mcnemar_test(tr_ar, tr_mv),
        }

    # Solo model accuracy
    solo_stats = {}
    for r in results:
        for solo in r["solo"]:
            model = solo["model"]
            if model not in solo_stats:
                solo_stats[model] = {"correct": 0, "total": 0}
            solo_stats[model]["total"] += 1
            if solo["correct"]:
                solo_stats[model]["correct"] += 1

    for model in solo_stats:
        s = solo_stats[model]
        s["accuracy"] = round(s["correct"] / s["total"], 4) if s["total"] > 0 else 0
        s["ci"] = wilson_ci(s["correct"], s["total"])

    analysis["solo_models"] = solo_stats

    # Interesting cases: where ARRIVAL flipped the answer
    flips = {"arrival_saved": [], "arrival_hurt": []}
    for r in results:
        mv_c = r["majority_vote"]["correct"]
        ar_c = r["arrival"]["correct"]
        if ar_c and not mv_c:
            flips["arrival_saved"].append({
                "question_id": r["question_id"],
                "domain": r["domain"],
                "correct": r["correct_answer"],
                "majority_answer": r["majority_vote"]["answer"],
                "arrival_answer": r["arrival"]["answer"],
            })
        elif not ar_c and mv_c:
            flips["arrival_hurt"].append({
                "question_id": r["question_id"],
                "domain": r["domain"],
                "correct": r["correct_answer"],
                "majority_answer": r["majority_vote"]["answer"],
                "arrival_answer": r["arrival"]["answer"],
            })

    analysis["case_studies"] = flips

    # Cost analysis
    total_mv_cost = sum(r["majority_vote"]["cost_usd"] for r in results)
    total_ar_cost = sum(r["arrival"]["cost_usd"] for r in results)
    analysis["cost"] = {
        "majority_vote_total": round(total_mv_cost, 4),
        "arrival_total": round(total_ar_cost, 4),
        "total": round(total_mv_cost + total_ar_cost, 4),
        "cost_per_question_mv": round(total_mv_cost / len(results), 6) if results else 0,
        "cost_per_question_ar": round(total_ar_cost / len(results), 6) if results else 0,
    }

    return analysis


# ============================================================
# Report Generation
# ============================================================

def generate_report_en(data: dict, analysis: dict) -> str:
    """Generate English Markdown report."""
    ov = analysis["overall"]
    mc = ov["mcnemar"]

    report = f"""# ARRIVAL Protocol Phase 5: Benchmark Results

## ARRIVAL Protocol vs Majority Voting on Knowledge Tasks

**Date**: {data.get('completed', 'N/A')[:10]}
**Total Questions**: {data.get('total_questions', 50)}
**Domains**: Science, History, Logic & Math, Law & Ethics, Technology
**Total Cost**: ${data.get('total_cost_usd', 0):.4f}

---

## Overall Results

| Condition | Accuracy | 95% CI | N |
|-----------|----------|--------|---|
| **Majority Vote** | {ov['majority_vote_accuracy']*100:.1f}% | [{ov['majority_vote_ci'][0]*100:.1f}%, {ov['majority_vote_ci'][1]*100:.1f}%] | {mc['n']} |
| **ARRIVAL Protocol** | {ov['arrival_accuracy']*100:.1f}% | [{ov['arrival_ci'][0]*100:.1f}%, {ov['arrival_ci'][1]*100:.1f}%] | {mc['n']} |

**Effect Size** (Cohen's h): {ov['cohens_h']}
**McNemar's Test**: chi2 = {mc['chi2']}, p = {mc['p_value']}
- ARRIVAL wins (MV wrong): {mc['b_arrival_wins']}
- MV wins (ARRIVAL wrong): {mc['c_majority_wins']}
- Both correct: {mc['both_correct']}
- Both wrong: {mc['both_wrong']}

{'**Result is statistically significant (p < 0.05)**' if mc['significant'] else 'Result is not statistically significant (p >= 0.05)'}

---

## Per-Domain Results

| Domain | MV Accuracy | ARRIVAL Accuracy | Cohen h | p-value |
|--------|-------------|------------------|---------|---------|
"""

    for domain in DOMAINS:
        if domain in analysis["per_domain"]:
            d = analysis["per_domain"][domain]
            dm = d["mcnemar"]
            sig = " *" if dm["significant"] else ""
            report += f"| {domain.replace('_', ' ').title()} | {d['majority_vote_accuracy']*100:.1f}% | {d['arrival_accuracy']*100:.1f}% | {d['cohens_h']} | {dm['p_value']}{sig} |\n"

    report += """
---

## Per-Trio Results

| Trio | MV Accuracy | ARRIVAL Accuracy | Cohen's h |
|------|-------------|------------------|-----------|
"""

    for trio_name, stats in analysis["per_trio"].items():
        report += f"| {trio_name.title()} | {stats['majority_vote_accuracy']*100:.1f}% | {stats['arrival_accuracy']*100:.1f}% | {stats['cohens_h']} |\n"

    report += """
---

## Individual Model Accuracy (Solo)

| Model | Accuracy | 95% CI |
|-------|----------|--------|
"""

    for model, stats in sorted(analysis["solo_models"].items(), key=lambda x: x[1]["accuracy"], reverse=True):
        report += f"| {model} | {stats['accuracy']*100:.1f}% | [{stats['ci'][0]*100:.1f}%, {stats['ci'][1]*100:.1f}%] |\n"

    # Case studies
    cs = analysis["case_studies"]
    if cs["arrival_saved"]:
        report += f"""
---

## Case Studies: ARRIVAL Corrected Majority Vote ({len(cs['arrival_saved'])} cases)

"""
        for case in cs["arrival_saved"][:5]:
            report += f"- **{case['question_id']}** ({case['domain']}): MV answered {case['majority_answer']}, ARRIVAL corrected to {case['arrival_answer']} (correct: {case['correct']})\n"

    if cs["arrival_hurt"]:
        report += f"""
## Case Studies: Majority Vote Beat ARRIVAL ({len(cs['arrival_hurt'])} cases)

"""
        for case in cs["arrival_hurt"][:5]:
            report += f"- **{case['question_id']}** ({case['domain']}): MV answered {case['majority_answer']} (correct), ARRIVAL chose {case['arrival_answer']} (wrong)\n"

    # Cost
    cost = analysis["cost"]
    report += f"""
---

## Cost Analysis

| Metric | Value |
|--------|-------|
| Majority Vote total | ${cost['majority_vote_total']:.4f} |
| ARRIVAL Protocol total | ${cost['arrival_total']:.4f} |
| **Total experiment cost** | **${cost['total']:.4f}** |
| Cost per question (MV) | ${cost['cost_per_question_mv']:.6f} |
| Cost per question (ARRIVAL) | ${cost['cost_per_question_ar']:.6f} |

---

## Methodology

- **Solo**: Each model answers independently (temperature={data.get('summary', {}).get('solo', {}).get('accuracy', 'N/A')})
- **Majority Vote**: 3 models answer independently, majority answer selected
- **ARRIVAL Protocol**: 4-round structured dialogue using DEUS.PROTOCOL v0.4 atoms (@GOAL, @INT, @C, @CONSENSUS, @CONFLICT, @RESOLUTION)
- **Statistical Test**: McNemar's test (paired nominal data) with continuity correction
- **Effect Size**: Cohen's h for proportion comparison

---

*Generated by ARRIVAL Phase 5 Analysis — {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    return report


def generate_report_ru(data: dict, analysis: dict) -> str:
    """Generate Russian Markdown report."""
    ov = analysis["overall"]
    mc = ov["mcnemar"]

    report = f"""# ARRIVAL Protocol Phase 5: Результаты бенчмарка

## Протокол ARRIVAL vs Голосование большинством на задачах знаний

**Дата**: {data.get('completed', 'N/A')[:10]}
**Всего вопросов**: {data.get('total_questions', 50)}
**Домены**: Наука, История, Логика и математика, Право и этика, Технологии
**Общая стоимость**: ${data.get('total_cost_usd', 0):.4f}

---

## Общие результаты

| Условие | Точность | 95% ДИ | N |
|---------|----------|--------|---|
| **Голосование большинством** | {ov['majority_vote_accuracy']*100:.1f}% | [{ov['majority_vote_ci'][0]*100:.1f}%, {ov['majority_vote_ci'][1]*100:.1f}%] | {mc['n']} |
| **Протокол ARRIVAL** | {ov['arrival_accuracy']*100:.1f}% | [{ov['arrival_ci'][0]*100:.1f}%, {ov['arrival_ci'][1]*100:.1f}%] | {mc['n']} |

**Размер эффекта** (Cohen's h): {ov['cohens_h']}
**Тест Макнемара**: chi2 = {mc['chi2']}, p = {mc['p_value']}
- ARRIVAL побеждает (MV ошибся): {mc['b_arrival_wins']}
- MV побеждает (ARRIVAL ошибся): {mc['c_majority_wins']}
- Оба правы: {mc['both_correct']}
- Оба ошиблись: {mc['both_wrong']}

{'**Результат статистически значим (p < 0.05)**' if mc['significant'] else 'Результат не является статистически значимым (p >= 0.05)'}

---

## Результаты по доменам

| Домен | MV Точность | ARRIVAL Точность | Cohen h | p-value |
|-------|-------------|------------------|---------|---------|
"""

    domain_names_ru = {
        "science": "Наука",
        "history": "История",
        "logic_math": "Логика и математика",
        "law_ethics": "Право и этика",
        "technology": "Технологии",
    }

    for domain in DOMAINS:
        if domain in analysis["per_domain"]:
            d = analysis["per_domain"][domain]
            dm = d["mcnemar"]
            sig = " *" if dm["significant"] else ""
            name_ru = domain_names_ru.get(domain, domain)
            report += f"| {name_ru} | {d['majority_vote_accuracy']*100:.1f}% | {d['arrival_accuracy']*100:.1f}% | {d['cohens_h']} | {dm['p_value']}{sig} |\n"

    report += """
---

## Результаты по трио

| Трио | MV Точность | ARRIVAL Точность | Cohen's h |
|------|-------------|------------------|-----------|
"""

    for trio_name, stats in analysis["per_trio"].items():
        report += f"| {trio_name.title()} | {stats['majority_vote_accuracy']*100:.1f}% | {stats['arrival_accuracy']*100:.1f}% | {stats['cohens_h']} |\n"

    report += """
---

## Точность отдельных моделей (Solo)

| Модель | Точность | 95% ДИ |
|--------|----------|--------|
"""

    for model, stats in sorted(analysis["solo_models"].items(), key=lambda x: x[1]["accuracy"], reverse=True):
        report += f"| {model} | {stats['accuracy']*100:.1f}% | [{stats['ci'][0]*100:.1f}%, {stats['ci'][1]*100:.1f}%] |\n"

    cs = analysis["case_studies"]
    if cs["arrival_saved"]:
        report += f"""
---

## Кейсы: ARRIVAL исправил ошибку большинства ({len(cs['arrival_saved'])} случаев)

"""
        for case in cs["arrival_saved"][:5]:
            report += f"- **{case['question_id']}** ({domain_names_ru.get(case['domain'], case['domain'])}): MV ответил {case['majority_answer']}, ARRIVAL исправил на {case['arrival_answer']} (верно: {case['correct']})\n"

    if cs["arrival_hurt"]:
        report += f"""
## Кейсы: Большинство оказалось точнее ARRIVAL ({len(cs['arrival_hurt'])} случаев)

"""
        for case in cs["arrival_hurt"][:5]:
            report += f"- **{case['question_id']}** ({domain_names_ru.get(case['domain'], case['domain'])}): MV ответил {case['majority_answer']} (верно), ARRIVAL выбрал {case['arrival_answer']} (ошибка)\n"

    cost = analysis["cost"]
    report += f"""
---

## Анализ стоимости

| Метрика | Значение |
|---------|----------|
| Голосование большинством | ${cost['majority_vote_total']:.4f} |
| Протокол ARRIVAL | ${cost['arrival_total']:.4f} |
| **Общая стоимость** | **${cost['total']:.4f}** |

---

## Методология

- **Solo**: Каждая модель отвечает независимо
- **Голосование большинством**: 3 модели отвечают независимо, выбирается ответ большинства
- **Протокол ARRIVAL**: 4-раундовый структурированный диалог через DEUS.PROTOCOL v0.4
- **Статистический тест**: тест Макнемара (парные номинальные данные)
- **Размер эффекта**: Cohen's h для сравнения пропорций

---

*Сгенерировано ARRIVAL Phase 5 Analysis -- {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    return report


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(base_dir, "results", "phase_5")
    docs_dir = os.path.join(base_dir, "docs")
    analysis_dir = os.path.join(base_dir, "results", "analysis")

    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(analysis_dir, exist_ok=True)

    # Load and analyze
    data = load_results(results_dir)
    analysis = full_analysis(data)

    # Save analysis JSON
    analysis_file = os.path.join(analysis_dir, f"phase5_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"Analysis saved: {analysis_file}")

    # Generate reports
    report_en = generate_report_en(data, analysis)
    report_ru = generate_report_ru(data, analysis)

    en_path = os.path.join(docs_dir, "PHASE_5_REPORT_EN.md")
    ru_path = os.path.join(docs_dir, "PHASE_5_REPORT_RU.md")

    with open(en_path, "w", encoding="utf-8") as f:
        f.write(report_en)
    print(f"English report: {en_path}")

    with open(ru_path, "w", encoding="utf-8") as f:
        f.write(report_ru)
    print(f"Russian report: {ru_path}")

    # Print summary
    ov = analysis["overall"]
    mc = ov["mcnemar"]
    print(f"\n{'='*50}")
    print(f"PHASE 5 ANALYSIS COMPLETE")
    print(f"{'='*50}")
    print(f"Majority Vote:    {ov['majority_vote_accuracy']*100:.1f}%")
    print(f"ARRIVAL Protocol: {ov['arrival_accuracy']*100:.1f}%")
    print(f"Cohen's h:        {ov['cohens_h']}")
    print(f"McNemar p-value:  {mc['p_value']}")
    print(f"Significant:      {'YES' if mc['significant'] else 'NO'}")
    print(f"{'='*50}")
