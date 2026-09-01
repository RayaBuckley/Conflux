"""Serializable transition-system IR with no executable callbacks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

from conflux.domain import fingerprint

IR_SCHEMA_VERSION = "1"


class Sort(StrEnum):
    """Value sort supported by the verification IR."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    SET = "set"


class ExpressionKind(StrEnum):
    """Enumeration of supported IR expression node types."""

    CONSTANT = "constant"
    VARIABLE = "variable"
    NOT = "not"
    AND = "and"
    OR = "or"
    EQUAL = "equal"
    LESS_EQUAL = "less_equal"
    ADD = "add"
    IN = "in"
    SUBSET = "subset"
    UNION = "union"
    INTERSECT = "intersect"
    IMPLIES = "implies"
    GREATER_EQUAL = "greater_equal"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    DIFFERENCE = "difference"


Scalar: TypeAlias = bool | int
SetValue: TypeAlias = frozenset[str]
IRValue: TypeAlias = Scalar | SetValue | str


@dataclass(frozen=True, slots=True)
class Expression:
    """Immutable IR expression node of a given kind, value, and arguments."""

    kind: ExpressionKind
    value: Scalar | str | None = None
    arguments: tuple[Expression, ...] = ()

    def __post_init__(self) -> None:
        """Validate arity and value constraints for this expression node."""
        object.__setattr__(self, "arguments", tuple(self.arguments))
        arity = {
            ExpressionKind.CONSTANT: 0,
            ExpressionKind.VARIABLE: 0,
            ExpressionKind.NOT: 1,
            ExpressionKind.AND: -1,
            ExpressionKind.OR: -1,
            ExpressionKind.EQUAL: 2,
            ExpressionKind.LESS_EQUAL: 2,
            ExpressionKind.ADD: 2,
            ExpressionKind.IN: 2,
            ExpressionKind.SUBSET: 2,
            ExpressionKind.UNION: -1,
            ExpressionKind.INTERSECT: -1,
            ExpressionKind.IMPLIES: 2,
            ExpressionKind.GREATER_EQUAL: 2,
            ExpressionKind.GREATER_THAN: 2,
            ExpressionKind.LESS_THAN: 2,
            ExpressionKind.DIFFERENCE: 2,
        }[self.kind]
        if arity >= 0 and len(self.arguments) != arity:
            raise ValueError(f"{self.kind.value} expression requires {arity} arguments")
        if self.kind in {ExpressionKind.AND, ExpressionKind.OR} and not self.arguments:
            raise ValueError(f"{self.kind.value} expression requires arguments")
        if self.kind in {ExpressionKind.UNION, ExpressionKind.INTERSECT} and len(self.arguments) < 2:
            raise ValueError(f"{self.kind.value} expression requires at least 2 arguments")
        if self.kind == ExpressionKind.CONSTANT and not isinstance(self.value, (bool, int, str)):
            raise ValueError("constant expression requires a Boolean, integer, or string")
        if self.kind == ExpressionKind.CONSTANT and isinstance(self.value, str) and not self.value:
            raise ValueError("constant string expression requires a non-empty value")
        if self.kind == ExpressionKind.VARIABLE and (not isinstance(self.value, str) or not self.value):
            raise ValueError("variable expression requires a name")
        if self.kind not in {ExpressionKind.CONSTANT, ExpressionKind.VARIABLE} and self.value is not None:
            raise ValueError("operator expressions cannot contain a direct value")

    @classmethod
    def constant(cls, value: Scalar | str) -> Expression:
        """Create a constant expression from a Boolean, integer, or string value."""
        return cls(ExpressionKind.CONSTANT, value)

    @classmethod
    def variable(cls, name: str) -> Expression:
        """Create a variable reference expression from a name."""
        return cls(ExpressionKind.VARIABLE, name)

    @classmethod
    def operator(
        cls,
        kind: ExpressionKind,
        *arguments: Expression,
    ) -> Expression:
        """Create an operator expression with the given kind and arguments."""
        return cls(kind, arguments=arguments)

    def to_dict(self) -> dict[str, object]:
        """Serialize this expression to a JSON-compatible dictionary."""
        return {
            "kind": self.kind.value,
            "value": self.value,
            "arguments": [argument.to_dict() for argument in self.arguments],
        }

    @classmethod
    def from_dict(cls, value: object) -> Expression:
        """Deserialize an expression from a JSON-compatible dictionary."""
        if not isinstance(value, Mapping) or set(value) != {"kind", "value", "arguments"}:
            raise ValueError("malformed IR expression")
        try:
            kind = ExpressionKind(value["kind"])
        except (TypeError, ValueError) as error:
            raise ValueError("unsupported IR expression kind") from error
        arguments = value["arguments"]
        if not isinstance(arguments, list):
            raise ValueError("IR expression arguments must be an array")
        direct = value["value"]
        if direct is not None and not isinstance(direct, (bool, int, str)):
            raise ValueError("unsupported IR expression value")
        return cls(
            kind,
            direct,
            tuple(cls.from_dict(argument) for argument in arguments),
        )


@dataclass(frozen=True, slots=True)
class StateVariable:
    """A named state variable with sort, initial value, and optional bounds."""

    name: str
    sort: Sort
    initial: IRValue
    minimum: int | None = None
    maximum: int | None = None

    def __post_init__(self) -> None:
        """Validate the variable name, sort, initial value, and domain bounds."""
        if not self.name:
            raise ValueError("state variable name must be non-empty")
        if self.sort == Sort.BOOLEAN and not isinstance(self.initial, bool):
            raise ValueError("Boolean state variable requires a Boolean initial value")
        if self.sort == Sort.INTEGER and (not isinstance(self.initial, int) or isinstance(self.initial, bool)):
            raise ValueError("integer state variable requires an integer initial value")
        if self.sort == Sort.SET:
            if not isinstance(self.initial, (set, frozenset)):
                raise ValueError("set state variable requires a set or frozenset initial value")
            object.__setattr__(self, "initial", frozenset(self.initial))
        if self.sort == Sort.BOOLEAN and (self.minimum is not None or self.maximum is not None):
            raise ValueError("Boolean state variables cannot have numeric bounds")
        if self.sort == Sort.SET and (self.minimum is not None or self.maximum is not None):
            raise ValueError("set state variables cannot have numeric bounds")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("state variable minimum exceeds maximum")
        if self.sort == Sort.INTEGER and (
            (
                self.minimum is not None
                and isinstance(self.initial, int)
                and not isinstance(self.initial, bool)
                and self.initial < self.minimum
            )
            or (
                self.maximum is not None
                and isinstance(self.initial, int)
                and not isinstance(self.initial, bool)
                and self.initial > self.maximum
            )
        ):
            raise ValueError("integer initial value is outside its domain")

    def to_dict(self) -> dict[str, object]:
        """Serialize this state variable to a JSON-compatible dictionary."""
        if self.sort == Sort.SET and isinstance(self.initial, frozenset):
            initial_value: object = sorted(self.initial)
        else:
            initial_value = self.initial
        return {
            "name": self.name,
            "sort": self.sort.value,
            "initial": initial_value,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass(frozen=True, slots=True)
class Assignment:
    """A guarded assignment of an expression to a state variable."""

    variable: str
    expression: Expression

    def to_dict(self) -> dict[str, object]:
        """Serialize this assignment to a JSON-compatible dictionary."""
        return {
            "variable": self.variable,
            "expression": self.expression.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class TransitionRule:
    """A transition rule with a guard and a set of simultaneous assignments."""

    id: str
    guard: Expression
    assignments: tuple[Assignment, ...]

    def __post_init__(self) -> None:
        """Validate that the rule has a non-empty id and unique assignment targets."""
        if not self.id:
            raise ValueError("transition rule id must be non-empty")
        object.__setattr__(self, "assignments", tuple(self.assignments))
        names = [assignment.variable for assignment in self.assignments]
        if len(names) != len(set(names)):
            raise ValueError("transition assignments must be unique")

    def to_dict(self) -> dict[str, object]:
        """Serialize this transition rule to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "guard": self.guard.to_dict(),
            "assignments": [assignment.to_dict() for assignment in self.assignments],
        }


@dataclass(frozen=True, slots=True)
class SafetyInvariant:
    """A named safety property expressed as an invariant expression."""

    id: str
    expression: Expression
    description: str = ""

    def __post_init__(self) -> None:
        """Validate that the invariant has a non-empty id."""
        if not self.id:
            raise ValueError("safety invariant id must be non-empty")

    def to_dict(self) -> dict[str, object]:
        """Serialize this safety invariant to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "expression": self.expression.to_dict(),
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class VerificationIR:
    """A complete serializable transition-system IR for bounded verification."""

    id: str
    variables: tuple[StateVariable, ...]
    transitions: tuple[TransitionRule, ...]
    invariants: tuple[SafetyInvariant, ...]
    bound: int
    assumptions: tuple[str, ...] = ()
    schema_version: str = IR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate all internal consistency and referential integrity constraints."""
        if not self.id or self.bound < 1:
            raise ValueError("verification IR requires an id and positive bound")
        if self.schema_version != IR_SCHEMA_VERSION:
            raise ValueError(f"unsupported verification IR version: {self.schema_version}")
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "transitions", tuple(self.transitions))
        object.__setattr__(self, "invariants", tuple(self.invariants))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        variable_names = {variable.name for variable in self.variables}
        if len(variable_names) != len(self.variables) or not variable_names:
            raise ValueError("verification variables must be non-empty and unique")
        if len({rule.id for rule in self.transitions}) != len(self.transitions):
            raise ValueError("transition rule ids must be unique")
        if len({item.id for item in self.invariants}) != len(self.invariants):
            raise ValueError("invariant ids must be unique")
        for rule in self.transitions:
            unknown = {item.variable for item in rule.assignments} - variable_names
            if unknown:
                raise ValueError(f"transition assigns unknown variables: {sorted(unknown)}")
            _validate_expression(rule.guard, variable_names)
            for assignment in rule.assignments:
                _validate_expression(assignment.expression, variable_names)
        for invariant in self.invariants:
            _validate_expression(invariant.expression, variable_names)

    def to_dict(self) -> dict[str, object]:
        """Serialize this verification IR to a JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "bound": self.bound,
            "assumptions": list(self.assumptions),
            "variables": [variable.to_dict() for variable in sorted(self.variables, key=lambda item: item.name)],
            "transitions": [rule.to_dict() for rule in sorted(self.transitions, key=lambda item: item.id)],
            "invariants": [item.to_dict() for item in sorted(self.invariants, key=lambda item: item.id)],
        }

    @property
    def fingerprint(self) -> str:
        """Return a content-based fingerprint of this verification IR."""
        return fingerprint(self.to_dict())

    @classmethod
    def from_dict(cls, value: object) -> VerificationIR:
        """Deserialize a verification IR from a JSON-compatible dictionary."""
        if not isinstance(value, Mapping):
            raise ValueError("verification IR must be an object")
        expected = {
            "schema_version",
            "id",
            "bound",
            "assumptions",
            "variables",
            "transitions",
            "invariants",
        }
        if set(value) != expected:
            raise ValueError("verification IR fields do not match schema")
        variables_value = value["variables"]
        transitions_value = value["transitions"]
        invariants_value = value["invariants"]
        assumptions_value = value["assumptions"]
        if not all(
            isinstance(item, list)
            for item in (
                variables_value,
                transitions_value,
                invariants_value,
                assumptions_value,
            )
        ):
            raise ValueError("verification IR collections must be arrays")
        variables = tuple(_parse_variable(item) for item in variables_value)
        transitions = tuple(_parse_transition(item) for item in transitions_value)
        invariants = tuple(_parse_invariant(item) for item in invariants_value)
        if not all(isinstance(item, str) for item in assumptions_value):
            raise ValueError("verification assumptions must be strings")
        identifier = value["id"]
        bound = value["bound"]
        version = value["schema_version"]
        if not isinstance(identifier, str) or not isinstance(bound, int) or not isinstance(version, str):
            raise ValueError("verification IR scalar fields are malformed")
        return cls(
            identifier,
            variables,
            transitions,
            invariants,
            bound,
            tuple(assumptions_value),
            version,
        )


def _validate_expression(expression: Expression, variables: set[str]) -> None:
    if expression.kind == ExpressionKind.VARIABLE and expression.value not in variables:
        raise ValueError(f"expression references unknown variable: {expression.value}")
    for argument in expression.arguments:
        _validate_expression(argument, variables)


def _parse_variable(value: object) -> StateVariable:
    if not isinstance(value, Mapping) or set(value) != {
        "name",
        "sort",
        "initial",
        "minimum",
        "maximum",
    }:
        raise ValueError("malformed state variable")
    sort = Sort(value["sort"])
    initial: Scalar | SetValue
    if sort == Sort.SET:
        initial_list = value["initial"]
        if not isinstance(initial_list, list):
            raise ValueError("set state variable initial must be an array")
        initial = frozenset(str(item) for item in initial_list)
    else:
        initial = value["initial"]
    return StateVariable(
        str(value["name"]),
        sort,
        initial,
        value["minimum"] if isinstance(value["minimum"], int) else None,
        value["maximum"] if isinstance(value["maximum"], int) else None,
    )


def _parse_assignment(value: object) -> Assignment:
    if not isinstance(value, Mapping) or set(value) != {"variable", "expression"}:
        raise ValueError("malformed transition assignment")
    variable = value["variable"]
    if not isinstance(variable, str):
        raise ValueError("assignment variable must be a string")
    return Assignment(variable, Expression.from_dict(value["expression"]))


def _parse_transition(value: object) -> TransitionRule:
    if not isinstance(value, Mapping) or set(value) != {"id", "guard", "assignments"}:
        raise ValueError("malformed transition rule")
    assignments = value["assignments"]
    if not isinstance(value["id"], str) or not isinstance(assignments, list):
        raise ValueError("malformed transition rule fields")
    return TransitionRule(
        value["id"],
        Expression.from_dict(value["guard"]),
        tuple(_parse_assignment(item) for item in assignments),
    )


def _parse_invariant(value: object) -> SafetyInvariant:
    if not isinstance(value, Mapping) or set(value) != {
        "id",
        "expression",
        "description",
    }:
        raise ValueError("malformed safety invariant")
    if not isinstance(value["id"], str) or not isinstance(value["description"], str):
        raise ValueError("malformed safety invariant fields")
    return SafetyInvariant(
        value["id"],
        Expression.from_dict(value["expression"]),
        value["description"],
    )


__all__ = [
    "IR_SCHEMA_VERSION",
    "Assignment",
    "Expression",
    "ExpressionKind",
    "IRValue",
    "SafetyInvariant",
    "Scalar",
    "SetValue",
    "Sort",
    "StateVariable",
    "TransitionRule",
    "VerificationIR",
]
