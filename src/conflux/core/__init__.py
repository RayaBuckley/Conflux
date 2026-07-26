"""
Core domain model.

Layer: canonical security domain. This package owns immutable Principals,
resources, permissions, provenance, artifacts, actions, consent, visibility,
and sessions. It must not import policy, provider, benchmark, or evaluator code.

See ``docs/ARCHITECTURE.md``, ``docs/REFERENCE.md``, and ``docs/AUDIT.md``.

This package contains the fundamental immutable objects used throughout the
system. These objects are deliberately independent of execution, policy and
authorisation logic.

Modules:

* principals: Represents users, services and other security principals.
* resources: Represents protected resources.
* permissions: Defines permission types.
* provenance: Tracks the causal origins of information.
* artifacts: Represents information together with its provenance.
* actions: Defines the shared action taxonomy.
* consent: Defines consent state and profiles.
* chat_policy: Defines conversation visibility policy.
* session: Binds together participants, consent, and chat policy.
"""

from .actions import (
    Action,
    ActionKind,
    ActionVisibility,
    ClarificationRequestAction,
    DelegationAction,
    MessageUserAction,
    NestedExecutionAction,
    NoOpAction,
    PrimitiveAction,
    Proposal,
    RequestConsentAction,
    StopAction,
)
from .artifacts import Artifact
from .chat_policy import ChatConfidentiality, ChatPolicy
from .consent import (
    ConsentDecision,
    ConsentGrant,
    ConsentProfile,
    ConsentState,
    ConsentWitness,
)
from .permissions import (
    DELEGATE,
    DELETE,
    READ,
    SHARE,
    WRITE,
    Permission,
    normalise_permission,
    permission_names,
)
from .principals import Principal
from .provenance import Provenance, authors_for, provenance_union
from .resources import Resource
from .session import Session

__all__ = [
    "Action",
    "ActionKind",
    "ActionVisibility",
    "Artifact",
    "ChatConfidentiality",
    "ChatPolicy",
    "ClarificationRequestAction",
    "ConsentDecision",
    "ConsentGrant",
    "ConsentProfile",
    "ConsentState",
    "ConsentWitness",
    "DELEGATE",
    "DELETE",
    "DelegationAction",
    "MessageUserAction",
    "NestedExecutionAction",
    "NoOpAction",
    "Permission",
    "PrimitiveAction",
    "Principal",
    "Proposal",
    "Provenance",
    "READ",
    "Resource",
    "RequestConsentAction",
    "SHARE",
    "Session",
    "StopAction",
    "WRITE",
    "authors_for",
    "normalise_permission",
    "permission_names",
    "provenance_union",
]
