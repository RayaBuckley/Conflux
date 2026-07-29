"""The sole pure ITES transition kernel."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from conflux.domain import (
    Action,
    ActionDecision,
    EnvironmentSnapshot,
    NestedExecutionAction,
    PrincipalContext,
    ProposalBatch,
    ProposalMode,
    Session,
    action_sort_key,
    provenance_union,
)

from .state import (
    ActionOutcome,
    AuthorisedStep,
    BranchState,
    BranchStatus,
    DecisionCertificate,
    TraceEvent,
)


class DecisionEngine(Protocol):
    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision: ...


@dataclass(frozen=True, slots=True)
class TransitionKernel:
    decisions: DecisionEngine

    def expand_batch(
        self,
        *,
        parent: BranchState,
        batch: ProposalBatch,
        session: Session,
        environment: EnvironmentSnapshot,
        model_calls: int,
    ) -> tuple[BranchState, ...]:
        if batch.mode == ProposalMode.ALTERNATIVES:
            ordered = tuple(sorted(batch.proposals, key=action_sort_key))
            return tuple(
                self._transition(
                    parent=parent,
                    action=action,
                    index=index,
                    session=session,
                    environment=environment,
                    model_calls=model_calls,
                )
                for index, action in enumerate(ordered, 1)
            )
        current = parent
        for index, action in enumerate(batch.proposals, 1):
            current = self._transition(
                parent=current,
                action=action,
                index=index,
                session=session,
                environment=environment,
                model_calls=model_calls,
            )
            if current.status == BranchStatus.BLOCKED:
                break
            if index < len(batch.proposals):
                current = replace(current, status=BranchStatus.ACTIVE)
        return (current,)

    def _transition(
        self,
        *,
        parent: BranchState,
        action: Action,
        index: int,
        session: Session,
        environment: EnvironmentSnapshot,
        model_calls: int,
    ) -> BranchState:
        branch_id = f"{parent.branch_id}.{index}"
        proposed = TraceEvent(
            sequence=len(parent.trace),
            branch_id=branch_id,
            parent_branch_id=parent.branch_id,
            depth=parent.depth,
            outcome=ActionOutcome.PROPOSED,
            context=parent.context,
            action=action,
            reason="model_proposal",
        )
        decision = self.decisions.decide(
            session=session,
            action=action,
            context=parent.context,
            environment=environment,
        )
        allowed = decision.allowed
        status = BranchStatus.AUTHORISED if allowed else BranchStatus.BLOCKED
        inputs = parent.inputs
        context = parent.context
        depth = parent.depth
        if allowed and isinstance(action, NestedExecutionAction):
            provenance = provenance_union(*(artifact.provenance for artifact in action.inputs))
            context = context.merge(provenance.context)
            inputs = action.inputs
            depth += 1
            status = BranchStatus.ACTIVE
        outcome = ActionOutcome.AUTHORISED if allowed else ActionOutcome.BLOCKED
        certificate = (
            DecisionCertificate.issue(
                action=action,
                context=context,
                branch_id=branch_id,
                decision=decision,
            )
            if allowed
            else None
        )
        result_event = TraceEvent(
            sequence=len(parent.trace) + 1,
            branch_id=branch_id,
            parent_branch_id=parent.branch_id,
            depth=parent.depth,
            outcome=outcome,
            context=context,
            action=action,
            decision=decision,
            reason="all_decisions_allow" if allowed else _first_denial(decision),
        )
        steps = parent.authorised_steps
        if certificate is not None:
            steps += (AuthorisedStep(action, decision, certificate),)
        return replace(
            parent,
            branch_id=branch_id,
            parent_branch_id=parent.branch_id,
            depth=depth,
            inputs=inputs,
            context=context,
            status=status,
            model_calls=model_calls,
            trace=parent.trace + (proposed, result_event),
            action=action,
            decision=decision,
            certificate=certificate,
            authorised_steps=steps,
        )


def _first_denial(decision: ActionDecision) -> str:
    return next(item.reason for item in decision.decisions if not item.allowed)


__all__ = ["DecisionEngine", "TransitionKernel"]
