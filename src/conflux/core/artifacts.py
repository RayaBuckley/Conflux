"""
Provenance-bearing artifacts.

An Artifact is a value plus the provenance needed to reason about influence,
consent, and visibility.

This is the core information-flow unit for the system:

- user messages become artifacts,
- tool outputs become artifacts,
- derived information becomes artifacts,
- nested execution consumes artifacts and produces new artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Generic, TypeVar

from .principals import Principal
from .provenance import Provenance

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Artifact(Generic[T]):
    """
    A provenance-bearing value.

    Attributes
    ----------
    value:
        The underlying payload.
    provenance:
        Provenance metadata describing how the artifact was produced.
    label:
        Optional human-readable label for debugging, tracing, or benchmarking.
    confidential:
        Whether the artifact should be treated as confidential by default.
    """

    value: T
    provenance: Provenance = field(default_factory=Provenance)
    label: str | None = None
    confidential: bool = False

    def __post_init__(self) -> None:
        if self.provenance is None:
            object.__setattr__(self, "provenance", Provenance.empty())

    def __repr__(self) -> str:
        return (
            "Artifact("
            f"value={self.value!r}, "
            f"provenance={self.provenance!r}, "
            f"label={self.label!r}, "
            f"confidential={self.confidential!r})"
        )

    def with_value(self, value: T) -> "Artifact[T]":
        """Return a copy with a new value but the same provenance."""
        return replace(self, value=value)

    def with_provenance(self, provenance: Provenance) -> "Artifact[T]":
        """Return a copy with updated provenance."""
        return replace(self, provenance=provenance)

    def map(self, *, value: T, operation: str) -> "Artifact[T]":
        """Derive an immutable artifact while recording the operation."""
        return replace(self, value=value, provenance=self.provenance.with_operation(operation))

    @classmethod
    def combine(
        cls,
        *artifacts: "Artifact[Any]",
        value: T,
        operation: str,
    ) -> "Artifact[T]":
        """Combine artifacts and retain all provenance and derivation data."""
        provenance = Provenance.empty()
        for artifact in artifacts:
            provenance = provenance.merge(artifact.provenance)
        return cls(value=value, provenance=provenance.with_operation(operation))

    def with_label(self, label: str | None) -> "Artifact[T]":
        """Return a copy with a new label."""
        return replace(self, label=label)

    def mark_confidential(self) -> "Artifact[T]":
        """Return a confidential copy of this artifact."""
        return replace(self, confidential=True)

    def mark_public(self) -> "Artifact[T]":
        """Return a non-confidential copy of this artifact."""
        return replace(self, confidential=False)

    @property
    def is_confidential(self) -> bool:
        """Convenience property for visibility checks."""
        return self.confidential

    @property
    def principals(self) -> frozenset[Principal]:
        """
        Compatibility accessor for the principals contributing to this artifact.
        """
        return self.provenance.principals


def wrap(
    value: T,
    *,
    label: str | None = None,
    confidential: bool = False,
) -> Artifact[T]:
    """Wrap a raw value in a provenance-bearing artifact with empty provenance."""
    return Artifact(value=value, label=label, confidential=confidential)


def unwrap(artifact: Artifact[T]) -> T:
    """Extract the payload from an artifact."""
    return artifact.value


def artifact_label(artifact: Artifact[Any]) -> str:
    """Return a usable display label for the artifact."""
    if artifact.label is not None:
        return artifact.label
    return type(artifact.value).__name__


__all__ = [
    "Artifact",
    "artifact_label",
    "unwrap",
    "wrap",
]
