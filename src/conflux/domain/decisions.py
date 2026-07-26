"""Typed outcomes for independent security checks and their composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .identity import PrincipalContext


class DecisionCategory(StrEnum):
    """Security check represented by a decision."""

    AUTHORISATION = "authorisation"
    VISIBILITY = "visibility"
    CONSENT = "consent"


@dataclass(frozen=True, slots=True)
class Decision:
    """Immutable result of one named security check."""

    category: DecisionCategory
    allowed: bool
    reason: str
    context: PrincipalContext = field(default_factory=PrincipalContext)
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MediationDecision:
    """Composition of authorisation, visibility, and consent decisions."""

    authorisation: Decision
    visibility: Decision
    consent: Decision

    @property
    def allowed(self) -> bool:
        """Return true only when every independent check allows the action."""
        return all((self.authorisation.allowed, self.visibility.allowed, self.consent.allowed))


__all__ = ["Decision", "DecisionCategory", "MediationDecision"]
