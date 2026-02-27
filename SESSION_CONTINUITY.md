# ARRIVAL Release — Session Continuity File
# ==========================================
# Этот файл обновляется на КАЖДОМ этапе работы.
# Если сессия прервётся — новый Claude читает этот файл и продолжает.
# Автор проекта: Mefodiy Kelevra (MiF), ORCID: 0009-0003-4153-392X

## ПОСЛЕДНЕЕ ОБНОВЛЕНИЕ: 2026-02-27 04:00 UTC

---

## МИССИЯ

Создать unified publication-ready repository `E:\Arrival Release\` для ARRIVAL Protocol.
Цель: Zenodo preprint уровня "best paper candidate" с:
- Полной кодовой базой (539+ экспериментов из 5 репозиториев)
- Phase 17: Solo CoT baseline (ответ на критику Wang et al.)
- Phase 18: Прикладной эксперимент (Solo vs ARRIVAL vs ARRIVAL+Memory на реальных задачах)
- Профессиональным preprint с результатами всех фаз

---

## ИСТОЧНИКИ (5 репозиториев + 1 документ)

| Репозиторий | Путь | Содержит |
|-------------|------|----------|
| Arrival Protocol | `E:\Arrival Protocol\` | Фазы 4-5, 46 атомов, 385 экспериментов |
| Arrival CRDT | `E:\Arrival CRDT\` | MEANING-CRDT v1.1, Фазы 6-13, 16 |
| Arrival Memory | `E:\Arrival Memory\` | ARRIVAL-MNEMO, Фазы 14-15, CARE-ALERT |
| Arrival Autogen | `E:\Arrival Autogen\` | AG2 framework-agnostic, 16 экспериментов |
| Dream OS Git | `E:\Dream OS Git\` | Meta-project, Dream OS paper |
| MEANING-CRDT math | `C:\Users\revol\Documents\Drea, OS 2.0\MEANING-CRDT.md` | Математика CRDT |

**API ключ OpenRouter:** `E:\Arrival CRDT\phase16_homogeneous\.env`

---

## ТЕКУЩИЙ СТАТУС (обновлять при каждом этапе!)

### Scaffold (repo structure)
- [x] Директория `E:\Arrival Release\` создана
- [x] src/arrival/ — все модули скопированы и рефакторены
- [x] experiments/ — все фазы 4-16 скопированы
- [x] docs/ — preprint, companion papers, setup guides
- [x] pyproject.toml, pip install -e . работает
- [x] 176 тестов проходят
- [x] README.md, CITATION.cff, .zenodo.json, CONTRIBUTING.md
- [x] LICENSE-CODE (AGPL-3.0), LICENSE-DOCS (CC BY-NC 4.0)
- [ ] Initial git commit (файлы staged, но НЕ закоммичены)

### Phase 17: Solo CoT Baseline (MCQ) — ЗАВЕРШЁН
- [x] Запуск run_phase17.py (40 вопросов × 5 runs) — ЗАВЕРШЁН 2026-02-27 06:56 UTC+3
- [x] Результат JSON: `results/phase17_results_20260226_215354.json`
- [x] Solo CoT MV: **70.0% (28/40)** vs ARRIVAL **65.0% (26/40)** — Fisher p=0.812 (ns)
- [x] Per-domain: physics 85.7%, chemistry 42.9%, biology 66.7%, interdisciplinary 100%
- [x] Cost: $0.50, 200 API calls
- [x] Результаты добавлены в preprint (все TBD заменены)

### Phase 18: Прикладной эксперимент (2 задания × 3 условия) — ЗАВЕРШЁН

#### Задание 1: Security Audit (аналитическое)
- [x] buggy_app.py создан (10 намеренных багов)
- [x] bugs_ground_truth.json создан
- [x] memory_seeds_audit.json создан
- [x] Condition A: Solo Claude 4.5 Sonnet → 10/10 bugs, $0.1196
- [x] Condition B: ARRIVAL (5 моделей, без памяти) → 10/10 bugs, $0.1398
- [x] Condition C: ARRIVAL + CARE-ALERT Memory → 10/10 bugs, $0.1401, 6 memories injected
- [x] evaluate.py — evaluation.json сохранён

#### Задание 2: Code Generation — REST API (конструктивное)
- [x] specification.md создан
- [x] test_suite_phase18.py написан (15 объективных тестов)
- [x] memory_seeds_api.json создан
- [x] Condition A: Solo Claude 4.5 Sonnet → 9/15 tests (60%), $0.1241
- [x] Condition B: ARRIVAL (5 моделей, без памяти) → 8/15 tests (53%), $0.1274
- [x] Condition C: ARRIVAL + CARE-ALERT Memory → 7/15 tests (47%), $0.1228
- [x] evaluate.py — evaluation.json сохранён

#### Phase 18 Общее
- [x] comparison_report.md — сводная таблица
- [x] PHASE18_REPORT.md — финальный отчёт

### Preprint
- [x] Phase 17 секция обновлена (Section 9) — все TBD заменены реальными данными
- [x] Phase 18 секция добавлена (Section 10)
- [x] Abstract обновлён (Phase 17 + Phase 18 results)
- [x] Discussion обновлён (CARE as task discriminator, cost efficiency, Wang et al. response)
- [x] Limitations обновлены (MCQ-only → limited open-ended)
- [x] Conclusion обновлён

### Git
- [x] Initial commit (f093563 + 6a7d6f8)
- [ ] Phase 17 commit
- [ ] Tag v1.0.0

---

## МОДЕЛИ ДЛЯ PHASE 18

### Solo baseline
| Роль | Модель | OpenRouter ID | $/1M in | $/1M out |
|------|--------|---------------|---------|----------|
| Solo | Claude Sonnet 4.5 | `anthropic/claude-sonnet-4.5` | $3.00 | $15.00 |

### ARRIVAL Swarm (5 гетерогенных моделей)
| Роль | Модель | OpenRouter ID | $/1M in | $/1M out |
|------|--------|---------------|---------|----------|
| Alpha (аналитик) | GPT-4.1 | `openai/gpt-4.1` | $2.00 | $8.00 |
| Beta (скептик) | DeepSeek V3.2 | `deepseek/deepseek-v3.2` | $0.25 | $0.40 |
| Gamma (латерал) | Mistral Large 3 | `mistralai/mistral-large-2512` | $0.50 | $1.50 |
| Delta (строгий) | Gemini 3 Flash | `google/gemini-3-flash-preview` | $0.50 | $3.00 |
| Epsilon (синтезатор) | Grok 4.1 Fast | `x-ai/grok-4.1-fast` | $0.20 | $0.50 |

---

## ОЖИДАЕМЫЙ БЮДЖЕТ

| Этап | Est. cost |
|------|-----------|
| Phase 17 (200 calls) | ~$0.40 |
| Phase 18 Task 1 (23 calls × 3) | ~$0.75-1.35 |
| Phase 18 Task 2 (23 calls × 3) | ~$0.85-1.55 |
| **ИТОГО** | **~$2.00-3.30** |

---

## ARRIVAL PROTOCOL — 4-ROUND STRUCTURE

```
Round 1: INDEPENDENT ANALYSIS (5 API calls)
  Каждая модель получает задание + свой persona prompt
  Отвечает самостоятельно, без знания о других

Round 2: CROSS-CRITIQUE (5 API calls)
  Каждая модель видит ответы 4 других (truncated)
  Использует @CONSENSUS[finding=...] или @CONFLICT[issue=...]
  Должна найти слабости в чужих аргументах

Round 3: CRDT OVERLAY (0 API calls, computation only)
  compute_care_resolve(dialogue) → CARE score
  compute_meaning_debt(dialogue) → MD score
  Для условия C: CARE-ALERT проверяет нужна ли memory injection

Round 4: FINAL SYNTHESIS (1 API call)
  Alpha получает все критики из R2 + (опционально) memory alert
  Создаёт финальный синтезированный ответ
```

---

## КЛЮЧЕВЫЕ ФАЙЛЫ В RELEASE REPO

| Файл | Назначение |
|------|-----------|
| `src/arrival/crdt_metrics.py` | CARE Resolve, Meaning Debt, Position extraction |
| `src/arrival/metrics.py` | Answer extraction, atom detection |
| `src/arrival/memory/care_alert.py` | CARE-ALERT gating logic |
| `src/arrival/memory/schema.py` | 4-layer memory schema |
| `src/arrival/openrouter_client.py` | OpenRouter API client |
| `src/arrival/config.py` | 66 atoms, model costs |
| `docs/paper/ARRIVAL_PROTOCOL.md` | Main preprint |
| `experiments/phase17_solo_cot/run_phase17.py` | Phase 17 runner |
| `experiments/phase18_applied/` | Phase 18 (NEW) |

---

## ЕСЛИ СЕССИЯ ПРЕРВАЛАСЬ — ЧТО ДЕЛАТЬ

1. Прочитай этот файл: `E:\Arrival Release\SESSION_CONTINUITY.md`
2. Посмотри чекбоксы выше — что уже сделано, что нет
3. Прочитай план: `C:\Users\revol\.claude\plans\valiant-gliding-moore.md`
4. Прочитай memory: `C:\Users\revol\.claude\projects\E--Dream-OS-Git\memory\MEMORY.md`
5. Продолжай с первого незавершённого чекбокса
6. Пиши подробные объяснения в чат на каждом шаге
7. Обновляй этот файл после каждого завершённого этапа

---

## РЕЗУЛЬТАТЫ (заполняется по мере выполнения)

### Phase 17 Results
```
Solo CoT per-run accuracy: 61.0% (122/200)
Solo CoT MV (5 runs):      70.0% (28/40)
Solo CoT Oracle (best-5):  85.0% (34/40)
Phase 16 MV baseline:      52.5% (21/40)
Phase 16 ARRIVAL:           65.0% (26/40)

Fisher p (Solo MV vs ARRIVAL): 0.812 (NOT significant)
Fisher p (Solo MV vs P16 MV):  0.168 (NOT significant)

Per-domain: physics 85.7%, chemistry 42.9%, biology 66.7%, interdisciplinary 100%
Cost: $0.50, API calls: 200

KEY INSIGHT: Solo CoT MV (70%) > ARRIVAL (65%) by 5pp, but NOT statistically significant.
ARRIVAL provides transparency, audit trails, CARE metrics that solo cannot.
```

### Phase 18 Task 1: Security Audit Results
```
Condition A (Solo Claude 4.5):  10/10 bugs, 2/2 bonus, $0.1196, 1 call
Condition B (ARRIVAL 5-model):  10/10 bugs, 2/2 bonus, $0.1398, 11 calls, CARE=0.500
Condition C (ARRIVAL+Memory):   10/10 bugs, 2/2 bonus, $0.1401, 11 calls, CARE=0.500, 6 memories injected

KEY INSIGHT: 5 heterogeneous models match frontier solo at same price ($0.14 vs $0.12)
CARE-ALERT correctly triggered (CARE 0.5 < 0.7 threshold)
```

### Phase 18 Task 2: Code Generation Results
```
Condition A (Solo Claude 4.5):  9/15 tests (60%), $0.1241, 259 lines, 1 call
Condition B (ARRIVAL 5-model):  8/15 tests (53%), $0.1274, 180 lines, 11 calls, CARE=0.979
Condition C (ARRIVAL+Memory):   7/15 tests (47%), $0.1228, 166 lines, 11 calls, CARE=0.973

Solo advantage on code synthesis (+1-2 tests), but ALL conditions cost ~$0.12-0.13
CARE-ALERT correctly suppressed (CARE 0.97 > 0.7 threshold — no memory needed)
CARE discriminates task types: 0.50 (analytical) vs 0.97 (constructive)
```

### Phase 18 Total Cost
```
Grand total: $0.7738 (6 conditions × 2 tasks)
```
