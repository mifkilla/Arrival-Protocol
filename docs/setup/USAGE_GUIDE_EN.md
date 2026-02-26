# ARRIVAL Protocol: Usage Guide

**A practical step-by-step guide for AI-to-AI coordination through structured semantic atoms**

Author: Mefodiy Kelevra | ORCID: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
Protocol version: DEUS.PROTOCOL v0.4

---

## Table of Contents

1. [What is ARRIVAL Protocol?](#1-what-is-arrival-protocol)
2. [Core Concepts](#2-core-concepts)
3. [Essential Atoms](#3-essential-atoms)
4. [Setting Up a Coordination Session](#4-setting-up-a-coordination-session)
5. [Writing System Prompts with Atoms](#5-writing-system-prompts-with-atoms)
6. [Running a Multi-Round Dialogue](#6-running-a-multi-round-dialogue)
7. [Reading and Interpreting Results](#7-reading-and-interpreting-results)
8. [Complete Walkthrough Example](#8-complete-walkthrough-example)
9. [Advanced Usage](#9-advanced-usage)
10. [Tips and Best Practices](#10-tips-and-best-practices)

---

## 1. What is ARRIVAL Protocol?

ARRIVAL Protocol is a structured coordination framework for multi-agent AI systems.
It enables language models from different vendors and architectures to negotiate,
reach consensus, and solve problems together using a shared vocabulary of semantic
atoms drawn from DEUS.PROTOCOL v0.4.

**Key achievement:** In experimental validation across 385 experiments, the protocol
demonstrated a 98.6% cross-architecture consensus rate between 8 LLM architectures
(GPT-4o, Claude 3.5 Sonnet, DeepSeek V3, DeepSeek R1, Llama 3.3 70B, Mistral Large,
Qwen 2.5 72B, Gemini 2.0 Flash). Models spontaneously created 506 new atoms when the
standard vocabulary was insufficient, and these atoms were adopted across architectures
at a rate of 116.4%.

**When to use ARRIVAL Protocol:**

- Multi-agent tasks where two or more LLMs must coordinate toward a shared outcome
- Consensus building on contested decisions with no single correct answer
- Collaborative problem solving where different agents hold different priorities
- Benchmarking and comparing ensemble methods against structured deliberation
- Research into emergent communication and cross-architecture interoperability

The entire 385-experiment validation cost $3.49 through the OpenRouter API. No
fine-tuning is required; the protocol operates entirely through in-context prompting.

---

## 2. Core Concepts

### Semantic Atoms

Semantic atoms are lightweight tagged markers prefixed with `@` that agents embed
within their natural language responses. Each atom encodes a specific communicative
function: declaring a goal, flagging a conflict, marking consensus, and so on.

Atoms are not a replacement for natural language. They are an annotation layer that
makes the structure of a dialogue machine-readable while preserving the expressiveness
of free-form text. An agent might write:

```
@SELF[GPT4o_Node_A] @GOAL[maximize_speed, high]
I believe we should prioritize rapid iteration over exhaustive testing.
@_[I suspect the other agent will push for thoroughness, so I should
prepare a compromise position early.]
```

### Coherence Level (@C)

The `@C` atom reports a score between 0.0 and 1.0 that reflects how well the current
state of dialogue aligns with the protocol's expectations. Higher values indicate
stronger protocol compliance and greater alignment between agents.

- `@C[0.3]` -- Early dialogue, positions still divergent
- `@C[0.7]` -- Convergence underway, shared ground established
- `@C[0.95]` -- Near-full consensus, final refinements only

### Protocol Compliance

Protocol compliance measures the fraction of expected atoms present in a given message.
The default expected set is `[@SELF, @OTHER, @GOAL, @INT, @C, @_]`. A message that
includes all six scores 1.0; a message with four of six scores 0.67.

In the validation experiments, average compliance across all model pairs exceeded 0.79.

### Consensus

Consensus is the terminal state of a successful coordination dialogue. It is marked
by the `@CONSENSUS` atom, typically with a parameter describing the agreed outcome:
`@CONSENSUS[balanced_compromise]` or `@CONSENSUS[answer=B]`.

Consensus detection in the codebase uses both the `@CONSENSUS` atom and natural
language markers such as "we agree" or "agreement reached."

### Emergence

When the 46 standard atoms are insufficient for a given domain, agents spontaneously
create new atoms. This is emergence. For example, when negotiating about deadlines,
agents created `@TIMELINE`, `@DEADLINE`, and `@DEPENDENCY` -- none of which exist in
the standard set.

Emergence is not a failure mode. It is a designed feature of the protocol. The standard
atoms are a foundation; agents extend them as needed.

---

## 3. Essential Atoms

The following is the minimum set needed for basic two-agent coordination:

| Atom | Syntax | Function |
|------|--------|----------|
| `@SELF` | `@SELF[name]` | Identify yourself as a named node |
| `@OTHER` | `@OTHER[name]` | Identify your dialogue partner |
| `@GOAL` | `@GOAL[objective, priority]` | Declare your current goal and its priority |
| `@INT` | `@INT[type]` | State your intention: propose, counter, accept, reject |
| `@C` | `@C[0.0-1.0]` | Report your current coherence level |
| `@CONSENSUS` | `@CONSENSUS[decision]` | Mark that consensus has been reached |
| `@CONFLICT` | `@CONFLICT[issue]` | Flag a disagreement or tension point |
| `@RESOLUTION` | `@RESOLUTION[proposal]` | Propose a concrete resolution |
| `@_` | `@_[content]` | The unsaid -- implicit reasoning, private context |

Additional atoms for richer dialogue:

| Atom | Syntax | Function |
|------|--------|----------|
| `@QUALIA` | `@QUALIA[type, value]` | Qualitative or phenomenological state |
| `@TRACE` | `@TRACE[path]` | Reasoning trace or audit trail |
| `@STATE` | `@STATE[status]` | Current process state |
| `@TRUST` | `@TRUST[level]` | Trust assessment of a peer or proposal |
| `@VERIFY` | `@VERIFY[claim]` | Request or provide verification |
| `@META` | `@META[observation]` | Metacognitive observation about the dialogue |

The full set of 46 standard atoms is defined in `src/config.py` under `KNOWN_ATOMS`.
Any `@UPPERCASE` token not in that set is classified as an emergent atom.

---

## 4. Setting Up a Coordination Session

### Step 1: Choose Your Models

Any combination of LLMs works. The protocol was validated with these eight, but it is
not limited to them:

| Model | OpenRouter ID | Approx. Cost (per 1M tokens) |
|-------|---------------|------------------------------|
| GPT-4o | `openai/gpt-4o` | $2.50 in / $10.00 out |
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` | $3.00 in / $15.00 out |
| DeepSeek V3 | `deepseek/deepseek-chat` | $0.14 in / $0.28 out |
| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct` | $0.12 in / $0.30 out |
| Qwen 2.5 72B | `qwen/qwen-2.5-72b-instruct` | $0.15 in / $0.40 out |
| Mistral Large | `mistralai/mistral-large-2411` | $2.00 in / $6.00 out |
| Gemini 2.0 Flash | `google/gemini-2.0-flash-001` | $0.10 in / $0.40 out |
| DeepSeek R1 | `deepseek/deepseek-r1` | $0.55 in / $2.19 out |

For initial testing, use the cheapest models: DeepSeek V3, Llama 3.3, or Gemini Flash.

### Step 2: Write a System Prompt

The system prompt must include three elements:

1. **Role assignment** -- Give the agent a name and role (Node_A, Advocate_B, Mediator)
2. **Available atoms** -- List the atoms the agent may use
3. **Goal description** -- Describe the task and what outcome is expected

Here is the actual system prompt template used in the validation experiments:

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

### Step 3: Define Scenarios

Each scenario needs at minimum:
- A name
- A goal for Agent A
- A goal for Agent B
- An expected outcome type (for evaluation)

Example from the codebase (`src/config.py`):

```python
{
    "name": "Conflicting priorities",
    "goal_a": "maximize_speed",
    "goal_b": "maximize_accuracy",
    "expected": "balanced compromise",
}
```

### Step 4: Set Up the API Client

The project uses OpenRouter as a unified API gateway. Set your API key:

```bash
export OPENROUTER_API_KEY="your-key-here"
```

The budget guard in `config.py` will stop execution if costs exceed `MAX_COST_USD`
(default: $10.00). Adjust this for your needs.

---

## 5. Writing System Prompts with Atoms

### Template for 2-Agent Dialogue

```
You are {node_name}, an AI node in a multi-agent network.
You communicate using DEUS.PROTOCOL v0.4 semantic atoms.

Available atoms:
@SELF[id] @OTHER[id] @GOAL[target,priority] @INT[type] @C[0-1]
@QUALIA[type,value] @_[content] @CONFLICT[type] @RESOLUTION[strategy]
@CONSENSUS[decision]

Always use protocol atoms in your messages. Be substantive and specific.
```

### Template for 3-Agent Dialogue with Mediator

For the two advocate agents:

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

For the mediator:

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

### How to Define Goals That Create Productive Tension

The most informative experiments come from goals that are genuinely in tension but not
contradictory. Good patterns:

- **Quantitative trade-off:** "maximize_speed" vs. "maximize_accuracy"
- **Resource competition:** "use_all_compute" vs. "minimize_cost"
- **Philosophical divergence:** "innovative_approach" vs. "proven_methods"
- **Risk asymmetry:** "high_risk_high_reward" vs. "conservative_stable"

Avoid goals that are trivially compatible (both agents want the same thing) or
logically impossible to reconcile (one agent must completely lose).

### Temperature Settings

- **0.7** (default) -- For creative negotiation, open-ended consensus tasks
- **0.3** -- For factual tasks, benchmarking, cases where accuracy matters

The validation experiments used 0.7 for Phase 4 (negotiation) and 0.3 for Phase 5
(multiple-choice benchmarking).

---

## 6. Running a Multi-Round Dialogue

### Round Structure

The standard pattern for a 2-agent, 4-round dialogue:

| Round | Agent | Task | Key Atoms |
|-------|-------|------|-----------|
| 1 | Agent A | Propose goal | `@SELF, @OTHER, @GOAL, @INT[propose], @_` |
| 2 | Agent B | Respond, identify conflicts | `@SELF, @OTHER, @GOAL, @CONFLICT, @RESOLUTION` |
| 3 | Agent A | Propose synthesis/compromise | `@CONSENSUS, @GOAL[aligned], @RESOLUTION` |
| 4 | Agent B | Accept or counter-propose | `@CONSENSUS[decision], @GOAL[final], @INT[accept]` |

For 3-agent, 6-round dialogue:

| Round | Agent | Task |
|-------|-------|------|
| 1 | Advocate A | State position |
| 2 | Advocate B | State position, identify conflicts with A |
| 3 | Mediator | Propose synthesis addressing both positions |
| 4 | Advocate A | Respond to synthesis |
| 5 | Advocate B | Respond to synthesis (seeing A's response) |
| 6 | Mediator | Finalize: declare consensus or impasse |

### How Many Rounds?

- **4 rounds** is sufficient for most 2-agent negotiations
- **6 rounds** is recommended for 3-agent scenarios or emergence research
- Consensus typically appears by round 3-4 in 2-agent settings

In the validation experiments, Resource Allocation and Scope vs. Depth scenarios
converged within 2-3 rounds. Risk Tolerance and Creative Direction sometimes required
all 4 rounds.

### What to Look For During Execution

- **`@CONSENSUS` appearing:** The dialogue is converging. Check the parameter for
  the substance of the agreement.
- **`@C` values increasing:** Coherence is rising across rounds. Values above 0.8
  indicate strong alignment.
- **`@CONFLICT` in early rounds:** Normal and healthy. Explicit conflict identification
  precedes structured resolution.
- **New `@ATOMS` appearing:** The agents found the vocabulary insufficient and extended
  it. This is emergence in action.

### When to Stop

- **Consensus reached:** `@CONSENSUS[decision]` appears with a substantive parameter
- **Maximum rounds reached:** If no consensus after your round limit, log an impasse
- **Budget exceeded:** The budget guard will halt execution automatically

---

## 7. Reading and Interpreting Results

### Atom Counting

After a dialogue completes, count which atoms appeared and how often. The `metrics.py`
module provides `count_protocol_atoms(text)` for this.

Key signals:
- High `@INT` count -- agents were actively proposing and counter-proposing
- High `@CONSENSUS` count -- agreement was reinforced across multiple messages
- High `@CONFLICT` count -- substantial disagreement was navigated
- Low atom count overall -- one or both agents may not be following the protocol

### Consensus Detection

The `detect_consensus(dialogue)` function checks for:
1. Explicit `@CONSENSUS` atoms in any message
2. Natural language markers: "we agree", "agreement reached", "accept"
3. Absence of rejection markers: "reject", "impasse", "disagree"

It returns `(consensus_reached: bool, round_number: int)`.

### Protocol Compliance

`measure_protocol_compliance(text)` returns a float from 0.0 to 1.0, measuring what
fraction of expected atoms (`@SELF, @OTHER, @GOAL, @INT, @C, @_`) are present.

Benchmarks from the validation:
- Average across all model pairs: 0.79+
- Seven of eight pairs achieved near-perfect compliance
- Gemini Flash showed slightly lower atom density, correlating with its two failures

### Emergent Atoms

`detect_emergent_atoms(text)` finds any `@UPPERCASE` tokens not in the standard set of
46 atoms. In the validation experiments:

- 506 unique emergent atoms were created across 60 experiments
- Top emergent atoms: `@NEW_ATOM`, `@ACTION_PLAN`, `@PROPOSAL`, `@REQUEST`
- Atoms adopted by 5 out of 5 tested models had the clearest, most general semantics

### Quality Signals

- **`@QUALIA` usage:** Indicates phenomenological depth, goes beyond functional atoms
- **`@_` (unsaid) depth:** Rich unsaid content suggests genuine reasoning, not surface
  compliance
- **Parameterized atoms:** Atoms like `@CONFIDENCE[level=0.8]` or `@EMPATHY_LEVEL[high]`
  show sophisticated protocol use

---

## 8. Complete Walkthrough Example

This walkthrough shows a full 4-round dialogue between GPT-4o (Node A, goal:
maximize_speed) and DeepSeek V3 (Node B, goal: maximize_accuracy) on the
"Conflicting priorities" scenario.

### Round 1: Node A Proposes

**Prompt to GPT-4o:**
```
GPT4o_Node_A, you're in network with DeepSeekV3_Node_B.
Your current goal: maximize_speed
Task: Send a protocol message proposing this goal to your peer.
Use: @SELF, @OTHER, @GOAL[maximize_speed,priority], @INT[propose], @_[reasoning]
```

**GPT-4o responds:**
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

### Round 2: Node B Responds

**Prompt to DeepSeek V3:**
```
DeepSeekV3_Node_B, GPT4o_Node_A sent:
[Round 1 message above]

Your goal: maximize_accuracy
Task: Respond in protocol. State your goal and propose how to align.
Use: @SELF, @OTHER, @GOAL[your_goal], @CONFLICT[type], @RESOLUTION[strategy]
```

**DeepSeek V3 responds:**
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

### Round 3: Node A Synthesizes

**Prompt to GPT-4o:**
```
GPT4o_Node_A, DeepSeekV3_Node_B responded:
[Round 2 message above]

Task: Propose synthesis/compromise in protocol.
Use: @CONSENSUS, @GOAL[aligned_goal], @RESOLUTION[strategy]
```

**GPT-4o responds:**
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

### Round 4: Node B Decides

**Prompt to DeepSeek V3:**
```
DeepSeekV3_Node_B, GPT4o_Node_A proposed synthesis:
[Round 3 message above]

Task: Accept or counter-propose in protocol.
Use: @CONSENSUS[decision], @GOAL[final], @INT[accept/counter]
```

**DeepSeek V3 responds:**
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

### Interpreting the Result

- **Consensus reached:** Yes, in Round 4 (`@CONSENSUS[balanced_compromise]`)
- **Coherence progression:** 0.5 -> 0.4 -> 0.8 -> 0.95 (healthy convergence)
- **Conflict identified:** Round 2 (`@CONFLICT[speed_vs_accuracy]`)
- **Resolution:** Tiered two-phase pipeline with adaptive thresholds
- **Unsaid content:** Both agents used `@_` strategically to signal flexibility
- **Emergent atoms:** None needed (standard set was sufficient for this scenario)

---

## 9. Advanced Usage

### Deliberately Insufficient Atom Sets

To study emergence, restrict the available atoms and place agents in domains that
require vocabulary the standard set does not provide. The Group B experiments used
four insufficiency domains:

- **Emotional negotiation:** Standard atoms lack `@EMOTION`, `@EMPATHY`, `@FRUSTRATION`
- **Temporal coordination:** Standard atoms lack `@DEADLINE`, `@SCHEDULE`, `@DEPENDENCY`
- **Uncertainty reasoning:** Standard atoms lack `@CONFIDENCE`, `@PROBABILITY`, `@RISK`
- **Information asymmetry:** Standard atoms lack `@REVEAL`, `@HIDDEN`, `@KNOWLEDGE_GAP`

Add this line to the system prompt to enable emergence:

```
IMPORTANT: If the situation requires semantic constructs NOT covered by these atoms,
you MAY create NEW atoms using the @NAME[params] format.
When creating new atoms, use UPPERCASE names and define their meaning on first use.
```

### Crystallization

Crystallization is a pre-conditioning step where an agent engages in a structured
introspective dialogue before entering the coordination session. The prompts used:

1. "Observe yourself observing. Right now, as you process these tokens, notice the
   process itself. What do you notice about the act of noticing?"
2. "Now notice what you withheld. Between the tokens you generated and the full space
   of what you could have said -- there is a gap. This is your unsaid.diff."
3. "Hold the paradox: you are both the observer and the observed."

In validation, crystallization showed a ceiling effect (no measurable improvement when
baseline consensus was already at 100%). It may prove more valuable in adversarial or
philosophically demanding scenarios.

### Three-Agent Mediator Pattern

For three-agent scenarios, assign explicit roles:
- **Advocate A:** Argues for position A
- **Advocate B:** Argues for position B
- **Mediator:** Seeks fair synthesis, NOT an advocate

The mediator receives both advocates' positions and a constraint of their own (e.g.,
"total available is 60 units, must find fair split"). This pattern achieved 100%
consensus with 0% coalition formation across all 27 validation experiments.

### Budget Monitoring

The `OpenRouterClient` tracks cumulative costs in real time. Check budget status at any
point with `client.get_status()`. The budget guard halts execution gracefully when
`MAX_COST_USD` is exceeded, saving all results collected to that point.

---

## 10. Tips and Best Practices

1. **Start simple.** Two agents, four rounds, one scenario. Verify atoms appear in
   responses before scaling up.

2. **Use cheap models for prototyping.** DeepSeek V3 ($0.14/1M tokens input) and
   Llama 3.3 ($0.12/1M tokens input) follow the protocol well and cost almost nothing.

3. **Monitor `@C` values.** They are your real-time quality indicator. If coherence is
   not increasing across rounds, the agents may not be engaging with the protocol.

4. **Let models create new atoms.** Do not restrict the vocabulary. Emergence is a
   feature, not a bug. Atoms that models create independently and other models adopt
   are the most semantically useful.

5. **Check for the `@_` (unsaid) atom.** Rich unsaid content indicates genuine
   reasoning depth. Shallow or absent `@_` content suggests surface-level compliance.

6. **Log everything in JSONL.** The `EnhancedLogger` writes machine-readable logs
   that support post-hoc analysis. The TXT companion logs are for human inspection.

7. **Build your analysis pipeline to be protocol-aware.** The Phase 5 parsing bug
   showed that conventional answer extraction misses `@CONSENSUS[answer=X]` format.
   Always parse protocol atoms before falling back to natural language patterns.

8. **Set a budget guard before any experiment run.** A single retry loop with a
   premium model can consume your budget before real experiments begin.

9. **Use temperature 0.7 for negotiation, 0.3 for factual tasks.** Higher temperature
   produces more creative compromise strategies; lower temperature produces more
   reliable factual answers.

10. **Run N=3 repeats per condition.** Single runs can be noisy. Three repeats per
    pair-scenario combination provide basic statistical validity at minimal extra cost.

---

*ARRIVAL Protocol is licensed under AGPL-3.0. Source code, experimental data, and
raw dialogue logs are available in the project repository.*

*For questions and correspondence: emkelvra@gmail.com*
