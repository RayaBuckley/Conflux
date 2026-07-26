"""Provider-neutral immutable resource identity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResourceRef:
    """Stable reference to a protected resource, without provider state."""

    provider: str
    resource_id: str
    resource_type: str

    def __post_init__(self) -> None:
        if not all((self.provider, self.resource_id, self.resource_type)):
            raise ValueError("ResourceRef fields must be non-empty")


__all__ = ["ResourceRef"]
