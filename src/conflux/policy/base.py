"""Deterministic policy implementations for the canonical ports."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import (
    Action,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    PrimitiveAction,
    Principal,
)


@dataclass(frozen=True, slots=True)
class PolicyGrant:
    """Immutable triple of principal, permission, and optional resource scope."""

    principal_id: str
    permission: str
    resource_id: str | None = None


@dataclass(frozen=True, slots=True)
class InMemoryAuthorisationPolicy:
    """Pointwise offline policy oracle used for specifications and tests."""

    grants: frozenset[PolicyGrant]
    policy_id: str = "in-memory-authorisation"
    policy_version: str = "1"

    def decide(
        self,
        principal: Principal,
        action: Action,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Return an authorisation decision based on matching policy grants."""
        _ = environment
        if not isinstance(action, PrimitiveAction):
            return Decision(
                DecisionCategory.AUTHORISATION,
                True,
                "not_authority_bearing",
                self.policy_id,
                self.policy_version,
            )
        resource_id = action.resource.resource_id if action.resource else None
        allowed = any(
            grant.principal_id == principal.id
            and grant.permission == action.permission.name
            and (grant.resource_id is None or grant.resource_id == resource_id)
            for grant in self.grants
        )
        return Decision(
            DecisionCategory.AUTHORISATION,
            allowed,
            "policy_grant" if allowed else "policy_deny",
            self.policy_id,
            self.policy_version,
            evidence=(principal.id, action.permission.name, resource_id or "*"),
        )


__all__ = ["InMemoryAuthorisationPolicy", "PolicyGrant"]
