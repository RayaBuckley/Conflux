# ADR-004: Immutable provenance and execution state

- Status: accepted
- Date: 2026-07-25

## Decision

Security-relevant domain values, artifacts, provenance, and execution state are
immutable from callers' perspective. Operations return new values and preserve
causal provenance.

## Consequences

Pure transformations and value-based tests are preferred. Any mutable adapter
state must remain outside the security model and be explicitly documented.
