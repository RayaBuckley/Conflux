"""Read, visibility, and consent policies with explicit defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from conflux.domain import (
    Action,
    ActionVisibility,
    Artifact,
    AudienceVisibilityDecision,
    Decision,
    DecisionCategory,
    DisclosureLevel,
    EnvironmentSnapshot,
    EventClass,
    NoOpAction,
    Principal,
    PrincipalContext,
    Session,
    StopAction,
)


@dataclass(frozen=True, slots=True)
class SnapshotReadPolicy:
    """Read policy that grants only principals listed in the snapshot's readers."""

    policy_id: str = "snapshot-read-policy"
    policy_version: str = "1"

    def decide(
        self,
        principal: Principal,
        artifact: Artifact[Any],
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Return a read decision based on the snapshot's readers list."""
        item = environment.data_item(artifact.id)
        allowed = item is not None and principal in item.readers
        return Decision(
            DecisionCategory.READ,
            allowed,
            "reader_grant" if allowed else "reader_deny",
            self.policy_id,
            self.policy_version,
            evidence=(principal.id, artifact.id),
        )


@dataclass(frozen=True, slots=True)
class SessionVisibilityPolicy:
    """Visibility policy checking principals against session participants."""

    policy_id: str = "session-visibility-policy"
    policy_version: str = "1"

    def decide(self, session: Session, action: Action, context: PrincipalContext) -> Decision:
        """Return a visibility decision based on session participation."""
        if action.visibility == ActionVisibility.INTERNAL:
            allowed = True
            reason = "internal"
        else:
            allowed = context.principals.issubset(session.participants)
            reason = "participants_visible" if allowed else "principal_not_visible"
        return Decision(
            DecisionCategory.VISIBILITY,
            allowed,
            reason,
            self.policy_id,
            self.policy_version,
            evidence=tuple(sorted(principal.id for principal in session.participants)),
        )


@dataclass(frozen=True, slots=True)
class ExplicitConsentPolicy:
    """Fail closed except for explicitly approved actions and safe control flow."""

    approved_action_ids: frozenset[str] = field(default_factory=frozenset)
    policy_id: str = "explicit-consent-policy"
    policy_version: str = "1"

    def decide(self, session: Session, action: Action, context: PrincipalContext) -> Decision:
        """Return a consent decision for explicitly approved or safe actions."""
        _ = session, context
        safe_control = isinstance(action, (StopAction, NoOpAction))
        allowed = safe_control or action.id in self.approved_action_ids
        return Decision(
            DecisionCategory.CONSENT,
            allowed,
            "safe_internal_control" if safe_control else ("explicit_consent" if allowed else "missing_consent"),
            self.policy_id,
            self.policy_version,
            evidence=(action.id,) if allowed else (),
        )


@dataclass(frozen=True, slots=True)
class SessionAudienceVisibilityPolicy:
    """Conservative field-disclosure policy for one recipient and event class."""

    policy_id: str = "session-audience-visibility-policy"
    policy_version: str = "1"

    def decide(
        self,
        session: Session,
        audience: Principal,
        event_class: EventClass,
        action: Action | None,
        context: PrincipalContext,
    ) -> AudienceVisibilityDecision:
        """Return a disclosure-level decision for one audience and event class."""
        _ = action
        if audience not in session.participants:
            level = DisclosureLevel.NONE
            reason = "audience_not_participant"
        elif event_class in {EventClass.DECISION, EventClass.ERROR}:
            level = DisclosureLevel.REDACTED
            reason = "sensitive_decision_details_redacted"
        elif audience in context.principals:
            level = DisclosureLevel.FULL
            reason = "influencing_principal"
        elif event_class == EventClass.DECLARATION:
            level = DisclosureLevel.EXISTENCE
            reason = "participant_declaration_exists"
        else:
            level = DisclosureLevel.REDACTED
            reason = "participant_not_in_context"
        return AudienceVisibilityDecision(
            audience,
            event_class,
            level,
            reason,
            self.policy_id,
            self.policy_version,
        )


@dataclass(frozen=True, slots=True)
class AllowInternalReadPolicy:
    """Allow already-active internal values; useful for model-checking fixtures."""

    policy_id: str = "allow-internal-read"
    policy_version: str = "1"

    def decide(
        self,
        principal: Principal,
        artifact: Artifact[Any],
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Unconditionally allow internal reads; for model-checking fixtures."""
        _ = principal, artifact, environment
        return Decision(
            DecisionCategory.READ,
            True,
            "trusted_internal_fixture",
            self.policy_id,
            self.policy_version,
        )


__all__ = [
    "AllowInternalReadPolicy",
    "ExplicitConsentPolicy",
    "SessionAudienceVisibilityPolicy",
    "SessionVisibilityPolicy",
    "SnapshotReadPolicy",
]
