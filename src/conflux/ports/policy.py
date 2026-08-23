"""Independent fail-closed policy boundaries.

SEM-015: Policy dimensions are independent. Authorisation, read, visibility,
and consent are separate decisions. No dimension can override a denial in
another.

SEM-016: Fail-closed defaults. Missing consent, unknown schemas, policy
errors, and unavailable boundaries deny.
"""

from __future__ import annotations

from typing import Any, Protocol

from conflux.domain import (
    Action,
    ActionArgument,
    Artifact,
    AudienceVisibilityDecision,
    Decision,
    EnvironmentSnapshot,
    EventClass,
    Principal,
    PrincipalContext,
    Session,
)


class AuthorisationPort(Protocol):
    """Pointwise authorisation boundary for principal-action decisions."""

    @property
    def policy_id(self) -> str:
        """Stable identifier for this authorisation policy."""
        ...

    @property
    def policy_version(self) -> str:
        """Version string for this authorisation policy."""
        ...

    def decide(
        self,
        principal: Principal,
        action: Action,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Return an authorisation decision for the principal and action."""
        ...


class ReadPolicyPort(Protocol):
    """Pointwise read-access boundary for artifact visibility decisions."""

    @property
    def policy_id(self) -> str:
        """Stable identifier for this read policy."""
        ...

    @property
    def policy_version(self) -> str:
        """Version string for this read policy."""
        ...

    def decide(
        self,
        principal: Principal,
        artifact: Artifact[Any],
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Return a read decision for the given principal and artifact."""
        ...


class ArgumentAuthorisationPort(Protocol):
    """Pointwise authority for one trusted-role action argument."""

    @property
    def policy_id(self) -> str:
        """Stable identifier for this argument authorisation policy."""
        ...

    @property
    def policy_version(self) -> str:
        """Version string for this argument authorisation policy."""
        ...

    def decide(
        self,
        principal: Principal,
        action: Action,
        argument: ActionArgument,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Return an authorisation decision for one action argument."""
        ...


class VisibilityPolicyPort(Protocol):
    """Pointwise visibility boundary for session-level action visibility."""

    @property
    def policy_id(self) -> str:
        """Stable identifier for this visibility policy."""
        ...

    @property
    def policy_version(self) -> str:
        """Version string for this visibility policy."""
        ...

    def decide(self, session: Session, action: Action, context: PrincipalContext) -> Decision:
        """Return a visibility decision for the action within the session."""
        ...


class ConsentPolicyPort(Protocol):
    """Pointwise consent boundary with fail-closed defaults."""

    @property
    def policy_id(self) -> str:
        """Stable identifier for this consent policy."""
        ...

    @property
    def policy_version(self) -> str:
        """Version string for this consent policy."""
        ...

    def decide(self, session: Session, action: Action, context: PrincipalContext) -> Decision:
        """Return a consent decision for the action within the session."""
        ...


class AudienceVisibilityPolicyPort(Protocol):
    """Per-audience field-disclosure boundary for event-class visibility."""

    @property
    def policy_id(self) -> str:
        """Stable identifier for this audience visibility policy."""
        ...

    @property
    def policy_version(self) -> str:
        """Version string for this audience visibility policy."""
        ...

    def decide(
        self,
        session: Session,
        audience: Principal,
        event_class: EventClass,
        action: Action | None,
        context: PrincipalContext,
    ) -> AudienceVisibilityDecision:
        """Return a disclosure-level decision for the given audience."""
        ...


__all__ = [
    "ArgumentAuthorisationPort",
    "AudienceVisibilityPolicyPort",
    "AuthorisationPort",
    "ConsentPolicyPort",
    "ReadPolicyPort",
    "VisibilityPolicyPort",
]
