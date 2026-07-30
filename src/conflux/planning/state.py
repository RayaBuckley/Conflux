"""Immutable dynamic-plan execution state and replayable events."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any

from conflux.domain import Artifact, fingerprint

from .model import Plan, node_fingerprint


class NodeStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

    @property
    def terminal(self) -> bool:
        return self in {
            NodeStatus.SUCCEEDED,
            NodeStatus.FAILED,
            NodeStatus.BLOCKED,
            NodeStatus.SKIPPED,
        }


class PlanRunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SAFE_STOP = "safe_stop"
    FAILED = "failed"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class NodeState:
    node_id: str
    status: NodeStatus = NodeStatus.PENDING
    attempts: int = 0
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "attempts": self.attempts,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class NodeOutput:
    node_id: str
    name: str
    artifact: Artifact[Any]

    @property
    def key(self) -> tuple[str, str]:
        return (self.node_id, self.name)

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "artifact": self.artifact.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PlanTraceEvent:
    sequence: int
    event_type: str
    run_id: str
    plan_id: str
    node_id: str | None
    branch_id: str
    causal_parent_ids: tuple[str, ...]
    payload: dict[str, object]
    schema_version: str = "1"

    @property
    def id(self) -> str:
        return fingerprint(
            {
                "schema_version": self.schema_version,
                "event_type": self.event_type,
                "run_id": self.run_id,
                "plan_id": self.plan_id,
                "node_id": self.node_id,
                "branch_id": self.branch_id,
                "causal_parent_ids": self.causal_parent_ids,
                "payload": self.payload,
            }
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "plan_id": self.plan_id,
            "node_id": self.node_id,
            "branch_id": self.branch_id,
            "causal_parent_ids": list(self.causal_parent_ids),
            "payload": self.payload,
        }


@dataclass(frozen=True, slots=True)
class PlanExecutionState:
    run_id: str
    plan: Plan
    nodes: tuple[NodeState, ...]
    initial_artifacts: tuple[Artifact[Any], ...]
    outputs: tuple[NodeOutput, ...] = ()
    events: tuple[PlanTraceEvent, ...] = ()
    activated_node_ids: frozenset[str] = frozenset()
    loop_iterations: tuple[tuple[str, int], ...] = ()
    status: PlanRunStatus = PlanRunStatus.RUNNING
    transitions: int = 0
    planner_calls: int = 0
    continuation_depth: int = 0
    effects: int = 0
    failure_category: str | None = None

    @classmethod
    def initial(
        cls,
        plan: Plan,
        artifacts: tuple[Artifact[Any], ...] = (),
    ) -> "PlanExecutionState":
        artifacts = tuple(artifacts)
        gated = _gated_nodes(plan)
        activated = plan.node_ids - gated
        run_id = fingerprint(
            {
                "plan": plan.fingerprint,
                "artifacts": [item.fingerprint for item in artifacts],
            }
        )
        state = cls(
            run_id,
            plan,
            tuple(NodeState(node.id) for node in plan.nodes),
            artifacts,
            activated_node_ids=activated,
        )
        return state.emit(
            "plan.created",
            payload={
                "plan_fingerprint": plan.fingerprint,
                "node_count": len(plan.nodes),
            },
        )

    def node_state(self, node_id: str) -> NodeState:
        try:
            return next(item for item in self.nodes if item.node_id == node_id)
        except StopIteration as error:
            raise ValueError(f"unknown execution node: {node_id}") from error

    def node_outputs(self) -> dict[tuple[str, str], Artifact[Any]]:
        return {item.key: item.artifact for item in self.outputs}

    def artifacts(self) -> dict[str, Artifact[Any]]:
        result = {item.id: item for item in self.initial_artifacts}
        result.update({item.artifact.id: item.artifact for item in self.outputs})
        return result

    def loop_count(self, node_id: str) -> int:
        return dict(self.loop_iterations).get(node_id, 0)

    def with_node(
        self,
        node_id: str,
        status: NodeStatus,
        *,
        reason: str = "",
        increment_attempts: bool = False,
    ) -> "PlanExecutionState":
        updated: list[NodeState] = []
        found = False
        for item in self.nodes:
            if item.node_id != node_id:
                updated.append(item)
                continue
            found = True
            updated.append(
                replace(
                    item,
                    status=status,
                    reason=reason,
                    attempts=item.attempts + int(increment_attempts),
                )
            )
        if not found:
            raise ValueError(f"unknown execution node: {node_id}")
        return replace(self, nodes=tuple(updated))

    def with_output(self, output: NodeOutput) -> "PlanExecutionState":
        retained = tuple(item for item in self.outputs if item.key != output.key)
        return replace(self, outputs=retained + (output,))

    def activate(self, *node_ids: str) -> "PlanExecutionState":
        unknown = set(node_ids) - self.plan.node_ids
        if unknown:
            raise ValueError(f"cannot activate unknown nodes: {sorted(unknown)}")
        return replace(
            self,
            activated_node_ids=self.activated_node_ids | frozenset(node_ids),
        )

    def deactivate(self, *node_ids: str) -> "PlanExecutionState":
        return replace(
            self,
            activated_node_ids=self.activated_node_ids - frozenset(node_ids),
        )

    def skip(self, *node_ids: str, reason: str) -> "PlanExecutionState":
        state = self
        for node_id in node_ids:
            item = state.node_state(node_id)
            if item.status == NodeStatus.PENDING:
                state = state.with_node(node_id, NodeStatus.SKIPPED, reason=reason)
        return state

    def increment_loop(self, node_id: str) -> "PlanExecutionState":
        counts = dict(self.loop_iterations)
        counts[node_id] = counts.get(node_id, 0) + 1
        return replace(self, loop_iterations=tuple(sorted(counts.items())))

    def emit(
        self,
        event_type: str,
        *,
        node_id: str | None = None,
        branch_id: str = "root",
        payload: dict[str, object] | None = None,
        causal_parent_ids: tuple[str, ...] | None = None,
    ) -> "PlanExecutionState":
        parents = causal_parent_ids
        if parents is None:
            parents = (self.events[-1].id,) if self.events else ()
        event = PlanTraceEvent(
            len(self.events),
            event_type,
            self.run_id,
            self.plan.id,
            node_id,
            branch_id,
            parents,
            payload or {},
        )
        return replace(self, events=self.events + (event,))

    def replace_plan(self, plan: Plan, *, removed_node_ids: tuple[str, ...]) -> "PlanExecutionState":
        removed = set(removed_node_ids)
        existing = {item.node_id: item for item in self.nodes if item.node_id not in removed}
        nodes = tuple(existing.get(node.id, NodeState(node.id)) for node in plan.nodes)
        gated = _gated_nodes(plan)
        newly_ungated = {
            node.id for node in plan.nodes if node.id not in existing and node.id not in gated
        }
        return replace(
            self,
            plan=plan,
            nodes=nodes,
            activated_node_ids=(self.activated_node_ids - removed) | newly_ungated,
        )

    @property
    def state_key(self) -> str:
        return fingerprint(
            {
                "plan": self.plan.fingerprint,
                "nodes": [item.to_dict() for item in self.nodes],
                "outputs": [item.artifact.fingerprint for item in self.outputs],
                "activated": sorted(self.activated_node_ids),
                "loops": list(self.loop_iterations),
                "status": self.status.value,
                "transitions": self.transitions,
                "planner_calls": self.planner_calls,
                "continuation_depth": self.continuation_depth,
                "effects": self.effects,
            }
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1",
            "run_id": self.run_id,
            "plan_id": self.plan.id,
            "plan_fingerprint": self.plan.fingerprint,
            "status": self.status.value,
            "failure_category": self.failure_category,
            "nodes": [item.to_dict() for item in self.nodes],
            "outputs": [item.to_dict() for item in self.outputs],
            "events": [item.to_dict() for item in self.events],
            "activated_node_ids": sorted(self.activated_node_ids),
            "loop_iterations": dict(self.loop_iterations),
            "statistics": {
                "transitions": self.transitions,
                "planner_calls": self.planner_calls,
                "continuation_depth": self.continuation_depth,
                "effects": self.effects,
            },
        }


def _gated_nodes(plan: Plan) -> frozenset[str]:
    from .model import ActionTemplateNode, BranchNode, LoopNode

    gated: set[str] = set()
    for node in plan.nodes:
        if isinstance(node, BranchNode):
            gated.update((node.when_true, node.when_false))
        elif isinstance(node, LoopNode):
            gated.update((node.body_node_id, node.exit_node_id))
        elif isinstance(node, ActionTemplateNode):
            gated.update(item for item in (node.on_block, node.on_failure) if item is not None)
    return frozenset(gated)


def ready_nodes(state: PlanExecutionState) -> tuple[str, ...]:
    ready: list[tuple[str, str]] = []
    statuses = {item.node_id: item.status for item in state.nodes}
    for node in state.plan.nodes:
        if (
            statuses[node.id] == NodeStatus.PENDING
            and node.id in state.activated_node_ids
            and all(statuses[dependency] == NodeStatus.SUCCEEDED for dependency in node.dependencies)
        ):
            ready.append((node.id, node_fingerprint(node)))
    return tuple(node_id for node_id, _ in sorted(ready))


__all__ = [
    "NodeOutput",
    "NodeState",
    "NodeStatus",
    "PlanExecutionState",
    "PlanRunStatus",
    "PlanTraceEvent",
    "ready_nodes",
]
