"""Cone-of-influence reduction and witness-lifting regression tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator

from conflux.verification import (
    Assignment,
    Expression,
    ExpressionKind,
    FormalVerdict,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
    compare_cone_of_influence,
    reduce_cone_of_influence,
)

pytestmark = pytest.mark.security

ROOT = Path(__file__).resolve().parents[1]


def _not(expression: Expression) -> Expression:
    return Expression.operator(ExpressionKind.NOT, expression)


def reducible_ir(*, unsafe: bool = False) -> VerificationIR:
    return VerificationIR(
        "coi-fixture",
        (
            StateVariable("safe", Sort.BOOLEAN, True),
            StateVariable("control", Sort.BOOLEAN, unsafe),
            StateVariable("guard", Sort.BOOLEAN, True),
            StateVariable("noise", Sort.INTEGER, 0, 0, 3),
            StateVariable("noise_cycle", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "apply-control",
                Expression.variable("guard"),
                (
                    Assignment("safe", _not(Expression.variable("control"))),
                    Assignment("control", Expression.variable("control")),
                    Assignment("noise", Expression.constant(1)),
                ),
            ),
            TransitionRule(
                "disable-guard",
                Expression.constant(False),
                (Assignment("guard", Expression.constant(False)),),
            ),
            TransitionRule(
                "irrelevant-cycle",
                Expression.constant(True),
                (
                    Assignment(
                        "noise_cycle",
                        _not(Expression.variable("noise_cycle")),
                    ),
                ),
            ),
        ),
        (SafetyInvariant("safe-remains-true", Expression.variable("safe")),),
        4,
        ("fixture assignments are synchronous",),
    )


def test_reduction_closes_over_guards_rhs_and_simultaneous_assignments() -> None:
    reduction = reduce_cone_of_influence(reducible_ir(), ("safe-remains-true",))
    assert reduction.applicable
    assert reduction.retained_variables == ("control", "guard", "safe")
    assert reduction.removed_variables == ("noise", "noise_cycle")
    assert reduction.retained_rules == ("apply-control", "disable-guard")
    assert reduction.removed_rules == ("irrelevant-cycle",)
    apply = next(rule for rule in reduction.reduced_ir.transitions if rule.id == "apply-control")
    assert tuple(item.variable for item in apply.assignments) == ("safe", "control")
    assert reduction.reduced_ir.bound == reducible_ir().bound
    assert reduction.reduced_ir.assumptions == reducible_ir().assumptions


def test_reduction_is_deterministic_and_schema_valid() -> None:
    first = reduce_cone_of_influence(reducible_ir(), ("safe-remains-true",))
    second = reduce_cone_of_influence(reducible_ir(), ("safe-remains-true",))
    assert first.to_dict() == second.to_dict()
    schema = cast(
        dict[str, object],
        json.loads((ROOT / "schemas" / "verification-reduction.schema.json").read_text(encoding="utf-8")),
    )
    Draft202012Validator(schema).validate(first.to_dict())


def test_safe_original_and_reduced_models_agree() -> None:
    comparison = compare_cone_of_influence(reducible_ir(), ("safe-remains-true",))
    assert comparison.equivalent
    assert comparison.original.verdict == FormalVerdict.SAFE
    assert comparison.reduced.verdict == FormalVerdict.SAFE
    assert comparison.reduced.states < comparison.original.states
    assert comparison.reduction.witness_lifting.validated is None


def test_shortest_reduced_counterexample_lifts_to_original() -> None:
    comparison = compare_cone_of_influence(reducible_ir(unsafe=True), ("safe-remains-true",))
    assert comparison.equivalent
    assert comparison.original.verdict == FormalVerdict.UNSAFE
    assert comparison.reduced.verdict == FormalVerdict.UNSAFE
    assert len(comparison.reduced.counterexample) == 2
    assert comparison.reduction.witness_lifting.validated is True


def test_multiple_invariants_select_the_union_of_dependencies() -> None:
    ir = reducible_ir()
    expanded = replace(
        ir,
        invariants=(
            *ir.invariants,
            SafetyInvariant(
                "bounded-noise",
                Expression.operator(
                    ExpressionKind.LESS_EQUAL,
                    Expression.variable("noise"),
                    Expression.constant(3),
                ),
            ),
        ),
    )
    reduction = reduce_cone_of_influence(expanded, ("safe-remains-true", "bounded-noise"))
    assert "noise" in reduction.retained_variables
    assert "noise_cycle" in reduction.removed_variables


def test_constant_property_returns_unchanged_explicit_fallback() -> None:
    ir = replace(
        reducible_ir(),
        invariants=(SafetyInvariant("constant", Expression.constant(True)),),
    )
    reduction = reduce_cone_of_influence(ir, ("constant",))
    assert not reduction.applicable
    assert reduction.reason == "selected_invariants_have_no_state_variables"
    assert reduction.original_fingerprint == reduction.reduced_fingerprint


def test_complete_cone_returns_unchanged_explicit_fallback() -> None:
    ir = VerificationIR(
        "complete",
        (StateVariable("safe", Sort.BOOLEAN, True),),
        (
            TransitionRule(
                "retain",
                Expression.constant(True),
                (Assignment("safe", Expression.variable("safe")),),
            ),
        ),
        (SafetyInvariant("safe", Expression.variable("safe")),),
        2,
    )
    reduction = reduce_cone_of_influence(ir, ("safe",))
    assert not reduction.applicable
    assert reduction.reason == "cone_is_already_complete"
    assert reduction.reduced_ir is ir


def test_empty_selection_means_all_and_invalid_selections_fail_closed() -> None:
    ir = reducible_ir()
    assert reduce_cone_of_influence(ir, ()).invariant_ids == ("safe-remains-true",)
    with pytest.raises(ValueError, match="unknown verification invariants"):
        reduce_cone_of_influence(ir, ("missing",))
    with pytest.raises(ValueError, match="must be unique"):
        reduce_cone_of_influence(ir, ("safe-remains-true", "safe-remains-true"))
