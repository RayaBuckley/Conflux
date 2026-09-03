"""Native bounded SLED model-checking tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from conflux.application import DecisionPipeline
from conflux.domain import (
    Action,
    ActionArgument,
    ActionDecision,
    ArgumentRole,
    Artifact,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    NestedExecutionAction,
    NoOpAction,
    Permission,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    Provenance,
    ResourceRef,
    Session,
)
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
from conflux.ites import BranchState, BranchStatus, TransitionKernel

pytestmark = pytest.mark.security


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
    initial = BranchState.initial((Artifact("input", "x", Provenance.from_principal(principal)),))
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


# ---------------------------------------------------------------------------
# Direct unit tests for SLED property violation() methods.
# These cover both the violation and non-violation branches that SLED
# integration exercises only indirectly.
# ---------------------------------------------------------------------------


def _allow_decision() -> ActionDecision:
    """A decision where every dimension allows."""
    allow = Decision(DecisionCategory.AUTHORISATION, True, "allow", "auth", "1")
    read = Decision(DecisionCategory.READ, True, "allow", "read", "1")
    vis = Decision(DecisionCategory.VISIBILITY, True, "allow", "vis", "1")
    consent = Decision(DecisionCategory.CONSENT, True, "allow", "consent", "1")
    return ActionDecision(
        context=PrincipalContext.from_principals(frozenset({Principal("alice", "Alice")})),
        authorisation=allow,
        read=read,
        visibility=vis,
        consent=consent,
    )


def test_no_unauthorised_authorisation_passes_when_decision_allows() -> None:
    """Non-violation: AUTHORISED with an allowing decision."""
    principal = Principal("alice", "Alice")
    state = BranchState.initial(())
    authorised = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({principal})),
        status=BranchStatus.AUTHORISED,
        decision=_allow_decision(),
    )
    transition: Transition[BranchState, Action] = Transition(state, NoOpAction("noop"), authorised)
    assert NoUnauthorisedAuthorisation().violation(transition) is None


def test_no_forbidden_observation_passes_when_read_and_visibility_allow() -> None:
    """Non-violation: AUTHORISED with read and visibility both allowed."""
    principal = Principal("alice", "Alice")
    state = BranchState.initial(())
    authorised = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({principal})),
        status=BranchStatus.AUTHORISED,
        decision=_allow_decision(),
    )
    transition: Transition[BranchState, Action] = Transition(state, NoOpAction("noop"), authorised)
    assert NoForbiddenObservation().violation(transition) is None


def test_principal_context_monotonicity_passes_when_context_grows() -> None:
    """Non-violation: context grows monotonically (superset)."""
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    source = BranchState(
        branch_id="root",
        parent_branch_id=None,
        depth=0,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({alice})),
    )
    target = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({alice, bob})),
    )
    transition: Transition[BranchState, Action] = Transition(source, NoOpAction("noop"), target)
    assert PrincipalContextMonotonicity().violation(transition) is None


def test_principal_context_monotonicity_detects_unknown_to_known() -> None:
    """Violation: unknown=True silently converted to unknown=False."""
    source = BranchState(
        branch_id="root",
        parent_branch_id=None,
        depth=0,
        inputs=(),
        context=PrincipalContext(unknown=True),
    )
    target = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({Principal("alice", "Alice")})),
    )
    transition: Transition[BranchState, Action] = Transition(source, NoOpAction("noop"), target)
    violation = PrincipalContextMonotonicity().violation(transition)
    assert violation is not None
    assert "unknown" in violation


def test_provenance_preserved_passes_for_non_nested_action() -> None:
    """Non-violation: PrimitiveAction is not NestedExecutionAction."""
    alice = Principal("alice", "Alice")
    state = BranchState.initial(())
    target = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({alice})),
    )
    action: Action = PrimitiveAction("act", "write", Permission("write"), ResourceRef("test", "res", "doc"))
    transition: Transition[BranchState, Action] = Transition(state, action, target)
    assert ProvenancePreserved().violation(transition) is None


def test_provenance_preserved_passes_when_provenance_carried() -> None:
    """Non-violation: NestedExecutionAction with all input provenance in context."""
    alice = Principal("alice", "Alice")
    artifact = Artifact("test", "data", Provenance.from_principal(alice))
    state = BranchState.initial(())
    target = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(artifact,),
        context=PrincipalContext.from_principals(frozenset({alice})),
    )
    action: Action = NestedExecutionAction("nested", (artifact,))
    transition: Transition[BranchState, Action] = Transition(state, action, target)
    assert ProvenancePreserved().violation(transition) is None


def test_argument_selectors_authorised_passes_when_no_arguments() -> None:
    """Non-violation: no authority-bearing arguments present."""
    alice = Principal("alice", "Alice")
    state = BranchState.initial(())
    authorised = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({alice})),
        status=BranchStatus.AUTHORISED,
        decision=_allow_decision(),
    )
    action: Action = PrimitiveAction("act", "write", Permission("write"), ResourceRef("test", "res", "doc"))
    transition: Transition[BranchState, Action] = Transition(state, action, authorised)
    from conflux.evaluation.properties import ArgumentSelectorsAuthorised

    assert ArgumentSelectorsAuthorised().violation(transition) is None


def test_argument_selectors_authorised_passes_when_arg_auth_allows() -> None:
    """Non-violation: authority-bearing argument with argument_authorisation.allowed=True."""
    alice = Principal("alice", "Alice")
    arg = ActionArgument.bind(
        name="cred",
        role=ArgumentRole.CREDENTIAL_REFERENCE,
        value="secret",
        provenance=Provenance.from_principal(alice),
    )
    allow = Decision(DecisionCategory.AUTHORISATION, True, "allow", "auth", "1")
    arg_allow = Decision(DecisionCategory.AUTHORISATION, True, "arg allow", "arg", "1")
    read = Decision(DecisionCategory.READ, True, "allow", "read", "1")
    vis = Decision(DecisionCategory.VISIBILITY, True, "allow", "vis", "1")
    consent = Decision(DecisionCategory.CONSENT, True, "allow", "consent", "1")
    decision = ActionDecision(
        context=PrincipalContext.from_principals(frozenset({alice})),
        authorisation=allow,
        read=read,
        visibility=vis,
        consent=consent,
        argument_authorisation=arg_allow,
    )
    state = BranchState.initial(())
    authorised = BranchState(
        branch_id="b1",
        parent_branch_id="root",
        depth=1,
        inputs=(),
        context=PrincipalContext.from_principals(frozenset({alice})),
        status=BranchStatus.AUTHORISED,
        decision=decision,
    )
    action: Action = PrimitiveAction(
        "act",
        "write",
        Permission("write"),
        ResourceRef("test", "res", "doc"),
        arguments=(arg,),
    )
    transition: Transition[BranchState, Action] = Transition(state, action, authorised)
    from conflux.evaluation.properties import ArgumentSelectorsAuthorised

    assert ArgumentSelectorsAuthorised().violation(transition) is None
