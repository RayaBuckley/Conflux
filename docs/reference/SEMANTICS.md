# Conflux Formal Semantics

This document specifies the algebraic structures and security properties
implemented by the Conflux domain and ITES kernel. Each property carries a
unique identifier (SEM-*), a formal statement, the code that enforces it, and
the tests that verify it. Each property also links to the decision record (ADR)
that motivated its design.

## Domain algebraic structures

### SEM-001: PrincipalContext is a join semilattice

`PrincipalContext` with `merge` forms a join semilattice over the set of
Principals, extended with an absorbing `unknown` flag.

```text
Commutativity:   a.merge(b) == b.merge(a)
Associativity:   a.merge(b).merge(c) == a.merge(b.merge(c))
Idempotence:     a.merge(a) == a
Monotonicity:    a.principals ⊆ a.merge(b).principals
Unknown absorbs: if a.unknown or b.unknown then a.merge(b).unknown
```

| Aspect | Location |
|---|---|
| Definition | `src/conflux/domain/identity.py` `PrincipalContext.merge` |
| Tests | `tests/test_domain.py::test_provenance_merge_never_drops_principals`, `test_unknown_precision_dominates_merge`, `test_combination_is_monotone` |
| Algebraic tests | `tests/semantics/test_algebraic_laws.py::test_pc_merge_commutative` etc. |
| ADR | [ADR-002](../decisions/002-principal-context-terminology.md) |

### SEM-002: is_authority_bearing guard

A `PrincipalContext` is authority-bearing if and only if it contains at least
one Principal and is not unknown:

```text
ctx.is_authority_bearing  ==  (ctx.principals ≠ ∅) ∧ ¬ctx.unknown
```

All authorisation decisions require `is_authority_bearing`; empty or unknown
contexts deny all effectful actions.

| Aspect | Location |
|---|---|
| Definition | `src/conflux/domain/identity.py` `PrincipalContext.is_authority_bearing` |
| Tests | `tests/test_domain.py::test_empty_principal_context_is_not_authority_bearing`, `test_policy_and_ites.py::test_empty_context_denies_effect` |
| ADR | [ADR-002](../decisions/002-principal-context-terminology.md) |

### SEM-003: Provenance is a commutative monoid

`Provenance` with `merge` forms a commutative monoid. The identity element is
`Provenance.unknown()`, and merge is:

```text
Commutativity:          a.merge(b) == b.merge(a)
Associativity:          a.merge(b).merge(c) == a.merge(b.merge(c))
Identity:               a.merge(Provenance.unknown()) has is_unknown == a.is_unknown or True
Precision monotonicity:  max(precision_rank(a), precision_rank(b))
Attestation conjunction: a.merge(b).attested == a.attested ∧ b.attested
```

| Aspect | Location |
|---|---|
| Definition | `src/conflux/domain/provenance.py` `Provenance.merge` |
| Tests | `tests/test_domain.py::test_provenance_merge_never_drops_principals`, `test_unknown_precision_dominates_merge` |
| ADR | [ADR-004](../decisions/004-immutable-state-and-provenance.md) |

### SEM-004: Provenance is not a read ACL

Provenance describes influence origin; it does not determine read access.
Read policy is a separate, independent decision.

```text
∀ principal, artifact:
  principal ∈ artifact.provenance.principals  ⟏  read_policy.allow(principal, artifact)
```

The mutant `ProvenanceAsReadPolicy` violates this and is killed by SLED.

| Aspect | Location |
|---|---|
| Separation | `src/conflux/ports/policy.py` `ReadPolicyPort` vs `Provenance` |
| Mutant | `tests/semantics/mutants.py` `ProvenanceAsReadPolicy` |
| Kill test | `tests/semantics/test_mutation_killing.py::test_provenance_as_acl_mutant` |
| ADR | [ADR-004](../decisions/004-immutable-state-and-provenance.md) |

## Decision composition

### SEM-005: ActionDecision is a conjunction of independent decisions

An `ActionDecision` is allowed if and only if every independent decision
dimension allows:

```text
ActionDecision.allowed == auth.allow ∧ arg_auth.allow? ∧ read.allow ∧ vis.allow ∧ consent.allow
```

Where `arg_auth` is required when present and ignored when absent. No single
dimension can override a denial in another.

| Aspect | Location |
|---|---|
| Definition | `src/conflux/domain/decisions.py` `ActionDecision.allowed` |
| Tests | `tests/test_policy_and_ites.py::test_mixed_context_requires_every_principal`, `test_missing_consent_denies_effect` |
| ADR | [ADR-009](../decisions/009-branch-and-consent-semantics.md) |

### SEM-006: Consent never manufactures authority

Consent is a restricting decision only:

```text
consent.allow ∧ ¬auth.allow  →  ¬ActionDecision.allowed
```

Consent can deny an otherwise-allowed action but cannot permit a
denied one. The mutant `EmptyContextAllow` violates this and is killed by SLED.

| Aspect | Location |
|---|---|
| Rule | `docs/reference/SECURITY_MODEL.md` normative rules |
| Mutant | `tests/semantics/mutants.py` `EmptyContextAllow` |
| Kill test | `tests/semantics/test_mutation_killing.py::test_empty_context_allow_mutant` |
| ADR | [ADR-009](../decisions/009-branch-and-consent-semantics.md) |

### SEM-007: Authorisation requires pointwise Principal allow

Every Principal in the context must independently receive a policy allow:

```text
ActionDecision.allowed  →  ∀ p ∈ PrincipalContext.principals: policy.allow(p, action)
```

One Principal cannot lend permissions to another. The mutant `PermissionUnion`
violates this and is killed by SLED.

| Aspect | Location |
|---|---|
| Rule | `docs/reference/SECURITY_MODEL.md` normative rules |
| Mutant | `tests/semantics/mutants.py` `PermissionUnion` |
| Kill test | `tests/semantics/test_mutation_killing.py::test_permission_union_mutant` |
| ADR | [ADR-009](../decisions/009-branch-and-consent-semantics.md) |

## Transition kernel

### SEM-008: Complete mediation

Every action crosses the ITES kernel before any effect is observable:

```text
execute(action)  →  ∃ certificate: TransitionKernel._transition(parent, action, ...) ∧ certificate ≠ None
```

No action bypasses mediation. The kernel is the sole authority path.

| Aspect | Location |
|---|---|
| Implementation | `src/conflux/ites/kernel.py` `TransitionKernel._transition` |
| Tests | `tests/test_policy_and_ites.py::test_execution_requires_matching_certificate` |
| ADR | [ADR-006](../decisions/006-canonical-ites-contract.md), [ADR-008](../decisions/008-canonical-security-kernel.md) |

Consuming information from an additional Principal can preserve or reduce
effective authority but cannot increase it. The context is merged with
action provenance before the decision:

```text
decision_context = parent.context.merge(action_provenance(action).context)
```

After merge, the Principal set is a superset and the authority can only
decrease (more Principals must each independently allow).

| Aspect | Location |
|---|---|
| Implementation | `src/conflux/ites/kernel.py:98` |
| Tests | `tests/test_policy_and_ites.py::test_nested_execution_accumulates_provenance_and_hits_bound` |
| ADR | [ADR-012](../decisions/012-foundational-security-lineage.md) |

### SEM-010: Branch isolation (alternative siblings)

In `ALTERNATIVES` mode, each proposal branches independently of the same
parent. Sibling branches never observe each other's context:

```text
∀ i, j: i ≠ j  →  child_i.context does not depend on proposal_j
```

The mutant `SiblingLeakKernel` violates this and is killed by SLED.

| Aspect | Location |
|---|---|
| Implementation | `src/conflux/ites/kernel.py` `expand_batch` (alternatives path) |
| Mutant | `tests/semantics/mutants.py` `SiblingLeakKernel` |
| Kill test | `tests/semantics/test_mutation_killing.py::test_sibling_leak_mutant` |
| ADR | [ADR-009](../decisions/009-branch-and-consent-semantics.md) |

### SEM-011: Ordered-plan sequential propagation

In `ORDERED_PLAN` mode, proposals propagate state sequentially. The plan
stops at the first denial or provider failure:

```text
stop at first: status == BLOCKED  →  no further proposals processed
```

| Aspect | Location |
|---|---|
| Implementation | `src/conflux/ites/kernel.py` `expand_batch` (ordered path) |
| Tests | `tests/test_policy_and_ites.py::test_ordered_plan_stops_at_first_denial`, `test_ordered_plan_execution_stops_on_provider_failure` |
| ADR | [ADR-009](../decisions/009-branch-and-consent-semantics.md) |

### SEM-012: Certificate binding

A decision certificate binds to the exact action fingerprint, context
fingerprint, branch identity, and policy versions at decision time. Execution
requires a match:

```text
certificate.action_fingerprint == action_fingerprint(effect_action)
certificate.context_fingerprint == context.fingerprint
certificate.branch_id == executing_branch_id
```

A certificate from one branch cannot authorise an effect on another.

| Aspect | Location |
|---|---|
| Implementation | `src/conflux/ites/state.py` `DecisionCertificate.issue`, `src/conflux/application/mediate.py` re-authorisation |
| Tests | `tests/test_policy_and_ites.py::test_execution_requires_matching_certificate` |
| ADR | [ADR-006](../decisions/006-canonical-ites-contract.md) |

The context at execution time must match the context at decision time. If
policy has changed (revocation), the certificate is invalid:

```text
context_at_execution.fingerprint ≠ certificate.context_fingerprint  →  blocked
```

The mutant `StaleContextKernel` violates this and is killed by SLED.

| Aspect | Location |
|---|---|
| Implementation | `src/conflux/application/mediate.py` |
| Mutant | `tests/semantics/mutants.py` `StaleContextKernel` |
| Kill test | `tests/semantics/test_mutation_killing.py::test_stale_context_mutant` |
| Integration | `tests/test_policy_and_ites.py::test_execution_reauthorises_and_observes_policy_revocation` |
| ADR | [ADR-006](../decisions/006-canonical-ites-contract.md) |

### SEM-014: Rejected proposals are diagnostics, not violations

A blocked proposal is a successful defence outcome, not an executed security
violation. Safety properties must not fire on rejected proposals:

```text
BranchStatus.BLOCKED  →  not an execution, not a violation
```

The mutant test `ExecutedInvariantOnly` enforces this distinction.

| Aspect | Location |
|---|---|
| Rule | `docs/reference/SECURITY_MODEL.md` normative rules |
| Property | `tests/semantics/mutants.py` `ExecutedInvariantOnly` |
| Kill test | `tests/semantics/test_mutation_killing.py::test_rejected_proposal_misclassification_mutant` |
| ADR | [ADR-008](../decisions/008-canonical-security-kernel.md) |

## Policy ports

### SEM-015: Policy dimensions are independent

Authorisation, read, visibility, and consent are separate policy decisions.
No dimension can override another:

```text
¬(auth.allow ∧ read.deny) → allowed  (read denial blocks regardless of auth)
¬(consent.allow ∧ vis.deny) → allowed  (visibility denial blocks regardless of consent)
```

| Aspect | Location |
|---|---|
| Definition | `src/conflux/ports/policy.py` independent port protocols |
| Composition | `src/conflux/domain/decisions.py` `ActionDecision.allowed` (conjunction) |
| ADR | [ADR-009](../decisions/009-branch-and-consent-semantics.md) |

### SEM-016: Fail-closed defaults

Missing consent, unknown schemas, policy errors, and unavailable boundaries
deny:

```text
missing_consent  →  denied
unknown_schema   →  denied
policy_error    →  denied
unavailable     →  denied
```

| Aspect | Location |
|---|---|
| Tests | `tests/test_policy_and_ites.py::test_missing_consent_denies_effect`, `test_delegation_is_unsupported` |
| ADR | [ADR-005](../decisions/005-testing-and-validation.md) |

## SLED property cross-reference

| SLED property | SEM ID | Status |
|---|---|---|
| Authority safety | SEM-005, SEM-007, SEM-008 | Supported |
| Provenance monotonicity | SEM-001, SEM-009 | Supported |
| Read safety | SEM-004, SEM-015 | Supported |
| Branch isolation | SEM-010 | Supported |
| Certificate binding | SEM-012, SEM-013 | Supported |
| Delegation safety | — | Model only, runtime disabled |
| Observational confidentiality | — | Future work |
| Robust disclosure | — | Future work |
| Liveness / utility | — | Future work |

See [SLED](SLED.md) for the verification approach and verdict semantics.
