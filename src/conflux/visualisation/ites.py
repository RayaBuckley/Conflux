"""ITES execution-graph adapter for the visualisation layer.

Converts an ``ITESReport`` into a ``VisualGraph`` showing the branch tree,
trace events, Principal Context, action decisions, and certificates.
Every node carries an ``EvidenceReference`` back to the report data.
"""

from __future__ import annotations

from conflux.ites.state import (
    ActionOutcome,
    BranchState,
    BranchStatus,
    ITESReport,
    TraceEvent,
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

_OUTCOME_STATUS: dict[ActionOutcome, VisualStatus] = {
    ActionOutcome.PROPOSED: VisualStatus.UNKNOWN,
    ActionOutcome.AUTHORISED: VisualStatus.ALLOWED,
    ActionOutcome.BLOCKED: VisualStatus.BLOCKED,
    ActionOutcome.EXECUTED: VisualStatus.SUCCESS,
    ActionOutcome.PROVIDER_FAILED: VisualStatus.FAILED,
    ActionOutcome.INCOMPLETE: VisualStatus.INCOMPLETE,
    ActionOutcome.COMPLETE: VisualStatus.NOT_APPLICABLE,
}

_BRANCH_STATUS: dict[BranchStatus, VisualStatus] = {
    BranchStatus.ACTIVE: VisualStatus.ACTIVE,
    BranchStatus.AUTHORISED: VisualStatus.ALLOWED,
    BranchStatus.BLOCKED: VisualStatus.BLOCKED,
    BranchStatus.EXECUTED: VisualStatus.SUCCESS,
    BranchStatus.PROVIDER_FAILED: VisualStatus.FAILED,
    BranchStatus.TERMINAL: VisualStatus.NOT_APPLICABLE,
    BranchStatus.INCOMPLETE: VisualStatus.INCOMPLETE,
}


def _branch_node(branch: BranchState, run_id: str) -> VisualNode:
    """Create a visual node for a branch."""
    fields: list[VisualField] = [
        VisualField(key="depth", value=str(branch.depth)),
        VisualField(key="status", value=branch.status.value),
        VisualField(key="model_calls", value=str(branch.model_calls)),
        VisualField(key="principal_ids", value=", ".join(sorted(str(p) for p in branch.context.principals))),
    ]
    if branch.parent_branch_id:
        fields.append(VisualField(key="parent", value=branch.parent_branch_id))
    if branch.action is not None:
        fields.append(VisualField(key="action_id", value=branch.action.id))
    if branch.certificate is not None:
        fields.append(VisualField(key="certificate_id", value=branch.certificate.id))

    return VisualNode(
        node_id=f"branch:{branch.branch_id}",
        kind=NodeKind.EXECUTION,
        label=f"Branch {branch.branch_id}",
        fields=tuple(fields),
        status=_BRANCH_STATUS.get(branch.status),
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer=f"/branches/{branch.branch_id}",
        ),
    )


def _trace_event_node(event: TraceEvent, run_id: str) -> VisualNode:
    """Create a visual node for a single trace event."""
    fields: list[VisualField] = [
        VisualField(key="sequence", value=str(event.sequence)),
        VisualField(key="outcome", value=event.outcome.value),
    ]
    if event.action is not None:
        fields.append(VisualField(key="action_id", value=event.action.id))
    if event.decision is not None:
        fields.append(VisualField(key="decision", value="ALLOWED" if event.decision.allowed else "BLOCKED"))
    if event.reason:
        fields.append(VisualField(key="reason", value=event.reason))

    return VisualNode(
        node_id=f"event:{event.id}",
        kind=NodeKind.ACTION,
        label=f"{event.outcome.value} (seq={event.sequence})",
        fields=tuple(fields),
        status=_OUTCOME_STATUS.get(event.outcome),
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer=f"/trace_events/{event.id}",
        ),
    )


def _decision_node(
    branch_id: str,
    event_id: str,
    category: str,
    allowed: bool,
    reason: str,
    policy_id: str,
    run_id: str,
) -> VisualNode:
    """Create a visual node for a single policy decision dimension."""
    return VisualNode(
        node_id=f"decision:{event_id}:{category}",
        kind=NodeKind.DECISION,
        label=f"{category}: {'ALLOW' if allowed else 'DENY'}",
        fields=(
            VisualField(key="category", value=category),
            VisualField(key="allowed", value=str(allowed)),
            VisualField(key="reason", value=reason),
            VisualField(key="policy_id", value=policy_id),
        ),
        status=VisualStatus.ALLOWED if allowed else VisualStatus.BLOCKED,
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer=f"/trace_events/{event_id}/decision/{category}",
        ),
    )


def ites_to_graph(report: ITESReport) -> VisualGraph:
    """Convert an ITES report into a visual execution graph.

    The graph contains:
    - One node per branch (execution node)
    - One node per trace event (action node)
    - One node per policy decision dimension (decision node)
    - Edges: parent-child branch, branch-to-event, event-to-decision
    """
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []
    run_id = report.run_id

    for branch in sorted(report.branches, key=lambda b: b.branch_id):
        nodes.append(_branch_node(branch, run_id))

        if branch.parent_branch_id:
            edges.append(
                VisualEdge(
                    source=f"branch:{branch.parent_branch_id}",
                    target=f"branch:{branch.branch_id}",
                    kind=EdgeKind.PARENT_OF,
                ),
            )

        for event in branch.trace:
            nodes.append(_trace_event_node(event, run_id))
            edges.append(
                VisualEdge(
                    source=f"branch:{branch.branch_id}",
                    target=f"event:{event.id}",
                    kind=EdgeKind.TRANSITION,
                ),
            )

            if event.decision is not None:
                for decision in event.decision.decisions:
                    cat = decision.category.value
                    d_node = _decision_node(
                        branch.branch_id,
                        event.id,
                        cat,
                        decision.allowed,
                        decision.reason,
                        decision.policy_id,
                        run_id,
                    )
                    nodes.append(d_node)
                    edges.append(
                        VisualEdge(
                            source=f"event:{event.id}",
                            target=d_node.node_id,
                            kind=EdgeKind.DEPENDS_ON,
                        ),
                    )

    return VisualGraph(
        graph_id=f"ites:{run_id}",
        title=f"ITES Execution Graph — {run_id}",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "run_id": run_id,
            "branch_count": str(len(report.branches)),
            "proposed": str(report.proposed_count),
            "authorised": str(report.authorised_count),
            "blocked": str(report.blocked_count),
            "executed": str(report.executed_count),
            "provider_failed": str(report.provider_failed_count),
            "incomplete": str(report.incomplete_count),
        },
    )
