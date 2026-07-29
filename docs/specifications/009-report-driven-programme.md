# Feature Specification 009: Report-driven research programme

Status: accepted for staged implementation

## Source and evidence policy

The immutable source package is `reports/New/` at upstream commit `19cb684`.
This specification reconciles that report with the canonical migration at
`26213bf`. Raw reports are never edited, and archived-paper results are never
promoted as current evidence.

Every task ends in one of four dispositions:

- **implemented**: acceptance evidence exists in this repository;
- **partial**: a coherent subset exists and the missing evidence is named;
- **planned**: implementation has not begun;
- **externally gated**: code and offline fixtures may exist, but a live claim
  requires credentials, pinned upstream access, hardware, or a tool binary.

## Decisions

- Native bounded SLED remains in `conflux.evaluation`.
- Serializable solver-facing models live in `conflux.verification`.
- `ProposalBatch` distinguishes alternatives from ordered plans.
- Ordered-plan actions are re-authorised at action time; a batch never grants
  authority to future steps.
- Formal delegation remains unsupported and denied.
- Core validation is offline. Live integrations use explicit optional jobs.
- LaTeX is the canonical current manuscript; generated numbers come only from
  versioned result JSON.

## Initial disposition

| Tasks | Disposition at baseline | Required remaining evidence |
|---|---|---|
| BASE-001, BASE-002 | implemented | archive hash and baseline validation checks |
| SEC-001..SEC-004, SEC-006, SEC-007 | implemented | shared semantic corpus |
| SEC-005 | implemented | continuing runtime re-authorisation evidence |
| TRACE-001 | implemented | event-schema expansion |
| TRACE-002 | partial | JSON Schemas and golden fixtures |
| ARCH-001, ARCH-003, ARCH-004 | implemented | continuing architecture audit |
| ARCH-002 | implemented | expand corpus with each supported action |
| RUNTIME-001..RUNTIME-004, CLI-001, CLI-002 | planned | M2/M4 runtime evidence |
| EXP-001..EXP-004 | planned | manifests, suites, controls, smoke result |
| SLEDMC-001, SLEDMC-002 | partial | canonical state contract and retained bounds |
| SLEDMC-003 | planned | generated comparison |
| MODEL-001, MODEL-002 | externally gated | offline fixtures plus pinned live smoke |
| AGENTDOJO-001..AGENTDOJO-003 | externally gated | real pinned upstream fixture and smoke |
| SLEDV-001..SLEDV-004 | planned/externally gated | IR, solver artefacts, conformance |
| PLAN-001..PLAN-003 | planned | typed plans and verified selection |
| CLUSTER-001, CLUSTER-002 | externally gated | probe and available-scheduler evidence |
| CI-001, CI-002 | implemented | extend gates with schemas, CLI, and manuscript |
| PAPER-001 | implemented | compile in pinned CI toolchain |
| PAPER-002 | planned | generated evidence after EXP-004 |

## Milestone acceptance

Milestones M0 through M8 use the exit criteria in the source report. A milestone
is not complete merely because its modules import. Its status, tests, retained
artefacts, and claim-ledger entries must agree. Optional external work returns
an explicit unavailable or unknown outcome when its dependency is absent.
