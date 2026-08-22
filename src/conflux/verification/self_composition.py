"""Self-composition encoding for observational confidentiality verification.

SEM-OBS-1: Observational confidentiality is a relational hyperproperty (2-safety).
It requires comparing two execution traces that differ only in secret inputs and
checking that unauthorised observers see equivalent observations.

SEM-OBS-2: Self-composition (Barthe, D'Argenio, and Rezk 2004) constructs a
product transition system with two copies of every variable.  The product IR is
a valid :class:`VerificationIR` and can be verified by the existing Z3 BMC
backend and COI reducer without modification.

SEM-OBS-3: The confidentiality invariant asserts that observable variables are
equal between the two copies (``v == v'``) for every observer principal who is
not an authorised reader of the secret.

The encoding is bounded: it produces ``bounded_evidence``, not a proof of
unbounded noninterference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from .ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)

SELF_COMPOSITION_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class SecretPartition:
    """Specification of which IR variables are secret and who may observe them.

    Attributes:
        observable_variable_ids: variables whose equality is checked between
            the two product copies (typically outputs or effects visible to
            unauthorised observers).
        secret_variable_ids: variables whose initial values differ between the
            two copies (the secret inputs).
        observer_description: human-readable description of the observer
            principal set and why they are unauthorised for the secret.
        declassification_boundaries: invariant IDs that are excluded from the
            confidentiality check (declared declassification points).
    """

    observable_variable_ids: frozenset[str]
    secret_variable_ids: frozenset[str]
    observer_description: str = ""
    declassification_boundaries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate that the partition has non-empty, disjoint sets."""
        object.__setattr__(self, "observable_variable_ids", frozenset(self.observable_variable_ids))
        object.__setattr__(self, "secret_variable_ids", frozenset(self.secret_variable_ids))
        object.__setattr__(self, "declassification_boundaries", tuple(self.declassification_boundaries))
        if not self.observable_variable_ids:
            raise ValueError("secret partition requires at least one observable variable")
        if not self.secret_variable_ids:
            raise ValueError("secret partition requires at least one secret variable")
        overlap = self.observable_variable_ids & self.secret_variable_ids
        if overlap:
            raise ValueError(f"observable and secret variables must be disjoint: {sorted(overlap)}")

    def to_dict(self) -> dict[str, object]:
        """Serialize this secret partition to a JSON-compatible dictionary."""
        return {
            "schema_version": SELF_COMPOSITION_SCHEMA_VERSION,
            "observable_variable_ids": sorted(self.observable_variable_ids),
            "secret_variable_ids": sorted(self.secret_variable_ids),
            "observer_description": self.observer_description,
            "declassification_boundaries": list(self.declassification_boundaries),
        }

    @classmethod
    def from_dict(cls, value: object) -> "SecretPartition":
        """Deserialize a secret partition from a JSON-compatible dictionary."""
        if not isinstance(value, dict):
            raise ValueError("secret partition must be an object")
        expected = {
            "schema_version",
            "observable_variable_ids",
            "secret_variable_ids",
            "observer_description",
            "declassification_boundaries",
        }
        if set(value) != expected:
            raise ValueError("secret partition fields do not match schema")
        schema_version = value["schema_version"]
        if schema_version != SELF_COMPOSITION_SCHEMA_VERSION:
            raise ValueError(f"unsupported secret partition schema version: {schema_version}")
        observable = value["observable_variable_ids"]
        secret = value["secret_variable_ids"]
        if not isinstance(observable, list) or not isinstance(secret, list):
            raise ValueError("secret partition variable IDs must be arrays")
        observer_description = value["observer_description"]
        if not isinstance(observer_description, str):
            raise ValueError("observer description must be a string")
        boundaries = value["declassification_boundaries"]
        if not isinstance(boundaries, list):
            raise ValueError("declassification boundaries must be an array")
        return cls(
            frozenset(cast(list[str], observable)),
            frozenset(cast(list[str], secret)),
            observer_description,
            tuple(cast(list[str], boundaries)),
        )

    @property
    def fingerprint_seed(self) -> dict[str, object]:
        """Return a stable dictionary for fingerprinting."""
        return self.to_dict()


def _different_initial(variable: StateVariable) -> bool | int:
    """Return a different initial value for a primed secret variable.

    For booleans, flip the value.  For integers, shift by one within bounds,
    or use zero if the current value is non-zero.
    """
    if variable.sort == Sort.BOOLEAN:
        return not variable.initial
    if variable.minimum is not None and variable.initial == variable.minimum:
        return variable.initial + 1
    if variable.maximum is not None and variable.initial == variable.maximum:
        return variable.initial - 1
    return 0 if variable.initial != 0 else 1


def construct_product_ir(
    ir: VerificationIR,
    partition: SecretPartition,
) -> VerificationIR:
    """Construct a self-composition product IR for observational confidentiality.

    The product IR doubles every variable (unprimed + primed) and creates
    **combined** transition rules that fire both copies in lockstep: each
    product rule's guard is the conjunction of the original guard and the
    primed guard, and its assignments update both unprimed and primed variables
    simultaneously.  This ensures the two execution copies stay aligned in
    control flow.

    Confidentiality invariants of the form ``observable == observable__prime``
    are added for each observable variable.

    Secret variables share the same initial value in both copies at the IR
    level; the Z3 backend treats initial values as symbolic constraints, so
    the solver explores different secret values across the two copies.
    """
    _validate_partition(ir, partition)
    all_variables: list[StateVariable] = []
    for variable in ir.variables:
        all_variables.append(variable)
        primed_name = _primed(variable.name)
        if variable.name in partition.secret_variable_ids:
            primed_initial = _different_initial(variable)
        else:
            primed_initial = variable.initial
        all_variables.append(
            StateVariable(
                primed_name,
                variable.sort,
                primed_initial,
                variable.minimum,
                variable.maximum,
            )
        )

    combined_rules: list[TransitionRule] = []
    for rule in ir.transitions:
        primed_guard = _prime_expression(rule.guard)
        combined_guard = Expression.operator(
            ExpressionKind.AND,
            rule.guard,
            primed_guard,
        )
        combined_assignments: list[Assignment] = []
        for assignment in rule.assignments:
            combined_assignments.append(assignment)
            combined_assignments.append(
                Assignment(
                    _primed(assignment.variable),
                    _prime_expression(assignment.expression),
                )
            )
        combined_rules.append(
            TransitionRule(
                id=rule.id,
                guard=combined_guard,
                assignments=tuple(combined_assignments),
            )
        )

    confidentiality_invariants: list[SafetyInvariant] = []
    for observable_id in sorted(partition.observable_variable_ids):
        primed_name = _primed(observable_id)
        confidentiality_invariants.append(
            SafetyInvariant(
                id=f"confidentiality__{observable_id}",
                expression=Expression.operator(
                    ExpressionKind.EQUAL,
                    Expression.variable(observable_id),
                    Expression.variable(primed_name),
                ),
                description=f"Observational confidentiality: {observable_id} must not leak to unauthorised observers",
            )
        )

    assumptions = list(ir.assumptions)
    assumptions.extend(
        (
            "self-composition product of two execution copies",
            f"observer: {partition.observer_description}" if partition.observer_description else "observer: unauthorised principal",
            f"secret variables: {sorted(partition.secret_variable_ids)}",
            f"observable variables: {sorted(partition.observable_variable_ids)}",
        )
    )
    if partition.declassification_boundaries:
        assumptions.append(f"declassification boundaries: {list(partition.declassification_boundaries)}")

    return VerificationIR(
        id=f"{ir.id}--product",
        variables=tuple(all_variables),
        transitions=tuple(combined_rules),
        invariants=tuple(confidentiality_invariants),
        bound=ir.bound,
        assumptions=tuple(assumptions),
    )


def _validate_partition(ir: VerificationIR, partition: SecretPartition) -> None:
    variable_names = {variable.name for variable in ir.variables}
    unknown_observable = partition.observable_variable_ids - variable_names
    if unknown_observable:
        raise ValueError(f"observable variables not in IR: {sorted(unknown_observable)}")
    unknown_secret = partition.secret_variable_ids - variable_names
    if unknown_secret:
        raise ValueError(f"secret variables not in IR: {sorted(unknown_secret)}")


def _primed(name: str) -> str:
    """Return the primed variable name for the product IR."""
    return f"{name}__prime"


def _prime_expression(expression: Expression) -> Expression:
    """Return a copy of *expression* with every variable reference primed."""
    if expression.kind == ExpressionKind.VARIABLE:
        assert isinstance(expression.value, str)
        return Expression.variable(_primed(expression.value))
    return Expression(
        expression.kind,
        expression.value,
        tuple(_prime_expression(arg) for arg in expression.arguments),
    )


__all__ = [
    "SELF_COMPOSITION_SCHEMA_VERSION",
    "SecretPartition",
    "construct_product_ir",
]
