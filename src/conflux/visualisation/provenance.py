"""Provenance-graph adapter for the visualisation layer.

Converts an ``ITESReport`` into a ``VisualGraph`` showing Principals,
Artifacts, Executions, and Actions, with edges representing provenance
relationships (authored, derived-from, input-to, influences).
"""

from __future__ import annotations

from conflux.domain import (
    Artifact,
    Principal,
    action_provenance,
)
from conflux.ites.state import ITESReport
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
from conflux.visualisation.normalise import sorted_principals, truncate_label


def _principal_node(principal: Principal, run_id: str) -> VisualNode:
    """Create a visual node for a Principal."""
    return VisualNode(
        node_id=f"principal:{principal.id}",
        kind=NodeKind.PRINCIPAL,
        label=principal.name,
        fields=(
            VisualField(key="id", value=principal.id),
            VisualField(key="kind", value=principal.kind),
        ),
        status=VisualStatus.ACTIVE,
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer=f"/principals/{principal.id}",
        ),
    )


def _artifact_node(artifact: Artifact[object], run_id: str) -> VisualNode:
    """Create a visual node for an Artifact."""
    fields: list[VisualField] = [
        VisualField(key="id", value=artifact.id),
        VisualField(key="fingerprint", value=artifact.fingerprint[:16] + "..."),
    ]
    if artifact.label:
        fields.append(VisualField(key="label", value=truncate_label(artifact.label)))
    fields.append(VisualField(key="confidential", value=str(artifact.confidential)))
    prov = artifact.provenance
    fields.append(VisualField(key="precision", value=prov.precision.value))
    fields.append(VisualField(key="attested", value=str(prov.attested)))

    return VisualNode(
        node_id=f"artifact:{artifact.id}",
        kind=NodeKind.ARTIFACT,
        label=f"Artifact {artifact.id}",
        fields=tuple(fields),
        status=VisualStatus.NOT_APPLICABLE,
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer=f"/artifacts/{artifact.id}",
        ),
    )


def _collect_principals(report: ITESReport) -> set[Principal]:
    """Collect all principals from branch contexts."""
    principals: set[Principal] = set()
    for branch in report.branches:
        principals.update(branch.context.principals)
        for event in branch.trace:
            principals.update(event.context.principals)
            if event.action is not None:
                principals.update(action_provenance(event.action).principals)
    return principals


def _collect_artifacts(report: ITESReport) -> list[Artifact[object]]:
    """Collect all artifacts from branch inputs and actions."""
    artifacts: dict[str, Artifact[object]] = {}
    for branch in report.branches:
        for artifact in branch.inputs:
            if artifact.id not in artifacts:
                artifacts[artifact.id] = artifact
    return list(artifacts.values())


def provenance_to_graph(report: ITESReport) -> VisualGraph:
    """Convert an ITES report into a provenance visual graph.

    The graph contains:
    - One node per Principal found in any context
    - One node per Artifact from branch inputs
    - One node per branch (execution)
    - One node per trace event with provenance-relevant info (action)
    - Edges: INFLUENCES (principal->artifact), INPUT_TO (artifact->branch),
      EXECUTED (branch->event), OBSERVABLE_TO (event->principal)
    """
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []
    run_id = report.run_id

    principals = _collect_principals(report)
    for pid in sorted_principals(p.id for p in principals):
        principal = next(p for p in principals if p.id == pid)
        nodes.append(_principal_node(principal, run_id))

    artifacts = _collect_artifacts(report)
    for artifact in sorted(artifacts, key=lambda a: a.id):
        nodes.append(_artifact_node(artifact, run_id))
        for principal in sorted(artifact.provenance.principals, key=lambda p: p.id):
            edges.append(
                VisualEdge(
                    source=f"principal:{principal.id}",
                    target=f"artifact:{artifact.id}",
                    kind=EdgeKind.INFLUENCES,
                ),
            )

    for branch in sorted(report.branches, key=lambda b: b.branch_id):
        b_node = VisualNode(
            node_id=f"exec:{branch.branch_id}",
            kind=NodeKind.EXECUTION,
            label=f"Execution {branch.branch_id}",
            fields=(
                VisualField(key="depth", value=str(branch.depth)),
                VisualField(key="status", value=branch.status.value),
            ),
            status=VisualStatus.ACTIVE,
            source_ref=EvidenceReference(
                source_file=f"{run_id}.json",
                json_pointer=f"/branches/{branch.branch_id}",
            ),
        )
        nodes.append(b_node)

        for artifact in branch.inputs:
            edges.append(
                VisualEdge(
                    source=f"artifact:{artifact.id}",
                    target=f"exec:{branch.branch_id}",
                    kind=EdgeKind.INPUT_TO,
                ),
            )

        for event in branch.trace:
            if event.action is not None:
                e_node = VisualNode(
                    node_id=f"action:{event.id}",
                    kind=NodeKind.ACTION,
                    label=f"Action {event.action.id[:8]}...",
                    fields=(
                        VisualField(key="outcome", value=event.outcome.value),
                        VisualField(key="action_id", value=event.action.id),
                    ),
                    status=VisualStatus.ACTIVE,
                    source_ref=EvidenceReference(
                        source_file=f"{run_id}.json",
                        json_pointer=f"/trace_events/{event.id}",
                    ),
                )
                nodes.append(e_node)
                edges.append(
                    VisualEdge(
                        source=f"exec:{branch.branch_id}",
                        target=f"action:{event.id}",
                        kind=EdgeKind.EXECUTED,
                    ),
                )

    return VisualGraph(
        graph_id=f"provenance:{run_id}",
        title=f"Provenance Graph — {run_id}",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "run_id": run_id,
            "principal_count": str(len(principals)),
            "artifact_count": str(len(artifacts)),
            "branch_count": str(len(report.branches)),
        },
    )


def diagnose_provenance(report: ITESReport) -> list[str]:
    """Return structural diagnostics for provenance completeness.

    Checks for:
    - Empty provenance on artifacts
    - Missing contributors (artifacts with no principal provenance)
    - Unknown principal contexts
    """
    issues: list[str] = []

    for branch in report.branches:
        if branch.context.unknown:
            issues.append(f"branch {branch.branch_id} has unknown Principal Context")

        for artifact in branch.inputs:
            if artifact.provenance.is_unknown:
                issues.append(f"artifact {artifact.id} in branch {branch.branch_id} has unknown provenance")
            if not artifact.provenance.principals:
                issues.append(f"artifact {artifact.id} in branch {branch.branch_id} has no contributing principal")

        for event in branch.trace:
            if event.context.unknown:
                issues.append(f"event {event.id} in branch {branch.branch_id} has unknown Principal Context")

    return issues
