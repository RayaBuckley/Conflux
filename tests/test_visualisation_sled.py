"""Tests for the SLED visualisation adapter."""

from __future__ import annotations

from conflux.evaluation.model_checking import (
    Counterexample,
    Transition,
    VerificationBounds,
    VerificationResult,
    VerificationVerdict,
)
from conflux.visualisation.model import validate_graph
from conflux.visualisation.sled import (
    DEFAULT_STATE_THRESHOLD,
    sled_to_graph,
)


def _make_result(
    *,
    verdict: VerificationVerdict = VerificationVerdict.SAFE,
    unique_states: int = 5,
    transitions: int = 10,
    truncated: bool = False,
    counterexample: Counterexample[str, str] | None = None,
) -> VerificationResult[str, str]:
    return VerificationResult(
        verdict=verdict,
        unique_states=unique_states,
        transitions=transitions,
        duplicate_states=2,
        truncated=truncated,
        bounds=VerificationBounds(),
        counterexample=counterexample,
    )


def _make_counterexample() -> Counterexample[str, str]:
    return Counterexample(
        property_name="no_unauthorised_execution",
        reason="executed without authorisation",
        transitions=(
            Transition("s0", "a1", "s1", "step1"),
            Transition("s1", "a2", "s2", "step2"),
        ),
    )


class TestSledToGraph:
    def test_verdict_node_exists(self) -> None:
        result = _make_result()
        graph = sled_to_graph(result)
        verdict_nodes = [n for n in graph.nodes if n.node_id == "verdict"]
        assert len(verdict_nodes) == 1
        assert verdict_nodes[0].label == "Verdict: safe"

    def test_safe_verdict_has_safe_status(self) -> None:
        result = _make_result(verdict=VerificationVerdict.SAFE)
        graph = sled_to_graph(result)
        verdict_node = next(n for n in graph.nodes if n.node_id == "verdict")
        assert verdict_node.status is not None
        assert "SAFE" in verdict_node.status.value

    def test_unsafe_verdict_has_unsafe_status(self) -> None:
        result = _make_result(verdict=VerificationVerdict.UNSAFE)
        graph = sled_to_graph(result)
        verdict_node = next(n for n in graph.nodes if n.node_id == "verdict")
        assert verdict_node.status is not None
        assert "UNSAFE" in verdict_node.status.value

    def test_counterexample_node_exists(self) -> None:
        cx = _make_counterexample()
        result = _make_result(
            verdict=VerificationVerdict.UNSAFE,
            counterexample=cx,
        )
        graph = sled_to_graph(result)
        cx_nodes = [n for n in graph.nodes if n.node_id == "counterexample"]
        assert len(cx_nodes) == 1
        assert "Counterexample" in cx_nodes[0].label

    def test_counterexample_edge_exists(self) -> None:
        cx = _make_counterexample()
        result = _make_result(
            verdict=VerificationVerdict.UNSAFE,
            counterexample=cx,
        )
        graph = sled_to_graph(result)
        cx_edges = [e for e in graph.edges if e.kind.value == "COUNTEREXAMPLE"]
        assert len(cx_edges) == 1
        assert cx_edges[0].source == "verdict"
        assert cx_edges[0].target == "counterexample"

    def test_all_edges_valid(self) -> None:
        result = _make_result()
        graph = sled_to_graph(result)
        assert validate_graph(graph) == []

    def test_deterministic(self) -> None:
        result = _make_result()
        g1 = sled_to_graph(result)
        g2 = sled_to_graph(result)
        assert g1.to_dict() == g2.to_dict()

    def test_large_run_produces_summary(self) -> None:
        result = _make_result(unique_states=DEFAULT_STATE_THRESHOLD + 1)
        graph = sled_to_graph(result)
        assert "unique_states" in graph.metadata
        assert graph.metadata["unique_states"] == str(DEFAULT_STATE_THRESHOLD + 1)

    def test_small_run_includes_threshold(self) -> None:
        result = _make_result(unique_states=10)
        graph = sled_to_graph(result)
        assert "threshold" in graph.metadata

    def test_metadata_has_verdict(self) -> None:
        result = _make_result(verdict=VerificationVerdict.BOUNDED_SAFE)
        graph = sled_to_graph(result)
        assert graph.metadata["verdict"] == "bounded_safe"

    def test_truncated_flag_in_metadata(self) -> None:
        result = _make_result(truncated=True)
        graph = sled_to_graph(result)
        assert graph.metadata["truncated"] == "True"
