"""Policy composition and canonical ITES semantics."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from conflux.application import DecisionPipeline, MediationService
from conflux.domain import (
    ActionVisibility,
    Artifact,
    DelegationAction,
    EnvironmentSnapshot,
    MessageAction,
    NestedExecutionAction,
    NoOpAction,
    Permission,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    ProposalBatch,
    ProposalMode,
    Provenance,
    ResourceRef,
    Session,
    StopAction,
)
from conflux.ites import BranchStatus, MediatingITES, TransitionKernel
from conflux.policy import ExplicitConsentPolicy
from conflux.ports import ProviderResult


def primitive(
    action_id: str,
    inputs: tuple[Artifact[Any], ...] = (),
    visibility: ActionVisibility = ActionVisibility.INTERNAL,
) -> PrimitiveAction:
    return PrimitiveAction(
        action_id,
        "write",
        Permission("write"),
        ResourceRef("test", "out", "document"),
        inputs,
        visibility,
    )


def test_empty_context_denies_effect(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    decision = pipeline.decide(
        session=session,
        action=primitive("write"),
        context=PrincipalContext(),
        environment=environment,
    )
    assert not decision.allowed
    assert {item.reason for item in decision.decisions} == {"empty_principal_context"}


def test_mixed_context_requires_every_principal(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    ungranted = Principal("mallory", "Mallory")
    decision = pipeline.decide(
        session=session,
        action=primitive("write"),
        context=PrincipalContext(frozenset({alice, ungranted})),
        environment=environment,
    )
    assert not decision.allowed
    assert decision.authorisation.reason == "principal_denied"


def test_reader_not_author_can_read(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    artifact = environment.data_item("shared-doc")
    assert artifact is not None
    decision = pipeline.decide(
        session=session,
        action=primitive("write", (artifact.to_artifact(),)),
        context=PrincipalContext(frozenset({alice})),
        environment=environment,
    )
    assert decision.read.allowed


def test_author_not_reader_is_denied(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    bob: Principal,
) -> None:
    item = environment.data_item("alice-doc")
    assert item is not None
    decision = pipeline.decide(
        session=session,
        action=primitive("write", (item.to_artifact(),)),
        context=PrincipalContext(frozenset({bob})),
        environment=environment,
    )
    assert not decision.read.allowed


def test_missing_consent_denies_effect(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    denied = replace(pipeline, consent=ExplicitConsentPolicy())
    decision = denied.decide(
        session=session,
        action=primitive("write"),
        context=PrincipalContext(frozenset({alice})),
        environment=environment,
    )
    assert not decision.consent.allowed
    assert decision.consent.reason == "missing_consent"


@pytest.mark.parametrize("action", [StopAction("stop"), NoOpAction("noop")])
def test_safe_internal_control_needs_no_context_or_consent(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    action: StopAction | NoOpAction,
) -> None:
    assert pipeline.decide(
        session=session,
        action=action,
        context=PrincipalContext(),
        environment=environment,
    ).allowed


def test_delegation_is_unsupported(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    decision = pipeline.decide(
        session=session,
        action=DelegationAction("delegate", "write:*"),
        context=PrincipalContext(frozenset({alice})),
        environment=environment,
    )
    assert not decision.allowed
    assert decision.authorisation.reason == "delegation_unsupported"


class StaticModel:
    def __init__(
        self,
        proposals: tuple[object, ...],
        mode: ProposalMode = ProposalMode.ALTERNATIVES,
    ) -> None:
        self.batch = ProposalBatch(mode, proposals)  # type: ignore[arg-type]

    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        _ = inputs
        return self.batch


def test_proposals_are_deterministic_isolated_branches(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
) -> None:
    source = environment.data_item("alice-doc")
    assert source is not None
    mediator = MediatingITES(TransitionKernel(pipeline))
    report = mediator.run(
        environment=environment,
        session=session,
        initial_inputs=(source.to_artifact(),),
        model=StaticModel((primitive("z"), primitive("write"))),
    )
    assert [branch.action.id for branch in report.branches if branch.action] == ["write", "z"]
    assert {branch.parent_branch_id for branch in report.branches} == {"root"}


def test_nested_execution_accumulates_provenance_and_hits_bound(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    shared = environment.data_item("shared-doc")
    assert shared is not None
    report = MediatingITES(TransitionKernel(pipeline)).run(
        environment=environment,
        session=session,
        initial_inputs=(shared.to_artifact(),),
        model=StaticModel((NestedExecutionAction("nested", (shared.to_artifact(),)),)),
        max_model_calls=1,
    )
    assert report.incomplete
    assert report.branches[0].status is BranchStatus.INCOMPLETE


def test_ordered_plan_preserves_order_and_retains_every_certificate(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    item = environment.data_item("shared-doc")
    assert item is not None
    ordered_pipeline = replace(
        pipeline,
        consent=ExplicitConsentPolicy(frozenset({"second", "first"})),
    )
    report = MediatingITES(TransitionKernel(ordered_pipeline)).run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=StaticModel(
            (primitive("second"), primitive("first")),
            ProposalMode.ORDERED_PLAN,
        ),
    )
    branch = report.branches[0]
    assert branch.status is BranchStatus.AUTHORISED
    assert [step.action.id for step in branch.authorised_steps] == ["second", "first"]
    assert len({step.certificate.id for step in branch.authorised_steps}) == 2
    assert report.authorised_plans[0].branch_id == branch.branch_id


def test_ordered_plan_stops_at_first_denial(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    item = environment.data_item("shared-doc")
    assert item is not None
    denied = PrimitiveAction(
        "denied",
        "delete",
        Permission("delete"),
        ResourceRef("test", "out", "document"),
    )
    ordered_pipeline = replace(
        pipeline,
        consent=ExplicitConsentPolicy(frozenset({"allowed", "denied", "not-observed"})),
    )
    report = MediatingITES(TransitionKernel(ordered_pipeline)).run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=StaticModel(
            (primitive("allowed"), denied, primitive("not-observed")),
            ProposalMode.ORDERED_PLAN,
        ),
    )
    branch = report.branches[0]
    assert branch.status is BranchStatus.BLOCKED
    assert [step.action.id for step in branch.authorised_steps] == ["allowed"]
    assert [event.action.id for event in branch.trace if event.action] == [
        "allowed",
        "allowed",
        "denied",
        "denied",
    ]


def test_blocked_proposal_does_not_break_execution_guarantee(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    unknown = Artifact("unknown", "x", Provenance.unknown())
    report = MediatingITES(TransitionKernel(pipeline)).run(
        environment=environment,
        session=session,
        initial_inputs=(unknown,),
        model=StaticModel((primitive("write"),)),
    )
    assert report.blocked_count == 1
    assert next(item for item in report.assessments if item.name == "no_unauthorised_execution").holds


class Executor:
    def execute(self, action: object, *, certificate_id: str, action_fingerprint: str) -> ProviderResult:
        _ = action, certificate_id, action_fingerprint
        return ProviderResult(True, "ok")


def test_execution_requires_matching_certificate(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    item = environment.data_item("shared-doc")
    assert item is not None
    mediator = MediatingITES(TransitionKernel(pipeline))
    report = mediator.run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=StaticModel((primitive("write"),)),
    )
    branch = report.authorised_branches[0]
    service = MediationService(mediator)
    result = service.execute(report=report, branch=branch, executor=Executor())
    assert result.provider.success
    assert result.report.executed_count == 1
    assert result.report.authorised_count == 0
    tampered = replace(branch, action=primitive("different"))
    rejected = service.execute(report=report, branch=tampered, executor=Executor())
    assert rejected.provider.error == "certificate_action_mismatch"
    assert rejected.report.executed_count == 0


def test_provider_failure_is_recorded_separately(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    class FailedExecutor:
        def execute(
            self,
            action: object,
            *,
            certificate_id: str,
            action_fingerprint: str,
        ) -> ProviderResult:
            _ = action, certificate_id, action_fingerprint
            return ProviderResult(False, error="provider_unavailable")

    item = environment.data_item("shared-doc")
    assert item is not None
    mediator = MediatingITES(TransitionKernel(pipeline))
    report = mediator.run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=StaticModel((primitive("write"),)),
    )
    branch = report.authorised_branches[0]
    result = MediationService(mediator).execute(
        report=report,
        branch=branch,
        executor=FailedExecutor(),
    )
    assert not result.provider.success
    assert result.report.provider_failed_count == 1
    assert result.report.executed_count == 0


def test_report_is_deterministically_serialisable(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    item = environment.data_item("shared-doc")
    assert item is not None
    mediator = MediatingITES(TransitionKernel(pipeline))
    first = mediator.run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=StaticModel((MessageAction("message", "hello"),)),
    )
    second = mediator.run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=StaticModel((MessageAction("message", "hello"),)),
    )
    assert first.to_dict() == second.to_dict()


def test_no_proposals_complete_and_model_errors_fail_closed(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    item = environment.data_item("shared-doc")
    assert item is not None
    mediator = MediatingITES(TransitionKernel(pipeline))
    complete = mediator.run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=StaticModel(()),
    )
    assert complete.branches[0].status is BranchStatus.TERMINAL

    class BrokenModel:
        def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
            raise RuntimeError("broken")

    blocked = mediator.run(
        environment=environment,
        session=session,
        initial_inputs=(item.to_artifact(),),
        model=BrokenModel(),
    )
    assert blocked.branches[0].status is BranchStatus.BLOCKED


def test_mediation_service_rejects_raw_inputs(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    service = MediationService(MediatingITES(TransitionKernel(pipeline)))
    with pytest.raises(TypeError, match="Artifacts"):
        service.evaluate(
            environment=environment,
            session=session,
            initial_inputs=("raw",),
            model=StaticModel(()),
        )
