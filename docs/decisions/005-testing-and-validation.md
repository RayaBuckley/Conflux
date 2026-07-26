# ADR-005: Testing and validation policy

- Status: accepted
- Date: 2026-07-25

## Decision

Validation consists of pytest tests, coverage reporting, Ruff, and strict
mypy. Tests prioritise observable security invariants and include unit,
integration, adapter, benchmark smoke, and reproducibility coverage. Coverage
is initially reported and baselined rather than enforced at an arbitrary
threshold.

## Consequences

Every security change needs regression tests and documentation. Generated
coverage and experiment outputs are local or explicitly managed artefacts.
