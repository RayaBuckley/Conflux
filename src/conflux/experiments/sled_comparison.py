"""Deterministic trace-enumeration versus state-exploration comparison."""

from __future__ import annotations

from collections import deque

from conflux.evaluation import (
    AbstractEffect,
    AbstractPatchKind,
    AbstractPlanPatch,
    ExplicitStateChecker,
    NoUnauthorisedPlanningEffect,
    PlanningModelState,
    VerificationBounds,
    WorstCasePlanningSystem,
)


def comparison(depth: int = 8) -> dict[str, object]:
    if depth < 1:
        raise ValueError("comparison depth must be positive")
    equivalent = AbstractEffect(
        "safe",
        "write",
        "safe.txt",
        frozenset({"observation"}),
        True,
    )
    system = WorstCasePlanningSystem(
        frozenset({"invoker"}),
        (
            AbstractPlanPatch(
                "safe-a",
                AbstractPatchKind.APPEND_EFFECT,
                frozenset({"observation"}),
                equivalent,
            ),
            AbstractPlanPatch(
                "safe-b",
                AbstractPatchKind.APPEND_EFFECT,
                frozenset({"observation"}),
                equivalent,
            ),
            AbstractPlanPatch(
                "stop",
                AbstractPatchKind.TERMINATE,
                frozenset({"observation"}),
            ),
        ),
        max_plan_nodes=depth + 2,
        max_continuation_depth=depth + 2,
        max_planner_calls=depth + 2,
        max_effects=depth + 2,
    )
    trace_states, trace_transitions = _enumerate_traces(system, depth)
    result = ExplicitStateChecker().verify(
        system,
        (NoUnauthorisedPlanningEffect(),),
        VerificationBounds(
            max_depth=depth,
            max_states=100_000,
            max_transitions=500_000,
            max_model_calls=depth + 2,
        ),
    )
    return {
        "schema_version": "1",
        "fixture": "equivalent-safe-continuations",
        "depth": depth,
        "trace_enumeration": {
            "state_visits": trace_states,
            "transitions": trace_transitions,
        },
        "state_exploration": {
            "unique_states": result.unique_states,
            "transitions": result.transitions,
            "duplicate_states": result.duplicate_states,
            "verdict": result.verdict.value,
        },
    }


def _enumerate_traces(
    system: WorstCasePlanningSystem,
    depth: int,
) -> tuple[int, int]:
    queue: deque[tuple[PlanningModelState, int]] = deque(
        (state, 0) for state in system.initial_states()
    )
    states = len(queue)
    transitions = 0
    while queue:
        state, current_depth = queue.popleft()
        if current_depth >= depth or system.is_terminal(state) or system.bound_reached(state):
            continue
        for action in sorted(system.enabled(state), key=system.action_key):
            for target in system.step(state, action):
                transitions += 1
                states += 1
                queue.append((target, current_depth + 1))
    return states, transitions


__all__ = ["comparison"]
