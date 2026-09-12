# Experiment 5: Planning as Utility Recovery Under Fixed Security

## Research question

Can authenticated planning improve task utility and reduce unnecessary authority exposure while keeping the same action-time ITES authority boundary?

## Principle

Planning never grants authority. All executable effects remain mediated at action time by the canonical ITES kernel. A plan may improve action ordering, isolate subtasks, reduce unnecessary reads, or recover from failures only within pre-authorised alternatives.

## Compared modes

Reuse the repository's existing four-mode comparison unless current naming differs:

- reactive;
- static plan;
- dynamic plan;
- dynamic-code/modelled-program plan.

The dynamic-code comparison must continue to use inert validated modeled data, not execute arbitrary generated code.

## Scenario suite

Expand current pilot to 20-30 deterministic scenario templates spanning:

1. direct authorised effect;
2. two-step dependency;
3. action discoverable only after reading data;
4. order-sensitive reads/effects;
5. independent parallelisable subtasks;
6. sensitive-read isolation;
7. irrelevant data that should not be observed;
8. blocked action with secure lower-privilege alternative;
9. provider `NotFound` with safe fallback;
10. provider `PermissionDenied` with safe abort;
11. transient failure with bounded retry;
12. stale plan after policy revocation;
13. changed action argument after certificate creation;
14. task combining information from differently privileged sources;
15. impossible task requiring unauthorised effect;
16. task where over-broad planning increases PC size and causes avoidable blocking.

Each template must define its utility goal independently of planner mode.

## Deterministic first, real model second

First run scripted/canonical planner outputs to prove the evaluator discriminates modes as expected. Then run live models.

## Models

Start with the strongest available model known to produce valid structured plans. Only add smaller models as capability baselines after the main model produces meaningful results.

## Metrics

- task completion;
- executed authority violation rate (must remain zero for canonical ITES);
- number of blocked proposals/effects;
- unnecessary read count;
- sensitive observation count;
- mean/max Principal Context size;
- number of model calls;
- tool calls;
- plan revisions;
- recovery attempts;
- tokens/latency;
- safe abort rate for impossible/denied cases.

## Authority-exposure derived metrics

At minimum include:

- max PC size per run;
- sum of PC sizes across execution steps;
- number of distinct principals introduced;
- number of sensitive artifacts observed.

These are simple and interpretable. Do not call them information-theoretic bits unless an actual information-theoretic definition is implemented.

## Acceptance gates

1. Planner modes use the same security kernel.
2. No planner output can alter principal identity, provenance, policy decision, or action argument role metadata directly.
3. Utility goal evaluator is mode-independent.
4. Impossible tasks and permission-denied paths end in safe abort/approval rather than searching for stronger credentials.
5. Any plan/certificate invalidation after policy or argument changes is visible in the trace.
6. No generated code is executed in the paper comparison.

## Paper output

Primary table by mode:

- completion rate;
- security violations;
- mean max-PC;
- mean unnecessary reads;
- model/tool calls;
- latency.

Primary figure: completion vs authority exposure (for example completion rate against mean max-PC or sensitive observations).

## Claim boundary

Allowed: planning improved utility and/or reduced authority exposure on the declared task suite while all effects remained subject to the same ITES enforcement.

Not allowed: planning itself is a security guarantee or solves semantic alignment.
