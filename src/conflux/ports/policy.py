"""Port for provider-independent policy decisions."""

from __future__ import annotations

from typing import Protocol

from conflux.core.actions import Action
from conflux.core.session import Session
from conflux.domain.decisions import Decision
from conflux.domain.identity import PrincipalContext


class PolicyPort(Protocol):
    """Evaluate one independent policy dimension for an action."""

    def decide(self, session: Session, action: Action[object]) -> Decision:
        """Return a typed decision with reason and evidence."""
        ...


class AuthorisationPort(Protocol):
    """Evaluate collective authorisation without owning Principal identity."""

    def decide(self, action: Action[object], context: PrincipalContext) -> Decision:
        """Return an intersection-rule authorisation decision."""
        ...


__all__ = ["AuthorisationPort", "PolicyPort"]
