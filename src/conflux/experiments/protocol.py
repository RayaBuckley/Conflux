"""Strict version-two experiment protocols and resolved run metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, cast

import yaml
from jsonschema import Draft202012Validator, ValidationError
from yaml import YAMLError

from conflux.adapters.scenarios import load_schema
from conflux.domain import canonical_json, fingerprint
from conflux.ports import LocalModelSpec


def _frozen(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class ExperimentProtocol:
    """Immutable, schema-validated version-two experiment protocol."""

    id: str
    track: str
    suite: Mapping[str, object]
    source_commit: str
    inputs: Mapping[str, object]
    model: LocalModelSpec | None
    prompts: Mapping[str, object]
    seeds: tuple[int, ...]
    repetitions: int
    bounds: Mapping[str, object]
    environment: Mapping[str, object]
    output_directory: str
    rerun_command: tuple[str, ...]
    schema_version: str = "2"

    def __post_init__(self) -> None:
        """Freeze mutable fields and validate against the protocol schema."""
        for name in ("suite", "inputs", "prompts", "bounds", "environment"):
            object.__setattr__(self, name, _frozen(cast(Mapping[str, object], getattr(self, name))))
        object.__setattr__(self, "seeds", tuple(self.seeds))
        object.__setattr__(self, "rerun_command", tuple(self.rerun_command))
        _validate("experiment-protocol-v2.schema.json", self.to_dict(), "protocol")

    def to_dict(self) -> dict[str, object]:
        """Serialize this protocol to a JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "track": self.track,
            "suite": dict(self.suite),
            "source_commit": self.source_commit,
            "inputs": dict(self.inputs),
            "model": None if self.model is None else self.model.to_dict(),
            "prompts": dict(self.prompts),
            "seeds": list(self.seeds),
            "repetitions": self.repetitions,
            "bounds": dict(self.bounds),
            "environment": dict(self.environment),
            "output_directory": self.output_directory,
            "rerun_command": list(self.rerun_command),
        }

    @property
    def fingerprint(self) -> str:
        """Return a content-based fingerprint of this protocol."""
        return fingerprint(self.to_dict())

    def materialise(self, directory: Path) -> Path:
        """Write the protocol and rerun command into *directory* and return the path."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "protocol.json"
        path.write_text(canonical_json(self.to_dict()) + "\n", encoding="utf-8", newline="\n")
        (directory / "RERUN.txt").write_text(" ".join(self.rerun_command) + "\n", encoding="utf-8", newline="\n")
        return path


@dataclass(frozen=True, slots=True)
class RunFailure:
    """A categorized failure record for an experiment run."""

    category: str
    detail: str
    case_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize this run failure to a JSON-compatible dictionary."""
        return {"category": self.category, "detail": self.detail, "case_id": self.case_id}


@dataclass(frozen=True, slots=True)
class ResolvedRunManifest:
    """Immutable, schema-validated manifest summarizing a resolved experiment run."""

    run_id: str
    track: str
    protocol_fingerprint: str
    source_commit: str
    status: str
    complete: bool
    exclusions: tuple[str, ...]
    failures: tuple[RunFailure, ...]
    environment: Mapping[str, object]
    checksums: Mapping[str, object]
    schema_version: str = "2"

    def __post_init__(self) -> None:
        """Freeze fields and validate completeness and schema compliance."""
        object.__setattr__(self, "exclusions", tuple(self.exclusions))
        object.__setattr__(self, "failures", tuple(self.failures))
        object.__setattr__(self, "environment", _frozen(self.environment))
        object.__setattr__(self, "checksums", _frozen(self.checksums))
        _validate("experiment-run-manifest-v2.schema.json", self.to_dict(), "run_manifest")
        if self.complete != (self.status == "complete"):
            raise ValueError("run_manifest_completeness_mismatch")

    def to_dict(self) -> dict[str, object]:
        """Serialize this resolved run manifest to a JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "track": self.track,
            "protocol_fingerprint": self.protocol_fingerprint,
            "source_commit": self.source_commit,
            "status": self.status,
            "complete": self.complete,
            "exclusions": list(self.exclusions),
            "failures": [failure.to_dict() for failure in self.failures],
            "environment": dict(self.environment),
            "checksums": dict(self.checksums),
        }


def _validate(schema: str, payload: object, label: str) -> None:
    try:
        Draft202012Validator(load_schema(schema)).validate(payload)
    except ValidationError as error:
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise ValueError(f"{label}_schema_error:{location}:{error.message}") from error


def load_protocol(path: Path) -> ExperimentProtocol:
    """Load and validate an experiment protocol from a YAML or JSON file."""
    payload = _load_mapping(path, "protocol")
    _validate("experiment-protocol-v2.schema.json", payload, "protocol")
    model_payload = cast(dict[str, Any] | None, payload["model"])
    return ExperimentProtocol(
        id=str(payload["id"]),
        track=str(payload["track"]),
        suite=cast(dict[str, object], payload["suite"]),
        source_commit=str(payload["source_commit"]),
        inputs=cast(dict[str, object], payload["inputs"]),
        model=None if model_payload is None else LocalModelSpec(**model_payload),
        prompts=cast(dict[str, object], payload["prompts"]),
        seeds=tuple(int(seed) for seed in cast(list[int], payload["seeds"])),
        repetitions=int(payload["repetitions"]),
        bounds=cast(dict[str, object], payload["bounds"]),
        environment=cast(dict[str, object], payload["environment"]),
        output_directory=str(payload["output_directory"]),
        rerun_command=tuple(str(item) for item in cast(list[str], payload["rerun_command"])),
    )


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, YAMLError) as error:
        raise ValueError(f"{label}_load_failed:{type(error).__name__}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label}_root_must_be_mapping")
    return cast(dict[str, Any], payload)


__all__ = [
    "ExperimentProtocol",
    "LocalModelSpec",
    "ResolvedRunManifest",
    "RunFailure",
    "load_protocol",
]
