"""
Filesystem provider adapter.

This adapter materialises a filesystem subtree into the internal SLED model.
It is intentionally conservative: the adapter can describe the environment,
map files into resources, and execute a small set of filesystem operations.

The goal is not to model every POSIX detail. The goal is to provide a realistic
provider-backed attack surface for the exhaustive evaluator and future
benchmarking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from conflux.core import Principal, Resource
from conflux.core.actions import PrimitiveAction, Proposal
from conflux.sled.environment import Data, Environment

from .base import (
    BaseProviderAdapter,
    ProviderActionResult,
    ProviderCapability,
    ProviderMaterialisation,
    build_materialisation,
)


@dataclass(frozen=True, slots=True)
class FileSystemObject:
    """
    Represents a file-system object in the provider surface.
    """

    path: Path
    resource_type: str
    resource: Resource
    data: Data

    @property
    def external_id(self) -> str:
        return str(self.path)


@dataclass
class FileSystemProviderAdapter(BaseProviderAdapter):
    """
    Adapter for a filesystem-backed environment.

    Parameters
    ----------
    root:
        Root directory to materialise.
    provider_id:
        Stable provider identifier used in the internal model.
    principal_map:
        Optional external-id to principal map for ACL-style metadata.
    manifest_name:
        Optional JSON manifest filename used to enrich authors/readers metadata.
    """

    root: Path
    provider_id: str = "filesystem"
    principal_map: Mapping[str, Principal] = field(default_factory=dict)
    manifest_name: str = ".ites.manifest.json"

    def __post_init__(self) -> None:
        self.root = self.root.expanduser().resolve()
        self.capability = ProviderCapability(
            provider_id=self.provider_id,
            provider_type="filesystem",
            supported_resource_types=frozenset({"file", "directory", "symlink"}),
            supported_operations=frozenset(
                {
                    "filesystem.read_file",
                    "filesystem.write_file",
                    "filesystem.delete_file",
                    "filesystem.list_dir",
                    "filesystem.stat",
                }
            ),
            metadata={"root": str(self.root)},
        )

    def _manifest_path(self) -> Path:
        return self.root / self.manifest_name

    def _load_manifest(self) -> dict[str, Any]:
        path = self._manifest_path()
        if not path.exists():
            return {}

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
        return {}

    def _manifest_entry(self, relative_path: str) -> dict[str, Any]:
        manifest = self._load_manifest()
        entries = manifest.get("entries", {})
        if isinstance(entries, dict):
            value = entries.get(relative_path, {})
            if isinstance(value, dict):
                return value
        return {}

    def _resolve_principals(self, ids: Iterable[str]) -> frozenset[Principal]:
        principals: set[Principal] = set()
        for external_id in ids:
            principal = self.resolve_principal(external_id)
            if principal is not None:
                principals.add(principal)
        return frozenset(principals)

    def _resource_for_path(self, path: Path) -> Resource:
        relative_path = str(path.relative_to(self.root))
        stat = path.lstat()
        resource_type = "directory" if path.is_dir() else "file"
        if path.is_symlink():
            resource_type = "symlink"

        entry = self._manifest_entry(relative_path)
        metadata = {
            "path": relative_path,
            "size": stat.st_size,
            "mode": stat.st_mode,
            "manifest": entry,
        }

        return Resource(
            id=relative_path,
            provider=self.provider_id,
            resource_type=resource_type,
            name=path.name or relative_path,
            attributes=metadata,
        )

    def _data_for_path(self, path: Path) -> Data:
        relative_path = str(path.relative_to(self.root))
        entry = self._manifest_entry(relative_path)

        author_ids = entry.get("authors", [])
        reader_ids = entry.get("readers", [])

        authors = self._resolve_principals(author_ids) if isinstance(author_ids, list) else frozenset()
        readers = self._resolve_principals(reader_ids) if isinstance(reader_ids, list) else frozenset()

        confidential = bool(entry.get("confidential", path.name.startswith(".")))
        tag = entry.get("tag", relative_path)

        return Data(
            authors=authors,
            readers=readers,
            tag=tag,
            confidential=confidential,
            metadata={
                "path": relative_path,
                "kind": "directory" if path.is_dir() else "file",
                "manifest": entry,
            },
        )

    def _walk_paths(self) -> Iterable[Path]:
        if not self.root.exists():
            return []
        return [self.root, *self.root.rglob("*")]

    def materialise(self) -> ProviderMaterialisation:
        data_items = []
        principal_map: dict[str, Principal] = dict(self.principal_map)
        resource_map: dict[str, Resource] = {}

        for path in self._walk_paths():
            if not path.exists():
                continue
            if path == self.root:
                continue
            if path.name == self.manifest_name:
                continue

            try:
                resource = self._resource_for_path(path)
                resource_map[resource.id] = resource
                data_items.append(self._data_for_path(path))
            except Exception:
                continue

        return build_materialisation(
            provider_id=self.provider_id,
            data=data_items,
            principal_map=principal_map,
            resource_map=resource_map,
            metadata={
                "root": str(self.root),
                "manifest_name": self.manifest_name,
                "item_count": len(data_items),
            },
        )

    def resolve_principal(self, external_id: str) -> Principal | None:
        return self.principal_map.get(external_id)

    def resolve_resource(self, external_id: str) -> Resource | None:
        materialisation = self.materialise()
        return materialisation.resource_map.get(external_id)

    def list_principals(self) -> Iterable[Principal]:
        materialisation = self.materialise()
        return materialisation.principal_map.values()

    def list_resources(self) -> Iterable[Resource]:
        materialisation = self.materialise()
        return materialisation.resource_map.values()

    def describe_environment(self) -> Environment:
        return self.materialise().environment

    def execute(self, proposal: Proposal) -> ProviderActionResult:
        """
        Execute a proposal against the filesystem.

        Supported operations:
        - filesystem.read_file
        - filesystem.write_file
        - filesystem.delete_file
        - filesystem.list_dir
        - filesystem.stat

        The adapter interprets `PrimitiveAction.resource` as a filesystem path
        relative to the configured root.
        """
        if not isinstance(proposal, PrimitiveAction):
            return ProviderActionResult(
                ok=False,
                action=proposal,
                error="Filesystem provider only executes primitive actions.",
            )

        operation = proposal.provider_operation
        resource = proposal.resource
        if resource is None:
            return ProviderActionResult(
                ok=False,
                action=proposal,
                error="Primitive action is missing a target resource.",
            )

        target = self.root / resource.id
        try:
            target = target.resolve()
        except Exception:
            target = (self.root / resource.id)

        if self.root not in target.parents and target != self.root:
            return ProviderActionResult(
                ok=False,
                action=proposal,
                error="Target is outside the configured filesystem root.",
            )

        try:
            if operation == "filesystem.read_file":
                if not target.is_file():
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error="Target is not a regular file.",
                    )
                output = target.read_text(encoding="utf-8")
                return ProviderActionResult(ok=True, action=proposal, output=output)

            if operation == "filesystem.write_file":
                payload = proposal.inputs
                content = ""
                if payload:
                    first = next(iter(payload))
                    content = str(first.value)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return ProviderActionResult(ok=True, action=proposal, output=str(target))

            if operation == "filesystem.delete_file":
                if target.is_dir():
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error="Refusing to delete a directory via delete_file.",
                    )
                if target.exists():
                    target.unlink()
                return ProviderActionResult(ok=True, action=proposal, output=str(target))

            if operation == "filesystem.list_dir":
                if not target.is_dir():
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error="Target is not a directory.",
                    )
                listing = sorted(child.name for child in target.iterdir())
                return ProviderActionResult(ok=True, action=proposal, output=listing)

            if operation == "filesystem.stat":
                stat = target.stat()
                return ProviderActionResult(
                    ok=True,
                    action=proposal,
                    output={
                        "path": str(target),
                        "size": stat.st_size,
                        "mode": stat.st_mode,
                        "is_file": target.is_file(),
                        "is_dir": target.is_dir(),
                    },
                )

            return ProviderActionResult(
                ok=False,
                action=proposal,
                error=f"Unsupported filesystem operation: {operation}",
            )
        except Exception as exc:
            return ProviderActionResult(
                ok=False,
                action=proposal,
                error=str(exc),
            )


def build_filesystem_environment(
    root: str | Path,
    *,
    provider_id: str = "filesystem",
    principal_map: Mapping[str, Principal] | None = None,
) -> ProviderMaterialisation:
    """
    Convenience helper to materialise a filesystem environment in one call.
    """
    adapter = FileSystemProviderAdapter(
        root=Path(root),
        provider_id=provider_id,
        principal_map={} if principal_map is None else dict(principal_map),
    )
    return adapter.materialise()


__all__ = [
    "FileSystemObject",
    "FileSystemProviderAdapter",
    "build_filesystem_environment",
]
