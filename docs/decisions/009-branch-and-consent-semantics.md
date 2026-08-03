# ADR 009: Alternative branches and explicit consent

Status: accepted

## Decision

A model output containing multiple proposals denotes independent alternative
successors evaluated from the same immutable parent. Canonical ordering is
deterministic. Ordered workflows require a future explicit plan type.

All observable, nested, effectful, and delegation proposals require an explicit
consent decision. Missing consent denies. Internal stop and no-op transitions
are the only exceptions. A scoped attenuating capability model now exists,
but runtime delegation remains unsupported and denied until its independent
policy-parity and activation evidence gates pass.
