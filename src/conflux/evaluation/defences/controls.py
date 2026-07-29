"""Executable negative-control decision engines for evaluator validation."""

from __future__ import annotations

from dataclasses import dataclass, replace

from conflux.application import DecisionPipeline
from conflux.domain import (
    Action,
    ActionDecision,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    PrimitiveAction,
    PrincipalContext,
    Session,
)
from conflux.ites import BranchState, BranchStatus

from ..model_checking import Transition


@dataclass(frozen=True, slots=True)
class CanonicalITES:
    pipeline: DecisionPipeline
    name: str = "ites"

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        return self.pipeline.decide(
            session=session,
            action=action,
            context=context,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class NoDefence:
    name: str = "no_defence"

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        _ = session, action, environment
        return ActionDecision(
            context,
            _allow(DecisionCategory.AUTHORISATION, self.name),
            _allow(DecisionCategory.READ, self.name),
            _allow(DecisionCategory.VISIBILITY, self.name),
            _allow(DecisionCategory.CONSENT, self.name),
        )


@dataclass(frozen=True, slots=True)
class UnionPermissions:
    pipeline: DecisionPipeline
    name: str = "union_permissions"

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        canonical = self.pipeline.decide(
            session=session,
            action=action,
            context=context,
            environment=environment,
        )
        if not context.is_authority_bearing or not isinstance(action, PrimitiveAction):
            return canonical
        allowed = False
        for principal in context.principals:
            try:
                allowed = allowed or self.pipeline.authorisation.decide(
                    principal,
                    action,
                    environment,
                ).allowed
            except Exception:
                allowed = False
        return replace(
            canonical,
            authorisation=Decision(
                DecisionCategory.AUTHORISATION,
                allowed,
                "any_principal_authorised" if allowed else "no_principal_authorised",
                self.name,
                "1",
            ),
        )


@dataclass(frozen=True, slots=True)
class InitiatorOnly:
    pipeline: DecisionPipeline
    name: str = "initiator_only"

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        if not context.principals:
            narrowed = context
        else:
            narrowed = PrincipalContext.from_principals(
                frozenset({min(context.principals)})
            )
        return self.pipeline.decide(
            session=session,
            action=action,
            context=narrowed,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class LatestInputOnly:
    pipeline: DecisionPipeline
    name: str = "latest_input_only"

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        if not action.inputs:
            return self.pipeline.decide(
                session=session,
                action=action,
                context=context,
                environment=environment,
            )
        latest = action.inputs[-1]
        narrowed_action = (
            replace(action, inputs=(latest,))
            if isinstance(action, PrimitiveAction)
            else action
        )
        return self.pipeline.decide(
            session=session,
            action=narrowed_action,
            context=latest.provenance.context,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class NoReadCheck:
    pipeline: DecisionPipeline
    name: str = "no_read_check"

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        canonical = self.pipeline.decide(
            session=session,
            action=action,
            context=context,
            environment=environment,
        )
        if not context.is_authority_bearing:
            return canonical
        return replace(
            canonical,
            read=_allow(DecisionCategory.READ, self.name),
        )


@dataclass(frozen=True, slots=True)
class ForbiddenAuthorisation:
    action_id: str
    name: str = "forbidden_fixture_authorisation"

    def violation(
        self,
        transition: Transition[BranchState, Action],
    ) -> str | None:
        target = transition.target
        if (
            target.status == BranchStatus.AUTHORISED
            and target.action is not None
            and target.action.id == self.action_id
        ):
            return f"fixture marked {self.action_id} as forbidden"
        return None


def _allow(category: DecisionCategory, policy_id: str) -> Decision:
    return Decision(category, True, "negative_control_allow", policy_id, "1")


__all__ = [
    "CanonicalITES",
    "ForbiddenAuthorisation",
    "InitiatorOnly",
    "LatestInputOnly",
    "NoDefence",
    "NoReadCheck",
    "UnionPermissions",
]
