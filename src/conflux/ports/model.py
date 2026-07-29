"""Boundary for deterministic or real model proposal generation."""

from __future__ import annotations

from typing import Any, Protocol

from conflux.domain import Action, Artifact


class ModelPort(Protocol):
    def propose(self, inputs: tuple[Artifact[Any], ...]) -> tuple[Action, ...]:
        """Return declarative alternatives without performing side effects."""
        ...


__all__ = ["ModelPort"]
