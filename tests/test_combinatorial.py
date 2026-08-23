"""Tests for combinatorial worst-case exploration mode."""

from __future__ import annotations

import pytest

from conflux.domain import (
    ActionDecision,
    DataItem,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    NestedExecutionAction,
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
from conflux.ites import BranchState, BranchStatus, TransitionKernel

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


class TestFromEnvironment:
    """The from_environment factory auto-generates nested execution actions."""

    def test_generates_nested_execution_actions_from_data(self) -> None:
        alice = Principal("alice", "Alice")
        env = EnvironmentSnapshot(
            id="env",
            data=(
                DataItem("d1", "a", frozenset({alice}), frozenset({alice})),
                DataItem("d2", "b", frozenset({alice}), frozenset({alice})),
            ),
        )
        system = CombinatorialVerificationSystem.from_environment(
            environment=env,
            primitive_actions=(_make_action("write"),),
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({alice})),
            max_nested_inputs=2,
        )
        nested = [a for a in system.actions if isinstance(a, NestedExecutionAction)]
        assert len(nested) == 3  # {d1}, {d2}, {d1,d2}
        primitives = [a for a in system.actions if isinstance(a, PrimitiveAction)]
        assert len(primitives) == 1

    def test_respects_max_nested_inputs(self) -> None:
        alice = Principal("alice", "Alice")
        env = EnvironmentSnapshot(
            id="env",
            data=tuple(DataItem(f"d{i}", f"v{i}", frozenset({alice}), frozenset({alice})) for i in range(4)),
        )
        system = CombinatorialVerificationSystem.from_environment(
            environment=env,
            primitive_actions=(_make_action("write"),),
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({alice})),
            max_nested_inputs=1,
        )
        nested = [a for a in system.actions if isinstance(a, NestedExecutionAction)]
        assert len(nested) == 4  # only singletons

    def test_initial_inputs_default_to_environment_artifacts(self) -> None:
        alice = Principal("alice", "Alice")
        env = EnvironmentSnapshot(
            id="env",
            data=(DataItem("d1", "a", frozenset({alice}), frozenset({alice})),),
        )
        system = CombinatorialVerificationSystem.from_environment(
            environment=env,
            primitive_actions=(_make_action("write"),),
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({alice})),
        )
        initial = system.initial_states()[0]
        assert len(initial.inputs) == 1
        assert initial.inputs[0].id == "d1"

    def test_verification_runs_with_from_environment(self) -> None:
        alice = Principal("alice", "Alice")
        env = EnvironmentSnapshot(
            id="env",
            data=(DataItem("d1", "a", frozenset({alice}), frozenset({alice})),),
        )
        system = CombinatorialVerificationSystem.from_environment(
            environment=env,
            primitive_actions=(_make_action("write"),),
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({alice})),
            max_nested_inputs=1,
            max_batch_size=1,
        )
        checker = ExplicitStateChecker()
        result = checker.verify(
            system,
            (),
            VerificationBounds(max_depth=2, max_states=100, max_transitions=100, max_model_calls=2),
        )
        assert result.verdict in (VerificationVerdict.SAFE, VerificationVerdict.BOUNDED_SAFE)
        assert result.unique_states > 0


class TestDepthDependentOptions:
    """Depth-dependent option sets restrict proposals at the final model-call depth."""

    def test_final_primitive_only_restricts_at_last_depth(self) -> None:
        alice = Principal("alice", "Alice")
        from conflux.domain import Artifact, Provenance

        artifact = Artifact("a1", "v", Provenance.from_principal(alice))
        nested = NestedExecutionAction(id="nested-1", inputs=(artifact,))
        primitive = _make_action("write")
        system = CombinatorialVerificationSystem(
            initial=(BranchState.initial(()),),
            actions=(primitive, nested),
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({alice})),
            environment=EnvironmentSnapshot(id="env", version="1"),
            max_batch_size=2,
            max_model_calls=2,
            final_primitive_only=True,
        )
        non_final = BranchState.initial(())
        non_final_enabled = system.enabled(non_final)
        assert any(isinstance(b.proposals[0], NestedExecutionAction) for b in non_final_enabled)

        final_state = BranchState(
            branch_id="final",
            parent_branch_id="root",
            depth=0,
            inputs=(),
            context=PrincipalContext(unknown=True),
            status=BranchStatus.ACTIVE,
            model_calls=1,
        )
        final_enabled = system.enabled(final_state)
        for batch in final_enabled:
            for p in batch.proposals:
                assert isinstance(p, PrimitiveAction)

    def test_final_max_batch_size_overrides_at_last_depth(self) -> None:
        alice = Principal("alice", "Alice")
        primitives = (_make_action("a"), _make_action("b"), _make_action("c"))
        system = CombinatorialVerificationSystem(
            initial=(BranchState.initial(()),),
            actions=primitives,
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({alice})),
            environment=EnvironmentSnapshot(id="env", version="1"),
            max_batch_size=3,
            max_model_calls=2,
            final_max_batch_size=1,
        )
        non_final = BranchState.initial(())
        non_final_enabled = system.enabled(non_final)
        assert len(non_final_enabled) == 7  # 3 singletons + 3 pairs + 1 triple

        final_state = BranchState(
            branch_id="final",
            parent_branch_id="root",
            depth=0,
            inputs=(),
            context=PrincipalContext(unknown=True),
            status=BranchStatus.ACTIVE,
            model_calls=1,
        )
        final_enabled = system.enabled(final_state)
        assert len(final_enabled) == 3  # only singletons with final_max_batch_size=1

    def test_defaults_preserve_uniform_behaviour(self) -> None:
        alice = Principal("alice", "Alice")
        primitive = _make_action("a")
        system = CombinatorialVerificationSystem(
            initial=(BranchState.initial(()),),
            actions=(primitive,),
            kernel=_make_kernel(),
            session=Session(id="test", participants=frozenset({alice})),
            environment=EnvironmentSnapshot(id="env", version="1"),
            max_batch_size=1,
            max_model_calls=2,
        )
        non_final = BranchState.initial(())
        final_state = BranchState(
            branch_id="final",
            parent_branch_id="root",
            depth=0,
            inputs=(),
            context=PrincipalContext(unknown=True),
            status=BranchStatus.ACTIVE,
            model_calls=1,
        )
        assert len(system.enabled(non_final)) == len(system.enabled(final_state))
