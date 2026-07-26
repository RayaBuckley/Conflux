# ADR-002: Principal Context terminology and invariants

- Status: accepted
- Date: 2026-07-25

## Decision

Use **Principal** for an entity contributing information or authority and
**Principal Context** for the principals relevant to an action decision. The
Principal Context is evaluated at action time; provenance is never discarded;
consent cannot create authority; visibility is separate from authorisation.

## Consequences

Code, documentation, tests, and paper notes must use these terms consistently.
Security changes require explicit invariant tests.
