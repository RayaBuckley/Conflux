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
| EXP-001..EXP-004 | Manifests, separated suites, negative controls, and current-code smoke | strict manifest tests, six scenarios, five controls, `output/runs/smoke/` |
| SLEDMC-001..SLEDMC-003 | Canonical-state checking and trace/state comparison | checker and deterministic comparison tests |
| SLEDV-001..SLEDV-003 | Serializable IR, bounded backend, and runtime conformance | verification schemas and differential tests |
| PLAN-001..PLAN-003 | Typed plans, outcome validation, authority-minimising selection | planning and optimisation tests |
| AGENTDOJO-001, AGENTDOJO-002 | Pinned upstream structures and strict result translation | lock, raw fixture, adapter tests |
| CLUSTER-001, CLUSTER-002 | Capability discovery and resumable manifest jobs | doctor and resume tests |
| PLAN-DYN-000..PLAN-DYN-011, PLAN-DYN-013..PLAN-DYN-015, PLAN-DYN-017 | Open-ended planning contracts, mediation, code envelope, SLED abstraction, and optimisation | specification, runtime, sandbox, verification, and mutation tests |

## Partial and externally gated programme

| IDs | Implemented boundary and remaining evidence |
|---|---|
| FM-001..FM-006 | Parameterised effects, role-sensitive context, pointwise production ACS, scoped delegation, observer model, and complete-mediation inventory |
| PROV-001, MEM-001 | Denial-feedback provenance and origin-bound persistent memory |
| SLED-002..SLED-004 | Reductions, mutation-completeness research, and relational confidentiality |
| EVAL-001..EVAL-006 | Reproducible real-model and external-benchmark evidence |
| POL-001, POL-002 | Differentially tested production PDP and cloud-policy adapters |
| CAP-001, TRACE-002 | Short-lived executor capabilities and W3C PROV mapping |
| FW-001, MCP-001, SUPPLY-001 | Framework, protocol, and supply-chain integration |
| MODEL-001, MODEL-002, PLAN-DYN-012 | Offline adapters are implemented; credentialed/model-weight evidence remains gated |
| AGENTDOJO-003 | Pinned manifest and translation exist; live no-defence-versus-ITES result remains gated |
| SLEDV-004 | nuXmv adapter exists; binary-backed evidence remains gated |
| PLAN-DYN-016 | Strict four-mode aggregation exists; live observations remain gated |
| PAPER-002, RW-001 | Generated external-result evidence and continuing related-work revision |

## Foundational literature integration (partial/deferred)

Source: `reports/analysis/2026-08-13-foundational-security-literature.md`.

| Item | Status | Notes |
|---|---|---|
| Classical IFC/integrity lineage integrated into documentation | Implemented | Glossary terms, ADR 012, RELATED_WORK, RESEARCH_OVERVIEW, SECURITY_MODEL, ARCHITECTURE, SLED property hierarchy, EVALUATION confidentiality hierarchy, CLAIMS novelty qualification, STATUS, PROJECT_ANALYSIS |
| Priority A bibliography entries | Partial | Added to publications/manuscript/REFERENCES.md as "unverified"; primary-source checking deferred |
| Literature matrix | Deferred | Classical integrity/IFC stream with structured comparison fields |
| Novelty audit | Deferred | Search repository for claims made unsafe by classical precedent |
| Manuscript migration | Deferred | Report §31 proposes manuscript structural changes; requires operator gate after primary-source reading |

The complete, per-task disposition and evidence paths are in
`docs/evidence/task-registry.json`. No gated item is promoted to a live claim merely
because its adapter, manifest, or report source exists.
