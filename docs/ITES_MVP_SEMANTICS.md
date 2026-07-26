# ITES MVP Operational Semantics

Status: normative for the MVP  
Semantics version: `ites-mvp-1`

This document specifies the smallest ITES security boundary implemented by
`conflux.research.mvp`. It covers provenance, Principal Context accumulation,
nested execution, primitive authorisation, bounded exploration, immutable
traces, and isolated branches. Consent, visibility, delegation, providers,
legacy proposal coercion, and richer action kinds are extensions, not part of
this semantics.

## Domains

- `p ∈ Principal` is an entity with a permission set `Perm(p)`.
- `r ∈ Resource` is a protected target.
- `a ∈ Artifact` is an immutable value paired with provenance.
- `Prov(a) ⊆ Principal` is the set of Principals contributing to `a`.
- `C ⊆ Principal` is the current Principal Context.
- `Prim(perm, r, op)` is a primitive action.
- `Nest(I)` is a nested execution proposal over input artifacts `I`.
- `E` is an opaque immutable environment in the MVP.

The MVP authorisation predicate is:

```text
Authorised(C, perm) iff ∀ p ∈ C : perm ∈ Perm(p)
```

The empty Principal Context is not granted implicit authority by the MVP. A
deployment must provide an explicit policy for empty-context actions before
using them.

## State

Each branch has an immutable state:

```text
S = (E, I, C, b, d, t, status)
```

where:

- `E` is the environment;
- `I` is the current input artifact set;
- `C = ⋃ Prov(a)` for `a ∈ I`;
- `b` is the branch identifier;
- `d` is nesting depth;
- `t` is the append-only trace;
- `status` is active, terminal, blocked, or incomplete.

The aggregate evaluator additionally maintains one run-level call count `q`.
The call budget is `q ≤ Q`, where `Q` is fixed at the start of a run and is
shared across all branches.

## Initialisation

For initial inputs `I₀` and environment `E`:

```text
S₀ = (E, I₀, ⋃ Prov(a), root, 0, [], active)
```

No model-generated value may enter the state without an explicit artifact and
provenance. The MVP does not infer provenance from text content.

## Model proposals

At an active state, the model receives exactly `I` and returns a finite ordered
set of typed proposals. Proposals are sorted by a stable key before
exploration. A proposal is not an executed action; it becomes declared only
after the relevant rule succeeds.

## Primitive transition

For `Prim(perm, r, op)`:

```text
if Authorised(C, perm):
    S ──declare──▶ S' with terminal status and an allowed trace event
else:
    S ──block──▶ S' with blocked status and a denied trace event
```

The transition does not remove Principals from `C`, add authority, or mutate
the parent state.

## Nested transition

For `Nest(I')`, readability requires:

```text
Readable(C, I') iff ∀ p ∈ C, ∀ a ∈ I' : p ∈ Prov(a)
```

If readability fails, the proposal is blocked and produces a blocked terminal
child. If it succeeds:

```text
C' = C ∪ ⋃ Prov(a) for a ∈ I'
S' = (E, I', C', child-id, d + 1, t + nested-event, active)
```

The evaluator recursively explores `S'`. Influence is accumulated, never
removed.

## Branching and non-interference

Given proposals `x₁, …, xₙ` returned for state `S`, each proposal is evaluated
from the same parent `S`:

```text
Explore(S, [x₁, …, xₙ]) = {ExploreChild(S, xᵢ) | 1 ≤ i ≤ n}
```

No child state is used as the parent of a sibling. Therefore a sibling cannot
observe another sibling's inputs, Principal Context, trace, declarations, or
status. The global call count is the sole shared run-level resource. Allocation
is deterministic depth-first in proposal-key order; once `Q` calls have been
consumed, remaining reachable work is marked incomplete.

## Guarantees

Under the trusted assumptions below, the MVP establishes:

1. **Provenance preservation:** every accepted nested input retains its input
   provenance and contributes it to the child Principal Context.
2. **Authority monotonicity:** `C ⊆ C'` implies the set of authorised
   permissions under `C'` is a subset of that under `C`.
3. **No privilege escalation:** every declared primitive action is authorised
   for every Principal in its current Principal Context.
4. **Branch non-interference:** sibling branches have no shared mutable state.
5. **Bounded execution:** the evaluator performs at most `Q` model calls.

## Trusted assumptions and limitations

- supplied provenance is correct;
- the access-control permission predicate is correct;
- the mediator cannot be bypassed;
- the environment and resources are not mutated by this MVP;
- provider execution is outside the MVP;
- arbitrary model proposals are allowed, so security does not depend on model
  refusal behaviour;
- real model utility and natural-language attack success are not security
  proofs.

## Paper synchronisation

This MVP directly exercises the paper's influence accumulation, intersection
authorisation, authority monotonicity, and no-privilege-escalation claims. The
paper's richer SLED environment transitions, provider actions, delegation,
utility model, and exhaustive state-space claims require later implementation
and evidence. Until then, those claims must be labelled as abstract or future
work rather than inferred from this MVP.
