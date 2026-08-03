"""Deterministic, audience-projectable delegation lifecycle evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from conflux.domain import (
    AttributionRecord,
    AudienceVisibilityDecision,
    DelegationConsumption,
    DelegationStoreSnapshot,
    EventClass,
    PrincipalContext,
    ScopedDelegationGrant,
    fingerprint,
    project_record,
)


class DelegationEventType(StrEnum):
    ISSUED = "delegation.issued"
    USED = "delegation.used"
    DENIED = "delegation.denied"
    EXPIRED = "delegation.expired"
    REVOKED = "delegation.revoked"
    IDEMPOTENT_RETRY = "delegation.idempotent_retry"


@dataclass(frozen=True, slots=True)
class DelegationTraceRecord:
    event_type: DelegationEventType
    grant: ScopedDelegationGrant
    context: PrincipalContext
    sequence: int
    timestamp: str
    reason: str
    allowed: bool
    certificate_binding: str | None = None
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if self.sequence < 0 or not self.reason:
            raise ValueError("delegation trace requires a non-negative sequence and reason")

    @property
    def event_class(self) -> EventClass:
        if self.event_type is DelegationEventType.ISSUED:
            return EventClass.DECLARATION
        if self.event_type in {DelegationEventType.DENIED, DelegationEventType.EXPIRED}:
            return EventClass.ERROR
        return EventClass.OUTCOME

    @property
    def attribution(self) -> AttributionRecord:
        request = self.grant.request
        influence = self.context.merge(request.issuance_provenance.context)
        uncertainty = (
            ("unknown_principal_context",)
            if influence.unknown
            else ()
        )
        evidence = [f"issuance_certificate:{self.grant.issuance_certificate_id}"]
        if self.certificate_binding is not None:
            evidence.append(f"use_certificate_binding:{self.certificate_binding}")
        return AttributionRecord(
            verified_input_ids=(self.grant.id,),
            conservative_influence=influence,
            policy_evidence=tuple(evidence),
            uncertainty_reasons=uncertainty,
            redaction_requirements=("revocation_id", "one_use_nonce"),
        )

    def to_dict(self) -> dict[str, object]:
        request = self.grant.request
        payload = {
            "grant_id": self.grant.id,
            "issuer_id": request.issuer.id,
            "beneficiary_id": request.beneficiary.id,
            "operation_id": request.operation_id,
            "operation_version": request.operation_version,
            "resource_fingerprint": fingerprint(request.resource.to_dict()),
            "allowed": self.allowed,
            "reason": self.reason,
            "certificate_binding": self.certificate_binding,
            "attribution": self.attribution.to_dict(),
        }
        event_id = fingerprint(
            {
                "event_type": self.event_type.value,
                "grant_id": self.grant.id,
                "sequence": self.sequence,
                "reason": self.reason,
            }
        )
        return {
            "schema_version": self.schema_version,
            "event_type": self.event_type.value,
            "event_class": self.event_class.value,
            "event_id": event_id,
            "run_id": f"delegation:{self.grant.id}",
            "branch_id": "delegation",
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "payload": payload,
        }

    def project(self, decision: AudienceVisibilityDecision) -> dict[str, object] | None:
        return project_record(self.to_dict(), decision)


def issuance_record(
    grant: ScopedDelegationGrant,
    context: PrincipalContext,
) -> DelegationTraceRecord:
    return DelegationTraceRecord(
        DelegationEventType.ISSUED,
        grant,
        context,
        0,
        grant.issued_at,
        "delegation_issued",
        True,
        grant.issuance_certificate_id,
    )


def consumption_record(
    grant: ScopedDelegationGrant,
    consumption: DelegationConsumption,
    context: PrincipalContext,
    *,
    sequence: int,
) -> DelegationTraceRecord:
    record = consumption.record
    if consumption.idempotent_retry:
        event_type = DelegationEventType.IDEMPOTENT_RETRY
    elif record.allowed:
        event_type = DelegationEventType.USED
    elif record.reason == "delegation_expired":
        event_type = DelegationEventType.EXPIRED
    else:
        event_type = DelegationEventType.DENIED
    return DelegationTraceRecord(
        event_type,
        grant,
        context,
        sequence,
        record.used_at,
        record.reason,
        record.allowed,
        record.certificate_binding,
    )


def revocation_record(
    grant: ScopedDelegationGrant,
    snapshot: DelegationStoreSnapshot,
    context: PrincipalContext,
    *,
    sequence: int,
    revoked_at: str,
) -> DelegationTraceRecord:
    if grant.request.revocation_id not in snapshot.revoked_ids:
        raise ValueError("delegation revocation is not present in the snapshot")
    return DelegationTraceRecord(
        DelegationEventType.REVOKED,
        grant,
        context,
        sequence,
        revoked_at,
        "delegation_revoked",
        False,
    )


__all__ = [
    "DelegationEventType",
    "DelegationTraceRecord",
    "consumption_record",
    "issuance_record",
    "revocation_record",
]
