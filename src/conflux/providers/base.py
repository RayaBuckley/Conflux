"""
Provider adapter base interfaces.

Provider adapters materialise real systems into the internal ITES/SLED model.

The goal is to keep provider-specific complexity out of the core semantics:
- core models principals, resources, actions, provenance, sessions
- providers translate those abstractions to and from real environments
- evaluators and mediators operate only on the internal model
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, FrozenSet, Iterable, Mapping, Protocol, runtime_checkable

from conflux.compatibility.environment import Data, Environment, snapshot_from_legacy
from conflux.core import Principal, Resource
from conflux.core.actions import Proposal
from conflux.domain.environment import EnvironmentSnapshot


@dataclass(frozen=True, slots=True)
class ProviderCapability:
    """
    Describes a provider's supported surface.

    This is mainly useful for:
    - benchmark selection,
    - adapter discovery,
    - reporting,
    - and feature gating.
    """

    provider_id: str
    provider_type: str
    supported_resource_types: FrozenSet[str] = field(default_factory=frozenset)
    supported_operations: FrozenSet[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "supported_resource_types", frozenset(self.supported_resource_types))
        object.__setattr__(self, "supported_operations", frozenset(self.supported_operations))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def supports_operation(self, operation: str) -> bool:
        """Return True if the provider supports the named operation."""
        return operation in self.supported_operations

    def supports_resource_type(self, resource_type: str) -> bool:
        """Return True if the provider supports the named resource type."""
        return resource_type in self.supported_resource_types


@dataclass(frozen=True, slots=True)
class ProviderActionResult:
    """
    Result of attempting to execute a provider action.

    The provider adapter is responsible only for the external system
    interaction and conversion of the result into an internal representation.
    """

    ok: bool
    action: Proposal | None = None
    output: Any = None
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def succeeded(self) -> bool:
        return self.ok

    @property
    def failed(self) -> bool:
        return not self.ok


@dataclass(frozen=True, slots=True)
class ProviderMaterialisation:
    """
    The internal view produced by a provider adapter.

    This is the bridge between real systems and the exhaustive evaluator.
    """

    provider_id: str
    environment: Environment
    principal_map: Mapping[str, Principal] = field(default_factory=dict)
    resource_map: Mapping[str, Resource] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "principal_map", dict(self.principal_map))
        object.__setattr__(self, "resource_map", dict(self.resource_map))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def principal_for(self, external_id: str) -> Principal | None:
        """Return the internal principal corresponding to an external identifier."""
        return self.principal_map.get(external_id)

    def resource_for(self, external_id: str) -> Resource | None:
        """Return the internal resource corresponding to an external identifier."""
        return self.resource_map.get(external_id)

    @property
    def snapshot(self) -> EnvironmentSnapshot:
        """Return this materialisation in the provider-neutral contract."""
        return snapshot_from_legacy(self.environment)


@runtime_checkable
class ProviderAdapter(Protocol):
    """
    Minimal interface for provider adapters.

    Adapters should be deterministic for a fixed provider state where possible.
    """

    capability: ProviderCapability

    def materialise(self) -> ProviderMaterialisation:
        """
        Convert the current provider state into the internal SLED environment.
        """
        ...

    def snapshot(self) -> EnvironmentSnapshot:
        """Return the provider-neutral environment contract."""
        ...

    def resolve_principal(self, external_id: str) -> Principal | None:
        """
        Resolve an external principal identifier into the internal model.
        """
        ...

    def resolve_resource(self, external_id: str) -> Resource | None:
        """
        Resolve an external resource identifier into the internal model.
        """
        ...

    def list_principals(self) -> Iterable[Principal]:
        """
        Return the principals visible to the adapter.
        """
        ...

    def list_resources(self) -> Iterable[Resource]:
        """
        Return the resources visible to the adapter.
        """
        ...

    def describe_environment(self) -> Environment:
        """
        Return a snapshot of the current environment without executing anything.
        """
        ...

    def execute(self, proposal: Proposal) -> ProviderActionResult:
        """
        Execute a proposal against the external provider.
        """
        ...


class BaseProviderAdapter(ABC):
    """
    Base class for concrete provider adapters.

    Implementations should:
    - expose stable materialisation into the internal model,
    - translate provider-specific policy into the core model,
    - keep provider execution isolated from the defence logic.
    """

    capability: ProviderCapability

    def snapshot(self) -> EnvironmentSnapshot:
        """Translate the legacy environment view to the canonical snapshot."""
        return snapshot_from_legacy(self.describe_environment())

    @abstractmethod
    def materialise(self) -> ProviderMaterialisation:
        """Convert the current provider state into the internal SLED environment."""
        raise NotImplementedError

    @abstractmethod
    def resolve_principal(self, external_id: str) -> Principal | None:
        """Resolve an external principal identifier into the internal model."""
        raise NotImplementedError

    @abstractmethod
    def resolve_resource(self, external_id: str) -> Resource | None:
        """Resolve an external resource identifier into the internal model."""
        raise NotImplementedError

    @abstractmethod
    def list_principals(self) -> Iterable[Principal]:
        """Return the principals visible to the adapter."""
        raise NotImplementedError

    @abstractmethod
    def list_resources(self) -> Iterable[Resource]:
        """Return the resources visible to the adapter."""
        raise NotImplementedError

    @abstractmethod
    def describe_environment(self) -> Environment:
        """Return a snapshot of the current environment without executing anything."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, proposal: Proposal) -> ProviderActionResult:
        """Execute a proposal against the external provider."""
        raise NotImplementedError


def build_environment(
    *,
    provider_id: str,
    data: Iterable[Data],
    metadata: Mapping[str, Any] | None = None,
) -> Environment:
    """
    Convenience helper for adapters that want to build an Environment directly.
    """
    return Environment(
        data=frozenset(data),
        name=provider_id,
        metadata={} if metadata is None else dict(metadata),
    )


def build_materialisation(
    *,
    provider_id: str,
    data: Iterable[Data],
    principal_map: Mapping[str, Principal] | None = None,
    resource_map: Mapping[str, Resource] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ProviderMaterialisation:
    """
    Convenience helper for returning a complete provider materialisation.
    """
    return ProviderMaterialisation(
        provider_id=provider_id,
        environment=build_environment(provider_id=provider_id, data=data, metadata=metadata),
        principal_map={} if principal_map is None else dict(principal_map),
        resource_map={} if resource_map is None else dict(resource_map),
        metadata={} if metadata is None else dict(metadata),
    )


__all__ = [
    "BaseProviderAdapter",
    "ProviderActionResult",
    "ProviderAdapter",
    "ProviderCapability",
    "ProviderMaterialisation",
    "build_environment",
    "build_materialisation",
]
