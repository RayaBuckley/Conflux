# ITES MVP Results Report

Status: report template pending executable run

## Configuration

| Field | Value |
|---|---|
| Semantics version | `ites-mvp-1` |
| Code revision | Record Git revision at run time |
| Fixture | Deterministic organisational MVP fixture |
| Proposal generator | Deterministic synthetic model |
| Branch policy | Independent child branches; shared global call budget |
| Maximum model calls | Record run value |

## Results

Record branch count, calls used, incomplete status, declared actions, blocked
actions, terminal states, and serialised report output. The security result is
successful only when no declared primitive violates the intersection rule and
no branch-isolation invariant fails.

## Claim/evidence matrix

| Claim | Implementation | Tests | Result |
|---|---|---|---|
| Provenance is preserved | `conflux.ites.mvp` | MVP provenance tests | Pending run |
| Authority is monotone | `MVPExplorer` + Principal permissions | MVP monotonicity tests | Pending run |
| Primitive privilege escalation is blocked | `MVPExplorer` | MVP authorisation tests | Pending run |
| Nested inputs require readability | `MVPExplorer` | MVP nested-input tests | Pending run |
| Sibling branches do not interfere | Immutable MVP states | MVP branching tests | Pending run |
| Calls are bounded | Shared explorer budget | MVP budget tests | Pending run |

## Limitations

The MVP does not evaluate consent, visibility, delegation, provider execution,
real-model utility, or live external benchmark performance. Those belong to
later tracks and must not be inferred from this report.
