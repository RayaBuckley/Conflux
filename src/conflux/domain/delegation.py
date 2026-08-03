"""Scoped, attenuating delegation values and immutable one-use state."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import Lock

from .actions_base import ArgumentRole
from .identity import Principal, PrincipalContext
from .provenance import Provenance, ProvenancePrecision
from .resources import ResourceRef
from .serialization import fingerprint


@dataclass(frozen=True, slots=True)
class DelegationArgumentConstraint:
    name: str
    role: ArgumentRole
    value_fingerprint: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("delegation argument name must be non-empty")
        _require_sha256(self.value_fingerprint, "delegation argument")

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "role": self.role.value,
            "value_fingerprint": self.value_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class DelegationArgumentFact:
    name: str
    role: ArgumentRole
    value_fingerprint: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("delegation argument fact name must be non-empty")
        _require_sha256(self.value_fingerprint, "delegation argument fact")


@dataclass(frozen=True, slots=True)
class DelegationRequest:
    issuer: Principal
    beneficiary: Principal
    operation_id: str
    operation_version: str
    resource: ResourceRef
    argument_constraints: tuple[DelegationArgumentConstraint, ...]
    expires_at: str
    revocation_id: str
    issuance_provenance: Provenance
    remaining_use_count: int = 1
    redelegable: bool = False
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "argument_constraints", tuple(self.argument_constraints))
        if not self.operation_id or not self.operation_version or not self.revocation_id:
            raise ValueError("delegation request identity must be non-empty")
        if self.issuer == self.beneficiary:
            raise ValueError("delegation beneficiary must differ from issuer")
        if self.remaining_use_count != 1:
            raise ValueError("delegation is initially limited to one use")
        if self.redelegable:
            raise ValueError("redelegation is unsupported")
        _parse_time(self.expires_at)
        names = [item.name for item in self.argument_constraints]
        if len(names) != len(set(names)):
            raise ValueError("delegation argument constraints must be unique")
        if self.issuer not in self.issuance_provenance.principals:
            raise ValueError("delegation issuance provenance must include the issuer")

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "issuer_id": self.issuer.id,
            "beneficiary_id": self.beneficiary.id,
            "operation_id": self.operation_id,
            "operation_version": self.operation_version,
            "resource": self.resource.to_dict(),
            "argument_constraints": [item.to_dict() for item in self.argument_constraints],
            "expires_at": self.expires_at,
            "revocation_id": self.revocation_id,
            "remaining_use_count": self.remaining_use_count,
            "redelegable": self.redelegable,
            "issuance_provenance": self.issuance_provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ScopedDelegationGrant:
    request: DelegationRequest
    issued_at: str
    issuance_certificate_id: str
    one_use_nonce: str
    schema_version: str = "1"

    def __post_init__(self) -> None:
        issued = _parse_time(self.issued_at)
        if issued >= _parse_time(self.request.expires_at):
            raise ValueError("delegation must be issued before expiry")
        _require_sha256(self.issuance_certificate_id, "issuance certificate")
        _require_sha256(self.one_use_nonce, "delegation nonce")

    @property
    def id(self) -> str:
        return fingerprint(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "request": self.request.to_dict(),
            "issued_at": self.issued_at,
            "issuance_certificate_id": self.issuance_certificate_id,
            "one_use_nonce": self.one_use_nonce,
        }


@dataclass(frozen=True, slots=True)
class DelegationUseRecord:
    grant_id: str
    idempotency_key: str
    request_fingerprint: str
    allowed: bool
    reason: str
    used_at: str
    certificate_binding: str | None

    def __post_init__(self) -> None:
        if not self.grant_id or not self.idempotency_key or not self.reason:
            raise ValueError("delegation use evidence must be non-empty")
        _parse_time(self.used_at)


@dataclass(frozen=True, slots=True)
class DelegationConsumption:
    snapshot: DelegationStoreSnapshot
    record: DelegationUseRecord
    idempotent_retry: bool = False


@dataclass(frozen=True, slots=True)
class DelegationStoreSnapshot:
    grants: tuple[ScopedDelegationGrant, ...] = ()
    revoked_ids: frozenset[str] = frozenset()
    uses: tuple[DelegationUseRecord, ...] = ()
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "grants", tuple(self.grants))
        object.__setattr__(self, "revoked_ids", frozenset(self.revoked_ids))
        object.__setattr__(self, "uses", tuple(self.uses))
        ids = [item.id for item in self.grants]
        if len(ids) != len(set(ids)):
            raise ValueError("delegation grant IDs must be unique")

    def add(self, grant: ScopedDelegationGrant) -> DelegationStoreSnapshot:
        if any(item.id == grant.id for item in self.grants):
            return self
        return replace(self, grants=tuple(sorted(self.grants + (grant,), key=lambda item: item.id)))

    def revoke(self, revocation_id: str) -> DelegationStoreSnapshot:
        if not revocation_id:
            raise ValueError("revocation ID must be non-empty")
        return replace(self, revoked_ids=self.revoked_ids | {revocation_id})

    def consume(
        self,
        *,
        grant_id: str,
        idempotency_key: str,
        beneficiary: Principal,
        operation_id: str,
        operation_version: str,
        resource: ResourceRef,
        arguments: tuple[DelegationArgumentFact, ...],
        used_at: str,
        context: PrincipalContext,
        decision_certificate_id: str,
    ) -> DelegationConsumption:
        if not idempotency_key:
            raise ValueError("delegation idempotency key must be non-empty")
        _require_sha256(decision_certificate_id, "delegation use decision certificate")
        request_fingerprint = fingerprint(
            {
                "grant_id": grant_id,
                "beneficiary_id": beneficiary.id,
                "operation_id": operation_id,
                "operation_version": operation_version,
                "resource": resource.to_dict(),
                "arguments": [
                    {"name": item.name, "role": item.role.value, "value_fingerprint": item.value_fingerprint}
                    for item in arguments
                ],
                "used_at": used_at,
                "context": context.to_dict(),
                "decision_certificate_id": decision_certificate_id,
            }
        )
        for existing in self.uses:
            if existing.idempotency_key == idempotency_key:
                if existing.request_fingerprint == request_fingerprint:
                    return DelegationConsumption(self, existing, True)
                return DelegationConsumption(
                    self,
                    DelegationUseRecord(
                        grant_id,
                        idempotency_key,
                        request_fingerprint,
                        False,
                        "idempotency_conflict",
                        used_at,
                        None,
                    ),
                )
        grant = next((item for item in self.grants if item.id == grant_id), None)
        reason = _denial_reason(
            grant,
            self,
            beneficiary,
            operation_id,
            operation_version,
            resource,
            arguments,
            used_at,
            context,
        )
        if reason is not None or grant is None:
            return DelegationConsumption(
                self,
                DelegationUseRecord(
                    grant_id,
                    idempotency_key,
                    request_fingerprint,
                    False,
                    reason or "unknown_grant",
                    used_at,
                    None,
                ),
            )
        binding = fingerprint(
            {
                "grant_id": grant.id,
                "grant_schema_version": grant.schema_version,
                "one_use_nonce": grant.one_use_nonce,
                "decision_certificate_id": decision_certificate_id,
                "request_fingerprint": request_fingerprint,
            }
        )
        record = DelegationUseRecord(
            grant.id,
            idempotency_key,
            request_fingerprint,
            True,
            "delegation_consumed",
            used_at,
            binding,
        )
        return DelegationConsumption(replace(self, uses=self.uses + (record,)), record)


class AtomicDelegationStore:
    """In-process atomic wrapper; runtime policy consumption remains disabled."""

    def __init__(self, snapshot: DelegationStoreSnapshot = DelegationStoreSnapshot()) -> None:
        self._snapshot = snapshot
        self._lock = Lock()

    @property
    def snapshot(self) -> DelegationStoreSnapshot:
        with self._lock:
            return self._snapshot

    def consume(self, **kwargs: object) -> DelegationConsumption:
        with self._lock:
            result = self._snapshot.consume(**kwargs)  # type: ignore[arg-type]
            self._snapshot = result.snapshot
            return result


def delegation_request_from_dict(
    payload: object,
    *,
    principals: dict[str, Principal],
) -> DelegationRequest:
    if not isinstance(payload, dict):
        raise ValueError("delegation request must be an object")
    expected = {
        "schema_version", "issuer_id", "beneficiary_id", "operation_id",
        "operation_version", "resource", "argument_constraints", "expires_at",
        "revocation_id", "remaining_use_count", "redelegable", "issuance_provenance",
    }
    if set(payload) != expected or payload.get("schema_version") != "1":
        raise ValueError("unsupported or malformed delegation request")
    try:
        issuer = principals[str(payload["issuer_id"])]
        beneficiary = principals[str(payload["beneficiary_id"])]
        resource_payload = payload["resource"]
        provenance_payload = payload["issuance_provenance"]
        constraint_payload = payload["argument_constraints"]
        if not isinstance(resource_payload, dict) or not isinstance(provenance_payload, dict) or not isinstance(constraint_payload, list):
            raise ValueError
        provenance_ids = provenance_payload["principal_ids"]
        if not isinstance(provenance_ids, list):
            raise ValueError
        expected_provenance = {"principal_ids", "sources", "activities", "precision", "attested"}
        if set(provenance_payload) != expected_provenance:
            raise ValueError
        provenance = Provenance(
            principals=frozenset(principals[str(item)] for item in provenance_ids),
            sources=frozenset(str(item) for item in provenance_payload["sources"]),
            activities=tuple(str(item) for item in provenance_payload["activities"]),
            precision=ProvenancePrecision(str(provenance_payload["precision"])),
            attested=bool(provenance_payload["attested"]),
        )
        constraints = tuple(
            DelegationArgumentConstraint(
                str(item["name"]),
                ArgumentRole(str(item["role"])),
                str(item["value_fingerprint"]),
            )
            for item in constraint_payload
            if isinstance(item, dict)
        )
        if len(constraints) != len(constraint_payload):
            raise ValueError
        return DelegationRequest(
            issuer,
            beneficiary,
            str(payload["operation_id"]),
            str(payload["operation_version"]),
            ResourceRef(
                str(resource_payload["provider"]),
                str(resource_payload["resource_id"]),
                str(resource_payload["resource_type"]),
            ),
            constraints,
            str(payload["expires_at"]),
            str(payload["revocation_id"]),
            provenance,
            int(payload["remaining_use_count"]),
            bool(payload["redelegable"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("unsupported or malformed delegation request") from error


def delegation_grant_from_dict(
    payload: object,
    *,
    principals: dict[str, Principal],
) -> ScopedDelegationGrant:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "request",
        "issued_at",
        "issuance_certificate_id",
        "one_use_nonce",
    } or payload.get("schema_version") != "1":
        raise ValueError("unsupported or malformed delegation grant")
    try:
        return ScopedDelegationGrant(
            delegation_request_from_dict(payload["request"], principals=principals),
            str(payload["issued_at"]),
            str(payload["issuance_certificate_id"]),
            str(payload["one_use_nonce"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("unsupported or malformed delegation grant") from error


def _denial_reason(
    grant: ScopedDelegationGrant | None,
    store: DelegationStoreSnapshot,
    beneficiary: Principal,
    operation_id: str,
    operation_version: str,
    resource: ResourceRef,
    arguments: tuple[DelegationArgumentFact, ...],
    used_at: str,
    context: PrincipalContext,
) -> str | None:
    if grant is None:
        return "unknown_grant"
    request = grant.request
    if request.revocation_id in store.revoked_ids:
        return "delegation_revoked"
    if any(item.grant_id == grant.id and item.allowed for item in store.uses):
        return "delegation_exhausted"
    moment = _parse_time(used_at)
    if moment <= _parse_time(grant.issued_at):
        return "delegation_issued_after_influence"
    if moment >= _parse_time(request.expires_at):
        return "delegation_expired"
    if beneficiary != request.beneficiary or beneficiary not in context.principals:
        return "wrong_beneficiary"
    if operation_id != request.operation_id or operation_version != request.operation_version:
        return "operation_out_of_scope"
    if resource != request.resource:
        return "resource_out_of_scope"
    expected = {(item.name, item.role, item.value_fingerprint) for item in request.argument_constraints}
    actual = {(item.name, item.role, item.value_fingerprint) for item in arguments}
    if actual != expected:
        return "arguments_out_of_scope"
    return None


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("delegation timestamp must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("delegation timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be lowercase SHA-256")


__all__ = [
    "AtomicDelegationStore",
    "DelegationArgumentConstraint",
    "DelegationArgumentFact",
    "DelegationConsumption",
    "DelegationRequest",
    "DelegationStoreSnapshot",
    "DelegationUseRecord",
    "ScopedDelegationGrant",
    "delegation_grant_from_dict",
    "delegation_request_from_dict",
]
