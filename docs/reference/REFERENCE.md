# Public API Reference

## `conflux.domain` — Immutable security-domain values

| Type | Invariant |
|---|---|
| `Principal` | Identity only; authority comes from policy, not identity |
| `PrincipalContext` | Join semilattice via `merge` (SEM-001); `is_authority_bearing` guard (SEM-002) |
| `Provenance` | Commutative monoid via `merge` (SEM-003); not a read ACL (SEM-004) |
| `Artifact` | Immutable; fingerprint is deterministic |
| `ResourceRef` | Stable protected-object reference |
| `ActionArgument` | Immutable; `authority_bearing` derived from trusted `ArgumentRole` |
| `OperationArgumentSchema` | Trusted role assignment; model output cannot change roles |
| `ActionDecision` | Conjunction of independent decisions (SEM-005) |
| `PrimitiveAction` | Declares permission and resource; no side effect on construction |
| `NestedExecutionAction` | Requires inputs; provenance merged into context at transition |
| `ProposalBatch` | Immutable; `ALTERNATIVES` branches independently, `ORDERED_PLAN` propagates sequentially |
| Delegation values | Scoped, one-use, expiry-bound, revocable; runtime disabled |

## `conflux.ports` — Independent fail-closed policy boundaries

| Port | Contract |
|---|---|
| `AuthorisationPort` | Pointwise decision per Principal (SEM-007) |
| `ReadPolicyPort` | Independent of provenance (SEM-004) |
| `ArgumentAuthorisationPort` | Required for authority-bearing selectors |
| `VisibilityPolicyPort` | Per-action observation decision |
| `ConsentPolicyPort` | Restricting only; never grants authority (SEM-006) |
| `AudienceVisibilityPolicyPort` | Per-audience, per-event-class projection |

All ports return `Decision` with non-empty `reason`, `policy_id`, and
`policy_version`. Denial is the default for errors, unknowns, and missing
configuration (SEM-016).

## `conflux.policy` — Deterministic offline policies

`InMemoryAuthorisationPolicy`: pointwise Principal grants, explicit deny
overrides. `SnapshotReadPolicy`: data-owner-based read decisions.
`SessionVisibilityPolicy`: participant-based visibility.
`ExplicitConsentPolicy`: opt-in consent for named operations.
`ArgumentGrantPolicy`: pointwise authority for action selectors.
Audience disclosure levels: `none`, `existence`, `redacted`, `full`.

## `conflux.application` — Decision composition and mediation

`DecisionPipeline`: composes independent policy dimensions into an
`ActionDecision`. Every dimension must allow (SEM-005).

`MediationService`: re-runs all policy dimensions immediately before each
effect. Certificate must match (SEM-012). Revocation blocks execution
(SEM-013). Provider failure is separate from policy denial.

## `conflux.ites` — Sole security transition kernel

`TransitionKernel._transition`: complete mediation (SEM-008) with context
merge (SEM-009), branch isolation (SEM-010), ordered-plan stop-at-first
(SEM-011), and certificate binding (SEM-012).

`DecisionCertificate.issue`: binds action fingerprint, context fingerprint,
branch identity, and policy versions.

`BranchState.initial`: derives initial context from input provenance; unknown
when no inputs. State key is deterministic.

`ITESReport`: immutable report with safety assessments. Execution records
require a matching certificate. `no_unauthorised_execution` assessment
considers only executed (not blocked) branches (SEM-014).

## `conflux.evaluation` — SLED bounded verification

`ExplicitStateChecker`: BFS exploration with depth, state, transition, and
model-call bounds. Verdicts: `SAFE`, `BOUNDED_SAFE`, `UNSAFE`, `UNKNOWN`.

Properties: `NoUnauthorisedAuthorisation`, `NoForbiddenObservation`,
`PrincipalContextMonotonicity`, `ProvenancePreserved`,
`ArgumentSelectorsAuthorised`. See [SLED](SLED.md) and
[Semantics](SEMANTICS.md).

## `conflux.verification` — Formal subset and optional backends

Serialisable finite-state IR with reference interpreter. Cone-of-influence
reduction is property-scoped. Reduction comparisons check original versus
reduced verdicts. Optional Z3 and nuXmv backends; missing or unsupported
returns `UNKNOWN`.

## `conflux.adapters` — External translations

Provider, policy, and benchmark adapters translate external systems without
redefining security decisions.

---

Stable offline adapters are `ScriptedModel`, `load_scenario`,
`InMemoryExecutor`, and `ConfinedFilesystemExecutor`. The filesystem executor
is dry-run by default and live writes require a matching precondition hash.
See [Deterministic Runtime](RUNTIME.md) for the fail-closed contract.

The installed `conflux` entry point exposes the supported runtime and native
verification workflows. See the [CLI contract](CLI.md) for commands and exit
codes.

There are no compatibility imports from `core`, `auth`, `research`, or
`compatibility`.
