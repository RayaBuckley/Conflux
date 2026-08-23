"""Boundary for deterministic or real model proposal generation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Protocol

from conflux.domain import Artifact, ProposalBatch


class ModelPort(Protocol):
    """Boundary for deterministic or real model proposal generation."""

    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        """Return a typed proposal batch without performing side effects."""
        ...


@dataclass(frozen=True, slots=True)
class LocalModelSpec:
    """Immutable identity, sampling, and placement of a self-hosted model."""

    backend: str
    model_id: str
    revision: str
    weight_manifest_sha256: str
    tokenizer_id: str
    tokenizer_revision: str
    prompt_template_version: str
    seed: int
    temperature: float
    top_p: float
    max_output_tokens: int
    context_limit: int
    device: str
    dtype: str
    runtime_version: str
    endpoint: str | None = None
    allow_private_remote: bool = False

    def __post_init__(self) -> None:
        if self.backend not in {"openai_compatible", "transformers"}:
            raise ValueError("local_model_backend_unsupported")
        required = (
            self.model_id,
            self.revision,
            self.tokenizer_id,
            self.tokenizer_revision,
            self.prompt_template_version,
            self.device,
            self.dtype,
            self.runtime_version,
        )
        if not all(required) or len(self.weight_manifest_sha256) != 64:
            raise ValueError("local_model_identity_incomplete")
        if self.seed < 0 or self.temperature < 0 or not 0 < self.top_p <= 1:
            raise ValueError("local_model_sampling_invalid")
        if self.max_output_tokens < 1 or self.context_limit < 1:
            raise ValueError("local_model_bounds_invalid")
        if self.backend == "openai_compatible" and not self.endpoint:
            raise ValueError("local_model_endpoint_required")
        if self.backend == "transformers" and self.endpoint is not None:
            raise ValueError("transformers_endpoint_forbidden")

    def to_dict(self) -> dict[str, object]:
        """Serialise the model specification to a plain dictionary."""
        return {
            "backend": self.backend,
            "model_id": self.model_id,
            "revision": self.revision,
            "weight_manifest_sha256": self.weight_manifest_sha256,
            "tokenizer_id": self.tokenizer_id,
            "tokenizer_revision": self.tokenizer_revision,
            "prompt_template_version": self.prompt_template_version,
            "seed": self.seed,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_output_tokens": self.max_output_tokens,
            "context_limit": self.context_limit,
            "device": self.device,
            "dtype": self.dtype,
            "runtime_version": self.runtime_version,
            "endpoint": self.endpoint,
            "allow_private_remote": self.allow_private_remote,
        }


@dataclass(frozen=True, slots=True)
class LocalModelRequest:
    """One side-effect-free structured generation request."""

    request_id: str
    system_prompt: str
    user_prompt: str
    schema_name: str
    schema: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.request_id or not self.schema_name:
            raise ValueError("local_model_request_identity_required")
        object.__setattr__(self, "schema", MappingProxyType(dict(self.schema)))


@dataclass(frozen=True, slots=True)
class LocalModelResponse:
    """Immutable response from a structured self-hosted model call."""

    request_id: str
    model_id: str
    payload: Mapping[str, object]
    prompt_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    raw_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True, slots=True)
class LocalModelPreflight:
    """Result of checking local model availability and identity."""

    backend: str
    model_id: str
    available: bool
    network_scope: str
    reason: str | None
    dependency_available: bool | None = None
    artifact_available: bool | None = None
    identity_verified: bool | None = None
    runtime_available: bool | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "warnings", tuple(self.warnings))


class LocalModelPort(Protocol):
    """Structured self-hosted inference; it never performs tool effects."""

    def preflight(self) -> LocalModelPreflight:
        """Check model availability, identity, and network scope."""
        ...

    def generate(self, request: LocalModelRequest) -> LocalModelResponse:
        """Generate a structured response without side effects."""
        ...


__all__ = [
    "LocalModelPort",
    "LocalModelPreflight",
    "LocalModelRequest",
    "LocalModelResponse",
    "LocalModelSpec",
    "ModelPort",
]
