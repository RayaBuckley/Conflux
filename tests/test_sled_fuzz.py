"""Regression fuzz harness for SLED properties.

Generates random environment snapshots and bound configurations,
runs SLED on each, and asserts that the verification infrastructure
doesn't crash and produces valid verdicts.

Source: ESBMC (arXiv:2605.26169) random test generation.
"""

from __future__ import annotations

import random

import pytest

from conflux.evaluation.delegation_verification import (
    DELEGATION_PROPERTIES,
    DelegationMutation,
    DelegationVerificationSystem,
)
from conflux.evaluation.model_checking import (
    ExplicitStateChecker,
    VerificationBounds,
    VerificationVerdict,
)
from conflux.evaluation.planning import (
    CodeCapabilityPreserved,
    NoUnauthorisedPlanningEffect,
    PlanningContextMonotonicity,
    WorstCasePlanningSystem,
)

PLANNING_PROPERTIES = (
    NoUnauthorisedPlanningEffect(),
    PlanningContextMonotonicity(),
    CodeCapabilityPreserved(),
)

VALID_VERDICTS = frozenset(
    {VerificationVerdict.SAFE, VerificationVerdict.BOUNDED_SAFE, VerificationVerdict.UNSAFE, VerificationVerdict.UNKNOWN},
)


def _random_delegation_system(rng: random.Random) -> DelegationVerificationSystem:
    mutation = rng.choice(list(DelegationMutation))
    return DelegationVerificationSystem(mutation)


def _random_planning_system(rng: random.Random) -> WorstCasePlanningSystem:
    return WorstCasePlanningSystem(
        initial_context=frozenset(rng.sample(["alice", "bob", "carol", "dave"], k=rng.randint(1, 4))),
        patches=(),
        max_plan_nodes=rng.randint(4, 16),
        max_continuation_depth=rng.randint(2, 8),
        max_planner_calls=rng.randint(2, 8),
        max_effects=rng.randint(2, 8),
    )


def _random_bounds(rng: random.Random) -> VerificationBounds:
    return VerificationBounds(
        max_depth=rng.randint(4, 12),
        max_states=rng.randint(100, 10_000),
        max_transitions=rng.randint(500, 50_000),
        max_model_calls=rng.randint(2, 8),
    )


@pytest.mark.parametrize("seed", range(20))
def test_delegation_fuzz_no_crash(seed: int) -> None:
    rng = random.Random(seed)
    system = _random_delegation_system(rng)
    bounds = _random_bounds(rng)
    result = ExplicitStateChecker().verify(system, DELEGATION_PROPERTIES, bounds)
    assert result.verdict in VALID_VERDICTS


@pytest.mark.parametrize("seed", range(20))
def test_planning_fuzz_no_crash(seed: int) -> None:
    rng = random.Random(seed + 100)
    system = _random_planning_system(rng)
    bounds = _random_bounds(rng)
    result = ExplicitStateChecker().verify(system, PLANNING_PROPERTIES, bounds)
    assert result.verdict in VALID_VERDICTS


def test_safe_verdict_has_no_counterexample() -> None:
    result = ExplicitStateChecker().verify(
        DelegationVerificationSystem(DelegationMutation.CANONICAL),
        DELEGATION_PROPERTIES,
    )
    if result.verdict is VerificationVerdict.SAFE:
        assert result.counterexample is None or result.counterexample.length == 0


def test_unsafe_verdict_has_counterexample() -> None:
    for mutation in DelegationMutation:
        if mutation == DelegationMutation.CANONICAL:
            continue
        result = ExplicitStateChecker().verify(
            DelegationVerificationSystem(mutation),
            DELEGATION_PROPERTIES,
        )
        if result.verdict is VerificationVerdict.UNSAFE:
            assert result.counterexample is not None
            assert result.counterexample.length >= 1
