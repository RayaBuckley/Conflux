"""Information provenance, separate from access-control policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable

from .identity import Principal, PrincipalContext


class ProvenancePrecision(StrEnum):
    EXACT = "exact"
    CONSERVATIVE = "conservative"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Provenance:
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
    def unknown(cls, *, source: str = "unknown") -> "Provenance":
        return cls(
            sources=frozenset({source}),
            precision=ProvenancePrecision.UNKNOWN,
            attested=False,
        )

    @classmethod
    def from_principal(cls, principal: Principal, *, source: str | None = None) -> "Provenance":
        return cls(
            principals=frozenset({principal}),
            sources=frozenset({source}) if source else frozenset(),
        )

    @classmethod
    def from_principals(cls, principals: Iterable[Principal]) -> "Provenance":
        principal_set = frozenset(principals)
        return cls(
            principals=principal_set,
            precision=ProvenancePrecision.EXACT if principal_set else ProvenancePrecision.UNKNOWN,
            attested=bool(principal_set),
        )

    @property
    def is_unknown(self) -> bool:
        return self.precision == ProvenancePrecision.UNKNOWN or not self.attested or not self.principals

    @property
    def context(self) -> PrincipalContext:
        return PrincipalContext(self.principals, unknown=self.is_unknown)

    def merge(self, other: "Provenance") -> "Provenance":
        precision = max(self.precision, other.precision, key=_precision_rank)
        return Provenance(
            principals=self.principals | other.principals,
            sources=self.sources | other.sources,
            activities=self.activities + tuple(
                activity for activity in other.activities if activity not in self.activities
            ),
            precision=precision,
            attested=self.attested and other.attested,
        )

    def with_activity(self, activity: str) -> "Provenance":
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
    if not items:
        return Provenance.unknown(source="empty_union")
    result = items[0]
    for item in items[1:]:
        result = result.merge(item)
    return result


__all__ = ["Provenance", "ProvenancePrecision", "provenance_union"]
