"""Application policy services for typed, collective security decisions."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.core.actions import Action, PrimitiveAction
from conflux.domain.decisions import Decision, DecisionCategory
from conflux.domain.identity import PrincipalContext


@dataclass(frozen=True, slots=True)
class AuthorisationService:
    """Apply the collective intersection rule to a declarative action."""

    def decide(self, action: Action[object], context: PrincipalContext) -> Decision:
        """Allow only when every Principal can perform the primitive permission."""
        if not isinstance(action, PrimitiveAction):
            return Decision(
                category=DecisionCategory.AUTHORISATION,
                allowed=True,
                reason="non_primitive_action_delegated_to_action_policy",
                context=context,
            )

        allowed = all(principal.can_perform(action.permission) for principal in context.principals)
        return Decision(
            category=DecisionCategory.AUTHORISATION,
            allowed=allowed,
            reason="all_principals_authorised" if allowed else "principal_missing_permission",
            context=context,
            evidence=(action.permission.name,),
        )


__all__ = ["AuthorisationService"]
