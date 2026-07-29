"""Pure provenance-preserving transformations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from conflux.domain import Artifact

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass(frozen=True, slots=True)
class Operation(Generic[InputT, OutputT]):
    name: str
    transform: Callable[[InputT], OutputT]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Operation.name must be non-empty")

    def run(self, artifact: Artifact[InputT], *, output_id: str) -> Artifact[OutputT]:
        return Artifact(
            id=output_id,
            value=self.transform(artifact.value),
            provenance=artifact.provenance.with_activity(self.name),
            confidential=artifact.confidential,
        )


__all__ = ["Operation"]
