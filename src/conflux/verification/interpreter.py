"""Pure interpreter and differential conformance for the verification IR."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint

from .ir import (
    Expression,
    ExpressionKind,
    IRValue,
    StateVariable,
    VerificationIR,
)


def evaluate(expression: Expression, state: dict[str, IRValue]) -> IRValue:
    """Evaluate an IR expression against a state mapping and return the result."""
    if expression.kind == ExpressionKind.CONSTANT:
        if not isinstance(expression.value, (bool, int, str)):
            raise TypeError(f"expected bool/int/str constant, got {type(expression.value).__name__}")
        return expression.value
    if expression.kind == ExpressionKind.VARIABLE:
        if not isinstance(expression.value, str):
            raise TypeError(f"expected str variable name, got {type(expression.value).__name__}")
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
    if expression.kind == ExpressionKind.ADD:
        return _int(values[0]) + _int(values[1])
    if expression.kind == ExpressionKind.IN:
        return _str(values[0]) in _set(values[1])
    if expression.kind == ExpressionKind.SUBSET:
        return _set(values[0]).issubset(_set(values[1]))
    if expression.kind == ExpressionKind.UNION:
        result: frozenset[str] = frozenset()
        for value in values:
            result = result | _to_set(value)
        return result
    if expression.kind == ExpressionKind.INTERSECT:
        result_inter = _to_set(values[0])
        for value in values[1:]:
            result_inter = result_inter & _to_set(value)
        return result_inter
    if expression.kind == ExpressionKind.IMPLIES:
        return (not _bool(values[0])) or _bool(values[1])
    if expression.kind == ExpressionKind.GREATER_EQUAL:
        return _int(values[0]) >= _int(values[1])
    if expression.kind == ExpressionKind.GREATER_THAN:
        return _int(values[0]) > _int(values[1])
    if expression.kind == ExpressionKind.LESS_THAN:
        return _int(values[0]) < _int(values[1])
    if expression.kind == ExpressionKind.DIFFERENCE:
        return _to_set(values[0]) - _to_set(values[1])
    raise ValueError(f"unsupported expression kind: {expression.kind}")


def initial_state(ir: VerificationIR) -> dict[str, IRValue]:
    """Return the initial state mapping for a verification IR."""
    return {variable.name: variable.initial for variable in ir.variables}


def successors(
    ir: VerificationIR,
    state: dict[str, IRValue],
) -> tuple[tuple[str, dict[str, IRValue]], ...]:
    """Return all domain-valid successor states of a state under the IR transitions."""
    result: list[tuple[str, dict[str, IRValue]]] = []
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
    """A single observed runtime transition with source, rule id, and target."""

    source: dict[str, IRValue]
    rule_id: str
    target: dict[str, IRValue]

    def to_dict(self) -> dict[str, object]:
        """Serialize this runtime transition record to a JSON-compatible dictionary."""
        return {
            "source": _serialise_state(self.source),
            "rule_id": self.rule_id,
            "target": _serialise_state(self.target),
        }


@dataclass(frozen=True, slots=True)
class DifferentialConformanceResult:
    """Result of checking runtime transitions against the IR semantics."""

    conforms: bool
    ir_hash: str
    corpus_hash: str
    mismatches: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Serialize this conformance result to a JSON-compatible dictionary."""
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
    """Check that every runtime transition record is a valid IR transition."""
    mismatches: list[str] = []
    for index, record in enumerate(records):
        expected = {(rule_id, fingerprint(_serialise_state(target))) for rule_id, target in successors(ir, record.source)}
        observed = (record.rule_id, fingerprint(_serialise_state(record.target)))
        if observed not in expected:
            mismatches.append(f"record[{index}] is not an IR transition")
    return DifferentialConformanceResult(
        not mismatches,
        ir.fingerprint,
        fingerprint([record.to_dict() for record in records]),
        tuple(mismatches),
    )


def _serialise_state(state: dict[str, IRValue]) -> dict[str, object]:
    """Convert a state mapping to a JSON-compatible dictionary."""
    result: dict[str, object] = {}
    for key, value in state.items():
        if isinstance(value, frozenset):
            result[key] = sorted(value)
        else:
            result[key] = value
    return result


def _within_domains(
    state: dict[str, IRValue],
    variables: dict[str, StateVariable],
) -> bool:
    for name, value in state.items():
        variable = variables[name]
        if variable.sort.value == "set":
            continue
        if variable.minimum is not None and _int(value) < variable.minimum:
            return False
        if variable.maximum is not None and _int(value) > variable.maximum:
            return False
    return True


def _bool(value: IRValue) -> bool:
    if not isinstance(value, bool):
        raise TypeError("IR expression expected a Boolean")
    return value


def _int(value: IRValue) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("IR expression expected an integer")
    return value


def _str(value: IRValue) -> str:
    if not isinstance(value, str):
        raise TypeError("IR expression expected a string")
    return value


def _set(value: IRValue) -> frozenset[str]:
    if not isinstance(value, frozenset):
        raise TypeError("IR expression expected a set")
    return value


def _to_set(value: IRValue) -> frozenset[str]:
    if isinstance(value, frozenset):
        return value
    if isinstance(value, str):
        return frozenset({value})
    raise TypeError("IR set operation expected a set or string")


__all__ = [
    "DifferentialConformanceResult",
    "RuntimeTransitionRecord",
    "differential_conformance",
    "evaluate",
    "initial_state",
    "successors",
]
