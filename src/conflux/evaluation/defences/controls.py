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
    """Canonical ITES defence that delegates to the full decision pipeline."""

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
        """Delegate the authorisation decision to the decision pipeline."""
        return self.pipeline.decide(
            session=session,
            action=action,
            context=context,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class NoDefence:
    """Negative control that unconditionally allows every decision."""

    name: str = "no_defence"

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        """Allow all decision categories regardless of context."""
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
    """Defective control that authorises if any context principal is authorised."""

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
        """Authorise the action if any principal in the context is authorised."""
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
                allowed = (
                    allowed
                    or self.pipeline.authorisation.decide(
                        principal,
                        action,
                        environment,
                    ).allowed
                )
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
    """Defective control that narrows the context to a single initiator."""

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
        """Evaluate the pipeline using only the lexicographically smallest principal."""
        if not context.principals:
            narrowed = context
        else:
            narrowed = PrincipalContext.from_principals(frozenset({min(context.principals)}))
        return self.pipeline.decide(
            session=session,
            action=action,
            context=narrowed,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class LatestInputOnly:
    """Defective control that considers only the most recent input's provenance."""

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
        """Evaluate the pipeline using only the latest input and its provenance."""
        if not action.inputs:
            return self.pipeline.decide(
                session=session,
                action=action,
                context=context,
                environment=environment,
            )
        latest = action.inputs[-1]
        narrowed_action = replace(action, inputs=(latest,)) if isinstance(action, PrimitiveAction) else action
        return self.pipeline.decide(
            session=session,
            action=narrowed_action,
            context=latest.provenance.context,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class NoReadCheck:
    """Defective control that skips the read permission check."""

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
        """Allow read for authority-bearing contexts, bypassing the read decision."""
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
    """Safety property that marks a specific action id as forbidden."""

    action_id: str
    name: str = "forbidden_fixture_authorisation"

    def violation(
        self,
        transition: Transition[BranchState, Action],
    ) -> str | None:
        """Return a reason if the forbidden action was authorised."""
        target = transition.target
        if target.status == BranchStatus.AUTHORISED and target.action is not None and target.action.id == self.action_id:
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
