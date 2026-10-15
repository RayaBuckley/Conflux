"""The validator rejects a definite sort mismatch between an assignment value and its target.

F4 from ``writing/audits/2026-10-15-ir-modelling``: ``next(count: integer) = flag: boolean`` was
accepted, and the three backends then disagreed on that one IR - z3 answered ``bounded_safe``
through ``If(flag, 1, 0)``, nuXmv emitted an SMV syntax error, and the interpreter raised.

The check is deliberately a single-sorted inference, not a type system: it returns ``None``
when it cannot name a sort and never rejects on ``None``. The last test pins the property that
matters - no IR this repository already builds is rejected.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from conflux.verification import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)

pytestmark = pytest.mark.security

ROOT = Path(__file__).resolve().parents[1]


def _f4_ir() -> VerificationIR:
    """The F4 IR: an integer counter assigned a Boolean flag."""
    return VerificationIR(
        "type-gap",
        (
            StateVariable("flag", Sort.BOOLEAN, True),
            StateVariable("count", Sort.INTEGER, 0, 0, 3),
        ),
        (
            TransitionRule(
                "type-gap",
                Expression.constant(True),
                (Assignment("count", Expression.variable("flag")),),
            ),
        ),
        (SafetyInvariant("flag-holds", Expression.variable("flag"), "flag stays true"),),
        2,
    )


def test_boolean_assigned_to_integer_is_rejected() -> None:
    with pytest.raises(ValueError, match="assigns a boolean expression to integer variable count"):
        _f4_ir()


def test_integer_assigned_to_boolean_is_rejected() -> None:
    with pytest.raises(ValueError, match="assigns a integer expression to boolean variable flag"):
        VerificationIR(
            "reverse-gap",
            (StateVariable("flag", Sort.BOOLEAN, True),),
            (TransitionRule("t", Expression.constant(True), (Assignment("flag", Expression.constant(3)),)),),
            (SafetyInvariant("i", Expression.variable("flag"), "d"),),
            2,
        )


def test_non_boolean_guard_is_rejected() -> None:
    with pytest.raises(ValueError, match="transition guard for g is not boolean"):
        VerificationIR(
            "guard-gap",
            (StateVariable("n", Sort.INTEGER, 0, 0, 3),),
            (TransitionRule("g", Expression.constant(2), (Assignment("n", Expression.constant(1)),)),),
            (SafetyInvariant("i", Expression.constant(True), "d"),),
            2,
        )


def test_well_typed_ir_is_accepted() -> None:
    ir = VerificationIR(
        "well-typed",
        (
            StateVariable("flag", Sort.BOOLEAN, True),
            StateVariable("count", Sort.INTEGER, 0, 0, 3),
        ),
        (
            TransitionRule(
                "increment",
                Expression.variable("flag"),
                (Assignment("count", Expression.operator(ExpressionKind.ADD, Expression.variable("count"), Expression.constant(1))),),
            ),
        ),
        (SafetyInvariant("count-bounded", Expression.operator(ExpressionKind.LESS_EQUAL, Expression.variable("count"), Expression.constant(3)), "d"),),
        2,
    )
    assert ir.id == "well-typed"


def test_a_sort_the_inference_cannot_name_is_not_rejected() -> None:
    """``None`` means 'do not reject', so an opaque constant does not fail the gate."""
    ir = VerificationIR(
        "opaque",
        (StateVariable("flag", Sort.BOOLEAN, True),),
        (TransitionRule("t", Expression.constant(True), (Assignment("flag", Expression.constant("opaque")),)),),
        (SafetyInvariant("i", Expression.variable("flag"), "d"),),
        2,
    )
    assert ir.id == "opaque"


def _load_generator() -> Any:
    """Load the IC3 generator module without importing the scripts directory as a package."""
    path = ROOT / "scripts" / "generate_ic3_unbounded_evidence.py"
    spec = importlib.util.spec_from_file_location("generate_ic3_unbounded_evidence_sortgate", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.reproducibility
@pytest.mark.slow
def test_every_ir_the_generator_builds_still_constructs() -> None:
    """The sort gate must not reject any IR in the retained population (689 rows)."""
    generator = _load_generator()
    rows = 0
    for factory in generator.FAMILIES.values():
        for _row_id, _family, _source, ir, _notes in factory():
            rows += 1
            assert ir.id
    assert rows == 689
