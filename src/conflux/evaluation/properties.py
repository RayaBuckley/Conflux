"""SLED properties and the white-box adapter for the ITES transition kernel."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import (
    Action,
    EnvironmentSnapshot,
    NestedExecutionAction,
    Session,
    action_sort_key,
)
from conflux.ites import BranchState, BranchStatus, TransitionKernel

from .model_checking import Transition


@dataclass(frozen=True, slots=True)
class ITESVerificationSystem:
    initial: tuple[BranchState, ...]
    actions: tuple[Action, ...]
    kernel: TransitionKernel
    session: Session
    environment: EnvironmentSnapshot

    def initial_states(self) -> tuple[BranchState, ...]:
        return self.initial

    def enabled(self, state: BranchState) -> tuple[Action, ...]:
        return self.actions if state.status == BranchStatus.ACTIVE else ()

    def step(self, state: BranchState, action: Action) -> tuple[BranchState, ...]:
        return self.kernel.expand(
            parent=state,
            proposals=(action,),
            session=self.session,
            environment=self.environment,
            model_calls=state.model_calls + 1,
        )

    def is_terminal(self, state: BranchState) -> bool:
        return state.status != BranchStatus.ACTIVE

    def state_key(self, state: BranchState) -> str:
        return state.state_key

    def action_key(self, action: Action) -> tuple[object, ...]:
        return action_sort_key(action)

    def model_calls(self, state: BranchState) -> int:
        return state.model_calls


@dataclass(frozen=True, slots=True)
class NoUnauthorisedAuthorisation:
    name: str = "no_unauthorised_authorisation"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        target = transition.target
        if (
            target.status == BranchStatus.AUTHORISED
            and (target.decision is None or not target.decision.allowed)
        ):
            return "an action was authorised without a fully allowing decision"
        return None


@dataclass(frozen=True, slots=True)
class NoForbiddenObservation:
    name: str = "no_forbidden_observation"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        target = transition.target
        if target.status == BranchStatus.AUTHORISED and target.decision is not None:
            if not target.decision.read.allowed or not target.decision.visibility.allowed:
                return "an action was authorised despite a read or visibility denial"
        return None


@dataclass(frozen=True, slots=True)
class PrincipalContextMonotonicity:
    name: str = "principal_context_monotonicity"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        if not transition.source.context.principals.issubset(transition.target.context.principals):
            return "a transition removed a Principal from the Principal Context"
        if transition.source.context.unknown and not transition.target.context.unknown:
            return "a transition silently converted unknown provenance into trusted provenance"
        return None


@dataclass(frozen=True, slots=True)
class ProvenancePreserved:
    name: str = "provenance_preserved"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        if not isinstance(transition.action, NestedExecutionAction):
            return None
        expected = {
            principal
            for artifact in transition.action.inputs
            for principal in artifact.provenance.principals
        }
        if not expected.issubset(transition.target.context.principals):
            return "nested execution discarded input provenance"
        return None


__all__ = [
    "ITESVerificationSystem",
    "NoForbiddenObservation",
    "NoUnauthorisedAuthorisation",
    "PrincipalContextMonotonicity",
    "ProvenancePreserved",
]
