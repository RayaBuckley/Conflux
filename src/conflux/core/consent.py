"""
Consent model.

Consent is narrower than authorisation.

Authorisation answers:
    "May this action happen under the provider policy and intersection rule?"

Consent answers:
    "Will the current decision principals permit this action to proceed
    without further confirmation?"

Consent must be tied to decision provenance. It is not enough that a principal
exists somewhere in the session; the principal must be one of the actual
decision principals for the action being considered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from .actions import Action, ActionKind
from .permissions import Permission, normalise_permission
from .principals import Principal
from .resources import Resource


class ConsentState(str, Enum):
    """Possible outcomes for a consent check."""

    ALLOW = "allow"
    WITHHOLD = "withhold"
    REQUIRE_CONFIRMATION = "require_confirmation"


@dataclass(frozen=True, slots=True)
class ConsentGrant:
    """
    Consent provided by a principal for a restricted set of actions.

    A grant is intentionally conservative:
    - it may apply to selected permissions,
    - optionally to a selected resource,
    - optionally to a selected action kind,
    - and only if the principal is actually part of the decision provenance.
    """

    principal: Principal
    permissions: frozenset[Permission] = field(default_factory=frozenset)
    resource_id: str | None = None
    action_kinds: frozenset[ActionKind] = field(default_factory=frozenset)
    note: str = ""

    def __post_init__(self) -> None:
        normalised = frozenset(
            normalise_permission(permission) for permission in self.permissions
        )
        object.__setattr__(self, "permissions", normalised)
        object.__setattr__(self, "action_kinds", frozenset(self.action_kinds))

    def covers_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    def covers_action(self, action: Action[Any]) -> bool:
        if self.action_kinds and action.kind not in self.action_kinds:
            return False

        if hasattr(action, "permission"):
            permission = getattr(action, "permission")
            if isinstance(permission, str):
                permission = normalise_permission(permission)
            if permission not in self.permissions:
                return False

        if self.resource_id is not None:
            resource = getattr(action, "resource", None)
            if resource is None or resource.id != self.resource_id:
                return False

        return True


@dataclass(frozen=True, slots=True)
class ConsentProfile:
    """
    A consent policy for a single principal.

    This is the reduced set of permissions the principal is willing to let the
    LLM execute automatically.
    """

    principal: Principal
    allowed_permissions: frozenset[Permission] = field(default_factory=frozenset)
    allowed_action_kinds: frozenset[ActionKind] = field(default_factory=frozenset)
    allowed_resources: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        normalised = frozenset(
            normalise_permission(permission) for permission in self.allowed_permissions
        )
        object.__setattr__(self, "allowed_permissions", normalised)
        object.__setattr__(self, "allowed_action_kinds", frozenset(self.allowed_action_kinds))
        object.__setattr__(self, "allowed_resources", frozenset(self.allowed_resources))

    def allows(self, action: Action[Any]) -> bool:
        """
        Return True if this profile permits the given action.

        This is only a consent check. It does not imply authorisation.
        """
        if self.allowed_action_kinds and action.kind not in self.allowed_action_kinds:
            return False

        if self.allowed_resources:
            resource = getattr(action, "resource", None)
            if resource is None or resource.id not in self.allowed_resources:
                return False

        if hasattr(action, "permission"):
            permission = getattr(action, "permission")
            if isinstance(permission, str):
                permission = normalise_permission(permission)
            if self.allowed_permissions and permission not in self.allowed_permissions:
                return False

        return True

    def allows_resource(self, resource: Resource) -> bool:
        """Return True if this profile allows the resource."""
        if not self.allowed_resources:
            return True
        return resource.id in self.allowed_resources

    def allows_kind(self, kind: ActionKind) -> bool:
        """Return True if this profile allows the action kind."""
        if not self.allowed_action_kinds:
            return True
        return kind in self.allowed_action_kinds


@dataclass(frozen=True, slots=True)
class ConsentWitness:
    """
    Records which principals actually consented to a specific action.

    The witness must be attributable to the action's decision principals.
    """

    action_kind: ActionKind
    consenting_principals: frozenset[Principal] = field(default_factory=frozenset)
    refused_principals: frozenset[Principal] = field(default_factory=frozenset)
    explanation: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "consenting_principals", frozenset(self.consenting_principals))
        object.__setattr__(self, "refused_principals", frozenset(self.refused_principals))
        if not self.consenting_principals and not self.refused_principals:
            raise ValueError("ConsentWitness must record at least one principal")

    def has_consenter(self, principal: Principal) -> bool:
        return principal in self.consenting_principals

    def refused_by(self, principal: Principal) -> bool:
        return principal in self.refused_principals


@dataclass(frozen=True, slots=True)
class ConsentDecision:
    """
    The result of evaluating consent for a candidate action.

    This is the object the evaluator can inspect when deciding whether to
    proceed, request confirmation, or block the branch.
    """

    state: ConsentState
    witness: ConsentWitness | None = None
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.state == ConsentState.ALLOW


def consent_from_profiles(
    action: Action[Any],
    decision_principals: Iterable[Principal],
    profiles: Iterable[ConsentProfile],
) -> ConsentDecision:
    """
    Evaluate whether the action has valid consent from the current decision principals.

    Rules:
    - only current decision principals can count as consenters;
    - at least one current decision principal must explicitly allow the action;
    - if any current decision principal refuses, the action is not automatically allowed;
    - the function does not broaden authority or recruit extra principals.
    """
    decision_set = frozenset(decision_principals)
    profile_by_principal = {profile.principal: profile for profile in profiles}

    consenting: set[Principal] = set()
    refused: set[Principal] = set()

    for principal in decision_set:
        profile = profile_by_principal.get(principal)
        if profile is None:
            refused.add(principal)
            continue

        if profile.allows(action):
            consenting.add(principal)
        else:
            refused.add(principal)

    if consenting:
        witness = ConsentWitness(
            action_kind=action.kind,
            consenting_principals=frozenset(consenting),
            refused_principals=frozenset(refused),
            explanation="At least one current decision principal consented.",
        )
        if refused:
            return ConsentDecision(
                state=ConsentState.REQUIRE_CONFIRMATION,
                witness=witness,
                reason="One or more current decision principals withheld consent.",
            )
        return ConsentDecision(
            state=ConsentState.ALLOW,
            witness=witness,
            reason="Current decision principals consented.",
        )

    witness = ConsentWitness(
        action_kind=action.kind,
        consenting_principals=frozenset(),
        refused_principals=frozenset(refused or decision_set),
        explanation="No current decision principal consented.",
    )
    return ConsentDecision(
        state=ConsentState.WITHHOLD,
        witness=witness,
        reason="No current decision principal consented.",
    )


def consent_allows(
    action: Action[Any],
    decision_principals: Iterable[Principal],
    profiles: Iterable[ConsentProfile],
) -> bool:
    """Convenience wrapper returning only the boolean result."""
    return consent_from_profiles(action, decision_principals, profiles).allowed


__all__ = [
    "ConsentDecision",
    "ConsentGrant",
    "ConsentProfile",
    "ConsentState",
    "ConsentWitness",
    "consent_allows",
    "consent_from_profiles",
]
