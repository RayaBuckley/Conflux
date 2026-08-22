"""Pinned, fail-closed Cedar CLI policy adapter.

The optional CLI is invoked with an argument vector and ``shell=False``.  Core
CI uses a fake runner and never downloads or executes Cedar.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType
from typing import Mapping, Protocol

from conflux.domain import (
    Action,
    ActionArgument,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    PrimitiveAction,
    Principal,
    canonical_json,
    fingerprint,
)

CEDAR_VERSION = "4.12.0"
CEDAR_COMMIT = "fdcbaed32bdb8c8d13e4eaf2b58db5555e9fb8c5"
SUPPORTED_FEATURES = frozenset(
    {
        "parc",
        "json_schema",
        "entities_json",
        "request_context",
        "explicit_forbid",
    }
)


class CedarDecision(StrEnum):
    """Cedar authorization decision enum."""

    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True, slots=True)
class CedarBinaryIdentity:
    """Pinned identity of the Cedar CLI binary."""

    version: str
    commit: str
    sha256: str

    def __post_init__(self) -> None:
        if self.version != CEDAR_VERSION or self.commit != CEDAR_COMMIT:
            raise ValueError("unsupported Cedar binary version or commit")
        _require_sha256(self.sha256, "Cedar binary")

    def to_dict(self) -> dict[str, str]:
        """Serialise the binary identity to a canonical dictionary."""
        return {"version": self.version, "commit": self.commit, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class CedarPolicyBundle:
    """Immutable Cedar policy bundle with schema, policies, entities, and binary identity."""

    bundle_id: str
    schema_json: str
    policies: str
    entities_json: str
    binary: CedarBinaryIdentity
    supported_features: frozenset[str] = SUPPORTED_FEATURES
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if not self.bundle_id or not self.policies.strip():
            raise ValueError("Cedar bundle identity and policies must be non-empty")
        schema = _canonical_json_document(self.schema_json, expected_type=dict)
        entities = _canonical_json_document(self.entities_json, expected_type=list)
        unsupported = self.supported_features - SUPPORTED_FEATURES
        if unsupported:
            raise ValueError(f"unsupported Cedar features: {sorted(unsupported)}")
        if not self.supported_features:
            raise ValueError("Cedar supported-feature declaration must be non-empty")
        object.__setattr__(self, "schema_json", schema)
        object.__setattr__(self, "entities_json", entities)
        object.__setattr__(self, "policies", self.policies.strip() + "\n")
        object.__setattr__(self, "supported_features", frozenset(self.supported_features))

    @property
    def fingerprint(self) -> str:
        """Return the content fingerprint of the policy bundle."""
        return fingerprint(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        """Serialise the policy bundle to a canonical dictionary."""
        return {
            "schema_version": self.schema_version,
            "bundle_id": self.bundle_id,
            "schema": json.loads(self.schema_json),
            "policies": self.policies,
            "entities": json.loads(self.entities_json),
            "binary": self.binary.to_dict(),
            "supported_features": sorted(self.supported_features),
        }


@dataclass(frozen=True, slots=True)
class CedarRequest:
    """Cedar authorization request with principal, action, resource, and context."""

    principal: str
    action: str
    resource: str
    context_json: str
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if not self.principal or not self.action or not self.resource:
            raise ValueError("Cedar PARC entities must be non-empty")
        object.__setattr__(
            self,
            "context_json",
            _canonical_json_document(self.context_json, expected_type=dict),
        )

    @property
    def fingerprint(self) -> str:
        """Stable fingerprint of the Cedar request."""
        return fingerprint(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        """Serialise the request to a canonical dictionary."""
        return {
            "schema_version": self.schema_version,
            "principal": self.principal,
            "action": self.action,
            "resource": self.resource,
            "context": json.loads(self.context_json),
        }


@dataclass(frozen=True, slots=True)
class CedarRunnerResult:
    """Result of invoking the Cedar CLI: availability, decision, reason, and diagnostics."""

    available: bool
    decision: CedarDecision | None
    reason: str
    response_sha256: str
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("Cedar runner result requires a reason")
        _require_sha256(self.response_sha256, "Cedar response")
        if self.available != (self.decision is not None):
            raise ValueError("available Cedar result must contain exactly one decision")
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))


class CedarRunnerPort(Protocol):
    """Port for executing Cedar authorization requests against a policy bundle."""

    def evaluate(self, bundle: CedarPolicyBundle, request: CedarRequest) -> CedarRunnerResult:
        """Evaluate a Cedar request against the given policy bundle."""
        ...


@dataclass(frozen=True, slots=True)
class CedarCliRunner:
    """Invoke the hash-pinned Cedar binary via subprocess to evaluate requests."""

    binary_path: Path
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("Cedar timeout must be positive")

    def evaluate(self, bundle: CedarPolicyBundle, request: CedarRequest) -> CedarRunnerResult:
        """Validate the bundle and authorize the request via the pinned Cedar binary."""
        try:
            binary = self.binary_path.resolve(strict=True)
        except OSError as error:
            return _failure("binary_unavailable", type(error).__name__)
        if not binary.is_file():
            return _failure("binary_unavailable", "not_a_file")
        if _file_sha256(binary) != bundle.binary.sha256:
            return _failure("binary_identity_mismatch", "sha256")
        try:
            version = self._invoke((str(binary), "--version"))
            if version.returncode != 0 or version.stdout.strip() not in {
                f"cedar {CEDAR_VERSION}",
                f"cedar-policy-cli {CEDAR_VERSION}",
            }:
                return _failure("binary_identity_mismatch", "version")
            with TemporaryDirectory(prefix="conflux-cedar-") as directory:
                root = Path(directory)
                schema_path = root / "schema.json"
                policy_path = root / "policies.cedar"
                entity_path = root / "entities.json"
                schema_path.write_text(bundle.schema_json + "\n", encoding="utf-8")
                policy_path.write_text(bundle.policies, encoding="utf-8")
                entity_path.write_text(bundle.entities_json + "\n", encoding="utf-8")
                validation = self._invoke(
                    (
                        str(binary),
                        "validate",
                        "--schema",
                        str(schema_path),
                        "--policies",
                        str(policy_path),
                    )
                )
                if validation.returncode != 0:
                    return _failure(
                        "validation_error",
                        _combined_hash(validation.stdout, validation.stderr),
                    )
                response = self._invoke(
                    (
                        str(binary),
                        "authorize",
                        "--policies",
                        str(policy_path),
                        "--entities",
                        str(entity_path),
                        "--principal",
                        request.principal,
                        "--action",
                        request.action,
                        "--resource",
                        request.resource,
                        "--context",
                        request.context_json,
                    )
                )
        except subprocess.TimeoutExpired:
            return _failure("timeout", "TimeoutExpired")
        except OSError as error:
            return _failure("runner_error", type(error).__name__)

        response_hash = _combined_hash(response.stdout, response.stderr)
        if response.returncode != 0:
            return CedarRunnerResult(False, None, "cedar_error", response_hash, ("nonzero_exit",))
        output = response.stdout.strip()
        if output not in {CedarDecision.ALLOW.value, CedarDecision.DENY.value}:
            return CedarRunnerResult(False, None, "malformed_output", response_hash, ("unexpected_stdout",))
        decision = CedarDecision(output)
        return CedarRunnerResult(
            True,
            decision,
            "cedar_allow" if decision is CedarDecision.ALLOW else "cedar_deny",
            response_hash,
        )

    def _invoke(self, command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 - executable identity is hash-pinned above
            command,
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self.timeout_seconds,
        )


@dataclass(frozen=True, slots=True)
class CedarAuthorisationPolicy:
    """Cedar-backed authorisation policy that mediates principal/action/resource decisions."""

    bundle: CedarPolicyBundle
    runner: CedarRunnerPort
    operation_versions: Mapping[str, str] = field(default_factory=dict)
    agent_metadata: Mapping[str, str] = field(default_factory=dict)
    policy_id: str = "cedar-local-cli"

    def __post_init__(self) -> None:
        if any(not key or not value for key, value in self.operation_versions.items()):
            raise ValueError("Cedar operation versions must be non-empty")
        if any(not key or not value for key, value in self.agent_metadata.items()):
            raise ValueError("Cedar agent metadata must be non-empty")
        object.__setattr__(
            self,
            "operation_versions",
            MappingProxyType(dict(self.operation_versions)),
        )
        object.__setattr__(
            self,
            "agent_metadata",
            MappingProxyType(dict(self.agent_metadata)),
        )

    @property
    def policy_version(self) -> str:
        """Composite policy version string from Cedar version and bundle fingerprint."""
        return f"{CEDAR_VERSION}:{self.bundle.fingerprint}"

    def decide(
        self,
        principal: Principal,
        action: Action,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Authorize a primitive action for a principal in the given environment."""
        request_or_reason = self._request(principal, action, environment)
        if isinstance(request_or_reason, str):
            return self._deny(request_or_reason)
        return self._evaluate(request_or_reason)

    def decide_argument(
        self,
        principal: Principal,
        action: Action,
        argument: ActionArgument,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Authorize a single argument under decision for a primitive action."""
        request_or_reason = self._request(principal, action, environment, argument=argument)
        if isinstance(request_or_reason, str):
            return self._deny(request_or_reason)
        return self._evaluate(request_or_reason)

    def _request(
        self,
        principal: Principal,
        action: Action,
        environment: EnvironmentSnapshot,
        *,
        argument: ActionArgument | None = None,
    ) -> CedarRequest | str:
        if not isinstance(action, PrimitiveAction):
            return "unsupported_action"
        if action.resource is None or action.resource not in environment.resources:
            return "missing_resource_entity"
        version = self.operation_versions.get(action.operation)
        if not version:
            return "unsupported_operation_version"
        arguments: dict[str, list[dict[str, object]]] = {}
        for item in sorted(action.arguments, key=lambda value: (value.role.value, value.name)):
            arguments.setdefault(item.role.value, []).append(
                {
                    "name": item.name,
                    "value_fingerprint": item.value_fingerprint,
                    "provenance": item.provenance.to_dict(),
                }
            )
        context = {
            "operation_version": version,
            "arguments": arguments,
            "argument_under_decision": argument.name if argument is not None else None,
            "agent": dict(sorted(self.agent_metadata.items())),
            "delegation": None,
        }
        resource_id = f"{action.resource.provider}:{action.resource.resource_type}:{action.resource.resource_id}"
        return CedarRequest(
            principal=f'Principal::"{_cedar_id(principal.id)}"',
            action=f'Action::"{_cedar_id(action.operation)}"',
            resource=f'Resource::"{_cedar_id(resource_id)}"',
            context_json=canonical_json(context),
        )

    def _evaluate(self, request: CedarRequest) -> Decision:
        try:
            result = self.runner.evaluate(self.bundle, request)
        except Exception as error:
            return self._deny("policy_runner_error", type(error).__name__, request.fingerprint)
        if not result.available or result.decision is None:
            return self._deny(result.reason, self.bundle.fingerprint, result.response_sha256, request.fingerprint)
        allowed = result.decision is CedarDecision.ALLOW
        return Decision(
            DecisionCategory.AUTHORISATION,
            allowed,
            "cedar_allow" if allowed else "cedar_deny",
            self.policy_id,
            self.policy_version,
            (self.bundle.fingerprint, result.response_sha256, request.fingerprint, *result.diagnostics),
        )

    def _deny(self, reason: str, *evidence: str) -> Decision:
        return Decision(
            DecisionCategory.AUTHORISATION,
            False,
            reason,
            self.policy_id,
            self.policy_version,
            tuple(evidence),
        )


@dataclass(frozen=True, slots=True)
class CedarArgumentAuthorisationPolicy:
    """Delegate argument-level authorisation to a wrapped :class:`CedarAuthorisationPolicy`."""

    adapter: CedarAuthorisationPolicy

    @property
    def policy_id(self) -> str:
        """Policy identifier inherited from the wrapped adapter."""
        return self.adapter.policy_id

    @property
    def policy_version(self) -> str:
        """Policy version inherited from the wrapped adapter."""
        return self.adapter.policy_version

    def decide(
        self,
        principal: Principal,
        action: Action,
        argument: ActionArgument,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Authorize a single argument by delegating to the adapter's ``decide_argument``."""
        return self.adapter.decide_argument(principal, action, argument, environment)


def _canonical_json_document(value: str, *, expected_type: type[object]) -> str:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError("malformed Cedar JSON document") from error
    if not isinstance(parsed, expected_type):
        raise ValueError(f"Cedar JSON document must be a {expected_type.__name__}")
    return canonical_json(parsed)


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} identity must be lowercase SHA-256")


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _combined_hash(stdout: str, stderr: str) -> str:
    return sha256((stdout + "\0" + stderr).encode("utf-8")).hexdigest()


def _failure(reason: str, diagnostic: str) -> CedarRunnerResult:
    return CedarRunnerResult(
        False,
        None,
        reason,
        sha256(diagnostic.encode("utf-8")).hexdigest(),
        (diagnostic,),
    )


def _cedar_id(value: str) -> str:
    if not value or any(character in {'"', "\\", "\n", "\r"} for character in value):
        raise ValueError("Cedar entity IDs contain unsupported characters")
    return value


__all__ = [
    "CEDAR_COMMIT",
    "CEDAR_VERSION",
    "SUPPORTED_FEATURES",
    "CedarArgumentAuthorisationPolicy",
    "CedarAuthorisationPolicy",
    "CedarBinaryIdentity",
    "CedarCliRunner",
    "CedarDecision",
    "CedarPolicyBundle",
    "CedarRequest",
    "CedarRunnerPort",
    "CedarRunnerResult",
]
