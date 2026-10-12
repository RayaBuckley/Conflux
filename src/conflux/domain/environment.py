"""Provider-neutral data and immutable environment snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .artifacts import Artifact
from .identity import Principal
from .provenance import Provenance
from .resources import ResourceRef


@dataclass(frozen=True, slots=True)
class DataItem:
    """A provider-neutral data value with authorship and reader sets."""

    id: str
    value: Any
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

    @property
    def provenance_source(self) -> str:
        """Return the provenance source that names this item (SEM-020)."""
        return f"environment:{self.id}"

    def to_artifact(self) -> Artifact[Any]:
        """Convert this data item into a provenance-bearing artifact.

        The artifact names the item in its provenance sources, so a rule over an argument's origin
        can read which item supplied the value; the item's authors stay in the principals and read
        policy stays a separate decision (SEM-004, SEM-020).
        """
        provenance = (
            Provenance.from_principals(self.authors)
            .with_source(self.provenance_source)
            .with_activity("environment_input")
            if self.authors
            else Provenance.unknown(source=self.provenance_source)
        )
        return Artifact(
            id=self.id,
            value=self.value,
            provenance=provenance,
            label=self.label,
            confidential=self.confidential,
        )


@dataclass(frozen=True, slots=True)
class EnvironmentSnapshot:
    """An immutable snapshot of environment data and resources."""

    id: str
    data: tuple[DataItem, ...] = ()
    resources: tuple[ResourceRef, ...] = ()
    version: str = "1"
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        if not self.id or not self.version:
            raise ValueError("EnvironmentSnapshot id and version must be non-empty")
        object.__setattr__(self, "data", tuple(self.data))
        object.__setattr__(self, "resources", tuple(self.resources))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        if len({item.id for item in self.data}) != len(self.data):
            raise ValueError("EnvironmentSnapshot data ids must be unique")

    def data_item(self, item_id: str) -> DataItem | None:
        """Return the data item with the given id, or None."""
        return next((item for item in self.data if item.id == item_id), None)

    def resource(self, resource_id: str) -> ResourceRef | None:
        """Return the resource reference with the given id, or None."""
        return next((item for item in self.resources if item.resource_id == resource_id), None)

    def artifacts(self) -> tuple[Artifact[Any], ...]:
        """Convert all data items in the snapshot into artifacts."""
        return tuple(item.to_artifact() for item in self.data)

    @property
    def all_principals(self) -> frozenset[Principal]:
        """Return the union of all authors and readers across all data items."""
        result: set[Principal] = set()
        for item in self.data:
            result |= item.authors
            result |= item.readers
        return frozenset(result)


__all__ = ["DataItem", "EnvironmentSnapshot"]
