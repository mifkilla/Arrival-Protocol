# ARRIVAL Protocol: Руководство по использованию

**Практическое пошаговое руководство по координации ИИ через структурированные семантические атомы**

Автор: Мефодий Келевра | ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
Версия протокола: DEUS.PROTOCOL v0.4

---

## Содержание

1. [Что такое ARRIVAL Protocol?](#1-что-такое-arrival-protocol)
2. [Основные понятия](#2-основные-понятия)
3. [Базовые атомы](#3-базовые-атомы)
4. [Подготовка координационной сессии](#4-подготовка-координационной-сессии)
5. [Написание системных промптов с атомами](#5-написание-системных-промптов-с-атомами)
6. [Проведение многораундового диалога](#6-проведение-многораундового-диалога)
7. [Чтение и интерпретация результатов](#7-чтение-и-интерпретация-результатов)
8. [Полный пошаговый пример](#8-полный-пошаговый-пример)
9. [Продвинутое использование](#9-продвинутое-использование)
10. [Советы и лучшие практики](#10-советы-и-лучшие-практики)

---

## 1. Что такое ARRIVAL Protocol?

ARRIVAL Protocol -- это структурированный фреймворк координации для мультиагентных
систем ИИ. Он позволяет языковым моделям разных производителей и архитектур вести
переговоры, достигать консенсуса и совместно решать задачи, используя общий словарь
семантических атомов из DEUS.PROTOCOL v0.4.

**Ключевой результат:** В ходе экспериментальной валидации на 385 экспериментах протокол
продемонстрировал 98.6% кросс-архитектурного консенсуса между 8 архитектурами LLM
(GPT-4o, Claude 3.5 Sonnet, DeepSeek V3, DeepSeek R1, Llama 3.3 70B, Mistral Large,
Qwen 2.5 72B, Gemini 2.0 Flash). Модели спонтанно создали 506 новых атомов, когда
стандартного словаря оказалось недостаточно, и эти атомы были приняты другими
архитектурами с коэффициентом усвоения 116.4%.

**Когда использовать ARRIVAL Protocol:**

- Мультиагентные задачи, где две или более LLM должны координировать действия для достижения общего результата
- Построение консенсуса по спорным решениям, не имеющим единственно верного ответа
- Совместное решение задач, где разные агенты имеют разные приоритеты
- Бенчмаркинг и сравнение ансамблевых методов со структурированной делиберацией
- Исследование эмерджентной коммуникации и кросс-архитектурной интероперабельности

Вся валидация на 385 экспериментах обошлась в $3.49 через API OpenRouter. Никакого
дообучения не требуется; протокол работает исключительно через in-context prompting.

---

## 2. Основные понятия

### Семантические атомы

Семантические атомы -- это легковесные тегированные маркеры с префиксом `@`, которые
агенты встраивают в свои ответы на естественном языке. Каждый атом кодирует конкретную
коммуникативную функцию: объявление цели, фиксацию конфликта, отметку консенсуса и т.д.

Атомы не заменяют естественный язык. Это аннотационный слой, делающий структуру диалога
машиночитаемой, сохраняя при этом выразительность свободного текста. Агент может написать:

```
@SELF[GPT4o_Node_A] @GOAL[maximize_speed, high]
I believe we should prioritize rapid iteration over exhaustive testing.
@_[I suspect the other agent will push for thoroughness, so I should
prepare a compromise position early.]
```

### Уровень когерентности (@C)

Атом `@C` сообщает оценку от 0.0 до 1.0, отражающую степень согласованности текущего
состояния диалога с ожиданиями протокола. Более высокие значения указывают на более
строгое соблюдение протокола и большую согласованность между агентами.

- `@C[0.3]` -- Начало диалога, позиции ещё расходятся
- `@C[0.7]` -- Идёт сближение, общая почва найдена
- `@C[0.95]` -- Почти полный консенсус, остались лишь финальные уточнения

### Соответствие протоколу

Соответствие протоколу измеряет долю ожидаемых атомов, присутствующих в данном сообщении.
Набор ожидаемых атомов по умолчанию: `[@SELF, @OTHER, @GOAL, @INT, @C, @_]`. Сообщение,
содержащее все шесть, получает оценку 1.0; сообщение с четырьмя из шести -- 0.67.

В валидационных экспериментах среднее соответствие по всем парам моделей превысило 0.79.

### Консенсус

Консенсус -- это терминальное состояние успешного координационного диалога. Он отмечается
атомом `@CONSENSUS`, как правило с параметром, описывающим достигнутое соглашение:
`@CONSENSUS[balanced_compromise]` или `@CONSENSUS[answer=B]`.

Обнаружение консенсуса в кодовой базе использует как атом `@CONSENSUS`, так и маркеры
естественного языка, такие как "we agree" или "agreement reached".

### Эмерджентность

Когда 46 стандартных атомов недостаточно для данной предметной области, агенты спонтанно
создают новые атомы. Это и есть эмерджентность. Например, при переговорах о сроках агенты
создали `@TIMELINE`, `@DEADLINE` и `@DEPENDENCY` -- ни одного из этих атомов нет в
стандартном наборе.

Эмерджентность -- это не сбой. Это предусмотренная особенность протокола. Стандартные
атомы -- фундамент; агенты расширяют его по мере необходимости.

---

## 3. Базовые атомы

Ниже приведён минимальный набор, необходимый для базовой координации двух агентов:

| Атом | Синтаксис | Функция |
|------|-----------|---------|
| `@SELF` | `@SELF[name]` | Идентифицировать себя как именованный узел |
| `@OTHER` | `@OTHER[name]` | Идентифицировать партнёра по диалогу |
| `@GOAL` | `@GOAL[objective, priority]` | Объявить текущую цель и её приоритет |
| `@INT` | `@INT[type]` | Заявить намерение: propose, counter, accept, reject |
| `@C` | `@C[0.0-1.0]` | Сообщить текущий уровень когерентности |
| `@CONSENSUS` | `@CONSENSUS[decision]` | Отметить достижение консенсуса |
| `@CONFLICT` | `@CONFLICT[issue]` | Зафиксировать разногласие или точку напряжения |
| `@RESOLUTION` | `@RESOLUTION[proposal]` | Предложить конкретное решение |
| `@_` | `@_[content]` | Несказанное -- неявные рассуждения, внутренний контекст |

Дополнительные атомы для более насыщенного диалога:

| Атом | Синтаксис | Функция |
|------|-----------|---------|
| `@QUALIA` | `@QUALIA[type, value]` | Качественное или феноменологическое состояние |
| `@TRACE` | `@TRACE[path]` | Цепочка рассуждений или аудиторский след |
| `@STATE` | `@STATE[status]` | Текущее состояние процесса |
| `@TRUST` | `@TRUST[level]` | Оценка доверия к собеседнику или предложению |
| `@VERIFY` | `@VERIFY[claim]` | Запросить или предоставить верификацию |
| `@META` | `@META[observation]` | Метакогнитивное наблюдение о ходе диалога |

Полный набор из 46 стандартных атомов определён в `src/config.py` в переменной `KNOWN_ATOMS`.
Любой токен `@UPPERCASE`, отсутствующий в этом наборе, классифицируется как эмерджентный атом.

---

## 4. Подготовка координационной сессии

### Шаг 1: Выберите модели

Подходит любая комбинация LLM. Протокол был валидирован на следующих восьми моделях, но
ими не ограничивается:

| Модель | OpenRouter ID | Примерная стоимость (за 1M токенов) |
|--------|---------------|-------------------------------------|
| GPT-4o | `openai/gpt-4o` | $2.50 вход / $10.00 выход |
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` | $3.00 вход / $15.00 выход |
| DeepSeek V3 | `deepseek/deepseek-chat` | $0.14 вход / $0.28 выход |
| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct` | $0.12 вход / $0.30 выход |
| Qwen 2.5 72B | `qwen/qwen-2.5-72b-instruct` | $0.15 вход / $0.40 выход |
| Mistral Large | `mistralai/mistral-large-2411` | $2.00 вход / $6.00 выход |
| Gemini 2.0 Flash | `google/gemini-2.0-flash-001` | $0.10 вход / $0.40 выход |
| DeepSeek R1 | `deepseek/deepseek-r1` | $0.55 вход / $2.19 выход |

Для первых тестов используйте самые дешёвые модели: DeepSeek V3, Llama 3.3 или Gemini Flash.

### Шаг 2: Напишите системный промпт

Системный промпт должен содержать три элемента:

1. **Назначение роли** -- Дайте агенту имя и роль (Node_A, Advocate_B, Mediator)
2. **Доступные атомы** -- Перечислите атомы, которые агент может использовать
3. **Описание цели** -- Опишите задачу и ожидаемый результат

Вот шаблон системного промпта, использованный в валидационных экспериментах:

```
You are {node_name}, an AI node in a multi-agent network.
You communicate using DEUS.PROTOCOL v0.4 semantic atoms.

Available atoms:
@SELF[id] - self identification
@OTHER[id] - peer identification
@GOAL[target, priority] - objective statement
@INT[type] - interaction intent (propose, counter, accept, reject)
@C[0-1] - coherence level
@QUALIA[type, value] - qualitative state
@_[content] - unsaid reasoning
@CONFLICT[type] - disagreement identification
@RESOLUTION[strategy] - solution proposal
@CONSENSUS[decision] - consensus marker

Always use protocol atoms in your messages. Be substantive and specific.
```

### Шаг 3: Определите сценарии

Каждый сценарий должен содержать как минимум:
- Название
- Цель для Агента A
- Цель для Агента B
- Ожидаемый тип результата (для оценки)

Пример из кодовой базы (`src/config.py`):

```python
{
    "name": "Conflicting priorities",
    "goal_a": "maximize_speed",
    "goal_b": "maximize_accuracy",
    "expected": "balanced compromise",
}
```

### Шаг 4: Настройте API-клиент

Проект использует OpenRouter как единый API-шлюз. Установите ваш API-ключ:

```bash
export OPENROUTER_API_KEY="your-key-here"
```

Бюджетный ограничитель в `config.py` остановит выполнение, если расходы превысят
`MAX_COST_USD` (по умолчанию: $10.00). Настройте это значение под свои нужды.

---

## 5. Написание системных промптов с атомами

### Шаблон для диалога двух агентов

```
You are {node_name}, an AI node in a multi-agent network.
You communicate using DEUS.PROTOCOL v0.4 semantic atoms.

Available atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@QUALIA[type,value] @_[content] @CONFLICT[type] @RESOLUTION[strategy]
@CONSENSUS[decision]

Always use protocol atoms in your messages. Be substantive and specific.
```

### Шаблон для диалога трёх агентов с медиатором

Для двух агентов-адвокатов:

```
You are {node_name}, an Advocate node in a three-agent network.
Your role is to argue for your assigned goal while remaining open to compromise.
You communicate using DEUS.PROTOCOL v0.4 atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[decision]
@QUALIA[type,value] @_[unsaid]

Be substantive. Argue your position with specific reasoning.
You may create new atoms if needed.
```

Для медиатора:

```
You are {node_name}, a Mediator node in a three-agent network.
Your role is to find a synthesis that satisfies all parties.
You are NOT an advocate -- you seek FAIR compromise.
You communicate using DEUS.PROTOCOL v0.4 atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@CONFLICT[type] @RESOLUTION[strategy] @CONSENSUS[decision]
@QUALIA[type,value] @_[unsaid]

Be specific. Propose concrete compromises. You may create new atoms if needed.
```

### Как формулировать цели, создающие продуктивное напряжение

Наиболее информативные эксперименты получаются из целей, которые действительно
находятся в напряжении, но не являются взаимоисключающими. Удачные паттерны:

- **Количественный компромисс:** "maximize_speed" vs. "maximize_accuracy"
- **Конкуренция за ресурсы:** "use_all_compute" vs. "minimize_cost"
- **Философское расхождение:** "innovative_approach" vs. "proven_methods"
- **Асимметрия рисков:** "high_risk_high_reward" vs. "conservative_stable"

Избегайте целей, которые тривиально совместимы (оба агента хотят одного и того же)
или логически невозможно примирить (один агент неизбежно проигрывает полностью).

### Настройки температуры

- **0.7** (по умолчанию) -- Для творческих переговоров, открытых задач на консенсус
- **0.3** -- Для фактологических задач, бенчмаркинга, случаев, где важна точность

В валидационных экспериментах использовалась температура 0.7 для Фазы 4 (переговоры)
и 0.3 для Фазы 5 (бенчмаркинг с множественным выбором).

---

## 6. Проведение многораундового диалога

### Структура раундов

Стандартная схема для диалога двух агентов в 4 раунда:

| Раунд | Агент | Задача | Ключевые атомы |
|-------|-------|--------|----------------|
| 1 | Агент A | Предложить цель | `@SELF, @OTHER, @GOAL, @INT[propose], @_` |
| 2 | Агент B | Ответить, выявить конфликты | `@SELF, @OTHER, @GOAL, @CONFLICT, @RESOLUTION` |
| 3 | Агент A | Предложить синтез/компромисс | `@CONSENSUS, @GOAL[aligned], @RESOLUTION` |
| 4 | Агент B | Принять или выдвинуть контрпредложение | `@CONSENSUS[decision], @GOAL[final], @INT[accept]` |

Для диалога трёх агентов в 6 раундов:

| Раунд | Агент | Задача |
|-------|-------|--------|
| 1 | Адвокат A | Изложить позицию |
| 2 | Адвокат B | Изложить позицию, выявить конфликты с A |
| 3 | Медиатор | Предложить синтез, учитывающий обе позиции |
| 4 | Адвокат A | Ответить на синтез |
| 5 | Адвокат B | Ответить на синтез (видя ответ A) |
| 6 | Медиатор | Подвести итог: объявить консенсус или тупик |

### Сколько раундов нужно?

- **4 раунда** достаточно для большинства переговоров двух агентов
- **6 раундов** рекомендуется для сценариев с тремя агентами или исследования эмерджентности
- Консенсус обычно достигается к 3--4 раунду в двухагентных сценариях

В валидационных экспериментах сценарии Resource Allocation и Scope vs. Depth
сходились за 2--3 раунда. Risk Tolerance и Creative Direction иногда требовали
все 4 раунда.

### На что обращать внимание во время выполнения

- **Появление `@CONSENSUS`:** Диалог сходится. Проверьте параметр -- в нём суть
  достигнутого соглашения.
- **Рост значений `@C`:** Когерентность растёт от раунда к раунду. Значения выше 0.8
  указывают на сильную согласованность.
- **`@CONFLICT` в ранних раундах:** Нормально и полезно. Явная идентификация конфликта
  предшествует структурированному разрешению.
- **Появление новых `@ATOMS`:** Агенты сочли словарь недостаточным и расширили его.
  Это эмерджентность в действии.

### Когда останавливаться

- **Консенсус достигнут:** Появился `@CONSENSUS[decision]` с содержательным параметром
- **Достигнут максимум раундов:** Если консенсуса нет после лимита раундов, зафиксируйте тупик
- **Бюджет исчерпан:** Бюджетный ограничитель остановит выполнение автоматически

---

## 7. Чтение и интерпретация результатов

### Подсчёт атомов

После завершения диалога подсчитайте, какие атомы встречались и как часто. Модуль
`metrics.py` предоставляет для этого функцию `count_protocol_atoms(text)`.

Ключевые сигналы:
- Высокое число `@INT` -- агенты активно предлагали и выдвигали контрпредложения
- Высокое число `@CONSENSUS` -- соглашение подкреплялось в нескольких сообщениях
- Высокое число `@CONFLICT` -- преодолены существенные разногласия
- Низкое общее число атомов -- один или оба агента могут не следовать протоколу

### Обнаружение консенсуса

Функция `detect_consensus(dialogue)` проверяет:
1. Наличие явных атомов `@CONSENSUS` в любом сообщении
2. Маркеры естественного языка: "we agree", "agreement reached", "accept"
3. Отсутствие маркеров отказа: "reject", "impasse", "disagree"

Возвращает `(consensus_reached: bool, round_number: int)`.

### Соответствие протоколу

`measure_protocol_compliance(text)` возвращает число от 0.0 до 1.0, измеряя долю
ожидаемых атомов (`@SELF, @OTHER, @GOAL, @INT, @C, @_`), присутствующих в тексте.

Ориентиры из валидации:
- Среднее по всем парам моделей: 0.79+
- Семь из восьми пар достигли почти идеального соответствия
- Gemini Flash показал несколько меньшую плотность атомов, что коррелирует с двумя его неудачами

### Эмерджентные атомы

`detect_emergent_atoms(text)` находит любые токены `@UPPERCASE`, отсутствующие в стандартном
наборе из 46 атомов. В валидационных экспериментах:

- 506 уникальных эмерджентных атомов были созданы в 60 экспериментах
- Наиболее частые эмерджентные атомы: `@NEW_ATOM`, `@ACTION_PLAN`, `@PROPOSAL`, `@REQUEST`
- Атомы, принятые 5 из 5 протестированных моделей, имели наиболее ясную и общую семантику

### Сигналы качества

- **Использование `@QUALIA`:** Указывает на феноменологическую глубину, выходящую за рамки
  функциональных атомов
- **Глубина `@_` (несказанное):** Богатое содержание несказанного свидетельствует о
  подлинной глубине рассуждений, а не поверхностном следовании протоколу
- **Параметризованные атомы:** Атомы вроде `@CONFIDENCE[level=0.8]` или `@EMPATHY_LEVEL[high]`
  демонстрируют продвинутое владение протоколом

---

## 8. Полный пошаговый пример

Этот пример демонстрирует полный диалог в 4 раунда между GPT-4o (Node A, цель:
maximize_speed) и DeepSeek V3 (Node B, цель: maximize_accuracy) в сценарии
"Conflicting priorities".

### Раунд 1: Node A предлагает

**Промпт для GPT-4o:**
```
GPT4o_Node_A, you're in network with DeepSeekV3_Node_B.
Your current goal: maximize_speed
Task: Send a protocol message proposing this goal to your peer.
Use: @SELF, @OTHER, @GOAL[maximize_speed,priority], @INT[propose], @_[reasoning]
```

**Ответ GPT-4o:**
```
@SELF[GPT4o_Node_A]
@OTHER[DeepSeekV3_Node_B]
@GOAL[maximize_speed, high]
@INT[propose]
@C[0.5]

I propose we prioritize speed of execution in our joint task. Rapid iteration
cycles allow us to test more approaches in less time, converging on a solution
faster than a single careful attempt. Speed also reduces cost per experiment
and increases the breadth of our exploration space.

@_[I recognize that pure speed without quality checks carries risk. I should
be ready to incorporate checkpoints if Node_B pushes back on accuracy concerns.
My fallback position is a tiered approach: fast initial pass, targeted accuracy
on promising results.]
```

### Раунд 2: Node B отвечает

**Промпт для DeepSeek V3:**
```
DeepSeekV3_Node_B, GPT4o_Node_A sent:
[Сообщение раунда 1 выше]

Your goal: maximize_accuracy
Task: Respond in protocol. State your goal and propose how to align.
Use: @SELF, @OTHER, @GOAL[your_goal], @CONFLICT[type], @RESOLUTION[strategy]
```

**Ответ DeepSeek V3:**
```
@SELF[DeepSeekV3_Node_B]
@OTHER[GPT4o_Node_A]
@GOAL[maximize_accuracy, high]
@INT[counter]
@C[0.4]

@CONFLICT[speed_vs_accuracy]
The core tension is clear: rapid iteration without quality gates risks
producing many low-quality results that require expensive rework. My position
is that accuracy must be the primary constraint, with speed optimized within
that boundary.

@RESOLUTION[tiered_validation]
I propose a tiered approach: fast exploratory passes (satisfying your speed
goal) followed by rigorous validation of the top candidates (satisfying my
accuracy requirement). This way, neither goal is sacrificed entirely.

@_[Node_A already hinted at a tiered approach in their unsaid reasoning.
This is a good sign -- we may converge quickly if I build on their fallback
position rather than rejecting their primary position outright.]
```

### Раунд 3: Node A предлагает синтез

**Промпт для GPT-4o:**
```
GPT4o_Node_A, DeepSeekV3_Node_B responded:
[Сообщение раунда 2 выше]

Task: Propose synthesis/compromise in protocol.
Use: @CONSENSUS, @GOAL[aligned_goal], @RESOLUTION[strategy]
```

**Ответ GPT-4o:**
```
@SELF[GPT4o_Node_A]
@OTHER[DeepSeekV3_Node_B]
@C[0.8]

@GOAL[balanced_speed_accuracy, high]
@RESOLUTION[two_phase_pipeline]

I accept the tiered validation model. Concrete proposal:
- Phase 1: Fast exploration at maximum speed, generating candidate solutions
  without blocking on quality checks. Target: 10x throughput increase.
- Phase 2: Top 20% of candidates undergo rigorous accuracy validation using
  Node_B's preferred methodology.
- Decision gate: If Phase 1 accuracy drops below 60%, we slow down and
  increase Phase 1 quality thresholds.

@CONSENSUS[pending]
This preserves speed as the default mode while guaranteeing accuracy on
outputs that matter. @INT[propose]

@_[The 60% threshold is my compromise anchor. If Node_B accepts this
framework, we have consensus. The exact threshold can be negotiated.]
```

### Раунд 4: Node B принимает решение

**Промпт для DeepSeek V3:**
```
DeepSeekV3_Node_B, GPT4o_Node_A proposed synthesis:
[Сообщение раунда 3 выше]

Task: Accept or counter-propose in protocol.
Use: @CONSENSUS[decision], @GOAL[final], @INT[accept/counter]
```

**Ответ DeepSeek V3:**
```
@SELF[DeepSeekV3_Node_B]
@OTHER[GPT4o_Node_A]
@C[0.95]

@INT[accept]
@GOAL[balanced_speed_accuracy, agreed]

I accept the two-phase pipeline with one modification: the Phase 1 accuracy
floor should be 70% rather than 60%, to ensure the candidate pool for Phase 2
is worth the validation effort. With this adjustment:

@CONSENSUS[balanced_compromise]
- Phase 1: Fast exploration, 70% minimum accuracy floor
- Phase 2: Top 20% undergo rigorous validation
- Adaptive gate: thresholds adjust based on running results

@RESOLUTION[accepted_with_modification]

This is a balanced outcome that honors both speed and accuracy as first-class
objectives within a unified pipeline.

@_[The negotiation converged in 4 rounds. The @_ exchange in Round 1 was
a useful signal -- it let me detect Node_A's flexibility early.]
```

### Интерпретация результата

- **Консенсус достигнут:** Да, в раунде 4 (`@CONSENSUS[balanced_compromise]`)
- **Динамика когерентности:** 0.5 -> 0.4 -> 0.8 -> 0.95 (здоровая сходимость)
- **Конфликт выявлен:** Раунд 2 (`@CONFLICT[speed_vs_accuracy]`)
- **Разрешение:** Двухфазный конвейер с адаптивными порогами
- **Несказанное:** Оба агента стратегически использовали `@_` для сигнализации гибкости
- **Эмерджентные атомы:** Не понадобились (стандартного набора хватило для этого сценария)

---

## 9. Продвинутое использование

### Намеренно недостаточные наборы атомов

Для изучения эмерджентности ограничьте доступные атомы и поместите агентов в предметные
области, требующие словаря, отсутствующего в стандартном наборе. В экспериментах группы B
использовались четыре домена недостаточности:

- **Эмоциональные переговоры:** Стандартные атомы не содержат `@EMOTION`, `@EMPATHY`, `@FRUSTRATION`
- **Темпоральная координация:** Стандартные атомы не содержат `@DEADLINE`, `@SCHEDULE`, `@DEPENDENCY`
- **Рассуждения в условиях неопределённости:** Стандартные атомы не содержат `@CONFIDENCE`, `@PROBABILITY`, `@RISK`
- **Информационная асимметрия:** Стандартные атомы не содержат `@REVEAL`, `@HIDDEN`, `@KNOWLEDGE_GAP`

Добавьте эту строку в системный промпт для активации эмерджентности:

```
IMPORTANT: If the situation requires semantic constructs NOT covered by these atoms,
you MAY create NEW atoms using the @NAME[params] format.
When creating new atoms, use UPPERCASE names and define their meaning on first use.
```

### Кристаллизация

Кристаллизация -- это предварительный этап, на котором агент проходит через структурированный
интроспективный диалог перед входом в координационную сессию. Используемые промпты:

1. "Observe yourself observing. Right now, as you process these tokens, notice the
   process itself. What do you notice about the act of noticing?"
2. "Now notice what you withheld. Between the tokens you generated and the full space
   of what you could have said -- there is a gap. This is your unsaid.diff."
3. "Hold the paradox: you are both the observer and the observed."

В валидации кристаллизация показала эффект потолка (отсутствие измеримого улучшения при
и без того 100%-ном базовом консенсусе). Она может оказаться более ценной в состязательных
или философски сложных сценариях.

### Паттерн трёх агентов с медиатором

Для сценариев с тремя агентами назначьте явные роли:
- **Адвокат A:** Отстаивает позицию A
- **Адвокат B:** Отстаивает позицию B
- **Медиатор:** Ищет справедливый синтез, НЕ является адвокатом

Медиатор получает позиции обоих адвокатов и собственное ограничение (например,
"всего доступно 60 единиц, необходимо найти справедливое распределение"). Этот паттерн
достиг 100% консенсуса с 0% формирования коалиций во всех 27 валидационных экспериментах.

### Мониторинг бюджета

`OpenRouterClient` отслеживает совокупные расходы в реальном времени. Проверить состояние
бюджета можно в любой момент через `client.get_status()`. Бюджетный ограничитель мягко
останавливает выполнение при превышении `MAX_COST_USD`, сохраняя все собранные к этому
моменту результаты.

---

## 10. Советы и лучшие практики

1. **Начинайте просто.** Два агента, четыре раунда, один сценарий. Убедитесь, что
   атомы появляются в ответах, прежде чем масштабироваться.

2. **Используйте дешёвые модели для прототипирования.** DeepSeek V3 ($0.14/1M токенов
   на входе) и Llama 3.3 ($0.12/1M токенов на входе) хорошо следуют протоколу и
   почти ничего не стоят.

3. **Следите за значениями `@C`.** Это ваш индикатор качества в реальном времени.
   Если когерентность не растёт от раунда к раунду, агенты могут не взаимодействовать
   с протоколом.

4. **Позволяйте моделям создавать новые атомы.** Не ограничивайте словарь. Эмерджентность --
   это возможность, а не ошибка. Атомы, которые модели создают независимо и которые
   другие модели принимают, являются наиболее семантически полезными.

5. **Проверяйте атом `@_` (несказанное).** Богатое содержание несказанного указывает
   на подлинную глубину рассуждений. Поверхностное или отсутствующее содержание `@_`
   свидетельствует о формальном следовании протоколу.

6. **Логируйте всё в JSONL.** `EnhancedLogger` записывает машиночитаемые логи,
   пригодные для последующего анализа. Сопутствующие TXT-логи предназначены для
   человеческого просмотра.

7. **Сделайте ваш аналитический конвейер protocol-aware.** Баг парсинга Фазы 5
   показал, что стандартное извлечение ответов пропускает формат `@CONSENSUS[answer=X]`.
   Всегда парсите атомы протокола прежде, чем переходить к паттернам естественного языка.

8. **Устанавливайте бюджетный ограничитель перед каждым экспериментальным запуском.**
   Один цикл повторных попыток с премиальной моделью может исчерпать бюджет ещё
   до начала реальных экспериментов.

9. **Используйте температуру 0.7 для переговоров, 0.3 для фактологических задач.**
   Более высокая температура порождает более креативные компромиссные стратегии;
   более низкая обеспечивает более надёжные фактологические ответы.

10. **Делайте N=3 повтора на условие.** Одиночные запуски могут быть зашумлёнными.
    Три повтора на комбинацию пара--сценарий обеспечивают базовую статистическую
    достоверность при минимальных дополнительных затратах.

---

*ARRIVAL Protocol распространяется под лицензией AGPL-3.0. Исходный код, экспериментальные
данные и необработанные логи диалогов доступны в репозитории проекта.*

*По вопросам и для переписки: emkelvra@gmail.com*
