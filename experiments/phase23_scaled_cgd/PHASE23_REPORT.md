# Phase 23: Scaled CGD with 7-Model Ensemble (CGD-7) — Full Results

**Date**: 2026-03-03
**Author**: Mefodiy Kelevra (ORCID: 0009-0003-4153-392X)
**Benchmark**: GPQA Diamond (198 questions)
**Models**: 7 (Grok 4.1 Fast, Gemini 3 Flash, Claude Sonnet 4.6, DeepSeek V3.2, Kimi K2.5, GLM-5, Qwen3.5-397B)
**Total Cost**: $11.35 USD (1,822 API calls, 4.4M tokens)

---

## 1. Motivation

Phase 22 CGD achieved 86.4% on GPQA Diamond with a 3-model ensemble (Grok, Gemini, GPT-4.1). Key bottleneck: GPT-4.1 was the weakest link (66.2% solo, 6/7 extraction failures, 3% minority-correct rate). Theory: expanding to more diverse models should raise both the solo floor and the oracle ceiling, improving CGD performance.

Phase 23 scales CGD to **7 models from 5 vendors across 2 continents** (3 US, 4 Chinese), testing whether cross-vendor diversity improves collective intelligence.

---

## 2. Model Lineup

| # | Model | Vendor | Country | Solo (198q) | Solo (20q cal.) | Reasoning |
|---|-------|--------|---------|-------------|-----------------|-----------|
| 1 | Grok 4.1 Fast | xAI | US | **87.4%** | 80% | native |
| 2 | Gemini 3 Flash | Google | US | 82.8% | 80% | native |
| 3 | Claude Sonnet 4.6 | Anthropic | US | 80.8% | 85% | native |
| 4 | DeepSeek V3.2 | DeepSeek | CN | 74.7% | 80% | DISABLED |
| 5 | Kimi K2.5 | Moonshot | CN | 72.2% | 80% | DISABLED |
| 6 | GLM-5 | Zhipu AI | CN | 70.7% | 80% | DISABLED |
| 7 | Qwen3.5-397B | Alibaba | CN | 58.6% | 65% | DISABLED |

**Key observations**:
- Grok 4.1 Fast is the strongest individual model (87.4%) — higher than CGD-7 ensemble
- US models significantly outperform Chinese models (avg 83.7% vs 69.1%)
- Qwen3.5-397B severely underperforms with 54 extraction failures (27% of questions)
- Reasoning was disabled for all Chinese models to avoid thinking-token bloat

---

## 3. Protocol: CGD-7

```
Step 1: SOLO PHASE (7 independent calls)
  → Each model answers independently (temperature=0.3)
  → Extraction retry: if None, retry once with strict prompt
  → No cross-contamination

Step 2: AGREEMENT CLASSIFICATION
  → ≥5/7 agree: LOCK answer (unanimous / supermajority / strong_majority)
  → 4/7 agree:  Minority debate (simple_majority_4v3)
  → <4/7:       Full debate (no_majority)

Step 3: TARGETED DEBATE (only if ≤4/7 agreement)
  → Simple majority (4v3): 3 minority models see majority reasoning
  → No majority: All 7 exchange reasoning, majority vote decides
  → No R4 finalizer (confirmed destructive in Phases 20-22)
```

---

## 4. Results

### 4.1 Overall Accuracy

| Method | Correct | Accuracy | Notes |
|--------|---------|----------|-------|
| **CGD-7 (Phase 23)** | **172/198** | **86.9%** | Primary result |
| Best solo (Grok 4.1) | 173/198 | 87.4% | Solo > ensemble |
| Simple MV (7 models) | 170/198 | 85.9% | Debate adds +1.0pp |
| Weighted MV (7 models) | 169/198 | 85.4% | Weights from 20q calibration |
| Phase 22 CGD (3 models) | 171/198 | 86.4% | Previous SOTA |
| Oracle (any of 7) | 191/198 | 96.5% | Theoretical ceiling |

**CGD-7 vs Phase 22 CGD**: +0.5pp improvement (172 vs 171), McNemar p=1.0 (not significant).

### 4.2 Debate Type Breakdown

| Type | Count | % | Accuracy | Description |
|------|-------|---|----------|-------------|
| Unanimous (7/7) | 105 | 53% | 99.0% | All agree → locked |
| Supermajority (6/7) | 23 | 12% | 82.6% | Near-consensus → locked |
| Strong majority (5/7) | 22 | 11% | 81.8% | Locked threshold |
| Simple majority (4v3) | 21 | 11% | 66.7% | Minority debated |
| No majority (3v) | 22 | 11% | 68.2% | Full debate |
| No majority (2v) | 5 | 3% | 40.0% | Maximum disagreement |

**75.8% of questions locked** (≥5/7 agreement) with 93.3% accuracy on locked questions.
Only 24.2% required debate — these harder questions averaged 63.3% accuracy.

### 4.3 Per-Domain Analysis

| Domain | N | CGD-7 | Best solo | Worst solo |
|--------|---|-------|-----------|------------|
| Physics | 86 | **97.7%** | Grok 97% | Qwen 79% |
| Chemistry | 93 | 79.6% | Grok 83% | Qwen 39% |
| Biology | 19 | 73.7% | Claude 79% | GLM 58% |

Chemistry remains the hardest domain. Physics is nearly solved by the ensemble.

### 4.4 Cross-Vendor Diversity

| Group | Models | MV Accuracy | Oracle |
|-------|--------|-------------|--------|
| US (3) | Grok, Gemini, Claude | **86.9%** | 96.0% |
| CN (4) | Qwen, DeepSeek, GLM, Kimi | 76.3% | 88.4% |
| All 7 | Combined | 85.9% | **96.5%** |

- Cross-vendor disagreement on 40/198 = 20.2% of questions
- US-only MV (3 models) matches CGD-7 (7 models): 86.9%
- Adding 4 Chinese models barely helps: the diversity gain is offset by their lower accuracy

### 4.5 Minority-Was-Right Analysis

| Model | Times in minority | Minority correct | Rate |
|-------|-------------------|-----------------|------|
| Grok 4.1 | 20 | 10 | **50%** |
| Gemini 3 Flash | 27 | 9 | 33% |
| Claude Sonnet 4.6 | 22 | 4 | 18% |
| Kimi K2.5 | 23 | 3 | 13% |
| DeepSeek V3.2 | 28 | 3 | 11% |
| GLM-5 | 36 | 4 | 11% |
| Qwen3.5-397B | 22 | 1 | **5%** |

Grok is the strongest minority voice — when it disagrees with the majority, it's correct 50% of the time. Qwen's minority dissent is almost never useful (5%).

---

## 5. Key Findings

### 5.1 The Diversity-Quality Tradeoff

The central finding of Phase 23: **adding more models does not automatically improve CGD accuracy when the new models are substantially weaker.** The 7-model ensemble achieves 86.9%, barely above the 3-model Phase 22 result (86.4%, p=1.0). Meanwhile, the best solo model (Grok, 87.4%) outperforms the 7-model ensemble.

This occurs because:
1. **Weak models vote incorrectly on easy questions** — Qwen's 54 extraction failures and 58.6% accuracy drag down consensus
2. **Debate amplifies errors** — on 4v3 splits where the majority is wrong, debate rarely corrects the error (66.7% accuracy)
3. **The oracle gap is huge** (96.5%) — the information is IN the ensemble, but CGD cannot extract it

### 5.2 The Solo-Beats-Ensemble Problem

This is the most significant finding: Grok 4.1 solo (87.4%) outperforms CGD-7 (86.9%). This means:
- 1 API call to the best model > 7+ API calls to 7 models with debate
- The protocol overhead ($11.35 vs ~$1.50 for Grok solo) provides no accuracy benefit
- Cross-model debate introduces more error than it corrects when model quality varies widely

### 5.3 What Works

1. **Unanimous agreement** (53% of questions, 99.0% accuracy) — nearly perfect signal
2. **Physics** is effectively solved (97.7%)
3. **Oracle ceiling is high** (96.5%) — the knowledge exists; better extraction needed
4. **Debate adds +1.0pp over simple MV** — modest but consistent
5. **Cross-vendor diversity does increase oracle** (+0.5pp over US-only)

### 5.4 What Doesn't Work

1. **Adding weak models hurts more than it helps** — quality > quantity
2. **Debate on high-disagreement questions** has low accuracy (40-68%)
3. **Weighted voting didn't help** — 20q calibration insufficient, weight range too narrow
4. **Extraction failures** remain a critical issue for some models (Qwen: 54 None answers)

---

## 6. Comparison Across Phases

| Phase | Method | Models | Accuracy | Cost | Key Finding |
|-------|--------|--------|----------|------|-------------|
| 20 | ARRIVAL Full | 3 | 78.8% | $7.98 | Anchoring destroys accuracy |
| 21 | ARRIVAL Strong | 3 | 76.3% | $7.03 | R4 confirmed destructive |
| 22 | CGD (3 models) | 3 | 86.4% | $5.72 | CGD works, independence key |
| **23** | **CGD-7** | **7** | **86.9%** | **$11.35** | Quality > quantity |
| - | Grok solo | 1 | 87.4% | ~$1.50 | Best model beats ensemble |
| - | Oracle (7) | 7 | 96.5% | - | Diversity gap = 10pp |

---

## 7. Conclusions

Phase 23 demonstrates that **scaling CGD from 3 to 7 models provides negligible accuracy improvement** (+0.5pp, p=1.0) when the additional models are substantially weaker than the best performers. The best individual model (Grok 4.1 Fast, 87.4%) outperforms the 7-model ensemble (86.9%) at 1/8 the cost.

However, the 96.5% oracle ceiling proves that cross-vendor diversity contains valuable signal — the ensemble collectively knows the answer to 191/198 questions. The challenge shifts from "add more models" to "extract collective knowledge more effectively."

Future directions:
1. **Model-gated voting**: Weight votes by estimated per-model reliability (e.g., exclude Qwen on Chemistry)
2. **Confidence scoring**: Use model logprobs or self-reported confidence to weight answers
3. **Best-3 CGD**: Run CGD only on the top 3 models (Grok, Gemini, Claude) — should match or exceed CGD-7 at lower cost
4. **Adaptive ensemble**: Dynamically select which models to query based on domain

---

## 8. Reproducibility

All code, data, and results are available in this repository:
- Script: `experiments/phase23_scaled_cgd/run_phase23.py`
- Evaluation: `experiments/phase23_scaled_cgd/evaluate.py`
- Results: `experiments/phase23_scaled_cgd/results/cgd7_results.json`
- Solo baselines: `experiments/phase23_scaled_cgd/results/solo_baselines_20q.json`
- GPQA data: `experiments/phase20_gpqa_full/data/gpqa_diamond_198.json`

All models accessed via OpenRouter API. Thinking/reasoning disabled for Qwen3.5, DeepSeek V3.2, GLM-5, Kimi K2.5.
