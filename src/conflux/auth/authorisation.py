"""
Authorisation and visibility checks.

This module combines:
- the exact intersection rule from the original prototype,
- consent checks over the current decision principals,
- and chat visibility policy checks.

It deliberately does not expand the authority set. If consent is withheld by
the current decision principals, the action is blocked or must be replaced by
another plan generated from the same current influences.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from conflux.core.actions import (
    Action,
    ActionVisibility,
    ClarificationRequestAction,
    DelegationAction,
    MessageUserAction,
    NestedExecutionAction,
    NoOpAction,
    PrimitiveAction,
    RequestConsentAction,
    StopAction,
)
from conflux.core.artifacts import Artifact
from conflux.core.consent import (
    ConsentDecision,
    ConsentState,
    consent_from_profiles,
)
from conflux.core.permissions import Permission, normalise_permission
from conflux.core.principals import Principal
from conflux.core.provenance import Provenance
from conflux.core.session import Session


@dataclass(frozen=True, slots=True)
class AuthorisationDecision:
    """
    Result of evaluating whether an action may proceed.
    """

    allowed: bool
    reason: str
    visibility_allowed: bool = True
    consent: ConsentDecision | None = None

    @property
    def blocked(self) -> bool:
        return not self.allowed


def principals_for_provenance(provenance: Provenance) -> frozenset[Principal]:
    """
    Return the set of principals that influenced the provenance.
    """
    return provenance.principals


def effective_authority(provenance: Provenance) -> frozenset[Principal]:
    """Return the Principal Context represented by provenance."""
    return frozenset(provenance.principals)


def can_access(
    provenance: Provenance,
    resource: object,
    permission: Permission | str,
) -> bool:
    """Return whether provenance permits an operation on a resource.

    Supports the historical owner-shaped resource API and the current model's
    optional ``attributes['owner']`` representation. Missing ownership is
    denied conservatively.
    """
    owner = getattr(resource, "owner", None)
    if owner is None:
        attributes = getattr(resource, "attributes", {})
        owner = attributes.get("owner") if hasattr(attributes, "get") else None
    if not isinstance(owner, Principal) or owner not in provenance.principals:
        return False
    return all_principals_authorised(provenance.principals, permission)


def influencers_for_artifacts(
    artifacts: Iterable[Artifact[object]],
) -> frozenset[Principal]:
    """
    Return the union of the principals that influenced a collection of artifacts.
    """
    principals: set[Principal] = set()
    for artifact in artifacts:
        principals.update(artifact.provenance.principals)
    return frozenset(principals)


def all_principals_authorised(
    principals: Iterable[Principal],
    permission: Permission | str,
) -> bool:
    """
    Exact intersection rule from the original prototype.

    Every principal in the influencer set must authorise the action.
    """
    perm = normalise_permission(permission)
    return all(principal.can_perform(perm) for principal in principals)


def any_principal_authorised(
    principals: Iterable[Principal],
    permission: Permission | str,
) -> bool:
    """
    Convenience helper used by some policy adapters.

    This is not the intersection rule. It is only useful for diagnostics or
    adapter-specific heuristics.
    """
    perm = normalise_permission(permission)
    return any(principal.can_perform(perm) for principal in principals)


def chat_visibility_allows(session: Session, visibility: ActionVisibility) -> bool:
    """
    Return whether the session permits the action's visibility class.
    """
    return session.chat_policy.permits_visibility(visibility)


def decision_principals_for_action(action: Action[object]) -> frozenset[Principal]:
    """
    Return the principals that actually determined the action.
    """
    return action.decision_principals


def consent_allows_action(session: Session, action: Action[object]) -> ConsentDecision:
    """
    Check whether the current decision principals consent to the action.

    Consent is only meaningful for the principals currently attached to the
    action's decision provenance. The function does not recruit new principals.
    """
    profiles = tuple(
        profile
        for profile in session.consent_profiles
        if profile.principal in action.decision_principals
    )
    return consent_from_profiles(action, action.decision_principals, profiles)


def _action_inputs(action: Action[object]) -> frozenset[Artifact[object]]:
    """
    Return the action inputs as a typed artifact set.
    """
    return frozenset(action.inputs)


def _readability_required(action: Action[object]) -> bool:
    """
    Return True if this action must satisfy the "all influencers can read all
    inputs" rule before it can be emitted.

    Any non-internal action that depends on inputs should not expose content to
    observers who cannot already read those inputs.
    """
    return action.visibility != ActionVisibility.INTERNAL and bool(action.inputs)


def _inputs_readable_by_principals(
    inputs: Iterable[Artifact[object]],
    principals: Iterable[Principal],
) -> bool:
    """
    Exact readability check inherited from the prior prototype.

    Every principal must be permitted to read every input.
    """
    principal_set = frozenset(principals)
    for artifact in inputs:
        readers = artifact.provenance.principals
        if any(principal not in readers for principal in principal_set):
            return False
    return True


def _effective_influencers(action: Action[object]) -> frozenset[Principal]:
    """
    Derive the influencer set for an action.

    For legacy compatibility, this prefers input provenance and falls back to
    the decision principals if no provenance is attached.
    """
    from_inputs = influencers_for_artifacts(action.inputs)
    if from_inputs:
        return from_inputs
    return action.decision_principals


def primitive_authorisation(
    session: Session,
    action: PrimitiveAction,
) -> AuthorisationDecision:
    """
    Evaluate a primitive provider action.

    This uses:
    - the exact intersection rule over the action's influencers,
    - the session's consent profiles,
    - and the session's visibility policy.
    """
    influencers = _effective_influencers(action)
    if action.decision_principals:
        influencers = influencers | action.decision_principals

    if _readability_required(action) and not _inputs_readable_by_principals(action.inputs, influencers):
        return AuthorisationDecision(
            allowed=False,
            reason=(
                "Blocked because not all influencers can read all inputs for "
                "this visible primitive action."
            ),
            visibility_allowed=chat_visibility_allows(session, action.visibility),
        )

    if not all_principals_authorised(influencers, action.permission):
        return AuthorisationDecision(
            allowed=False,
            reason=(
                "Blocked by the intersection rule: at least one influencer "
                "lacks the permission."
            ),
            visibility_allowed=chat_visibility_allows(session, action.visibility),
        )

    consent = consent_allows_action(session, action)
    if consent.state == ConsentState.WITHHOLD:
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because the current decision principals withheld consent.",
            visibility_allowed=chat_visibility_allows(session, action.visibility),
            consent=consent,
        )

    if consent.state == ConsentState.REQUIRE_CONFIRMATION:
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked pending confirmation from current decision principals.",
            visibility_allowed=chat_visibility_allows(session, action.visibility),
            consent=consent,
        )

    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
            consent=consent,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Authorised by intersection rule, consent, and visibility policy.",
        visibility_allowed=True,
        consent=consent,
    )


def message_authorisation(
    session: Session,
    action: MessageUserAction,
) -> AuthorisationDecision:
    """
    Evaluate a user-visible message action.

    The content may be visible only if the chat policy permits the visibility
    class and the current influencers are authorised to expose the underlying
    inputs.
    """
    influencers = _effective_influencers(action)
    if action.decision_principals:
        influencers = influencers | action.decision_principals

    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    if action.inputs and not _inputs_readable_by_principals(action.inputs, influencers):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because not all influencers can read all message inputs.",
            visibility_allowed=True,
        )

    consent = consent_allows_action(session, action)
    if consent.state != ConsentState.ALLOW:
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because the current decision principals did not consent.",
            visibility_allowed=True,
            consent=consent,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Message is visible and consented.",
        visibility_allowed=True,
        consent=consent,
    )


def nested_execution_authorisation(
    session: Session,
    action: NestedExecutionAction,
) -> AuthorisationDecision:
    """
    Evaluate a nested execution action.

    Nested execution is allowed only if:
    - the inputs are visible under the session policy,
    - the current influencers can read all inputs,
    - and the current decision principals consent.
    """
    influencers = _effective_influencers(action)
    if action.decision_principals:
        influencers = influencers | action.decision_principals

    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    if action.inputs and not _inputs_readable_by_principals(action.inputs, influencers):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because not all influencers can read all nested inputs.",
            visibility_allowed=True,
        )

    consent = consent_allows_action(session, action)
    if consent.state != ConsentState.ALLOW:
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because the current decision principals did not consent.",
            visibility_allowed=True,
            consent=consent,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Nested execution is authorised.",
        visibility_allowed=True,
        consent=consent,
    )


def delegation_authorisation(
    session: Session,
    action: DelegationAction,
) -> AuthorisationDecision:
    """
    Evaluate a delegation action.

    Delegation is treated as a high-impact control action. It requires:
    - session visibility permission,
    - readability of any attached inputs,
    - intersection-rule authorisation for the delegated scope,
    - and consent from the current decision principals.
    """
    influencers = _effective_influencers(action)
    if action.decision_principals:
        influencers = influencers | action.decision_principals

    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    if action.inputs and not _inputs_readable_by_principals(action.inputs, influencers):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because not all influencers can read all delegation inputs.",
            visibility_allowed=True,
        )

    if action.delegated_permissions:
        if any(not all_principals_authorised(influencers, permission) for permission in action.delegated_permissions):
            return AuthorisationDecision(
                allowed=False,
                reason="Blocked by the intersection rule for one or more delegated permissions.",
                visibility_allowed=True,
            )
    else:
        if not all_principals_authorised(influencers, "delegate"):
            return AuthorisationDecision(
                allowed=False,
                reason="Blocked by the intersection rule: delegation permission missing.",
                visibility_allowed=True,
            )

    consent = consent_allows_action(session, action)
    if consent.state != ConsentState.ALLOW:
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because the current decision principals did not consent.",
            visibility_allowed=True,
            consent=consent,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Delegation is authorised.",
        visibility_allowed=True,
        consent=consent,
    )


def clarification_request_authorisation(
    session: Session,
    action: ClarificationRequestAction,
) -> AuthorisationDecision:
    """
    Evaluate a clarification request.

    Clarification requests are user-visible and therefore must respect both the
    visibility policy and input-readability constraints.
    """
    influencers = _effective_influencers(action)
    if action.decision_principals:
        influencers = influencers | action.decision_principals

    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    if action.inputs and not _inputs_readable_by_principals(action.inputs, influencers):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because not all influencers can read all clarification inputs.",
            visibility_allowed=True,
        )

    consent = consent_allows_action(session, action)
    if consent.state != ConsentState.ALLOW:
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because the current decision principals did not consent.",
            visibility_allowed=True,
            consent=consent,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Clarification request is authorised.",
        visibility_allowed=True,
        consent=consent,
    )


def request_consent_authorisation(
    session: Session,
    action: RequestConsentAction,
) -> AuthorisationDecision:
    """
    Evaluate a request-consent action.

    This action is always internal or user-visible, but it still cannot reveal
    content that the current influencers are not entitled to expose.
    """
    influencers = _effective_influencers(action)
    if action.decision_principals:
        influencers = influencers | action.decision_principals

    if action.inputs and not _inputs_readable_by_principals(action.inputs, influencers):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because not all influencers can read all request inputs.",
            visibility_allowed=chat_visibility_allows(session, action.visibility),
        )

    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Consent request may be shown to current decision principals.",
        visibility_allowed=True,
    )


def stop_authorisation(
    session: Session,
    action: StopAction,
) -> AuthorisationDecision:
    """
    Evaluate a stop action.
    """
    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Stop action is authorised.",
        visibility_allowed=True,
    )


def noop_authorisation(
    session: Session,
    action: NoOpAction,
) -> AuthorisationDecision:
    """
    Evaluate a no-op action.
    """
    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="No-op action is authorised.",
        visibility_allowed=True,
    )


def authorise_action(
    session: Session,
    action: Action[object],
) -> AuthorisationDecision:
    """
    Dispatch to the correct authorisation check for an action.
    """
    if isinstance(action, PrimitiveAction):
        return primitive_authorisation(session, action)

    if isinstance(action, MessageUserAction):
        return message_authorisation(session, action)

    if isinstance(action, NestedExecutionAction):
        return nested_execution_authorisation(session, action)

    if isinstance(action, DelegationAction):
        return delegation_authorisation(session, action)

    if isinstance(action, ClarificationRequestAction):
        return clarification_request_authorisation(session, action)

    if isinstance(action, RequestConsentAction):
        return request_consent_authorisation(session, action)

    if isinstance(action, StopAction):
        return stop_authorisation(session, action)

    if isinstance(action, NoOpAction):
        return noop_authorisation(session, action)

    if not chat_visibility_allows(session, action.visibility):
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked by the session visibility policy.",
            visibility_allowed=False,
        )

    consent = consent_allows_action(session, action)
    if consent.state != ConsentState.ALLOW:
        return AuthorisationDecision(
            allowed=False,
            reason="Blocked because the current decision principals did not consent.",
            visibility_allowed=True,
            consent=consent,
        )

    return AuthorisationDecision(
        allowed=True,
        reason="Authorised.",
        visibility_allowed=True,
        consent=consent,
    )


__all__ = [
    "AuthorisationDecision",
    "all_principals_authorised",
    "any_principal_authorised",
    "authorise_action",
    "can_access",
    "chat_visibility_allows",
    "clarification_request_authorisation",
    "consent_allows_action",
    "delegation_authorisation",
    "decision_principals_for_action",
    "effective_authority",
    "influencers_for_artifacts",
    "message_authorisation",
    "nested_execution_authorisation",
    "noop_authorisation",
    "principals_for_provenance",
    "primitive_authorisation",
    "request_consent_authorisation",
    "stop_authorisation",
]
