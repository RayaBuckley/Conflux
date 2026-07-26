"""Port for provider resource resolution and execution."""

from __future__ import annotations

from typing import Protocol

from conflux.core.actions import Action
from conflux.core.resources import Resource


class ResourcePort(Protocol):
    """Translate stable resources to provider operations."""

    def resolve(self, resource_id: str) -> Resource | None:
        """Resolve a stable provider resource identifier."""
        ...

    def execute(self, action: Action[object]) -> object:
        """Execute an already-authorised action."""
        ...


__all__ = ["ResourcePort"]
