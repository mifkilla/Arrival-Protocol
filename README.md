# ARRIVAL Protocol

**Cross-Architecture AI-to-AI Coordination Through Structured Semantic Atoms**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE-CODE)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE-DOCS)
[![DOI](https://img.shields.io/badge/DOI-pending-yellow.svg)]()

> 2,200+ experiments across 17 LLM architectures, 23 phases, for under $95. 86.4% GPQA Diamond (vs 65% SOTA debate). 0%->100% GovSim survival (Fisher p=0.008). Zero training required.

---

## What is ARRIVAL Protocol?

ARRIVAL (Atomic Reasoning via Rival Validation and Adversarial Logic) is a lightweight communication protocol that enables AI-to-AI coordination across heterogeneous LLM architectures without fine-tuning, shared weights, or prior joint training. It uses 66 structured semantic @-atoms injected via system prompts (DEUS.PROTOCOL v0.5).

**Key insight**: When given a shared atomic vocabulary, LLMs from completely different architectures can coordinate structured reasoning — they just *understand* the protocol.

## Key Results

| Experiment | Condition | Result | Statistical Test |
|------------|-----------|--------|------------------|
| Phase 13 (3-agent, GPQA Diamond) | Majority Vote | 42.5% | |
| | **ARRIVAL** | **63.8%** | McNemar p = 0.006 |
| Phase 22 (CGD-3, GPQA Diamond 198q) | Solo best model | 69.2% | |
| | **CGD-3** | **86.4%** | +17.2 pp |
| Phase 23 (CGD-7, GPQA Diamond 20q) | Solo best model | 75.0% | |
| | **CGD-7** | **86.9%** | |
| Phase 19 (GovSim Cooperation) | Baseline LLMs | 0% survival | |
| | **ARRIVAL + R4** | **100% survival** | Fisher p = 0.008 |
| Phase 15 (CARE-ALERT) | Global injection | CARE = 0.881 | |
| | **Gated CARE-ALERT** | **CARE = 0.923** | Mann-Whitney p = 0.042 |

- **2,200+ experiments** across **17 LLM architectures** for **under $95 total**
- **MEANING-CRDT v1.1**: 11 theorems formalizing conflict resolution (DOI: 10.5281/zenodo.18702383)
- **7 echo-chamber metrics**: quantitative social conformity detection
- **Adversarial robustness**: Byzantine saboteurs, Trojan atoms tested
- **Confidence-Gated Debate (CGD)**: 86.4% GPQA Diamond accuracy

## Ecosystem

| Component | Description | Preprint |
|-----------|-------------|----------|
| **ARRIVAL Protocol** | Core coordination framework, 23 experimental phases | [`docs/PREPRINT.md`](docs/PREPRINT.md) |
| **MEANING-CRDT v1.1** | Mathematical foundation (11 theorems, CARE Resolve) | [`docs/math/MEANING-CRDT_v1.1.md`](docs/math/MEANING-CRDT_v1.1.md) |
| **ARRIVAL-MNEMO** | Persistent memory with CARE-ALERT intervention | [`crdt-memory/docs/PREPRINT_MEMORY.md`](crdt-memory/docs/PREPRINT_MEMORY.md) |
| **Synthesis Paper** | Unified theory of semantic coordination | [`docs/PREPRINT_SYNTHESIS.md`](docs/PREPRINT_SYNTHESIS.md) |
| **AutoGen (AG2)** | Framework-agnostic validation | [`docs/companion/AUTOGEN_PAPER.md`](docs/companion/AUTOGEN_PAPER.md) |

## Repository Structure

```
arrival-protocol/
  src/arrival/               # Core library
    config.py                # 66 atoms, model registry (DEUS v0.5)
    crdt_metrics.py          # CARE Resolve, Meaning Debt
    metrics.py               # Answer extraction, atom detection
    echo_chamber.py          # 7 echo-chamber metrics
    openrouter_client.py     # OpenRouter API client
    memory/                  # ARRIVAL-MNEMO memory subsystem
    autogen/                 # AutoGen (AG2) integration
  experiments/               # All phase runners (4-23)
    phase04_basic/           # Cross-architecture validation
    phase05_adversarial/     # Adversarial atoms
    phase06_byzantine/       # Byzantine saboteurs
    phase13_gpqa/            # GPQA Diamond benchmark
    phase14_memory_global/   # Memory injection (negative result)
    phase15_care_alert/      # Gated CARE-ALERT
    phase19_govsim/          # GovSim cooperation
    phase22_confidence_gated/ # CGD-3
    phase23_scaled_cgd/      # CGD-7
    autogen_validation/      # AG2 framework test
  results/                   # JSON experiment results
  crdt-memory/               # Self-contained CRDT memory component
    src/                     # Memory store, CARE-ALERT, schema
    docs/                    # PREPRINT_MEMORY.md, MEMORY_CRDT_SPEC.md
    tests/                   # CRDT property tests
  docs/
    PREPRINT.md              # Main unified preprint
    PREPRINT_SYNTHESIS.md    # Synthesis preprint (theory-first)
    math/                    # MEANING-CRDT v1.1 proofs
    companion/               # AutoGen & Memory papers
    setup/                   # Setup guides (EN/RU)
    reports/                 # Phase-specific reports
  tests/                     # Pytest test suite
  pyproject.toml             # Python packaging
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/DreamOS-Network/Arrival-Protocol.git
cd arrival-protocol

# Install in development mode
pip install -e ".[dev]"

# Set your API key
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Run tests
pytest tests/ -v

# Run Phase 22 experiment (CGD on GPQA Diamond)
cd experiments/phase22_confidence_gated
python run_cgd_full.py
```

### Manual Reproduction (No Code)

You can reproduce ARRIVAL Protocol experiments **without any code** using an LLM chat interface. See [`docs/setup/USAGE_GUIDE_EN.md`](docs/setup/USAGE_GUIDE_EN.md) for instructions.

## Models Tested (17 Architectures)

| Model | Provider | Params | Phases |
|-------|----------|--------|--------|
| GPT-4o | OpenAI | Undisclosed | 4--12 |
| GPT-4.1 | OpenAI | Undisclosed | 18, 20--22 |
| Claude 3.5 Sonnet | Anthropic | Undisclosed | 4--12 |
| Claude Sonnet 4.5 | Anthropic | Undisclosed | 18 |
| Claude Sonnet 4.6 | Anthropic | Undisclosed | 23 |
| DeepSeek V3 | DeepSeek | 671B MoE | 4--13 |
| DeepSeek R1 | DeepSeek | 671B MoE | 4--13 |
| DeepSeek V3.2 | DeepSeek | MoE | 18, 23 |
| Llama 3.3 70B | Meta | 70B | 4--12 |
| Qwen 2.5 72B | Alibaba | 72B | 4--12 |
| Qwen3-235B | Alibaba | 235B MoE | 13, 16, 17 |
| Qwen3.5-397B | Alibaba | 397B MoE | 23 |
| Mistral Large | Mistral AI | Undisclosed | 4--12 |
| Mistral Large 3 | Mistral AI | Undisclosed | 18 |
| Gemini 2.0 Flash | Google | Undisclosed | 4--12 |
| Gemini 3 Flash | Google | Undisclosed | 18, 20--23 |
| Grok 4.1 Fast | xAI | Undisclosed | 18, 20--23 |
| Kimi K2.5 | Moonshot AI | Undisclosed | 23 |
| GLM-5 | Zhipu AI | Undisclosed | 23 |

All models accessed through [OpenRouter](https://openrouter.ai/) unified API.

## Cost Summary

| Phase | Experiments | API Calls | Cost (USD) |
|-------|-------------|-----------|------------|
| 4--5 (validation) | 485 | ~2,000 | ~$2.00 |
| 6--12 (adversarial, scaling) | ~80 | ~500 | ~$1.50 |
| 13 (GPQA Diamond 3-agent) | 80 | ~320 | ~$1.00 |
| 14--15 (memory, CARE-ALERT) | ~40 | ~200 | ~$0.50 |
| 16 (5-agent homogeneous) | 200+ | 640 | $1.92 |
| 17 (solo CoT baselines) | 200 | 200 | $0.50 |
| 18 (applied tasks) | 6 | ~66 | $0.77 |
| 19 (GovSim cooperation) | 25 | 2,165 | $5.76 |
| 20 (full GPQA, mid-tier) | 198 | ~1,782 | $7.43 |
| 21 (frontier models) | 792 | ~1,386 | $9.63 |
| 22 (CGD-3, 198q) | 198 | ~692 | $5.72 |
| 23 (CGD-7, 198q) | 198 | ~1,822 | $11.35 |
| AutoGen (AG2) | 16 | ~100 | $0.02 |
| **Total** | **2,200+** | **~14,500** | **< $95** |

Average cost per experiment: ~$0.04.

## Citation

```bibtex
@software{kelevra2026arrival,
  author       = {Kelevra, Mefodiy},
  title        = {{ARRIVAL Protocol: Cross-Architecture AI-to-AI
                   Coordination Through Structured Semantic Atoms}},
  year         = 2026,
  version      = {2.0.0},
  license      = {AGPL-3.0-or-later},
  url          = {https://github.com/DreamOS-Network/Arrival-Protocol}
}
```

See [CITATION.cff](CITATION.cff) for the machine-readable citation file.

## Documentation

- **[Main Preprint](docs/PREPRINT.md)** — Unified paper covering all 23 phases
- **[Synthesis Preprint](docs/PREPRINT_SYNTHESIS.md)** — Theory-first synthesis paper
- **[Memory Preprint](crdt-memory/docs/PREPRINT_MEMORY.md)** — ARRIVAL-MNEMO companion paper
- **[MEANING-CRDT v1.1](docs/math/MEANING-CRDT_v1.1.md)** — Mathematical foundation
- **[Atom Dictionary](docs/ATOM_DICTIONARY.md)** — Complete reference of 66 standard atoms
- **[Setup Guide](docs/setup/SETUP_EN.md)** — Installation and configuration
- **[Usage Guide](docs/setup/USAGE_GUIDE_EN.md)** — How to use in your projects
- **[FAQ](docs/FAQ.md)** — Frequently asked questions

## License

- **Code**: [AGPL-3.0-or-later](LICENSE-CODE) (anti-corporate: derivative works must also be open source)
- **Documentation**: [CC BY-NC 4.0](LICENSE-DOCS)

## Author

**Mefodiy Kelevra** | ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)

---

# ARRIVAL Protocol (RU)

**Кросс-архитектурная координация ИИ-ИИ через структурированные семантические атомы**

---

ARRIVAL (Atomic Reasoning via Rival Validation and Adversarial Logic) --- легковесный коммуникационный протокол для координации между гетерогенными архитектурами LLM без файн-тюнинга, общих весов или совместного обучения. Использует 66 структурированных семантических @-атомов (DEUS.PROTOCOL v0.5), инжектируемых через системные промпты.

## Основные результаты

| Эксперимент | Условие | Результат | Статистика |
|-------------|---------|-----------|------------|
| Фаза 13 (3 агента, GPQA Diamond) | Голосование большинством | 42.5% | |
| | **ARRIVAL** | **63.8%** | McNemar p = 0.006 |
| Фаза 22 (CGD-3, GPQA Diamond 198q) | Лучшая соло модель | 69.2% | |
| | **CGD-3** | **86.4%** | +17.2 п.п. |
| Фаза 19 (GovSim кооперация) | Базовые LLM | 0% выживание | |
| | **ARRIVAL + R4** | **100% выживание** | Fisher p = 0.008 |

- **2,200+ экспериментов** на **17 архитектурах LLM** за **менее $95**
- **MEANING-CRDT v1.1**: 11 теорем формализации разрешения конфликтов
- **7 метрик эхо-камеры**: количественное обнаружение социального конформизма
- **Confidence-Gated Debate (CGD)**: 86.4% точности на GPQA Diamond

## Быстрый старт

```bash
git clone https://github.com/DreamOS-Network/Arrival-Protocol.git
cd arrival-protocol
pip install -e ".[dev]"
export OPENROUTER_API_KEY="sk-or-v1-ваш-ключ"
pytest tests/ -v
```

## Лицензия

- **Код**: [AGPL-3.0-or-later](LICENSE-CODE) (анти-корпоративная: производные работы тоже должны быть открыты)
- **Документация**: [CC BY-NC 4.0](LICENSE-DOCS)

## Автор

**Мефодий Келевра** | ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
