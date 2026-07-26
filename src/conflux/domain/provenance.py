"""Provider-independent provenance records built on the canonical core model."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.core.provenance import Provenance


@dataclass(frozen=True, slots=True)
class Derivation:
    """A typed, named operation that produced a derived artifact."""

    operation: str
    inputs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.operation:
            raise ValueError("Derivation.operation must be non-empty")


__all__ = ["Derivation", "Provenance"]
