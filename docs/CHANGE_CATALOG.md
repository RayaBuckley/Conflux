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
| PAPER-001, PAPER-002, RW-001 | Post-paper claim and related-work revision |

No deferred item is described as implemented merely because an experimental
adapter or report exists.
