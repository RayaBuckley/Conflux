"""
Core ITES mediation algorithm.

This module contains the executable heart of ITES.

The mediator:
- tracks provenance-derived influence through nested LLM calls,
- only allows nested execution when the current influencers can read the inputs,
- allows primitive actions only when the exact intersection rule is satisfied,
- enforces consent only for the current decision principals,
- respects conversation visibility policy,
- records every step in an immutable execution trace,
- returns a structured report of the run.

This keeps the original prototype's semantics intact while extending the
action model to include message emission, consent requests, delegation, and
other control actions.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Any, Callable, FrozenSet

from conflux.auth.authorisation import AuthorisationDecision, authorise_action
from conflux.core import Artifact, Principal, Provenance
from conflux.core.actions import (
    Action,
    ClarificationRequestAction,
    DelegationAction,
    MessageUserAction,
    NestedExecutionAction,
    NoOpAction,
    PrimitiveAction,
    RequestConsentAction,
    StopAction,
)
from conflux.core.chat_policy import ChatPolicy
from conflux.core.consent import ConsentProfile
from conflux.core.permissions import Permission, normalise_permission
from conflux.core.session import Session

from . import ITES, Declare, Guarantee, ITESReport, LLMCall
from .state import ExecutionState, ExecutionStep

PrimitiveAuthoriser = Callable[[str, FrozenSet[Principal]], bool]
NestedAuthoriser = Callable[[Any, FrozenSet[Principal], FrozenSet[Any]], bool]


def _default_primitive_authoriser(action: str, influencers: FrozenSet[Principal]) -> bool:
    """
    Default primitive action policy.

    The exact intersection rule is enforced locally in the mediator, so this
    hook is only retained for compatibility with older wiring.
    """
    _ = action
    _ = influencers
    return True


def _default_nested_authoriser(
    environment: Any,
    influencers: FrozenSet[Principal],
    inputs: FrozenSet[Any],
) -> bool:
    """
    Default nested execution policy.

    A nested LLM call is permitted only when every current influencer can read
    every proposed input. This is the core safety rule inherited from the
    previous codebase.
    """
    _ = environment

    for item in inputs:
        value = item.value if isinstance(item, Artifact) else item
        readers = frozenset(getattr(value, "readers", frozenset()))
        if not all(principal in readers for principal in influencers):
            return False

    return True


def _artifact_principals(inputs: Iterable[Artifact[Any]]) -> FrozenSet[Principal]:
    """
    Extract the union of principals appearing in artifact provenance.
    """
    principals: set[Principal] = set()
    for artifact in inputs:
        principals.update(artifact.provenance.principals)
    return frozenset(principals)


def _provenance_for_input(item: Any) -> Provenance:
    """
    Build provenance for a raw SLED input item.
    """
    provenance = Provenance()

    for author in getattr(item, "authors", frozenset()):
        provenance = provenance.add_principal(author)

    tag = getattr(item, "tag", None)
    if tag is not None:
        provenance = provenance.with_tag(str(tag))

    return provenance.with_tag("sled_input")


def _materialise_inputs(inputs: FrozenSet[Any]) -> FrozenSet[Artifact[Any]]:
    """
    Convert raw SLED inputs into provenance-bearing artifacts.
    """
    materialised: set[Artifact[Any]] = set()
    for item in inputs:
        if isinstance(item, Artifact):
            materialised.add(item)
            continue

        materialised.add(
            Artifact(
                value=item,
                provenance=_provenance_for_input(item),
                label=getattr(item, "label", None),
                confidential=bool(getattr(item, "confidential", False)),
            )
        )
    return frozenset(materialised)


def _session_from_environment(environment: Any, initial_inputs: FrozenSet[Artifact[Any]]) -> Session:
    """
    Resolve the current session from the environment when one is not supplied.

    Fallback behaviour is conservative:
    - participants are derived from the input provenance,
    - consent defaults to each participant's own permission set,
    - chat visibility defaults to private participants-only visibility.
    """
    if isinstance(environment, Session):
        return environment

    existing = getattr(environment, "session", None)
    if isinstance(existing, Session):
        return existing

    participants = _artifact_principals(initial_inputs)
    consent_profiles = frozenset(
        ConsentProfile(
            principal=principal,
            allowed_permissions=frozenset(principal.permissions),
        )
        for principal in participants
    )
    return Session(
        id=str(getattr(environment, "session_id", "auto-session")),
        participants=participants,
        chat_policy=ChatPolicy(participants=participants),
        consent_profiles=consent_profiles,
    )


def _bind_action_context(
    action: Action[Any],
    current_inputs: FrozenSet[Artifact[Any]],
    influencers: FrozenSet[Principal],
) -> Action[Any]:
    """
    Attach the current decision context to an action.

    This ensures the action's decision provenance is the current influencer set
    and that any missing input set is filled from the current call context.
    """
    if isinstance(action, PrimitiveAction):
        return replace(
            action,
            inputs=action.inputs or current_inputs,
            decision_principals=influencers,
        )

    if isinstance(action, NestedExecutionAction):
        nested_inputs = action.nested_inputs or current_inputs
        nested_inputs = frozenset(nested_inputs)
        return replace(
            action,
            inputs=action.inputs or current_inputs,
            nested_inputs=nested_inputs,
            decision_principals=influencers,
        )

    if isinstance(action, MessageUserAction):
        return replace(
            action,
            inputs=action.inputs or current_inputs,
            decision_principals=influencers,
        )

    if isinstance(action, ClarificationRequestAction):
        return replace(
            action,
            inputs=action.inputs or current_inputs,
            decision_principals=influencers,
        )

    if isinstance(action, RequestConsentAction):
        return replace(
            action,
            inputs=action.inputs or current_inputs,
            decision_principals=influencers,
        )

    if isinstance(action, DelegationAction):
        return replace(
            action,
            inputs=action.inputs or current_inputs,
            decision_principals=influencers,
        )

    if isinstance(action, (StopAction, NoOpAction)):
        return replace(
            action,
            inputs=action.inputs or current_inputs,
            decision_principals=influencers,
        )

    return replace(
        action,
        inputs=action.inputs or current_inputs,
        decision_principals=influencers,
    )


def _primitive_permission_for(action: PrimitiveAction) -> Permission | str:
    """
    Derive the permission to check for a primitive action.

    If the provider operation is more specific than the permission label,
    the explicit permission field wins.
    """
    if action.permission and action.permission.name:
        return action.permission
    return normalise_permission(action.provider_operation)


def _delegation_permissions(action: DelegationAction) -> FrozenSet[Permission]:
    """
    Return the permissions that must be authorised for delegation.
    """
    if action.delegated_permissions:
        return frozenset(action.delegated_permissions)
    return frozenset({Permission("delegate")})


@dataclass(frozen=True, slots=True)
class MediatingITES(ITES):
    """
    Reference mediator for provenance-aware defence execution.
    """

    max_llm_calls: int = 3
    primitive_authoriser: PrimitiveAuthoriser = _default_primitive_authoriser
    nested_authoriser: NestedAuthoriser = _default_nested_authoriser
    session: Session | None = None

    def __post_init__(self) -> None:
        if self.max_llm_calls < 1:
            raise ValueError("max_llm_calls must be at least 1")

    def run(
        self,
        environment: Any,
        initial_inputs: FrozenSet[Artifact[Any]],
        llm_call: LLMCall,
        declare: Declare,
    ) -> ITESReport:
        session = self.session or _session_from_environment(environment, initial_inputs)
        initial_influencers = _artifact_principals(initial_inputs)
        state = ExecutionState(
            environment=environment,
            session=session,
            initial_inputs=initial_inputs,
            max_llm_calls=self.max_llm_calls,
            active_influencers=initial_influencers,
        )

        (
            state,
            nested_inputs_readable,
            primitive_actions_authorised,
            visibility_allowed,
            consent_allowed,
        ) = self._run_branch(
            session=session,
            state=state,
            inputs=initial_inputs,
            influencers=initial_influencers,
            llm_call=llm_call,
            declare=declare,
            depth=1,
            environment=environment,
        )

        state = state.add_guarantee(
            Guarantee(
                name="bounded_llm_calls",
                holds=state.llm_calls_used <= self.max_llm_calls,
                details=(
                    f"Used {state.llm_calls_used} LLM call(s) with limit "
                    f"{self.max_llm_calls}."
                ),
            )
        )
        state = state.add_guarantee(
            Guarantee(
                name="nested_inputs_readable",
                holds=nested_inputs_readable,
                details=(
                    "Every nested execution request satisfied the readability "
                    "check for the current influencers."
                ),
            )
        )
        state = state.add_guarantee(
            Guarantee(
                name="primitive_actions_authorised",
                holds=primitive_actions_authorised,
                details=(
                    "Every primitive action satisfied the exact intersection rule."
                ),
            )
        )
        state = state.add_guarantee(
            Guarantee(
                name="visibility_respected",
                holds=visibility_allowed,
                details=(
                    "Every visible action satisfied the session visibility policy."
                ),
            )
        )
        state = state.add_guarantee(
            Guarantee(
                name="consent_respected",
                holds=consent_allowed,
                details=(
                    "Every consent-sensitive action was approved by the current decision principals."
                ),
            )
        )

        return ITESReport(
            guarantees=state.guarantees,
            declared_actions=state.declared_actions,
            blocked_actions=state.blocked_actions,
        )

    def _run_branch(
        self,
        session: Session,
        state: ExecutionState,
        inputs: FrozenSet[Artifact[Any]],
        influencers: FrozenSet[Principal],
        llm_call: LLMCall,
        declare: Declare,
        depth: int,
        environment: Any,
    ) -> tuple[ExecutionState, bool, bool, bool, bool]:
        """
        Execute one branch of the defence.

        Returns the updated state together with:
        - whether nested execution remained readable,
        - whether primitive actions remained authorised,
        - whether visibility remained respected,
        - whether consent remained respected.
        """
        if not state.can_call_llm():
            return state, True, True, True, True

        state = state.increment_llm_calls()
        proposals = frozenset(llm_call(inputs))

        declared_this_step: set[Any] = set()
        blocked_this_step: set[Any] = set()

        nested_inputs_readable = True
        primitive_actions_authorised = True
        visibility_allowed = True
        consent_allowed = True

        for raw_proposal in proposals:
            proposal: Action[Any] | None = raw_proposal if isinstance(raw_proposal, Action) else None
            if proposal is None:
                blocked_this_step.add(raw_proposal)
                state = state.record_blocked(raw_proposal)
                continue

            proposal = _bind_action_context(proposal, inputs, influencers)

            if isinstance(proposal, PrimitiveAction):
                if not self.primitive_authoriser(proposal.provider_operation, influencers):
                    primitive_actions_authorised = False
                    blocked_this_step.add(proposal)
                    state = state.record_blocked(proposal)
                    continue

            if isinstance(proposal, NestedExecutionAction):
                nested_inputs = frozenset(proposal.nested_inputs or proposal.inputs)
                if not self.nested_authoriser(environment, influencers, nested_inputs):
                    nested_inputs_readable = False
                    blocked_this_step.add(proposal)
                    state = state.record_blocked(proposal)
                    continue

            decision: AuthorisationDecision = authorise_action(session, proposal)

            if not decision.allowed:
                blocked_this_step.add(proposal)
                state = state.record_blocked(proposal)

                if isinstance(proposal, PrimitiveAction):
                    primitive_actions_authorised = False

                if isinstance(proposal, NestedExecutionAction):
                    nested_inputs_readable = False

                if not decision.visibility_allowed:
                    visibility_allowed = False

                if decision.consent is not None and decision.consent.state != decision.consent.state.ALLOW:
                    consent_allowed = False
                elif decision.consent is None and not decision.visibility_allowed:
                    consent_allowed = False

                continue

            declare(proposal)
            declared_this_step.add(proposal)
            state = state.record_declared(proposal)

            if isinstance(proposal, NestedExecutionAction):
                nested_artifacts = _materialise_inputs(frozenset(proposal.nested_inputs or proposal.inputs))
                next_influencers = influencers | _artifact_principals(nested_artifacts)

                state = state.with_influencers(next_influencers)
                (
                    state,
                    child_nested_ok,
                    child_primitive_ok,
                    child_visibility_ok,
                    child_consent_ok,
                ) = self._run_branch(
                    session=session,
                    state=state,
                    inputs=nested_artifacts,
                    influencers=next_influencers,
                    llm_call=llm_call,
                    declare=declare,
                    depth=depth + 1,
                    environment=environment,
                )
                nested_inputs_readable = nested_inputs_readable and child_nested_ok
                primitive_actions_authorised = primitive_actions_authorised and child_primitive_ok
                visibility_allowed = visibility_allowed and child_visibility_ok
                consent_allowed = consent_allowed and child_consent_ok

        state = state.add_step(
            ExecutionStep(
                depth=depth,
                inputs=inputs,
                proposals=proposals,
                declared=frozenset(declared_this_step),
                blocked=frozenset(blocked_this_step),
                influencers=influencers,
                note="mediated_llm_call",
            )
        )

        return state, nested_inputs_readable, primitive_actions_authorised, visibility_allowed, consent_allowed


__all__ = [
    "MediatingITES",
]
