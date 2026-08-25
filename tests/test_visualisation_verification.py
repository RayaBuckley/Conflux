"""Tests for the verification visualisation adapter."""

from __future__ import annotations

from conflux.verification.ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)
from conflux.verification.reduction import VerificationReduction, WitnessLiftingEvidence
from conflux.verification.results import FormalVerdict, FormalVerificationResult
from conflux.visualisation.model import VisualStatus, validate_graph
from conflux.visualisation.verification import (
    ir_to_graph,
    reduction_to_graph,
    verdict_to_graph,
)


def _make_ir() -> VerificationIR:
    x = StateVariable("x", Sort.BOOLEAN, False)
    y = StateVariable("y", Sort.INTEGER, 0, minimum=0, maximum=10)
    guard = Expression(ExpressionKind.VARIABLE, "x")
    assign = Expression(ExpressionKind.CONSTANT, 1)
    rule = TransitionRule(
        "r1",
        guard,
        (Assignment("y", assign),),
    )
    inv_expr = Expression(ExpressionKind.VARIABLE, "x")
    inv = SafetyInvariant("inv1", inv_expr, "x is stable")
    return VerificationIR(
        id="test-ir",
        variables=(x, y),
        transitions=(rule,),
        invariants=(inv,),
        bound=5,
    )


def _make_result(
    *,
    verdict: FormalVerdict = FormalVerdict.SAFE,
    counterexample: tuple[dict[str, object], ...] = (),
) -> FormalVerificationResult:
    return FormalVerificationResult(
        verdict=verdict,
        backend="z3",
        ir_hash="a" * 64,
        query_hash="b" * 64,
        solver_hash="c" * 64,
        model_hash="d" * 64,
        bound=5,
        assumptions=("no_overflow",),
        counterexample=counterexample,
    )


def _make_reduction() -> VerificationReduction:
    return VerificationReduction(
        original_fingerprint="orig",
        reduced_fingerprint="reduced",
        reduced_ir=_make_ir(),
        invariant_ids=("inv1",),
        retained_variables=("x",),
        removed_variables=("y",),
        retained_rules=("r1",),
        removed_rules=(),
        assumptions=("no_overflow",),
        applicable=True,
        reason=None,
        witness_lifting=WitnessLiftingEvidence(
            strategy="variable_projection",
            rule_ids_preserved=True,
            projected_variables=("x",),
            validated=True,
        ),
    )


class TestIRToGraph:
    def test_variable_nodes_exist(self) -> None:
        graph = ir_to_graph(_make_ir())
        var_nodes = [n for n in graph.nodes if n.node_id.startswith("var:")]
        assert len(var_nodes) == 2

    def test_rule_nodes_exist(self) -> None:
        graph = ir_to_graph(_make_ir())
        rule_nodes = [n for n in graph.nodes if n.node_id.startswith("rule:")]
        assert len(rule_nodes) == 1

    def test_invariant_nodes_exist(self) -> None:
        graph = ir_to_graph(_make_ir())
        inv_nodes = [n for n in graph.nodes if n.node_id.startswith("inv:")]
        assert len(inv_nodes) == 1

    def test_dependency_edges_exist(self) -> None:
        graph = ir_to_graph(_make_ir())
        dep_edges = [e for e in graph.edges if e.kind.value == "DEPENDS_ON"]
        assert len(dep_edges) >= 1

    def test_all_edges_valid(self) -> None:
        graph = ir_to_graph(_make_ir())
        assert validate_graph(graph) == []

    def test_deterministic(self) -> None:
        ir = _make_ir()
        assert ir_to_graph(ir).to_dict() == ir_to_graph(ir).to_dict()

    def test_metadata(self) -> None:
        graph = ir_to_graph(_make_ir())
        assert graph.metadata["variable_count"] == "2"
        assert graph.metadata["rule_count"] == "1"
        assert graph.metadata["bound"] == "5"


class TestVerdictToGraph:
    def test_verdict_node_exists(self) -> None:
        graph = verdict_to_graph(_make_result())
        verdict_nodes = [n for n in graph.nodes if n.node_id == "verdict"]
        assert len(verdict_nodes) == 1

    def test_safe_verdict_has_safe_status(self) -> None:
        graph = verdict_to_graph(_make_result(verdict=FormalVerdict.SAFE))
        node = next(n for n in graph.nodes if n.node_id == "verdict")
        assert node.status is not None
        assert "SAFE" in node.status.value

    def test_unsafe_verdict_has_unsafe_status(self) -> None:
        graph = verdict_to_graph(_make_result(verdict=FormalVerdict.UNSAFE))
        node = next(n for n in graph.nodes if n.node_id == "verdict")
        assert node.status is not None
        assert "UNSAFE" in node.status.value

    def test_counterexample_node(self) -> None:
        cx: tuple[dict[str, object], ...] = ({"x": True, "y": 1}, {"x": False, "y": 2})
        graph = verdict_to_graph(_make_result(verdict=FormalVerdict.UNSAFE, counterexample=cx))
        cx_nodes = [n for n in graph.nodes if n.node_id == "counterexample"]
        assert len(cx_nodes) == 1
        assert "2 steps" in cx_nodes[0].label

    def test_all_edges_valid(self) -> None:
        graph = verdict_to_graph(_make_result())
        assert validate_graph(graph) == []


class TestReductionToGraph:
    def test_summary_node_exists(self) -> None:
        graph = reduction_to_graph(_make_reduction())
        summary_nodes = [n for n in graph.nodes if n.node_id == "reduction"]
        assert len(summary_nodes) == 1

    def test_retained_variable_nodes(self) -> None:
        graph = reduction_to_graph(_make_reduction())
        retained = [n for n in graph.nodes if n.node_id.startswith("retained:")]
        assert len(retained) == 1
        assert retained[0].label == "x"

    def test_removed_variable_nodes(self) -> None:
        graph = reduction_to_graph(_make_reduction())
        removed = [n for n in graph.nodes if n.node_id.startswith("removed:")]
        assert len(removed) == 1
        assert removed[0].status == VisualStatus.PRUNED

    def test_all_edges_valid(self) -> None:
        graph = reduction_to_graph(_make_reduction())
        assert validate_graph(graph) == []

    def test_metadata(self) -> None:
        graph = reduction_to_graph(_make_reduction())
        assert graph.metadata["applicable"] == "True"
        assert graph.metadata["retained_variables"] == "1"
