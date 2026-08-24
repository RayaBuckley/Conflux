"""Tests for the visualisation common graph model."""

from __future__ import annotations

from conflux.visualisation.graph.model import LayoutDirection, LayoutOptions
from conflux.visualisation.model import (
    EdgeKind,
    EvidenceReference,
    NodeKind,
    VisualEdge,
    VisualField,
    VisualGraph,
    VisualNode,
    VisualStatus,
    validate_graph,
)


class TestVisualStatus:
    def test_status_values_are_distinct(self) -> None:
        values = {status.value for status in VisualStatus}
        assert len(values) == len(list(VisualStatus))

    def test_key_statuses_exist(self) -> None:
        assert VisualStatus.ALLOWED
        assert VisualStatus.BLOCKED
        assert VisualStatus.SAFE
        assert VisualStatus.UNSAFE
        assert VisualStatus.UNKNOWN
        assert VisualStatus.UNAVAILABLE


class TestEvidenceReference:
    def test_to_dict(self) -> None:
        ref = EvidenceReference(source_file="result.json", json_pointer="/executions/0")
        assert ref.to_dict() == {
            "source_file": "result.json",
            "json_pointer": "/executions/0",
        }


class TestVisualField:
    def test_to_dict_without_status(self) -> None:
        field = VisualField(key="operation", value="send_email")
        assert field.to_dict() == {"key": "operation", "value": "send_email"}

    def test_to_dict_with_status(self) -> None:
        field = VisualField(key="decision", value="allow", status=VisualStatus.ALLOWED)
        assert field.to_dict() == {
            "key": "decision",
            "value": "allow",
            "status": "ALLOWED",
        }


class TestVisualNode:
    def test_minimal_to_dict(self) -> None:
        node = VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="E0")
        result = node.to_dict()
        assert result["node_id"] == "n1"
        assert result["kind"] == "execution"
        assert result["label"] == "E0"
        assert "fields" not in result
        assert "status" not in result
        assert "source_ref" not in result

    def test_full_to_dict(self) -> None:
        ref = EvidenceReference(source_file="result.json", json_pointer="/executions/0")
        node = VisualNode(
            node_id="n1",
            kind=NodeKind.ACTION,
            label="send_email",
            fields=(VisualField(key="final", value="BLOCK", status=VisualStatus.BLOCKED),),
            status=VisualStatus.BLOCKED,
            source_ref=ref,
        )
        result = node.to_dict()
        assert result["fields"] == [{"key": "final", "value": "BLOCK", "status": "BLOCKED"}]
        assert result["status"] == "BLOCKED"
        assert result["source_ref"] == {"source_file": "result.json", "json_pointer": "/executions/0"}


class TestVisualEdge:
    def test_minimal_to_dict(self) -> None:
        edge = VisualEdge(source="n1", target="n2", kind=EdgeKind.INPUT_TO)
        result = edge.to_dict()
        assert result == {"source": "n1", "target": "n2", "kind": "INPUT_TO"}

    def test_full_to_dict(self) -> None:
        ref = EvidenceReference(source_file="result.json", json_pointer="/trace/0")
        edge = VisualEdge(
            source="n1",
            target="n2",
            kind=EdgeKind.TRANSITION,
            label="observe",
            source_ref=ref,
        )
        result = edge.to_dict()
        assert result["label"] == "observe"
        assert result["source_ref"] == {"source_file": "result.json", "json_pointer": "/trace/0"}


class TestVisualGraph:
    def _make_graph(self) -> VisualGraph:
        return VisualGraph(
            graph_id="g1",
            title="Test Graph",
            nodes=(
                VisualNode(node_id="b", kind=NodeKind.EXECUTION, label="E1"),
                VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="E0"),
            ),
            edges=(VisualEdge(source="a", target="b", kind=EdgeKind.PARENT_OF),),
        )

    def test_to_dict_sorts_nodes_by_id(self) -> None:
        graph = self._make_graph()
        result = graph.to_dict()
        node_ids = [n["node_id"] for n in result["nodes"]]
        assert node_ids == ["a", "b"]

    def test_to_dict_sorts_edges(self) -> None:
        graph = VisualGraph(
            graph_id="g1",
            title="Test",
            nodes=(
                VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="A"),
                VisualNode(node_id="b", kind=NodeKind.EXECUTION, label="B"),
                VisualNode(node_id="c", kind=NodeKind.EXECUTION, label="C"),
            ),
            edges=(
                VisualEdge(source="a", target="c", kind=EdgeKind.TRANSITION),
                VisualEdge(source="a", target="b", kind=EdgeKind.TRANSITION),
            ),
        )
        result = graph.to_dict()
        edges = [(e["source"], e["target"]) for e in result["edges"]]
        assert edges == [("a", "b"), ("a", "c")]

    def test_node_ids(self) -> None:
        graph = self._make_graph()
        assert graph.node_ids == {"a", "b"}

    def test_to_dict_includes_metadata(self) -> None:
        graph = VisualGraph(
            graph_id="g1",
            title="Test",
            nodes=(VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="A"),),
            metadata={"run_id": "abc123", "commit": "def456"},
        )
        result = graph.to_dict()
        assert result["metadata"] == {"commit": "def456", "run_id": "abc123"}

    def test_deterministic_serialisation(self) -> None:
        graph1 = self._make_graph()
        graph2 = VisualGraph(
            graph_id="g1",
            title="Test Graph",
            nodes=(
                VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="E0"),
                VisualNode(node_id="b", kind=NodeKind.EXECUTION, label="E1"),
            ),
            edges=(VisualEdge(source="a", target="b", kind=EdgeKind.PARENT_OF),),
        )
        assert graph1.to_dict() == graph2.to_dict()


class TestValidateGraph:
    def test_valid_graph(self) -> None:
        graph = VisualGraph(
            graph_id="g1",
            title="Test",
            nodes=(
                VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="A"),
                VisualNode(node_id="b", kind=NodeKind.EXECUTION, label="B"),
            ),
            edges=(VisualEdge(source="a", target="b", kind=EdgeKind.TRANSITION),),
        )
        assert validate_graph(graph) == []

    def test_edge_source_not_in_nodes(self) -> None:
        graph = VisualGraph(
            graph_id="g1",
            title="Test",
            nodes=(VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="A"),),
            edges=(VisualEdge(source="a", target="missing", kind=EdgeKind.TRANSITION),),
        )
        errors = validate_graph(graph)
        assert any("target" in e for e in errors)

    def test_duplicate_node_ids(self) -> None:
        graph = VisualGraph(
            graph_id="g1",
            title="Test",
            nodes=(
                VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="A"),
                VisualNode(node_id="a", kind=NodeKind.EXECUTION, label="Duplicate"),
            ),
        )
        errors = validate_graph(graph)
        assert any("duplicate" in e for e in errors)


class TestLayoutOptions:
    def test_defaults(self) -> None:
        opts = LayoutOptions()
        assert opts.direction == LayoutDirection.TOP_TO_BOTTOM
        assert opts.ranksep == "0.5"
        assert opts.fontname == "Helvetica"

    def test_to_dict(self) -> None:
        opts = LayoutOptions(direction=LayoutDirection.LEFT_TO_RIGHT)
        result = opts.to_dict()
        assert result["direction"] == "LR"
