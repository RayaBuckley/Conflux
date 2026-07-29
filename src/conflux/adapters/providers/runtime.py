"""Deterministic in-memory and confined filesystem execution adapters."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from conflux.domain import Action, PrimitiveAction
from conflux.domain import action_fingerprint as fingerprint_action
from conflux.ports import ProviderResult


@dataclass(slots=True)
class InMemoryExecutor:
    """Execute against memory only, with certificate-based idempotency."""

    failures: frozenset[str] = frozenset()
    outcomes: dict[str, ProviderResult] = field(default_factory=dict)
    certificate_bindings: dict[str, str] = field(default_factory=dict)

    def execute(
        self,
        action: Action,
        *,
        certificate_id: str,
        action_fingerprint: str,
    ) -> ProviderResult:
        if not certificate_id or action_fingerprint != fingerprint_action(action):
            return ProviderResult(False, error="certificate_action_mismatch")
        bound = self.certificate_bindings.get(certificate_id)
        if bound is not None and bound != action_fingerprint:
            return ProviderResult(False, error="certificate_reuse_mismatch")
        cached = self.outcomes.get(certificate_id)
        if cached is not None:
            return cached
        self.certificate_bindings[certificate_id] = action_fingerprint
        result = (
            ProviderResult(False, error="configured_provider_failure")
            if action.id in self.failures
            else ProviderResult(
                True,
                outcome={
                    "action_id": action.id,
                    "idempotency_key": certificate_id,
                },
            )
        )
        self.outcomes[certificate_id] = result
        return result

@dataclass(slots=True)
class ConfinedFilesystemExecutor:
    """Write UTF-8 files beneath one root; dry-run unless explicitly enabled."""

    root: Path
    dry_run: bool = True
    outcomes: dict[str, ProviderResult] = field(default_factory=dict)
    certificate_bindings: dict[str, str] = field(default_factory=dict)

    def execute(
        self,
        action: Action,
        *,
        certificate_id: str,
        action_fingerprint: str,
    ) -> ProviderResult:
        if not certificate_id or action_fingerprint != fingerprint_action(action):
            return ProviderResult(False, error="certificate_action_mismatch")
        bound = self.certificate_bindings.get(certificate_id)
        if bound is not None and bound != action_fingerprint:
            return ProviderResult(False, error="certificate_reuse_mismatch")
        cached = self.outcomes.get(certificate_id)
        if cached is not None:
            return cached
        self.certificate_bindings[certificate_id] = action_fingerprint
        result = self._execute_once(action, certificate_id)
        self.outcomes[certificate_id] = result
        return result

    def _execute_once(self, action: Action, certificate_id: str) -> ProviderResult:
        if not isinstance(action, PrimitiveAction) or action.operation != "write":
            return ProviderResult(False, error="unsupported_filesystem_action")
        if action.resource is None or action.resource.provider != "filesystem":
            return ProviderResult(False, error="unsupported_filesystem_resource")
        if not action.inputs:
            return ProviderResult(False, error="filesystem_write_missing_input")
        value = action.inputs[0].value
        if not isinstance(value, str):
            return ProviderResult(False, error="filesystem_write_requires_text")
        try:
            root = self.root.resolve(strict=True)
            target = _confined_target(root, action.resource.resource_id)
        except (OSError, ValueError):
            return ProviderResult(False, error="filesystem_path_rejected")
        expected = action.resource.attributes.get("precondition_sha256")
        try:
            current = _current_hash(target)
        except (OSError, ValueError):
            return ProviderResult(False, error="filesystem_target_rejected")
        if expected is not None and str(expected) != current:
            return ProviderResult(False, error="filesystem_precondition_failed")
        if not self.dry_run and expected is None:
            return ProviderResult(False, error="filesystem_precondition_required")
        content = value.encode("utf-8")
        outcome = {
            "path": target.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "precondition_sha256": current,
            "idempotency_key": str(
                action.resource.attributes.get("idempotency_key", certificate_id)
            ),
            "dry_run": self.dry_run,
        }
        if self.dry_run:
            return ProviderResult(True, outcome=outcome)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
            )
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary_name, target)
            except Exception:
                Path(temporary_name).unlink(missing_ok=True)
                raise
        except OSError:
            return ProviderResult(False, error="filesystem_write_failed")
        return ProviderResult(True, outcome=outcome)


def _confined_target(root: Path, resource_id: str) -> Path:
    relative = Path(resource_id)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("unconfined path")
    target = root.joinpath(relative)
    if target.is_symlink():
        raise ValueError("symlink target")
    resolved = target.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError("path escapes root")
    return resolved


def _current_hash(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.is_symlink() or not path.is_file():
        raise ValueError("unsupported target")
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = ["ConfinedFilesystemExecutor", "InMemoryExecutor"]
