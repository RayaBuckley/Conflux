"""SLED properties and the white-box adapter for the ITES transition kernel."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import (
    Action,
    ActionArgument,
    EnvironmentSnapshot,
    NestedExecutionAction,
    ProposalBatch,
    Session,
    action_sort_key,
)
from conflux.ites import BranchState, BranchStatus, TransitionKernel

from .model_checking import Transition


@dataclass(frozen=True, slots=True)
class ITESVerificationSystem:
    """White-box adapter exposing the ITES transition kernel for model checking."""

    initial: tuple[BranchState, ...]
    actions: tuple[Action, ...]
    kernel: TransitionKernel
    session: Session
    environment: EnvironmentSnapshot

    def initial_states(self) -> tuple[BranchState, ...]:
        """Return the initial branch states for exploration."""
        return self.initial

    def enabled(self, state: BranchState) -> tuple[Action, ...]:
        """Return actions enabled in a branch, only when it is active."""
        return self.actions if state.status == BranchStatus.ACTIVE else ()

    def step(self, state: BranchState, action: Action) -> tuple[BranchState, ...]:
        """Expand a proposal batch under the ITES kernel, yielding successor branches."""
        return self.kernel.expand_batch(
            parent=state,
            batch=ProposalBatch.alternatives(action),
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

    def action_key(self, action: Action) -> tuple[object, ...]:
        """Return a stable sort key for an action."""
        return action_sort_key(action)

    def model_calls(self, state: BranchState) -> int:
        """Return the number of model calls consumed by a branch."""
        return state.model_calls


@dataclass(frozen=True, slots=True)
class NoUnauthorisedAuthorisation:
    """Ensures authorisation only occurs with a fully allowing decision."""

    name: str = "no_unauthorised_authorisation"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        """Return a reason if an action was authorised without a allowing decision."""
        target = transition.target
        if target.status == BranchStatus.AUTHORISED and (target.decision is None or not target.decision.allowed):
            return "an action was authorised without a fully allowing decision"
        return None


@dataclass(frozen=True, slots=True)
class NoForbiddenObservation:
    """Ensures authorised actions do not violate read or visibility decisions."""

    name: str = "no_forbidden_observation"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        """Return a reason if an authorised action violated read or visibility."""
        target = transition.target
        if target.status == BranchStatus.AUTHORISED and target.decision is not None:
            if not target.decision.read.allowed or not target.decision.visibility.allowed:
                return "an action was authorised despite a read or visibility denial"
        return None


@dataclass(frozen=True, slots=True)
class PrincipalContextMonotonicity:
    """Ensures Principal Context grows monotonically and never loses trust."""

    name: str = "principal_context_monotonicity"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        """Return a reason if a transition shrank context or silently trusted unknown provenance."""
        if not transition.source.context.principals.issubset(transition.target.context.principals):
            return "a transition removed a Principal from the Principal Context"
        if transition.source.context.unknown and not transition.target.context.unknown:
            return "a transition silently converted unknown provenance into trusted provenance"
        return None


@dataclass(frozen=True, slots=True)
class ProvenancePreserved:
    """Ensures nested execution carries all input provenance into the context."""

    name: str = "provenance_preserved"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        """Return a reason if nested execution discarded input provenance."""
        if not isinstance(transition.action, NestedExecutionAction):
            return None
        expected = {principal for artifact in transition.action.inputs for principal in artifact.provenance.principals}
        if not expected.issubset(transition.target.context.principals):
            return "nested execution discarded input provenance"
        return None


@dataclass(frozen=True, slots=True)
class ArgumentSelectorsAuthorised:
    """Ensures authority-bearing selectors are authorised by argument policy."""

    name: str = "argument_selectors_authorised"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        """Return a reason if an authority-bearing selector was authorised without argument policy."""
        arguments = tuple(
            item for item in getattr(transition.action, "arguments", ()) if isinstance(item, ActionArgument) and item.authority_bearing
        )
        if not arguments or transition.target.status != BranchStatus.AUTHORISED:
            return None
        decision = transition.target.decision
        if decision is None or decision.argument_authorisation is None or not decision.argument_authorisation.allowed:
            return "an authority-bearing selector was authorised without argument policy"
        return None


__all__ = [
    "ArgumentSelectorsAuthorised",
    "ITESVerificationSystem",
    "NoForbiddenObservation",
    "NoUnauthorisedAuthorisation",
    "PrincipalContextMonotonicity",
    "ProvenancePreserved",
]
