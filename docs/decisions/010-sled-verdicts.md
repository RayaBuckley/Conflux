# ADR 010: Native SLED verdict semantics

Status: accepted

## Decision

The native checker performs breadth-first explicit-state exploration with
canonical state keys, visited-state memoisation, predecessor-based minimal
counterexamples, and explicit bounds.

- `SAFE`: the finite reachable state space was exhausted.
- `BOUNDED_SAFE`: no violation was found, but a configured bound truncated work.
- `UNSAFE`: a property violation has a counterexample.
- `UNKNOWN`: model, property, or adapter evaluation failed.

No bounded result is described as an unqualified proof.
