"""Deterministic pointwise policy for trusted-role action arguments."""

from __future__ import annotations

from dataclasses import dataclass, field

from conflux.domain import (
    Action,
    ActionArgument,
    ArgumentRole,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    PrimitiveAction,
    Principal,
)


@dataclass(frozen=True, slots=True)
class ArgumentPolicyGrant:
    principal_id: str
    operation: str
    argument_name: str
    role: ArgumentRole
    value_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.principal_id or not self.operation or not self.argument_name:
            raise ValueError("argument policy grant identity must be non-empty")
        if self.value_fingerprint is not None and (
            len(self.value_fingerprint) != 64 or any(character not in "0123456789abcdef" for character in self.value_fingerprint)
        ):
            raise ValueError("argument policy grant fingerprint must be SHA-256")


@dataclass(frozen=True, slots=True)
class InMemoryArgumentAuthorisationPolicy:
    grants: frozenset[ArgumentPolicyGrant] = field(default_factory=frozenset)
    policy_id: str = "in-memory-argument-policy"
    policy_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "grants", frozenset(self.grants))

    def decide(
        self,
        principal: Principal,
        action: Action,
        argument: ActionArgument,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        _ = environment
        if not isinstance(action, PrimitiveAction):
            return Decision(
                DecisionCategory.AUTHORISATION,
                False,
                "argument_action_unsupported",
                self.policy_id,
                self.policy_version,
            )
        allowed = any(
            grant.principal_id == principal.id
            and grant.operation == action.operation
            and grant.argument_name == argument.name
            and grant.role == argument.role
            and (grant.value_fingerprint is None or grant.value_fingerprint == argument.value_fingerprint)
            for grant in self.grants
        )
        return Decision(
            DecisionCategory.AUTHORISATION,
            allowed,
            "argument_grant" if allowed else "argument_deny",
            self.policy_id,
            self.policy_version,
            evidence=(
                principal.id,
                action.operation,
                argument.name,
                argument.role.value,
                argument.value_fingerprint,
            ),
        )


__all__ = ["ArgumentPolicyGrant", "InMemoryArgumentAuthorisationPolicy"]
