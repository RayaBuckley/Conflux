"""Application-owned composition of independent policy decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from conflux.domain import (
    Action,
    ActionDecision,
    Decision,
    DecisionCategory,
    DelegationAction,
    EnvironmentSnapshot,
    NoOpAction,
    PrimitiveAction,
    PrincipalContext,
    Session,
    StopAction,
)
from conflux.ports import AuthorisationPort, ConsentPolicyPort, ReadPolicyPort, VisibilityPolicyPort


@dataclass(frozen=True, slots=True)
class DecisionPipeline:
    authorisation: AuthorisationPort
    read: ReadPolicyPort
    visibility: VisibilityPolicyPort
    consent: ConsentPolicyPort

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        safe_control = isinstance(action, (StopAction, NoOpAction))
        if not context.is_authority_bearing and not safe_control:
            return _context_denial(context)

        authorisation = self._authorise(action, context, environment)
        read = self._read(action, context, environment)
        visibility = _guarded(
            DecisionCategory.VISIBILITY,
            self.visibility.policy_id,
            self.visibility.policy_version,
            lambda: self.visibility.decide(session, action, context),
        )
        consent = _guarded(
            DecisionCategory.CONSENT,
            self.consent.policy_id,
            self.consent.policy_version,
            lambda: self.consent.decide(session, action, context),
        )
        return ActionDecision(context, authorisation, read, visibility, consent)

    def _authorise(
        self,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        if isinstance(action, DelegationAction):
            return Decision(
                DecisionCategory.AUTHORISATION,
                False,
                "delegation_unsupported",
                "ites-kernel",
                "1",
            )
        if not isinstance(action, PrimitiveAction):
            return Decision(
                DecisionCategory.AUTHORISATION,
                True,
                "not_authority_bearing",
                "ites-kernel",
                "1",
            )
        results: list[Decision] = []
        for principal in sorted(context.principals):
            try:
                decision = self.authorisation.decide(principal, action, environment)
            except Exception as error:
                decision = Decision(
                    DecisionCategory.AUTHORISATION,
                    False,
                    "policy_error",
                    self.authorisation.policy_id,
                    self.authorisation.policy_version,
                    evidence=(type(error).__name__,),
                )
            results.append(decision)
        decisions = tuple(results)
        return _compose(
            DecisionCategory.AUTHORISATION,
            decisions,
            self.authorisation.policy_id,
            self.authorisation.policy_version,
            "all_principals_authorised",
            "principal_denied",
        )

    def _read(
        self,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        if not action.inputs:
            return Decision(
                DecisionCategory.READ,
                True,
                "no_inputs",
                self.read.policy_id,
                self.read.policy_version,
            )
        results: list[Decision] = []
        for principal in sorted(context.principals):
            for artifact in action.inputs:
                try:
                    decision = self.read.decide(principal, artifact, environment)
                except Exception as error:
                    decision = Decision(
                        DecisionCategory.READ,
                        False,
                        "policy_error",
                        self.read.policy_id,
                        self.read.policy_version,
                        evidence=(type(error).__name__,),
                    )
                results.append(decision)
        decisions = tuple(results)
        return _compose(
            DecisionCategory.READ,
            decisions,
            self.read.policy_id,
            self.read.policy_version,
            "all_reads_authorised",
            "read_denied",
        )


def _context_denial(context: PrincipalContext) -> ActionDecision:
    reason = "unknown_principal_context" if context.unknown else "empty_principal_context"

    def denial(category: DecisionCategory) -> Decision:
        return Decision(category, False, reason, "ites-kernel", "1")

    return ActionDecision(
        context,
        denial(DecisionCategory.AUTHORISATION),
        denial(DecisionCategory.READ),
        denial(DecisionCategory.VISIBILITY),
        denial(DecisionCategory.CONSENT),
    )


def _guarded(
    category: DecisionCategory,
    policy_id: str,
    policy_version: str,
    call: Callable[[], Decision],
) -> Decision:
    try:
        decision = call()
    except Exception as error:
        return Decision(
            category,
            False,
            "policy_error",
            policy_id,
            policy_version,
            evidence=(type(error).__name__,),
        )
    if decision.category != category:
        return Decision(
            category,
            False,
            "policy_category_mismatch",
            policy_id,
            policy_version,
            evidence=(decision.category.value,),
        )
    return decision


def _compose(
    category: DecisionCategory,
    decisions: tuple[Decision, ...],
    policy_id: str,
    policy_version: str,
    allow_reason: str,
    deny_reason: str,
) -> Decision:
    allowed = bool(decisions) and all(decision.allowed for decision in decisions)
    evidence = tuple(item for decision in decisions for item in decision.evidence)
    return Decision(
        category,
        allowed,
        allow_reason if allowed else deny_reason,
        policy_id,
        policy_version,
        evidence=evidence,
    )


__all__ = ["DecisionPipeline"]
