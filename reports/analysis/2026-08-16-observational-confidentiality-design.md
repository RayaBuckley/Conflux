# Observational Confidentiality Design for SLED Property 5

**Date:** 16 August 2026
**Status:** Research design; not a canonical specification
**Source:** Plan step 9 — design relational verification approach for SLED property 5
**Advances:** SLEDV-005 from `conceptual` to `designed`
**Dependencies:** Novelty audit (step 1) and literature matrix (step 2) complete

## 1. Property definition

SLED property 5, observational confidentiality, is stated in `docs/reference/SLED.md`:

> Executions differing only in secret information produce equivalent
> observations for unauthorised principals, modulo declared declassification.
> This is a relational property requiring comparison of execution pairs,
> unlike the safety properties above which are checked on individual traces.
> Authorised reads do not establish noninterference.

Formally, let $\sigma_1, \sigma_2$ be two ITES execution traces from the
same initial state but with different secret inputs. Let $O_P(\sigma)$
denote the observation available to principal $P$ from trace $\sigma$.
Then:

$$
\forall P \notin \mathrm{AuthorisedReaders}(\text{secret}):
  O_P(\sigma_1) = O_P(\sigma_2)
$$

where equality is up to declared declassification boundaries.

This is a **relational hyperproperty** (a 2-safety property in the sense of
Terauchi and Aiken 2005): it relates two execution traces, not a single
trace. It is distinct from the trace-level safety properties (1–4) currently
supported by native SLED.

## 2. Distinctness from classical IFC

The novelty audit (step 1) and literature matrix (step 2) confirm that
observational confidentiality as a verification target is well-established in
the IFC literature (Sabelfeld & Myers 2003, Zdancewic & Myers 2001, Askarov
& Myers 2007, Cecchetti et al. 2017). What is potentially novel in Conflux's
formulation is:

1. **Principal-context-dependent read policies**: the read decision is not a
   static label comparison but a per-principal, per-action policy evaluation
   against the current Principal Context. Two traces may produce different
   read decisions for the same principal depending on provenance accumulation.

2. **Four independent policy dimensions**: authorisation, read, visibility,
   and consent are evaluated independently. Observational confidentiality
   requires reasoning about the *interaction* of these dimensions, not a
   single label check.

3. **Provenance-mediated authority**: the set of principals in the context
   grows monotonically (property 3), which means an unauthorised observer's
   read policy may change during execution. The relational property must
   account for this.

No prior IFC system verified a relational confidentiality property over
execution pairs where the observation function depends on a monotonic
principal context derived from authenticated provenance. Classical
noninterference assumes a static lattice; Dec-IFC assumes a fixed declassification
policy. Conflux's formulation is more expressive but harder to verify.

## 3. Execution-pair relation

### 3.1 Pair construction

Given an ITES transition system $(S, A, \to)$ with initial state $s_0$ and
a secret partition of inputs $I = I_{\text{pub}} \cup I_{\text{sec}}$:

1. Construct two initial states:
   - $s_0^1 = \text{initial}(I_{\text{pub}} \cup I_{\text{sec}}^{(1)})$
   - $s_0^2 = \text{initial}(I_{\text{pub}} \cup I_{\text{sec}}^{(2)})$
   where $I_{\text{sec}}^{(1)}$ and $I_{\text{sec}}^{(2)}$ differ in secret
   content but share the same provenance structure.

2. Explore both systems independently using the existing BFS model checker.

3. At each step, compare the observations available to each principal $P$
   who is not authorised to read the secret.

### 3.2 Observation function

The observation available to principal $P$ from state $s$ is:

$$
O_P(s) = \{ (a, d.\text{read}, d.\text{visibility}) \mid
  a \in \text{authorised\_actions}(s),\;
  d = \text{decision}(a, P, s) \}
$$

where $\text{decision}(a, P, s)$ is the four-dimensional policy decision
for action $a$ evaluated in principal $P$'s context at state $s$.

Concretely, from the ITES kernel (`src/conflux/ites/kernel.py`), each
transition produces a `TraceEvent` containing the `ActionDecision`, which
has independent `read`, `visibility`, `consent`, and `authorisation`
decisions. The observation for principal $P$ is the set of trace events
where $P$ is in the audience and the visibility level is not `NONE`.

### 3.3 Equivalence criterion

Two traces $\sigma_1, \sigma_2$ are observationally equivalent for principal
$P$ if, at every corresponding step $i$:

1. The set of authorised actions visible to $P$ is the same:
   $\{ a \mid (a, d) \in O_P(s_1^i) \} = \{ a \mid (a, d) \in O_P(s_2^i) \}$

2. The read and visibility decisions for those actions agree:
   $\forall (a, d_1) \in O_P(s_1^i), (a, d_2) \in O_P(s_2^i):
     d_1.\text{read} = d_2.\text{read} \wedge
     d_1.\text{visibility} = d_2.\text{visibility}$

3. Exceptions are allowed where both traces have a declared declassification
   for the same action at the same step.

## 4. Mapping to the existing verification infrastructure

### 4.1 Native SLED (BFS model checker)

The `ExplicitStateChecker` in `src/conflux/evaluation/model_checking.py`
explores reachable states breadth-first and checks `SafetyProperty` instances
on individual transitions. It cannot directly verify relational properties
because:

- It visits one state at a time and has no mechanism for comparing pairs.
- `SafetyProperty.violation` takes a single `Transition`, not a pair.
- State deduplication is single-trace; the product state space would require
  paired deduplication.

**Assessment: Native SLED cannot verify observational confidentiality
without modification.** The required change is the introduction of a paired
state space and a relational property interface.

### 4.2 Verification IR

The serializable IR in `src/conflux/verification/ir.py` represents the
transition system as variables, rules, and invariants. Each invariant is a
state predicate (boolean expression over variables). The IR does not natively
support hyperproperties because:

- Invariants are single-state predicates.
- The IR has no construct for relating two copies of the state space.
- Z3 and nuXmv backends translate single-state invariants.

**Assessment: The IR can express observational confidentiality via a
self-composition encoding.** The standard technique (Barthe, D'Argenio, and
Rezk 2004) creates a product program/transition system with two copies of
each variable ($v$ and $v'$), runs both traces in the product system, and
checks that the observations agree. This requires:

1. Doubling all variables: for each variable $v$, create $v$ and $v'$.
2. Doubling all rules: for each rule $r$, create $r$ (operates on unprimed
   variables) and $r'$ (operates on primed variables), sharing control flow.
3. Adding an invariant: for each unauthorised principal $P$ and each
   observable variable $v$, check that $v = v'$ whenever $P$ is not an
   authorised reader.

The COI reducer (`src/conflux/verification/reduction.py`) would then project
this product IR to only the variables relevant to the confidentiality
property, which is its existing behaviour.

### 4.3 Self-composition feasibility

**State-space blowup**: the product system has at most $|S|^2$ states
where $|S|$ is the original state space. For the existing SLED fixtures
(2–4 states each), this is trivially tractable. For larger benchmarks, the
COI reducer mitigates blowup by projecting away variables irrelevant to the
confidentiality invariant.

**Secret partition**: the encoding requires the operator to specify which
inputs are secret. This is an annotation on the initial state, not a change
to the kernel.

**Declassification**: the invariant must be conditional on declassification
boundaries. The existing `ActionDecision` structure already records the
policy evidence for each decision, so the invariant can reference these.

**Principal-dependent observations**: the invariant must be parameterised
by the observer principal. This is a natural fit for the existing IR, where
invariants can reference principal-identity variables.

## 5. Verification strategy

### 5.1 Recommended approach: IR self-composition

1. **Define the secret partition** on the initial state. This is an
   annotation that identifies which `Artifact` inputs are secret and which
   are public. Two product initial states are created: one with the original
   secret and one with a symbolic alternative.

2. **Construct the product IR** by doubling variables and rules. The
   `VerificationIR` dataclass in `src/conflux/verification/ir.py` has
   `variables`, `initial_values`, `rules`, and `invariants`. Each of these
   is doubled.

3. **Add confidentiality invariants** of the form:
   ```
   FORALL P in Principals WHERE NOT authorised_reader(P, secret):
     observations(P, unprimed_state) = observations(P, primed_state)
   ```
   These invariants are boolean expressions over both primed and unprimed
   variables in the product IR.

4. **Apply COI reduction** to the product IR, projecting away variables
   that do not appear in any confidentiality invariant or their transitive
   guard/assignment dependencies.

5. **Verify** using the existing Z3 BMC backend, which already handles
   `VerificationIR` invariants. The product IR is a valid `VerificationIR`
   instance; no backend changes are required.

6. **Interpret the result**:
   - `SAFE`: observational confidentiality holds for the bounded state space.
   - `BOUNDED_SAFE`: no counterexample found within bounds.
   - `UNSAFE`: a counterexample trace shows where observations diverge.
   - `UNKNOWN`: the encoding or backend failed.

### 5.2 Alternative: product-state native SLED

An alternative is to modify the native BFS model checker to explore a product
state space. This would require:

1. A new `PairedBranchState` that holds two `BranchState` instances.
2. A paired `TransitionSystem` implementation.
3. A `RelationalSafetyProperty` protocol that takes paired transitions.

This approach is more direct but requires new protocol types and a modified
checker. It would produce native SLED results rather than IR results, which
has the advantage of staying within the operational semantics but the
disadvantage of requiring more infrastructure changes.

**Recommendation**: implement the IR self-composition approach first, because
it reuses existing infrastructure (IR construction, COI reduction, Z3 backend)
and produces results in the existing verification evidence format. The
native product-state approach is a future optimisation for larger state
spaces where the IR abstraction is too coarse.

## 6. Relation to SLED properties 1–4

| Property | Kind | Verified by | Relation to property 5 |
|---|---|---|---|
| 1. Authority safety | Trace safety | Native SLED + IR | Prerequisite: authority must be correct before observations can be compared |
| 2. Provenance monotonicity | Trace safety | Native SLED + IR | Prerequisite: monotonic context ensures observations cannot gain secret access retroactively |
| 3. Delegation safety | Trace safety (model only) | IR only | Independent; delegation activation is unconditionally denied in current runtime |
| 4. Read safety | Trace safety | Native SLED + IR | Prerequisite: read safety ensures no single trace violates read policy; property 5 strengthens this to relational confidentiality |
| 5. Observational confidentiality | Relational (2-safety) | IR self-composition (designed) | **New**: requires comparing execution pairs |
| 6. Robust disclosure | Relational | Future work | Builds on property 5 by adding attacker-control conditions |
| 7. Liveness/utility | Trace liveness | Future work | Independent; requires a different verification approach (fairness, temporal logic) |

Properties 1–4 are trace-level safety properties: each can be checked on a
single transition. Property 5 is the first relational property and requires
a fundamentally different verification approach. Properties 1 and 4 are
prerequisites: if authority or read safety is violated, observational
confidentiality is trivially violated. Property 2 (monotonicity) is a
prerequisite because it ensures that the principal context only grows, which
means an observer's access can only increase, not decrease, making the
relational comparison well-founded.

## 7. Expected evidence strength

| Approach | Evidence level | Conditions |
|---|---|---|
| IR self-composition + Z3 BMC | `bounded_evidence` | Z3 proves no counterexample within bounds on the product IR |
| IR self-composition + nuXmv | `bounded_evidence` (stronger) | nuXmv can verify CTL properties over the product system |
| Native product-state SLED | `bounded_evidence` | BFS exhausts the product state space or finds a counterexample |
| Full noninterference proof | Theorem | Requires a mechanised proof assistant (Coq, Isabelle); not currently available |

The IR self-composition approach with Z3 BMC will produce `bounded_evidence`,
which is the same evidence level as the existing SLED properties 1–4. This is
appropriate for a research prototype. A full noninterference proof would
require significant additional infrastructure (proof assistant integration,
a verified semantics mapping) and is out of scope.

## 8. Implementation sketch

### 8.1 New types needed

```python
@dataclass(frozen=True, slots=True)
class SecretPartition:
    public_input_ids: frozenset[str]
    secret_input_ids: frozenset[str]
    observer_principal_ids: frozenset[str]
    declassification_boundaries: tuple[str, ...]
```

### 8.2 Product IR construction

A function `construct_product_ir(ir: VerificationIR, partition: SecretPartition) -> VerificationIR`:

1. Double all variables: for each `v`, add `v'` with the same sort.
2. Double initial values: set `v'` initial to the same value (or symbolic
   alternative for secret variables).
3. Double all rules: for each rule `r`, create `r` (unprimed) and `r'`
   (primed), with the same guard and assignment structure applied to the
   respective variable sets.
4. Add confidentiality invariants: for each observable variable `v` that an
   unauthorised observer can see, add the invariant `v = v'`.

### 8.3 Integration point

The product IR is constructed in `src/conflux/verification/` as a new module
(e.g., `self_composition.py`). It takes an existing `VerificationIR` and a
`SecretPartition`, and produces a new `VerificationIR` that can be verified
by the existing Z3 backend without modification.

### 8.4 CLI surface

```
conflux verify confidentiality --ir <ir.json> --partition <partition.json> --output <result.json>
```

This would:
1. Load the IR and partition.
2. Construct the product IR.
3. Apply COI reduction.
4. Verify with Z3 BMC.
5. Interpret the result as a confidentiality verdict.

## 9. Tractability assessment

For the existing SLED fixtures (2–4 states, 1–3 transitions each), the
product state space is at most 16 states and 9 transitions. This is well
within the capacity of both the native checker and Z3.

For larger benchmarks (e.g., the AgentDojo or planning scenarios), the
state space is determined by the number of distinct `BranchState` values,
which grows with model calls and action alternatives. The product state
space is quadratic in the original, but COI reduction can significantly
shrink it by projecting away variables irrelevant to the confidentiality
invariant.

**Simplifying abstractions** that may help for larger cases:

1. **Principal symmetry**: if two principals have the same policy, their
   observations are equivalent. The product space only needs to distinguish
   principals with different policies.

2. **Control-flow alignment**: if two traces follow the same control flow
   (same authorised/blocked decisions at each step), the observation
   comparison is trivial. The product space only needs to explore control
   flow divergence.

3. **Read-policy projection**: only variables that appear in read decisions
   for the observer principal need to be tracked in the product. All other
   variables can be projected away by COI reduction.

**Assessment: tractable for existing fixtures and small benchmarks. Larger
benchmarks may require the principal-symmetry and control-flow abstractions.**

## 10. Open questions

1. **Declassification encoding**: should declassification boundaries be
   expressed as exceptions in the confidentiality invariant (the standard
   approach) or as conditional equivalences? The former is simpler; the
   latter is more expressive but requires the IR to support conditional
   invariants.

2. **Secret-partition annotation**: should the secret partition be specified
   at the IR level (which variables are secret) or at the domain level
   (which artifacts are secret)? The IR-level annotation is simpler but
   requires a mapping from domain artifacts to IR variables.

3. **Product IR fingerprinting**: the product IR has doubled variables and
   rules. How should its fingerprint be computed to ensure reproducibility?
   The existing `VerificationIR.fingerprint` can be applied to the product
   IR without modification.

4. **Counterexample interpretation**: if Z3 finds a counterexample in the
   product IR, how should it be mapped back to a pair of concrete ITES
   traces? This requires a witness-lifting step, analogous to the existing
   COI witness lifting.

5. **Observation granularity**: should the observation function include
   `consent` decisions, or only `read` and `visibility`? Including consent
   makes the property stronger but may produce false positives for
   benign consent disagreements.

6. **Dynamic principal sets**: the Principal Context grows during execution.
   Should the observer set be fixed at the initial state, or should it
   include principals that appear later? A fixed observer set is standard
   in noninterference; a dynamic observer set is more conservative but
   may be needed for agent scenarios where the set of relevant principals
   changes.

7. **Relation to robust disclosure (property 6)**: observational
   confidentiality (property 5) says observations agree for unauthorised
   observers. Robust disclosure (property 6) adds that an unauthorised
   influencing principal cannot control the disclosed value. Should the
   self-composition encoding for property 5 be designed to also support
   property 6, or should property 6 have a separate encoding?

## 11. Summary

Observational confidentiality is a relational hyperproperty that requires
comparing execution pairs. The recommended verification approach is
self-composition at the IR level: double the variables and rules, add
confidentiality invariants, apply COI reduction, and verify with the
existing Z3 BMC backend. This reuses existing infrastructure and produces
evidence at the `bounded_evidence` level.

The design is tractable for existing fixtures and small benchmarks. Larger
benchmarks may require principal-symmetry and control-flow abstractions.
Seven open questions remain, primarily around declassification encoding,
observation granularity, and the relationship to robust disclosure.
