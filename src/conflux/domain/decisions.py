"""Typed independent policy decisions and deterministic composition.

SEM-005: ActionDecision.allowed is the conjunction of all independent decision
dimensions (authorisation, argument_authorisation when present, read,
visibility, consent). No single dimension can override a denial in another.

SEM-006: Consent never manufactures authority. A consent allow cannot override
an authorisation denial.

SEM-007: Authorisation requires a pointwise allow from every Principal in the
context. One Principal cannot lend permissions to another.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .identity import PrincipalContext


class DecisionCategory(StrEnum):
    """Independent dimensions along which a policy decision is evaluated."""

    AUTHORISATION = "authorisation"
    READ = "read"
    VISIBILITY = "visibility"
    CONSENT = "consent"


@dataclass(frozen=True, slots=True)
class Decision:
    """An immutable single-dimension policy decision with evidence."""

    category: DecisionCategory
    allowed: bool
    reason: str
    policy_id: str
    policy_version: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reason or not self.policy_id or not self.policy_version:
            raise ValueError("Decision reason and policy identity must be non-empty")

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""
        return {
            "category": self.category.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class ActionDecision:
    """The composite of independent decisions for a single action."""

    context: PrincipalContext
    authorisation: Decision
    read: Decision
    visibility: Decision
    consent: Decision
    argument_authorisation: Decision | None = None

    @property
    def allowed(self) -> bool:
        """Return True only when every decision dimension allows the action."""
        return all(decision.allowed for decision in self.decisions)

    @property
    def decisions(self) -> tuple[Decision, ...]:
        """Return all non-optional decision dimensions as a tuple."""
        return (
            (self.authorisation, self.argument_authorisation, self.read, self.visibility, self.consent)
            if self.argument_authorisation is not None
            else (self.authorisation, self.read, self.visibility, self.consent)
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""
        return {
            "context": self.context.to_dict(),
            "allowed": self.allowed,
            "argument_authorisation": (self.argument_authorisation.to_dict() if self.argument_authorisation is not None else None),
            "decisions": [decision.to_dict() for decision in self.decisions],
        }


__all__ = ["ActionDecision", "Decision", "DecisionCategory"]
