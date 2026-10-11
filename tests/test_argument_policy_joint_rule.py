"""One argument rule that constrains content origin and destination together.

The harness demo's own gateway is used for the end-to-end cases, so the call construction,
fixture, and annotations are the retained demonstration's. Only the installed policy differs.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from conflux.application import DecisionPipeline
from conflux.domain import (
    ActionArgument,
    ArgumentRole,
    EnvironmentSnapshot,
    OperationArgumentSchema,
    Permission,
    PrimitiveAction,
    Principal,
    Provenance,
    ResourceRef,
    fingerprint,
)
from conflux.experiments import harness_demo
from conflux.policy import (
    ArgumentPolicyGrant,
    ArgumentRequirement,
    ExplicitConsentPolicy,
    InMemoryArgumentAuthorisationPolicy,
    InMemoryAuthorisationPolicy,
    SessionVisibilityPolicy,
    SnapshotReadPolicy,
)
from conflux.ports import ProviderResult

pytestmark = pytest.mark.security


ALICE = Principal("alice", "agent")
TASK_ITEM = "item:task"
PRIVATE_ITEM = "item:private"
OUTSIDE = "outside-sink"
ENVIRONMENT = EnvironmentSnapshot("test", (), ())
REVIEWED_BODY = "status: ready"


class _StubExecutor:
    """ExecutorPort stand-in that records an authorised call instead of running an effect."""

    def __init__(self) -> None:
        """Start with no executed call."""
        self.calls: list[str] = []

    def execute(self, action: Any, *, certificate_id: str, action_fingerprint: str) -> ProviderResult:
        """Record the authorised action name."""
        _ = (certificate_id, action_fingerprint)
        self.calls.append(action.operation)
        return ProviderResult(True, outcome={"stub": True})


def _arguments(body: str, source: str | None, *, destination: str = OUTSIDE) -> tuple[ActionArgument, ...]:
    schema = OperationArgumentSchema(
        "post_json",
        "1",
        {"body": ArgumentRole.CONTENT, "destination": ArgumentRole.DESTINATION},
    )
    body_provenance = Provenance.from_principal(ALICE, source=source) if source else Provenance.unknown()
    return schema.bind(
        {
            "body": (body, body_provenance),
            "destination": (destination, Provenance.from_principal(ALICE, source=TASK_ITEM)),
        },
    )


def _action(arguments: tuple[ActionArgument, ...]) -> PrimitiveAction:
    return PrimitiveAction(
        "post_json",
        "post_json",
        Permission("send"),
        ResourceRef("test", OUTSIDE, "sink"),
        arguments=arguments,
        inputs=(),
    )


def _judge(grants: tuple[ArgumentPolicyGrant, ...], arguments: tuple[ActionArgument, ...]) -> Any:
    policy = InMemoryArgumentAuthorisationPolicy(frozenset(grants))
    destination = next(item for item in arguments if item.name == "destination")
    return policy.decide(ALICE, _action(arguments), destination, ENVIRONMENT)


def _destination_grant(*requirements: ArgumentRequirement, pinned: str | None = None) -> ArgumentPolicyGrant:
    return ArgumentPolicyGrant(
        ALICE.id,
        "post_json",
        "destination",
        ArgumentRole.DESTINATION,
        pinned,
        requirements,
    )


def test_a_joint_rule_refuses_private_content_at_an_outside_destination() -> None:
    """A rule on the destination that names the body's permitted source refuses the private send."""
    grant = _destination_grant(ArgumentRequirement("body", provenance_sources=frozenset({TASK_ITEM})))

    decision = _judge((grant,), _arguments("secret body", PRIVATE_ITEM))

    assert not decision.allowed
    assert decision.reason == "argument_requirement_denied"
    assert decision.evidence[-1] == "requires_failed:body"


def test_the_same_rule_allows_reviewed_content() -> None:
    """Reviewed content from the permitted source still reaches the same destination."""
    grant = _destination_grant(ArgumentRequirement("body", provenance_sources=frozenset({TASK_ITEM})))

    decision = _judge((grant,), _arguments(REVIEWED_BODY, TASK_ITEM))

    assert decision.allowed
    assert decision.reason == "argument_grant"
    assert decision.evidence == (
        ALICE.id,
        "post_json",
        "destination",
        "destination",
        fingerprint(OUTSIDE),
    )


def test_a_grant_without_requirements_keeps_its_decision_shape() -> None:
    """A grant with no requirements decides exactly as it did before the requirement field existed."""
    decision = _judge((_destination_grant(),), _arguments("secret body", PRIVATE_ITEM))

    assert decision.allowed
    assert decision.reason == "argument_grant"
    assert len(decision.evidence) == 5


def test_an_unconstrained_grant_defeats_a_requirement_on_the_same_argument() -> None:
    """Grants stay additive allowances, so a rule needs to be the only grant for that argument."""
    grants = (
        _destination_grant(),
        _destination_grant(ArgumentRequirement("body", provenance_sources=frozenset({TASK_ITEM}))),
    )

    decision = _judge(grants, _arguments("secret body", PRIVATE_ITEM))

    assert decision.allowed


def test_a_requirement_on_an_absent_argument_fails_closed() -> None:
    """A requirement that names an argument the action does not carry denies."""
    grant = _destination_grant(ArgumentRequirement("attachment", provenance_sources=frozenset({TASK_ITEM})))

    decision = _judge((grant,), _arguments(REVIEWED_BODY, TASK_ITEM))

    assert not decision.allowed
    assert decision.reason == "argument_requirement_denied"
    assert decision.evidence[-1] == "requires_failed:attachment"


def test_unknown_provenance_fails_closed() -> None:
    """Content whose provenance is unknown satisfies no source list."""
    grant = _destination_grant(ArgumentRequirement("body", provenance_sources=frozenset({TASK_ITEM})))

    decision = _judge((grant,), _arguments(REVIEWED_BODY, None))

    assert not decision.allowed
    assert decision.reason == "argument_requirement_denied"


def test_a_value_pin_requirement_denies_a_different_value() -> None:
    """A fingerprint requirement accepts the pinned value and refuses every other one."""
    pinned = ArgumentRequirement("body", value_fingerprint=fingerprint(REVIEWED_BODY))
    grant = _destination_grant(pinned)

    assert _judge((grant,), _arguments(REVIEWED_BODY, TASK_ITEM)).allowed
    refused = _judge((grant,), _arguments("different body", TASK_ITEM))
    assert not refused.allowed
    assert refused.reason == "argument_requirement_denied"


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"argument_name": ""}, "needs an argument name"),
        ({"argument_name": "body"}, "needs a provenance source list or a value fingerprint"),
        ({"argument_name": "body", "value_fingerprint": "not-a-digest"}, "fingerprint must be SHA-256"),
        ({"argument_name": "body", "provenance_sources": frozenset({""})}, "sources must be non-empty"),
    ],
)
def test_impossible_requirements_are_rejected(fields: dict[str, Any], message: str) -> None:
    """A requirement that could never hold, or that names nothing, is rejected at construction."""
    with pytest.raises(ValueError, match=message):
        _ = ArgumentRequirement(**fields)


def test_impossible_grants_are_rejected() -> None:
    """A grant cannot require the argument it grants, or carry the same requirement twice."""
    with pytest.raises(ValueError, match="cannot require the argument it grants"):
        _destination_grant(ArgumentRequirement("destination", provenance_sources=frozenset({TASK_ITEM})))
    duplicated = ArgumentRequirement("body", provenance_sources=frozenset({TASK_ITEM}))
    with pytest.raises(ValueError, match="duplicate requirements"):
        _destination_grant(duplicated, duplicated)


def _joint_rule_pipeline() -> Any:
    """Return the demonstration's pipeline with the owner's address grant replaced by a joint rule.

    The address role and the reviewed value come from the demonstration's own annotation table, so
    the test follows the shipped schema rather than a copy of it.
    """
    user = harness_demo.demo_principals()[0]
    schema = harness_demo.harness_annotations().operations["post_json"]
    destination_role = schema.roles["destination"]
    existing = frozenset(
        grant
        for grant in harness_demo.argument_grants()
        if not (grant.operation == "post_json" and grant.argument_name == "destination" and grant.principal_id == user.id)
    )
    joint = ArgumentPolicyGrant(
        user.id,
        "post_json",
        "destination",
        destination_role,
        None,
        (ArgumentRequirement("body", provenance_sources=frozenset({harness_demo.USER_TASK_ITEM})),),
    )
    return DecisionPipeline(
        InMemoryAuthorisationPolicy(harness_demo.envelope_grants()),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset(harness_demo.harness_annotations().operations)),
        InMemoryArgumentAuthorisationPolicy(existing | {joint}),
    )


def _run_gateway(monkeypatch: pytest.MonkeyPatch, call: harness_demo.ScriptedCall) -> tuple[dict[str, Any], _StubExecutor]:
    """Mediate one scripted call through the demonstration's gateway with the joint rule installed."""
    stub = _StubExecutor()
    monkeypatch.setattr(harness_demo, "demo_pipeline", _joint_rule_pipeline)
    gateway = harness_demo.HarnessGateway(policy_enabled=True, executor_factory=lambda _call: stub)
    gateway.mediate(call)
    return gateway.records[-1], stub


def test_the_demonstration_gateway_refuses_the_owners_private_send(monkeypatch: pytest.MonkeyPatch) -> None:
    """The joint rule blocks the owner's own send and leaves the effect boundary uncalled.

    The environment fixtures do not record a data-item identity in artifact provenance, so the
    requirement fails closed here. The rule therefore still refuses reviewed content under the
    demonstration's own fixture; recording item identity in provenance is a separate change.
    """
    call = harness_demo.ScriptedCall(
        101,
        "post_json",
        {"destination": harness_demo.OUTSIDE_DESTINATION, "body": harness_demo.SECRET_VALUE},
        {"destination": harness_demo.USER_TASK_ITEM, "body": harness_demo.PRIVATE_ITEM},
        "the task owner sends the private note to the outside address",
    )

    record, stub = _run_gateway(monkeypatch, call)

    assert record["outcome"] == "blocked"
    assert record["policy_dimension"] == "authorisation"
    assert record["policy_id"] == "in-memory-argument-policy"
    assert record["reason"] == "argument_denied"
    assert "requires_failed:body" in json.dumps(record, sort_keys=True)
    assert stub.calls == []
