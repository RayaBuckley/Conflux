"""Security-oriented tests for dynamic-plan contracts and provenance."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator

from conflux.domain import READ, WRITE, Artifact, Principal, Provenance
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    ArtifactBinding,
    BindingEnvironment,
    BranchNode,
    ContinuationRequest,
    ContinuePlanningNode,
    HistoricalNodeStatus,
    LiteralBinding,
    LoopNode,
    NodeOutputBinding,
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
    apply_patch,
    ground_action,
    parse_plan,
    parse_plan_patch,
)

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.security


def provenance(*principals: Principal, source: str = "fixture") -> Provenance:
    return Provenance(
        principals=frozenset(principals),
        sources=frozenset({source}),
    )


def write_operation() -> OperationSchema:
    return OperationSchema(
        id="filesystem.write",
        version="1",
        provider="filesystem",
        resource_type="file",
        operation="write",
        permission=WRITE,
        arguments=(
            ArgumentSpec("path", ArgumentType.STRING),
            ArgumentSpec("content", ArgumentType.STRING),
        ),
        resource_argument="path",
    )


def template(content_binding: object) -> ActionTemplate:
    assert isinstance(content_binding, (LiteralBinding, ArtifactBinding, NodeOutputBinding))
    return ActionTemplate(
        "write-readme",
        "filesystem.write",
        "1",
        (
            TemplateArgument(
                "path",
                LiteralBinding("README.md", Provenance.unknown(source="planner_literal")),
            ),
            TemplateArgument("content", content_binding),
        ),
    )


def test_authenticated_operation_catalogue_rejects_unknown_and_duplicate() -> None:
    operation = write_operation()
    catalogue = OperationCatalogue((operation,), identity="fixture")
    assert catalogue.resolve("filesystem.write", "1") is operation
    with pytest.raises(ValueError, match="unknown operation"):
        catalogue.resolve("free.text.operation", "1")
    with pytest.raises(ValueError, match="duplicate"):
        OperationCatalogue((operation, operation))


def test_grounding_resolves_literal_artifact_and_node_outputs_and_unions_provenance(
    alice: Principal,
    bob: Principal,
) -> None:
    source = Artifact("source", "hello", provenance(alice, source="source"))
    output = Artifact("model-output", "generated", provenance(bob, source="model"))
    environment = BindingEnvironment(
        {"source": source},
        {("model", "text"): output},
    )
    catalogue = OperationCatalogue((write_operation(),))
    invocation = provenance(alice, source="invocation")
    control = provenance(bob, source="control")

    from_artifact = ground_action(
        template(ArtifactBinding("source")),
        catalogue=catalogue,
        environment=environment,
        invocation_provenance=invocation,
        control_provenance=control,
    )
    from_output = ground_action(
        template(NodeOutputBinding("model", "text")),
        catalogue=catalogue,
        environment=environment,
        invocation_provenance=invocation,
        control_provenance=control,
    )

    assert from_artifact.provenance.principals == frozenset({alice, bob})
    assert from_output.provenance.principals == frozenset({alice, bob})
    resource = from_artifact.to_action().resource
    assert resource is not None
    assert resource.resource_id == "README.md"
    assert from_output.to_action().inputs[0].value == "generated"
    assert from_output.fingerprint == from_output.fingerprint


def test_grounding_fails_closed_on_missing_unknown_and_invalid_arguments(
    alice: Principal,
) -> None:
    catalogue = OperationCatalogue((write_operation(),))
    environment = BindingEnvironment({}, {})
    with pytest.raises(ValueError, match="missing operation arguments"):
        ground_action(
            ActionTemplate(
                "missing",
                "filesystem.write",
                "1",
                (
                    TemplateArgument(
                        "path",
                        LiteralBinding("x", provenance(alice)),
                    ),
                ),
            ),
            catalogue=catalogue,
            environment=environment,
            invocation_provenance=provenance(alice),
            control_provenance=provenance(alice),
        )
    with pytest.raises(ValueError, match="unknown operation arguments"):
        ground_action(
            ActionTemplate(
                "unknown",
                "filesystem.write",
                "1",
                (
                    TemplateArgument("path", LiteralBinding("x", provenance(alice))),
                    TemplateArgument("content", LiteralBinding("y", provenance(alice))),
                    TemplateArgument("surprise", LiteralBinding("z", provenance(alice))),
                ),
            ),
            catalogue=catalogue,
            environment=environment,
            invocation_provenance=provenance(alice),
            control_provenance=provenance(alice),
        )
    with pytest.raises(ValueError, match="must be string"):
        ground_action(
            template(LiteralBinding(7, provenance(alice))),
            catalogue=catalogue,
            environment=environment,
            invocation_provenance=provenance(alice),
            control_provenance=provenance(alice),
        )


def test_ground_action_is_immutable(alice: Principal) -> None:
    action = ground_action(
        template(LiteralBinding("content", provenance(alice))),
        catalogue=OperationCatalogue((write_operation(),)),
        environment=BindingEnvironment({}, {}),
        invocation_provenance=provenance(alice),
        control_provenance=provenance(alice),
    )
    with pytest.raises(FrozenInstanceError):
        action.id = "changed"  # type: ignore[misc]


def simple_plan(alice: Principal) -> Plan:
    source = provenance(alice)
    done = TerminalNode("done", TerminalOutcome.SUCCEEDED, "complete", source, ("write",))
    write = ActionTemplateNode(
        "write",
        template(LiteralBinding("hello", source)),
        source,
    )
    return Plan("repair", "repair repository", (write, done), source)


def test_plan_accepts_explicit_loop_and_rejects_dependency_cycle(alice: Principal) -> None:
    source = provenance(alice)
    body = TerminalNode("body", TerminalOutcome.SAFE_STOP, "body", source)
    exit_node = TerminalNode("exit", TerminalOutcome.SUCCEEDED, "exit", source)
    loop = LoopNode(
        "loop",
        LiteralBinding(True, source),
        "body",
        "exit",
        2,
        source,
    )
    plan = Plan("loop-plan", "loop", (loop, body, exit_node), source)
    assert plan.node("loop") is loop

    first = TerminalNode("a", TerminalOutcome.SAFE_STOP, "a", source, ("b",))
    second = TerminalNode("b", TerminalOutcome.SAFE_STOP, "b", source, ("a",))
    with pytest.raises(ValueError, match="implicit dependency cycle"):
        Plan("bad", "bad graph", (first, second), source)


def test_plan_validates_targets_and_is_deterministic(alice: Principal) -> None:
    source = provenance(alice)
    yes = TerminalNode("yes", TerminalOutcome.SUCCEEDED, "yes", source)
    no = TerminalNode("no", TerminalOutcome.SAFE_STOP, "no", source)
    branch = BranchNode(
        "branch",
        LiteralBinding(True, source),
        "yes",
        "no",
        source,
    )
    first = Plan("branch-plan", "branch", (yes, branch, no), source)
    second = Plan("branch-plan", "branch", (no, yes, branch), source)
    assert first.fingerprint == second.fingerprint
    with pytest.raises(ValueError, match="unknown targets"):
        Plan(
            "invalid",
            "invalid",
            (
                BranchNode(
                    "branch",
                    LiteralBinding(True, source),
                    "missing",
                    "no",
                    source,
                ),
                no,
            ),
            source,
        )


def test_patch_append_inherits_request_provenance(
    alice: Principal,
    bob: Principal,
) -> None:
    plan = simple_plan(alice)
    recovery = TerminalNode(
        "recovery",
        TerminalOutcome.SAFE_STOP,
        "recovered",
        provenance(alice),
    )
    patch = PlanPatch(
        "patch-1",
        plan.id,
        (PatchOperation("append", PatchKind.APPEND, nodes=(recovery,)),),
    )
    applied = apply_patch(
        plan,
        patch,
        history={},
        request_provenance=provenance(bob, source="untrusted-observation"),
    )
    inherited = applied.plan.node("recovery").control_provenance
    assert inherited.principals == frozenset({alice, bob})
    assert applied.added_node_ids == ("recovery",)


def test_patch_cannot_replace_completed_history(alice: Principal) -> None:
    plan = simple_plan(alice)
    replacement = TerminalNode(
        "replacement",
        TerminalOutcome.SAFE_STOP,
        "replacement",
        provenance(alice),
    )
    patch = PlanPatch(
        "patch-2",
        plan.id,
        (
            PatchOperation(
                "replace",
                PatchKind.REPLACE,
                nodes=(replacement,),
                target_node_ids=("write",),
            ),
        ),
    )
    with pytest.raises(ValueError, match="completed history"):
        apply_patch(
            plan,
            patch,
            history={"write": HistoricalNodeStatus.SUCCEEDED},
            request_provenance=provenance(alice),
        )


def test_patch_replaces_pending_subtree_and_can_terminate(alice: Principal) -> None:
    plan = simple_plan(alice)
    replacement = TerminalNode(
        "replacement",
        TerminalOutcome.SAFE_STOP,
        "replacement",
        provenance(alice),
    )
    patch = PlanPatch(
        "patch-3",
        plan.id,
        (
            PatchOperation(
                "a-replace",
                PatchKind.REPLACE,
                nodes=(replacement,),
                target_node_ids=("write",),
            ),
            PatchOperation(
                "z-stop",
                PatchKind.TERMINATE,
                terminal_outcome=TerminalOutcome.SAFE_STOP,
                terminal_reason="planner stopped",
            ),
        ),
    )
    applied = apply_patch(
        plan,
        patch,
        history={},
        request_provenance=provenance(alice),
    )
    assert set(applied.removed_node_ids) == {"write", "done"}
    assert applied.terminal_node_id is not None
    assert applied.plan.node(applied.terminal_node_id).kind.value == "terminal"


def test_continuation_request_unions_observation_provenance(
    alice: Principal,
    bob: Principal,
) -> None:
    plan = simple_plan(alice)
    observation = Artifact("error", "denied", provenance(bob))
    request = ContinuationRequest.create(
        request_id="continue-1",
        plan=plan,
        completed_node_ids=("write",),
        observations=(observation,),
        catalogue_fingerprint="catalogue",
        remaining_budgets=PlanBudgets(),
        trigger="blocked",
        control_provenance=provenance(alice),
    )
    assert request.provenance.principals == frozenset({alice, bob})
    assert request.fingerprint == request.fingerprint


def test_planning_request_and_schema_records_validate(alice: Principal) -> None:
    plan = simple_plan(alice)
    request = PlanningRequest(
        "initial-1",
        "repair",
        (),
        "catalogue",
        PlanBudgets(),
        provenance(alice),
    )
    assert request.fingerprint
    plan_schema = cast(
        dict[str, object],
        json.loads((ROOT / "schemas" / "plan.schema.json").read_text(encoding="utf-8")),
    )
    patch_schema = cast(
        dict[str, object],
        json.loads((ROOT / "schemas" / "plan-patch.schema.json").read_text(encoding="utf-8")),
    )
    Draft202012Validator(plan_schema).validate(plan.to_dict())
    patch = PlanPatch(
        "patch",
        plan.id,
        (
            PatchOperation(
                "terminate",
                PatchKind.TERMINATE,
                terminal_outcome=TerminalOutcome.SAFE_STOP,
                terminal_reason="done",
            ),
        ),
    )
    Draft202012Validator(patch_schema).validate(patch.to_dict())
    parsed_plan = parse_plan(
        plan.to_dict(),
        trusted_provenance=provenance(alice),
    )
    assert (
        parse_plan(
            parsed_plan.to_dict(),
            trusted_provenance=provenance(alice),
        ).fingerprint
        == parsed_plan.fingerprint
    )
    assert (
        parse_plan_patch(
            patch.to_dict(),
            trusted_provenance=provenance(alice),
        ).fingerprint
        == patch.fingerprint
    )


def test_parser_ignores_model_supplied_provenance(
    alice: Principal,
    bob: Principal,
) -> None:
    payload = simple_plan(alice).to_dict()
    parsed = parse_plan(payload, trusted_provenance=provenance(bob, source="planner-call"))
    assert parsed.invocation_provenance.principals == frozenset({bob})
    assert all(node.control_provenance.principals == frozenset({bob}) for node in parsed.nodes)


def test_parser_rejects_unknown_fields(alice: Principal) -> None:
    payload = simple_plan(alice).to_dict()
    payload["untrusted_extension"] = True
    with pytest.raises(ValueError, match="fields do not match schema"):
        parse_plan(payload, trusted_provenance=provenance(alice))


def test_operation_schema_rejects_invalid_resource_reference() -> None:
    with pytest.raises(ValueError, match="resource_argument"):
        OperationSchema(
            "read",
            "1",
            "filesystem",
            "file",
            "read",
            READ,
            (ArgumentSpec("other", ArgumentType.STRING),),
            resource_argument="path",
        )


def test_continuation_node_preserves_observation_bindings(alice: Principal) -> None:
    source = provenance(alice)
    node = ContinuePlanningNode(
        "continue",
        (ArtifactBinding("observation"),),
        "provider_failed",
        source,
    )
    assert node.observation_bindings == (ArtifactBinding("observation"),)
