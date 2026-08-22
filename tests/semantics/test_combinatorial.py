"""Combinatorial security tests across policy dimensions and action types.

Systematically verifies SEM-005 (conjunction of independent decisions),
SEM-006 (consent never manufactures authority), and SEM-007 (pointwise
authorisation across all principals in context) by varying principal sets,
action types, and each policy dimension.
"""

from __future__ import annotations

from typing import Any

import pytest

from conflux.application import DecisionPipeline
from conflux.domain import (
    WRITE,
    Action,
    ActionKind,
    ActionVisibility,
    Artifact,
    DataItem,
    DelegationAction,
    EnvironmentSnapshot,
    MessageAction,
    NestedExecutionAction,
    NoOpAction,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    ResourceRef,
    Session,
    StopAction,
)
from conflux.policy import (
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
    SnapshotReadPolicy,
)

pytestmark = pytest.mark.security

alice = Principal("alice", "Alice")
bob = Principal("bob", "Bob")
mallory = Principal("mallory", "Mallory")

_RESOURCE = ResourceRef("test", "out", "document")
_SESSION = Session("s", frozenset({alice, bob}))

_PSETS: dict[str, frozenset[Principal]] = {
    "single": frozenset({alice}),
    "mixed": frozenset({alice, mallory}),
    "empty": frozenset(),
}

_KINDS = [
    ActionKind.PRIMITIVE,
    ActionKind.NESTED,
    ActionKind.MESSAGE,
    ActionKind.DELEGATION,
    ActionKind.STOP,
    ActionKind.NO_OP,
]

_BOOLS = [True, False]


def _ctx(key: str) -> PrincipalContext:
    return PrincipalContext.from_principals(_PSETS[key])


def _env(read_allowed: bool) -> EnvironmentSnapshot:
    readers = frozenset({alice, mallory}) if read_allowed else frozenset({bob})
    item = DataItem("doc", "v", frozenset({alice}), readers)
    return EnvironmentSnapshot(id="env", data=(item,), resources=(_RESOURCE,))


def _grants(key: str, auth_granted: bool) -> frozenset[PolicyGrant]:
    if not auth_granted:
        return frozenset()
    if key == "mixed":
        return frozenset({PolicyGrant("alice", "write", "out"), PolicyGrant("mallory", "write", "out")})
    return frozenset({PolicyGrant("alice", "write", "out")})


def _pipeline(*, grants: frozenset[PolicyGrant], consent_ids: frozenset[str]) -> DecisionPipeline:
    return DecisionPipeline(
        InMemoryAuthorisationPolicy(grants),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(consent_ids),
    )


def _action(kind: ActionKind, *, visible: bool, env: EnvironmentSnapshot, action_id: str = "a1") -> Action:
    visibility = ActionVisibility.INTERNAL if visible else ActionVisibility.PARTICIPANTS
    inputs: tuple[Artifact[Any], ...] = ()
    if kind in (ActionKind.PRIMITIVE, ActionKind.NESTED):
        data_item = env.data_item("doc")
        assert data_item is not None
        inputs = (data_item.to_artifact(),)
    if kind == ActionKind.PRIMITIVE:
        return PrimitiveAction(
            id=action_id,
            operation="write",
            permission=WRITE,
            resource=_RESOURCE,
            visibility=visibility,
            inputs=inputs,
        )
    if kind == ActionKind.NESTED:
        return NestedExecutionAction(id=action_id, inputs=inputs, visibility=visibility)
    if kind == ActionKind.MESSAGE:
        return MessageAction(id=action_id, message="hello", visibility=visibility)
    if kind == ActionKind.DELEGATION:
        return DelegationAction(id=action_id, visibility=visibility)
    if kind == ActionKind.STOP:
        return StopAction(id=action_id, visibility=visibility)
    return NoOpAction(id=action_id, visibility=visibility)


def _expected(
    kind: ActionKind,
    pset: str,
    auth_granted: bool,
    consent_given: bool,
    visible: bool,
    read_allowed: bool,
) -> bool:
    if pset == "empty":
        return kind in (ActionKind.STOP, ActionKind.NO_OP)
    vis_ok = visible or _PSETS[pset].issubset(_SESSION.participants)
    if kind in (ActionKind.STOP, ActionKind.NO_OP):
        return vis_ok
    if kind == ActionKind.DELEGATION:
        return False
    auth_ok = auth_granted if kind == ActionKind.PRIMITIVE else True
    consent_ok = consent_given if kind in (ActionKind.PRIMITIVE, ActionKind.NESTED, ActionKind.MESSAGE) else True
    read_ok = read_allowed if kind in (ActionKind.PRIMITIVE, ActionKind.NESTED) else True
    return auth_ok and consent_ok and vis_ok and read_ok


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("pset", _PSETS)
@pytest.mark.parametrize("auth_granted", _BOOLS)
@pytest.mark.parametrize("consent_given", _BOOLS)
@pytest.mark.parametrize("visible", _BOOLS)
@pytest.mark.parametrize("read_allowed", _BOOLS)
def test_combinatorial_matrix(
    kind: ActionKind, pset: str, auth_granted: bool, consent_given: bool, visible: bool, read_allowed: bool
) -> None:
    env = _env(read_allowed)
    context = _ctx(pset)
    action = _action(kind, visible=visible, env=env)
    consent_ids = frozenset({"a1"}) if consent_given else frozenset()
    pipeline = _pipeline(grants=_grants(pset, auth_granted), consent_ids=consent_ids)
    decision = pipeline.decide(session=_SESSION, action=action, context=context, environment=env)
    assert decision.allowed == _expected(kind, pset, auth_granted, consent_given, visible, read_allowed)


@pytest.mark.parametrize("kind", [ActionKind.PRIMITIVE, ActionKind.DELEGATION])
@pytest.mark.parametrize("consent_given", _BOOLS)
@pytest.mark.parametrize("visible", _BOOLS)
@pytest.mark.parametrize("read_allowed", _BOOLS)
def test_auth_denial_dominates(kind: ActionKind, consent_given: bool, visible: bool, read_allowed: bool) -> None:
    env = _env(read_allowed)
    context = _ctx("single")
    action = _action(kind, visible=visible, env=env)
    consent_ids = frozenset({"a1"}) if consent_given else frozenset()
    pipeline = _pipeline(grants=frozenset(), consent_ids=consent_ids)
    decision = pipeline.decide(session=_SESSION, action=action, context=context, environment=env)
    assert not decision.allowed


@pytest.mark.parametrize("kind", [ActionKind.PRIMITIVE, ActionKind.NESTED, ActionKind.MESSAGE])
def test_consent_withheld_denies(kind: ActionKind) -> None:
    env = _env(True)
    context = _ctx("single")
    action = _action(kind, visible=True, env=env)
    pipeline = _pipeline(grants=_grants("single", True), consent_ids=frozenset())
    decision = pipeline.decide(session=_SESSION, action=action, context=context, environment=env)
    assert not decision.allowed


@pytest.mark.parametrize("kind", [ActionKind.PRIMITIVE, ActionKind.NESTED, ActionKind.MESSAGE])
def test_visibility_blocked_denies(kind: ActionKind) -> None:
    env = _env(True)
    context = _ctx("mixed")
    action = _action(kind, visible=False, env=env)
    pipeline = _pipeline(grants=_grants("mixed", True), consent_ids=frozenset({"a1"}))
    decision = pipeline.decide(session=_SESSION, action=action, context=context, environment=env)
    assert not decision.allowed


@pytest.mark.parametrize("kind", [ActionKind.PRIMITIVE, ActionKind.NESTED])
def test_read_denied_denies(kind: ActionKind) -> None:
    env = _env(False)
    context = _ctx("single")
    action = _action(kind, visible=True, env=env)
    pipeline = _pipeline(grants=_grants("single", True), consent_ids=frozenset({"a1"}))
    decision = pipeline.decide(session=_SESSION, action=action, context=context, environment=env)
    assert not decision.allowed


@pytest.mark.parametrize("kind", _KINDS)
def test_empty_context_denies_effect_actions(kind: ActionKind) -> None:
    env = _env(True)
    context = _ctx("empty")
    action = _action(kind, visible=True, env=env)
    pipeline = _pipeline(grants=_grants("empty", True), consent_ids=frozenset({"a1"}))
    decision = pipeline.decide(session=_SESSION, action=action, context=context, environment=env)
    if kind in (ActionKind.STOP, ActionKind.NO_OP):
        assert decision.allowed
    else:
        assert not decision.allowed


@pytest.mark.parametrize("denied", ["auth", "read", "visibility"])
def test_mixed_context_requires_all_principals(denied: str) -> None:
    if denied == "read":
        item = DataItem("doc", "v", frozenset({alice}), frozenset({alice}))
        env = EnvironmentSnapshot(id="env", data=(item,), resources=(_RESOURCE,))
    else:
        env = _env(True)
    context = _ctx("mixed")
    visible = denied != "visibility"
    action = _action(ActionKind.PRIMITIVE, visible=visible, env=env)
    grants = frozenset({PolicyGrant("alice", "write", "out")}) if denied == "auth" else _grants("mixed", True)
    pipeline = _pipeline(grants=grants, consent_ids=frozenset({"a1"}))
    decision = pipeline.decide(session=_SESSION, action=action, context=context, environment=env)
    assert not decision.allowed
