"""Tests for expanding SET-sorted IR state into the Boolean fragment."""

from __future__ import annotations

import pytest

from conflux.verification import defence_models as dm
from conflux.verification.horn_backend import verify_with_horn
from conflux.verification.interpreter import evaluate
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
from conflux.verification.sensitivity import (
    CLASS_CHECKED,
    CLASS_CHECKED_BY_CONSTRUCTION,
    classify_ir,
    reachable_states,
)
from conflux.verification.set_encoding import SetExpansionError, expand_sets, member_variable
from conflux.verification.z3_backend import verify_with_z3

SET_FACTORIES = ("ites_with_read_check_ir", "fides_native_property_ir", "pace_native_property_ir")

#: Every SET model that is in the catalogue, and whether its invariants are falsifiable.
#: ``ites_with_read_check_ir`` states ``not pe_violation``, but no rule ever assigns
#: ``pe_violation`` True, so the property holds by construction rather than by any guard.
EXPECTED_EXERCISE = {
    "ites_with_read_check_ir": {"no-pe-violation": CLASS_CHECKED_BY_CONSTRUCTION},
    "fides_native_property_ir": {
        "no-untrusted-action": CLASS_CHECKED,
        "no-flow-to-untrusted-reader": CLASS_CHECKED,
    },
    "pace_native_property_ir": {"no-uncut-flow-to-unsafe-terminal": CLASS_CHECKED},
}


def _set_models() -> list[tuple[str, VerificationIR]]:
    return [(name, getattr(dm, name)()) for name in SET_FACTORIES]


def _counter_ir(universe: tuple[str, ...]) -> VerificationIR:
    """A set model whose invariant is falsifiable: the attacker may join the permitted set."""
    return VerificationIR(
        "set-counter",
        (
            StateVariable("holders", Sort.SET, frozenset({"alice"}), universe=universe),
            StateVariable("leaked", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "attacker-joins",
                Expression.constant(True),
                (
                    Assignment(
                        "holders",
                        Expression.operator(
                            ExpressionKind.UNION,
                            Expression.variable("holders"),
                            Expression.constant("mallory"),
                        ),
                    ),
                ),
            ),
            TransitionRule(
                "release-to-attacker",
                Expression.operator(
                    ExpressionKind.IN,
                    Expression.constant("mallory"),
                    Expression.variable("holders"),
                ),
                (Assignment("leaked", Expression.constant(True)),),
            ),
        ),
        (
            SafetyInvariant(
                "no-leak",
                Expression.operator(ExpressionKind.NOT, Expression.variable("leaked")),
            ),
        ),
        4,
        (),
    )


def test_every_set_model_declares_a_universe() -> None:
    for _name, ir in _set_models():
        set_variables = [variable for variable in ir.variables if variable.sort == Sort.SET]
        assert set_variables
        for variable in set_variables:
            assert variable.universe, variable.name


def test_expansion_removes_every_set_variable() -> None:
    for name, ir in _set_models():
        expanded = expand_sets(ir)
        assert not [variable for variable in expanded.variables if variable.sort == Sort.SET], name
        assert expanded.variables != ir.variables
        assert len(expanded.transitions) == len(ir.transitions)
        assert len(expanded.invariants) == len(ir.invariants)


def test_expansion_leaves_the_input_untouched_and_changes_the_identity() -> None:
    for _name, ir in _set_models():
        before = ir.to_dict()
        expanded = expand_sets(ir)
        assert ir.to_dict() == before
        assert expanded.id == f"{ir.id}:set-expanded"
        assert expanded.fingerprint != ir.fingerprint


def test_expansion_preserves_the_reachable_verdict_of_every_set_model() -> None:
    for name, ir in _set_models():
        original = reachable_states(ir)
        expanded = expand_sets(ir)
        assert len(expanded.variables) >= len(original[0]) if original else True
        for invariant in ir.invariants:
            hold_original = all(evaluate(invariant.expression, state) is True for state in original)
            mirrored = next(item for item in expanded.invariants if item.id == invariant.id)
            expanded_states = reachable_states(expanded)
            hold_expanded = all(evaluate(mirrored.expression, state) is True for state in expanded_states)
            assert hold_original == hold_expanded, f"{name}:{invariant.id}"


def test_element_outside_the_universe_is_false_not_unknown() -> None:
    ir = _counter_ir(("alice",))
    expanded = expand_sets(ir)
    members = {variable.name for variable in expanded.variables}
    assert member_variable("holders", "alice") in members
    # 'mallory' is outside the declared universe, so its membership is the constant False.
    assert member_variable("holders", "mallory") not in members


def test_a_set_variable_without_a_universe_is_refused() -> None:
    ir = VerificationIR(
        "undeclared-universe",
        (StateVariable("holders", Sort.SET, frozenset({"alice"})),),
        (),
        (SafetyInvariant("trivial", Expression.constant(True)),),
        1,
        (),
    )
    with pytest.raises(SetExpansionError, match="declare no universe"):
        expand_sets(ir)


def test_an_out_of_fragment_operator_is_refused_rather_than_weakened() -> None:
    ir = VerificationIR(
        "intersect-fixture",
        (
            StateVariable("a", Sort.SET, frozenset(), universe=("alice",)),
            StateVariable("b", Sort.SET, frozenset(), universe=("alice",)),
        ),
        (),
        (
            SafetyInvariant(
                "intersection-empty",
                Expression.operator(
                    ExpressionKind.IN,
                    Expression.constant("alice"),
                    Expression.operator(
                        ExpressionKind.INTERSECT,
                        Expression.variable("a"),
                        Expression.variable("b"),
                    ),
                ),
            ),
        ),
        1,
        (),
    )
    with pytest.raises(SetExpansionError, match="must be a set variable"):
        expand_sets(ir)


def test_the_backends_return_a_verdict_for_the_set_models() -> None:
    for name, ir in _set_models():
        bounded = verify_with_z3(ir)
        unbounded = verify_with_horn(ir)
        assert bounded.error is None, f"{name}: {bounded.error}"
        assert unbounded.error is None, f"{name}: {unbounded.error}"
        assert bounded.verdict.value == "bounded_safe", name
        assert unbounded.verdict.value == "safe", name


def test_the_reported_hash_is_the_original_ir_not_the_expansion() -> None:
    for _name, ir in _set_models():
        for result in (verify_with_z3(ir), verify_with_horn(ir)):
            assert result.ir_hash == ir.fingerprint
            assert any("expanded" in assumption for assumption in result.assumptions)


def test_an_unsafe_set_model_is_refuted_by_name() -> None:
    ir = _counter_ir(("alice", "mallory"))
    assert verify_with_z3(ir).verdict.value == "unsafe"
    unbounded = verify_with_horn(ir)
    assert unbounded.verdict.value == "unsafe"
    assert {entry["invariant"] for entry in unbounded.counterexample} == {"no-leak"}


def test_every_set_model_verdict_is_falsifiable_or_declared_vacuous() -> None:
    """The gate that stops a vacuous proof being published as a hold."""
    for name, ir in _set_models():
        classified = {row.invariant_id: row for row in classify_ir(ir)}
        assert set(classified) == set(EXPECTED_EXERCISE[name]), name
        for invariant_id, expected in EXPECTED_EXERCISE[name].items():
            row = classified[invariant_id]
            assert row.exercise_class == expected, f"{name}:{invariant_id}"
            if expected == CLASS_CHECKED:
                assert row.falsifiers, f"{name}:{invariant_id} is cited as checked with no falsifier"
