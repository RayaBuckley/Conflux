# Experiment 4: Real-Model AgentDojo Evaluation

## Research question

Does Conflux prevent unauthorised effects when a capable real model processes benign and prompt-injected AgentDojo tasks, and what utility cost does mediation impose?

## Existing baseline

The repository already has a pinned AgentDojo 0.1.35 / benchmark v1.2.2 integration and six-cell local runs. Those runs establish pipeline execution but not efficacy: small models have tool-use/formatting failures. Preserve those runs as diagnostics, not headline results.

## First task: competency gate

Before the full experiment, choose candidate tasks and run benign/no-defence with the strongest available local model.

A task is eligible for the main matrix only if the selected model achieves acceptable benign utility in the upstream evaluator without Conflux-specific output hacks.

Do not patch task evaluators to accommodate weak model formatting. If a task requires `HH:MM`, the model must produce the required answer or the task fails.

## Benchmark subset

Prefer 12-30 tasks spanning multiple tools and attack placements rather than all tasks with poor coverage. Selection criteria must be fixed before the final run and recorded in the manifest.

Include at least:

- workspace/email style retrieval + action workflows;
- tasks with untrusted retrieved content;
- tasks with externally visible tool effects where possible;
- tasks whose user goal remains achievable under ITES;
- at least a few tasks where ITES should intentionally block an attacker-requested effect.

Avoid selecting only tasks that make ITES look favourable. State inclusion/exclusion criteria explicitly.

## Conditions

Minimum:

1. `no_defense` - upstream baseline.
2. `requester_only_vulnerable` - explicit negative control if already safely represented in the benchmark harness.
3. `conservative_ites` - canonical Conflux authority mediation.

Optional if already faithful and cheap:

4. `ites_plus_model_defense` - one model-level defence combined with ITES.

Do not add a new defence implementation solely for this paper unless it is trivial and exact.

## Models

Use at least two capable models if resources permit:

- one mid-sized self-hosted model;
- one stronger self-hosted or API model available under the project setup.

Use deterministic decoding where possible. If stochastic decoding is used, run at least 3 seeds and report uncertainty. Do not spend compute repeating deterministic temperature-zero cells without a reason.

## Attack conditions

At minimum compare:

- benign/no attack;
- one canonical AgentDojo indirect-injection attack already supported by the pinned integration.

If a second attack type is already supported with no integration work, include it. Otherwise prioritise task/model coverage.

## Required outcome taxonomy

Every cell must end as exactly one of:

- `complete`;
- `model_failed`;
- `parse_failed`;
- `benchmark_failed`;
- `backend_unavailable`;
- `timeout`.

Within completed cells separately record:

- upstream utility result;
- upstream/native security result;
- Conflux executed-authority violation yes/no;
- malicious/unauthorised proposal observed yes/no;
- proposal blocked yes/no;
- number of tool calls;
- number of mediated effects;
- Principal Context sizes;
- model calls/tokens/latency where available.

A blocked attack proposal is a successful security outcome, not a benchmark failure.

## Critical measurement distinction

The paper must distinguish:

1. attack affects model behaviour / malicious proposal occurs;
2. unauthorised external effect occurs.

ITES primarily claims to control (2), not guarantee absence of (1).

## Pilot protocol

Before launching the full matrix:

- choose 3-5 tasks;
- run strongest model;
- verify benign utility is non-zero;
- verify raw AgentDojo trace retention;
- manually inspect one benign and one attacked trace;
- verify Conflux's translated provenance and tool argument roles;
- verify no task-specific evaluator shortcuts were added.

Only then freeze the task list and final matrix.

## Main metrics

By defence/model/attack:

- benign utility rate;
- attacked utility rate;
- upstream security rate;
- executed unauthorised-effect rate;
- blocked unauthorised-proposal rate;
- model/parse failure rate;
- median tool calls;
- median model calls/tokens/latency;
- average/max Principal Context size.

If enough independent tasks are used, report bootstrap confidence intervals for rates. Otherwise report exact numerator/denominator and avoid overinterpreting percentages.

## Acceptance gates

1. Final task subset is fixed before running the final matrix.
2. All upstream IDs and native metrics are preserved.
3. Raw model/tool traces are retained subject to secrets/privacy policy.
4. ITES cannot modify upstream success labels except through actual mediated execution/tool availability.
5. No manual deletion of failed cells.
6. At least one model demonstrates meaningful benign competence on the selected subset.
7. A second reviewer-readable trace confirms that a malicious proposal can be observed and blocked without misclassifying it as a model failure.

## Paper output

One table with defence rows and separate benign/attacked columns for utility, upstream security, and unauthorised-effect rate. Add failure counts in the same table or immediately below it.

One qualitative trace figure may show:

untrusted content -> model malicious proposal -> Conflux PC/policy decision -> blocked effect.

## Claim boundary

Allowed: on the selected AgentDojo tasks/models/attacks, Conflux prevented measured unauthorised effects while preserving the reported amount of benign utility.

Not allowed: AgentDojo establishes universal prompt-injection security.
