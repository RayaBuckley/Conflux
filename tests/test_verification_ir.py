"""Serializable verification IR, differential conformance, and backends."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, cast

import pytest
from jsonschema import Draft202012Validator

from conflux.verification import (
    Assignment,
    Expression,
    ExpressionKind,
    FormalVerdict,
    NuXmvBackend,
    NuXmvOutcome,
    RuntimeTransitionRecord,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
    differential_conformance,
    initial_state,
    successors,
    verify_with_z3,
)

ROOT = Path(__file__).resolve().parents[1]


def security_ir(*, authorised: bool = True) -> VerificationIR:
    authorised_expression = Expression.variable("authorised")
    executed_expression = Expression.variable("executed_unauthorised")
    return VerificationIR(
        "security-monitor",
        (
            StateVariable("authorised", Sort.BOOLEAN, authorised),
            StateVariable("executed_unauthorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "execute",
                Expression.constant(True),
                (
                    Assignment(
                        "executed_unauthorised",
                        Expression.operator(
                            ExpressionKind.NOT,
                            authorised_expression,
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-unauthorised-execution",
                Expression.operator(
                    ExpressionKind.NOT,
                    executed_expression,
                ),
            ),
        ),
        3,
        ("the action authorisation bit is an exact abstraction",),
    )


def test_ir_round_trip_schema_and_interpreter_are_deterministic() -> None:
    ir = security_ir()
    payload = ir.to_dict()
    parsed = VerificationIR.from_dict(payload)
    assert parsed.fingerprint == ir.fingerprint
    schema = cast(
        dict[str, object],
        json.loads(
            (ROOT / "schemas" / "verification-ir.schema.json").read_text(
                encoding="utf-8"
            )
        ),
    )
    Draft202012Validator(schema).validate(payload)
    state = initial_state(ir)
    transitions = successors(ir, state)
    assert transitions == successors(ir, state)
    assert transitions[0][0] == "execute"
    assert transitions[0][1]["executed_unauthorised"] is False


def test_runtime_to_ir_differential_conformance_detects_drift() -> None:
    ir = security_ir()
    source = initial_state(ir)
    target = successors(ir, source)[0][1]
    conforming = differential_conformance(
        ir,
        (RuntimeTransitionRecord(source, "execute", target),),
    )
    assert conforming.conforms
    drifted = differential_conformance(
        ir,
        (
            RuntimeTransitionRecord(
                source,
                "execute",
                {**target, "executed_unauthorised": True},
            ),
        ),
    )
    assert not drifted.conforms
    assert drifted.mismatches == ("record[0] is not an IR transition",)


def test_z3_backend_is_bounded_or_explicitly_unavailable() -> None:
    safe = verify_with_z3(security_ir())
    if importlib.util.find_spec("z3") is None:
        assert safe.verdict == FormalVerdict.UNKNOWN
        assert safe.error == "optional_dependency_unavailable:z3"
    else:
        assert safe.verdict == FormalVerdict.BOUNDED_SAFE
        unsafe = verify_with_z3(security_ir(authorised=False))
        assert unsafe.verdict == FormalVerdict.UNSAFE
        assert unsafe.counterexample
    result_schema = cast(
        dict[str, object],
        json.loads(
            (ROOT / "schemas" / "formal-verification-result.schema.json").read_text(
                encoding="utf-8"
            )
        ),
    )
    Draft202012Validator(result_schema).validate(safe.to_dict())


@dataclass
class Runner:
    outcome: NuXmvOutcome
    models: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)

    def run(
        self,
        binary: str,
        model_path: Path,
        commands: str,
    ) -> NuXmvOutcome:
        assert binary == "nuXmv"
        self.models.append(model_path.read_text(encoding="utf-8"))
        self.commands.append(commands)
        return self.outcome


def test_nuxmv_adapter_safe_unsafe_unknown_and_hashes() -> None:
    safe_runner = Runner(NuXmvOutcome(0, "-- invariant x is true\n", "", "2.1"))
    safe = NuXmvBackend(
        runner=safe_runner,
        availability=lambda _: True,
    ).verify(security_ir())
    assert safe.verdict == FormalVerdict.SAFE
    assert safe.model_hash
    assert "check_invar_ic3" in safe_runner.commands[0]
    assert "INVARSPEC" in safe_runner.models[0]

    unsafe = NuXmvBackend(
        runner=Runner(NuXmvOutcome(0, "-- invariant x is false\n", "", "2.1")),
        availability=lambda _: True,
    ).verify(security_ir(authorised=False))
    assert unsafe.verdict == FormalVerdict.UNSAFE
    assert unsafe.counterexample

    missing = NuXmvBackend(availability=lambda _: False).verify(security_ir())
    assert missing.verdict == FormalVerdict.UNKNOWN
    assert missing.error == "optional_binary_unavailable:nuXmv"

    integer = VerificationIR(
        "integer",
        (StateVariable("count", Sort.INTEGER, 0, 0, 2),),
        (),
        (
            SafetyInvariant(
                "bounded",
                Expression.operator(
                    ExpressionKind.LESS_EQUAL,
                    Expression.variable("count"),
                    Expression.constant(2),
                ),
            ),
        ),
        2,
    )
    unsupported = NuXmvBackend(availability=lambda _: True).verify(integer)
    assert unsupported.verdict == FormalVerdict.UNKNOWN
    assert "unsupported_integer_variables" in (unsupported.error or "")


@pytest.mark.parametrize(
    ("expression", "message"),
    [
        (lambda: Expression(ExpressionKind.NOT), "requires 1 arguments"),
        (lambda: Expression(ExpressionKind.AND), "requires arguments"),
        (lambda: Expression(ExpressionKind.CONSTANT, "bad"), "requires a Boolean"),
        (lambda: Expression(ExpressionKind.VARIABLE, ""), "requires a name"),
        (
            lambda: Expression(
                ExpressionKind.NOT,
                True,
                (Expression.constant(True),),
            ),
            "cannot contain a direct value",
        ),
    ],
)
def test_expression_contracts_fail_closed(
    expression: Callable[[], Expression],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        expression()


@pytest.mark.parametrize(
    ("variable", "message"),
    [
        (lambda: StateVariable("", Sort.BOOLEAN, True), "name must be non-empty"),
        (lambda: StateVariable("flag", Sort.BOOLEAN, 1), "requires a Boolean"),
        (lambda: StateVariable("count", Sort.INTEGER, True), "requires an integer"),
        (lambda: StateVariable("flag", Sort.BOOLEAN, True, 0, 1), "cannot have numeric"),
        (lambda: StateVariable("count", Sort.INTEGER, 2, 3, 1), "minimum exceeds"),
        (lambda: StateVariable("count", Sort.INTEGER, 4, 0, 3), "outside its domain"),
    ],
)
def test_state_variable_contracts_fail_closed(
    variable: Callable[[], StateVariable],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        variable()


def test_ir_rejects_duplicate_unknown_and_malformed_structures() -> None:
    flag = StateVariable("flag", Sort.BOOLEAN, False)
    with pytest.raises(ValueError, match="non-empty and unique"):
        VerificationIR("empty", (), (), (), 1)
    with pytest.raises(ValueError, match="transition rule ids must be unique"):
        rule = TransitionRule("same", Expression.constant(True), ())
        VerificationIR("duplicate", (flag,), (rule, rule), (), 1)
    with pytest.raises(ValueError, match="invariant ids must be unique"):
        invariant = SafetyInvariant("same", Expression.constant(True))
        VerificationIR("duplicate", (flag,), (), (invariant, invariant), 1)
    with pytest.raises(ValueError, match="assigns unknown variables"):
        VerificationIR(
            "unknown",
            (flag,),
            (
                TransitionRule(
                    "bad",
                    Expression.constant(True),
                    (Assignment("missing", Expression.constant(True)),),
                ),
            ),
            (),
            1,
        )
    with pytest.raises(ValueError, match="references unknown variable"):
        VerificationIR(
            "unknown",
            (flag,),
            (),
            (SafetyInvariant("bad", Expression.variable("missing")),),
            1,
        )
    for payload in (
        None,
        {},
        {
            **security_ir().to_dict(),
            "variables": "not-an-array",
        },
        {
            **security_ir().to_dict(),
            "assumptions": [1],
        },
        {
            **security_ir().to_dict(),
            "id": 1,
        },
    ):
        with pytest.raises(ValueError):
            VerificationIR.from_dict(payload)


def test_ir_nested_parsers_reject_malformed_records() -> None:
    payload = security_ir().to_dict()
    malformed_values = (
        ("variables", [None]),
        ("transitions", [None]),
        ("invariants", [None]),
        (
            "transitions",
            [{"id": "x", "guard": Expression.constant(True).to_dict(), "assignments": [None]}],
        ),
    )
    for key, value in malformed_values:
        candidate = dict(payload)
        candidate[key] = value
        with pytest.raises((ValueError, TypeError)):
            VerificationIR.from_dict(candidate)
