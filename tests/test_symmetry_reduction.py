"""Tests for symmetry reduction and read-policy projection."""

from __future__ import annotations

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
from conflux.verification.self_composition import (
    SecretPartition,
    construct_product_ir,
)
from conflux.verification.symmetry_reduction import (
    add_symmetry_breaking_constraints,
    identify_symmetry_classes,
    project_to_read_policy,
)


def test_identify_symmetry_classes() -> None:
    policies = {"alice": "read:write", "bob": "read:write", "carol": "deny"}
    classes = identify_symmetry_classes(policies)
    assert len(classes) == 2
    rw = next(c for c in classes if c.policy_signature == "read:write")
    assert rw.principal_ids == frozenset({"alice", "bob"})


def test_symmetry_breaking_adds_invariants() -> None:
    base = VerificationIR(
        id="t",
        variables=(
            StateVariable("secret", Sort.BOOLEAN, False),
            StateVariable("output", Sort.BOOLEAN, False),
            StateVariable("step", Sort.INTEGER, 0, 0, 4),
        ),
        transitions=(
            TransitionRule(
                "s",
                Expression.operator(ExpressionKind.LESS_EQUAL, Expression.variable("step"), Expression.constant(3)),
                (
                    Assignment("step", Expression.operator(ExpressionKind.ADD, Expression.variable("step"), Expression.constant(1))),
                    Assignment("output", Expression.variable("secret")),
                ),
            ),
        ),
        invariants=(SafetyInvariant("inv", Expression.operator(ExpressionKind.NOT, Expression.variable("output")), "t"),),
        bound=4,
    )
    partition = SecretPartition(frozenset({"output"}), frozenset({"secret"}))
    product = construct_product_ir(base, partition)
    reduced = add_symmetry_breaking_constraints(product, partition)
    sym_invs = [i for i in reduced.invariants if "symmetry" in i.id]
    assert len(sym_invs) > 0


def test_project_to_read_policy_returns_valid_ir() -> None:
    base = VerificationIR(
        id="t2",
        variables=(
            StateVariable("secret", Sort.BOOLEAN, False),
            StateVariable("output", Sort.BOOLEAN, False),
            StateVariable("step", Sort.INTEGER, 0, 0, 4),
        ),
        transitions=(
            TransitionRule(
                "s",
                Expression.operator(ExpressionKind.LESS_EQUAL, Expression.variable("step"), Expression.constant(3)),
                (
                    Assignment("step", Expression.operator(ExpressionKind.ADD, Expression.variable("step"), Expression.constant(1))),
                    Assignment("output", Expression.variable("secret")),
                ),
            ),
        ),
        invariants=(
            SafetyInvariant("confidentiality__output", Expression.operator(ExpressionKind.NOT, Expression.variable("output")), "t"),
        ),
        bound=4,
    )
    partition = SecretPartition(frozenset({"output"}), frozenset({"secret"}))
    product = construct_product_ir(base, partition)
    projected = project_to_read_policy(product, frozenset({"output"}))
    assert projected.variables
    assert projected.invariants
