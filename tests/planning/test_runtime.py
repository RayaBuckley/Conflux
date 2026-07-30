"""Deterministic dynamic-plan execution and mediation tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from conflux.adapters.models import ScriptedPlanner, ScriptedValueModel
from conflux.adapters.providers import InMemoryExecutor
from conflux.application import DecisionPipeline, MediationService
from conflux.domain import (
    WRITE,
    Artifact,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    Principal,
    Provenance,
    ResourceRef,
    Session,
)
from conflux.evaluation import plan_trace_records, replay_plan_trace, write_plan_trace
from conflux.ites import MediatingITES, TransitionKernel
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    ContinuePlanningNode,
    DynamicPlanExecutor,
    LiteralBinding,
    LoopNode,
    NodeOutputBinding,
    NodeStatus,
    OperationCatalogue,
    OperationSchema,
    PatchKind,
    PatchOperation,
    Plan,
    PlanBudgets,
    PlanningRequest,
    PlanPatch,
    PlanRunStatus,
    TemplateArgument,
    TerminalNode,
    TerminalOutcome,
)
from conflux.policy import (
    AllowInternalReadPolicy,
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
)
from conflux.ports import AuthorisationPort


def source(principal: Principal, label: str = "fixture") -> Provenance:
    return Provenance.from_principal(principal, source=label)


def catalogue() -> OperationCatalogue:
    return OperationCatalogue(
        (
            OperationSchema(
                "filesystem.write",
                "1",
                "filesystem",
                "file",
                "write",
                WRITE,
                (
                    ArgumentSpec("path", ArgumentType.STRING),
                    ArgumentSpec("content", ArgumentType.STRING),
                ),
                "path",
            ),
        ),
        identity="runtime-fixture",
    )


def write_template(
    action_id: str,
    path: str,
    content: LiteralBinding | NodeOutputBinding,
    principal: Principal,
) -> ActionTemplate:
    return ActionTemplate(
        action_id,
        "filesystem.write",
        "1",
        (
            TemplateArgument("path", LiteralBinding(path, source(principal))),
            TemplateArgument("content", content),
        ),
    )


def executor(
    *,
    alice: Principal,
    planner: ScriptedPlanner,
    value_model: ScriptedValueModel,
    provider: InMemoryExecutor,
    grants: frozenset[PolicyGrant],
    consent: frozenset[str],
    budgets: PlanBudgets = PlanBudgets(),
    authorisation: AuthorisationPort | None = None,
) -> DynamicPlanExecutor:
    pipeline = DecisionPipeline(
        authorisation=authorisation or InMemoryAuthorisationPolicy(grants),
        read=AllowInternalReadPolicy(),
        visibility=SessionVisibilityPolicy(),
        consent=ExplicitConsentPolicy(consent),
    )
    return DynamicPlanExecutor(
        planner,
        value_model,
        MediationService(MediatingITES(TransitionKernel(pipeline))),
        provider,
        catalogue(),
        EnvironmentSnapshot(
            "plan-env",
            resources=(
                ResourceRef("filesystem", "safe.txt", "file"),
                ResourceRef("filesystem", "forbidden.txt", "file"),
            ),
        ),
        Session("plan-session", frozenset({alice})),
        budgets,
        clock=lambda: 0.0,
    )


def test_scripted_planner_reports_malformed_output(alice: Principal) -> None:
    planner = ScriptedPlanner({"request": {"bad": True}}, {})
    request = PlanningRequest(
        "request",
        "repair",
        (),
        catalogue().fingerprint,
        PlanBudgets(),
        source(alice),
    )
    response = planner.initial_plan(request)
    assert response.plan is None
    assert response.record.error is not None
    assert response.record.raw_response == '{"bad":true}'


def test_model_value_binds_later_mediated_action(alice: Principal) -> None:
    provenance = source(alice)
    value_node_id = "draft"
    action = ActionTemplateNode(
        "safe-write",
        write_template(
            "safe-write",
            "safe.txt",
            NodeOutputBinding(value_node_id, "text"),
            alice,
        ),
        provenance,
        (value_node_id,),
    )
    from conflux.planning import ModelCallNode

    value_node = ModelCallNode(
        value_node_id,
        LiteralBinding("write a repair", provenance),
        "text",
        provenance,
    )
    terminal = TerminalNode(
        "done",
        TerminalOutcome.SUCCEEDED,
        "complete",
        provenance,
        ("safe-write",),
    )
    plan = Plan("value-plan", "repair", (terminal, action, value_node), provenance)
    provider = InMemoryExecutor()
    runtime = executor(
        alice=alice,
        planner=ScriptedPlanner({}, {}),
        value_model=ScriptedValueModel(
            {
                value_node_id: Artifact(
                    "scripted-output",
                    "generated repair",
                    provenance,
                )
            }
        ),
        provider=provider,
        grants=frozenset({PolicyGrant("alice", "write", "safe.txt")}),
        consent=frozenset({"safe-write"}),
    )
    result = runtime.execute(plan)
    assert result.completed
    assert result.state.status == PlanRunStatus.SUCCEEDED
    assert result.state.node_outputs()[("draft", "text")].value == "generated repair"
    assert len(provider.outcomes) == 1
    assert result.mediation_reports[0].executed_count == 1


def test_blocked_effect_continues_with_patch_and_executes_safe_effect(
    alice: Principal,
) -> None:
    provenance = source(alice)
    continuation = ContinuePlanningNode(
        "continue",
        (),
        "blocked",
        provenance,
    )
    blocked = ActionTemplateNode(
        "unsafe",
        write_template(
            "unsafe",
            "forbidden.txt",
            LiteralBinding("unsafe", provenance),
            alice,
        ),
        provenance,
        on_block="continue",
    )
    initial = Plan("repair-plan", "repair", (blocked, continuation), provenance)

    safe = ActionTemplateNode(
        "safe",
        write_template(
            "safe",
            "safe.txt",
            LiteralBinding("safe repair", provenance),
            alice,
        ),
        provenance,
    )
    done = TerminalNode(
        "done",
        TerminalOutcome.SAFE_STOP,
        "recovered",
        provenance,
        ("safe",),
    )
    child = Plan(
        "diagnostic-subplan",
        "record recovery",
        (
            TerminalNode(
                "child-done",
                TerminalOutcome.SUCCEEDED,
                "recorded",
                provenance,
            ),
        ),
        provenance,
    )
    patch = PlanPatch(
        "recovery-patch",
        initial.id,
        (
            PatchOperation("append", PatchKind.APPEND, nodes=(safe, done)),
            PatchOperation("spawn", PatchKind.SPAWN_SUBPLAN, subplans=(child,)),
        ),
    )
    planner = ScriptedPlanner({}, {"*": patch.to_dict()})
    provider = InMemoryExecutor()
    runtime = executor(
        alice=alice,
        planner=planner,
        value_model=ScriptedValueModel({}),
        provider=provider,
        grants=frozenset({PolicyGrant("alice", "write", "safe.txt")}),
        consent=frozenset({"unsafe", "safe"}),
    )
    result = runtime.execute(initial)

    assert result.completed
    assert result.state.status == PlanRunStatus.SAFE_STOP
    assert result.state.node_state("unsafe").status == NodeStatus.BLOCKED
    assert result.state.node_state("safe").status == NodeStatus.SUCCEEDED
    assert result.state.plan.subplans[0].id == "diagnostic-subplan"
    assert len(result.mediation_reports) == 2
    assert result.mediation_reports[0].blocked_count == 1
    assert result.mediation_reports[1].executed_count == 1
    event_types = [event.event_type for event in result.state.events]
    assert "plan.continuation_requested" in event_types
    assert "plan.patch_applied" in event_types
    assert list(provider.certificate_bindings.values())

    replayed_plan, replayed_nodes = replay_plan_trace(initial.to_dict(), result.state.events)
    assert replayed_plan == result.state.plan.to_dict()
    assert replayed_nodes == tuple(item.to_dict() for item in result.state.nodes)
    records = plan_trace_records(result.state)
    assert records == plan_trace_records(result.state)
    assert all(record["plan_id"] == result.state.plan.id for record in records)


def test_plan_trace_writer_is_byte_deterministic(
    tmp_path: Path,
    alice: Principal,
) -> None:
    provenance = source(alice)
    plan = Plan(
        "trace-plan",
        "trace",
        (
            TerminalNode(
                "done",
                TerminalOutcome.SUCCEEDED,
                "done",
                provenance,
            ),
        ),
        provenance,
    )
    runtime = executor(
        alice=alice,
        planner=ScriptedPlanner({}, {}),
        value_model=ScriptedValueModel({}),
        provider=InMemoryExecutor(),
        grants=frozenset(),
        consent=frozenset(),
    )
    result = runtime.execute(plan)
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    assert write_plan_trace(result.state, first) == write_plan_trace(result.state, second)
    assert first.read_bytes() == second.read_bytes()


def test_malformed_patch_fails_closed_without_provider_effect(alice: Principal) -> None:
    provenance = source(alice)
    continuation = ContinuePlanningNode("continue", (), "manual", provenance)
    plan = Plan("malformed", "repair", (continuation,), provenance)
    planner = ScriptedPlanner({}, {"*": {"schema_version": "999"}})
    provider = InMemoryExecutor()
    result = executor(
        alice=alice,
        planner=planner,
        value_model=ScriptedValueModel({}),
        provider=provider,
        grants=frozenset(),
        consent=frozenset(),
    ).execute(plan)
    assert not result.completed
    assert result.state.failure_category == "plan_patch_invalid"
    assert not provider.outcomes
    assert result.state.events[-2].event_type == "plan.patch_rejected"


@dataclass
class RevokingAuthorisation:
    calls: int = 0
    policy_id: str = "revoking-policy"
    policy_version: str = "1"

    def decide(
        self,
        principal: Principal,
        action: object,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        _ = principal, action, environment
        self.calls += 1
        return Decision(
            DecisionCategory.AUTHORISATION,
            self.calls == 1,
            "initial_grant" if self.calls == 1 else "revoked",
            self.policy_id,
            self.policy_version,
        )


def test_policy_revocation_between_grounding_and_effect_is_honoured(
    alice: Principal,
) -> None:
    provenance = source(alice)
    action = ActionTemplateNode(
        "safe",
        write_template(
            "safe",
            "safe.txt",
            LiteralBinding("content", provenance),
            alice,
        ),
        provenance,
    )
    plan = Plan("revocation", "test revocation", (action,), provenance)
    provider = InMemoryExecutor()
    result = executor(
        alice=alice,
        planner=ScriptedPlanner({}, {}),
        value_model=ScriptedValueModel({}),
        provider=provider,
        grants=frozenset(),
        consent=frozenset({"safe"}),
        authorisation=RevokingAuthorisation(),
    ).execute(plan)
    assert not result.completed
    assert result.state.status == PlanRunStatus.FAILED
    assert result.state.node_state("safe").reason == "execution_reauthorisation_denied"
    assert not provider.outcomes
    assert result.mediation_reports[0].blocked_count == 1


def test_loop_bound_is_explicit_and_does_not_claim_completion(alice: Principal) -> None:
    provenance = source(alice)
    body = ActionTemplateNode(
        "body",
        write_template(
            "body",
            "safe.txt",
            LiteralBinding("iteration", provenance),
            alice,
        ),
        provenance,
    )
    exit_node = TerminalNode(
        "exit",
        TerminalOutcome.SUCCEEDED,
        "exit",
        provenance,
    )
    loop = LoopNode(
        "loop",
        LiteralBinding(True, provenance),
        "body",
        "exit",
        1,
        provenance,
    )
    plan = Plan("bounded-loop", "loop", (loop, body, exit_node), provenance)
    result = executor(
        alice=alice,
        planner=ScriptedPlanner({}, {}),
        value_model=ScriptedValueModel({}),
        provider=InMemoryExecutor(),
        grants=frozenset({PolicyGrant("alice", "write", "safe.txt")}),
        consent=frozenset({"body"}),
    ).execute(plan)
    assert not result.completed
    assert result.state.status == PlanRunStatus.INCOMPLETE
    assert result.state.failure_category == "loop_iteration_bound"
    assert result.state.effects == 1


def test_authenticated_outcome_contract_blocks_malformed_provider_result(
    alice: Principal,
) -> None:
    provenance = source(alice)
    operation = OperationSchema(
        "filesystem.write",
        "1",
        "filesystem",
        "file",
        "write",
        WRITE,
        (
            ArgumentSpec("path", ArgumentType.STRING),
            ArgumentSpec("content", ArgumentType.STRING),
        ),
        "path",
        ArgumentType.STRING,
    )
    action = ActionTemplateNode(
        "contracted-write",
        ActionTemplate(
            "contracted-write",
            operation.id,
            operation.version,
            (
                TemplateArgument(
                    "path",
                    LiteralBinding("safe.txt", provenance),
                ),
                TemplateArgument(
                    "content",
                    LiteralBinding("content", provenance),
                ),
            ),
        ),
        provenance,
    )
    plan = Plan("outcome-contract", "validate provider output", (action,), provenance)
    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(
            frozenset({PolicyGrant("alice", "write", "safe.txt")})
        ),
        AllowInternalReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset({action.id})),
    )
    result = DynamicPlanExecutor(
        ScriptedPlanner({}, {}),
        ScriptedValueModel({}),
        MediationService(MediatingITES(TransitionKernel(pipeline))),
        InMemoryExecutor(),
        OperationCatalogue((operation,)),
        EnvironmentSnapshot(
            "contract-env",
            resources=(ResourceRef("filesystem", "safe.txt", "file"),),
        ),
        Session("contract-session", frozenset({alice})),
        clock=lambda: 0.0,
    ).execute(plan)
    assert not result.completed
    assert result.state.failure_category == "outcome_contract_violation"
    assert result.state.node_state(action.id).status == NodeStatus.FAILED
