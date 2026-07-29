"""Immutable, versioned experiment manifests."""

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


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    id: str
    suite: str
    suite_version: str
    source_commit: str
    defence: str
    bounds: Mapping[str, object]
    model: Mapping[str, object]
    provider: Mapping[str, object]
    policy: Mapping[str, object]
    seed: int
    machine: Mapping[str, object]
    output_directory: str
    rerun_command: tuple[str, ...]
    schema_version: str = "1"

    def __post_init__(self) -> None:
        for name in ("bounds", "model", "provider", "policy", "machine"):
            object.__setattr__(
                self,
                name,
                MappingProxyType(dict(cast(Mapping[str, object], getattr(self, name)))),
            )
        object.__setattr__(self, "rerun_command", tuple(self.rerun_command))
        Draft202012Validator(load_schema("experiment-manifest.schema.json")).validate(
            self.to_dict()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "suite": self.suite,
            "suite_version": self.suite_version,
            "source_commit": self.source_commit,
            "defence": self.defence,
            "bounds": dict(self.bounds),
            "model": dict(self.model),
            "provider": dict(self.provider),
            "policy": dict(self.policy),
            "seed": self.seed,
            "machine": dict(self.machine),
            "output_directory": self.output_directory,
            "rerun_command": list(self.rerun_command),
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())

    def materialise(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "manifest.json"
        path.write_text(
            canonical_json(self.to_dict()) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (directory / "RERUN.txt").write_text(
            " ".join(self.rerun_command) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path


def load_manifest(path: Path) -> ExperimentManifest:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, YAMLError) as error:
        raise ValueError(f"manifest_load_failed:{type(error).__name__}") from error
    if not isinstance(payload, dict):
        raise ValueError("manifest_root_must_be_mapping")
    try:
        Draft202012Validator(load_schema("experiment-manifest.schema.json")).validate(
            payload
        )
    except ValidationError as error:
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise ValueError(f"manifest_schema_error:{location}:{error.message}") from error
    value = cast(dict[str, Any], payload)
    return ExperimentManifest(
        id=str(value["id"]),
        suite=str(value["suite"]),
        suite_version=str(value["suite_version"]),
        source_commit=str(value["source_commit"]),
        defence=str(value["defence"]),
        bounds=cast(dict[str, object], value["bounds"]),
        model=cast(dict[str, object], value["model"]),
        provider=cast(dict[str, object], value["provider"]),
        policy=cast(dict[str, object], value["policy"]),
        seed=int(value["seed"]),
        machine=cast(dict[str, object], value["machine"]),
        output_directory=str(value["output_directory"]),
        rerun_command=tuple(str(item) for item in value["rerun_command"]),
    )


def manifest_from_json(path: Path) -> ExperimentManifest:
    """Load materialised JSON using the same strict YAML-compatible parser."""
    return load_manifest(path)


__all__ = ["ExperimentManifest", "load_manifest", "manifest_from_json"]
