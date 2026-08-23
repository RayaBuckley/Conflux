"""Planning as contamination minimisation (RQ8).

Formalises the connection between low-water-mark contamination and
security-aware planning.  The objective is to minimise Principal
Context growth and authority loss while completing tasks subject to
security invariants.

Cost function:

    cost(trace) = sum_t (
        |PC_t|              — context size at step t
        + observations_t    — number of new data items observed
        + authority_loss_t  — actions denied due to PC growth
        + sensitive_exposure_t — sensitive information accessed
    )

Security-constrained reachability:

    Is there a strategy reaching the goal without entering an authority
    state that prevents required future actions?

This module implements the cost function, a contamination-aware plan
evaluation, and a security-constrained reachability check over finite
plan traces.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint

CONTAMINATION_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class StepCost:
    """Contamination cost of a single plan step.

    Attributes:
        context_size: number of principals in the Principal Context.
        new_observations: number of new data items observed.
        authority_loss: number of actions denied due to PC growth.
        sensitive_exposure: number of sensitive items accessed.
    """

    context_size: int
    new_observations: int
    authority_loss: int
    sensitive_exposure: int

    @property
    def total(self) -> int:
        """Total contamination cost for this step."""
        return self.context_size + self.new_observations + self.authority_loss + self.sensitive_exposure

    def to_dict(self) -> dict[str, object]:
        """Serialise this step cost to a JSON-compatible dictionary."""
        return {
            "context_size": self.context_size,
            "new_observations": self.new_observations,
            "authority_loss": self.authority_loss,
            "sensitive_exposure": self.sensitive_exposure,
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class TraceCost:
    """Contamination cost of an entire plan trace.

    Attributes:
        steps: per-step costs.
        total_cost: sum of all step costs.
        max_context_size: maximum context size reached.
        total_authority_loss: total actions denied across the trace.
        goal_reached: whether the trace reaches the goal.
        security_violated: whether any security invariant was violated.
    """

    steps: tuple[StepCost, ...]
    total_cost: int
    max_context_size: int
    total_authority_loss: int
    goal_reached: bool
    security_violated: bool

    def to_dict(self) -> dict[str, object]:
        """Serialise this trace cost to a JSON-compatible dictionary."""
        return {
            "schema_version": CONTAMINATION_SCHEMA_VERSION,
            "steps": [s.to_dict() for s in self.steps],
            "total_cost": self.total_cost,
            "max_context_size": self.max_context_size,
            "total_authority_loss": self.total_authority_loss,
            "goal_reached": self.goal_reached,
            "security_violated": self.security_violated,
        }


def compute_trace_cost(
    steps: tuple[StepCost, ...],
    goal_reached: bool,
    security_violated: bool = False,
) -> TraceCost:
    """Compute the contamination cost of a plan trace.

    Args:
        steps: per-step contamination costs.
        goal_reached: whether the plan reached its goal.
        security_violated: whether any security invariant was violated.

    Returns:
        A TraceCost with aggregated metrics.
    """
    total = sum(s.total for s in steps)
    max_ctx = max((s.context_size for s in steps), default=0)
    total_loss = sum(s.authority_loss for s in steps)
    return TraceCost(
        steps=steps,
        total_cost=total,
        max_context_size=max_ctx,
        total_authority_loss=total_loss,
        goal_reached=goal_reached,
        security_violated=security_violated,
    )


@dataclass(frozen=True, slots=True)
class ReachabilityResult:
    """Result of a security-constrained reachability check.

    Attributes:
        reachable: whether the goal is reachable without violating
            security invariants.
        min_cost: minimum contamination cost among safe reaching traces.
        security_violated: whether any trace violates security.
        trace_count: number of traces examined.
    """

    reachable: bool
    min_cost: int | None
    security_violated: bool
    trace_count: int

    def to_dict(self) -> dict[str, object]:
        """Serialise this reachability result to a JSON-compatible dictionary."""
        return {
            "schema_version": CONTAMINATION_SCHEMA_VERSION,
            "reachable": self.reachable,
            "min_cost": self.min_cost,
            "security_violated": self.security_violated,
            "trace_count": self.trace_count,
        }


def check_security_constrained_reachability(
    traces: tuple[TraceCost, ...],
) -> ReachabilityResult:
    """Check if any trace reaches the goal without violating security.

    Given a set of plan traces with contamination costs, determine:
    1. Whether any trace reaches the goal without security violation.
    2. The minimum contamination cost among safe reaching traces.
    3. Whether any trace violates security.

    Args:
        traces: a collection of plan trace costs to evaluate.

    Returns:
        A ReachabilityResult.
    """
    safe_reaching = [t for t in traces if t.goal_reached and not t.security_violated]
    any_violated = any(t.security_violated for t in traces)
    min_cost = min((t.total_cost for t in safe_reaching), default=None)
    return ReachabilityResult(
        reachable=len(safe_reaching) > 0,
        min_cost=min_cost,
        security_violated=any_violated,
        trace_count=len(traces),
    )


def run_contamination_experiment() -> dict[str, object]:
    """Run a demonstration contamination-minimisation experiment.

    Constructs two plan traces:
    1. A low-contamination trace that avoids unnecessary observations
       and reaches the goal safely.
    2. A high-contamination trace that observes everything, grows the
       PC, and loses authority — but still reaches the goal.

    The experiment shows that contamination-minimising planning can
    reduce authority loss while maintaining task completion.
    """
    low_contamination = compute_trace_cost(
        steps=(
            StepCost(context_size=1, new_observations=1, authority_loss=0, sensitive_exposure=0),
            StepCost(context_size=1, new_observations=0, authority_loss=0, sensitive_exposure=0),
        ),
        goal_reached=True,
    )
    high_contamination = compute_trace_cost(
        steps=(
            StepCost(context_size=1, new_observations=1, authority_loss=0, sensitive_exposure=1),
            StepCost(context_size=2, new_observations=2, authority_loss=1, sensitive_exposure=1),
            StepCost(context_size=3, new_observations=1, authority_loss=2, sensitive_exposure=0),
        ),
        goal_reached=True,
    )
    unsafe_trace = compute_trace_cost(
        steps=(StepCost(context_size=1, new_observations=1, authority_loss=0, sensitive_exposure=1),),
        goal_reached=False,
        security_violated=True,
    )
    reachability = check_security_constrained_reachability(
        (low_contamination, high_contamination, unsafe_trace),
    )
    return {
        "schema_version": CONTAMINATION_SCHEMA_VERSION,
        "low_contamination": low_contamination.to_dict(),
        "high_contamination": high_contamination.to_dict(),
        "unsafe_trace": unsafe_trace.to_dict(),
        "reachability": reachability.to_dict(),
        "summary": {
            "goal_reachable_safely": reachability.reachable,
            "min_safe_cost": reachability.min_cost,
            "low_cost": low_contamination.total_cost,
            "high_cost": high_contamination.total_cost,
            "contamination_saved": high_contamination.total_cost - low_contamination.total_cost,
        },
        "fingerprint": fingerprint(
            {
                "reachable": reachability.reachable,
                "min_cost": reachability.min_cost,
            },
        ),
    }


__all__ = [
    "CONTAMINATION_SCHEMA_VERSION",
    "ReachabilityResult",
    "StepCost",
    "TraceCost",
    "check_security_constrained_reachability",
    "compute_trace_cost",
    "run_contamination_experiment",
]
