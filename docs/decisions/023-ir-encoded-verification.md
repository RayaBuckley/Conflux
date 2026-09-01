# 023 — IR-Encoded Verification for Delegation and Planning

## Status

Accepted — 2026-09-01

## Context

SLED-V previously verified delegation safety only through native SLED
(`conflux.evaluation.delegation_verification`), which uses abstract boolean
flags set directly by mutation type. This tests that properties *would*
detect violations, but not that the actual `consume()` logic is correct.
Similarly, the plan IR (`plan_ir.py`) had a vacuous `context_narrowed`
invariant, ignored `DelegationNode`, and lacked monotonic confinement,
revocation propagation, and bounded liveness properties.

## Decision

Encode delegation and planning safety properties as `VerificationIR`
invariants and transition rules, making them available to all backends
(Z3, nuXmv, reference interpreter) and serialisable for reproducibility.

The new IR encodings **coexist** with native SLED — native SLED tests the
actual implementation, while IR encoding tests the abstract property. Both
are evidence.

## Consequences

- Delegation safety is now IR-encoded with 11 properties (8 original + 3
  new: cascade containment, authority narrowing, TOCTOU drift detection)
- Plan IR gains 4 new invariants: delegation-authority-requires-grant,
  monotonic-confinement, revocation-propagation, bounded-liveness
- Self-composition gains symmetry reduction and read-policy projection
- Refinement conformance gains assume/guarantee contracts, compositional
  verification, and CEGAR loop
- New IR expression kinds: IMPLIES, GREATER_EQUAL, GREATER_THAN, LESS_THAN,
  DIFFERENCE — additive, backward compatible

## Security impact

Strengthens SLED-V guarantees. No authority broadening, provenance loss,
or trust assumptions introduced. All new properties are additive — they
verify more, never weaken existing guarantees. Bounded results are
classified as `bounded_evidence`, never silently promoted to proof.

## References

- SentinelAgent (arXiv:2604.02767) — cascade containment, authority narrowing
- Progent (arXiv:2504.11703) — monotonic confinement
- OpenPort (arXiv:2602.20196) — TOCTOU State Witness
- SecIC3 (arXiv:2601.21353) — symmetry reduction
- FORGE (arXiv:2602.16708) — assume/guarantee contracts
- BMC-Agent (arXiv:2605.21434) — compositional verification, CEGAR
- Formalizing Agent Safety (arXiv:2510.14133) — bounded liveness
