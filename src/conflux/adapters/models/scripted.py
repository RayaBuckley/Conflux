"""Deterministic model adapter for tests, demos, and offline experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from conflux.domain import Artifact, ProposalBatch


@dataclass(slots=True)
class ScriptedModel:
    batches: tuple[ProposalBatch, ...]
    repeat_last: bool = False
    calls: int = 0
    input_fingerprints: list[tuple[str, ...]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.batches = tuple(self.batches)
        if not self.batches:
            raise ValueError("scripted model requires at least one proposal batch")

    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        self.input_fingerprints.append(tuple(item.fingerprint for item in inputs))
        if self.calls >= len(self.batches):
            if not self.repeat_last:
                raise RuntimeError("scripted_model_exhausted")
            batch = self.batches[-1]
        else:
            batch = self.batches[self.calls]
        self.calls += 1
        return batch


__all__ = ["ScriptedModel"]
