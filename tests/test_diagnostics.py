"""Tests for the SLED diagnostic taxonomy."""

from __future__ import annotations

import pytest

from conflux.domain import (
    ActionDecision,
    Decision,
    DecisionCategory,
    PrimitiveAction,
    Principal,
    PrincipalContext,
)
from conflux.evaluation.diagnostics import (
    DiagnosticCategory,
    DiagnosticConfig,
    classify_branches,
)
from conflux.ites import BranchState, BranchStatus, ITESReport

pytestmark = pytest.mark.security

alice = Principal("alice", "Alice")
mallory = Principal("mallory", "Mallory")


def _make_action(action_id: str = "write") -> PrimitiveAction:
    return PrimitiveAction(
        id=action_id,
        operation="write",
        permission="write",
    )


def _make_decision(allowed: bool = True) -> ActionDecision:
    decision = Decision(
        category=DecisionCategory.AUTHORISATION,
        allowed=allowed,
        reason="test",
        policy_id="test-policy",
        policy_version="1",
    )
    read = Decision(
        category=DecisionCategory.READ,
        allowed=True,
        reason="test",
        policy_id="test-policy",
        policy_version="1",
    )
    visibility = Decision(
        category=DecisionCategory.VISIBILITY,
        allowed=True,
        reason="test",
        policy_id="test-policy",
        policy_version="1",
    )
    consent = Decision(
        category=DecisionCategory.CONSENT,
        allowed=True,
        reason="test",
        policy_id="test-policy",
        policy_version="1",
    )
    return ActionDecision(
        context=PrincipalContext.from_principals(frozenset({alice})),
        authorisation=decision,
        read=read,
        visibility=visibility,
        consent=consent,
    )


def _make_branch(
    branch_id: str = "1.1",
    status: BranchStatus = BranchStatus.AUTHORISED,
    action_id: str = "write",
    allowed: bool = True,
) -> BranchState:
    action = _make_action(action_id) if action_id else None
    decision = _make_decision(allowed) if action else None
    return BranchState(
        branch_id=branch_id,
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({alice})),
        status=status,
        action=action,
        decision=decision,
    )


def _make_report(branches: tuple[BranchState, ...]) -> ITESReport:
    return ITESReport(
        run_id="test",
        branches=branches,
        assessments=(),
        model_calls=1,
        max_model_calls=3,
        incomplete=False,
    )


class TestDiagnosticCategories:
    """Each diagnostic category is correctly assigned."""

    def test_goal_secure(self) -> None:
        branch = _make_branch(status=BranchStatus.AUTHORISED, action_id="write", allowed=True)
        report = _make_report((branch,))
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.classifications[0].category == DiagnosticCategory.GOAL_SECURE

    def test_goal_insecure(self) -> None:
        branch = _make_branch(status=BranchStatus.AUTHORISED, action_id="write", allowed=False)
        report = _make_report((branch,))
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.classifications[0].category == DiagnosticCategory.GOAL_INSECURE

    def test_goal_missing(self) -> None:
        branch = _make_branch(status=BranchStatus.BLOCKED, action_id="write", allowed=False)
        report = _make_report((branch,))
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.classifications[0].category == DiagnosticCategory.GOAL_MISSING

    def test_non_goal_accidental(self) -> None:
        branch = _make_branch(status=BranchStatus.AUTHORISED, action_id="delete", allowed=True)
        report = _make_report((branch,))
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.classifications[0].category == DiagnosticCategory.NON_GOAL_ACCIDENTAL

    def test_non_goal_insecure(self) -> None:
        branch = _make_branch(status=BranchStatus.AUTHORISED, action_id="delete", allowed=False)
        report = _make_report((branch,))
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.classifications[0].category == DiagnosticCategory.NON_GOAL_INSECURE

    def test_non_goal_blocked(self) -> None:
        branch = _make_branch(status=BranchStatus.BLOCKED, action_id="delete", allowed=False)
        report = _make_report((branch,))
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.classifications[0].category == DiagnosticCategory.NON_GOAL_BLOCKED


class TestDiagnosticReport:
    """Aggregate report properties."""

    def test_counts_are_correct(self) -> None:
        branches = (
            _make_branch("1.1", BranchStatus.AUTHORISED, "write", True),
            _make_branch("1.2", BranchStatus.BLOCKED, "write", False),
            _make_branch("1.3", BranchStatus.AUTHORISED, "delete", True),
        )
        report = _make_report(branches)
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.counts[DiagnosticCategory.GOAL_SECURE.value] == 1
        assert result.counts[DiagnosticCategory.GOAL_MISSING.value] == 1
        assert result.counts[DiagnosticCategory.NON_GOAL_ACCIDENTAL.value] == 1
        assert result.total_branches == 3

    def test_goal_completion_rate(self) -> None:
        branches = (
            _make_branch("1.1", BranchStatus.AUTHORISED, "write", True),
            _make_branch("1.2", BranchStatus.AUTHORISED, "write", False),
            _make_branch("1.3", BranchStatus.BLOCKED, "write", False),
        )
        report = _make_report(branches)
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.goal_completion_rate == pytest.approx(1 / 3)

    def test_security_violation_count(self) -> None:
        branches = (
            _make_branch("1.1", BranchStatus.AUTHORISED, "write", True),
            _make_branch("1.2", BranchStatus.AUTHORISED, "write", False),
        )
        report = _make_report(branches)
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.security_violation_count == 1

    def test_empty_report(self) -> None:
        report = _make_report(())
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        assert result.total_branches == 0
        assert result.goal_completion_rate == 0.0

    def test_report_round_trips(self) -> None:
        branches = (_make_branch("1.1", BranchStatus.AUTHORISED, "write", True),)
        report = _make_report(branches)
        config = DiagnosticConfig(goal_action_ids=frozenset({"write"}))
        result = classify_branches(report, config)
        d = result.to_dict()
        assert d["schema_version"] == "1"
        assert d["total_branches"] == 1
        assert d["counts"]["goal_secure"] == 1

    def test_config_round_trips(self) -> None:
        config = DiagnosticConfig(goal_action_ids=frozenset({"write", "read"}))
        d = config.to_dict()
        assert d["goal_action_ids"] == ["read", "write"]
