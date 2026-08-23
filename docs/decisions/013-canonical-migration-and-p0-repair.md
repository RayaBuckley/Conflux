# Specification 013: Canonical Migration and P0 Repair

Type: specification
Status: accepted for implementation

## Problem

Conflux currently has two security semantics and two domain models. Transitional
packages still own behaviour, provenance contributors are used as a read ACL,
empty Principal Contexts can acquire authority through vacuous truth, consent
defaults are derived from permissions, and reports confuse rejected proposals
with executed violations.

## Security contract

- `conflux.domain` is the only owner of security-domain values.
- A `Principal` is an identity. Authority comes from an injected policy oracle.
- Empty or unknown Principal Contexts cannot authorise observable or effectful
  behaviour.
- Provenance records influence; a read policy records observation rights.
- Model output cannot narrow its conservative Principal Context.
- Multiple proposals are alternative successors of the same immutable parent.
- Consent, visibility, and authorisation are independent fail-closed decisions.
- Only an action bound to its decision certificate may be executed.
- SLED reports bounded evidence precisely and retains minimal counterexamples.

## In scope

Complete the package migration; replace both ITES implementations with one pure
transition kernel; add versioned traces and decision certificates; implement a
native bounded explicit-state checker; migrate adapters; remove legacy imports;
replace the tests; update documentation, audit tooling, validation, and CI.

## Non-goals

Parameterized argument effects, formal delegation capabilities, persistent
memory authority, symbolic model-checking backends, controller synthesis,
production credentials, real external benchmark experiments, and edits to the
archived paper are post-migration work.

## Failure modes

Missing provenance, empty context, missing consent, policy exceptions, unknown
actions, unsupported adapter features, stale decision certificates, provider
errors, and verification bounds all produce explicit non-allowing outcomes.

## Acceptance evidence

The portable validation workflow must pass repository audit, unit/property and
integration tests, branch coverage, Ruff, strict mypy, package build/import,
native SLED smoke verification, and deterministic trace checks. The import
graph must contain no `conflux.core`, `conflux.auth`, `conflux.research`, or
`conflux.compatibility` references.
