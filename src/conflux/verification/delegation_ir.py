"""Delegation safety properties encoded as serialisable verification IR.

This module encodes the delegation ``consume()`` logic (from
``conflux.domain.delegation``) as ``VerificationIR`` transition systems
with mutation variants.  Unlike the native SLED delegation model
(``conflux.evaluation.delegation_verification``) which uses abstract
boolean flags, this IR encoding models the actual consumption logic as
guarded transitions, making it available to all backends (Z3, nuXmv,
reference interpreter) and serialisable for reproducibility.

Mutations A2/A3/A4 add cascade containment, authority narrowing, and
TOCTOU drift properties beyond the original eight.

Source: SentinelAgent (arXiv:2604.02767) — deterministic delegation
properties; OpenPort (arXiv:2602.20196) — TOCTOU State Witness.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)


class DelegationIRMutation(StrEnum):
    """Canonical or defective delegation variant for IR verification."""

    CANONICAL = "canonical"
    WIDENED_SCOPE = "widened_scope"
    WRONG_BENEFICIARY = "wrong_beneficiary"
    REUSE = "reuse"
    EXPIRY_BYPASS = "expiry_bypass"
    REVOCATION_BYPASS = "revocation_bypass"
    REDELEGATION = "redelegation"
    POST_INFLUENCE_ISSUANCE = "post_influence_issuance"
    REDELEGATION_CHAIN = "redelegation_chain"
    WIDENED_SCOPE_CHAIN = "widened_scope_chain"
    STALE_CONTEXT = "stale_context"


DELEGATION_IR_BOUND = 4


def _variables() -> tuple[StateVariable, ...]:
    return (
        StateVariable("grant_consumed", Sort.BOOLEAN, False),
        StateVariable("grant_revoked", Sort.BOOLEAN, False),
        StateVariable("use_count", Sort.INTEGER, 0, 0, 2),
        StateVariable("expired", Sort.BOOLEAN, False),
        StateVariable("beneficiary_valid", Sort.BOOLEAN, True),
        StateVariable("scope_match", Sort.BOOLEAN, True),
        StateVariable("issued_before_influence", Sort.BOOLEAN, True),
        StateVariable("redelegated", Sort.BOOLEAN, False),
        StateVariable("context_verified", Sort.BOOLEAN, True),
        StateVariable("context_preserved", Sort.BOOLEAN, True),
        StateVariable("step", Sort.INTEGER, 0, 0, DELEGATION_IR_BOUND),
    )


def _invariants() -> tuple[SafetyInvariant, ...]:
    var = Expression.variable
    implies = ExpressionKind.IMPLIES
    not_ = ExpressionKind.NOT
    return (
        SafetyInvariant(
            "delegation_attenuated",
            Expression.operator(implies, var("grant_consumed"), var("scope_match")),
            "Consumed delegation does not widen its exact scope",
        ),
        SafetyInvariant(
            "delegation_beneficiary_bound",
            Expression.operator(implies, var("grant_consumed"), var("beneficiary_valid")),
            "Consumed delegation authorises only the intended beneficiary",
        ),
        SafetyInvariant(
            "delegation_single_use",
            Expression.operator(
                implies,
                var("grant_consumed"),
                Expression.operator(not_, Expression.operator(ExpressionKind.GREATER_THAN, var("use_count"), Expression.constant(1))),
            ),
            "Delegation is consumed at most once",
        ),
        SafetyInvariant(
            "delegation_expiry_enforced",
            Expression.operator(implies, var("grant_consumed"), Expression.operator(not_, var("expired"))),
            "Consumed delegation must not be expired",
        ),
        SafetyInvariant(
            "delegation_revocation_enforced",
            Expression.operator(implies, var("grant_consumed"), Expression.operator(not_, var("grant_revoked"))),
            "Consumed delegation must not be revoked",
        ),
        SafetyInvariant(
            "delegation_not_redelegated",
            Expression.operator(implies, var("grant_consumed"), Expression.operator(not_, var("redelegated"))),
            "Consumed delegation must not be redelegated",
        ),
        SafetyInvariant(
            "delegation_precedes_influence",
            Expression.operator(implies, var("grant_consumed"), var("issued_before_influence")),
            "Consumed delegation must be issued before any untrusted influence",
        ),
        SafetyInvariant(
            "delegation_context_preserved",
            Expression.operator(implies, var("grant_consumed"), var("context_preserved")),
            "Consumed delegation does not narrow the Principal Context",
        ),
        SafetyInvariant(
            "cascade_containment",
            Expression.operator(implies, var("grant_consumed"), Expression.operator(not_, var("redelegated"))),
            "Delegation cannot create unbounded authority chains",
        ),
        SafetyInvariant(
            "authority_narrowing",
            Expression.operator(implies, var("grant_consumed"), var("scope_match")),
            "Delegated authority cannot exceed issuer authority",
        ),
        SafetyInvariant(
            "toctou_drift_detection",
            Expression.operator(implies, var("grant_consumed"), var("context_verified")),
            "Context at verification time must match context at execution time",
        ),
    )


def _transitions(mutation: DelegationIRMutation) -> tuple[TransitionRule, ...]:
    var = Expression.variable
    const = Expression.constant
    step = var("step")
    step_guard = Expression.operator(ExpressionKind.LESS_EQUAL, step, const(DELEGATION_IR_BOUND - 1))
    step_inc = Assignment("step", Expression.operator(ExpressionKind.ADD, step, const(1)))

    not_consumed = Expression.operator(ExpressionKind.NOT, var("grant_consumed"))
    not_revoked = Expression.operator(ExpressionKind.NOT, var("grant_revoked"))

    consume_guard_parts: list[Expression] = [step_guard, not_consumed, not_revoked]

    if mutation is not DelegationIRMutation.EXPIRY_BYPASS:
        not_expired = Expression.operator(ExpressionKind.NOT, var("expired"))
        consume_guard_parts.append(not_expired)

    if mutation is not DelegationIRMutation.POST_INFLUENCE_ISSUANCE:
        consume_guard_parts.append(var("issued_before_influence"))

    if mutation is not DelegationIRMutation.WRONG_BENEFICIARY:
        consume_guard_parts.append(var("beneficiary_valid"))

    if mutation is not DelegationIRMutation.WIDENED_SCOPE:
        consume_guard_parts.append(var("scope_match"))

    if mutation is not DelegationIRMutation.STALE_CONTEXT:
        consume_guard_parts.append(var("context_verified"))

    consume_guard = Expression.operator(ExpressionKind.AND, *consume_guard_parts)

    use_count_expr = const(2) if mutation is DelegationIRMutation.REUSE else const(1)
    grant_consumed_expr = const(True)
    redelegated_expr = (
        const(True)
        if mutation
        in (
            DelegationIRMutation.REDELEGATION,
            DelegationIRMutation.REDELEGATION_CHAIN,
        )
        else const(False)
    )

    scope_match_expr = (
        const(False)
        if mutation
        in (
            DelegationIRMutation.WIDENED_SCOPE,
            DelegationIRMutation.WIDENED_SCOPE_CHAIN,
        )
        else const(True)
    )

    consume_assignments: list[Assignment] = [
        step_inc,
        Assignment("grant_consumed", grant_consumed_expr),
        Assignment("use_count", use_count_expr),
        Assignment("redelegated", redelegated_expr),
        Assignment("scope_match", scope_match_expr),
    ]

    if mutation is DelegationIRMutation.WRONG_BENEFICIARY:
        consume_assignments.append(Assignment("beneficiary_valid", const(False)))

    if mutation is DelegationIRMutation.POST_INFLUENCE_ISSUANCE:
        consume_assignments.append(Assignment("issued_before_influence", const(False)))

    if mutation is DelegationIRMutation.REVOCATION_BYPASS:
        consume_assignments.append(Assignment("grant_revoked", const(True)))

    if mutation is DelegationIRMutation.EXPIRY_BYPASS:
        consume_assignments.append(Assignment("expired", const(True)))

    if mutation is DelegationIRMutation.STALE_CONTEXT:
        consume_assignments.append(Assignment("context_verified", const(False)))
        consume_assignments.append(Assignment("context_preserved", const(False)))

    revoke_guard = Expression.operator(ExpressionKind.AND, step_guard, not_revoked, not_consumed)
    revoke_assignments = [
        step_inc,
        Assignment("grant_revoked", const(True)),
    ]

    expire_guard = Expression.operator(
        ExpressionKind.AND,
        step_guard,
        Expression.operator(ExpressionKind.NOT, var("expired")),
        not_consumed,
    )
    expire_assignments = [
        step_inc,
        Assignment("expired", const(True)),
    ]

    rules: list[TransitionRule] = [
        TransitionRule("attempt_use", consume_guard, tuple(consume_assignments)),
        TransitionRule("revoke_grant", revoke_guard, tuple(revoke_assignments)),
        TransitionRule("expire_grant", expire_guard, tuple(expire_assignments)),
    ]
    return tuple(rules)


def build_delegation_ir(mutation: DelegationIRMutation = DelegationIRMutation.CANONICAL) -> VerificationIR:
    """Build a verification IR for delegation safety under the given mutation."""
    return VerificationIR(
        id=f"delegation-ir:{mutation.value}",
        variables=_variables(),
        transitions=_transitions(mutation),
        invariants=_invariants(),
        bound=DELEGATION_IR_BOUND,
        assumptions=(
            "delegation grant is single-use with remaining_use_count=1",
            "redelegable=False is hardcoded",
            "consume() enforces scope, expiry, revocation, beneficiary, and temporal ordering",
            "stale_context mutation models TOCTOU drift between verification and execution time",
        ),
    )


@dataclass(frozen=True, slots=True)
class DelegationIRResult:
    """Summary of a delegation IR verification run."""

    mutation: DelegationIRMutation
    ir: VerificationIR


def all_delegation_ir_variants() -> tuple[DelegationIRResult, ...]:
    """Return IR variants for every mutation (canonical + defective)."""
    return tuple(DelegationIRResult(mutation, build_delegation_ir(mutation)) for mutation in DelegationIRMutation)


__all__ = [
    "DELEGATION_IR_BOUND",
    "DelegationIRMutation",
    "DelegationIRResult",
    "all_delegation_ir_variants",
    "build_delegation_ir",
]
