"""Information provenance, separate from access-control policy.

SEM-003: Provenance.merge forms a commutative monoid. Precision is monotone
(EXACT < CONSERVATIVE < UNKNOWN); merge takes the maximum. Attestation is
conjunction: both sides must be attested for the result to be attested.
Unknown provenance propagates through merge.

SEM-004: Provenance describes influence origin; it is not a read ACL. Read
policy is a separate, independent decision.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

from .identity import Principal, PrincipalContext


class ProvenancePrecision(StrEnum):
    """Monotone precision rank for provenance values."""

    EXACT = "exact"
    CONSERVATIVE = "conservative"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Provenance:
    """Immutable information provenance describing the origin of influence."""

    principals: frozenset[Principal] = field(default_factory=frozenset)
    sources: frozenset[str] = field(default_factory=frozenset)
    activities: tuple[str, ...] = ()
    precision: ProvenancePrecision = ProvenancePrecision.EXACT
    attested: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "principals", frozenset(self.principals))
        object.__setattr__(self, "sources", frozenset(self.sources))
        object.__setattr__(self, "activities", tuple(self.activities))

    @classmethod
    def unknown(cls, *, source: str = "unknown") -> Provenance:
        """Return an unattested, unknown-precision provenance."""
        return cls(
            sources=frozenset({source}),
            precision=ProvenancePrecision.UNKNOWN,
            attested=False,
        )

    @classmethod
    def from_principal(cls, principal: Principal, *, source: str | None = None) -> Provenance:
        """Return exact provenance rooted at a single principal."""
        return cls(
            principals=frozenset({principal}),
            sources=frozenset({source}) if source else frozenset(),
        )

    @classmethod
    def from_principals(cls, principals: Iterable[Principal]) -> Provenance:
        """Return exact provenance rooted at a set of principals."""
        principal_set = frozenset(principals)
        return cls(
            principals=principal_set,
            precision=ProvenancePrecision.EXACT if principal_set else ProvenancePrecision.UNKNOWN,
            attested=bool(principal_set),
        )

    @property
    def is_unknown(self) -> bool:
        """Return True when provenance is unattested, unknown, or principal-free."""
        return self.precision == ProvenancePrecision.UNKNOWN or not self.attested or not self.principals

    @property
    def context(self) -> PrincipalContext:
        """Return the conservative PrincipalContext implied by this provenance."""
        return PrincipalContext(self.principals, unknown=self.is_unknown)

    def merge(self, other: Provenance) -> Provenance:
        """Return the commutative-monoid merge of two provenance values."""
        precision = max(self.precision, other.precision, key=_precision_rank)
        return Provenance(
            principals=self.principals | other.principals,
            sources=self.sources | other.sources,
            activities=self.activities + tuple(activity for activity in other.activities if activity not in self.activities),
            precision=precision,
            attested=self.attested and other.attested,
        )

    def with_activity(self, activity: str) -> Provenance:
        """Return a copy of this provenance with an additional activity."""
        if not activity:
            raise ValueError("activity must be non-empty")
        return Provenance(
            principals=self.principals,
            sources=self.sources,
            activities=self.activities + (activity,),
            precision=self.precision,
            attested=self.attested,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""
        return {
            "principal_ids": sorted(principal.id for principal in self.principals),
            "sources": sorted(self.sources),
            "activities": list(self.activities),
            "precision": self.precision.value,
            "attested": self.attested,
        }


def _precision_rank(precision: ProvenancePrecision) -> int:
    return {
        ProvenancePrecision.EXACT: 0,
        ProvenancePrecision.CONSERVATIVE: 1,
        ProvenancePrecision.UNKNOWN: 2,
    }[precision]


def provenance_union(*items: Provenance) -> Provenance:
    """Return the monoid merge of zero or more provenance values."""
    if not items:
        return Provenance.unknown(source="empty_union")
    result = items[0]
    for item in items[1:]:
        result = result.merge(item)
    return result


__all__ = ["Provenance", "ProvenancePrecision", "provenance_union"]
