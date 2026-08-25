"""Tests for the planning visualisation adapter."""

from __future__ import annotations

from conflux.domain import Provenance
from conflux.planning.model import Plan, TerminalNode, TerminalOutcome
from conflux.planning.state import (
    NodeState,
    NodeStatus,
    PlanExecutionState,
    PlanRunStatus,
    PlanTraceEvent,
)
from conflux.visualisation.model import VisualStatus, validate_graph
from conflux.visualisation.planning import planning_to_graph, trace_to_timeline


def _make_plan() -> Plan:
    terminal = TerminalNode(
        "done",
        TerminalOutcome.SUCCEEDED,
        "goal completed",
        Provenance.unknown(),
    )
    return Plan(
        id="test-plan",
        goal="test goal",
        nodes=(terminal,),
        invocation_provenance=Provenance.unknown(),
    )


def _make_state(
    *,
    status: PlanRunStatus = PlanRunStatus.SUCCEEDED,
    events: tuple[PlanTraceEvent, ...] = (),
) -> PlanExecutionState:
    plan = _make_plan()
    return PlanExecutionState(
        run_id="test-run-123",
        plan=plan,
        nodes=(NodeState("done", NodeStatus.SUCCEEDED),),
        initial_artifacts=(),
        events=events,
        status=status,
        transitions=3,
        planner_calls=2,
        effects=1,
        continuation_depth=0,
    )


class TestPlanningToGraph:
    def test_node_exists(self) -> None:
        graph = planning_to_graph(_make_state())
        node_ids = {n.node_id for n in graph.nodes}
        assert "node:done" in node_ids

    def test_run_summary_node_exists(self) -> None:
        graph = planning_to_graph(_make_state())
        run_nodes = [n for n in graph.nodes if n.node_id == "run"]
        assert len(run_nodes) == 1

    def test_succeeded_status(self) -> None:
        graph = planning_to_graph(_make_state(status=PlanRunStatus.SUCCEEDED))
        run_node = next(n for n in graph.nodes if n.node_id == "run")
        assert run_node.status == VisualStatus.SUCCESS

    def test_failed_status(self) -> None:
        graph = planning_to_graph(_make_state(status=PlanRunStatus.FAILED))
        run_node = next(n for n in graph.nodes if n.node_id == "run")
        assert run_node.status == VisualStatus.FAILED

    def test_all_edges_valid(self) -> None:
        graph = planning_to_graph(_make_state())
        assert validate_graph(graph) == []

    def test_deterministic(self) -> None:
        state = _make_state()
        assert planning_to_graph(state).to_dict() == planning_to_graph(state).to_dict()

    def test_metadata(self) -> None:
        graph = planning_to_graph(_make_state())
        assert graph.metadata["plan_id"] == "test-plan"
        assert graph.metadata["status"] == "succeeded"

    def test_node_fields_include_status(self) -> None:
        graph = planning_to_graph(_make_state())
        done_node = next(n for n in graph.nodes if n.node_id == "node:done")
        status_fields = [f for f in done_node.fields if f.key == "status"]
        assert len(status_fields) == 1
        assert status_fields[0].value == "succeeded"


class TestTraceToTimeline:
    def test_empty_events(self) -> None:
        graph = trace_to_timeline(())
        assert len(graph.nodes) == 0
        assert graph.metadata["event_count"] == "0"

    def test_events_ordered_by_sequence(self) -> None:
        events = (
            PlanTraceEvent(
                sequence=1,
                event_type="plan.created",
                run_id="r1",
                plan_id="p1",
                node_id=None,
                branch_id="b1",
                causal_parent_ids=(),
                payload={},
            ),
            PlanTraceEvent(
                sequence=0,
                event_type="plan.started",
                run_id="r1",
                plan_id="p1",
                node_id=None,
                branch_id="b1",
                causal_parent_ids=(),
                payload={},
            ),
        )
        graph = trace_to_timeline(events)
        assert len(graph.nodes) == 2
        node_labels = [n.label for n in graph.nodes]
        assert "seq=0" in node_labels[0]
        assert "seq=1" in node_labels[1]

    def test_transition_edges_connect_events(self) -> None:
        events = (
            PlanTraceEvent(
                sequence=0,
                event_type="plan.created",
                run_id="r1",
                plan_id="p1",
                node_id=None,
                branch_id="b1",
                causal_parent_ids=(),
                payload={},
            ),
            PlanTraceEvent(
                sequence=1,
                event_type="node.succeeded",
                run_id="r1",
                plan_id="p1",
                node_id="done",
                branch_id="b1",
                causal_parent_ids=(),
                payload={},
            ),
        )
        graph = trace_to_timeline(events)
        assert len(graph.edges) == 1
        assert validate_graph(graph) == []
