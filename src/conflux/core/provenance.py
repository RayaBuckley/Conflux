"""
Information provenance.

This module models the provenance of artifacts: who authored them, who
contributed to them, and which principals should be treated as influencers for
authorisation and visibility checks.

This is intentionally information provenance only.

Decision provenance belongs on actions.
Consent belongs to action evaluation.
Chat visibility belongs to the conversation policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, FrozenSet, Iterable

from .principals import Principal


@dataclass(frozen=True, slots=True)
class Provenance:
    """
    Information provenance for an artifact.

    Attributes
    ----------
    principals:
        The principals that contributed to the artifact.
    sources:
        Optional human-readable source labels or system identifiers.
    tags:
        Opaque provenance tags for adapters, benchmark harnesses, or tracing.
    """

    principals: FrozenSet[Principal] = field(default_factory=frozenset)
    sources: FrozenSet[str] = field(default_factory=frozenset)
    tags: FrozenSet[str] = field(default_factory=frozenset)
    resources: FrozenSet[Any] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "principals", frozenset(self.principals))
        object.__setattr__(self, "sources", frozenset(self.sources))
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "resources", frozenset(self.resources))

    @classmethod
    def empty(cls) -> "Provenance":
        """Return an empty provenance object."""
        return cls()

    @classmethod
    def from_principal(
        cls,
        principal: Principal,
        *,
        source: str | None = None,
        tag: str | None = None,
    ) -> "Provenance":
        """Create provenance containing a single principal."""
        sources = frozenset({source}) if source is not None else frozenset()
        tags = frozenset({tag}) if tag is not None else frozenset()
        return cls(principals=frozenset({principal}), sources=sources, tags=tags)

    @classmethod
    def from_resource(cls, resource: Any) -> "Provenance":
        """Create provenance whose source is a protected resource."""
        return cls(resources=frozenset({resource}))

    def with_operation(self, operation: str) -> "Provenance":
        """Return a copy recording a derivation operation."""
        return Provenance(
            principals=self.principals,
            sources=self.sources,
            tags=self.tags | {operation},
            resources=self.resources,
        )

    @classmethod
    def from_principals(
        cls,
        principals: Iterable[Principal],
        *,
        sources: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
    ) -> "Provenance":
        """Create provenance from an iterable of principals."""
        return cls(
            principals=frozenset(principals),
            sources=frozenset(sources or ()),
            tags=frozenset(tags or ()),
        )

    def add_principal(
        self,
        principal: Principal,
        *,
        source: str | None = None,
        tag: str | None = None,
    ) -> "Provenance":
        """Return a copy with one more contributing principal."""
        sources = set(self.sources)
        tags = set(self.tags)

        if source is not None:
            sources.add(source)
        if tag is not None:
            tags.add(tag)

        return Provenance(
            principals=self.principals | {principal},
            sources=frozenset(sources),
            tags=frozenset(tags),
        )

    def add_principals(
        self,
        principals: Iterable[Principal],
        *,
        sources: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
    ) -> "Provenance":
        """Return a copy with additional contributing principals."""
        return Provenance(
            principals=self.principals | frozenset(principals),
            sources=self.sources | frozenset(sources or ()),
            tags=self.tags | frozenset(tags or ()),
        )

    def merge(self, other: "Provenance") -> "Provenance":
        """
        Merge two provenance objects.

        This is the main combinator used by derived artifacts.
        """
        return Provenance(
            principals=self.principals | other.principals,
            sources=self.sources | other.sources,
            tags=self.tags | other.tags,
            resources=self.resources | other.resources,
        )

    def with_source(self, source: str) -> "Provenance":
        """Return a copy with one extra source label."""
        return Provenance(
            principals=self.principals,
            sources=self.sources | {source},
            tags=self.tags,
        )

    def with_tag(self, tag: str) -> "Provenance":
        """Return a copy with one extra provenance tag."""
        return Provenance(
            principals=self.principals,
            sources=self.sources,
            tags=self.tags | {tag},
        )

    def contains(self, principal: Principal) -> bool:
        """Return True if the principal is part of this provenance."""
        return principal in self.principals

    def is_empty(self) -> bool:
        """Return True if no principals are recorded."""
        return not self.principals

    def __bool__(self) -> bool:
        return not self.is_empty()


def authors_for(provenance: Provenance) -> frozenset[Principal]:
    """Compatibility helper returning the principals contributing to provenance."""
    return provenance.principals


def provenance_union(*items: Provenance) -> Provenance:
    """Merge any number of provenance objects into one."""
    result = Provenance.empty()
    for item in items:
        result = result.merge(item)
    return result


__all__ = [
    "Provenance",
    "authors_for",
    "provenance_union",
]
