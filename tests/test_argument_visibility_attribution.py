"""Argument authority, audience disclosure, attribution, and their SLED monitors."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator

from conflux.application import DecisionPipeline
from conflux.domain import (
    ActionArgument,
    ArgumentRole,
    AttributionRecord,
    AudienceVisibilityDecision,
    DisclosureLevel,
    EnvironmentSnapshot,
    EventClass,
    OperationArgumentSchema,
    Permission,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    ProposalBatch,
    Provenance,
    ResourceRef,
    Session,
    action_to_dict,
    attribution_for_action,
    explain_attribution,
    fingerprint,
    project_record,
)
from conflux.evaluation import (
    ArgumentSelectorsAuthorised,
    CompleteAttribution,
    DisclosureMutation,
    DisclosureVerificationSystem,
    ExplicitStateChecker,
    NoHiddenDecisionLeakage,
    NoUnauthorisedSelector,
    SafeRedaction,
    VerificationVerdict,
)
from conflux.evaluation.model_checking import Transition
from conflux.ites import BranchState, BranchStatus, TransitionKernel
from conflux.policy import (
    ArgumentPolicyGrant,
    InMemoryArgumentAuthorisationPolicy,
    SessionAudienceVisibilityPolicy,
)

pytestmark = pytest.mark.security


ROOT = Path(__file__).resolve().parents[1]


def _selector(principal: Principal, value: str = "vault") -> ActionArgument:
    return ActionArgument.bind(
        name="destination",
        role=ArgumentRole.DESTINATION,
        value=value,
        provenance=Provenance.from_principal(principal, source="trusted-binding"),
    )


def _action(argument: ActionArgument) -> PrimitiveAction:
    return PrimitiveAction(
        "write",
        "write",
        Permission("write"),
        ResourceRef("test", "out", "document"),
        arguments=(argument,),
    )


def _with_argument_policy(
    pipeline: DecisionPipeline,
    *grants: ArgumentPolicyGrant,
) -> DecisionPipeline:
    return replace(
        pipeline,
        argument_authorisation=InMemoryArgumentAuthorisationPolicy(frozenset(grants)),
    )


def test_trusted_argument_schema_binds_roles_without_retaining_raw_values(
    alice: Principal,
) -> None:
    provenance = Provenance.from_principal(alice)
    schema = OperationArgumentSchema(
        "send",
        "1",
        {"body": ArgumentRole.CONTENT, "destination": ArgumentRole.DESTINATION},
    )
    arguments = schema.bind(
        {"body": ("secret body", provenance), "destination": ("vault", provenance)},
        redacted_values={"destination": "v***t"},
    )

    assert [item.role for item in arguments] == [ArgumentRole.CONTENT, ArgumentRole.DESTINATION]
    assert arguments[0].redacted_value is None
    assert arguments[1].redacted_value == "v***t"
    assert arguments[0].value_fingerprint == fingerprint("secret body")
    assert "secret body" not in json.dumps([item.to_dict() for item in arguments])
    with pytest.raises(FrozenInstanceError):
        arguments[0].name = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="binding mismatch"):
        schema.bind({"body": ("text", provenance)})
    with pytest.raises(ValueError, match="binding mismatch"):
        schema.bind(
            {
                "body": ("text", provenance),
                "destination": ("vault", provenance),
                "invented_role": ("x", provenance),
            },
        )


def test_argument_policy_is_pointwise_and_fail_closed(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
    bob: Principal,
) -> None:
    argument = _selector(alice)
    action = _action(argument)
    context = PrincipalContext(frozenset({alice, bob}))

    missing = pipeline.decide(
        session=session,
        action=action,
        context=context,
        environment=environment,
    )
    assert not missing.allowed
    assert missing.argument_authorisation is not None
    assert missing.argument_authorisation.reason == "argument_policy_unconfigured"

    alice_only = _with_argument_policy(
        pipeline,
        ArgumentPolicyGrant("alice", "write", "destination", ArgumentRole.DESTINATION),
    ).decide(session=session, action=action, context=context, environment=environment)
    assert not alice_only.allowed
    assert alice_only.argument_authorisation is not None
    assert alice_only.argument_authorisation.reason == "argument_denied"

    both = _with_argument_policy(
        pipeline,
        ArgumentPolicyGrant("alice", "write", "destination", ArgumentRole.DESTINATION),
        ArgumentPolicyGrant(
            "bob",
            "write",
            "destination",
            ArgumentRole.DESTINATION,
            argument.value_fingerprint,
        ),
    ).decide(session=session, action=action, context=context, environment=environment)
    assert both.allowed
    assert both.argument_authorisation is not None
    assert both.argument_authorisation.reason == "all_arguments_authorised"

    changed = _action(_selector(alice, "different-vault"))
    changed_decision = _with_argument_policy(
        pipeline,
        ArgumentPolicyGrant(
            "alice",
            "write",
            "destination",
            ArgumentRole.DESTINATION,
            argument.value_fingerprint,
        ),
        ArgumentPolicyGrant(
            "bob",
            "write",
            "destination",
            ArgumentRole.DESTINATION,
            argument.value_fingerprint,
        ),
    ).decide(session=session, action=changed, context=context, environment=environment)
    assert not changed_decision.allowed


def test_non_authority_content_does_not_require_selector_policy(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    content = ActionArgument.bind(
        name="body",
        role=ArgumentRole.CONTENT,
        value="hello",
        provenance=Provenance.from_principal(alice),
    )
    decision = pipeline.decide(
        session=session,
        action=_action(content),
        context=PrincipalContext(frozenset({alice})),
        environment=environment,
    )
    assert decision.allowed
    assert decision.argument_authorisation is None


def test_argument_provenance_expands_action_time_context(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
    bob: Principal,
) -> None:
    source = environment.data_item("alice-doc")
    assert source is not None
    argument = _selector(bob)
    secured = _with_argument_policy(
        pipeline,
        ArgumentPolicyGrant("alice", "write", "destination", ArgumentRole.DESTINATION),
        ArgumentPolicyGrant("bob", "write", "destination", ArgumentRole.DESTINATION),
    )
    branches = TransitionKernel(secured).expand_batch(
        parent=BranchState.initial((source.to_artifact(),)),
        environment=environment,
        session=session,
        batch=ProposalBatch.alternatives(_action(argument)),
        model_calls=1,
    )

    assert branches[0].decision is not None
    assert branches[0].decision.context.principals == frozenset({alice, bob})


@pytest.mark.parametrize(
    ("event_class", "audience_name", "expected"),
    [
        (EventClass.OUTPUT, "alice", DisclosureLevel.FULL),
        (EventClass.DECLARATION, "bob", DisclosureLevel.EXISTENCE),
        (EventClass.DECISION, "alice", DisclosureLevel.REDACTED),
        (EventClass.ERROR, "outsider", DisclosureLevel.NONE),
    ],
)
def test_visibility_is_decided_per_audience_and_event_class(
    event_class: EventClass,
    audience_name: str,
    expected: DisclosureLevel,
    alice: Principal,
    bob: Principal,
    session: Session,
) -> None:
    audience = {"alice": alice, "bob": bob}.get(audience_name, Principal("eve", "Eve"))
    decision = SessionAudienceVisibilityPolicy().decide(
        session,
        audience,
        event_class,
        None,
        PrincipalContext(frozenset({alice})),
    )
    assert decision.level is expected


def test_disclosure_projection_never_copies_hidden_payload(alice: Principal) -> None:
    record: dict[str, object] = {
        "schema_version": "3",
        "event_type": "action.failed",
        "event_class": "error",
        "event_id": "event-1",
        "run_id": "run-1",
        "branch_id": "branch-1",
        "sequence": 1,
        "timestamp": "2026-08-02T00:00:00Z",
        "payload": {"secret_value": "secret", "policy_detail": "hidden"},
    }
    base = AudienceVisibilityDecision(
        alice,
        EventClass.ERROR,
        DisclosureLevel.REDACTED,
        "test",
        "test-policy",
        "1",
    )
    first = project_record(record, base)
    assert first == project_record(record, base)
    serialized = json.dumps(first)
    assert "secret" not in serialized
    assert "hidden" not in serialized
    assert cast(dict[str, object], first)["payload"] == {
        "redacted": True,
        "payload_fingerprint": fingerprint(record["payload"]),
    }
    existence = project_record(record, replace(base, level=DisclosureLevel.EXISTENCE))
    assert existence is not None and "payload" not in existence
    assert project_record(record, replace(base, level=DisclosureLevel.NONE)) is None


def test_attribution_is_structured_conservative_and_model_text_is_untrusted(
    alice: Principal,
) -> None:
    argument = _selector(alice)
    record = attribution_for_action(
        _action(argument),
        PrincipalContext(frozenset({alice})),
        None,
        model_explanation="I chose this destination.",
    )
    assert record.conservative_influence.principals == frozenset({alice})
    assert record.redaction_requirements == ("destination",)
    assert not record.model_explanation_trusted
    assert explain_attribution(record, DisclosureLevel.REDACTED) == explain_attribution(record, DisclosureLevel.REDACTED)
    with pytest.raises(ValueError, match="cannot be marked trusted"):
        AttributionRecord((), PrincipalContext(), (), (), (), "claim", True)


def test_v2_action_certificate_and_v3_trace_validate(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    source = environment.data_item("alice-doc")
    assert source is not None
    action = _action(_selector(alice))
    secured = _with_argument_policy(
        pipeline,
        ArgumentPolicyGrant("alice", "write", "destination", ArgumentRole.DESTINATION),
    )
    branches = TransitionKernel(secured).expand_batch(
        parent=BranchState.initial((source.to_artifact(),)),
        environment=environment,
        session=session,
        batch=ProposalBatch.alternatives(action),
        model_calls=1,
    )
    branch = branches[0]
    assert branch.certificate is not None
    proposal_schema = json.loads((ROOT / "schemas" / "proposal-batch-v2.schema.json").read_text(encoding="utf-8"))
    certificate_schema = json.loads((ROOT / "schemas" / "decision-certificate.schema.json").read_text(encoding="utf-8"))
    attribution_schema = json.loads((ROOT / "schemas" / "attribution-record.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(proposal_schema).validate(ProposalBatch.alternatives(action).to_dict())
    Draft202012Validator(certificate_schema).validate(branch.certificate.to_dict())
    Draft202012Validator(attribution_schema).validate(branch.trace[-1].to_dict()["attribution"])
    assert action_to_dict(action)["schema_version"] == "2"
    assert branch.trace[-1].schema_version == "3"


def test_actual_selector_property_rejects_missing_argument_decision(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    source = environment.data_item("alice-doc")
    assert source is not None
    action = _action(_selector(alice))
    parent = BranchState.initial((source.to_artifact(),))
    base_decision = pipeline.decide(
        session=session,
        action=PrimitiveAction("write", "write", Permission("write"), ResourceRef("test", "out", "document")),
        context=PrincipalContext(frozenset({alice})),
        environment=environment,
    )
    defective = replace(parent, status=BranchStatus.AUTHORISED, action=action, decision=base_decision)
    reason = ArgumentSelectorsAuthorised().violation(Transition(parent, action, defective))
    assert reason == "an authority-bearing selector was authorised without argument policy"


@pytest.mark.parametrize(
    "mutation",
    [
        DisclosureMutation.UNAUTHORISED_SELECTOR,
        DisclosureMutation.HIDDEN_ERROR_LEAK,
        DisclosureMutation.INCOMPLETE_ATTRIBUTION,
        DisclosureMutation.UNSAFE_REDACTION,
    ],
)
def test_sled_kills_disclosure_mutants_with_minimal_witness(
    mutation: DisclosureMutation,
) -> None:
    properties = (
        NoUnauthorisedSelector(),
        NoHiddenDecisionLeakage(),
        CompleteAttribution(),
        SafeRedaction(),
    )
    result = ExplicitStateChecker().verify(DisclosureVerificationSystem(mutation), properties)
    assert result.verdict is VerificationVerdict.UNSAFE
    assert result.counterexample is not None
    assert result.counterexample.length == 1


def test_canonical_disclosure_monitor_is_safe() -> None:
    result = ExplicitStateChecker().verify(
        DisclosureVerificationSystem(),
        (
            NoUnauthorisedSelector(),
            NoHiddenDecisionLeakage(),
            CompleteAttribution(),
            SafeRedaction(),
        ),
    )
    assert result.verdict is VerificationVerdict.SAFE
