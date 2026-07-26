# ADR-003: Benchmark-independent core design

- Status: accepted
- Date: 2026-07-25

## Decision

Core, execution, authorisation, and ITES modules must not depend on a specific
benchmark. SLED and external benchmark integrations adapt scenarios and traces
to canonical Conflux models.

## Consequences

Benchmark-specific shortcuts are prohibited in the security boundary. New
benchmarks require adapters and compatibility tests.
