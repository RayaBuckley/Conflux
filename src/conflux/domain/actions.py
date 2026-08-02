"""Typed declarative model proposals; none performs a side effect."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

from .artifacts import Artifact
from .permissions import Permission, normalise_permission
from .provenance import Provenance, provenance_union
from .resources import ResourceRef
from .serialization import canonical_value, fingerprint


class ActionKind(StrEnum):
    PRIMITIVE = "primitive"
    NESTED = "nested"
    MESSAGE = "message"
    DELEGATION = "delegation"
    STOP = "stop"
    NO_OP = "no_op"


class ActionVisibility(StrEnum):
    INTERNAL = "internal"
    PARTICIPANTS = "participants"
    TRANSCRIPT = "transcript"


class ProposalMode(StrEnum):
    ALTERNATIVES = "alternatives"
    ORDERED_PLAN = "ordered_plan"


class ArgumentRole(StrEnum):
    CONTENT = "content"
    RESOURCE = "resource"
    RECIPIENT = "recipient"
    DESTINATION = "destination"
    VALUE = "value"
    CREDENTIAL_REFERENCE = "credential_reference"


AUTHORITY_BEARING_ARGUMENT_ROLES = frozenset(
    {
        ArgumentRole.RESOURCE,
        ArgumentRole.RECIPIENT,
        ArgumentRole.DESTINATION,
        ArgumentRole.CREDENTIAL_REFERENCE,
    }
)


@dataclass(frozen=True, slots=True)
class ActionArgument:
    name: str
    role: ArgumentRole
    value_fingerprint: str
    provenance: Provenance
    redacted_value: object | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("action argument name must be non-empty")
        if len(self.value_fingerprint) != 64 or any(character not in "0123456789abcdef" for character in self.value_fingerprint):
            raise ValueError("action argument fingerprint must be lowercase SHA-256")
        object.__setattr__(self, "redacted_value", canonical_value(self.redacted_value))

    @classmethod
    def bind(
        cls,
        *,
        name: str,
        role: ArgumentRole,
        value: object,
        provenance: Provenance,
        redacted_value: object | None = None,
    ) -> "ActionArgument":
        return cls(
            name,
            role,
            fingerprint(value),
            provenance,
            canonical_value(redacted_value),
        )

    @property
    def authority_bearing(self) -> bool:
        return self.role in AUTHORITY_BEARING_ARGUMENT_ROLES

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "role": self.role.value,
            "value_fingerprint": self.value_fingerprint,
            "provenance": self.provenance.to_dict(),
            "redacted_value": self.redacted_value,
        }


@dataclass(frozen=True, slots=True)
class OperationArgumentSchema:
    operation: str
    version: str
    roles: Mapping[str, ArgumentRole]

    def __post_init__(self) -> None:
        if not self.operation or not self.version or not self.roles:
            raise ValueError("operation argument schema requires identity and roles")
        if any(not name for name in self.roles):
            raise ValueError("operation argument names must be non-empty")
        object.__setattr__(self, "roles", MappingProxyType(dict(self.roles)))

    def bind(
        self,
        values: Mapping[str, tuple[object, Provenance]],
        *,
        redacted_values: Mapping[str, object] | None = None,
    ) -> tuple[ActionArgument, ...]:
        missing = set(self.roles) - set(values)
        unknown = set(values) - set(self.roles)
        if missing or unknown:
            raise ValueError(f"operation argument binding mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}")
        safe_values = redacted_values or {}
        unknown_redactions = set(safe_values) - set(self.roles)
        if unknown_redactions:
            raise ValueError(f"unknown redacted argument values: {sorted(unknown_redactions)}")
        return tuple(
            ActionArgument.bind(
                name=name,
                role=role,
                value=values[name][0],
                provenance=values[name][1],
                redacted_value=safe_values.get(name),
            )
            for name, role in sorted(self.roles.items())
        )


@dataclass(frozen=True, slots=True)
class PrimitiveAction:
    id: str
    operation: str
    permission: Permission
    resource: ResourceRef | None = None
    inputs: tuple[Artifact[Any], ...] = ()
    visibility: ActionVisibility = ActionVisibility.INTERNAL
    arguments: tuple[ActionArgument, ...] = ()
    kind: ActionKind = field(default=ActionKind.PRIMITIVE, init=False)

    def __post_init__(self) -> None:
        if not self.id or not self.operation:
            raise ValueError("PrimitiveAction id and operation must be non-empty")
        object.__setattr__(self, "permission", normalise_permission(self.permission))
        object.__setattr__(self, "inputs", tuple(self.inputs))
        object.__setattr__(self, "arguments", tuple(self.arguments))
        if any(not isinstance(argument, ActionArgument) for argument in self.arguments):
            raise TypeError("PrimitiveAction.arguments must contain ActionArgument values")
        names = [argument.name for argument in self.arguments]
        if len(names) != len(set(names)):
            raise ValueError("action argument names must be unique")


@dataclass(frozen=True, slots=True)
class NestedExecutionAction:
    id: str
    inputs: tuple[Artifact[Any], ...]
    visibility: ActionVisibility = ActionVisibility.INTERNAL
    kind: ActionKind = field(default=ActionKind.NESTED, init=False)

    def __post_init__(self) -> None:
        if not self.id or not self.inputs:
            raise ValueError("NestedExecutionAction requires an id and inputs")
        object.__setattr__(self, "inputs", tuple(self.inputs))


@dataclass(frozen=True, slots=True)
class MessageAction:
    id: str
    message: str
    inputs: tuple[Artifact[Any], ...] = ()
    visibility: ActionVisibility = ActionVisibility.PARTICIPANTS
    kind: ActionKind = field(default=ActionKind.MESSAGE, init=False)

    def __post_init__(self) -> None:
        if not self.id or not self.message:
            raise ValueError("MessageAction id and message must be non-empty")
        object.__setattr__(self, "inputs", tuple(self.inputs))


@dataclass(frozen=True, slots=True)
class DelegationAction:
    id: str
    scope: str
    inputs: tuple[Artifact[Any], ...] = ()
    visibility: ActionVisibility = ActionVisibility.PARTICIPANTS
    kind: ActionKind = field(default=ActionKind.DELEGATION, init=False)

    def __post_init__(self) -> None:
        if not self.id or not self.scope:
            raise ValueError("DelegationAction id and scope must be non-empty")
        object.__setattr__(self, "inputs", tuple(self.inputs))


@dataclass(frozen=True, slots=True)
class StopAction:
    id: str
    reason: str = "stopped"
    inputs: tuple[Artifact[Any], ...] = ()
    visibility: ActionVisibility = ActionVisibility.INTERNAL
    kind: ActionKind = field(default=ActionKind.STOP, init=False)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("StopAction.id must be non-empty")


@dataclass(frozen=True, slots=True)
class NoOpAction:
    id: str
    label: str = "no-op"
    inputs: tuple[Artifact[Any], ...] = ()
    visibility: ActionVisibility = ActionVisibility.INTERNAL
    kind: ActionKind = field(default=ActionKind.NO_OP, init=False)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("NoOpAction.id must be non-empty")


Action: TypeAlias = PrimitiveAction | NestedExecutionAction | MessageAction | DelegationAction | StopAction | NoOpAction
Proposal: TypeAlias = Action


@dataclass(frozen=True, slots=True)
class ProposalBatch:
    mode: ProposalMode
    proposals: tuple[Action, ...]
    schema_version: str = "2"

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposals", tuple(self.proposals))
        if self.mode == ProposalMode.ORDERED_PLAN and not self.proposals:
            raise ValueError("an ordered plan must contain at least one action")

    @classmethod
    def alternatives(cls, *proposals: Action) -> "ProposalBatch":
        return cls(ProposalMode.ALTERNATIVES, proposals)

    @classmethod
    def ordered_plan(cls, *proposals: Action) -> "ProposalBatch":
        return cls(ProposalMode.ORDERED_PLAN, proposals)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode.value,
            "proposals": [action_to_dict(action) for action in self.proposals],
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


def action_inputs(action: Action) -> tuple[Artifact[Any], ...]:
    return action.inputs


def action_provenance(action: Action) -> Provenance:
    provenances = tuple(item.provenance for item in action.inputs)
    if isinstance(action, PrimitiveAction):
        provenances += tuple(argument.provenance for argument in action.arguments)
    return provenance_union(*provenances)


def action_to_dict(action: Action) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": "2",
        "id": action.id,
        "kind": action.kind.value,
        "visibility": action.visibility.value,
        "input_ids": [item.id for item in action.inputs],
    }
    if isinstance(action, PrimitiveAction):
        result.update(
            operation=action.operation,
            permission=action.permission.name,
            resource=action.resource.to_dict() if action.resource else None,
            arguments=[argument.to_dict() for argument in action.arguments],
        )
    elif isinstance(action, MessageAction):
        result["message"] = action.message
    elif isinstance(action, DelegationAction):
        result["scope"] = action.scope
    elif isinstance(action, StopAction):
        result["reason"] = action.reason
    elif isinstance(action, NoOpAction):
        result["label"] = action.label
    return result


def action_fingerprint(action: Action) -> str:
    return fingerprint(action_to_dict(action))


def action_sort_key(action: Action) -> tuple[str, str, str]:
    return (action.kind.value, action.id, action_fingerprint(action))


__all__ = [
    "Action",
    "ActionKind",
    "ActionArgument",
    "ActionVisibility",
    "ArgumentRole",
    "AUTHORITY_BEARING_ARGUMENT_ROLES",
    "DelegationAction",
    "MessageAction",
    "NestedExecutionAction",
    "NoOpAction",
    "OperationArgumentSchema",
    "PrimitiveAction",
    "Proposal",
    "ProposalBatch",
    "ProposalMode",
    "StopAction",
    "action_fingerprint",
    "action_inputs",
    "action_provenance",
    "action_sort_key",
    "action_to_dict",
]
