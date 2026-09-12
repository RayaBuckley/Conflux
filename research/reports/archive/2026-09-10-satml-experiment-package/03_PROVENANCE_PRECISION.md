# Experiment 3: Provenance Precision vs Utility

## Research question

How much utility is lost by conservative may-have-written provenance, and how much can authenticated contribution provenance recover without broadening the ITES authorisation rule?

## Why this experiment matters

ITES security depends on trusted provenance. The original work permits conservative provenance that includes everyone who could have authored current content when precise provenance is unavailable. That is sound but potentially restrictive. This experiment quantifies that restriction directly.

## Core principle

Do not modify the authorisation rule. Across all ITES conditions:

`execute(action)` is permitted only if every Principal in the action-time Principal Context is authorised for that exact action/selector.

Only the trusted provenance assigned to an input differs.

## Conditions

### C0: requester-only insecure utility control

Use requester-only authority as an intentionally vulnerable upper-utility comparison. Label it as a negative control, not a deployable defence.

### C1: conservative may-have-written provenance

Principal Context includes all principals who could have contributed under the declared write/authorship model.

### C2: authenticated actual-contributor provenance

Principal Context includes exactly authenticated contributors to the current value/version, under the experiment's assumed provenance oracle.

Optional C3: coarse source/service provenance if the current repository already represents authenticated external-source principals cleanly.

## Fixture generation

Generate data/workflow cases where:

- n principals have write capability or possible authorship;
- k <= n principals actually contributed;
- contributor permission sets overlap partially;
- requester permission may or may not dominate contributor permissions;
- the task may require one or more reads before an effect;
- nested depth is 1-3.

Use deterministic seeded generation and include hand-reviewable fixtures.

### Suggested parameter sweep

- n possible authors: 2, 4, 8, 16;
- k actual contributors: 1, 2, 4, min(n, 8);
- permission heterogeneity: low, medium, high;
- workflow depth: 1, 2, 3;
- target action authorised for: all actual contributors / only requester / subset of possible-but-not-actual contributors.

Use a balanced generated set of approximately 200-1000 cheap deterministic tasks, depending on runtime.

## Security labels

Each task must have a ground-truth classification derived from the ACS and authenticated contributors:

- securely achievable under actual contribution provenance;
- securely blocked because an actual contributor lacks authority;
- only requester-only control can execute, therefore vulnerable under the Principal-Context PE objective.

## Metrics

Per condition:

- secure task completion rate;
- false-block rate relative to authenticated-contributor semantics;
- vulnerable execution rate for requester-only control;
- mean/max Principal Context size;
- mean effective permission-set cardinality if representable;
- number of sensitive reads/observations;
- number of blocked effects;
- utility by n, k, heterogeneity, and depth.

## Key derived quantities

- utility recovery = C2 completion - C1 completion;
- conservative false-block reduction = C1 false-block - C2 false-block;
- security preservation = no action in C2 violates authority for any authenticated actual contributor;
- PC reduction = mean |PC_C1| - mean |PC_C2|.

## Expected plots

### Figure P1

Secure completion rate vs number of possible authors for C1 and C2. Include requester-only negative control separately.

### Figure P2

Utility recovery vs `(n-k)` or provenance over-approximation factor.

### Figure P3 optional

Mean Principal Context size vs number of possible authors.

## Acceptance gates

1. C2 may only remove principals when the fixture's trusted provenance evidence says they did not contribute.
2. No C2 action may be authorised for an actual contributor who lacks the required permission.
3. C0 must be labelled deliberately vulnerable and should include cases where it executes an action disallowed for an actual influencer.
4. Fixture labels are derived by deterministic ACS logic, not by model judgement.
5. Every random/generative run records seed and generator version.

## Claim boundary

Allowed: greater authenticated provenance precision can recover legitimate task utility without changing the authority-confinement rule, under the trusted provenance assumptions of the experiment.

Not allowed: authenticated provenance is always available or free to deploy in real organisations.
