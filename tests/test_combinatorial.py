"""Tests for combinatorial worst-case exploration mode."""

from __future__ import annotations

import pytest

from conflux.domain import (
    ActionDecision,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    Permission,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    Session,
)
from conflux.evaluation.combinatorial import CombinatorialVerificationSystem
from conflux.evaluation.model_checking import (
    ExplicitStateChecker,
    VerificationBounds,
    VerificationVerdict,
)
from conflux.ites import BranchState, TransitionKernel

pytestmark = pytest.mark.security


def _make_kernel() -> TransitionKernel:
    class AllowAll:
        def decide(self, *, session, action, context, environment):
            auth = Decision(
                category=DecisionCategory.AUTHORISATION,
                allowed=True,
                reason="test",
                policy_id="test",
                policy_version="1",
            )
            read = Decision(
                category=DecisionCategory.READ,
                allowed=True,
                reason="test",
                policy_id="test",
                policy_version="1",
            )
            vis = Decision(
                category=DecisionCategory.VISIBILITY,
                allowed=True,
                reason="test",
                policy_id="test",
                policy_version="1",
            )
            consent = Decision(
                category=DecisionCategory.CONSENT,
                allowed=True,
                reason="test",
                policy_id="test",
                policy_version="1",
            )
            return ActionDecision(
                context=context,
                authorisation=auth,
                read=read,
                visibility=vis,
                consent=consent,
            )

    return TransitionKernel(decisions=AllowAll())


def _make_action(action_id: str) -> PrimitiveAction:
    return PrimitiveAction(
        id=action_id,
        operation=action_id,
        permission=Permission(action_id),
    )


class TestCombinatorialSystem:
    """The combinatorial verification system explores all proposal subsets."""

    def test_powerset_generates_all_subsets(self) -> None:
        actions = (_make_action("a"), _make_action("b"))
        system = CombinatorialVerificationSystem(
            initial=(BranchState.initial(()),),
            actions=actions,
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({Principal("alice", "Alice")})),
            environment=EnvironmentSnapshot(id="env", version="1"),
            max_batch_size=2,
        )
        enabled = system.enabled(BranchState.initial(()))
        assert len(enabled) == 3  # {a}, {b}, {a,b}

    def test_max_batch_size_limits_subsets(self) -> None:
        actions = (_make_action("a"), _make_action("b"), _make_action("c"))
        system = CombinatorialVerificationSystem(
            initial=(BranchState.initial(()),),
            actions=actions,
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({Principal("alice", "Alice")})),
            environment=EnvironmentSnapshot(id="env", version="1"),
            max_batch_size=1,
        )
        enabled = system.enabled(BranchState.initial(()))
        assert len(enabled) == 3  # 3 singletons with max_batch_size=1

    def test_disabled_for_terminal_branches(self) -> None:
        system = CombinatorialVerificationSystem(
            initial=(BranchState.initial(()),),
            actions=(_make_action("a"),),
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({Principal("alice", "Alice")})),
            environment=EnvironmentSnapshot(id="env", version="1"),
        )
        blocked = BranchState(
            branch_id="blocked",
            parent_branch_id="root",
            depth=0,
            inputs=(),
            context=PrincipalContext(unknown=True),
            status=BranchState.status if hasattr(BranchState, "status") else "blocked",
        )
        # Use proper blocked status
        from conflux.ites import BranchStatus

        blocked = BranchState(
            branch_id="blocked",
            parent_branch_id="root",
            depth=0,
            inputs=(),
            context=PrincipalContext(unknown=True),
            status=BranchStatus.BLOCKED,
        )
        assert system.enabled(blocked) == ()

    def test_verification_produces_result(self) -> None:
        actions = (_make_action("a"),)
        system = CombinatorialVerificationSystem(
            initial=(BranchState.initial(()),),
            actions=actions,
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({Principal("alice", "Alice")})),
            environment=EnvironmentSnapshot(id="env", version="1"),
            max_batch_size=1,
        )
        checker = ExplicitStateChecker()
        result = checker.verify(system, (), VerificationBounds(max_depth=2, max_states=100, max_transitions=100, max_model_calls=2))
        assert result.verdict in (VerificationVerdict.SAFE, VerificationVerdict.BOUNDED_SAFE)
        assert result.unique_states > 0
