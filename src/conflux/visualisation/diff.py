"""Semantic diff between two VisualGraph instances.

Compares semantic identifiers (node IDs, kinds, statuses, edge
connectivity) rather than layout coordinates.  Reports added/removed
nodes, status changes, added/removed edges, and metadata changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.visualisation.model import VisualGraph, VisualNode, VisualStatus


@dataclass(frozen=True, slots=True)
class NodeDiff:
    """Difference for a single node between baseline and candidate."""

    node_id: str
    added: bool
    removed: bool
    status_changed: bool
    baseline_status: VisualStatus | None
    candidate_status: VisualStatus | None
    label_changed: bool
    baseline_label: str
    candidate_label: str


@dataclass(frozen=True, slots=True)
class EdgeDiff:
    """Difference for a single edge between baseline and candidate."""

    source: str
    target: str
    kind: str
    added: bool
    removed: bool


@dataclass(frozen=True, slots=True)
class GraphDiff:
    """Complete semantic diff between two VisualGraph instances."""

    nodes_added: tuple[str, ...] = ()
    nodes_removed: tuple[str, ...] = ()
    status_changes: tuple[NodeDiff, ...] = ()
    label_changes: tuple[NodeDiff, ...] = ()
    edges_added: tuple[EdgeDiff, ...] = ()
    edges_removed: tuple[EdgeDiff, ...] = ()
    metadata_added: tuple[str, ...] = ()
    metadata_removed: tuple[str, ...] = ()
    metadata_changed: tuple[tuple[str, str, str], ...] = ()

    @property
    def is_empty(self) -> bool:
        """Return True when there are no differences."""
        return not (
            self.nodes_added
            or self.nodes_removed
            or self.status_changes
            or self.label_changes
            or self.edges_added
            or self.edges_removed
            or self.metadata_added
            or self.metadata_removed
            or self.metadata_changed
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-compatible dictionary."""
        return {
            "nodes_added": list(self.nodes_added),
            "nodes_removed": list(self.nodes_removed),
            "status_changes": [
                {
                    "node_id": d.node_id,
                    "baseline": d.baseline_status.value if d.baseline_status else None,
                    "candidate": d.candidate_status.value if d.candidate_status else None,
                }
                for d in self.status_changes
            ],
            "label_changes": [
                {"node_id": d.node_id, "baseline": d.baseline_label, "candidate": d.candidate_label} for d in self.label_changes
            ],
            "edges_added": [{"source": e.source, "target": e.target, "kind": e.kind} for e in self.edges_added],
            "edges_removed": [{"source": e.source, "target": e.target, "kind": e.kind} for e in self.edges_removed],
            "metadata_added": list(self.metadata_added),
            "metadata_removed": list(self.metadata_removed),
            "metadata_changed": [{"key": k, "baseline": b, "candidate": c} for k, b, c in self.metadata_changed],
        }


def diff_graphs(baseline: VisualGraph, candidate: VisualGraph) -> GraphDiff:
    """Compute the semantic diff between two VisualGraph instances.

    Compares node IDs, statuses, labels, edge connectivity, and
    metadata.  Does not compare visual layout or rendering details.
    """
    baseline_nodes: dict[str, VisualNode] = {n.node_id: n for n in baseline.nodes}
    candidate_nodes: dict[str, VisualNode] = {n.node_id: n for n in candidate.nodes}

    baseline_ids = set(baseline_nodes)
    candidate_ids = set(candidate_nodes)

    nodes_added = tuple(sorted(candidate_ids - baseline_ids))
    nodes_removed = tuple(sorted(baseline_ids - candidate_ids))

    status_changes: list[NodeDiff] = []
    label_changes: list[NodeDiff] = []
    for node_id in sorted(baseline_ids & candidate_ids):
        b_node = baseline_nodes[node_id]
        c_node = candidate_nodes[node_id]
        if b_node.status != c_node.status:
            status_changes.append(
                NodeDiff(
                    node_id=node_id,
                    added=False,
                    removed=False,
                    status_changed=True,
                    baseline_status=b_node.status,
                    candidate_status=c_node.status,
                    label_changed=False,
                    baseline_label=b_node.label,
                    candidate_label=c_node.label,
                ),
            )
        if b_node.label != c_node.label:
            label_changes.append(
                NodeDiff(
                    node_id=node_id,
                    added=False,
                    removed=False,
                    status_changed=False,
                    baseline_status=b_node.status,
                    candidate_status=c_node.status,
                    label_changed=True,
                    baseline_label=b_node.label,
                    candidate_label=c_node.label,
                ),
            )

    def _edge_key(e: object) -> tuple[str, str, str]:
        return (getattr(e, "source"), getattr(e, "target"), getattr(e, "kind").value)

    baseline_edges = {_edge_key(e) for e in baseline.edges}
    candidate_edges = {_edge_key(e) for e in candidate.edges}

    edges_added = tuple(
        EdgeDiff(source=s, target=t, kind=k, added=True, removed=False) for s, t, k in sorted(candidate_edges - baseline_edges)
    )
    edges_removed = tuple(
        EdgeDiff(source=s, target=t, kind=k, added=False, removed=True) for s, t, k in sorted(baseline_edges - candidate_edges)
    )

    baseline_meta = dict(baseline.metadata)
    candidate_meta = dict(candidate.metadata)
    baseline_keys = set(baseline_meta)
    candidate_keys = set(candidate_meta)

    metadata_added = tuple(sorted(candidate_keys - baseline_keys))
    metadata_removed = tuple(sorted(baseline_keys - candidate_keys))
    metadata_changed = tuple(
        (k, str(baseline_meta[k]), str(candidate_meta[k]))
        for k in sorted(baseline_keys & candidate_keys)
        if str(baseline_meta[k]) != str(candidate_meta[k])
    )

    return GraphDiff(
        nodes_added=nodes_added,
        nodes_removed=nodes_removed,
        status_changes=tuple(status_changes),
        label_changes=tuple(label_changes),
        edges_added=edges_added,
        edges_removed=edges_removed,
        metadata_added=metadata_added,
        metadata_removed=metadata_removed,
        metadata_changed=metadata_changed,
    )
