"""Tests for the semantic diff between VisualGraph instances."""

from __future__ import annotations

from conflux.visualisation.diff import diff_graphs
from conflux.visualisation.model import (
    EdgeKind,
    NodeKind,
    VisualEdge,
    VisualGraph,
    VisualNode,
    VisualStatus,
)


def _make_graph(
    *,
    nodes: tuple[VisualNode, ...] = (
        VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="A", status=VisualStatus.ALLOWED),
        VisualNode(node_id="n2", kind=NodeKind.ACTION, label="B", status=VisualStatus.BLOCKED),
    ),
    edges: tuple[VisualEdge, ...] = (VisualEdge(source="n1", target="n2", kind=EdgeKind.TRANSITION),),
    metadata: dict[str, str] | None = None,
) -> VisualGraph:
    return VisualGraph(
        graph_id="test",
        title="Test",
        nodes=nodes,
        edges=edges,
        metadata=metadata or {},
    )


class TestDiffGraphs:
    def test_identical_graphs_have_empty_diff(self) -> None:
        g = _make_graph()
        d = diff_graphs(g, g)
        assert d.is_empty

    def test_added_node_detected(self) -> None:
        baseline = _make_graph()
        candidate = _make_graph(
            nodes=(
                VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="A", status=VisualStatus.ALLOWED),
                VisualNode(node_id="n2", kind=NodeKind.ACTION, label="B", status=VisualStatus.BLOCKED),
                VisualNode(node_id="n3", kind=NodeKind.DECISION, label="C", status=VisualStatus.UNKNOWN),
            ),
        )
        d = diff_graphs(baseline, candidate)
        assert d.nodes_added == ("n3",)
        assert not d.is_empty

    def test_removed_node_detected(self) -> None:
        baseline = _make_graph(
            nodes=(
                VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="A", status=VisualStatus.ALLOWED),
                VisualNode(node_id="n2", kind=NodeKind.ACTION, label="B", status=VisualStatus.BLOCKED),
                VisualNode(node_id="n3", kind=NodeKind.DECISION, label="C", status=VisualStatus.UNKNOWN),
            ),
        )
        candidate = _make_graph()
        d = diff_graphs(baseline, candidate)
        assert d.nodes_removed == ("n3",)

    def test_status_change_detected(self) -> None:
        baseline = _make_graph()
        candidate = _make_graph(
            nodes=(
                VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="A", status=VisualStatus.BLOCKED),
                VisualNode(node_id="n2", kind=NodeKind.ACTION, label="B", status=VisualStatus.BLOCKED),
            ),
        )
        d = diff_graphs(baseline, candidate)
        assert len(d.status_changes) == 1
        assert d.status_changes[0].node_id == "n1"
        assert d.status_changes[0].baseline_status == VisualStatus.ALLOWED
        assert d.status_changes[0].candidate_status == VisualStatus.BLOCKED

    def test_label_change_detected(self) -> None:
        baseline = _make_graph()
        candidate = _make_graph(
            nodes=(
                VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="CHANGED", status=VisualStatus.ALLOWED),
                VisualNode(node_id="n2", kind=NodeKind.ACTION, label="B", status=VisualStatus.BLOCKED),
            ),
        )
        d = diff_graphs(baseline, candidate)
        assert len(d.label_changes) == 1
        assert d.label_changes[0].baseline_label == "A"
        assert d.label_changes[0].candidate_label == "CHANGED"

    def test_added_edge_detected(self) -> None:
        baseline = _make_graph()
        candidate = _make_graph(
            edges=(
                VisualEdge(source="n1", target="n2", kind=EdgeKind.TRANSITION),
                VisualEdge(source="n2", target="n1", kind=EdgeKind.DEPENDS_ON),
            ),
        )
        d = diff_graphs(baseline, candidate)
        assert len(d.edges_added) == 1
        assert d.edges_added[0].source == "n2"
        assert d.edges_added[0].target == "n1"

    def test_removed_edge_detected(self) -> None:
        baseline = _make_graph(
            edges=(
                VisualEdge(source="n1", target="n2", kind=EdgeKind.TRANSITION),
                VisualEdge(source="n2", target="n1", kind=EdgeKind.DEPENDS_ON),
            ),
        )
        candidate = _make_graph()
        d = diff_graphs(baseline, candidate)
        assert len(d.edges_removed) == 1
        assert d.edges_removed[0].source == "n2"

    def test_metadata_change_detected(self) -> None:
        baseline = _make_graph(metadata={"run_id": "abc", "count": "5"})
        candidate = _make_graph(metadata={"run_id": "abc", "count": "10", "extra": "new"})
        d = diff_graphs(baseline, candidate)
        assert d.metadata_added == ("extra",)
        assert d.metadata_changed == (("count", "5", "10"),)

    def test_to_dict_structure(self) -> None:
        baseline = _make_graph()
        candidate = _make_graph(
            nodes=(VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="A", status=VisualStatus.BLOCKED),),
        )
        d = diff_graphs(baseline, candidate)
        result = d.to_dict()
        assert "nodes_added" in result
        assert "nodes_removed" in result
        assert "status_changes" in result
        assert "edges_removed" in result

    def test_deterministic(self) -> None:
        baseline = _make_graph()
        candidate = _make_graph(
            nodes=(VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="A", status=VisualStatus.BLOCKED),),
        )
        assert diff_graphs(baseline, candidate).to_dict() == diff_graphs(baseline, candidate).to_dict()
