"""Strict parsing of untrusted planner JSON into trusted-provenance types."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from conflux.domain import ActionVisibility, Provenance

from .actions import (
    ActionTemplate,
    ArtifactBinding,
    Binding,
    LiteralBinding,
    NodeOutputBinding,
    TemplateArgument,
)
from .continuation import (
    PATCH_SCHEMA_VERSION,
    PatchKind,
    PatchOperation,
    PlanPatch,
)
from .model import (
    PLAN_SCHEMA_VERSION,
    ActionTemplateNode,
    ApprovalNode,
    BranchNode,
    ContinuePlanningNode,
    DelegationNode,
    LoopNode,
    ModelCallNode,
    Plan,
    PlanNode,
    SubplanNode,
    TerminalNode,
    TerminalOutcome,
)


def parse_binding(value: object, *, trusted_provenance: Provenance) -> Binding:
    """Parse untrusted JSON into a validated Binding with trusted provenance."""
    payload = _object(value, "binding")
    kind = _string(payload.get("kind"), "binding.kind")
    if kind == "literal":
        _keys(payload, {"kind", "value", "provenance"}, "literal binding")
        return LiteralBinding(payload.get("value"), trusted_provenance)
    if kind == "artifact":
        _keys(payload, {"kind", "artifact_id"}, "artifact binding")
        return ArtifactBinding(_string(payload.get("artifact_id"), "artifact_id"))
    if kind == "node_output":
        _keys(payload, {"kind", "node_id", "output_name"}, "node-output binding")
        return NodeOutputBinding(
            _string(payload.get("node_id"), "node_id"),
            _string(payload.get("output_name"), "output_name"),
        )
    raise ValueError(f"unsupported binding kind: {kind}")


def parse_template(value: object, *, trusted_provenance: Provenance) -> ActionTemplate:
    """Parse untrusted JSON into a validated ActionTemplate."""
    payload = _object(value, "action template")
    _keys(
        payload,
        {"id", "operation_id", "operation_version", "arguments", "visibility"},
        "action template",
    )
    arguments: list[TemplateArgument] = []
    for item in _array(payload.get("arguments"), "template.arguments"):
        argument = _object(item, "template argument")
        _keys(argument, {"name", "binding"}, "template argument")
        arguments.append(
            TemplateArgument(
                _string(argument.get("name"), "argument.name"),
                parse_binding(
                    argument.get("binding"),
                    trusted_provenance=trusted_provenance,
                ),
            )
        )
    try:
        visibility = ActionVisibility(_string(payload.get("visibility"), "template.visibility"))
    except ValueError as error:
        raise ValueError("unsupported template visibility") from error
    return ActionTemplate(
        _string(payload.get("id"), "template.id"),
        _string(payload.get("operation_id"), "template.operation_id"),
        _string(payload.get("operation_version"), "template.operation_version"),
        tuple(arguments),
        visibility,
    )


def parse_node(value: object, *, trusted_provenance: Provenance) -> PlanNode:
    """Parse untrusted JSON into a validated PlanNode of the appropriate kind."""
    payload = _object(value, "plan node")
    kind = _string(payload.get("kind"), "node.kind")
    common = {"id", "kind", "dependencies", "control_provenance"}
    node_id = _string(payload.get("id"), "node.id")
    dependencies = tuple(_string(item, "node dependency") for item in _array(payload.get("dependencies"), "node.dependencies"))
    if kind == "model_call":
        _keys(payload, common | {"prompt", "output_name"}, "model-call node")
        return ModelCallNode(
            node_id,
            parse_binding(payload.get("prompt"), trusted_provenance=trusted_provenance),
            _string(payload.get("output_name"), "output_name"),
            trusted_provenance,
            dependencies,
        )
    if kind == "action_template":
        _keys(
            payload,
            common | {"template", "on_block", "on_failure", "output_name"},
            "action-template node",
        )
        return ActionTemplateNode(
            node_id,
            parse_template(
                payload.get("template"),
                trusted_provenance=trusted_provenance,
            ),
            trusted_provenance,
            dependencies,
            _optional_string(payload.get("on_block"), "on_block"),
            _optional_string(payload.get("on_failure"), "on_failure"),
            _string(payload.get("output_name"), "output_name"),
        )
    if kind == "branch":
        _keys(
            payload,
            common | {"condition", "when_true", "when_false"},
            "branch node",
        )
        return BranchNode(
            node_id,
            parse_binding(
                payload.get("condition"),
                trusted_provenance=trusted_provenance,
            ),
            _string(payload.get("when_true"), "when_true"),
            _string(payload.get("when_false"), "when_false"),
            trusted_provenance,
            dependencies,
        )
    if kind == "loop":
        _keys(
            payload,
            common
            | {
                "condition",
                "body_node_id",
                "exit_node_id",
                "max_iterations",
            },
            "loop node",
        )
        return LoopNode(
            node_id,
            parse_binding(
                payload.get("condition"),
                trusted_provenance=trusted_provenance,
            ),
            _string(payload.get("body_node_id"), "body_node_id"),
            _string(payload.get("exit_node_id"), "exit_node_id"),
            _integer(payload.get("max_iterations"), "max_iterations"),
            trusted_provenance,
            dependencies,
        )
    if kind == "continue_planning":
        _keys(
            payload,
            common | {"observation_bindings", "trigger"},
            "continuation node",
        )
        observations = tuple(
            parse_binding(item, trusted_provenance=trusted_provenance)
            for item in _array(
                payload.get("observation_bindings"),
                "observation_bindings",
            )
        )
        return ContinuePlanningNode(
            node_id,
            observations,
            _string(payload.get("trigger"), "trigger"),
            trusted_provenance,
            dependencies,
        )
    if kind == "approval":
        _keys(payload, common | {"request"}, "approval node")
        return ApprovalNode(
            node_id,
            _string(payload.get("request"), "request"),
            trusted_provenance,
            dependencies,
        )
    if kind == "delegation":
        _keys(payload, common | {"scope"}, "delegation node")
        return DelegationNode(
            node_id,
            _string(payload.get("scope"), "scope"),
            trusted_provenance,
            dependencies,
        )
    if kind == "subplan":
        _keys(payload, common | {"child_plan_id"}, "subplan node")
        return SubplanNode(
            node_id,
            _string(payload.get("child_plan_id"), "child_plan_id"),
            trusted_provenance,
            dependencies,
        )
    if kind == "terminal":
        _keys(payload, common | {"outcome", "reason"}, "terminal node")
        try:
            outcome = TerminalOutcome(_string(payload.get("outcome"), "outcome"))
        except ValueError as error:
            raise ValueError("unsupported terminal outcome") from error
        return TerminalNode(
            node_id,
            outcome,
            _string(payload.get("reason"), "reason"),
            trusted_provenance,
            dependencies,
        )
    raise ValueError(f"unsupported plan node kind: {kind}")


def parse_plan(value: object, *, trusted_provenance: Provenance) -> Plan:
    """Parse untrusted JSON into a validated Plan with subplans."""
    payload = _object(value, "plan")
    _keys(
        payload,
        {
            "schema_version",
            "id",
            "goal",
            "invocation_provenance",
            "nodes",
            "subplans",
        },
        "plan",
    )
    version = _string(payload.get("schema_version"), "plan.schema_version")
    if version != PLAN_SCHEMA_VERSION:
        raise ValueError(f"unsupported plan schema version: {version}")
    nodes = tuple(parse_node(item, trusted_provenance=trusted_provenance) for item in _array(payload.get("nodes"), "plan.nodes"))
    subplans = tuple(parse_plan(item, trusted_provenance=trusted_provenance) for item in _array(payload.get("subplans"), "plan.subplans"))
    return Plan(
        _string(payload.get("id"), "plan.id"),
        _string(payload.get("goal"), "plan.goal"),
        nodes,
        trusted_provenance,
        subplans,
        version,
    )


def parse_plan_patch(value: object, *, trusted_provenance: Provenance) -> PlanPatch:
    """Parse untrusted JSON into a validated PlanPatch."""
    payload = _object(value, "plan patch")
    _keys(payload, {"schema_version", "id", "plan_id", "operations"}, "plan patch")
    version = _string(payload.get("schema_version"), "patch.schema_version")
    if version != PATCH_SCHEMA_VERSION:
        raise ValueError(f"unsupported patch schema version: {version}")
    operations: list[PatchOperation] = []
    for item in _array(payload.get("operations"), "patch.operations"):
        operation = _object(item, "patch operation")
        _keys(
            operation,
            {
                "id",
                "kind",
                "nodes",
                "target_node_ids",
                "subplans",
                "terminal_outcome",
                "terminal_reason",
            },
            "patch operation",
        )
        try:
            kind = PatchKind(_string(operation.get("kind"), "operation.kind"))
        except ValueError as error:
            raise ValueError("unsupported patch operation") from error
        outcome_text = _optional_string(operation.get("terminal_outcome"), "terminal_outcome")
        outcome = TerminalOutcome(outcome_text) if outcome_text is not None else None
        operations.append(
            PatchOperation(
                _string(operation.get("id"), "operation.id"),
                kind,
                tuple(
                    parse_node(node, trusted_provenance=trusted_provenance) for node in _array(operation.get("nodes"), "operation.nodes")
                ),
                tuple(
                    _string(target, "target_node_id")
                    for target in _array(
                        operation.get("target_node_ids"),
                        "operation.target_node_ids",
                    )
                ),
                tuple(
                    parse_plan(plan, trusted_provenance=trusted_provenance)
                    for plan in _array(operation.get("subplans"), "operation.subplans")
                ),
                outcome,
                _string(operation.get("terminal_reason"), "terminal_reason", allow_empty=True),
            )
        )
    return PlanPatch(
        _string(payload.get("id"), "patch.id"),
        _string(payload.get("plan_id"), "patch.plan_id"),
        tuple(operations),
        version,
    )


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _array(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{label} must be an array")
    return cast(Sequence[object], value)


def _string(value: object, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not value and not allow_empty):
        raise ValueError(f"{label} must be a{' non-empty' if not allow_empty else ''} string")
    return value


def _optional_string(value: object, label: str) -> str | None:
    return None if value is None else _string(value, label)


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    return value


def _keys(payload: Mapping[str, object], expected: set[str], label: str) -> None:
    actual = set(payload)
    if actual != expected:
        raise ValueError(f"{label} fields do not match schema; missing={sorted(expected - actual)}, unknown={sorted(actual - expected)}")


__all__ = [
    "parse_binding",
    "parse_node",
    "parse_plan",
    "parse_plan_patch",
    "parse_template",
]
