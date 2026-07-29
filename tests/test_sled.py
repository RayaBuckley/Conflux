"""Native bounded SLED model-checking tests."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.application import DecisionPipeline
from conflux.domain import Artifact, EnvironmentSnapshot, NoOpAction, Principal, Provenance, Session
from conflux.evaluation import (
    ExplicitStateChecker,
    ITESVerificationSystem,
    NoForbiddenObservation,
    NoUnauthorisedAuthorisation,
    PrincipalContextMonotonicity,
    ProvenancePreserved,
    Transition,
    VerificationBounds,
    VerificationVerdict,
)
from conflux.ites import BranchState, TransitionKernel


@dataclass(frozen=True)
class Graph:
    edges: dict[int, tuple[int, ...]]

    def initial_states(self) -> tuple[int, ...]:
        return (0,)

    def enabled(self, state: int) -> tuple[int, ...]:
        return self.edges.get(state, ())

    def step(self, state: int, action: int) -> tuple[int, ...]:
        _ = state
        return (action,)

    def is_terminal(self, state: int) -> bool:
        return not self.edges.get(state)

    def state_key(self, state: int) -> str:
        return str(state)

    def action_key(self, action: int) -> tuple[object, ...]:
        return (action,)

    def model_calls(self, state: int) -> int:
        return state


@dataclass(frozen=True)
class ForbiddenState:
    forbidden: int
    name: str = "forbidden_state"

    def violation(self, transition: Transition[int, int]) -> str | None:
        return "forbidden" if transition.target == self.forbidden else None


def test_safe_requires_exhausted_state_space() -> None:
    result = ExplicitStateChecker().verify(Graph({0: (1,), 1: ()}), (ForbiddenState(9),))
    assert result.verdict is VerificationVerdict.SAFE


def test_bound_produces_bounded_safe() -> None:
    result = ExplicitStateChecker().verify(
        Graph({0: (1,), 1: (2,), 2: ()}),
        (ForbiddenState(9),),
        VerificationBounds(max_depth=1),
    )
    assert result.verdict is VerificationVerdict.BOUNDED_SAFE
    assert result.truncated


def test_breadth_first_counterexample_is_minimal() -> None:
    graph = Graph({0: (1, 2), 1: (3,), 2: (4,), 3: (9,), 4: (5,), 5: (9,)})
    result = ExplicitStateChecker().verify(graph, (ForbiddenState(9),))
    assert result.verdict is VerificationVerdict.UNSAFE
    assert result.counterexample is not None
    assert result.counterexample.length == 3


def test_cycles_are_deduplicated() -> None:
    result = ExplicitStateChecker().verify(Graph({0: (1,), 1: (0,)}), (ForbiddenState(9),))
    assert result.verdict is VerificationVerdict.SAFE
    assert result.unique_states == 2
    assert result.duplicate_states == 1


class BrokenGraph(Graph):
    def enabled(self, state: int) -> tuple[int, ...]:
        raise RuntimeError("broken")


def test_model_error_is_unknown() -> None:
    result = ExplicitStateChecker().verify(BrokenGraph({0: (1,)}), (ForbiddenState(9),))
    assert result.verdict is VerificationVerdict.UNKNOWN
    assert "RuntimeError" in (result.error or "")


def test_ites_white_box_properties_are_executable(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
) -> None:
    principal = Principal("alice", "Alice")
    initial = BranchState.initial(
        (Artifact("input", "x", Provenance.from_principal(principal)),)
    )
    system = ITESVerificationSystem(
        (initial,),
        (NoOpAction("noop"),),
        TransitionKernel(pipeline),
        Session("s", frozenset({principal})),
        environment,
    )
    result = ExplicitStateChecker().verify(
        system,
        (
            NoUnauthorisedAuthorisation(),
            NoForbiddenObservation(),
            PrincipalContextMonotonicity(),
            ProvenancePreserved(),
        ),
    )
    assert result.verdict is VerificationVerdict.SAFE
