"""Provider-neutral immutable resource identities."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ResourceRef:
    provider: str
    resource_id: str
    resource_type: str
    attributes: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        if not self.provider or not self.resource_id or not self.resource_type:
            raise ValueError("ResourceRef identity fields must be non-empty")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "attributes": dict(self.attributes),
        }

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.provider, self.resource_type, self.resource_id)


__all__ = ["ResourceRef"]
