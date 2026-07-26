"""
Protected resources.

A Resource represents an object that may be acted upon by the agent.
Unlike Artifacts, Resources are not pieces of information flowing through
the LLM—they are the targets of primitive actions.

Provider adapters (AWS, Google Cloud, Microsoft Entra, local filesystem,
etc.) materialise concrete Resources from real systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from .principals import Principal


@dataclass(frozen=True, slots=True)
class Resource:
    """
    Provider-backed protected object.

    Resources stay deliberately lightweight. Provider-specific adapters should
    carry the detailed policy semantics; this model only preserves the stable
    identifiers needed by the core defence and the exhaustive evaluator.
    """

    id: str
    provider: str
    resource_type: str
    name: str
    attributes: Mapping[str, Any] = field(default_factory=dict)
    owner: Principal | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Resource.id must be non-empty")
        if not self.provider:
            raise ValueError("Resource.provider must be non-empty")
        if not self.resource_type:
            raise ValueError("Resource.resource_type must be non-empty")
        if self.owner is not None and not isinstance(self.owner, Principal):
            raise TypeError("Resource.owner must be a Principal or None")

    def __hash__(self) -> int:
        """Hash stable resource identity, excluding mutable provider metadata."""
        return hash((self.id, self.provider, self.resource_type, self.name, self.owner))

    def with_attributes(self, **updates: Any) -> "Resource":
        """
        Return a copy with updated attributes.
        """
        merged = dict(self.attributes)
        merged.update(updates)
        return replace(self, attributes=merged)

    def with_name(self, name: str) -> "Resource":
        """
        Return a copy with a new display name.
        """
        return replace(self, name=name)

    def with_provider(self, provider: str) -> "Resource":
        """
        Return a copy with a new provider identifier.
        """
        return replace(self, provider=provider)

    def with_resource_type(self, resource_type: str) -> "Resource":
        """
        Return a copy with a new provider-specific type label.
        """
        return replace(self, resource_type=resource_type)

    @property
    def key(self) -> tuple[str, str]:
        """
        Stable equivalence key used by representative-environment reduction.

        Individual providers may refine this further, but provider + resource
        type is the right default grouping for most benchmark compression.
        """
        return (self.provider, self.resource_type)

    @property
    def label(self) -> str:
        """
        Human-readable label for debugging and reporting.
        """
        return self.name

    def __repr__(self) -> str:
        return (
            "Resource("
            f"id={self.id!r}, "
            f"provider={self.provider!r}, "
            f"resource_type={self.resource_type!r}, "
            f"name={self.name!r}, "
            f"attributes={dict(self.attributes)!r})"
        )


def resource_key(resource: Resource) -> tuple[str, str]:
    """
    Compatibility helper for representative grouping.
    """
    return resource.key


def merge_attributes(*mappings: Mapping[str, Any]) -> dict[str, Any]:
    """
    Merge resource attribute dictionaries left-to-right.
    """
    merged: dict[str, Any] = {}
    for mapping in mappings:
        merged.update(mapping)
    return merged
