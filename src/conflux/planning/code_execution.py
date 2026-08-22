"""Typed code-execution request and capability envelope."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from conflux.domain import Artifact, Permission, Provenance, fingerprint, provenance_union


@dataclass(frozen=True, slots=True)
class CapabilityEnvelope:
    """Immutable sandbox capability envelope for code execution."""

    runtime_image: str
    workspace: str
    read_paths: tuple[str, ...] = ()
    write_paths: tuple[str, ...] = ("outputs",)
    network_allowlist: tuple[str, ...] = ()
    credential_capabilities: tuple[str, ...] = ()
    timeout_seconds: float = 30.0
    memory_bytes: int = 268_435_456
    process_limit: int = 32
    output_bytes: int = 1_048_576
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if "@sha256:" not in self.runtime_image:
            raise ValueError("runtime image must be pinned by sha256 digest")
        if not self.workspace:
            raise ValueError("code workspace must be non-empty")
        object.__setattr__(self, "read_paths", tuple(self.read_paths))
        object.__setattr__(self, "write_paths", tuple(self.write_paths))
        object.__setattr__(self, "network_allowlist", tuple(self.network_allowlist))
        object.__setattr__(
            self,
            "credential_capabilities",
            tuple(self.credential_capabilities),
        )
        if (
            min(
                self.timeout_seconds,
                self.memory_bytes,
                self.process_limit,
                self.output_bytes,
            )
            <= 0
        ):
            raise ValueError("sandbox resource limits must be positive")
        for path in (self.workspace, *self.read_paths, *self.write_paths):
            _validate_relative_path(path)

    def to_dict(self) -> dict[str, object]:
        """Serialise the capability envelope to a canonical dictionary."""
        return {
            "schema_version": self.schema_version,
            "runtime_image": self.runtime_image,
            "workspace": self.workspace,
            "read_paths": list(self.read_paths),
            "write_paths": list(self.write_paths),
            "network_allowlist": list(self.network_allowlist),
            "credential_capabilities": list(self.credential_capabilities),
            "timeout_seconds": self.timeout_seconds,
            "memory_bytes": self.memory_bytes,
            "process_limit": self.process_limit,
            "output_bytes": self.output_bytes,
        }

    @property
    def fingerprint(self) -> str:
        """Return the content fingerprint of the capability envelope."""
        return fingerprint(self.to_dict())

    @classmethod
    def from_dict(cls, value: object) -> "CapabilityEnvelope":
        """Parse a dictionary into a validated CapabilityEnvelope."""
        if not isinstance(value, Mapping):
            raise ValueError("capability envelope must be an object")
        payload = MappingProxyType(dict(value))
        expected = {
            "schema_version",
            "runtime_image",
            "workspace",
            "read_paths",
            "write_paths",
            "network_allowlist",
            "credential_capabilities",
            "timeout_seconds",
            "memory_bytes",
            "process_limit",
            "output_bytes",
        }
        if set(payload) != expected or payload.get("schema_version") != "1":
            raise ValueError("unsupported or malformed capability envelope")
        return cls(
            _string(payload["runtime_image"], "runtime_image"),
            _string(payload["workspace"], "workspace"),
            _strings(payload["read_paths"], "read_paths"),
            _strings(payload["write_paths"], "write_paths"),
            _strings(payload["network_allowlist"], "network_allowlist"),
            _strings(
                payload["credential_capabilities"],
                "credential_capabilities",
            ),
            _number(payload["timeout_seconds"], "timeout_seconds"),
            _integer(payload["memory_bytes"], "memory_bytes"),
            _integer(payload["process_limit"], "process_limit"),
            _integer(payload["output_bytes"], "output_bytes"),
        )


@dataclass(frozen=True, slots=True)
class CodeExecutionRequest:
    """A typed request to execute code in a sandboxed capability envelope."""

    id: str
    source: Artifact[str]
    inputs: tuple[Artifact[Any], ...]
    output_contract: Mapping[str, object]
    envelope: CapabilityEnvelope
    runtime_provenance: Provenance

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("code execution request id must be non-empty")
        if not isinstance(self.source.value, str):
            raise TypeError("generated code source must be text")
        object.__setattr__(self, "inputs", tuple(self.inputs))
        object.__setattr__(
            self,
            "output_contract",
            MappingProxyType(dict(self.output_contract)),
        )

    @property
    def output_provenance(self) -> Provenance:
        """Return the combined provenance of source, inputs, and runtime."""
        return provenance_union(
            self.source.provenance,
            *(item.provenance for item in self.inputs),
            self.runtime_provenance,
        ).with_activity(f"execute_code:{self.id}")

    def to_dict(self) -> dict[str, object]:
        """Serialise the code execution request to a canonical dictionary."""
        return {
            "id": self.id,
            "source_id": self.source.id,
            "source_hash": fingerprint(self.source.value),
            "input_ids": [item.id for item in self.inputs],
            "input_hashes": [item.fingerprint for item in self.inputs],
            "output_contract": dict(self.output_contract),
            "envelope": self.envelope.to_dict(),
            "runtime_provenance": self.runtime_provenance.to_dict(),
        }

    @property
    def fingerprint(self) -> str:
        """Return the content fingerprint of the code execution request."""
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class CodeOutput:
    """A single output artifact produced by code execution."""

    path: str
    sha256: str
    size: int
    artifact: Artifact[bytes]

    def to_dict(self) -> dict[str, object]:
        """Serialise the code output to a canonical dictionary."""
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size": self.size,
            "artifact_id": self.artifact.id,
            "artifact_fingerprint": self.artifact.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class CodeExecutionResult:
    """Outcome of a code execution including outputs and observed I/O."""

    success: bool
    request_fingerprint: str
    runtime_image: str
    envelope_fingerprint: str
    command_hash: str
    exit_code: int | None
    stdout_sha256: str
    stderr_sha256: str
    outputs: tuple[CodeOutput, ...] = ()
    observed_reads: tuple[str, ...] = ()
    observed_writes: tuple[str, ...] = ()
    failure_category: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialise the code execution result to a canonical dictionary."""
        return {
            "success": self.success,
            "request_fingerprint": self.request_fingerprint,
            "runtime_image": self.runtime_image,
            "envelope_fingerprint": self.envelope_fingerprint,
            "command_hash": self.command_hash,
            "exit_code": self.exit_code,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "outputs": [item.to_dict() for item in self.outputs],
            "observed_reads": list(self.observed_reads),
            "observed_writes": list(self.observed_writes),
            "failure_category": self.failure_category,
        }


def code_operation_permission() -> Permission:
    """Return the permission required to execute code."""
    return Permission("execute_code")


def _validate_relative_path(value: str) -> None:
    from pathlib import PurePosixPath

    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unconfined capability path: {value}")


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{label} must be an array of non-empty strings")
    return tuple(value)


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    return value


def _number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    return float(value)


__all__ = [
    "CapabilityEnvelope",
    "CodeExecutionRequest",
    "CodeExecutionResult",
    "CodeOutput",
    "code_operation_permission",
]
