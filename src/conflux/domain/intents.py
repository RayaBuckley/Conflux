"""Declarative intent values; execution is owned by application services."""

from __future__ import annotations

from dataclasses import dataclass, field

from .identity import PrincipalContext
from .resources import ResourceRef


@dataclass(frozen=True, slots=True)
class Intent:
    """A provider-neutral request to perform an operation on a resource."""

    operation: str
    resource: ResourceRef | None = None
    context: PrincipalContext = field(default_factory=PrincipalContext)

    def __post_init__(self) -> None:
        if not self.operation:
            raise ValueError("Intent.operation must be non-empty")


__all__ = ["Intent"]
