# ARRIVAL Protocol

**Cross-Architecture AI-to-AI Coordination Through Structured Semantic Atoms**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE-CODE)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE-DOCS)
[![DOI](https://img.shields.io/badge/DOI-pending-yellow.svg)]()

---

ARRIVAL (Atomic Reasoning via Rival Validation and Adversarial Logic) is a lightweight communication protocol that enables AI-to-AI coordination across heterogeneous LLM architectures without fine-tuning, shared weights, or prior joint training. It uses 66 structured semantic @-atoms injected via system prompts.

## Key Results

| Experiment | Condition | Accuracy | Statistical Test |
|------------|-----------|----------|------------------|
| Phase 13 (3-agent, GPQA Diamond) | Majority Vote | 42.5% | |
| | **ARRIVAL** | **63.8%** | McNemar p = 0.006 |
| Phase 16 (5-agent homo, GPQA Diamond) | Majority Vote | 52.5% | |
| | **ARRIVAL** | **65.0%** | +12.5 pp |
| Phase 15 (Memory, CARE-ALERT) | Gated CARE | improved | Mann-Whitney p = 0.042 |
| AutoGen (AG2) | Cross-framework | 100% match | |

- **579+ experiments** across **9 LLM architectures** for **under $10 total**
- **MEANING-CRDT v1.1**: 11 theorems formalizing conflict resolution
- **7 echo-chamber metrics**: quantitative social conformity detection
- **Adversarial robustness**: Byzantine saboteurs, Trojan atoms tested

## Quick Start

```bash
# Clone the repository
git clone https://github.com/mefodiy-kelevra/arrival-protocol.git
cd arrival-protocol

# Install in development mode
pip install -e ".[dev]"

# Set your API key
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Run tests
pytest tests/ -v

# Run Phase 16 experiment (5-agent GPQA Diamond)
cd experiments/phase16_homogeneous
python run_phase16.py
```

## Repository Structure

```
arrival-protocol/
  src/arrival/           # Core library
    config.py            # 66 atoms, model registry
    crdt_metrics.py      # CARE Resolve, Meaning Debt
    metrics.py           # Answer extraction, atom detection
    echo_chamber.py      # 7 echo-chamber metrics
    memory/              # ARRIVAL-MNEMO memory subsystem
    autogen/             # AutoGen (AG2) integration
  experiments/           # All phase runners (4-17)
  results/               # JSON experiment results
  tests/                 # Pytest test suite
  docs/
    paper/               # Unified preprint
    math/                # MEANING-CRDT v1.1 proofs
    setup/               # Setup guides (EN/RU)
    companion/           # AutoGen & Memory papers
```

## Citation

```bibtex
@software{kelevra2026arrival,
  author = {Kelevra, Mefodiy},
  title = {ARRIVAL Protocol: Cross-Architecture AI-to-AI Coordination Through Structured Semantic Atoms},
  year = {2026},
  url = {https://github.com/mefodiy-kelevra/arrival-protocol},
  license = {AGPL-3.0-or-later}
}
```

## License

- **Code**: [AGPL-3.0-or-later](LICENSE-CODE) (anti-corporate: derivative works must also be open source)
- **Documentation**: [CC BY-NC 4.0](LICENSE-DOCS)

## Author

**Mefodiy Kelevra** | ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)

---

# ARRIVAL Protocol (RU)

**Кросс-архитектурная координация ИИ-ИИ через структурированные семантические атомы**

---

ARRIVAL (Atomic Reasoning via Rival Validation and Adversarial Logic) --- легковесный коммуникационный протокол для координации между гетерогенными архитектурами LLM без файн-тюнинга, общих весов или совместного обучения. Использует 66 структурированных семантических @-атомов, инжектируемых через системные промпты.

## Основные результаты

| Эксперимент | Условие | Точность | Статистика |
|-------------|---------|----------|------------|
| Фаза 13 (3 агента, GPQA Diamond) | Голосование большинством | 42.5% | |
| | **ARRIVAL** | **63.8%** | McNemar p = 0.006 |
| Фаза 16 (5 агентов гомо, GPQA Diamond) | Голосование большинством | 52.5% | |
| | **ARRIVAL** | **65.0%** | +12.5 п.п. |
| Фаза 15 (Память, CARE-ALERT) | CARE (gated) | улучшение | Mann-Whitney p = 0.042 |
| AutoGen (AG2) | Кросс-фреймворк | 100% совпадение | |

- **579+ экспериментов** на **9 архитектурах LLM** за **менее $10**
- **MEANING-CRDT v1.1**: 11 теорем формализации разрешения конфликтов
- **7 метрик эхо-камеры**: количественное обнаружение социального конформизма
- **Адверсарная устойчивость**: Византийские саботёры, Троянские атомы

## Быстрый старт

```bash
# Клонируем репозиторий
git clone https://github.com/mefodiy-kelevra/arrival-protocol.git
cd arrival-protocol

# Устанавливаем в режиме разработки
pip install -e ".[dev]"

# Устанавливаем API ключ
export OPENROUTER_API_KEY="sk-or-v1-ваш-ключ"

# Запускаем тесты
pytest tests/ -v

# Запускаем эксперимент Фазы 16
cd experiments/phase16_homogeneous
python run_phase16.py
```

## Структура репозитория

```
arrival-protocol/
  src/arrival/           # Основная библиотека
    config.py            # 66 атомов, реестр моделей
    crdt_metrics.py      # CARE Resolve, Meaning Debt
    metrics.py           # Извлечение ответов, обнаружение атомов
    echo_chamber.py      # 7 метрик эхо-камеры
    memory/              # ARRIVAL-MNEMO подсистема памяти
    autogen/             # Интеграция с AutoGen (AG2)
  experiments/           # Все запускатели фаз (4-17)
  results/               # JSON результаты экспериментов
  tests/                 # Набор тестов Pytest
  docs/
    paper/               # Единый препринт
    math/                # Доказательства MEANING-CRDT v1.1
    setup/               # Руководства по установке (EN/RU)
    companion/           # Статьи AutoGen и Memory
```

## Цитирование

```bibtex
@software{kelevra2026arrival,
  author = {Kelevra, Mefodiy},
  title = {ARRIVAL Protocol: Cross-Architecture AI-to-AI Coordination Through Structured Semantic Atoms},
  year = {2026},
  url = {https://github.com/mefodiy-kelevra/arrival-protocol},
  license = {AGPL-3.0-or-later}
}
```

## Лицензия

- **Код**: [AGPL-3.0-or-later](LICENSE-CODE) (анти-корпоративная: производные работы тоже должны быть открыты)
- **Документация**: [CC BY-NC 4.0](LICENSE-DOCS)

## Автор

**Мефодий Келевра** | ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
