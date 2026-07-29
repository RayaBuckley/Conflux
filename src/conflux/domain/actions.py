"""Typed declarative model proposals; none performs a side effect."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypeAlias

from .artifacts import Artifact
from .permissions import Permission, normalise_permission
from .resources import ResourceRef
from .serialization import fingerprint


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


@dataclass(frozen=True, slots=True)
class PrimitiveAction:
    id: str
    operation: str
    permission: Permission
    resource: ResourceRef | None = None
    inputs: tuple[Artifact[Any], ...] = ()
    visibility: ActionVisibility = ActionVisibility.INTERNAL
    kind: ActionKind = field(default=ActionKind.PRIMITIVE, init=False)

    def __post_init__(self) -> None:
        if not self.id or not self.operation:
            raise ValueError("PrimitiveAction id and operation must be non-empty")
        object.__setattr__(self, "permission", normalise_permission(self.permission))
        object.__setattr__(self, "inputs", tuple(self.inputs))


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


Action: TypeAlias = (
    PrimitiveAction
    | NestedExecutionAction
    | MessageAction
    | DelegationAction
    | StopAction
    | NoOpAction
)
Proposal: TypeAlias = Action


def action_inputs(action: Action) -> tuple[Artifact[Any], ...]:
    return action.inputs


def action_to_dict(action: Action) -> dict[str, object]:
    result: dict[str, object] = {
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
    "ActionVisibility",
    "DelegationAction",
    "MessageAction",
    "NestedExecutionAction",
    "NoOpAction",
    "PrimitiveAction",
    "Proposal",
    "StopAction",
    "action_fingerprint",
    "action_inputs",
    "action_sort_key",
    "action_to_dict",
]
