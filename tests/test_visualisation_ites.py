"""Tests for the ITES and provenance visualisation adapters."""

from __future__ import annotations

from conflux.domain import (
    Action,
    ActionDecision,
    Artifact,
    Decision,
    DecisionCategory,
    NoOpAction,
    Principal,
    PrincipalContext,
    Provenance,
)
from conflux.ites.state import (
    ActionOutcome,
    BranchState,
    BranchStatus,
    ITESReport,
    SafetyAssessment,
    TraceEvent,
)
from conflux.visualisation.ites import ites_to_graph
from conflux.visualisation.model import validate_graph
from conflux.visualisation.provenance import diagnose_provenance, provenance_to_graph


def _make_principal(pid: str, name: str) -> Principal:
    return Principal(pid, name)


def _make_decision(
    category: DecisionCategory,
    allowed: bool,
    reason: str = "",
    policy_id: str = "test-policy",
    policy_version: str = "1",
) -> Decision:
    return Decision(
        category=category,
        allowed=allowed,
        reason=reason or f"{category.value}_{'allow' if allowed else 'deny'}",
        policy_id=policy_id,
        policy_version=policy_version,
    )


def _make_action_decision(
    context: PrincipalContext,
    *,
    auth: bool = True,
    read: bool = True,
    vis: bool = True,
    consent: bool = True,
    arg: bool | None = None,
) -> ActionDecision:
    return ActionDecision(
        context=context,
        authorisation=_make_decision(DecisionCategory.AUTHORISATION, auth),
        read=_make_decision(DecisionCategory.READ, read),
        visibility=_make_decision(DecisionCategory.VISIBILITY, vis),
        consent=_make_decision(DecisionCategory.CONSENT, consent),
        argument_authorisation=_make_decision(DecisionCategory.AUTHORISATION, arg) if arg is not None else None,
    )


def _make_simple_report(
    *,
    run_id: str = "test-run",
    allow: bool = True,
    principals: tuple[Principal, ...] | None = None,
) -> ITESReport:
    """Build a minimal ITESReport with one branch and one trace event."""
    if principals is None:
        principals = (_make_principal("alice", "Alice"),)
    ctx = PrincipalContext.from_principals(frozenset(principals))
    artifact = Artifact("doc1", "content", Provenance.from_principal(principals[0]), label="Doc 1")
    branch = BranchState(
        branch_id="root",
        parent_branch_id=None,
        depth=0,
        inputs=(artifact,),
        context=ctx,
        status=BranchStatus.AUTHORISED if allow else BranchStatus.BLOCKED,
    )
    action: Action = NoOpAction("noop-1")
    decision = _make_action_decision(ctx, auth=allow)
    event = TraceEvent(
        sequence=0,
        branch_id="root",
        parent_branch_id=None,
        depth=0,
        outcome=ActionOutcome.AUTHORISED if allow else ActionOutcome.BLOCKED,
        context=ctx,
        action=action,
        decision=decision,
        reason="test",
    )
    branch = branch.append(event)
    return ITESReport(
        run_id=run_id,
        branches=(branch,),
        assessments=(SafetyAssessment("no_unauthorised_execution", True, "test", ("executed=0",)),),
        model_calls=1,
        max_model_calls=10,
        incomplete=False,
    )


class TestITESToGraph:
    def test_graph_has_run_id(self) -> None:
        report = _make_simple_report(run_id="abc123")
        graph = ites_to_graph(report)
        assert graph.metadata["run_id"] == "abc123"

    def test_graph_id_is_stable(self) -> None:
        report = _make_simple_report()
        graph1 = ites_to_graph(report)
        graph2 = ites_to_graph(report)
        assert graph1.graph_id == graph2.graph_id
        assert graph1.to_dict() == graph2.to_dict()

    def test_branch_nodes_exist(self) -> None:
        report = _make_simple_report()
        graph = ites_to_graph(report)
        branch_ids = {n.node_id for n in graph.nodes if n.node_id.startswith("branch:")}
        assert "branch:root" in branch_ids

    def test_event_nodes_exist(self) -> None:
        report = _make_simple_report()
        graph = ites_to_graph(report)
        event_nodes = [n for n in graph.nodes if n.node_id.startswith("event:")]
        assert len(event_nodes) >= 1

    def test_decision_nodes_exist(self) -> None:
        report = _make_simple_report()
        graph = ites_to_graph(report)
        decision_nodes = [n for n in graph.nodes if n.node_id.startswith("decision:")]
        assert len(decision_nodes) >= 4

    def test_all_edges_have_valid_endpoints(self) -> None:
        report = _make_simple_report()
        graph = ites_to_graph(report)
        errors = validate_graph(graph)
        assert errors == []

    def test_blocked_report_produces_blocked_status(self) -> None:
        report = _make_simple_report(allow=False)
        graph = ites_to_graph(report)
        event_nodes = [n for n in graph.nodes if n.node_id.startswith("event:")]
        assert any(n.status is not None and "BLOCK" in n.status.value for n in event_nodes)

    def test_metadata_has_counts(self) -> None:
        report = _make_simple_report()
        graph = ites_to_graph(report)
        assert "proposed" in graph.metadata
        assert "authorised" in graph.metadata
        assert "blocked" in graph.metadata
        assert "executed" in graph.metadata


class TestProvenanceToGraph:
    def test_principal_nodes_exist(self) -> None:
        alice = _make_principal("alice", "Alice")
        report = _make_simple_report(principals=(alice,))
        graph = provenance_to_graph(report)
        p_nodes = [n for n in graph.nodes if n.node_id.startswith("principal:")]
        assert len(p_nodes) == 1
        assert p_nodes[0].label == "Alice"

    def test_artifact_nodes_exist(self) -> None:
        report = _make_simple_report()
        graph = provenance_to_graph(report)
        a_nodes = [n for n in graph.nodes if n.node_id.startswith("artifact:")]
        assert len(a_nodes) >= 1

    def test_influences_edges_connect_principals_to_artifacts(self) -> None:
        alice = _make_principal("alice", "Alice")
        report = _make_simple_report(principals=(alice,))
        graph = provenance_to_graph(report)
        inf_edges = [e for e in graph.edges if e.kind.value == "INFLUENCES"]
        assert len(inf_edges) >= 1
        assert all(e.source.startswith("principal:") for e in inf_edges)
        assert all(e.target.startswith("artifact:") for e in inf_edges)

    def test_all_edges_have_valid_endpoints(self) -> None:
        report = _make_simple_report()
        graph = provenance_to_graph(report)
        errors = validate_graph(graph)
        assert errors == []

    def test_graph_is_deterministic(self) -> None:
        report = _make_simple_report()
        g1 = provenance_to_graph(report)
        g2 = provenance_to_graph(report)
        assert g1.to_dict() == g2.to_dict()


class TestDiagnoseProvenance:
    def test_clean_report_has_no_issues(self) -> None:
        report = _make_simple_report()
        issues = diagnose_provenance(report)
        assert issues == []

    def test_unknown_context_reported(self) -> None:
        report = _make_simple_report()
        ctx = PrincipalContext(unknown=True)
        branch = BranchState(
            branch_id="root",
            parent_branch_id=None,
            depth=0,
            inputs=(),
            context=ctx,
            status=BranchStatus.INCOMPLETE,
        )
        report = ITESReport(
            run_id="test",
            branches=(branch,),
            assessments=(),
            model_calls=0,
            max_model_calls=10,
            incomplete=True,
        )
        issues = diagnose_provenance(report)
        assert any("unknown Principal Context" in i for i in issues)
