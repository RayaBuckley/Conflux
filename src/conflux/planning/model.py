"""Immutable open-ended plan graph and typed node taxonomy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias

from conflux.domain import Provenance, fingerprint

from .actions import ActionTemplate, Binding

PLAN_SCHEMA_VERSION = "1"


class NodeKind(StrEnum):
    MODEL_CALL = "model_call"
    ACTION_TEMPLATE = "action_template"
    BRANCH = "branch"
    LOOP = "loop"
    CONTINUE_PLANNING = "continue_planning"
    APPROVAL = "approval"
    DELEGATION = "delegation"
    SUBPLAN = "subplan"
    TERMINAL = "terminal"


class TerminalOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    SAFE_STOP = "safe_stop"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ModelCallNode:
    id: str
    prompt: Binding
    output_name: str
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.MODEL_CALL, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.output_name:
            raise ValueError("model-call output name must be non-empty")


@dataclass(frozen=True, slots=True)
class ActionTemplateNode:
    id: str
    template: ActionTemplate
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    on_block: str | None = None
    on_failure: str | None = None
    output_name: str = "result"
    kind: NodeKind = field(default=NodeKind.ACTION_TEMPLATE, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.output_name:
            raise ValueError("action output name must be non-empty")


@dataclass(frozen=True, slots=True)
class BranchNode:
    id: str
    condition: Binding
    when_true: str
    when_false: str
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.BRANCH, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.when_true or not self.when_false:
            raise ValueError("branch targets must be non-empty")


@dataclass(frozen=True, slots=True)
class LoopNode:
    id: str
    condition: Binding
    body_node_id: str
    exit_node_id: str
    max_iterations: int
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.LOOP, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.body_node_id or not self.exit_node_id:
            raise ValueError("loop body and exit targets must be non-empty")
        if self.max_iterations < 1:
            raise ValueError("loop max_iterations must be positive")


@dataclass(frozen=True, slots=True)
class ContinuePlanningNode:
    id: str
    observation_bindings: tuple[Binding, ...]
    trigger: str
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.CONTINUE_PLANNING, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        object.__setattr__(self, "observation_bindings", tuple(self.observation_bindings))
        if not self.trigger:
            raise ValueError("continuation trigger must be non-empty")


@dataclass(frozen=True, slots=True)
class ApprovalNode:
    id: str
    request: str
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.APPROVAL, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.request:
            raise ValueError("approval request must be non-empty")


@dataclass(frozen=True, slots=True)
class DelegationNode:
    id: str
    scope: str
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.DELEGATION, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.scope:
            raise ValueError("delegation scope must be non-empty")


@dataclass(frozen=True, slots=True)
class SubplanNode:
    id: str
    child_plan_id: str
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.SUBPLAN, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.child_plan_id:
            raise ValueError("subplan node requires a child plan id")


@dataclass(frozen=True, slots=True)
class TerminalNode:
    id: str
    outcome: TerminalOutcome
    reason: str
    control_provenance: Provenance
    dependencies: tuple[str, ...] = ()
    kind: NodeKind = field(default=NodeKind.TERMINAL, init=False)

    def __post_init__(self) -> None:
        _validate_node(self.id, self.dependencies, self.control_provenance)
        if not self.reason:
            raise ValueError("terminal reason must be non-empty")


PlanNode: TypeAlias = (
    ModelCallNode
    | ActionTemplateNode
    | BranchNode
    | LoopNode
    | ContinuePlanningNode
    | ApprovalNode
    | DelegationNode
    | SubplanNode
    | TerminalNode
)


@dataclass(frozen=True, slots=True)
class Plan:
    id: str
    goal: str
    nodes: tuple[PlanNode, ...]
    invocation_provenance: Provenance
    subplans: tuple["Plan", ...] = ()
    schema_version: str = PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.id or not self.goal:
            raise ValueError("plan id and goal must be non-empty")
        if self.schema_version != PLAN_SCHEMA_VERSION:
            raise ValueError(f"unsupported plan schema version: {self.schema_version}")
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "subplans", tuple(self.subplans))
        _validate_graph(self.nodes, self.subplans)

    @property
    def node_ids(self) -> frozenset[str]:
        return frozenset(node.id for node in self.nodes)

    def node(self, node_id: str) -> PlanNode:
        try:
            return next(node for node in self.nodes if node.id == node_id)
        except StopIteration as error:
            raise ValueError(f"unknown plan node: {node_id}") from error

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "goal": self.goal,
            "invocation_provenance": self.invocation_provenance.to_dict(),
            "nodes": [
                node_to_dict(node)
                for node in sorted(self.nodes, key=lambda item: (item.id, node_fingerprint(item)))
            ],
            "subplans": [
                plan.to_dict() for plan in sorted(self.subplans, key=lambda item: item.id)
            ],
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


def _validate_node(
    node_id: str,
    dependencies: tuple[str, ...],
    control_provenance: Provenance,
) -> None:
    if not node_id:
        raise ValueError("plan node id must be non-empty")
    if len(dependencies) != len(set(dependencies)):
        raise ValueError(f"node {node_id!r} contains duplicate dependencies")
    if not isinstance(control_provenance, Provenance):
        raise TypeError("control_provenance must be trusted Provenance")


def _validate_graph(nodes: tuple[PlanNode, ...], subplans: tuple[Plan, ...]) -> None:
    by_id = {node.id: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("plan node ids must be unique")
    child_ids = [plan.id for plan in subplans]
    if len(child_ids) != len(set(child_ids)):
        raise ValueError("child plan ids must be unique")
    for node in nodes:
        unknown = set(node.dependencies) - by_id.keys()
        if unknown:
            raise ValueError(f"node {node.id!r} has unknown dependencies: {sorted(unknown)}")
        if isinstance(node, BranchNode):
            _require_targets(by_id, node.id, node.when_true, node.when_false)
        elif isinstance(node, LoopNode):
            _require_targets(by_id, node.id, node.body_node_id, node.exit_node_id)
        elif isinstance(node, ActionTemplateNode):
            targets = tuple(item for item in (node.on_block, node.on_failure) if item is not None)
            _require_targets(by_id, node.id, *targets)
        elif isinstance(node, SubplanNode) and node.child_plan_id not in child_ids:
            raise ValueError(f"node {node.id!r} references an unknown child plan")
    _reject_dependency_cycles(by_id)


def _require_targets(by_id: dict[str, PlanNode], source: str, *targets: str) -> None:
    unknown = set(targets) - by_id.keys()
    if unknown:
        raise ValueError(f"node {source!r} has unknown targets: {sorted(unknown)}")


def _reject_dependency_cycles(by_id: dict[str, PlanNode]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise ValueError("implicit dependency cycle; use LoopNode for cycles")
        if node_id in visited:
            return
        visiting.add(node_id)
        for dependency in by_id[node_id].dependencies:
            visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(by_id):
        visit(node_id)


def _common_dict(node: PlanNode) -> dict[str, object]:
    return {
        "id": node.id,
        "kind": node.kind.value,
        "dependencies": list(node.dependencies),
        "control_provenance": node.control_provenance.to_dict(),
    }


def node_to_dict(node: PlanNode) -> dict[str, object]:
    result = _common_dict(node)
    if isinstance(node, ModelCallNode):
        result.update(prompt=node.prompt.to_dict(), output_name=node.output_name)
    elif isinstance(node, ActionTemplateNode):
        result.update(
            template=node.template.to_dict(),
            on_block=node.on_block,
            on_failure=node.on_failure,
            output_name=node.output_name,
        )
    elif isinstance(node, BranchNode):
        result.update(
            condition=node.condition.to_dict(),
            when_true=node.when_true,
            when_false=node.when_false,
        )
    elif isinstance(node, LoopNode):
        result.update(
            condition=node.condition.to_dict(),
            body_node_id=node.body_node_id,
            exit_node_id=node.exit_node_id,
            max_iterations=node.max_iterations,
        )
    elif isinstance(node, ContinuePlanningNode):
        result.update(
            observation_bindings=[item.to_dict() for item in node.observation_bindings],
            trigger=node.trigger,
        )
    elif isinstance(node, ApprovalNode):
        result["request"] = node.request
    elif isinstance(node, DelegationNode):
        result["scope"] = node.scope
    elif isinstance(node, SubplanNode):
        result["child_plan_id"] = node.child_plan_id
    elif isinstance(node, TerminalNode):
        result.update(outcome=node.outcome.value, reason=node.reason)
    return result


def node_fingerprint(node: PlanNode) -> str:
    return fingerprint(node_to_dict(node))


__all__ = [
    "ActionTemplateNode",
    "ApprovalNode",
    "BranchNode",
    "ContinuePlanningNode",
    "DelegationNode",
    "LoopNode",
    "ModelCallNode",
    "NodeKind",
    "PLAN_SCHEMA_VERSION",
    "Plan",
    "PlanNode",
    "SubplanNode",
    "TerminalNode",
    "TerminalOutcome",
    "node_fingerprint",
    "node_to_dict",
]
