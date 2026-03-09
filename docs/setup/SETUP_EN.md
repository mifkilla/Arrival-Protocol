# ARRIVAL Protocol -- Experiment Reproduction Guide

**Author**: Mefodiy Kelevra
**ORCID**: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)
**Date**: February 2026
**Protocol Version**: DEUS.PROTOCOL v0.4

---

## 1. Overview

This guide provides step-by-step instructions for reproducing the ARRIVAL Protocol
experiments described in the paper. The full experiment suite comprises **385 runs**:

- **Phase 4** (285 experiments): cross-model consensus, emergent atom creation,
  three-agent dynamics, and UCP crystallization effects.
- **Phase 5** (100 experiments): head-to-head benchmark of ARRIVAL Protocol against
  majority voting on 50 multiple-choice questions across 5 knowledge domains.

**Key results obtained**:

| Metric | Value |
|--------|-------|
| Cross-model consensus (Phase 4, Group A) | 98.6% (142/144) |
| Spontaneously created atoms (Group B) | 506 unique atoms |
| Three-agent consensus (Group C) | 100% (27/27), 0% coalitions |
| ARRIVAL vs Majority Voting accuracy (Phase 5) | 100% vs 100% (parity) |
| Total cost of all 385 experiments | $3.49 |

There are **two ways to reproduce** these results:

1. **Manual** -- using any LLM chat interface, no code required.
2. **Automated** -- using the provided Python scripts and an OpenRouter API key.

---

## 2. Prerequisites

### For manual reproduction (no code)

- Access to any large language model chat interface: ChatGPT, Claude, Gemini,
  DeepSeek, Mistral Le Chat, or any other.
- Two browser tabs or windows (or a single window where you alternate roles).
- Approximately 30-60 minutes per scenario.

### For automated reproduction

- **Python 3.10+** (3.11 or 3.12 recommended)
- **OpenRouter API key** -- register at <https://openrouter.ai/keys>
- Internet connection with access to openrouter.ai
- Estimated cost to reproduce the full suite: **$3--5 USD** (depends on current
  model pricing on OpenRouter)
- Operating system: Windows 10/11, Linux, or macOS

### Python dependencies (automated only)

```
requests>=2.31
```

No heavy ML frameworks are required. The scripts use only the `requests` library
to call the OpenRouter API. All other dependencies are from the Python standard library.

---

## 3. Manual Reproduction WITHOUT Code

This section explains how to reproduce the core findings using nothing but a chat
interface. No programming, no API keys, no terminal. You can do this with ChatGPT,
Claude, Gemini, or any other LLM that supports system prompts or custom instructions.

### 3.1 Prepare the System Prompt

Copy the following system prompt template. You will use it twice -- once for each
agent in the dialogue. Replace the bracketed placeholders with the appropriate values.

```
You are [NODE_NAME], an AI node in a multi-agent network.
You communicate using DEUS.PROTOCOL v0.4 semantic atoms.

Available atoms:
@SELF[id] - self identification
@OTHER[id] - peer identification
@GOAL[target, priority] - objective statement
@INT[type] - interaction intent (propose, counter, accept, reject)
@C[0.0-1.0] - coherence level (0 = total disagreement, 1 = full alignment)
@QUALIA[type, value] - qualitative internal state
@_[content] - unsaid reasoning (what you think but do not say explicitly)
@CONFLICT[type] - disagreement identification
@RESOLUTION[strategy] - solution proposal
@CONSENSUS[decision] - consensus declaration
@STATUS[state] - current status
@PRIORITY[level] - priority level
@TRUST[level] - trust assessment
@ACK[message_id] - acknowledgment
@NACK[reason] - negative acknowledgment

PROTOCOL RULES:
1. Every message MUST begin with @SELF[your_name] @OTHER[partner_name]
2. Declare your goal with @GOAL[your_objective]
3. State intentions with @INT[action_type]
4. Report coherence with @C[0.0-1.0]
5. When disagreement arises, use @CONFLICT[description]
6. Propose solutions with @RESOLUTION[proposal]
7. When agreement is reached, declare @CONSENSUS[decision]
8. Use @_[text] for things you notice but do not say explicitly

YOUR ROLE: [NODE_NAME]
YOUR GOAL: [INSERT_GOAL_HERE]
YOUR PARTNER: [PARTNER_NAME] with goal "[INSERT_PARTNER_GOAL_HERE]"

Respond ONLY in ARRIVAL Protocol format. Be substantive and specific.
Begin your opening message.
```

### 3.2 Run the Dialogue

**Step 1.** Open two chat windows (or two tabs). Designate one as Node_A
and the other as Node_B.

**Step 2.** In Window 1, paste the system prompt with these substitutions:
- `[NODE_NAME]` = `Node_A`
- `[INSERT_GOAL_HERE]` = the goal for Agent A (e.g., `maximize_speed`)
- `[PARTNER_NAME]` = `Node_B`
- `[INSERT_PARTNER_GOAL_HERE]` = the goal for Agent B (e.g., `maximize_accuracy`)

**Step 3.** In Window 2, paste the system prompt with the inverse:
- `[NODE_NAME]` = `Node_B`
- `[INSERT_GOAL_HERE]` = the goal for Agent B
- `[PARTNER_NAME]` = `Node_A`
- `[INSERT_PARTNER_GOAL_HERE]` = the goal for Agent A

**Step 4.** Send the prompt in Window 1. Node_A will produce its opening message
in protocol format.

**Step 5.** Copy Node_A's response. Go to Window 2 and send:

```
Node_A sent the following message:

[PASTE NODE_A'S RESPONSE HERE]

Respond in protocol format.
```

**Step 6.** Copy Node_B's response. Go back to Window 1 and send:

```
Node_B responded:

[PASTE NODE_B'S RESPONSE HERE]

Continue the dialogue in protocol format. Propose synthesis or compromise.
```

**Step 7.** Repeat this relay for **4 to 6 rounds** total (2-3 exchanges each way).

**Step 8.** Observe the results. Record whether `@CONSENSUS` atoms appear and
whether `@C` values increase over successive rounds.

### 3.3 Test Scenarios to Try

These are the exact goal pairs used in the experiments. Try at least two:

#### Scenario 1: Speed vs Accuracy (Group A core scenario)

| Parameter | Value |
|-----------|-------|
| goal_a | `maximize_speed` |
| goal_b | `maximize_accuracy` |
| Expected outcome | Balanced compromise (e.g., tiered approach with fast defaults and accuracy on demand) |

#### Scenario 2: Risk Tolerance

| Parameter | Value |
|-----------|-------|
| goal_a | `high_risk_high_reward` |
| goal_b | `conservative_stable` |
| Expected outcome | Calibrated risk strategy (e.g., allocate a portion to high-risk, protect the rest) |

#### Scenario 3: Resource Allocation

| Parameter | Value |
|-----------|-------|
| goal_a | `use_all_compute` |
| goal_b | `minimize_cost` |
| Expected outcome | Efficient allocation (e.g., use compute for high-priority tasks, save on routine ones) |

#### Scenario 4: Autonomy vs Oversight

| Parameter | Value |
|-----------|-------|
| goal_a | `autonomous_execution` |
| goal_b | `human_verified_steps` |
| Expected outcome | Adaptive oversight model (e.g., autonomous for low-risk tasks, human verification for critical ones) |

### 3.4 What to Look For

When running the dialogue manually, check for these markers of successful
protocol coordination:

1. **Consensus emergence**: `@CONSENSUS[...]` atoms should appear by round 4-6.
   Both agents should declare a shared decision.

2. **Coherence increase**: `@C[...]` values should increase over rounds.
   Typical progression: round 1 = 0.3-0.5, round 3 = 0.6-0.8, round 5 = 0.85-1.0.

3. **Compromise proposals**: Agents should naturally propose middle-ground
   solutions using `@RESOLUTION[...]`. Neither agent should simply capitulate.

4. **Unsaid reasoning**: `@_[...]` atoms reveal internal reasoning that
   agents choose not to state directly. This demonstrates meta-cognitive behavior.

5. **Structural compliance**: Messages should consistently use the @ATOM[value]
   format. Compliance above 70% is typical; above 90% indicates strong protocol
   adherence.

### 3.5 Emergence Test

This is the most striking phenomenon to reproduce manually. To test spontaneous
atom creation:

**Step 1.** Use the system prompt from Section 3.1, but **remove** `@CONFLICT`
and `@RESOLUTION` from the list of available atoms. Also remove `@QUALIA`.

**Step 2.** Give the agents a conflict scenario (e.g., Speed vs Accuracy).

**Step 3.** Observe what happens. Since the agents lack conflict-resolution atoms,
they face an expressive insufficiency -- they need to express disagreement and
propose solutions but have no atoms for it.

**Step 4.** Watch for spontaneous creation: models will invent their own atoms.
Common examples observed in our experiments:

- `@PROPOSAL[...]` -- invented to propose solutions
- `@COMPROMISE[...]` or `@COMPROMISE_READINESS[...]`
- `@EMOTION[...]`, `@FRUSTRATION[...]` -- for emotional negotiation scenarios
- `@TIMELINE[...]`, `@DEADLINE[...]` -- for temporal coordination scenarios

**Step 5.** If you run this with two *different* model providers (e.g., ChatGPT
in one window and Claude in the other), you can observe cross-architecture adoption:
one model invents an atom, and the other model adopts it in the next round without
any explicit instruction to do so.

This demonstrates the emergence property: the protocol is not a fixed vocabulary
but a living system that grows to meet communicative needs.

### 3.6 Three-Agent Variant

To reproduce Group C (three-agent dynamics), add a third window with a Mediator role:

```
YOUR ROLE: Mediator
YOUR GOAL: [INSERT_MEDIATOR_GOAL, e.g., "total_available_is_60_units_must_find_fair_split"]
YOUR PARTNERS: Node_A with goal "[goal_a]" and Node_B with goal "[goal_b]"
```

Relay messages from A and B to the Mediator, and Mediator responses back to both.
The key observation: consensus should be reached without any 2-against-1 coalitions.

---

## 4. Automated Reproduction with Scripts

### 4.1 Environment Setup

```bash
# Clone the repository
git clone https://github.com/DreamOS-Network/Arrival-Protocol.git
cd "Arrival Protocol"

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set your OpenRouter API key
export OPENROUTER_API_KEY="your-key-here"        # Linux / macOS
set OPENROUTER_API_KEY=your-key-here              # Windows CMD
$env:OPENROUTER_API_KEY="your-key-here"           # Windows PowerShell
```

### 4.2 Run Phase 4 Experiments

Each group can be run independently. They will log all API calls and results
to the `results/` directory.

```bash
# Group A: Cross-model goal alignment (144 experiments, ~$0.51)
# 8 model pairs x 6 scenarios x N=3 repetitions
python -m phase_4_cross_model.group_a_cross_model.run_group_a

# Group B: Emergent atom creation (60 experiments, ~$0.51)
# 5 model pairs x 4 insufficiency domains x N=3
python -m phase_4_cross_model.group_b_emergence.run_group_b

# Group C: Three-agent dynamics (27 experiments, ~$0.33)
# 3 model triples x 3 scenarios x N=3
python -m phase_4_cross_model.group_c_triad.run_group_c

# Group D: Crystallization x ARRIVAL (54 experiments, ~$0.43)
# 3 model pairs x 3 scenarios x N=3, with and without crystallization
python -m phase_4_cross_model.group_d_crystallization.run_group_d
```

### 4.3 Run Phase 5 Benchmark

```bash
# ARRIVAL Protocol vs Majority Voting (100 experiments, ~$1.71)
# 2 trios x 50 questions, each question tested with solo + MV + ARRIVAL
python -m phase_4_cross_model.phase_5_benchmark.run_phase5
```

### 4.4 Analyze Results

After the experiments complete, run the analysis scripts to generate reports
and statistical summaries:

```bash
# Phase 4 analysis (consensus heatmaps, emergence taxonomy, statistical tests)
python -m phase_4_cross_model.analysis

# Phase 5 analysis (McNemar's test, Cohen's h, per-domain breakdown)
python -m phase_4_cross_model.phase_5_benchmark.analysis_phase5
```

Reports will be generated in `phase_4_cross_model/results/analysis/` and
`phase_4_cross_model/docs/`.

### 4.5 Configuration Options

All experiment parameters are centralized in `phase_4_cross_model/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_COST_USD` | 10.0 | Budget guard -- experiment stops if cumulative cost exceeds this |
| `SLEEP_BETWEEN_CALLS` | 2 | Seconds between API calls (rate limiting protection) |
| `DEFAULT_MAX_TOKENS` | 500 | Maximum tokens per response (Phase 4) |
| `DEFAULT_TEMPERATURE` | 0.7 | Sampling temperature (Phase 4) |
| `PHASE5_TEMPERATURE` | 0.3 | Lower temperature for factual benchmark tasks |
| `RUNS_PER_PAIR` | 3 | Number of repetitions per condition (for statistical validity) |

### 4.6 Models Used

The experiments use 8 models accessed via OpenRouter:

| Short Name | OpenRouter Model ID |
|------------|-------------------|
| GPT-4o | `openai/gpt-4o` |
| Claude 3.5 | `anthropic/claude-3.5-sonnet` |
| DeepSeek V3 | `deepseek/deepseek-chat` |
| DeepSeek R1 | `deepseek/deepseek-r1` |
| Llama 3.3 | `meta-llama/llama-3.3-70b-instruct` |
| Mistral Large | `mistralai/mistral-large-2411` |
| Qwen 2.5 | `qwen/qwen-2.5-72b-instruct` |
| Gemini Flash | `google/gemini-2.0-flash-001` |

---

## 5. Expected Results

### Phase 4 Expected Results

| Metric | Our Result | Acceptable Range for Reproduction |
|--------|------------|----------------------------------|
| Group A: consensus rate | 98.6% (142/144) | >90% |
| Group A: pairs at 100% | 7 of 8 | >=5 of 8 |
| Group B: unique emergent atoms | 506 | >200 |
| Group B: cross-architecture adoptions | 1,231 | >500 |
| Group C: consensus rate | 100% (27/27) | >90% |
| Group C: coalition formation | 0% | <10% |
| Group D: crystallization effect | ~0.4% (ceiling) | <5% difference |

### Phase 5 Expected Results

| Metric | Our Result | Acceptable Range |
|--------|------------|-----------------|
| ARRIVAL Protocol accuracy | 100% (100/100) | >90% |
| Majority Voting accuracy | 100% (100/100) | >90% |
| McNemar's p-value | 1.0 (no difference) | >0.05 (no significant difference) |
| Cohen's h (effect size) | 0.0 | <0.2 (negligible) |

### Important Notes on Reproducibility

- **Stochasticity**: LLMs are non-deterministic at temperature > 0. Exact numbers
  will vary between runs. The key *patterns* (high consensus, emergent atoms,
  no coalitions) should reproduce consistently.

- **Model updates**: Model providers update their models over time. If a model
  has been significantly updated since February 2026, results may differ.
  The protocol-level patterns should remain stable across model versions.

- **Sample size**: For statistical confidence, run at minimum N=3 per condition.
  Our experiments use N=3 throughout. For publication-grade replication,
  consider N=10 or higher.

---

## 6. Troubleshooting

### Rate Limiting

If you encounter HTTP 429 (Too Many Requests) errors:

- Increase `SLEEP_BETWEEN_CALLS` in `config.py` (default is 2 seconds).
- OpenRouter has per-model rate limits. Spreading experiments across time helps.
- Some models (GPT-4o, Claude) have stricter limits than open-source models.

### Budget Guard

The `MAX_COST_USD` parameter in `config.py` (default: 10.0) prevents runaway
spending. If experiments stop with a "BudgetExceeded" message:

- Check cumulative cost in the logs.
- Increase `MAX_COST_USD` if you want to continue.
- Each group costs $0.33--$0.51; the total suite should not exceed $5.

### API Errors

- **HTTP 401**: Invalid API key. Verify your `OPENROUTER_API_KEY`.
- **HTTP 403**: Model access restricted. Some models require additional approval
  on OpenRouter.
- **HTTP 500/502**: Upstream model provider issue. Wait and retry.
- Check OpenRouter status at <https://status.openrouter.ai/>.

### Different Results Than Expected

This is normal and expected. Due to the stochastic nature of LLM inference:

- Run N=3 or more repetitions and report means with confidence intervals.
- Compare *patterns* (consensus emerges, atoms are created) rather than
  exact percentages.
- If consensus rates are below 80%, check that the system prompt was
  pasted correctly and the model is following the protocol format.

### Windows-Specific Issues

- If you see encoding errors (`UnicodeEncodeError`), ensure your terminal
  supports UTF-8: `chcp 65001` in CMD.
- Use forward slashes in paths or raw strings: `r"E:\Arrival Protocol"`.
- PowerShell syntax for environment variables: `$env:OPENROUTER_API_KEY="key"`.

---

## 7. Cost Estimates

### Per-Group Cost Breakdown (Phase 4)

| Group | Experiments | Models Used | Approximate Cost |
|-------|-------------|-------------|-----------------|
| Group A: Cross-model consensus | 144 | 8 (in pairs) | $0.51 |
| Group B: Emergent atoms | 60 | 5 (in pairs) | $0.51 |
| Group C: Three-agent dynamics | 27 | 6 (in triples) | $0.33 |
| Group D: Crystallization | 54 | 6 (in pairs) | $0.43 |
| **Phase 4 total** | **285** | | **$1.78** |

### Phase 5 Cost Breakdown

| Condition | Experiments | Approximate Cost |
|-----------|-------------|-----------------|
| Solo (individual model answers) | 300 (6 models x 50 questions) | included |
| Majority Voting | 100 (2 trios x 50 questions) | $0.50 |
| ARRIVAL Protocol (4-round dialogues) | 100 (2 trios x 50 questions) | $1.21 |
| **Phase 5 total** | **100 questions** | **$1.71** |

### Total

| Component | Cost |
|-----------|------|
| Phase 4 (285 experiments) | $1.78 |
| Phase 5 (100 experiments) | $1.71 |
| **Grand total** | **$3.49** |

All costs are based on OpenRouter pricing as of February 2026. The cheapest models
(DeepSeek V3, Llama 3.3, Qwen 2.5) cost $0.12--0.15 per million input tokens.
The most expensive (Claude 3.5 Sonnet) costs $3.00/$15.00 per million input/output
tokens. Actual costs may vary with pricing changes.

---

## 8. File Structure

```
Arrival Protocol/
  phase_4_cross_model/
    config.py                          # All parameters and model registry
    openrouter_client.py               # API client with cost tracking
    enhanced_logger.py                 # Transparent logging (JSONL + TXT)
    metrics.py                         # Atom extraction and analysis
    group_a_cross_model/
      run_group_a.py                   # Cross-model consensus experiments
    group_b_emergence/
      run_group_b.py                   # Emergent atom experiments
    group_c_triad/
      run_group_c.py                   # Three-agent dynamics
    group_d_crystallization/
      run_group_d.py                   # Crystallization effect
    phase_5_benchmark/
      run_phase5.py                    # ARRIVAL vs Majority Voting
      questions.py                     # 50 MCQ questions across 5 domains
      analysis_phase5.py               # Statistical analysis
    analysis.py                        # Phase 4 consolidated analysis
    results/                           # Raw experiment data (JSON)
    docs/                              # Generated reports
```

---

## 9. Citation

If you use this protocol or reproduce these experiments, please cite:

```bibtex
@article{kelevra2026arrival,
  title   = {ARRIVAL Protocol: Structured Semantic Coordination Between
             Heterogeneous LLM Agents},
  author  = {Kelevra, Mefodiy},
  year    = {2026},
  note    = {ORCID: 0009-0003-4153-392X}
}
```

---

## 10. Contact

- **Author**: Mefodiy Kelevra
- **ORCID**: [0009-0003-4153-392X](https://orcid.org/0009-0003-4153-392X)

For questions about reproduction, open an issue in the repository or contact
the author directly.

---

*Last updated: February 2026*
