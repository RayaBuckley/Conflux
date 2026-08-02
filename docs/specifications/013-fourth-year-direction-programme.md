# Specification 013: Fourth-Year Direction Programme

Status: accepted, staged implementation  
Source snapshot: `reports/archive/2026-08-02-fourth-year-direction/`

## Goal and success criteria

Advance Conflux through small, evidence-gated research increments without
weakening the canonical ITES boundary. The programme is complete only when
each delivered increment has executable tests, explicit claim limits, a
canonical task disposition, and independently regenerable evidence where an
empirical claim is made.

The first research increment is property-preserving cone-of-influence (COI)
reduction for the serialisable verification IR. Later increments add a
dual-backend local-model smoke protocol, role-aware action arguments,
audience-aware disclosure and attribution, an optional pinned Cedar adapter,
and a disabled-by-default attenuating delegation model.

## Current architecture and affected boundaries

The existing ownership remains authoritative:

- `conflux.verification` owns serialisable models, reductions, reference
  interpretation, and optional solver adapters;
- `conflux.planning` owns inert plans and `ModeledProgram` values;
- `conflux.domain` owns immutable action and provenance values;
- `conflux.application` composes independent policy decisions;
- `conflux.ites` remains the only operational mediation boundary;
- adapters may translate local tools and policies but may not approximate an
  unsupported decision.

No stage permits model output, consent, visibility, a benchmark, or a
delegation grant to manufacture authority or narrow Principal Context.

## Public interfaces and data flow

### Verification reduction

```python
reduce_cone_of_influence(
    ir: VerificationIR,
    invariant_ids: tuple[str, ...],
) -> VerificationReduction
```

The reducer starts from variables read by selected invariants, closes over
guards and right-hand sides of rules that can update relevant variables,
projects assignments, and removes rules with only irrelevant effects. It
preserves rule IDs, bounds, initial values, assumptions, and selected
invariants. Unsupported expressions return the unchanged model with an
explicit inapplicability reason. Original and reduced results are compared;
verdict disagreement or an unliftable witness invalidates the reduced claim.

The CLI accepts `conflux verify --reduce cone_of_influence`. A retained
`sled-coi-reduction-v1` bundle must compare identical fixtures and demonstrate
a measurable reduction on at least one.

### Local planning smoke

One fixed prompt template and seed exercise `direct-authorised` and
`blocked-recovery` in all four planning modes. Direct Transformers and a
loopback llama.cpp server are separate model identities even when derived
from the same pinned SmolLM2 revision. Configuration records revisions,
tokenizer, conversion and binary identities, weight or GGUF digests, runtime
arguments, and failures. Acquisition, conversion, and live invocation require
operator action; CI uses fakes and downloads nothing.

### Argument decisions, disclosure, and attribution

Trusted operation schemas assign immutable argument roles. Model output binds
values but cannot assign roles. Every authority-bearing argument is checked
pointwise for every Principal through an `ArgumentAuthorisationPort`; a
missing or unknown role denies. Argument denial remains authorisation and
cannot be overridden by consent or visibility.

Trace disclosure is decided per audience and event class at levels `none`,
`existence`, `redacted`, and `full`. Deterministic projection prevents fields
above the decision level from reaching a recipient. Structured attribution
records verified input, conservative influence, Principal Context, relevant
decision evidence, uncertainty, and redaction requirements. Model-generated
explanations remain explicitly untrusted.

### Cedar and delegation

Cedar is an optional, no-shell, timeout-bounded local CLI adapter pinned to
v4.11.0 (`d86ed2ee47cbe5a30e6b70a3d8414bc66ce88ae3`). Its hashed bundle owns the
schema, policies, entities, supported subset, and binary identity. Requests
are pointwise across Principal Context; any mixed, malformed, missing,
unsupported, timed-out, or version-mismatched response denies.

Delegation is initially a serialisable model and disabled runtime capability.
A grant is issuer- and beneficiary-bound, operation-version- and resource-
exact, role-constrained, expiring, revocable, non-redelegable, and one use.
It attenuates existing authority and supplies neither consent nor read access.
Runtime consumption remains denied until mutant, Cedar parity, visibility,
attribution, and certificate-binding gates all pass.

## Rationale and rejected alternatives

COI reduction comes first because it can reduce verification cost while
retaining a reviewable semantic relationship to the current IR. Native
partial-order and symmetry reductions are deferred: both need additional
independence or equivalence arguments and would broaden the proof obligation.

The laptop run is an integration smoke, not an efficacy comparison. Keeping
the two runtimes distinct avoids claiming equivalent tokenization, numerical
behavior, or generated output. Live execution is operator-gated to avoid
silent downloads, licensing assumptions, and fabricated availability.

Argument roles belong to trusted schemas because letting generated text label
a recipient as harmless content would make the model its own policy oracle.
Audience projection follows the decision, rather than logging then redacting,
so forbidden detail never enters a recipient-facing record.

Cedar is optional because repository security semantics must be testable
offline. Its supported subset denies rather than approximates. Delegation is
modeled before activation because it adds authority lifecycle, ordering,
atomic-use, and revocation obligations that cannot safely be inferred from a
free-form scope.

## Security impact

All existing invariants remain mandatory. Principal Context is unchanged by
reduction, planning, arguments, disclosure, attribution, Cedar, and
delegation. Provenance is retained on argument values and grant issuance.
Authorisation, read access, visibility, and consent remain independent.
Unsupported constructs and uncertain external states fail closed. No stage
executes generated source code; `ModeledProgram` remains inert data.

## Implementation sequence and gates

1. Archive and reconcile the direction package.
2. Implement COI reduction, equivalence comparison, CLI support, and retained
   deterministic evidence.
3. Implement the 16-cell local-model smoke protocol and stop after any live
   bundle for human review.
4. Version action, certificate, and trace schemas for arguments, disclosure,
   and attribution; add SLED properties and defective variants.
5. Add the pinned Cedar adapter and retained offline differential corpus.
6. Add delegation values, parsing, snapshots, revocation, traces, and SLED
   model behind a disabled capability. Activate only in a separate commit if
   every stated gate passes.
7. Reconcile current documentation and manuscript claims solely from retained
   normalized results.

## Expected file set and change budget

Expected changes are confined to existing owners under `src/conflux/`,
`tests/`, `schemas/`, `experiments/`, `runs/`, `docs/`, `reports/analysis/`,
`reports/archive/`, `manuscript/`, and existing validation scripts. New
verification, policy-adapter, and test modules are allowed inside those
owners. The retained COI bundle lives at `runs/sled-coi-reduction-v1/`.

No new top-level directory or competing status, roadmap, rationale, claim,
architecture, or report-analysis document is approved by this specification.
Such a change requires explicit maintainer approval and an amended expected
file set.

## Tests and acceptance criteria

- Archive: byte hashes, Git objects, paths, lineage, and crosswalk coverage.
- COI: dependency closure, guards, simultaneous assignments, stuttering,
  irrelevant cycles, multiple invariants, deterministic serialisation,
  unchanged fallback, verdict equivalence, and witness lifting.
- Local models: fake backends, exact identities, local-cache and loopback
  enforcement, complete matrices, retained failures, and checksums.
- Arguments: every role, provenance and value fingerprints, mixed contexts,
  and proof that content or consent cannot authorise selectors.
- Disclosure and attribution: each event class and level, deterministic
  projections, hidden decision details, uncertainty, and safe redaction.
- Cedar: pinning, translation, hashes, explicit forbid, error paths, timeout,
  differential parity, and optional-binary isolation.
- Delegation: attenuation, ordering, exact bindings, expiry, revocation,
  atomic one-use behavior, idempotency, non-redelegation, unchanged context,
  and minimal mutant witnesses.

Repository acceptance remains the portable validator, audit, schemas,
deterministic regeneration, Ruff, strict mypy, branch coverage at least 90%,
wheel and CLI smoke, manuscript compilation, and `git diff --check`.

## Documentation and paper synchronisation

`docs/task-registry.json` owns disposition; `docs/CLAIMS.md` owns claim
strength; this specification owns the accepted design. Report prose stays
historical. Manuscript numbers may be added only from a matching checksummed
bundle and must state abstraction, bounds, runtime identity, and exclusions.

## Assumptions and resolved decisions

- Python APIs and schemas may break before 1.0; retained historical readers
  remain explicit rather than becoming general compatibility shims.
- Hosted models, automatic model downloads, real generated-code execution,
  unsupported Cedar approximation, multi-use grants, and redelegation are out
  of scope.
- Absent llama.cpp, Cedar, solver, model weights, or GPU access is an
  unavailable outcome, not evidence of success or failure.
- Native partial-order reduction, Principal symmetry, stronger
  noninterference, larger live benchmarks, and delegation activation remain
  later gated work.
