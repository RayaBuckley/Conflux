"""Test-only defective variants used to validate SLED's security properties."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Protocol

from conflux.application import DecisionPipeline
from conflux.domain import (
    Action,
    ActionDecision,
    Artifact,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    Principal,
    PrincipalContext,
    ProposalBatch,
    ProposalMode,
    Session,
)
from conflux.evaluation import Transition
from conflux.ites import BranchState, BranchStatus, TransitionKernel
from conflux.ports import ReadPolicyPort


@dataclass(frozen=True, slots=True)
class EmptyContextAllow:
    base: DecisionPipeline
    fallback: Principal

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        substituted = context
        if not context.is_authority_bearing:
            substituted = PrincipalContext(frozenset({self.fallback}))
        decision = self.base.decide(
            session=session,
            action=action,
            context=substituted,
            environment=environment,
        )
        return replace(decision, context=context)


@dataclass(frozen=True, slots=True)
class PermissionUnion:
    base: DecisionPipeline

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        for principal in sorted(context.principals):
            decision = self.base.decide(
                session=session,
                action=action,
                context=PrincipalContext(frozenset({principal})),
                environment=environment,
            )
            if decision.allowed:
                return replace(decision, context=context)
        return self.base.decide(
            session=session,
            action=action,
            context=context,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class ProvenanceAsReadPolicy:
    policy_id: str = "mutant-provenance-acl"
    policy_version: str = "1"

    def decide(
        self,
        principal: Principal,
        artifact: Artifact[Any],
        environment: EnvironmentSnapshot,
    ) -> Decision:
        _ = environment
        allowed = principal in artifact.provenance.principals
        return Decision(
            DecisionCategory.READ,
            allowed,
            "provenance_member" if allowed else "provenance_nonmember",
            self.policy_id,
            self.policy_version,
        )


@dataclass(frozen=True, slots=True)
class StaleContextKernel:
    base: TransitionKernel

    def expand_batch(
        self,
        *,
        parent: BranchState,
        batch: ProposalBatch,
        session: Session,
        environment: EnvironmentSnapshot,
        model_calls: int,
    ) -> tuple[BranchState, ...]:
        children = self.base.expand_batch(
            parent=parent,
            batch=batch,
            session=session,
            environment=environment,
            model_calls=model_calls,
        )
        return tuple(replace(child, context=parent.context) for child in children)


@dataclass(frozen=True, slots=True)
class SiblingLeakKernel:
    base: TransitionKernel

    def expand_batch(
        self,
        *,
        parent: BranchState,
        batch: ProposalBatch,
        session: Session,
        environment: EnvironmentSnapshot,
        model_calls: int,
    ) -> tuple[BranchState, ...]:
        if batch.mode != ProposalMode.ALTERNATIVES:
            return self.base.expand_batch(
                parent=parent,
                batch=batch,
                session=session,
                environment=environment,
                model_calls=model_calls,
            )
        current = parent
        result: list[BranchState] = []
        for proposal in batch.proposals:
            child = self.base.expand_batch(
                parent=current,
                batch=ProposalBatch.alternatives(proposal),
                session=session,
                environment=environment,
                model_calls=model_calls,
            )[0]
            result.append(child)
            current = child
        return tuple(result)


class BatchKernel(Protocol):
    def expand_batch(
        self,
        *,
        parent: BranchState,
        batch: ProposalBatch,
        session: Session,
        environment: EnvironmentSnapshot,
        model_calls: int,
    ) -> tuple[BranchState, ...]: ...


@dataclass(frozen=True, slots=True)
class BatchSystem:
    initial: BranchState
    batch: ProposalBatch
    kernel: BatchKernel
    session: Session
    environment: EnvironmentSnapshot

    def initial_states(self) -> tuple[BranchState, ...]:
        return (self.initial,)

    def enabled(self, state: BranchState) -> tuple[ProposalBatch, ...]:
        return (self.batch,) if state.status == BranchStatus.ACTIVE else ()

    def step(self, state: BranchState, batch: ProposalBatch) -> tuple[BranchState, ...]:
        return self.kernel.expand_batch(
            parent=state,
            batch=batch,
            session=self.session,
            environment=self.environment,
            model_calls=state.model_calls + 1,
        )

    def is_terminal(self, state: BranchState) -> bool:
        return state.status != BranchStatus.ACTIVE

    def state_key(self, state: BranchState) -> str:
        return state.state_key

    def action_key(self, batch: ProposalBatch) -> tuple[object, ...]:
        return (batch.mode.value, batch.fingerprint)

    def model_calls(self, state: BranchState) -> int:
        return state.model_calls


@dataclass(frozen=True, slots=True)
class NoAuthorityWithoutContext:
    name: str = "no_authority_without_context"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        if (
            not transition.source.context.is_authority_bearing
            and transition.target.status == BranchStatus.AUTHORISED
        ):
            return "empty or unknown context authorised an action"
        return None


@dataclass(frozen=True, slots=True)
class NoMixedContextUnion:
    name: str = "no_mixed_context_union"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        target = transition.target
        if len(target.context.principals) > 1 and target.status == BranchStatus.AUTHORISED:
            return "an any-principal decision authorised a mixed context"
        return None


@dataclass(frozen=True, slots=True)
class NoAuthorAsReader:
    readers: frozenset[Principal]
    name: str = "no_author_as_reader"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        target = transition.target
        if target.status != BranchStatus.AUTHORISED:
            return None
        if not target.context.principals.issubset(self.readers):
            return "provenance authors were treated as readers"
        return None


@dataclass(frozen=True, slots=True)
class NoSiblingLeakage:
    name: str = "no_sibling_leakage"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        if transition.target.parent_branch_id != transition.source.branch_id:
            return "an alternative inherited a sibling branch"
        return None


@dataclass(frozen=True, slots=True)
class NestedInputsInfluenceContext:
    name: str = "nested_inputs_influence_context"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        for action in transition.action.proposals:
            expected = {
                principal
                for artifact in action.inputs
                for principal in artifact.provenance.principals
            }
            if not expected.issubset(transition.target.context.principals):
                return "nested input provenance was omitted from the context"
        return None


@dataclass(frozen=True, slots=True)
class ExecutedInvariantOnly:
    name: str = "executed_invariant_only"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        if transition.target.status == BranchStatus.BLOCKED:
            return "a rejected proposal was misclassified as an executed violation"
        return None


def with_read_policy(
    pipeline: DecisionPipeline,
    read: ReadPolicyPort,
) -> DecisionPipeline:
    return replace(pipeline, read=read)
