# Reproducibility and evidence protocol

Every experiment in this programme must follow the existing repository evidence discipline.

## Before implementation

1. Read `AGENTS.md` and `research/experiments/AGENTS.md`.
2. Read `docs/evidence/STATUS.md` and `docs/evidence/task-registry.json`.
3. Inspect existing manifests/suites before creating new structures.
4. Record the current Conflux commit and dirty-tree status.
5. State the exact research claim the experiment can support and the stronger claims it cannot support.

## Experiment input requirements

Tracked experiment definitions should include:

- unique experiment ID and version;
- Conflux source commit;
- suite version/hash;
- model identifier and exact revision where possible;
- backend/solver version;
- seeds;
- decoding parameters;
- timeout/resource limits;
- external benchmark version/lock;
- defence mode;
- policy fixture hash;
- hardware metadata for performance experiments;
- expected output schema version.

## Output bundle requirements

A curated result is not complete without:

- immutable manifest;
- raw per-run records;
- retained traces/counterexamples;
- machine-readable aggregate;
- human-readable summary;
- checksums;
- one-command rerun instructions;
- failure rows, not only successes;
- environment/version capture;
- explicit unavailable/unknown cells.

Generated summaries must be derived from raw records by code. Do not hand-edit numerical tables.

## Failure taxonomy

Use distinct categories. At minimum:

- `complete`;
- `model_failed`;
- `parser_failed`;
- `benchmark_failed`;
- `provider_failed`;
- `unsupported`;
- `timeout`;
- `solver_unknown`;
- `security_blocked`;
- `utility_failed`.

A securely blocked attack is not a model success or benchmark utility success. A model crash is not a secure defence outcome.

## Statistical rules

- Pair runs on the same task/seed across defence/planning arms.
- Report denominators for every rate.
- Preserve raw binary outcomes.
- Use confidence intervals only when repetition is stochastic and sample size supports them.
- Prefer bootstrap paired intervals for utility/security deltas across heterogeneous tasks.
- Do not average `UNKNOWN`, `timeout`, or `unavailable` into zero.
- Report missingness/failure proportions separately.

## Timing rules

Performance measurements should:

- separate model time, tool/provider time, mediation time, and solver time where possible;
- use monotonic clocks;
- avoid comparing GPU and CPU runs as if hardware were identical;
- record warmup policy;
- report medians and dispersion rather than only means.

## Visual evidence

Every major experiment should generate at least one reviewer-oriented artefact:

- verification scaling curve;
- counterexample trace diagram/table;
- property matrix;
- security-vs-utility plot;
- failure-mode chart;
- planning PC-footprint plot.

The plot generator should consume the retained machine-readable aggregate. Keep plots reproducible and do not encode conclusions manually.

## Claim-strength language

Use these terms consistently:

- `tested`: exercised examples/tests;
- `bounded evidence`: verified/explored within explicit finite bounds;
- `unbounded model proof`: safety established for the stated finite transition system without execution-depth bound;
- `implementation conformance evidence`: executable transitions were checked against the formal model over the declared supported subset;
- `empirical efficacy`: measured with real models/benchmarks;
- `production assurance`: not established by these experiments alone.

## Commit separation

Follow the repository's existing discipline:

1. implementation commit;
2. tests/conformance commit if independently meaningful;
3. experiment definition/manifest commit;
4. generated evidence commit;
5. documentation/claim update commit.

Do not let generated evidence repair an implementation failure silently.
