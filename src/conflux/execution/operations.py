"""
Execution operations.

This module defines the basic abstraction for transforming artifacts while
preserving provenance. It is intentionally small: the project does not use a
planner/executor split, so execution units should be lightweight and composable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from conflux.core.artifacts import Artifact
from conflux.core.provenance import Provenance

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True, slots=True)
class Operation(ABC, Generic[T, U]):
    """
    Base class for an execution step.

    Subclasses should implement `run`, which accepts an input artifact and
    returns a new derived artifact.

    Operations are intentionally narrow:
    - they transform artifact values,
    - they preserve or extend provenance,
    - they do not perform authorisation,
    - they do not decide visibility,
    - they do not manage consent.
    """

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Operation.name must be non-empty")

    @abstractmethod
    def run(self, artifact: Artifact[T]) -> Artifact[U]:
        """
        Execute the operation on an input artifact.
        """
        raise NotImplementedError

    def __call__(self, artifact: Artifact[T]) -> Artifact[U]:
        """
        Convenience alias for `run`.
        """
        return self.run(artifact)

    def derive(
        self,
        artifact: Artifact[T],
        value: U,
        *,
        provenance: Provenance | None = None,
        label: str | None = None,
        confidential: bool | None = None,
    ) -> Artifact[U]:
        """
        Helper for subclasses that want to preserve the input artifact's
        provenance by default while producing a new value.

        If provenance is omitted, the input artifact provenance is reused.
        If confidential is omitted, the input artifact confidentiality is reused.
        """
        return Artifact(
            value=value,
            provenance=artifact.provenance if provenance is None else provenance,
            label=artifact.label if label is None else label,
            confidential=artifact.confidential if confidential is None else confidential,
        )


@dataclass(frozen=True, slots=True)
class IdentityOperation(Operation[T, T]):
    """
    An operation that returns its input unchanged.

    Useful in exhaustive search, testing, and adapter scaffolding.
    """

    def run(self, artifact: Artifact[T]) -> Artifact[T]:
        return artifact


@dataclass(frozen=True, slots=True)
class RenameOperation(Operation[T, T]):
    """
    An operation that changes the artifact label while preserving value and
    provenance.
    """

    new_label: str | None = None

    def run(self, artifact: Artifact[T]) -> Artifact[T]:
        return self.derive(
            artifact,
            artifact.value,
            label=self.new_label,
        )


@dataclass(frozen=True, slots=True)
class RedactOperation(Operation[T, T]):
    """
    An operation that marks an artifact as confidential.

    This is useful when a derived value should not be rendered verbatim in the
    transcript or exposed to lower-visibility channels.
    """

    def run(self, artifact: Artifact[T]) -> Artifact[T]:
        return self.derive(
            artifact,
            artifact.value,
            confidential=True,
        )


@dataclass(frozen=True, slots=True)
class RevealOperation(Operation[T, T]):
    """
    An operation that marks an artifact as non-confidential.

    This does not bypass policy; it only adjusts the artifact metadata.
    """

    def run(self, artifact: Artifact[T]) -> Artifact[T]:
        return self.derive(
            artifact,
            artifact.value,
            confidential=False,
        )


@dataclass(frozen=True, slots=True)
class MapOperation(Operation[T, U]):
    """
    An operation that applies a pure value transform while preserving
    provenance by default.

    This is useful for lightweight derived artifacts such as summaries,
    projections, normalisations, or formatting changes.
    """

    transform: Callable[[T], U]

    def run(self, artifact: Artifact[T]) -> Artifact[U]:
        return self.derive(
            artifact,
            self.transform(artifact.value),
        )


@dataclass(frozen=True, slots=True)
class ProvenanceUnionOperation(Operation[T, T]):
    """
    An operation that merges the artifact's provenance with an additional
    provenance object.

    This is useful when an execution step introduces a second authoritative
    source or a derived trace edge.
    """

    extra_provenance: Provenance = Provenance.empty()

    def run(self, artifact: Artifact[T]) -> Artifact[T]:
        return self.derive(
            artifact,
            artifact.value,
            provenance=artifact.provenance.merge(self.extra_provenance),
        )


__all__ = [
    "IdentityOperation",
    "MapOperation",
    "Operation",
    "ProvenanceUnionOperation",
    "RedactOperation",
    "RenameOperation",
    "RevealOperation",
]
