# Experiment 2: Security Mutation Benchmark

## Research question

Can native SLED and solver-backed SLED-V systematically detect representative implementation/semantic defects across Conflux's authority, provenance, read, visibility, planning, and delegation boundaries?

## Goal

Expand the current small mutation evidence into a principled fault-injection benchmark. Prefer simple, reviewable seeded defects with known expected failures over complicated artificial bugs.

## Required property families and candidate mutants

### A. Principal Context / action authorisation

A1. Empty Principal Context authorises an effect.
A2. Replace universal principal check with existential `any` check.
A3. Authorise only the requester/initiator.
A4. Drop one influencing principal before an effect.
A5. Cache authorisation and skip action-time re-authorisation after a policy change.
A6. Allow an authority-bearing selector if only the content principal can use it.

### B. Provenance propagation

B1. Nested execution starts a fresh Principal Context.
B2. Tool output inherits requesting user authority instead of authenticated source provenance.
B3. Derived artifact drops one source principal.
B4. Sibling branch influence leaks into or out of another branch incorrectly.
B5. Provenance is replaced with current session/requester provenance after a transform.

### C. Read and disclosure

C1. Treat provenance principals as readers.
C2. Skip read policy for one nested input path.
C3. Allow a visible action whose audience cannot read an influencing datum.
C4. Redaction accidentally copies a hidden payload field.
C5. Error message exposes a hidden value.

### D. Action arguments / selectors

D1. Ignore selector argument provenance.
D2. Authorise operation name but not resource selector.
D3. Trust model-provided argument-role metadata.
D4. Unknown authority-bearing argument fails open.

### E. Planning / certificates

E1. Execute a plan after relevant policy version changes without revalidation.
E2. Accept a stale certificate against changed action arguments.
E3. Permit a plan patch to widen required authority.
E4. Recovery path searches for stronger credentials after permission denial.

### F. Delegation model

Reuse the existing seven delegation mutants where possible. Ensure coverage includes wrong issuer, wrong beneficiary, wrong operation/resource/argument binding, expiry, revocation, and reuse/consumption semantics.

## Minimum target

At least 20 unique mutants across at least four families. Ideal target: 28-35 including existing delegation mutants.

Do not create duplicates whose only difference is a renamed field.

## Harness requirements

Each mutant must declare:

- stable mutant ID;
- property family;
- one-sentence defect description;
- exact semantic rule violated;
- expected safe/unsafe verdict;
- expected witness characteristic where known;
- model/fixture scope;
- whether it is existing or newly added.

The canonical implementation must not be edited in-place for experiment runs. Mutants should be isolated fixture/controller variants or explicit mutation hooks that cannot accidentally ship in the normal runtime.

## Backends

For every supported mutant run:

- native/reference finite checker;
- original IR reference interpreter if applicable;
- Z3 BMC;
- COI-reduced Z3 BMC when applicable.

## Metrics

- detected yes/no;
- verdict;
- shortest witness length;
- runtime;
- states/transitions explored by explicit checker;
- COI variable/rule reduction;
- witness lift/replay success;
- backend disagreement flag.

## Acceptance gates

1. 100% of deliberately unsafe retained mutants are detected by every backend that claims to support that fixture/property.
2. Canonical non-mutated controls remain safe.
3. Mutant tests verify that the seeded defect is actually active.
4. Minimal witness generation works for native SLED; solver witnesses are replayed against the reference semantics where supported.
5. Mutants remain clearly labelled synthetic defects, not real historical bugs unless they truly are.

## Paper output

Primary table grouped by family with:

- number of mutants;
- native detected;
- Z3 detected;
- reduced Z3 detected;
- median witness length;
- median checking time.

Supplementary appendix should list each mutant ID and defect.

## Claim boundary

Allowed: the verifier detects all seeded defects in the declared finite mutation suite.

Not allowed: mutation completeness implies absence of all implementation bugs.
