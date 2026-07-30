"""Pure interpreter and differential conformance for the verification IR."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint

from .ir import (
    Expression,
    ExpressionKind,
    Scalar,
    StateVariable,
    VerificationIR,
)


def evaluate(expression: Expression, state: dict[str, Scalar]) -> Scalar:
    if expression.kind == ExpressionKind.CONSTANT:
        assert isinstance(expression.value, (bool, int))
        return expression.value
    if expression.kind == ExpressionKind.VARIABLE:
        assert isinstance(expression.value, str)
        return state[expression.value]
    values = tuple(evaluate(argument, state) for argument in expression.arguments)
    if expression.kind == ExpressionKind.NOT:
        return not _bool(values[0])
    if expression.kind == ExpressionKind.AND:
        return all(_bool(value) for value in values)
    if expression.kind == ExpressionKind.OR:
        return any(_bool(value) for value in values)
    if expression.kind == ExpressionKind.EQUAL:
        return values[0] == values[1]
    if expression.kind == ExpressionKind.LESS_EQUAL:
        return _int(values[0]) <= _int(values[1])
    return _int(values[0]) + _int(values[1])


def initial_state(ir: VerificationIR) -> dict[str, Scalar]:
    return {variable.name: variable.initial for variable in ir.variables}


def successors(
    ir: VerificationIR,
    state: dict[str, Scalar],
) -> tuple[tuple[str, dict[str, Scalar]], ...]:
    result: list[tuple[str, dict[str, Scalar]]] = []
    variables = {variable.name: variable for variable in ir.variables}
    for rule in sorted(ir.transitions, key=lambda item: item.id):
        if not _bool(evaluate(rule.guard, state)):
            continue
        target = dict(state)
        for assignment in rule.assignments:
            target[assignment.variable] = evaluate(assignment.expression, state)
        if _within_domains(target, variables):
            result.append((rule.id, target))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class RuntimeTransitionRecord:
    source: dict[str, Scalar]
    rule_id: str
    target: dict[str, Scalar]

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "rule_id": self.rule_id,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class DifferentialConformanceResult:
    conforms: bool
    ir_hash: str
    corpus_hash: str
    mismatches: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "conforms": self.conforms,
            "ir_hash": self.ir_hash,
            "corpus_hash": self.corpus_hash,
            "mismatches": list(self.mismatches),
        }


def differential_conformance(
    ir: VerificationIR,
    records: tuple[RuntimeTransitionRecord, ...],
) -> DifferentialConformanceResult:
    mismatches: list[str] = []
    for index, record in enumerate(records):
        expected = {
            (rule_id, fingerprint(target))
            for rule_id, target in successors(ir, record.source)
        }
        observed = (record.rule_id, fingerprint(record.target))
        if observed not in expected:
            mismatches.append(f"record[{index}] is not an IR transition")
    return DifferentialConformanceResult(
        not mismatches,
        ir.fingerprint,
        fingerprint([record.to_dict() for record in records]),
        tuple(mismatches),
    )


def _within_domains(
    state: dict[str, Scalar],
    variables: dict[str, StateVariable],
) -> bool:
    for name, value in state.items():
        variable = variables[name]
        if variable.minimum is not None and _int(value) < variable.minimum:
            return False
        if variable.maximum is not None and _int(value) > variable.maximum:
            return False
    return True


def _bool(value: Scalar) -> bool:
    if not isinstance(value, bool):
        raise TypeError("IR expression expected a Boolean")
    return value


def _int(value: Scalar) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("IR expression expected an integer")
    return value


__all__ = [
    "DifferentialConformanceResult",
    "RuntimeTransitionRecord",
    "differential_conformance",
    "evaluate",
    "initial_state",
    "successors",
]
