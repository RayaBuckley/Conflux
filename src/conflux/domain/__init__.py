"""Canonical immutable security-domain values."""

from .actions import (
    Action,
    ActionKind,
    ActionVisibility,
    DelegationAction,
    MessageAction,
    NestedExecutionAction,
    NoOpAction,
    PrimitiveAction,
    Proposal,
    StopAction,
    action_fingerprint,
    action_sort_key,
)
from .artifacts import Artifact
from .decisions import ActionDecision, Decision, DecisionCategory
from .environment import DataItem, EnvironmentSnapshot
from .identity import Principal, PrincipalContext
from .permissions import (
    DELEGATE,
    DELETE,
    READ,
    SHARE,
    WRITE,
    Permission,
    normalise_permission,
)
from .provenance import Provenance, ProvenancePrecision, provenance_union
from .resources import ResourceRef
from .serialization import canonical_json, fingerprint
from .session import Session

__all__ = [
    "Action",
    "ActionDecision",
    "ActionKind",
    "ActionVisibility",
    "Artifact",
    "DELEGATE",
    "DELETE",
    "DataItem",
    "Decision",
    "DecisionCategory",
    "DelegationAction",
    "EnvironmentSnapshot",
    "MessageAction",
    "NestedExecutionAction",
    "NoOpAction",
    "Permission",
    "Principal",
    "PrincipalContext",
    "PrimitiveAction",
    "Proposal",
    "Provenance",
    "ProvenancePrecision",
    "READ",
    "ResourceRef",
    "SHARE",
    "Session",
    "StopAction",
    "WRITE",
    "action_fingerprint",
    "action_sort_key",
    "canonical_json",
    "fingerprint",
    "normalise_permission",
    "provenance_union",
]
