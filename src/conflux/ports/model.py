"""Boundary for deterministic or real model proposal generation."""

from __future__ import annotations

from typing import Any, Protocol

from conflux.domain import Artifact, ProposalBatch


class ModelPort(Protocol):
    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        """Return a typed proposal batch without performing side effects."""
        ...


__all__ = ["ModelPort"]
