"""Bounded delegation monitor and deliberately defective variants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from conflux.domain import fingerprint

from .model_checking import Transition


class DelegationMutation(StrEnum):
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
    mutation: DelegationMutation = DelegationMutation.CANONICAL

    def initial_states(self) -> tuple[DelegationModelState, ...]:
        return (DelegationModelState(),)

    def enabled(self, state: DelegationModelState) -> tuple[str, ...]:
        return () if state.terminal else ("attempt_delegated_use",)

    def step(self, state: DelegationModelState, action: str) -> tuple[DelegationModelState, ...]:
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
        return state.terminal

    def state_key(self, state: DelegationModelState) -> str:
        return fingerprint(state)

    def action_key(self, action: str) -> tuple[object, ...]:
        return (action,)

    def model_calls(self, state: DelegationModelState) -> int:
        return int(state.terminal)


@dataclass(frozen=True, slots=True)
class DelegationAttenuated:
    name: str = "delegation_attenuated"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        return None if transition.target.scope_preserved else "delegation widened its exact scope"


@dataclass(frozen=True, slots=True)
class DelegationBeneficiaryBound:
    name: str = "delegation_beneficiary_bound"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        return None if transition.target.beneficiary_bound else "delegation authorized the wrong beneficiary"


@dataclass(frozen=True, slots=True)
class DelegationSingleUse:
    name: str = "delegation_single_use"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        return "delegation was reused" if transition.target.use_count > 1 else None


@dataclass(frozen=True, slots=True)
class DelegationExpiryEnforced:
    name: str = "delegation_expiry_enforced"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        return None if transition.target.expiry_enforced else "delegation expiry was bypassed"


@dataclass(frozen=True, slots=True)
class DelegationRevocationEnforced:
    name: str = "delegation_revocation_enforced"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        return None if transition.target.revocation_enforced else "delegation revocation was bypassed"


@dataclass(frozen=True, slots=True)
class DelegationNotRedelegated:
    name: str = "delegation_not_redelegated"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        return "delegation was redelegated" if transition.target.redelegated else None


@dataclass(frozen=True, slots=True)
class DelegationPrecedesInfluence:
    name: str = "delegation_precedes_influence"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
        return None if transition.target.issued_before_influence else "delegation was issued after untrusted influence"


@dataclass(frozen=True, slots=True)
class DelegationContextPreserved:
    name: str = "delegation_context_preserved"

    def violation(self, transition: Transition[DelegationModelState, str]) -> str | None:
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
