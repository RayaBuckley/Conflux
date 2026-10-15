"""Tests for the unbounded Horn/Spacer verification backend."""

from __future__ import annotations

import pytest

from conflux.verification.delegation_ir import DelegationIRMutation, all_delegation_ir_variants, build_delegation_ir
from conflux.verification.horn_backend import verify_with_horn
from conflux.verification.ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)
from conflux.verification.results import FormalVerificationResult

z3 = pytest.importorskip("z3")

#: For each defect variant: the invariants the unbounded route refutes.
REFUTED_BY_VARIANT: dict[DelegationIRMutation, frozenset[str]] = {
    DelegationIRMutation.WIDENED_SCOPE: frozenset({"authority_narrowing", "delegation_attenuated"}),
    DelegationIRMutation.WRONG_BENEFICIARY: frozenset({"delegation_beneficiary_bound"}),
    DelegationIRMutation.REUSE: frozenset({"delegation_single_use"}),
    DelegationIRMutation.EXPIRY_BYPASS: frozenset({"delegation_expiry_enforced"}),
    DelegationIRMutation.REVOCATION_BYPASS: frozenset({"delegation_revocation_enforced"}),
    DelegationIRMutation.REDELEGATION: frozenset({"cascade_containment", "delegation_not_redelegated"}),
    DelegationIRMutation.POST_INFLUENCE_ISSUANCE: frozenset({"delegation_precedes_influence"}),
    DelegationIRMutation.REDELEGATION_CHAIN: frozenset({"cascade_containment", "delegation_not_redelegated"}),
    DelegationIRMutation.WIDENED_SCOPE_CHAIN: frozenset({"authority_narrowing", "delegation_attenuated"}),
    DelegationIRMutation.STALE_CONTEXT: frozenset({"delegation_context_preserved", "toctou_drift_detection"}),
}


def refuted(result: FormalVerificationResult) -> set[str]:
    """The invariant names a result records as refuted."""
    return {str(entry["invariant"]) for entry in result.counterexample}


def test_canonical_delegation_ir_is_safe_without_unrolling() -> None:
    result = verify_with_horn(build_delegation_ir())
    assert result.verdict.value == "safe"
    assert result.backend == "z3-spacer"
    assert result.error is None
    assert result.counterexample == ()


def test_the_safe_verdict_discloses_that_the_step_budget_was_dropped() -> None:
    result = verify_with_horn(build_delegation_ir())
    assert any(assumption.startswith("step_budget_dropped:") for assumption in result.assumptions)


VARIANT_ORDER = tuple(sorted(REFUTED_BY_VARIANT, key=str))


@pytest.mark.parametrize("mutation", VARIANT_ORDER)
def test_every_defect_variant_is_refuted_by_name(mutation: DelegationIRMutation) -> None:
    result = verify_with_horn(build_delegation_ir(mutation))
    assert result.verdict.value == "unsafe"
    assert REFUTED_BY_VARIANT[mutation] <= refuted(result)


def test_every_variant_is_covered_by_the_expectation_table() -> None:
    mutations = {row.mutation for row in all_delegation_ir_variants()}
    assert mutations == set(REFUTED_BY_VARIANT) | {DelegationIRMutation.CANONICAL}


def test_a_false_invariant_is_refuted_and_named() -> None:
    ir = build_delegation_ir()
    false_invariant = SafetyInvariant("always-false-claim", Expression.constant(False))
    mutated = VerificationIR(
        f"{ir.id}+false-claim",
        ir.variables,
        ir.transitions,
        (*ir.invariants, false_invariant),
        ir.bound,
        ir.assumptions,
    )
    result = verify_with_horn(mutated)
    assert result.verdict.value == "unsafe"
    assert "always-false-claim" in refuted(result)


def test_an_unreachable_state_is_not_reported_as_a_counterexample() -> None:
    """A query must be constrained by reachability, not merely by the declared domain.

    ``counter`` can only ever hold 0, but its declared domain also admits 1..3. A query that
    omits the reachability atom is satisfiable by ``counter != 0`` and would report unsafe.
    """
    counter = StateVariable("counter", Sort.INTEGER, 0, 0, 3)
    stutter = TransitionRule(
        "stutter",
        Expression.constant(True),
        (Assignment("counter", Expression.variable("counter")),),
    )
    is_zero = Expression.operator(
        ExpressionKind.EQUAL,
        Expression.variable("counter"),
        Expression.constant(0),
    )
    ir = VerificationIR(
        "unreachable-fixture",
        (counter,),
        (stutter,),
        (SafetyInvariant("counter-is-zero", is_zero),),
        1,
        (),
    )
    result = verify_with_horn(ir)
    assert result.verdict.value == "safe"


def test_a_boolean_assignment_value_is_translated() -> None:
    """A Boolean formula is a legal assignment value; the encoder must not refuse the IR."""
    flag = StateVariable("flag", Sort.BOOLEAN, False)
    other = StateVariable("other", Sort.BOOLEAN, False)
    rule = TransitionRule(
        "copy",
        Expression.constant(True),
        (
            Assignment(
                "flag",
                Expression.operator(ExpressionKind.AND, Expression.variable("other"), Expression.constant(True)),
            ),
            Assignment("other", Expression.variable("other")),
        ),
    )
    ir = VerificationIR(
        "boolean-assignment-fixture",
        (flag, other),
        (rule,),
        (SafetyInvariant("flag-is-false", Expression.operator(ExpressionKind.NOT, Expression.variable("flag"))),),
        1,
        (),
    )
    result = verify_with_horn(ir)
    assert result.error is None
    assert result.verdict.value == "safe"


def test_a_set_sorted_state_variable_is_refused_rather_than_weakened() -> None:
    granted = StateVariable("granted", Sort.SET, frozenset({"a"}))
    ir = VerificationIR(
        "set-fixture",
        (granted,),
        (),
        (SafetyInvariant("empty", Expression.constant(True)),),
        1,
        (),
    )
    result = verify_with_horn(ir)
    assert result.verdict.value == "unknown"
    assert result.error == "set_sort_not_supported_by_horn_backend"


def test_an_ir_without_invariants_is_refused() -> None:
    ir = VerificationIR("no-invariants", (StateVariable("x", Sort.INTEGER, 0),), (), (), 1, ())
    result = verify_with_horn(ir)
    assert result.verdict.value == "unknown"
    assert result.error == "no_safety_invariants"


def test_a_disjunctive_guard_is_refused_rather_than_weakened() -> None:
    x = StateVariable("x", Sort.INTEGER, 0, 0, 2)
    guard = Expression.operator(
        ExpressionKind.OR,
        Expression.operator(ExpressionKind.EQUAL, Expression.variable("x"), Expression.constant(0)),
        Expression.operator(ExpressionKind.EQUAL, Expression.variable("x"), Expression.constant(1)),
    )
    rule = TransitionRule("split", guard, (Assignment("x", Expression.variable("x")),))
    ir = VerificationIR(
        "disjunctive-fixture",
        (x,),
        (rule,),
        (SafetyInvariant("always", Expression.constant(True)),),
        1,
        (),
    )
    result = verify_with_horn(ir)
    assert result.verdict.value == "unknown"
    assert result.error is not None and result.error.startswith("unsupported_ir:")
