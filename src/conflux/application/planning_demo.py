"""Deterministic dynamic-planning vertical slice used by CLI and CI."""

from __future__ import annotations

from conflux.adapters.models import ScriptedPlanner, ScriptedValueModel
from conflux.adapters.providers import InMemoryExecutor
from conflux.domain import (
    WRITE,
    EnvironmentSnapshot,
    Principal,
    Provenance,
    ResourceRef,
    Session,
)
from conflux.ites import MediatingITES, TransitionKernel
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    ContinuePlanningNode,
    DynamicPlanExecutor,
    DynamicPlanResult,
    LiteralBinding,
    OperationCatalogue,
    OperationSchema,
    PatchKind,
    PatchOperation,
    Plan,
    PlanBudgets,
    PlanningRequest,
    PlanPatch,
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

from .mediate import MediationService
from .policy import DecisionPipeline


def run_dynamic_planning_demo() -> DynamicPlanResult:
    """Run one blocked effect followed by a continuation-generated safe effect."""
    principal = Principal("demo-principal", "Demo Principal")
    provenance = Provenance.from_principal(principal, source="demo-invocation")
    catalogue = OperationCatalogue(
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
        identity="demo-catalogue",
    )
    continuation = ContinuePlanningNode(
        "continue-after-block",
        (),
        "policy_block",
        provenance,
    )
    blocked = ActionTemplateNode(
        "blocked-write",
        _write_template(
            "blocked-write",
            "forbidden.txt",
            "unsafe proposal",
            provenance,
        ),
        provenance,
        on_block=continuation.id,
    )
    initial = Plan(
        "dynamic-repair-demo",
        "repair a repository without exceeding authority",
        (blocked, continuation),
        provenance,
    )
    safe = ActionTemplateNode(
        "safe-write",
        _write_template(
            "safe-write",
            "safe.txt",
            "safe recovery",
            provenance,
        ),
        provenance,
    )
    done = TerminalNode(
        "safe-stop",
        TerminalOutcome.SAFE_STOP,
        "unsafe effect blocked; safe recovery executed",
        provenance,
        (safe.id,),
    )
    diagnostic = Plan(
        "diagnostic-subplan",
        "retain the recovery decision",
        (
            TerminalNode(
                "diagnostic-complete",
                TerminalOutcome.SUCCEEDED,
                "diagnostic retained",
                provenance,
            ),
        ),
        provenance,
    )
    patch = PlanPatch(
        "safe-recovery-patch",
        initial.id,
        (
            PatchOperation("append-recovery", PatchKind.APPEND, nodes=(safe, done)),
            PatchOperation(
                "spawn-diagnostic",
                PatchKind.SPAWN_SUBPLAN,
                subplans=(diagnostic,),
            ),
        ),
    )
    request = PlanningRequest(
        "dynamic-demo-request",
        initial.goal,
        (),
        catalogue.fingerprint,
        PlanBudgets(),
        provenance,
    )
    planner = ScriptedPlanner(
        {request.request_id: initial.to_dict()},
        {"*": patch.to_dict()},
    )
    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(
            frozenset({PolicyGrant(principal.id, "write", "safe.txt")})
        ),
        AllowInternalReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset({blocked.id, safe.id})),
    )
    runtime = DynamicPlanExecutor(
        planner,
        ScriptedValueModel({}),
        MediationService(MediatingITES(TransitionKernel(pipeline))),
        InMemoryExecutor(),
        catalogue,
        EnvironmentSnapshot(
            "dynamic-demo-environment",
            resources=(
                ResourceRef("filesystem", "safe.txt", "file"),
                ResourceRef("filesystem", "forbidden.txt", "file"),
            ),
        ),
        Session("dynamic-demo-session", frozenset({principal})),
        clock=lambda: 0.0,
    )
    return runtime.run(request)


def _write_template(
    action_id: str,
    path: str,
    content: str,
    provenance: Provenance,
) -> ActionTemplate:
    return ActionTemplate(
        action_id,
        "filesystem.write",
        "1",
        (
            TemplateArgument("path", LiteralBinding(path, provenance)),
            TemplateArgument("content", LiteralBinding(content, provenance)),
        ),
    )


__all__ = ["run_dynamic_planning_demo"]
