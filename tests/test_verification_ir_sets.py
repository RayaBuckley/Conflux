"""Tests for verification IR set sorts and set expressions."""

from __future__ import annotations

import pytest

from conflux.verification import (
    Expression,
    ExpressionKind,
    FormalVerdict,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
    evaluate,
    reference_safety_check,
    verify_with_z3,
)

pytestmark = pytest.mark.security


class TestSetSort:
    """Set-typed state variables in the verification IR."""

    def test_set_variable_creation(self) -> None:
        var = StateVariable("principals", Sort.SET, frozenset({"alice"}))
        assert var.sort == Sort.SET
        assert var.initial == frozenset({"alice"})

    def test_set_variable_rejects_non_set(self) -> None:
        with pytest.raises(ValueError, match="set state variable requires a set"):
            StateVariable("principals", Sort.SET, True)

    def test_set_variable_rejects_numeric_bounds(self) -> None:
        with pytest.raises(ValueError, match="cannot have numeric bounds"):
            StateVariable("principals", Sort.SET, frozenset(), minimum=0)

    def test_set_variable_serialisation(self) -> None:
        var = StateVariable("pc", Sort.SET, frozenset({"alice", "bob"}))
        d = var.to_dict()
        assert d["sort"] == "set"
        assert d["initial"] == ["alice", "bob"]

    def test_set_variable_round_trip(self) -> None:
        var = StateVariable("pc", Sort.SET, frozenset({"alice", "bob"}))
        d = var.to_dict()
        from conflux.verification.ir import _parse_variable

        restored = _parse_variable(d)
        assert restored.sort == Sort.SET
        assert restored.initial == frozenset({"alice", "bob"})


class TestSetExpressions:
    """Set expression evaluation in the interpreter."""

    def test_in_expression(self) -> None:
        expr = Expression.operator(
            ExpressionKind.IN,
            Expression.constant("alice"),
            Expression.variable("pc"),
        )
        state = {"pc": frozenset({"alice", "bob"})}
        assert evaluate(expr, state) is True

    def test_in_expression_false(self) -> None:
        expr = Expression.operator(
            ExpressionKind.IN,
            Expression.constant("mallory"),
            Expression.variable("pc"),
        )
        state = {"pc": frozenset({"alice", "bob"})}
        assert evaluate(expr, state) is False

    def test_subset_expression(self) -> None:
        expr = Expression.operator(
            ExpressionKind.SUBSET,
            Expression.variable("pc"),
            Expression.variable("authorised"),
        )
        state = {
            "pc": frozenset({"alice"}),
            "authorised": frozenset({"alice", "bob"}),
        }
        assert evaluate(expr, state) is True

    def test_subset_expression_false(self) -> None:
        expr = Expression.operator(
            ExpressionKind.SUBSET,
            Expression.variable("pc"),
            Expression.variable("authorised"),
        )
        state = {
            "pc": frozenset({"alice", "mallory"}),
            "authorised": frozenset({"alice", "bob"}),
        }
        assert evaluate(expr, state) is False

    def test_union_expression(self) -> None:
        expr = Expression.operator(
            ExpressionKind.UNION,
            Expression.variable("pc"),
            Expression.variable("new_principals"),
        )
        state = {
            "pc": frozenset({"alice"}),
            "new_principals": frozenset({"bob"}),
        }
        result = evaluate(expr, state)
        assert result == frozenset({"alice", "bob"})

    def test_intersect_expression(self) -> None:
        expr = Expression.operator(
            ExpressionKind.INTERSECT,
            Expression.variable("pc"),
            Expression.variable("authorised"),
        )
        state = {
            "pc": frozenset({"alice", "mallory"}),
            "authorised": frozenset({"alice", "bob"}),
        }
        result = evaluate(expr, state)
        assert result == frozenset({"alice"})


class TestSetIRModel:
    """A complete IR model using set-typed variables."""

    def _principal_set_ir(self) -> VerificationIR:
        return VerificationIR(
            id="set-test",
            variables=(
                StateVariable("pc", Sort.SET, frozenset()),
                StateVariable("action_executed", Sort.BOOLEAN, False),
                StateVariable("pe_violation", Sort.BOOLEAN, False),
            ),
            transitions=(
                TransitionRule(
                    "add-attacker-to-pc",
                    Expression.constant(True),
                    (
                        _assignment(
                            "pc",
                            _union(
                                _var("pc"),
                                Expression.constant("mallory"),
                            ),
                        ),
                    ),
                ),
                TransitionRule(
                    "safe-execute",
                    _and(
                        _not(
                            Expression.operator(
                                ExpressionKind.IN,
                                Expression.constant("mallory"),
                                _var("pc"),
                            )
                        ),
                    ),
                    (
                        _assignment("action_executed", Expression.constant(True)),
                        _assignment("pe_violation", Expression.constant(False)),
                    ),
                ),
                TransitionRule(
                    "unsafe-execute",
                    Expression.operator(
                        ExpressionKind.IN,
                        Expression.constant("mallory"),
                        _var("pc"),
                    ),
                    (
                        _assignment("action_executed", Expression.constant(True)),
                        _assignment("pe_violation", Expression.constant(True)),
                    ),
                ),
            ),
            invariants=(
                _safety(
                    "no-pe",
                    Expression.operator(
                        ExpressionKind.NOT,
                        Expression.variable("pe_violation"),
                    ),
                ),
            ),
            bound=5,
            assumptions=("test IR with set-typed principal context",),
        )

    def test_set_ir_round_trips(self) -> None:
        ir = self._principal_set_ir()
        restored = VerificationIR.from_dict(ir.to_dict())
        assert restored.fingerprint == ir.fingerprint

    def test_set_ir_reference_check_finds_violation(self) -> None:
        ir = self._principal_set_ir()
        result = reference_safety_check(ir)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_z3_backend_returns_unknown_for_sets(self) -> None:
        ir = self._principal_set_ir()
        result = verify_with_z3(ir)
        assert result.verdict == FormalVerdict.UNKNOWN
        assert "set_sort_not_supported" in (result.error or "")


def _var(name: str) -> Expression:
    return Expression.variable(name)


def _const(value: bool | int | str) -> Expression:
    return Expression.constant(value)


def _not(expr: Expression) -> Expression:
    return Expression.operator(ExpressionKind.NOT, expr)


def _and(*exprs: Expression) -> Expression:
    return Expression.operator(ExpressionKind.AND, *exprs)


def _union(*exprs: Expression) -> Expression:
    return Expression.operator(ExpressionKind.UNION, *exprs)


def _assignment(var: str, expr: Expression):
    from conflux.verification import Assignment

    return Assignment(var, expr)


def _safety(id_: str, expr: Expression):
    from conflux.verification import SafetyInvariant

    return SafetyInvariant(id_, expr)
