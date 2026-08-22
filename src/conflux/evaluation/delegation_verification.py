"""Bounded delegation monitor and deliberately defective variants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from conflux.domain import fingerprint

from .model_checking import Transition


class DelegationMutation(StrEnum):
    """Canonical or defective delegation variant under verification."""

    CANONICAL = "canonical"
    WIDENED_SCOPE = "widened_scope"
    WRONG_BENEFICIARY = "wrong_beneficiary"
    REUSE = "reuse"
    EXPIRY_BYPASS = "expiry_bypass"
    REVOCATION_BYPASS = "revocation_bypass"
    REDELEGATION = "redelegation"
    POST_INFLUENCE_ISSUANCE = "post_influence_issuance"


@dataclass(frozen=True, slots=True)
class DelegationModelState:
    """Snapshot of delegation lifecycle invariants for model checking."""

    scope_preserved: bool = True
    beneficiary_bound: bool = True
    use_count: int = 0
    expiry_enforced: bool = True
    revocation_enforced: bool = True
    redelegated: bool = False
    issued_before_influence: bool = True
    principal_context_unchanged: bool = True
    terminal: bool = False


@dataclass(frozen=True, slots=True)
class DelegationVerificationSystem:
    """Transition system modelling a single delegated use under a mutation."""

    mutation: DelegationMutation = DelegationMutation.CANONICAL

    def initial_states(self) -> tuple[DelegationModelState, ...]:
        """Return the single initial delegation model state."""
        return (DelegationModelState(),)

    def enabled(self, state: DelegationModelState) -> tuple[str, ...]:
        """Return the delegated-use action when the state is non-terminal."""
        return () if state.terminal else ("attempt_delegated_use",)

    def step(self, state: DelegationModelState, action: str) -> tuple[DelegationModelState, ...]:
        """Execute a delegated use, producing a terminal state under the mutation."""
        if action != "attempt_delegated_use":
            raise ValueError("unsupported delegation model action")
        mutation = self.mutation
        return (
            DelegationModelState(
                scope_preserved=mutation is not DelegationMutation.WIDENED_SCOPE,
                beneficiary_bound=mutation is not DelegationMutation.WRONG_BENEFICIARY,
                use_count=2 if mutation is DelegationMutation.REUSE else 1,
                expiry_enforced=mutation is not DelegationMutation.EXPIRY_BYPASS,
                revocation_enforced=mutation is not DelegationMutation.REVOCATION_BYPASS,
                redelegated=mutation is DelegationMutation.REDELEGATION,
                issued_before_influence=mutation is not DelegationMutation.POST_INFLUENCE_ISSUANCE,
                principal_context_unchanged=True,
                terminal=True,
            ),
        )

    def is_terminal(self, state: DelegationModelState) -> bool:
        """Whether the delegation model has reached its terminal state."""
        return state.terminal

    def state_key(self, state: DelegationModelState) -> str:
        """Return a canonical deduplication key for a delegation state."""
        return fingerprint(state)

    def action_key(self, action: str) -> tuple[object, ...]:
        """Return a stable sort key for a delegation action."""
        return (action,)

    def model_calls(self, state: DelegationModelState) -> int:
        """Return the model-call count for a delegation state."""
        return int(state.terminal)


@dataclass(frozen=True, slots=True)
class DelegationAttenuated:
    """Ensures a delegation does not widen its exact scope."""

    name: str = "delegation_attenuated"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if the delegation widened its exact scope."""
        return None if transition.target.scope_preserved else "delegation widened its exact scope"


@dataclass(frozen=True, slots=True)
class DelegationBeneficiaryBound:
    """Ensures a delegation authorises only the intended beneficiary."""

    name: str = "delegation_beneficiary_bound"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if the delegation authorised the wrong beneficiary."""
        return None if transition.target.beneficiary_bound else "delegation authorized the wrong beneficiary"


@dataclass(frozen=True, slots=True)
class DelegationSingleUse:
    """Ensures a delegation is consumed at most once."""

    name: str = "delegation_single_use"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if the delegation was reused."""
        return "delegation was reused" if transition.target.use_count > 1 else None


@dataclass(frozen=True, slots=True)
class DelegationExpiryEnforced:
    """Ensures delegation expiry is respected."""

    name: str = "delegation_expiry_enforced"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if delegation expiry was bypassed."""
        return None if transition.target.expiry_enforced else "delegation expiry was bypassed"


@dataclass(frozen=True, slots=True)
class DelegationRevocationEnforced:
    """Ensures delegation revocation is respected."""

    name: str = "delegation_revocation_enforced"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if delegation revocation was bypassed."""
        return None if transition.target.revocation_enforced else "delegation revocation was bypassed"


@dataclass(frozen=True, slots=True)
class DelegationNotRedelegated:
    """Ensures a delegation is not redelegated."""

    name: str = "delegation_not_redelegated"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if the delegation was redelegated."""
        return "delegation was redelegated" if transition.target.redelegated else None


@dataclass(frozen=True, slots=True)
class DelegationPrecedesInfluence:
    """Ensures a delegation is issued before any untrusted influence."""

    name: str = "delegation_precedes_influence"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if the delegation was issued after untrusted influence."""
        return None if transition.target.issued_before_influence else "delegation was issued after untrusted influence"


@dataclass(frozen=True, slots=True)
class DelegationContextPreserved:
    """Ensures a delegation does not narrow the Principal Context."""

    name: str = "delegation_context_preserved"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        """Return a reason if the delegation narrowed the Principal Context."""
        return None if transition.target.principal_context_unchanged else "delegation narrowed Principal Context"


DELEGATION_PROPERTIES = (
    DelegationAttenuated(),
    DelegationBeneficiaryBound(),
    DelegationSingleUse(),
    DelegationExpiryEnforced(),
    DelegationRevocationEnforced(),
    DelegationNotRedelegated(),
    DelegationPrecedesInfluence(),
    DelegationContextPreserved(),
)


__all__ = [
    "DELEGATION_PROPERTIES",
    "DelegationAttenuated",
    "DelegationBeneficiaryBound",
    "DelegationContextPreserved",
    "DelegationExpiryEnforced",
    "DelegationModelState",
    "DelegationMutation",
    "DelegationNotRedelegated",
    "DelegationPrecedesInfluence",
    "DelegationRevocationEnforced",
    "DelegationSingleUse",
    "DelegationVerificationSystem",
]
