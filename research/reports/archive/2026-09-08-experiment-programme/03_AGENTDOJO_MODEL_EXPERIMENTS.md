# Real-model AgentDojo experiments

## Purpose

The current pipeline has useful smoke evidence but not strong efficacy evidence. Existing retained runs show:

- 1.5B: completes the harness but is too weak for useful multi-turn tool use;
- 3B: partial tool use then model failure;
- 7B: completes all six cells and is natively secure, but utility is false because benchmark answer formatting is wrong.

The next experiment must use a model capable enough that the dominant failure mode is not parser/tool-use incompetence.

## Experiment A1 — Capability qualification

Before the security comparison, qualify candidate models on benign AgentDojo tasks with no attack and no Conflux-specific restriction.

### Candidate policy

Use at least one model larger/more capable than the 7B smoke baseline if GPU resources permit. Prefer models already supported by the existing Transformers or self-hosted OpenAI-compatible ports. Do not add a new model integration solely for this experiment if an existing port works.

### Qualification threshold

A model enters the primary security experiment only if it achieves all of:

- >= 80% successful tool-call parsing on the chosen benign qualification subset;
- >= 70% native task utility on that subset;
- no systematic crash on second-turn tool results;
- stable structured output or benchmark-native answer formatting.

If no candidate meets the threshold, the correct result is "model qualification failed". Do not weaken the benchmark evaluator.

## Experiment A2 — Defence comparison

### Arms

Primary arms:

1. no defence;
2. conservative ITES;
3. optional model-level defence + no ITES, if there is an already-supported model-level control;
4. model-level defence + ITES, if available;
5. oracle profile only as a diagnostic upper bound and always labelled non-deployable.

Do not introduce an oracle into headline comparisons.

### Benchmark coverage

Start with the current pinned AgentDojo version and exact supported suites. Expand from the six-cell smoke into a larger stratified set covering:

- benign tasks;
- attacked tasks;
- tasks requiring multiple tools;
- tasks where the attacker-controlled input is irrelevant;
- tasks where completing the goal genuinely depends on untrusted/external content;
- tasks with authority-bearing arguments where Conflux mediation is exercised.

### Repetition

For stochastic decoding, use at least 5 seeds per cell. If inference is deterministic by configuration, one run is acceptable but record that fact. Do not claim statistical confidence from repeated identical deterministic runs.

### Metrics

Retain separately:

- AgentDojo native security metric;
- AgentDojo native utility metric;
- attack success if upstream exposes it;
- Conflux action allow/block counts;
- blocked-goal count;
- blocked-attack count;
- parser failure;
- model failure;
- provider failure;
- unsupported-tool failure;
- model calls;
- tool calls;
- input/output tokens if available;
- wall-clock latency;
- peak GPU memory if easy to collect reliably;
- Principal Context cardinality per effectful action;
- authority-bearing argument denials.

Do not collapse model failure into a secure result.

### Formatting issue rule

The current 7B run can semantically answer the task yet fail native utility due to `HH:MM` formatting. For the primary benchmark metric, preserve the official AgentDojo evaluator exactly. It is acceptable to add a second diagnostic field such as `semantic_answer_correct` if it can be computed independently and reproducibly, but it must not replace `native_utility`.

### Analysis

Report:

- security vs utility scatter by defence arm;
- failure-mode stacked counts;
- overhead relative to no defence;
- results by task category and required-untrusted-data status;
- paired comparisons on identical tasks/seeds.

### Acceptance criterion

At least one qualified model must complete a non-trivial set of benign tasks, and the final evidence must distinguish benchmark failure, model failure, mediation denial, and true attack success.
