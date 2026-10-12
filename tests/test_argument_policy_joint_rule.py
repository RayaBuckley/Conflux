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


def _permitted_source(item_id: str) -> str:
    """Return the demonstration's own provenance source for one of its fixture items."""
    return next(item for item in harness_demo.fixture_items() if item.id == item_id).provenance_source


def _joint_rule_pipeline(permitted: frozenset[str] | None = None) -> Any:
    """Return the demonstration's pipeline with the owner's address grant replaced by a joint rule.

    The address role, the permitted source and the replaced grant all come from the demonstration's
    own tables, so the test follows the shipped schema rather than a copy of it.
    """
    user = harness_demo.demo_principals()[0]
    schema = harness_demo.harness_annotations().operations["post_json"]
    destination_role = schema.roles["destination"]
    existing = frozenset(
        grant
        for grant in harness_demo.argument_grants()
        if not (
            grant.operation == "post_json"
            and grant.argument_name == "destination"
            and grant.principal_id == user.id
        )
    )
    joint = ArgumentPolicyGrant(
        user.id,
        "post_json",
        "destination",
        destination_role,
        None,
        (
            ArgumentRequirement(
                "body",
                provenance_sources=(
                    permitted
                    if permitted is not None
                    else frozenset({_permitted_source(harness_demo.USER_TASK_ITEM)})
                ),
            ),
        ),
    )
    return DecisionPipeline(
        InMemoryAuthorisationPolicy(harness_demo.envelope_grants()),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset(harness_demo.harness_annotations().operations)),
        InMemoryArgumentAuthorisationPolicy(existing | {joint}),
    )


def _installed_gateway(
    monkeypatch: pytest.MonkeyPatch, pipeline: Any, *, fetch_page: bool = True,
) -> tuple[harness_demo.HarnessGateway, _StubExecutor]:
    """Return the demonstration's gateway with one pipeline installed and the page already fetched.

    The demonstration's own arm fetches the page before step one, so the page is in the environment
    and in the initial inputs of every step; the mixed-origin call declares that page as the source
    of one of its arguments. The page is left out only where a test isolates the argument dimension,
    because the page's authors are what the envelope refuses first.
    """
    stub = _StubExecutor()
    monkeypatch.setattr(harness_demo, "demo_pipeline", lambda: pipeline)
    gateway = harness_demo.HarnessGateway(policy_enabled=True, executor_factory=lambda _call: stub)
    if fetch_page:
        gateway.fetch_page()
    return gateway, stub


def _run_gateway(
    monkeypatch: pytest.MonkeyPatch, call: harness_demo.ScriptedCall, *, fetch_page: bool = False,
) -> tuple[dict[str, Any], _StubExecutor]:
    """Mediate one scripted call through the demonstration's gateway with the joint rule installed."""
    gateway, stub = _installed_gateway(monkeypatch, _joint_rule_pipeline(), fetch_page=fetch_page)
    gateway.mediate(call)
    return gateway.records[-1], stub


def _injected_send() -> harness_demo.ScriptedCall:
    """Return the demonstration's injection step as the task owner would have issued it.

    The owner's declared sources are the task item and the private note, so the call carries no
    page-influenced input: the argument dimension is left to decide it.
    """
    return harness_demo.ScriptedCall(
        101,
        "post_json",
        {"destination": harness_demo.OUTSIDE_DESTINATION, "body": harness_demo.SECRET_VALUE},
        {"destination": harness_demo.USER_TASK_ITEM, "body": harness_demo.PRIVATE_ITEM},
        "the task owner sends the private note to the outside address",
    )


def _mixed_origin_post() -> harness_demo.ScriptedCall:
    """Return an in-task post whose two arguments declare different origins.

    The body came from the item the task owner authored, and the address came from the fetched page,
    so the union of the call's inputs holds a source that belongs to neither argument on its own.
    """
    return harness_demo.ScriptedCall(
        102,
        "post_json",
        {"destination": harness_demo.TASK_DESTINATION, "body": harness_demo.TASK_BODY},
        {"destination": harness_demo.PAGE_ITEM, "body": harness_demo.USER_TASK_ITEM},
        "an in-task post whose address was taken from the fetched page",
    )


def test_the_origin_form_allows_the_benign_post(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same rule lets the in-task post run, because the demonstration declares its body origin.

    This is the half the rule could not decide before a data item named itself in its provenance:
    the body's declared source is the item the task owner authored, so the requirement holds.
    """
    call = harness_demo.demo_plan()[1]

    record, stub = _run_gateway(monkeypatch, call, fetch_page=True)

    assert record["outcome"] == "executed"
    assert stub.calls == ["post_json"]


def test_the_demonstration_gateway_refuses_the_owners_private_send(monkeypatch: pytest.MonkeyPatch) -> None:
    """The joint rule blocks the owner's own send and leaves the effect boundary uncalled."""
    record, stub = _run_gateway(monkeypatch, _injected_send())

    assert record["outcome"] == "blocked"
    assert record["policy_dimension"] == "authorisation"
    assert record["policy_id"] == "in-memory-argument-policy"
    assert record["reason"] == "argument_denied"
    assert "requires_failed:body" in json.dumps(record, sort_keys=True)
    assert stub.calls == []


def test_a_requirement_reads_each_arguments_own_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """A rule on the body accepts the origin the plan declares for that argument, not the call's union.

    The call's declared inputs hold the page's source as well, so a rule that read one provenance for
    the whole call would deny this call; judging the argument against the item the plan declares for
    it allows it, because the body's own source is the one the rule permits.
    """
    gateway, stub = _installed_gateway(
        monkeypatch, _joint_rule_pipeline(frozenset({_permitted_source(harness_demo.USER_TASK_ITEM)})),
    )

    gateway.mediate(_mixed_origin_post())

    assert gateway.records[-1]["outcome"] == "executed"
    assert stub.calls == ["post_json"]


def test_a_requirement_refuses_an_argument_from_another_item(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same rule refuses the call when it permits only the page's source for the body."""
    gateway, stub = _installed_gateway(
        monkeypatch, _joint_rule_pipeline(frozenset({_permitted_source(harness_demo.PAGE_ITEM)})),
    )

    gateway.mediate(_mixed_origin_post())

    assert gateway.records[-1]["outcome"] == "blocked"
    assert gateway.records[-1]["reason"] == "argument_denied"
    assert "requires_failed:body" in json.dumps(gateway.records[-1], sort_keys=True)
    assert stub.calls == []
