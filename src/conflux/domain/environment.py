"""Provider-neutral immutable evaluation inputs and environment snapshots.

Purpose
Layer: domain
Dependencies: Principal, Provenance, Artifact, and standard-library values.
Public API: DataItem and EnvironmentSnapshot.
Security/data invariants: authors/readers are immutable; scenario metadata is
not added to provenance; snapshots contain no provider implementation state.
Related documentation and tests: docs/ARCHITECTURE.md, docs/EVALUATION.md,
tests/test_environment_contract.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from conflux.core.artifacts import Artifact
from conflux.core.principals import Principal
from conflux.core.provenance import Provenance


@dataclass(frozen=True, slots=True)
class DataItem:
    """Immutable provider-neutral information item used by evaluation."""

    id: str
    authors: frozenset[Principal] = field(default_factory=frozenset)
    readers: frozenset[Principal] = field(default_factory=frozenset)
    label: str | None = None
    confidential: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("DataItem.id must be non-empty")
        object.__setattr__(self, "authors", frozenset(self.authors))
        object.__setattr__(self, "readers", frozenset(self.readers))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def provenance(self) -> Provenance:
        """Return security provenance, excluding scenario metadata."""
        result = Provenance.from_principals(self.authors)
        if self.confidential:
            result = result.with_tag("confidential")
        return result

    def to_artifact(self) -> Artifact["DataItem"]:
        """Convert this item to an artifact with the canonical input operation."""
        return Artifact(
            value=self,
            provenance=self.provenance().with_operation("environment_input"),
            label=self.label,
            confidential=self.confidential,
        )

    def can_read(self, principal: Principal) -> bool:
        """Return whether a Principal may read this item."""
        return principal in self.readers

    def with_metadata(self, **updates: Any) -> "DataItem":
        """Return a copy with evaluation metadata changed only."""
        metadata = dict(self.metadata)
        metadata.update(updates)
        return replace(self, metadata=metadata)


@dataclass(frozen=True, slots=True)
class EnvironmentSnapshot:
    """Immutable provider-neutral collection of evaluation data."""

    data: frozenset[DataItem] = field(default_factory=frozenset)
    provider_id: str = "environment"
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("EnvironmentSnapshot.provider_id must be non-empty")
        object.__setattr__(self, "data", frozenset(self.data))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def contains_all(self, items: Iterable[DataItem]) -> bool:
        """Return whether every item is present in the snapshot."""
        return all(item in self.data for item in items)

    def as_artifacts(self) -> frozenset[Artifact[DataItem]]:
        """Materialise all data as provenance-bearing artifacts."""
        return frozenset(item.to_artifact() for item in self.data)


__all__ = ["DataItem", "EnvironmentSnapshot"]
