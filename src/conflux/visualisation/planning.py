"""Planning visualisation adapter.

Converts a ``PlanExecutionState`` into a ``VisualGraph`` showing plan
topology, node statuses, and execution trace.
"""

from __future__ import annotations

from conflux.planning.state import (
    NodeStatus,
    PlanExecutionState,
    PlanRunStatus,
    PlanTraceEvent,
)
from conflux.visualisation.model import (
    EdgeKind,
    EvidenceReference,
    NodeKind,
    VisualEdge,
    VisualField,
    VisualGraph,
    VisualNode,
    VisualStatus,
)

_NODE_STATUS_MAP: dict[NodeStatus, VisualStatus] = {
    NodeStatus.PENDING: VisualStatus.UNKNOWN,
    NodeStatus.READY: VisualStatus.ACTIVE,
    NodeStatus.RUNNING: VisualStatus.ACTIVE,
    NodeStatus.SUCCEEDED: VisualStatus.SUCCESS,
    NodeStatus.FAILED: VisualStatus.FAILED,
    NodeStatus.BLOCKED: VisualStatus.BLOCKED,
    NodeStatus.SKIPPED: VisualStatus.PRUNED,
}

_RUN_STATUS_MAP: dict[PlanRunStatus, VisualStatus] = {
    PlanRunStatus.RUNNING: VisualStatus.ACTIVE,
    PlanRunStatus.SUCCEEDED: VisualStatus.SUCCESS,
    PlanRunStatus.SAFE_STOP: VisualStatus.NOT_APPLICABLE,
    PlanRunStatus.FAILED: VisualStatus.FAILED,
    PlanRunStatus.BLOCKED: VisualStatus.BLOCKED,
    PlanRunStatus.INCOMPLETE: VisualStatus.INCOMPLETE,
}


def _node_kind_for_plan(node: object) -> NodeKind:
    """Map a plan node to a visual node kind."""
    kind_str = getattr(node, "kind", None)
    if kind_str is None:
        return NodeKind.OPERATION
    kind_value = str(kind_str.value) if hasattr(kind_str, "value") else str(kind_str)
    mapping = {
        "model_call": NodeKind.OPERATION,
        "action_template": NodeKind.OPERATION,
        "branch": NodeKind.DECISION,
        "loop": NodeKind.DECISION,
        "continue_planning": NodeKind.OPERATION,
        "approval": NodeKind.APPROVAL,
        "delegation": NodeKind.DELEGATION,
        "subplan": NodeKind.OPERATION,
        "terminal": NodeKind.TERMINAL,
    }
    return mapping.get(kind_value, NodeKind.OPERATION)


def planning_to_graph(state: PlanExecutionState) -> VisualGraph:
    """Convert a plan execution state into a visual graph.

    Nodes: one per plan node (with status from NodeState) plus a run
    summary node.  Edges: DEPENDS_ON (from node dependencies), TRANSITION
    (from trace events).
    """
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []
    run_id = state.run_id

    node_states = {ns.node_id: ns for ns in state.nodes}

    for plan_node in sorted(state.plan.nodes, key=lambda n: n.id):
        ns = node_states.get(plan_node.id)
        status = _NODE_STATUS_MAP.get(ns.status, VisualStatus.UNKNOWN) if ns else VisualStatus.UNKNOWN

        fields: list[VisualField] = [
            VisualField(key="kind", value=str(getattr(plan_node, "kind", "unknown"))),
        ]
        if ns is not None:
            fields.append(VisualField(key="status", value=ns.status.value))
            fields.append(VisualField(key="attempts", value=str(ns.attempts)))
            if ns.reason:
                fields.append(VisualField(key="reason", value=ns.reason))

        nodes.append(
            VisualNode(
                node_id=f"node:{plan_node.id}",
                kind=_node_kind_for_plan(plan_node),
                label=plan_node.id,
                fields=tuple(fields),
                status=status,
                source_ref=EvidenceReference(
                    source_file=f"{run_id}.json",
                    json_pointer=f"/nodes/{plan_node.id}",
                ),
            ),
        )

        for dep in plan_node.dependencies:
            edges.append(
                VisualEdge(
                    source=f"node:{dep}",
                    target=f"node:{plan_node.id}",
                    kind=EdgeKind.DEPENDS_ON,
                ),
            )

    run_fields: list[VisualField] = [
        VisualField(key="plan_id", value=state.plan.id),
        VisualField(key="goal", value=state.plan.goal[:60]),
        VisualField(key="status", value=state.status.value),
        VisualField(key="transitions", value=str(state.transitions)),
        VisualField(key="planner_calls", value=str(state.planner_calls)),
        VisualField(key="effects", value=str(state.effects)),
        VisualField(key="continuation_depth", value=str(state.continuation_depth)),
    ]
    if state.failure_category is not None:
        run_fields.append(VisualField(key="failure_category", value=state.failure_category))

    run_node = VisualNode(
        node_id="run",
        kind=NodeKind.SUMMARY,
        label=f"Plan Run: {state.status.value}",
        fields=tuple(run_fields),
        status=_RUN_STATUS_MAP.get(state.status),
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer="/",
        ),
    )
    nodes.append(run_node)

    for event in state.events:
        if event.node_id is not None:
            edges.append(
                VisualEdge(
                    source=f"node:{event.node_id}",
                    target="run",
                    kind=EdgeKind.TRANSITION,
                    label=event.event_type,
                ),
            )

    return VisualGraph(
        graph_id=f"planning:{run_id}",
        title=f"Plan Execution — {run_id[:16]}...",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "run_id": run_id,
            "plan_id": state.plan.id,
            "status": state.status.value,
            "node_count": str(len(state.nodes)),
            "transitions": str(state.transitions),
            "planner_calls": str(state.planner_calls),
        },
    )


def trace_to_timeline(events: tuple[PlanTraceEvent, ...]) -> VisualGraph:
    """Convert plan trace events into a visual timeline.

    Each event becomes a node ordered by sequence, connected by
    TRANSITION edges.
    """
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []

    sorted_events = sorted(events, key=lambda e: e.sequence)

    for event in sorted_events:
        fields: list[VisualField] = [
            VisualField(key="event_type", value=event.event_type),
            VisualField(key="node_id", value=event.node_id or ""),
        ]
        nodes.append(
            VisualNode(
                node_id=f"event:{event.id}",
                kind=NodeKind.OBSERVATION,
                label=f"{event.event_type} (seq={event.sequence})",
                fields=tuple(fields),
                status=VisualStatus.ACTIVE,
            ),
        )

    for i in range(len(sorted_events) - 1):
        edges.append(
            VisualEdge(
                source=f"event:{sorted_events[i].id}",
                target=f"event:{sorted_events[i + 1].id}",
                kind=EdgeKind.TRANSITION,
            ),
        )

    return VisualGraph(
        graph_id="plan-timeline",
        title="Plan Trace Timeline",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "event_count": str(len(events)),
        },
    )
