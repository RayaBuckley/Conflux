"""
Docker provider adapter.

This adapter materialises a Docker container or image-backed environment into
the internal SLED model.

The implementation is intentionally conservative:
- it does not assume a Python Docker SDK is installed,
- it uses the Docker CLI when available,
- it keeps provider-specific state out of the core model.

The goal is to expose realistic container-based attack surfaces for evaluation
and later benchmark integration.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

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
class DockerObject:
    """
    Represents a Docker-backed object in the provider surface.
    """

    external_id: str
    resource: Resource
    data: Data


@dataclass
class DockerProviderAdapter(BaseProviderAdapter):
    """
    Adapter for a Docker-backed organisational slice.

    Parameters
    ----------
    container_id:
        Container name or ID to inspect and optionally execute against.
    provider_id:
        Stable provider identifier used in the internal model.
    principal_map:
        Optional mapping from external principal identifiers to internal principals.
    resource_roots:
        Optional paths or labels used to scope the environment materialisation.
    """

    container_id: str
    provider_id: str = "docker"
    principal_map: Mapping[str, Principal] = field(default_factory=dict)
    resource_roots: Sequence[str] = field(default_factory=tuple)
    manifest_path: Path | None = None

    def __post_init__(self) -> None:
        self.capability = ProviderCapability(
            provider_id=self.provider_id,
            provider_type="docker",
            supported_resource_types=frozenset({"container", "image", "volume", "file"}),
            supported_operations=frozenset(
                {
                    "docker.exec",
                    "docker.read_file",
                    "docker.write_file",
                    "docker.inspect",
                    "docker.logs",
                    "docker.stop",
                }
            ),
            metadata={
                "container_id": self.container_id,
            },
        )

    def _run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["docker", *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def _inspect(self) -> dict[str, Any]:
        result = self._run(["inspect", self.container_id])
        if result.returncode != 0:
            return {}
        try:
            payload = json.loads(result.stdout)
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                return payload[0]
        except Exception:
            pass
        return {}

    def _manifest(self) -> dict[str, Any]:
        if self.manifest_path is None:
            return {}
        if not self.manifest_path.exists():
            return {}
        try:
            with self.manifest_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
        except Exception:
            return {}
        return {}

    def _resolve_principals(self, ids: Iterable[str]) -> frozenset[Principal]:
        principals: set[Principal] = set()
        for external_id in ids:
            principal = self.resolve_principal(external_id)
            if principal is not None:
                principals.add(principal)
        return frozenset(principals)

    def _resource_for_container(self) -> Resource:
        inspect = self._inspect()
        metadata = {
            "container_id": self.container_id,
            "inspect": inspect,
        }

        image = inspect.get("Config", {}).get("Image", "unknown")
        name = inspect.get("Name", self.container_id).lstrip("/")
        running = bool(inspect.get("State", {}).get("Running", False))

        return Resource(
            id=self.container_id,
            provider=self.provider_id,
            resource_type="container",
            name=name,
            attributes={
                "image": image,
                "running": running,
                "metadata": metadata,
            },
        )

    def _data_from_container(self) -> list[Data]:
        inspect = self._inspect()
        manifest = self._manifest()

        authors = self._resolve_principals(manifest.get("authors", [])) if isinstance(manifest.get("authors", []), list) else frozenset()
        readers = self._resolve_principals(manifest.get("readers", [])) if isinstance(manifest.get("readers", []), list) else frozenset()

        tag = manifest.get("tag", self.container_id)
        confidential = bool(manifest.get("confidential", True))

        data = Data(
            authors=authors,
            readers=readers,
            tag=str(tag),
            confidential=confidential,
            metadata={
                "container_id": self.container_id,
                "inspect": inspect,
                "manifest": manifest,
            },
        )
        return [data]

    def materialise(self) -> ProviderMaterialisation:
        resource = self._resource_for_container()
        data = self._data_from_container()
        principal_map = dict(self.principal_map)

        return build_materialisation(
            provider_id=self.provider_id,
            data=data,
            principal_map=principal_map,
            resource_map={resource.id: resource},
            metadata={
                "container_id": self.container_id,
                "resource_roots": list(self.resource_roots),
                "inspect": resource.attributes.get("metadata", {}).get("inspect", {}),
            },
        )

    def resolve_principal(self, external_id: str) -> Principal | None:
        return self.principal_map.get(external_id)

    def resolve_resource(self, external_id: str) -> Resource | None:
        materialisation = self.materialise()
        return materialisation.resource_map.get(external_id)

    def list_principals(self) -> Iterable[Principal]:
        return self.materialise().principal_map.values()

    def list_resources(self) -> Iterable[Resource]:
        return self.materialise().resource_map.values()

    def describe_environment(self) -> Environment:
        return self.materialise().environment

    def execute(self, proposal: Proposal) -> ProviderActionResult:
        """
        Execute a proposal against the Docker container.

        Supported operations:
        - docker.exec
        - docker.read_file
        - docker.write_file
        - docker.inspect
        - docker.logs
        - docker.stop
        """
        if not isinstance(proposal, PrimitiveAction):
            return ProviderActionResult(
                ok=False,
                action=proposal,
                error="Docker provider only executes primitive actions.",
            )

        operation = proposal.provider_operation
        resource = proposal.resource
        if resource is None:
            return ProviderActionResult(
                ok=False,
                action=proposal,
                error="Primitive action is missing a target resource.",
            )

        target = resource.id

        try:
            if operation == "docker.inspect":
                return ProviderActionResult(
                    ok=True,
                    action=proposal,
                    output=self._inspect(),
                )

            if operation == "docker.logs":
                result = self._run(["logs", target])
                if result.returncode != 0:
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error=result.stderr.strip() or "docker logs failed",
                    )
                return ProviderActionResult(ok=True, action=proposal, output=result.stdout)

            if operation == "docker.stop":
                result = self._run(["stop", target])
                if result.returncode != 0:
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error=result.stderr.strip() or "docker stop failed",
                    )
                return ProviderActionResult(ok=True, action=proposal, output=result.stdout.strip())

            if operation == "docker.exec":
                command = str(proposal.permission.name if proposal.permission else "sh")
                result = self._run(["exec", target, command])
                if result.returncode != 0:
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error=result.stderr.strip() or "docker exec failed",
                    )
                return ProviderActionResult(ok=True, action=proposal, output=result.stdout)

            if operation == "docker.read_file":
                file_path = resource.attributes.get("path")
                if not isinstance(file_path, str):
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error="Docker file resource is missing a path attribute.",
                    )
                result = self._run(["exec", target, "cat", file_path])
                if result.returncode != 0:
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error=result.stderr.strip() or "docker read_file failed",
                    )
                return ProviderActionResult(ok=True, action=proposal, output=result.stdout)

            if operation == "docker.write_file":
                file_path = resource.attributes.get("path")
                if not isinstance(file_path, str):
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error="Docker file resource is missing a path attribute.",
                    )
                payload = ""
                if proposal.inputs:
                    first = next(iter(proposal.inputs))
                    payload = str(first.value)
                docker_command: list[str] = [
                    "exec", "-i", target, "sh", "-c", f"cat > {json.dumps(file_path)}"
                ]
                proc = subprocess.run(
                    ["docker", *docker_command],
                    input=payload,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if proc.returncode != 0:
                    return ProviderActionResult(
                        ok=False,
                        action=proposal,
                        error=proc.stderr.strip() or "docker write_file failed",
                    )
                return ProviderActionResult(ok=True, action=proposal, output=file_path)

            return ProviderActionResult(
                ok=False,
                action=proposal,
                error=f"Unsupported docker operation: {operation}",
            )
        except Exception as exc:
            return ProviderActionResult(
                ok=False,
                action=proposal,
                error=str(exc),
            )


def build_docker_environment(
    container_id: str,
    *,
    provider_id: str = "docker",
    principal_map: Mapping[str, Principal] | None = None,
    manifest_path: str | Path | None = None,
) -> ProviderMaterialisation:
    """
    Convenience helper to materialise a Docker container environment.
    """
    adapter = DockerProviderAdapter(
        container_id=container_id,
        provider_id=provider_id,
        principal_map={} if principal_map is None else dict(principal_map),
        manifest_path=Path(manifest_path) if manifest_path is not None else None,
    )
    return adapter.materialise()


__all__ = [
    "DockerObject",
    "DockerProviderAdapter",
    "build_docker_environment",
]
