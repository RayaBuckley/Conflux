"""Owner policy expressed as a normal policy oracle, never a bypass."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import Action, Decision, DecisionCategory, EnvironmentSnapshot, PrimitiveAction, Principal


@dataclass(frozen=True, slots=True)
class OwnerAuthorisationPolicy:
    policy_id: str = "owner-authorisation"
    policy_version: str = "1"

    def decide(
        self,
        principal: Principal,
        action: Action,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        _ = environment
        owner_id = (
            action.resource.attributes.get("owner_id")
            if isinstance(action, PrimitiveAction) and action.resource is not None
            else None
        )
        allowed = owner_id == principal.id
        return Decision(
            DecisionCategory.AUTHORISATION,
            allowed,
            "owner_grant" if allowed else "owner_deny",
            self.policy_id,
            self.policy_version,
            evidence=(str(owner_id), principal.id),
        )


__all__ = ["OwnerAuthorisationPolicy"]
