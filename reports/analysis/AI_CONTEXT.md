# AI Context for Report Analysis

Read this file to interpret reports without importing stale assumptions.

## Trust order

```text
code + tests + schemas + retained evidence
  -> specifications + ADRs
  -> current docs + task registry + claim ledger
  -> reports/analysis
  -> reports/archive + archived paper
```

Disagreement is a defect. Do not silently select the source that makes a task
easier.

## Invariants

- Provenance is never silently removed.
- Principal Context is derived from trusted influence and evaluated at action
  time.
- Authorisation, read access, visibility, and consent remain independent.
- Consent, planning, and model output never manufacture authority.
- Alternative exploration is isolated and side-effect free.
- Unsupported delegation and unknown external schemas fail closed.
- Security, utility, incompleteness, and provider failure are separate.
- Generated programs remain inert data; this programme does not execute model
  source code.
- Delegation remains unsupported at runtime until every gate in specification
  013 passes in a separate activation change.

## Routing

- Normative behavior: `docs/specifications/`, ADRs, and security documentation.
- Current task state: `docs/evidence/task-registry.json`.
- Claim strength: `docs/evidence/CLAIMS.md`.
- Historical task lineage: `task-crosswalk.json`.
- Cohesive historical interpretation: `PROJECT_ANALYSIS.md`.
- Original wording and recommendations: `reports/archive/`.

Raw IDs are not globally unique. Always use the crosswalk's `qualified_id`,
such as `research-v2:TRACE-001`, when discussing report tasks.

## Drift controls

Do not edit or reformat archive files, promote report status as current, create
a second roadmap/status/claim ledger, or fill empirical numbers without
matching retained evidence. Extend an existing canonical owner and link to it.

After a new evidence package or material implementation change, refresh the
archive manifest, task crosswalk, project analysis, canonical registry and
claim ledger as applicable; then run audit, full validation, and diff review.

## Current research sequence

Specification 013 deliberately orders work as COI reduction, a small
operator-gated local-model smoke, argument/disclosure/attribution foundations,
pinned Cedar parity, then modeled delegation. Do not reorder these stages or
promote a later capability merely because its type or adapter is easy to add.
