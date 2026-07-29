"""Immutable values paired with security provenance."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Generic, TypeVar

from .provenance import Provenance, provenance_union
from .serialization import fingerprint

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Artifact(Generic[T]):
    id: str
    value: T
    provenance: Provenance
    label: str | None = None
    confidential: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Artifact.id must be non-empty")

    def derive(self, *, artifact_id: str, value: T, activity: str) -> "Artifact[T]":
        return Artifact(
            id=artifact_id,
            value=value,
            provenance=self.provenance.with_activity(activity),
            label=self.label,
            confidential=self.confidential,
        )

    @classmethod
    def combine(
        cls,
        *artifacts: "Artifact[Any]",
        artifact_id: str,
        value: T,
        activity: str,
    ) -> "Artifact[T]":
        provenance = provenance_union(*(artifact.provenance for artifact in artifacts)).with_activity(activity)
        return cls(id=artifact_id, value=value, provenance=provenance)

    def with_label(self, label: str | None) -> "Artifact[T]":
        return replace(self, label=label)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "value": self.value,
            "provenance": self.provenance.to_dict(),
            "label": self.label,
            "confidential": self.confidential,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


__all__ = ["Artifact"]
