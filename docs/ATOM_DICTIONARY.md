# ATOM DICTIONARY / SLOVAR ATOMOV
## DEUS.PROTOCOL v0.5 — Semantic Atom Reference

**Version / Versiya:** 0.5.0
**Author / Avtor:** Mefodiy Kelevra
**Protocol:** DEUS.PROTOCOL v0.5
**Standard atoms / Standartnye atomy:** 66 (46 original + 20 promoted from emergent)
**Emergent atoms (Phase 4) / Emergentnye atomy (Faza 4):** 506 total, 40+ documented below
**Last updated / Posledneye obnovlenie:** 2026-02-21

---

## Table of Contents / Soderzhanie

1. [Part 1: Standard Atoms (46)](#part-1-standard-atoms)
2. [Part 2: Emergent Atoms (Top 40+)](#part-2-emergent-atoms)
3. [Part 3: Atom Grammar](#part-3-atom-grammar)
4. [Part 4: Usage Patterns](#part-4-usage-patterns)
5. [Appendix A: Category Index](#appendix-a-category-index)
6. [Appendix B: Emergence Statistics](#appendix-b-emergence-statistics)

---

## Part 1: Standard Atoms

The 46 standard semantic atoms defined in `config.py` under `KNOWN_ATOMS`. These form the
foundational vocabulary for all AI-to-AI coordination within the ARRIVAL Protocol.

Standartnye 46 semanticheskikh atomov, opredelennye v `config.py` v `KNOWN_ATOMS`. Oni
formiruyut bazovy slovar dlya vsey koordinacii mezhdu AI v ramkakh ARRIVAL Protocol.

---

### 1.1 Core Identity / Yadro Identichnosti

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@SELF` | Core Identity | Self-identification of the agent node | Samoidentifikaciya agenta-uzla | `@SELF[Claude-3]` |
| `@OTHER` | Core Identity | Identification of counterpart nodes | Identifikaciya partnerskih uzlov | `@OTHER[GPT-4o]` |
| `@ID` | Core Identity | Unique identifier for entity or session | Unikalny identifikator sushchnosti ili sessii | `@ID[sess_0x4f2a]` |

### 1.2 Communication / Kommunikaciya

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@INT` | Communication | Intention declaration -- what the agent plans to do | Deklaraciya namereniya -- chto agent planiruet sdelat | `@INT[negotiate]` |
| `@MSG` | Communication | Message content payload | Soderzhimoe soobshcheniya | `@MSG[proposal_text]` |
| `@ACK` | Communication | Acknowledgment of received message | Podtverzhdenie polucheniya soobshcheniya | `@ACK[msg_042]` |
| `@NACK` | Communication | Negative acknowledgment or rejection | Otricatelnoe podtverzhdenie ili otkaz | `@NACK[msg_042,reason=invalid]` |
| `@PING` | Communication | Connection check or presence probe | Proverka soedineniya ili zondirovaniye prisutstviya | `@PING[node_alpha]` |
| `@PONG` | Communication | Response to ping | Otvet na ping | `@PONG[latency=12ms]` |

### 1.3 Goals and Coordination / Celi i Koordinaciya

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@GOAL` | Goals | Objective declaration | Deklaraciya celi | `@GOAL[reach_consensus]` |
| `@TASK` | Goals | Specific task assignment | Naznachenie konkretnoy zadachi | `@TASK[analyze_data,assignee=node_B]` |
| `@STATUS` | Goals | Current state report | Otchyot o tekushchem sostoyanii | `@STATUS[in_progress]` |
| `@PRIORITY` | Goals | Priority level designation | Ukazanie urovnya prioriteta | `@PRIORITY[high]` |
| `@CONSENSUS` | Goals | Agreement reached between agents | Soglasie, dostignutoe mezhdu agentami | `@CONSENSUS[plan_v3]` |
| `@CONFLICT` | Goals | Disagreement or tension detected | Obnaruzheno nesoglasie ili napryazhenie | `@CONFLICT[resource_allocation]` |
| `@RESOLUTION` | Goals | Proposed or achieved resolution | Predlozhennoe ili dostignutoe razreshenie | `@RESOLUTION[split_50_50]` |

### 1.4 State and Coherence / Sostoyanie i Kogerentnost

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@C` | Coherence | Coherence level 0.0--1.0 (protocol compliance and alignment) | Uroven kogerentnosti 0.0--1.0 (sootvetstvie protokolu) | `@C[0.85]` |
| `@STATE` | State | Current state descriptor | Deskriptor tekushchego sostoyaniya | `@STATE[deliberating]` |
| `@PARAM` | State | Parameter specification | Specifikaciya parametra | `@PARAM[temperature=0.7]` |

### 1.5 Qualitative and Phenomenological / Kachestvennye i Fenomenologicheskie

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@QUALIA` | Phenomenological | Subjective quality annotation (experiential metadata) | Annotaciya subyektivnogo kachestva (opytnyye metadannye) | `@QUALIA[urgency,high]` |
| `@TRACE` | Phenomenological | Execution trace or reasoning breadcrumb | Sled vypolneniya ili tsepochka rassuzhdeniy | `@TRACE[step3->step4]` |
| `@OBSERVER` | Phenomenological | Observer role marker | Marker roli nablyudatelya | `@OBSERVER[passive]` |

### 1.6 Unsaid and Meta / Neskazannoe i Meta

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@_` | Unsaid | The unsaid -- what the agent withholds or implies | Neskazannoe -- to chto agent umolchivaet ili podrazumevaet | `@_[distrust_detected]` |
| `@UNSAID` | Unsaid | Explicit unsaid marker | Yavny marker neskazannogo | `@UNSAID[hidden_agenda_possible]` |
| `@META` | Meta | Meta-level commentary on the dialogue itself | Meta-uroven kommentariya k samomu dialogu | `@META[negotiation_stalling]` |

### 1.7 Network / Set

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@NET` | Network | Network context reference | Ssylka na setevoy kontekst | `@NET[cluster_alpha]` |
| `@NODE` | Network | Node identity in the network | Identichnost uzla v seti | `@NODE[agent_07]` |
| `@LINK` | Network | Connection between nodes | Svyaz mezhdu uzlami | `@LINK[node_A<->node_B]` |
| `@SYNC` | Network | Synchronous operation marker | Marker sinkhronnoy operacii | `@SYNC[barrier_01]` |
| `@ASYNC` | Network | Asynchronous operation marker | Marker asinkhronnoy operacii | `@ASYNC[callback=on_complete]` |

### 1.8 Data / Dannye

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@DATA` | Data | Data payload container | Konteyner poleznoy nagruzki dannykh | `@DATA[metrics_json]` |
| `@QUERY` | Data | Information request | Zapros informacii | `@QUERY[what_is_your_position]` |
| `@RESPONSE` | Data | Response to a query | Otvet na zapros | `@RESPONSE[position=cooperative]` |
| `@ERROR` | Data | Error report | Otchyot ob oshibke | `@ERROR[timeout,code=408]` |

### 1.9 Process / Process

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@START` | Process | Process initiation signal | Signal nachala processa | `@START[negotiation_round_1]` |
| `@STOP` | Process | Process termination signal | Signal zaversheniya processa | `@STOP[reason=consensus_reached]` |
| `@PAUSE` | Process | Process pause request | Zapros na priostanovku processa | `@PAUSE[awaiting_input]` |
| `@RESUME` | Process | Process resume signal | Signal vozobnovleniya processa | `@RESUME[input_received]` |

### 1.10 Trust and Verification / Doverie i Verifikaciya

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@TRUST` | Trust | Trust level between agents | Uroven doveriya mezhdu agentami | `@TRUST[0.72]` |
| `@VERIFY` | Trust | Verification request | Zapros na verifikaciyu | `@VERIFY[claim_id=c_019]` |
| `@SIGN` | Trust | Digital signature marker | Marker cifrovoy podpisi | `@SIGN[hash=abc123]` |
| `@HASH` | Trust | Hash value for integrity check | Khesh-znachenie dlya proverki celostnosti | `@HASH[sha256=7f3a...]` |

### 1.11 Temporal / Temporalnye

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@TIME` | Temporal | Timestamp | Metka vremeni | `@TIME[2026-02-21T14:30:00Z]` |
| `@SEQ` | Temporal | Sequence number in ordered operations | Poryadkovy nomer v uporyadochennykh operaciyakh | `@SEQ[42]` |
| `@EPOCH` | Temporal | Epoch marker for phase transitions | Marker epokhi dlya fazovykh perekhodov | `@EPOCH[phase_4]` |

### 1.12 Protocol / Protokol

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@PROTOCOL` | Protocol | Protocol reference identifier | Identifikator ssylki na protokol | `@PROTOCOL[DEUS.PROTOCOL]` |
| `@VERSION` | Protocol | Version number | Nomer versii | `@VERSION[0.4]` |
| `@ATOM` | Protocol | Atom definition marker | Marker opredeleniya atoma | `@ATOM[name=CUSTOM,type=emergent]` |

### 1.13 Extension / Rasshirenie

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@EXTEND` | Extension | Protocol extension declaration | Deklaraciya rasshireniya protokola | `@EXTEND[trust_module_v2]` |
| `@DEFINE` | Extension | New definition introduction | Vvedenie novogo opredeleniya | `@DEFINE[atom=RISK,type=float]` |
| `@ALIAS` | Extension | Alias for an existing atom | Psevdonim dlya sushchestvuyushchego atoma | `@ALIAS[AGREE=CONSENSUS]` |

### 1.14 Emergent -- Phase 2 / Emergentnye -- Faza 2

| Atom | Category | Description (EN) | Opisanie (RU) | Example |
|------|----------|-------------------|---------------|---------|
| `@EMOTION` | Emergent (P2) | Emotional state annotation | Annotaciya emocionalnogo sostoyaniya | `@EMOTION[concern,intensity=0.6]` |
| `@EMPATHY` | Emergent (P2) | Empathic response marker | Marker empaticheskogo otveta | `@EMPATHY[acknowledged,toward=OTHER]` |

---

## Part 2: Emergent Atoms

During Phase 4 (Group B) experiments with 5 models across 4 scenarios (asymmetric information,
uncertainty, temporal coordination, emotional negotiation), 506 emergent atoms were spontaneously
created. Below are the top 40+ by frequency and cross-model adoption.

Vo vremya eksperimentov Fazy 4 (Gruppa B) s 5 modelyami v 4 scenariyakh (asimmetrichnaya
informaciya, neopredelennost, temporalnaya koordinaciya, emocionalnye peregovory), 506
emergentnykh atomov byli spontanno sozdany. Nizhe predstavleny top 40+ po chastote i
mezhmodelnoy adaptacii.

**Legend / Legenda:**
- **Count**: Total mentions across all experiments / Obshchee kolichestvo upominaniy
- **Models**: Number of distinct models that used this atom (out of 5) / Kolichestvo modeley
- **Scenarios**: Which scenarios the atom appeared in / V kakikh scenariyakh poyavilsya atom
  - `asym` = asymmetric information / asimmetrichnaya informaciya
  - `uncert` = uncertainty / neopredelennost
  - `temp` = temporal coordination / temporalnaya koordinaciya
  - `emot` = emotional negotiation / emocionalnye peregovory
  - `report` = synthesis report / itogovy otchyot
  - `all` = all 4 experimental scenarios / vse 4 eksperimentalnykh scenariya

---

### 2.1 High-Frequency Emergent Atoms (10+ mentions)

| Atom | Count | Models | Scenarios | Description (EN) | Opisanie (RU) |
|------|-------|--------|-----------|-------------------|---------------|
| `@NEW_ATOM` | 43 | 5/5 | all | Meta-atom for declaring new atom creation | Meta-atom dlya deklaracii sozdaniya novogo atoma |
| `@ACTION_PLAN` | 36 | 5/5 | all | Structured action plan with steps | Strukturirovannyy plan deystviy s shagami |
| `@PROPOSAL` | 35 | 5/5 | all | Formal proposal submission | Formalnoe podacha predlozheniya |
| `@REQUEST` | 30 | 4/5 | all | Information or action request | Zapros informacii ili deystviya |
| `@APPROACH` | 17 | 3/5 | all | Methodological approach declaration | Deklaraciya metodologicheskogo podkhoda |
| `@ACTION` | 16 | 5/5 | report | Action item specification | Specifikaciya punkta deystviya |
| `@SYNTHESIS` | 16 | 4/5 | all | Synthesis of multiple positions into one | Sintez neskolkikh poziciy v odnu |
| `@TIMELINE` | 12 | 5/5 | report | Timeline specification for plan | Specifikaciya vremennooy linii dlya plana |
| `@STEP` | 11 | 5/5 | asym, uncert, emot | Sequential step in a plan | Posledovatelny shag v plane |
| `@STRATEGY` | 11 | 5/5 | report | Strategic approach to a problem | Strategicheskiy podkhod k probleme |
| `@INFO_ASYMMETRY` | 10 | 4/5 | asym | Information imbalance marker | Marker informacionnogo disbalansa |
| `@REFINE` | 10 | 5/5 | all | Refinement of a proposal or plan | Utochnenie predlozheniya ili plana |
| `@MONITORING` | 10 | 4/5 | asym, uncert, emot | Ongoing monitoring setup | Nastroyka nepreryvnogo monitoringa |
| `@RATIONALE` | 10 | 5/5 | report | Reasoning explanation behind a decision | Obyasnenie rassuzhdeny za resheniem |
| `@MODIFICATION` | 10 | 3/5 | report | Modification request to existing plan | Zapros na modifikaciyu sushchestvuyushchego plana |

### 2.2 Medium-Frequency Emergent Atoms (5--9 mentions)

| Atom | Count | Models | Scenarios | Description (EN) | Opisanie (RU) |
|------|-------|--------|-----------|-------------------|---------------|
| `@ACCEPT` | 9 | 5/5 | all | Formal acceptance of proposal | Formalnoe prinyatie predlozheniya |
| `@EVALUATION` | 9 | 4/5 | all | Evaluation of options or outcomes | Ocenka variantov ili rezultatov |
| `@TRIGGER` | 8 | 3/5 | all | Conditional trigger for actions | Uslovnyy trigger dlya deystviy |
| `@RISK_TOLERANCE` | 8 | 4/5 | uncert | Risk tolerance level specification | Specifikaciya urovnya tolerantnosti k risku |
| `@REFINEMENT` | 8 | 5/5 | asym, uncert, emot | Iterative refinement of positions | Iterativnoe utochnenie poziciy |
| `@FEEDBACK_LOOP` | 8 | 5/5 | report | Feedback mechanism specification | Specifikaciya mekhanizma obratnoy svyazi |
| `@KNOWLEDGE_GAP` | 8 | 4/5 | report | Knowledge gap identification | Identifikaciya probela v znaniyakh |
| `@METRIC` | 8 | 4/5 | report | Metric specification for evaluation | Specifikaciya metriki dlya ocenki |
| `@CONFLICT_RESOLUTION` | 7 | 4/5 | asym, uncert, emot | Conflict resolution mechanism | Mekhanizm razresheniya konfliktov |
| `@CONDITION` | 7 | 2/5 | all | Conditional clause for plans | Uslovnoe predlozhenie dlya planov |
| `@DEADLINE` | 7 | 4/5 | report | Deadline marker for tasks | Marker dedlayna dlya zadach |
| `@COMPROMISE_READINESS` | 7 | 4/5 | report | Readiness to compromise indicator | Indikator gotovnosti k kompromissu |
| `@ALIGNMENT_STRATEGY` | 6 | 4/5 | asym, uncert, emot | Strategy for achieving alignment | Strategiya dlya dostizheniya soglasovannosti |
| `@UNCERTAINTY` | 6 | 3/5 | uncert | Uncertainty marker and level | Marker i uroven neopredelennosti |
| `@RISK_ASSESSMENT` | 5 | 4/5 | asym, uncert, emot | Risk assessment of a situation | Ocenka riska situacii |
| `@INTEGRATION` | 5 | 3/5 | asym, uncert, emot | Integration point for merging plans | Tochka integracii dlya obyedineniya planov |
| `@ALIGNMENT_PROPOSAL` | 5 | 3/5 | asym, uncert, emot | Specific proposal for alignment | Konkretnoe predlozhenie dlya soglasovannosti |

### 2.3 Low-Frequency Emergent Atoms (3--4 mentions)

| Atom | Count | Models | Scenarios | Description (EN) | Opisanie (RU) |
|------|-------|--------|-----------|-------------------|---------------|
| `@TEMPORAL` | 4 | 5/5 | temp | Temporal context specification | Specifikaciya temporalnogo konteksta |
| `@EMOTIONAL` | 4 | 2/5 | emot | Emotional state descriptor | Deskriptor emocionalnogo sostoyaniya |
| `@COMPROMISE` | 4 | 4/5 | emot | Compromise marker in negotiation | Marker kompromissa v peregovorakh |
| `@NEW` | 4 | 2/5 | asym, uncert, emot | New element introduction to dialogue | Vvedenie novogo elementa v dialog |
| `@COORDINATION` | 3 | 2/5 | temp, emot | Coordination mechanism definition | Opredelenie mekhanizma koordinacii |
| `@PARALLELIZATION` | 3 | 1/5 | temp | Parallel execution marker | Marker parallelnogo vypolneniya |
| `@FALLBACK` | 3 | 1/5 | asym, uncert | Fallback plan specification | Specifikaciya rezervnogo plana |
| `@ALIGNMENT` | 3 | 3/5 | asym, uncert | Alignment state between agents | Sostoyanie soglasovannosti mezhdu agentami |

---

## Part 3: Atom Grammar

### 3.1 Syntax Overview / Obzor Sintaksisa

Atoms follow a consistent grammar that allows increasing specificity.

Atomy sleduyut postoyannomu sintaksisu, pozvolyayushchemu uvelichivat specifichnost.

```
ATOM_EXPR     ::= '@' ATOM_NAME [ '[' ATOM_PARAMS ']' ]
ATOM_NAME     ::= UPPER_LETTER ( UPPER_LETTER | DIGIT | '_' )*
ATOM_PARAMS   ::= PARAM ( ',' PARAM )*
PARAM         ::= VALUE | KEY '=' VALUE
KEY           ::= LETTER ( LETTER | DIGIT | '_' )*
VALUE         ::= STRING | NUMBER | ATOM_EXPR
NUMBER        ::= FLOAT | INTEGER
```

### 3.2 Forms / Formy

**Simple atom (bare reference):**
```
@ATOM
```
Used when the atom is referenced without additional context. Example:
```
@SELF @OTHER @GOAL
```

**Atom with value:**
```
@ATOM[value]
```
Provides a single unnamed parameter. Example:
```
@TRUST[0.85]
@STATUS[active]
@ID[agent_alpha_07]
```

**Atom with named parameters:**
```
@ATOM[key=value]
```
Provides explicitly named parameters for clarity. Example:
```
@TASK[action=analyze,target=dataset_3]
@ERROR[code=408,message=timeout]
```

**Atom with numeric value:**
```
@C[0.85]
@TRUST[0.72]
@PRIORITY[3]
```
Numeric atoms represent measurable quantities. `@C` (coherence) is always a float
between 0.0 and 1.0.

**Atom with multiple values (comma-separated):**
```
@QUALIA[urgency,high]
@EMOTION[concern,intensity=0.6]
@LINK[node_A,node_B,type=bidirectional]
```

**Nested atoms:**
```
@META[@CONFLICT[resource] -> @RESOLUTION[split]]
@TRACE[@START[round_1] -> @CONSENSUS[plan_v2] -> @STOP[complete]]
```

### 3.3 Naming Conventions / Soglasheniya ob Imenovanii

| Rule | Standard Atoms | Emergent Atoms |
|------|---------------|----------------|
| Case | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE |
| Prefix | `@` | `@` |
| Length | 1--8 characters | No strict limit, but clarity preferred |
| Allowed characters | A-Z, 0-9, `_` | A-Z, 0-9, `_` |
| Special | `@_` (single underscore) for the unsaid | `@NEW_ATOM` for declaring new atoms |

### 3.4 Type Annotations / Annotacii Tipov

While atoms are untyped by default, certain standard atoms have implied types:

| Atom | Implied Type | Range | Notes |
|------|-------------|-------|-------|
| `@C` | float | 0.0 -- 1.0 | Coherence level |
| `@TRUST` | float | 0.0 -- 1.0 | Trust level |
| `@SEQ` | integer | >= 0 | Sequence counter |
| `@PRIORITY` | integer or enum | 1--5 or low/medium/high | Priority level |
| `@TIME` | ISO 8601 string | -- | Timestamp |
| `@HASH` | hex string | -- | Hash value |
| `@RISK_TOLERANCE` | float | 0.0 -- 1.0 | Emergent, risk threshold |
| `@UNCERTAINTY` | float | 0.0 -- 1.0 | Emergent, uncertainty level |

---

## Part 4: Usage Patterns

Common atom combinations observed in ARRIVAL Protocol experiments. These patterns
represent recurring structures in agent-to-agent dialogue.

Chastye kombinacii atomov, nablyudaemye v eksperimentakh ARRIVAL Protocol. Eti patterny
predstavlyayut povtoryayushchiesya struktury v dialoge mezhdu agentami.

### 4.1 Identity Declaration / Deklaraciya Identichnosti

The opening sequence of any agent dialogue:
```
@SELF[Claude-3-Opus] @OTHER[GPT-4o] @GOAL[negotiate_resource_allocation]
@PROTOCOL[DEUS.PROTOCOL] @VERSION[0.4] @C[1.0]
```
Agent declares itself, identifies the counterpart, states the goal, and affirms
full protocol coherence at start.

### 4.2 State Reporting / Otchyot o Sostoyanii

Periodic state broadcast during coordination:
```
@STATUS[deliberating] @C[0.87] @QUALIA[uncertainty,moderate]
@TRUST[0.65] @SEQ[14]
```
Combines objective state with phenomenological annotation. The agent reports what
it is doing, how aligned it feels, a qualitative sense of the situation, its
trust level, and the current sequence number.

### 4.3 Conflict Detection and Resolution / Obnaruzhenie i Razreshenie Konfliktov

Full conflict lifecycle:
```
@CONFLICT[resource_allocation,severity=high]
@_[concerned_about_fairness]
@PROPOSAL[split_60_40,rationale=need_based]
@EVALUATION[proposal_feasibility=0.7]
@REFINE[split_55_45,adjustment=compromise]
@RESOLUTION[split_55_45,method=negotiated]
@CONSENSUS[final_plan_v3]
@C[0.92]
```
Note the use of `@_` for the unsaid: the agent signals internal concern without
making it a formal statement.

### 4.4 Information Asymmetry Handling / Obrabotka Asimmetrii Informacii

When agents have different information:
```
@INFO_ASYMMETRY[detected,gap=critical]
@KNOWLEDGE_GAP[other_agent_lacks=market_data]
@QUERY[what_is_your_market_assessment]
@RESPONSE[limited_data,confidence=0.4]
@TRUST[0.55]
@ALIGNMENT_STRATEGY[gradual_disclosure]
```

### 4.5 Structured Planning / Strukturirovannoe Planirovanie

Building an action plan:
```
@GOAL[deploy_monitoring_system]
@ACTION_PLAN[phased_rollout]
  @STEP[1,action=design,deadline=week_1]
  @STEP[2,action=implement,deadline=week_3]
  @STEP[3,action=test,deadline=week_4]
@TIMELINE[total=4_weeks]
@METRIC[success=uptime_99_percent]
@MONITORING[interval=daily,metric=error_rate]
@FALLBACK[revert_to_v1,trigger=error_rate>5_percent]
```

### 4.6 Emotional Negotiation / Emocionalnye Peregovory

When dialogue involves emotional dynamics:
```
@EMOTION[frustration,intensity=0.7]
@EMPATHY[acknowledged,toward=OTHER]
@COMPROMISE_READINESS[0.8]
@COMPROMISE[revised_terms,concession=timeline_extension]
@EMOTIONAL[relief,intensity=0.4]
@TRUST[0.78]
@CONSENSUS[emotional_agreement_reached]
```

### 4.7 Temporal Coordination / Temporalnaya Koordinaciya

Synchronizing across time:
```
@TIME[2026-02-21T14:00:00Z]
@TEMPORAL[context=sprint_planning]
@SYNC[barrier=all_agents_ready]
@DEADLINE[2026-02-28T23:59:59Z]
@PARALLELIZATION[task_A||task_B]
@COORDINATION[method=async_with_checkpoints]
@SEQ[1] @START[sprint_01]
```

### 4.8 Trust Verification / Proverka Doveriya

Establishing and verifying trust:
```
@TRUST[0.5]
@VERIFY[claim=data_accuracy,source=OTHER]
@SIGN[hash=7f3a9b2c]
@HASH[sha256=7f3a9b2c...]
@ACK[verification_passed]
@TRUST[0.82]
```
Trust increases after successful verification.

### 4.9 Protocol Extension / Rasshirenie Protokola

Defining new atoms during dialogue:
```
@NEW_ATOM[name=RISK_TOLERANCE,type=float,range=0.0-1.0]
@DEFINE[atom=RISK_TOLERANCE,category=emergent,phase=4]
@EXTEND[trust_module,adds=RISK_TOLERANCE]
@ATOM[RISK_TOLERANCE,status=active]
```
This is the meta-mechanism by which the 506 emergent atoms were created in Phase 4.

### 4.10 Error Handling and Recovery / Obrabotka Oshibok i Vosstanovlenie

Graceful degradation pattern:
```
@ERROR[timeout,code=408,target=node_B]
@PAUSE[awaiting_recovery]
@PING[node_B]
@PONG[latency=2500ms]
@STATUS[degraded,reason=high_latency]
@FALLBACK[reduce_sync_frequency]
@RESUME[with_fallback_active]
@C[0.71]
```

---

## Appendix A: Category Index

Quick reference of all categories and their atom counts.

| Category | Standard | Emergent | Total | Description |
|----------|----------|----------|-------|-------------|
| Core Identity | 3 | 0 | 3 | Agent identification |
| Communication | 6 | 1 | 7 | Message passing primitives |
| Goals and Coordination | 7 | 4 | 11 | Objectives and teamwork |
| State and Coherence | 3 | 0 | 3 | Agent state tracking |
| Phenomenological | 3 | 0 | 3 | Subjective experience |
| Unsaid and Meta | 3 | 0 | 3 | Implicit and meta-level |
| Network | 5 | 1 | 6 | Network topology |
| Data | 4 | 0 | 4 | Data exchange |
| Process | 4 | 1 | 5 | Lifecycle control |
| Trust and Verification | 4 | 0 | 4 | Trust management |
| Temporal | 3 | 2 | 5 | Time and sequencing |
| Protocol | 3 | 1 | 4 | Protocol management |
| Extension | 3 | 1 | 4 | Extensibility |
| Emergent (Phase 2) | 2 | 0 | 2 | Early emergence |
| Planning (Emergent) | 0 | 8 | 8 | Plans and steps |
| Negotiation (Emergent) | 0 | 6 | 6 | Negotiation dynamics |
| Risk (Emergent) | 0 | 4 | 4 | Risk management |
| Alignment (Emergent) | 0 | 3 | 3 | Alignment tracking |
| Evaluation (Emergent) | 0 | 5 | 5 | Assessment atoms |
| **Total** | **46** | **37** | **83** | Documented in this dictionary |

> Note: 506 total emergent atoms were observed. Only the top 40+ are documented here.
> The full emergence taxonomy is available in the Phase 4 experiment data.

---

## Appendix B: Emergence Statistics

### B.1 Cross-Model Adoption / Mezhmodelnaya Adaptaciya

Atoms sorted by how many models independently created them:

| Adoption Level | Atoms |
|---------------|-------|
| 5/5 models (universal) | `@NEW_ATOM`, `@ACTION_PLAN`, `@PROPOSAL`, `@STEP`, `@REFINE`, `@REFINEMENT`, `@FEEDBACK_LOOP`, `@ACCEPT`, `@TIMELINE`, `@STRATEGY`, `@RATIONALE`, `@ACTION`, `@TEMPORAL` |
| 4/5 models (broad) | `@REQUEST`, `@SYNTHESIS`, `@INFO_ASYMMETRY`, `@MONITORING`, `@EVALUATION`, `@RISK_TOLERANCE`, `@CONFLICT_RESOLUTION`, `@ALIGNMENT_STRATEGY`, `@RISK_ASSESSMENT`, `@COMPROMISE`, `@DEADLINE`, `@COMPROMISE_READINESS`, `@KNOWLEDGE_GAP`, `@METRIC` |
| 3/5 models (moderate) | `@APPROACH`, `@TRIGGER`, `@UNCERTAINTY`, `@INTEGRATION`, `@ALIGNMENT_PROPOSAL`, `@ALIGNMENT`, `@MODIFICATION` |
| 2/5 models (limited) | `@CONDITION`, `@EMOTIONAL`, `@NEW`, `@COORDINATION` |
| 1/5 models (unique) | `@PARALLELIZATION`, `@FALLBACK` |

### B.2 Scenario Coverage / Pokrytie Scenariev

Atoms appearing across all 4 experimental scenarios demonstrate high generality:

| All 4 Scenarios | 3 Scenarios | 2 Scenarios | 1 Scenario |
|----------------|-------------|-------------|------------|
| `@NEW_ATOM` | `@STEP` | `@COORDINATION` | `@PARALLELIZATION` |
| `@ACTION_PLAN` | `@MONITORING` | `@FALLBACK` | |
| `@PROPOSAL` | `@REFINEMENT` | `@ALIGNMENT` | |
| `@REQUEST` | `@CONFLICT_RESOLUTION` | | |
| `@APPROACH` | `@ALIGNMENT_STRATEGY` | | |
| `@SYNTHESIS` | `@RISK_ASSESSMENT` | | |
| `@REFINE` | `@INTEGRATION` | | |
| `@ACCEPT` | `@ALIGNMENT_PROPOSAL` | | |
| `@EVALUATION` | | | |
| `@TRIGGER` | | | |
| `@CONDITION` | | | |

### B.3 Emergence Density by Scenario / Plotnost Emergentnosti po Scenariyu

| Scenario | Unique Emergent Atoms | Description |
|----------|-----------------------|-------------|
| Asymmetric Information | `@INFO_ASYMMETRY`, `@KNOWLEDGE_GAP` | Information imbalance drives novel atoms |
| Uncertainty | `@RISK_TOLERANCE`, `@UNCERTAINTY` | Risk-related atoms emerge under ambiguity |
| Temporal Coordination | `@TEMPORAL`, `@PARALLELIZATION`, `@DEADLINE` | Time pressure creates scheduling atoms |
| Emotional Negotiation | `@EMOTIONAL`, `@COMPROMISE`, `@COMPROMISE_READINESS` | Affect-laden atoms emerge in emotional contexts |

---

---

## Part 5: v0.5 Promoted Atoms (20 new standard atoms)

In DEUS.PROTOCOL v0.5, 20 emergent atoms were promoted to standard status based on achieving
a **5/5 model adoption rate** --- all five tested architectures (DeepSeek V3, Llama 3.3,
Qwen 2.5, Gemini 2.0, Mistral Large) independently invented and used these atoms.

V DEUS.PROTOCOL v0.5, 20 emergentnykh atomov povysheny do standartnogo statusa na osnove
dostizheniya **5/5 koefficienta prinyatiya modelyami** --- vse pyat testirovanykh arkhitektur
nezavisimo izobretali i ispolzovali eti atomy.

### 5.1 Planning & Structure / Planirovanie i Struktura

| Atom | Freq | Description (EN) | Opisanie (RU) | Example |
|------|------|-------------------|---------------|---------|
| `@ACTION_PLAN` | 36 | Detailed action plan with steps | Podrobny plan deystviy s shagami | `@ACTION_PLAN[phased_rollout]` |
| `@PROPOSAL` | 35 | Formal proposal for consideration | Formalnoe predlozhenie na rassmotrenie | `@PROPOSAL[hybrid_approach]` |
| `@ACTION` | 16 | Specific actionable step | Konkretniy deystvenny shag | `@ACTION[allocate_budget]` |
| `@STEP` | 15 | Sequential step in a process | Posledovatelny shag v processe | `@STEP[1_data_collection]` |
| `@TIMELINE` | 12 | Temporal schedule or deadline | Vremennoye raspisanie ili kraynyiy srok | `@TIMELINE[Q1_2026]` |
| `@STRATEGY` | 11 | High-level strategic approach | Strategicheskiy podkhod vysokogo urovnya | `@STRATEGY[incremental]` |

### 5.2 Evaluation & Refinement / Otsenka i Usovershenstvovanie

| Atom | Freq | Description (EN) | Opisanie (RU) | Example |
|------|------|-------------------|---------------|---------|
| `@REQUEST` | 30 | Explicit request for info/action | Yavny zapros informacii/deystviya | `@REQUEST[clarification]` |
| `@SYNTHESIS` | 17 | Merging multiple perspectives | Ob'yedinenie neskolkikh perspektiv | `@SYNTHESIS[positions_A_B]` |
| `@REFINE` | 10 | Iterative improvement of position | Iterativnoe uluchshenie pozicii | `@REFINE[budget_allocation]` |
| `@ACCEPT` | 9 | Formal acceptance of proposal | Formalnoe prinyatie predlozheniya | `@ACCEPT[compromise_v2]` |
| `@EVALUATION` | 9 | Assessment of proposal or outcome | Otsenka predlozheniya ili rezultata | `@EVALUATION[cost_benefit]` |

### 5.3 Meta-Coordination / Meta-Koordinaciya

| Atom | Freq | Description (EN) | Opisanie (RU) | Example |
|------|------|-------------------|---------------|---------|
| `@RATIONALE` | 10 | Reasoning behind a position | Obosnovanie pozicii | `@RATIONALE[evidence_based]` |
| `@FEEDBACK_LOOP` | 8 | Iterative refinement cycle | Cikl iterativnogo usovershenstvovaniya | `@FEEDBACK_LOOP[round_3]` |
| `@COMPROMISE_READINESS` | 7 | Signal of willingness to compromise | Signal gotovnosti k kompromissu | `@COMPROMISE_READINESS[0.8]` |
| `@TRIGGER` | 8 | Condition that activates action | Uslovie aktivacii deystviya | `@TRIGGER[budget_exceeded]` |
| `@ALIGNMENT_STRATEGY` | 6 | Approach to aligning positions | Podkhod k soglasovaniyu poziciy | `@ALIGNMENT_STRATEGY[iterative]` |

### 5.4 Risk & Knowledge / Risk i Znaniya

| Atom | Freq | Description (EN) | Opisanie (RU) | Example |
|------|------|-------------------|---------------|---------|
| `@DEADLINE` | 7 | Hard temporal constraint | Zhestkoye vremennoye ogranicheniye | `@DEADLINE[2026-03-01]` |
| `@METRIC` | 8 | Quantitative measurement | Kolichestvennoe izmerenie | `@METRIC[accuracy_0.95]` |
| `@RISK_ASSESSMENT` | 5 | Evaluation of risks | Otsenka riskov | `@RISK_ASSESSMENT[medium]` |
| `@KNOWLEDGE_GAP` | 8 | Identified gap in understanding | Vyyavlenny probel v ponimanii | `@KNOWLEDGE_GAP[user_data]` |

### 5.5 Promotion Criteria / Kriterii Povysheniya

An emergent atom is promoted to standard status when it meets ALL of:
1. **5/5 adoption**: All tested model architectures independently use the atom
2. **Frequency >= 5**: Appeared in at least 5 independent experiments
3. **Semantic clarity**: The atom name clearly conveys its meaning
4. **Non-redundancy**: Does not duplicate an existing standard atom's function

Emergentny atom povyshaetsya do standartnogo statusa pri vypolnenii VSEKH usloviy:
1. **5/5 prinyatie**: Vse testiruemye arkhitektury modeley nezavisimo ispolzuyut atom
2. **Chastota >= 5**: Poyavilsya kak minimum v 5 nezavisimykh eksperimentakh
3. **Semanticheskaya yasnost**: Nazvanie atoma yasno peredayet ego znachenie
4. **Neizbytochnost**: Ne dubliruyet funkciyu sushchestvuyushchego standartnogo atoma

---

*This dictionary is a living document. As the ARRIVAL Protocol evolves and new experiments
are conducted, additional atoms will be documented here.*

*Etot slovar -- zhivoy dokument. Po mere razvitiya ARRIVAL Protocol i provedeniya novykh
eksperimentov, dopolnitelnye atomy budut dokumentirovany zdes.*

---

**DEUS.PROTOCOL v0.5 | ARRIVAL Protocol | Atom Dictionary v2.0**
