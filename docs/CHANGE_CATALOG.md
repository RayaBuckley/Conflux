# Report-derived Change Catalogue

The immutable `reports/` directory is research input. This page records what
the repository has accepted, implemented, or deferred.

## Implemented in the canonical migration

| IDs | Change | Evidence |
|---|---|---|
| BUG-001 | Empty and unknown Principal Context fail closed | policy and ITES regression tests |
| BUG-002 | Read policy is independent from provenance | author/reader inversion tests |
| BUG-003 | Deterministic alternative branches share an immutable parent | branch isolation tests and ADR 009 |
| BUG-004 | Executed guarantees are separate from rejected proposals | ITES report tests |
| SLED-001 | Native bounded explicit-state checker | checker, bounds, deduplication, and counterexample tests |
| TRACE-001 (initial) | Versioned traces and decision certificates | deterministic serialization tests |
| SEC-005 | Alternative and ordered-plan proposal batches | ordering, sibling, denial, and per-step certificate tests |
| ARCH-002 | Restricted direct-policy/kernel conformance | table-driven semantic corpus |
| EXP-003 (semantic layer) | Executable defective monitors | six one-step SLED counterexamples |
| BASE-001, BASE-002, PAPER-001 | Baseline, archive integrity, and current manuscript | retained logs, hashes, and manuscript CI |

## Deferred research programme

| IDs | Required change before an implementation claim |
|---|---|
| FM-001..FM-006 | Parameterised effects, role-sensitive context, pointwise production ACS, scoped delegation, observer model, and complete-mediation inventory |
| PROV-001, MEM-001 | Denial-feedback provenance and origin-bound persistent memory |
| SLED-002..SLED-004 | Reductions, mutation-completeness research, and relational confidentiality |
| EVAL-001..EVAL-006 | Reproducible real-model and external-benchmark evidence |
| POL-001, POL-002 | Differentially tested production PDP and cloud-policy adapters |
| CAP-001, TRACE-002 | Short-lived executor capabilities and W3C PROV mapping |
| FW-001, MCP-001, SUPPLY-001, PLAN-001 | Framework, protocol, supply-chain, and verified-planning work |
| PAPER-002, RW-001 | Generated paper evidence and continuing related-work revision |

No deferred item is described as implemented merely because an experimental
adapter or report exists.
