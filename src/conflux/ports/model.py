"""Port for model proposal generation."""

from __future__ import annotations

from typing import Protocol

from conflux.core import Artifact
from conflux.core.actions import Action


class ModelPort(Protocol):
    """Generate declarative actions from immutable input artifacts."""

    def propose(self, inputs: frozenset[Artifact[object]]) -> frozenset[Action[object]]:
        """Return proposals without performing side effects."""
        ...


__all__ = ["ModelPort"]
