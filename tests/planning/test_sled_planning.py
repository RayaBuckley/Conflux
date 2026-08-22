"""Native SLED worst-case dynamic-planning model tests."""

from __future__ import annotations

import pytest

from conflux.evaluation import (
    AbstractEffect,
    AbstractPatchKind,
    AbstractPlanPatch,
    CodeCapabilityPreserved,
    ExplicitStateChecker,
    NoUnauthorisedPlanningEffect,
    PlanningContextMonotonicity,
    VerificationBounds,
    VerificationVerdict,
    WorstCasePlanningSystem,
)

pytestmark = pytest.mark.security


def patches() -> tuple[AbstractPlanPatch, ...]:
    return (
        AbstractPlanPatch(
            "safe",
            AbstractPatchKind.APPEND_EFFECT,
            frozenset({"observation"}),
            AbstractEffect(
                "safe-write",
                "write",
                "safe.txt",
                frozenset({"observation"}),
                True,
            ),
        ),
        AbstractPlanPatch(
            "unsafe",
            AbstractPatchKind.APPEND_EFFECT,
            frozenset({"attacker"}),
            AbstractEffect(
                "unsafe-write",
                "write",
                "secret.txt",
                frozenset({"attacker"}),
                False,
            ),
        ),
        AbstractPlanPatch(
            "code-escape",
            AbstractPatchKind.APPEND_CODE_EFFECT,
            frozenset({"code-author"}),
            AbstractEffect(
                "network",
                "connect",
                "network:any",
                frozenset({"code-author"}),
                True,
                code_effect=True,
                within_capability_envelope=False,
            ),
        ),
        AbstractPlanPatch(
            "stop",
            AbstractPatchKind.TERMINATE,
            frozenset({"observation"}),
        ),
    )


PROPERTIES = (
    NoUnauthorisedPlanningEffect(),
    PlanningContextMonotonicity(),
    CodeCapabilityPreserved(),
)


def test_canonical_planning_model_is_bounded_safe_and_deterministic() -> None:
    system = WorstCasePlanningSystem(
        frozenset({"invoker"}),
        patches(),
        max_plan_nodes=4,
        max_continuation_depth=3,
        max_planner_calls=3,
        max_effects=2,
    )
    bounds = VerificationBounds(
        max_depth=16,
        max_states=500,
        max_transitions=1_000,
        max_model_calls=8,
    )
    first = ExplicitStateChecker().verify(system, PROPERTIES, bounds)
    second = ExplicitStateChecker().verify(system, PROPERTIES, bounds)
    assert first.verdict == VerificationVerdict.BOUNDED_SAFE
    assert first.to_dict() == second.to_dict()
    assert first.unique_states > 1
    assert first.transitions > 1
    assert first.truncated


def test_permission_mutant_has_shortest_plan_counterexample() -> None:
    system = WorstCasePlanningSystem(
        frozenset({"invoker"}),
        patches(),
        enforce_authorisation=False,
    )
    result = ExplicitStateChecker().verify(
        system,
        (NoUnauthorisedPlanningEffect(),),
        VerificationBounds(max_depth=8, max_states=100, max_transitions=100),
    )
    assert result.verdict == VerificationVerdict.UNSAFE
    assert result.counterexample is not None
    assert result.counterexample.length == 2
    assert "unauthorised" in result.counterexample.reason
    assert "unsafe" in str(result.counterexample.transitions[0].action.key)


def test_capability_mutant_models_worst_case_generated_code() -> None:
    system = WorstCasePlanningSystem(
        frozenset({"invoker"}),
        patches(),
        enforce_capability_envelope=False,
    )
    result = ExplicitStateChecker().verify(
        system,
        (CodeCapabilityPreserved(),),
        VerificationBounds(max_depth=8, max_states=100, max_transitions=100),
    )
    assert result.verdict == VerificationVerdict.UNSAFE
    assert result.counterexample is not None
    assert result.counterexample.length == 2
    assert "capability" in result.counterexample.reason


def test_terminating_finite_planning_model_can_be_safe() -> None:
    system = WorstCasePlanningSystem(
        frozenset({"invoker"}),
        (
            AbstractPlanPatch(
                "stop",
                AbstractPatchKind.TERMINATE,
                frozenset({"observation"}),
            ),
        ),
    )
    result = ExplicitStateChecker().verify(
        system,
        PROPERTIES,
        VerificationBounds(max_depth=4, max_states=10, max_transitions=10),
    )
    assert result.verdict == VerificationVerdict.SAFE
    assert not result.truncated
    assert result.unique_states == 2
    assert result.transitions == 1


def test_external_checker_transition_bound_only_truncates_when_frontier_remains() -> None:
    terminating = WorstCasePlanningSystem(
        frozenset({"invoker"}),
        (
            AbstractPlanPatch(
                "stop",
                AbstractPatchKind.TERMINATE,
                frozenset(),
            ),
        ),
    )
    exact = ExplicitStateChecker().verify(
        terminating,
        PROPERTIES,
        VerificationBounds(max_depth=4, max_states=4, max_transitions=1),
    )
    assert exact.verdict == VerificationVerdict.SAFE

    branching = WorstCasePlanningSystem(
        frozenset({"invoker"}),
        (
            AbstractPlanPatch("a", AbstractPatchKind.TERMINATE, frozenset()),
            AbstractPlanPatch("b", AbstractPatchKind.TERMINATE, frozenset()),
        ),
    )
    truncated = ExplicitStateChecker().verify(
        branching,
        PROPERTIES,
        VerificationBounds(max_depth=4, max_states=4, max_transitions=1),
    )
    assert truncated.verdict == VerificationVerdict.BOUNDED_SAFE
    assert truncated.transitions == 1
