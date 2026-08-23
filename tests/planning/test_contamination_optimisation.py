"""Tests for planning as contamination minimisation (RQ8)."""

from __future__ import annotations

import pytest

from conflux.planning.contamination_optimisation import (
    StepCost,
    check_security_constrained_reachability,
    compute_trace_cost,
    run_contamination_experiment,
)

pytestmark = pytest.mark.security


class TestStepCost:
    """Per-step contamination cost."""

    def test_total_sums_all_components(self) -> None:
        step = StepCost(context_size=3, new_observations=2, authority_loss=1, sensitive_exposure=1)
        assert step.total == 7

    def test_zero_cost(self) -> None:
        step = StepCost(context_size=0, new_observations=0, authority_loss=0, sensitive_exposure=0)
        assert step.total == 0

    def test_round_trips(self) -> None:
        step = StepCost(context_size=2, new_observations=1, authority_loss=0, sensitive_exposure=1)
        d = step.to_dict()
        assert d["total"] == 4


class TestTraceCost:
    """Aggregated trace contamination cost."""

    def test_total_cost_sums_steps(self) -> None:
        trace = compute_trace_cost(
            steps=(
                StepCost(1, 1, 0, 0),
                StepCost(2, 0, 1, 0),
            ),
            goal_reached=True,
        )
        assert trace.total_cost == 5

    def test_max_context_size(self) -> None:
        trace = compute_trace_cost(
            steps=(
                StepCost(1, 0, 0, 0),
                StepCost(3, 0, 0, 0),
                StepCost(2, 0, 0, 0),
            ),
            goal_reached=True,
        )
        assert trace.max_context_size == 3

    def test_total_authority_loss(self) -> None:
        trace = compute_trace_cost(
            steps=(
                StepCost(1, 0, 0, 0),
                StepCost(2, 0, 1, 0),
                StepCost(3, 0, 2, 0),
            ),
            goal_reached=True,
        )
        assert trace.total_authority_loss == 3

    def test_empty_trace(self) -> None:
        trace = compute_trace_cost(steps=(), goal_reached=False)
        assert trace.total_cost == 0
        assert trace.max_context_size == 0


class TestReachability:
    """Security-constrained reachability."""

    def test_safe_reaching_trace(self) -> None:
        trace = compute_trace_cost(
            steps=(StepCost(1, 1, 0, 0),),
            goal_reached=True,
        )
        result = check_security_constrained_reachability((trace,))
        assert result.reachable
        assert result.min_cost == 2
        assert not result.security_violated

    def test_unsafe_trace_not_reachable(self) -> None:
        trace = compute_trace_cost(
            steps=(StepCost(1, 1, 0, 0),),
            goal_reached=True,
            security_violated=True,
        )
        result = check_security_constrained_reachability((trace,))
        assert not result.reachable
        assert result.security_violated

    def test_non_reaching_trace(self) -> None:
        trace = compute_trace_cost(
            steps=(StepCost(1, 1, 0, 0),),
            goal_reached=False,
        )
        result = check_security_constrained_reachability((trace,))
        assert not result.reachable

    def test_min_cost_among_multiple(self) -> None:
        low = compute_trace_cost(
            steps=(StepCost(1, 0, 0, 0),),
            goal_reached=True,
        )
        high = compute_trace_cost(
            steps=(StepCost(3, 2, 1, 1),),
            goal_reached=True,
        )
        result = check_security_constrained_reachability((low, high))
        assert result.reachable
        assert result.min_cost == 1


class TestExperiment:
    """The full contamination experiment."""

    def test_returns_valid_dict(self) -> None:
        result = run_contamination_experiment()
        assert result["schema_version"] == "1"
        assert "low_contamination" in result
        assert "high_contamination" in result
        assert "reachability" in result

    def test_goal_reachable_safely(self) -> None:
        result = run_contamination_experiment()
        assert result["summary"]["goal_reachable_safely"] is True

    def test_low_cost_lower_than_high(self) -> None:
        result = run_contamination_experiment()
        assert result["summary"]["low_cost"] < result["summary"]["high_cost"]

    def test_contamination_saved_positive(self) -> None:
        result = run_contamination_experiment()
        assert result["summary"]["contamination_saved"] > 0

    def test_has_fingerprint(self) -> None:
        result = run_contamination_experiment()
        assert len(result["fingerprint"]) == 64
