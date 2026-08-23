"""Tests for confidentiality levels and declassification boundary enforcement."""

from __future__ import annotations

import pytest

from conflux.verification import (
    Assignment,
    Expression,
    ExpressionKind,
    FormalVerdict,
    SafetyInvariant,
    SecretPartition,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
    construct_product_ir,
    reference_safety_check,
)

pytestmark = pytest.mark.security


def _var(name: str) -> Expression:
    return Expression.variable(name)


def _const(value: bool | int) -> Expression:
    return Expression.constant(value)


def _not(expr: Expression) -> Expression:
    return Expression.operator(ExpressionKind.NOT, expr)


def _and(*exprs: Expression) -> Expression:
    return Expression.operator(ExpressionKind.AND, *exprs)


def _equal(a: Expression, b: Expression) -> Expression:
    return Expression.operator(ExpressionKind.EQUAL, a, b)


def _assignment(var: str, expr: Expression) -> Assignment:
    return Assignment(var, expr)


def _safety(id_: str, expr: Expression) -> SafetyInvariant:
    return SafetyInvariant(id_, expr)


class TestAccessSafetyVsObservationalConfidentiality:
    """A fixture where authorised reads hold but observational confidentiality fails.

    This demonstrates the distinction between:
    - Access safety (Level 1): no forbidden read occurs.
    - Observational confidentiality (Level 2): varying secret information
      does not alter unauthorised observations.

    The model has a secret variable ``secret`` and an observable ``output``
    that copies the secret.  Access safety holds (the read is authorised),
    but observational confidentiality fails (the output leaks the secret).
    """

    def _leaky_ir(self) -> VerificationIR:
        return VerificationIR(
            id="leaky-confidentiality",
            variables=(
                StateVariable("secret", Sort.BOOLEAN, False),
                StateVariable("read_authorised", Sort.BOOLEAN, True),
                StateVariable("output", Sort.BOOLEAN, False),
            ),
            transitions=(
                TransitionRule(
                    "copy-secret-to-output",
                    _var("read_authorised"),
                    (_assignment("output", _var("secret")),),
                ),
            ),
            invariants=(_safety("access-safety", _var("read_authorised")),),
            bound=3,
            assumptions=(
                "access safety: read is authorised",
                "observational confidentiality: output should not leak secret",
            ),
        )

    def test_access_safety_holds(self) -> None:
        ir = self._leaky_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_observational_confidentiality_fails(self) -> None:
        ir = self._leaky_ir()
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
            observer_description="unauthorised observer",
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_counterexample_shows_divergence(self) -> None:
        ir = self._leaky_ir()
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
            observer_description="unauthorised observer",
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert len(result.counterexample) > 0
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("output") != final_state.get("output__prime")


class TestDeclassificationBoundaryEnforcement:
    """Declassification boundaries exclude rules from the confidentiality check."""

    def _declassification_ir(self) -> VerificationIR:
        return VerificationIR(
            id="declassification-test",
            variables=(
                StateVariable("secret", Sort.BOOLEAN, False),
                StateVariable("read_authorised", Sort.BOOLEAN, True),
                StateVariable("output", Sort.BOOLEAN, False),
            ),
            transitions=(
                TransitionRule(
                    "declassify-secret",
                    _var("read_authorised"),
                    (_assignment("output", _var("secret")),),
                ),
            ),
            invariants=(_safety("access-safety", _var("read_authorised")),),
            bound=3,
            assumptions=("declassification boundary: 'declassify-secret' is a permitted release",),
        )

    def test_without_boundary_confidentiality_fails(self) -> None:
        ir = self._declassification_ir()
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
            observer_description="unauthorised observer",
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_with_boundary_confidentiality_holds(self) -> None:
        ir = self._declassification_ir()
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
            observer_description="unauthorised observer",
            declassification_boundaries=("declassify-secret",),
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_boundary_adds_tracking_variable(self) -> None:
        ir = self._declassification_ir()
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
            observer_description="unauthorised observer",
            declassification_boundaries=("declassify-secret",),
        )
        product = construct_product_ir(ir, partition)
        var_names = {v.name for v in product.variables}
        assert "__declassified__declassify-secret" in var_names
