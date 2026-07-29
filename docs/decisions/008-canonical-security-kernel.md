# ADR 008: One canonical security kernel

Status: accepted

## Decision

`conflux.domain` owns immutable security values, `conflux.policy` owns policy
implementations, `conflux.application` composes use cases, and `conflux.ites`
owns the sole transition kernel. `core`, `auth`, `research`, and
`compatibility` are removed without shims before the `0.1.0` API stabilises.

Principals are identity-only. An injected per-Principal policy oracle supplies
authority. Information provenance and read entitlement are separate contracts.

## Consequences

The migration is intentionally breaking. Internal callers and tests move in one
change, preventing a transitional facade from becoming a second semantic
source of truth.
