# ADR-006: Canonical ITES Contract

## Decision

`conflux.ites` owns the domain-facing ITES contract. `MediatingITES` is the
reference implementation used by the existing execution path. `ites.mvp` is a
small executable semantics and exploration harness used to validate the
research model; it must translate to the canonical model rather than create a
parallel security contract.

## Consequences

New callers target `ITES`, `ITESReport`, `Guarantee`, and the core action,
artifact, provenance, and session types. Compatibility behavior must be
explicitly named and tested. SLED and benchmark adapters remain consumers of
ITES, never sources of its policy semantics.
