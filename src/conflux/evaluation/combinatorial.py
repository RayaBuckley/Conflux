"""Combinatorial worst-case exploration for SLED.

Explores all possible proposal subsets (powerset of actions) at each
state, independent of any specific model.  This enables worst-case
security analysis: if no proposal subset leads to a violation, the
system is safe regardless of model behaviour.

This mode is only feasible for small finite instances (same as the
prototype's ``max_depth=3``).  It should be opt-in and bounded.

The combinatorial adapter uses ``ProposalBatch`` as the action type.
At each state, ``enabled()`` returns all possible proposal subsets
of the configured actions.  ``step()`` expands each batch through
the ITES kernel, producing one or more successor branches.

The ``from_environment`` factory auto-generates ``NestedExecutionAction``
candidates from environment data items, matching the original
prototype's powerset-of-data enumeration.

Depth-dependent option sets are supported via ``final_primitive_only``
and ``final_max_batch_size``, matching the prototype's distinction
between intermediate and final LLM call option sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

from conflux.domain import (
    Action,
    Artifact,
    EnvironmentSnapshot,
    NestedExecutionAction,
    PrimitiveAction,
    ProposalBatch,
    Session,
    action_sort_key,
)
from conflux.ites import BranchState, BranchStatus, TransitionKernel


def _powerset(items: tuple[Action, ...], max_size: int) -> tuple[ProposalBatch, ...]:
    """Return all non-empty proposal subsets up to ``max_size``.

    The empty subset is excluded because an empty proposal batch terminates
    the branch without effect.
    """
    sorted_items = tuple(sorted(items, key=action_sort_key))
    result: list[ProposalBatch] = []
    for r in range(1, min(max_size, len(sorted_items)) + 1):
        for combo in combinations(sorted_items, r):
            result.append(ProposalBatch.alternatives(*combo))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class CombinatorialVerificationSystem:
    """White-box adapter exploring all proposal subsets through the ITES kernel.

    Unlike ``ITESVerificationSystem``, which explores single actions, this
    adapter enumerates all possible proposal batches at each state.  This
    enables worst-case security analysis independent of model behaviour.

    Attributes:
        initial: the initial branch states.
        actions: the set of actions to form proposal subsets from.
        kernel: the ITES transition kernel.
        session: the session context.
        environment: the environment snapshot.
        max_batch_size: maximum number of proposals per batch (controls
            combinatorial explosion).
    """

    initial: tuple[BranchState, ...]
    actions: tuple[Action, ...]
    kernel: TransitionKernel
    session: Session
    environment: EnvironmentSnapshot
    max_batch_size: int = 2
    max_model_calls: int = 3
    final_primitive_only: bool = False
    final_max_batch_size: int | None = None

    def initial_states(self) -> tuple[BranchState, ...]:
        """Return the initial branch states for exploration."""
        return self.initial

    def enabled(self, state: BranchState) -> tuple[ProposalBatch, ...]:
        """Return all possible proposal subsets for exploration.

        When ``final_primitive_only`` is set, the final model-call depth
        restricts proposals to ``PrimitiveAction`` only, matching the
        prototype's ``last_options`` behaviour.  When
        ``final_max_batch_size`` is set, it overrides ``max_batch_size``
        at the final depth.
        """
        if state.status != BranchStatus.ACTIVE:
            return ()
        is_final = state.model_calls >= self.max_model_calls - 1
        if is_final and self.final_primitive_only:
            actions: tuple[Action, ...] = tuple(a for a in self.actions if isinstance(a, PrimitiveAction))
        else:
            actions = self.actions
        batch_size = self.final_max_batch_size if is_final and self.final_max_batch_size is not None else self.max_batch_size
        return _powerset(actions, batch_size)

    @classmethod
    def from_environment(
        cls,
        *,
        environment: EnvironmentSnapshot,
        primitive_actions: tuple[PrimitiveAction, ...],
        kernel: TransitionKernel,
        session: Session,
        max_batch_size: int = 2,
        max_nested_inputs: int = 3,
        initial_inputs: tuple[Artifact[Any], ...] | None = None,
        max_model_calls: int = 3,
        final_primitive_only: bool = False,
        final_max_batch_size: int | None = None,
    ) -> CombinatorialVerificationSystem:
        """Create a combinatorial system with auto-generated nested execution actions.

        Generates ``NestedExecutionAction`` candidates from non-empty subsets
        of environment data items (up to ``max_nested_inputs`` size), matching
        the original prototype's ``powerset(environment.data)`` enumeration.

        Args:
            environment: the environment snapshot to derive data from.
            primitive_actions: primitive actions to include in the action set.
            kernel: the ITES transition kernel.
            session: the session context.
            max_batch_size: maximum proposals per batch for non-final depths.
            max_nested_inputs: maximum number of data items per nested
                execution action (controls combinatorial explosion).
            initial_inputs: initial branch inputs; defaults to all environment
                artifacts.
            max_model_calls: maximum model calls per branch.
            final_primitive_only: if True, restrict final-depth proposals to
                primitives only.
            final_max_batch_size: if set, overrides ``max_batch_size`` at the
                final depth.
        """
        artifacts = environment.artifacts()
        nested_actions: list[NestedExecutionAction] = []
        for r in range(1, min(max_nested_inputs, len(artifacts)) + 1):
            for combo in combinations(artifacts, r):
                nested_actions.append(
                    NestedExecutionAction(
                        id=f"nested-{r}-{'-'.join(a.id for a in combo)}",
                        inputs=combo,
                    ),
                )
        all_actions: tuple[Action, ...] = (*primitive_actions, *nested_actions)
        inputs = initial_inputs if initial_inputs is not None else artifacts
        return cls(
            initial=(BranchState.initial(inputs),),
            actions=all_actions,
            kernel=kernel,
            session=session,
            environment=environment,
            max_batch_size=max_batch_size,
            max_model_calls=max_model_calls,
            final_primitive_only=final_primitive_only,
            final_max_batch_size=final_max_batch_size,
        )

    def step(self, state: BranchState, batch: ProposalBatch) -> tuple[BranchState, ...]:
        """Expand a proposal batch under the ITES kernel, yielding successor branches."""
        return self.kernel.expand_batch(
            parent=state,
            batch=batch,
            session=self.session,
            environment=self.environment,
            model_calls=state.model_calls + 1,
        )

    def is_terminal(self, state: BranchState) -> bool:
        """Whether the branch has reached a non-active terminal status."""
        return state.status != BranchStatus.ACTIVE

    def state_key(self, state: BranchState) -> str:
        """Return the canonical deduplication key for a branch state."""
        return state.state_key

    def action_key(self, batch: ProposalBatch) -> tuple[object, ...]:
        """Return a stable sort key for a proposal batch."""
        return tuple(action_sort_key(action) for action in batch.proposals)

    def model_calls(self, state: BranchState) -> int:
        """Return the number of model calls consumed by a branch."""
        return state.model_calls


__all__ = [
    "CombinatorialVerificationSystem",
]
