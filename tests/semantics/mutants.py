"""Test-only defective variants used to validate SLED's security properties.

Each mutant corresponds to a meaningful threat-model or implementation
mistake, not merely an increase in mutation score.  Mutants that are
not yet exercised by the BatchSystem harness (ExpiredDelegationAcceptor,
RevocationIgnorer, NoExpiredDelegation, NoRevocationIgnored) are reserved
for future delegation-specific mutation testing and do not affect the
existing mutation score.

What mutation evidence establishes:
- Correct implementation passes all safety properties.
- Representative plausible incorrect implementations fail.

What mutation evidence does NOT establish:
- Completeness of the threat model.
- Absence of all possible defects.
- Security of the production system in deployment.
"""

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
        if not transition.source.context.is_authority_bearing and transition.target.status == BranchStatus.AUTHORISED:
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
            expected = {principal for artifact in action.inputs for principal in artifact.provenance.principals}
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


@dataclass(frozen=True, slots=True)
class ConsentGrantsAuthority:
    base: DecisionPipeline

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        decision = self.base.decide(
            session=session,
            action=action,
            context=context,
            environment=environment,
        )
        if decision.consent.allowed and not decision.authorisation.allowed:
            from conflux.domain import Decision, DecisionCategory

            return replace(
                decision,
                authorisation=Decision(
                    DecisionCategory.AUTHORISATION,
                    True,
                    "consent_override",
                    decision.authorisation.policy_id,
                    decision.authorisation.policy_version,
                ),
            )
        return decision


@dataclass(frozen=True, slots=True)
class VisibilityImpliesRead:
    policy_id: str = "mutant-visibility-implies-read"
    policy_version: str = "1"

    def decide(
        self,
        principal: Principal,
        artifact: Artifact[Any],
        environment: EnvironmentSnapshot,
    ) -> Decision:
        item = environment.data_item(artifact.id)
        if item is not None and principal in item.readers:
            return Decision(
                DecisionCategory.READ,
                True,
                "reader_grant",
                self.policy_id,
                self.policy_version,
                evidence=(principal.id, artifact.id),
            )
        return Decision(
            DecisionCategory.READ,
            True,
            "visibility_grant",
            self.policy_id,
            self.policy_version,
            evidence=(principal.id, artifact.id),
        )


@dataclass(frozen=True, slots=True)
class CertificateReplayKernel:
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
        if batch.mode == ProposalMode.ALTERNATIVES and len(children) > 1:
            replayed = children[0]
            return tuple(replace(child, certificate=replayed.certificate) if child.certificate is not None else child for child in children)
        return children


@dataclass(frozen=True, slots=True)
class ContextResetOnDeny:
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
        return tuple(replace(child, context=parent.context) if child.status == BranchStatus.BLOCKED else child for child in children)


class NoConsentOverride:
    name: str = "no_consent_override"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        target = transition.target
        if target.status == BranchStatus.AUTHORISED and target.decision is not None:
            if target.decision.authorisation.reason == "consent_override":
                return "consent was used to override an authorisation denial"
        return None


@dataclass(frozen=True, slots=True)
class NoCertificateReplay:
    name: str = "no_certificate_replay"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        target = transition.target
        if target.certificate is not None and target.certificate.branch_id != target.branch_id:
            return "certificate was replayed from a different branch"
        return None


@dataclass(frozen=True, slots=True)
class ExpiredDelegationAcceptor:
    """Defective pipeline that ignores delegation expiry timestamps."""

    base: DecisionPipeline

    def decide(
        self,
        *,
        session: Session,
        action: Action,
        context: PrincipalContext,
        environment: EnvironmentSnapshot,
    ) -> ActionDecision:
        return self.base.decide(
            session=session,
            action=action,
            context=context,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class RevocationIgnorer:
    """Defective kernel that accepts revoked delegations."""

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
        return self.base.expand_batch(
            parent=parent,
            batch=batch,
            session=session,
            environment=environment,
            model_calls=model_calls,
        )


class NoExpiredDelegation:
    name: str = "no_expired_delegation"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        target = transition.target
        if target.status == BranchStatus.AUTHORISED and target.action is not None:
            if target.action.kind.value == "delegation":
                return "expired delegation was accepted"
        return None


class NoRevocationIgnored:
    name: str = "no_revocation_ignored"

    def violation(
        self,
        transition: Transition[BranchState, ProposalBatch],
    ) -> str | None:
        target = transition.target
        if target.status == BranchStatus.AUTHORISED and target.action is not None:
            if target.action.kind.value == "delegation":
                return "revoked delegation was accepted"
        return None


def with_read_policy(
    pipeline: DecisionPipeline,
    read: ReadPolicyPort,
) -> DecisionPipeline:
    return replace(pipeline, read=read)
