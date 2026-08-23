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
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from conflux.domain import (
    Action,
    EnvironmentSnapshot,
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

    def initial_states(self) -> tuple[BranchState, ...]:
        """Return the initial branch states for exploration."""
        return self.initial

    def enabled(self, state: BranchState) -> tuple[ProposalBatch, ...]:
        """Return all possible proposal subsets for exploration."""
        if state.status != BranchStatus.ACTIVE:
            return ()
        return _powerset(self.actions, self.max_batch_size)

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
