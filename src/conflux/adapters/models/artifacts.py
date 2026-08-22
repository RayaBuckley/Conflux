"""Deterministic resolution of operator-owned local model snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, ValidationError

from conflux.adapters.scenarios import load_schema
from conflux.domain import canonical_json, fingerprint
from conflux.ports import LocalModelSpec


@dataclass(frozen=True, slots=True)
class LocalArtifactFile:
    """A single file entry within a local model artifact manifest."""

    path: str
    size: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        """Serialize this file entry to a canonical dictionary."""
        return {"path": self.path, "size": self.size, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class LocalArtifactManifest:
    """Manifest of all files comprising a local model snapshot."""

    model_id: str
    revision: str
    tokenizer_id: str
    tokenizer_revision: str
    files: tuple[LocalArtifactFile, ...]
    total_size: int
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "files", tuple(self.files))
        if not self.model_id or not self.revision or not self.files:
            raise ValueError("local_artifact_identity_incomplete")
        if tuple(sorted(item.path for item in self.files)) != tuple(item.path for item in self.files):
            raise ValueError("local_artifact_files_not_canonical")
        if len({item.path for item in self.files}) != len(self.files):
            raise ValueError("local_artifact_file_duplicate")
        if self.total_size != sum(item.size for item in self.files):
            raise ValueError("local_artifact_total_mismatch")
        Draft202012Validator(load_schema("local-artifact-manifest.schema.json")).validate(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        """Serialize the manifest to a canonical dictionary."""
        return {
            "schema_version": self.schema_version,
            "model_id": self.model_id,
            "revision": self.revision,
            "tokenizer_id": self.tokenizer_id,
            "tokenizer_revision": self.tokenizer_revision,
            "files": [item.to_dict() for item in self.files],
            "total_size": self.total_size,
        }

    @property
    def fingerprint(self) -> str:
        """Return the canonical fingerprint of this manifest."""
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class ResolvedLocalModel:
    """A locally resolved transformers model with verified artifact manifest."""

    spec: LocalModelSpec
    snapshot_path: Path
    manifest: LocalArtifactManifest
    warnings: tuple[str, ...] = ()
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_path", self.snapshot_path.resolve())
        object.__setattr__(self, "warnings", tuple(self.warnings))
        if self.spec.backend != "transformers":
            raise ValueError("resolved_transformers_spec_required")
        if self.spec.weight_manifest_sha256 != self.manifest.fingerprint:
            raise ValueError("resolved_manifest_fingerprint_mismatch")
        if (self.spec.model_id, self.spec.revision) != (
            self.manifest.model_id,
            self.manifest.revision,
        ):
            raise ValueError("resolved_model_identity_mismatch")

    def to_dict(self) -> dict[str, object]:
        """Serialize the resolved model to a canonical dictionary."""
        return {
            "schema_version": self.schema_version,
            "spec": self.spec.to_dict(),
            "snapshot_path": str(self.snapshot_path),
            "manifest": self.manifest.to_dict(),
            "warnings": list(self.warnings),
        }


def resolve_transformers_snapshot(
    snapshot_path: Path,
    *,
    model_id: str,
    revision: str,
    tokenizer_id: str | None = None,
    tokenizer_revision: str | None = None,
) -> tuple[LocalArtifactManifest, tuple[str, ...]]:
    """Scan a local snapshot directory and build a verified artifact manifest."""
    snapshot = snapshot_path.resolve(strict=True)
    if not snapshot.is_dir():
        raise ValueError("local_snapshot_not_directory")
    if snapshot.name != revision:
        raise ValueError("local_snapshot_revision_mismatch")
    model_root = snapshot.parent.parent.resolve(strict=True)
    files: list[LocalArtifactFile] = []
    for entry in sorted(snapshot.rglob("*"), key=lambda item: item.relative_to(snapshot).as_posix()):
        if entry.is_dir():
            continue
        try:
            resolved = entry.resolve(strict=True)
        except OSError as error:
            raise ValueError(f"local_artifact_dangling:{entry.name}") from error
        if not resolved.is_relative_to(model_root) or not resolved.is_file():
            raise ValueError(f"local_artifact_cache_escape:{entry.name}")
        relative = entry.relative_to(snapshot).as_posix()
        files.append(LocalArtifactFile(relative, resolved.stat().st_size, _sha256(resolved)))
    names = {item.path for item in files}
    if "config.json" not in names:
        raise ValueError("local_artifact_config_missing")
    if not ({"tokenizer.json", "tokenizer_config.json"} & names):
        raise ValueError("local_artifact_tokenizer_missing")
    if not any(name.endswith((".safetensors", ".bin")) for name in names):
        raise ValueError("local_artifact_weights_missing")
    manifest = LocalArtifactManifest(
        model_id,
        revision,
        tokenizer_id or model_id,
        tokenizer_revision or revision,
        tuple(files),
        sum(item.size for item in files),
    )
    cache_root = model_root.parent
    incomplete = tuple(sorted(cache_root.rglob("*.incomplete")))
    warnings = (f"unreferenced_incomplete_cache_entries:{len(incomplete)}",) if incomplete else ()
    return manifest, warnings


def verify_transformers_snapshot(
    snapshot_path: Path,
    manifest: LocalArtifactManifest,
) -> tuple[str, ...]:
    """Re-derive a snapshot manifest and verify it matches the given manifest."""
    regenerated, warnings = resolve_transformers_snapshot(
        snapshot_path,
        model_id=manifest.model_id,
        revision=manifest.revision,
        tokenizer_id=manifest.tokenizer_id,
        tokenizer_revision=manifest.tokenizer_revision,
    )
    if regenerated.fingerprint != manifest.fingerprint:
        raise ValueError("local_artifact_manifest_changed")
    return warnings


def write_resolved_local_model(value: ResolvedLocalModel, path: Path) -> None:
    """Write a resolved local model record to ``path`` as canonical JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value.to_dict()) + "\n", encoding="utf-8", newline="\n")


def load_resolved_local_model(path: Path) -> ResolvedLocalModel:
    """Load and verify a resolved local model record from ``path``."""
    try:
        payload = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
        if set(payload) != {"schema_version", "spec", "snapshot_path", "manifest", "warnings"}:
            raise ValueError("resolved_local_model_fields_invalid")
        manifest = _manifest(cast(dict[str, object], payload["manifest"]))
        spec = _spec(cast(dict[str, object], payload["spec"]))
        value = ResolvedLocalModel(
            spec,
            Path(cast(str, payload["snapshot_path"])),
            manifest,
            tuple(cast(list[str], payload["warnings"])),
            cast(str, payload["schema_version"]),
        )
        verify_transformers_snapshot(value.snapshot_path, value.manifest)
        return value
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValidationError) as error:
        raise ValueError(f"resolved_local_model_invalid:{type(error).__name__}") from error


def _manifest(payload: dict[str, object]) -> LocalArtifactManifest:
    return LocalArtifactManifest(
        cast(str, payload["model_id"]),
        cast(str, payload["revision"]),
        cast(str, payload["tokenizer_id"]),
        cast(str, payload["tokenizer_revision"]),
        tuple(
            LocalArtifactFile(
                cast(str, item["path"]),
                cast(int, item["size"]),
                cast(str, item["sha256"]),
            )
            for item in cast(list[dict[str, object]], payload["files"])
        ),
        cast(int, payload["total_size"]),
        cast(str, payload["schema_version"]),
    )


def _spec(payload: dict[str, object]) -> LocalModelSpec:
    return LocalModelSpec(
        backend=cast(str, payload["backend"]),
        model_id=cast(str, payload["model_id"]),
        revision=cast(str, payload["revision"]),
        weight_manifest_sha256=cast(str, payload["weight_manifest_sha256"]),
        tokenizer_id=cast(str, payload["tokenizer_id"]),
        tokenizer_revision=cast(str, payload["tokenizer_revision"]),
        prompt_template_version=cast(str, payload["prompt_template_version"]),
        seed=cast(int, payload["seed"]),
        temperature=cast(float, payload["temperature"]),
        top_p=cast(float, payload["top_p"]),
        max_output_tokens=cast(int, payload["max_output_tokens"]),
        context_limit=cast(int, payload["context_limit"]),
        device=cast(str, payload["device"]),
        dtype=cast(str, payload["dtype"]),
        runtime_version=cast(str, payload["runtime_version"]),
        endpoint=cast(str | None, payload["endpoint"]),
        allow_private_remote=cast(bool, payload["allow_private_remote"]),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "LocalArtifactFile",
    "LocalArtifactManifest",
    "ResolvedLocalModel",
    "load_resolved_local_model",
    "resolve_transformers_snapshot",
    "verify_transformers_snapshot",
    "write_resolved_local_model",
]
