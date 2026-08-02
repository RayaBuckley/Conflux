"""Audience disclosure and structured conservative attribution values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .actions import Action, ActionArgument, action_inputs
from .decisions import ActionDecision
from .identity import Principal, PrincipalContext
from .provenance import provenance_union
from .serialization import canonical_value, fingerprint


class EventClass(StrEnum):
    DECLARATION = "declaration"
    DECISION = "decision"
    OUTCOME = "outcome"
    OUTPUT = "output"
    ERROR = "error"


class DisclosureLevel(StrEnum):
    NONE = "none"
    EXISTENCE = "existence"
    REDACTED = "redacted"
    FULL = "full"


@dataclass(frozen=True, slots=True)
class AudienceVisibilityDecision:
    audience: Principal
    event_class: EventClass
    level: DisclosureLevel
    reason: str
    policy_id: str
    policy_version: str

    def __post_init__(self) -> None:
        if not self.reason or not self.policy_id or not self.policy_version:
            raise ValueError("audience visibility decision requires policy evidence")

    def to_dict(self) -> dict[str, object]:
        return {
            "audience_id": self.audience.id,
            "event_class": self.event_class.value,
            "level": self.level.value,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class AttributionRecord:
    verified_input_ids: tuple[str, ...]
    conservative_influence: PrincipalContext
    policy_evidence: tuple[str, ...]
    uncertainty_reasons: tuple[str, ...]
    redaction_requirements: tuple[str, ...]
    model_explanation: str | None = None
    model_explanation_trusted: bool = False
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "verified_input_ids", tuple(self.verified_input_ids))
        object.__setattr__(self, "policy_evidence", tuple(self.policy_evidence))
        object.__setattr__(self, "uncertainty_reasons", tuple(self.uncertainty_reasons))
        object.__setattr__(self, "redaction_requirements", tuple(self.redaction_requirements))
        if self.model_explanation_trusted:
            raise ValueError("model explanations cannot be marked trusted")

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "verified_input_ids": list(self.verified_input_ids),
            "conservative_influence": self.conservative_influence.to_dict(),
            "policy_evidence": list(self.policy_evidence),
            "uncertainty_reasons": list(self.uncertainty_reasons),
            "redaction_requirements": list(self.redaction_requirements),
            "model_explanation": self.model_explanation,
            "model_explanation_trusted": self.model_explanation_trusted,
        }


def attribution_for_action(
    action: Action,
    context: PrincipalContext,
    decision: ActionDecision | None,
    *,
    model_explanation: str | None = None,
) -> AttributionRecord:
    inputs = action_inputs(action)
    arguments = tuple(item for item in getattr(action, "arguments", ()) if isinstance(item, ActionArgument))
    provenances = tuple(item.provenance for item in inputs) + tuple(item.provenance for item in arguments)
    influence = context.merge(provenance_union(*provenances).context) if provenances else context
    uncertainty_items: set[str] = set()
    if context.unknown:
        uncertainty_items.add("unknown_principal_context")
    if any(item.is_unknown for item in provenances):
        uncertainty_items.add("unattested_or_unknown_provenance")
    uncertainty = tuple(sorted(uncertainty_items))
    policy_evidence = (
        tuple(f"{item.category.value}:{item.policy_id}@{item.policy_version}:{item.reason}" for item in decision.decisions)
        if decision is not None
        else ()
    )
    redactions = tuple(sorted(argument.name for argument in arguments if argument.redacted_value is None))
    return AttributionRecord(
        tuple(sorted(item.id for item in inputs if not item.provenance.is_unknown)),
        influence,
        policy_evidence,
        uncertainty,
        redactions,
        model_explanation,
    )


def project_record(
    record: dict[str, object],
    decision: AudienceVisibilityDecision,
) -> dict[str, object] | None:
    """Produce a deterministic audience view without copying hidden payload fields."""

    if decision.level == DisclosureLevel.NONE:
        return None
    envelope_names = (
        "schema_version",
        "event_type",
        "event_class",
        "event_id",
        "run_id",
        "branch_id",
        "sequence",
        "timestamp",
    )
    envelope = {name: canonical_value(record[name]) for name in envelope_names if name in record}
    envelope["audience_visibility"] = decision.to_dict()
    if decision.level == DisclosureLevel.EXISTENCE:
        return envelope
    if decision.level == DisclosureLevel.REDACTED:
        return {
            **envelope,
            "payload": {
                "redacted": True,
                "payload_fingerprint": fingerprint(record.get("payload", {})),
            },
        }
    return {**canonical_value(record), "audience_visibility": decision.to_dict()}


def explain_attribution(
    record: AttributionRecord,
    level: DisclosureLevel,
) -> str | None:
    if level == DisclosureLevel.NONE:
        return None
    if level == DisclosureLevel.EXISTENCE:
        return "Attribution evidence exists."
    principal_ids = cast_principal_ids(record.conservative_influence)
    if level == DisclosureLevel.REDACTED:
        return (
            f"Attribution includes {len(principal_ids)} Principal(s); {len(record.uncertainty_reasons)} uncertainty reason(s) are retained."
        )
    return (
        f"Principal Context: {', '.join(principal_ids) or 'unknown'}. "
        f"Verified inputs: {', '.join(record.verified_input_ids) or 'none'}. "
        f"Uncertainty: {', '.join(record.uncertainty_reasons) or 'none'}."
    )


def cast_principal_ids(context: PrincipalContext) -> tuple[str, ...]:
    return tuple(sorted(principal.id for principal in context.principals))


__all__ = [
    "AttributionRecord",
    "AudienceVisibilityDecision",
    "DisclosureLevel",
    "EventClass",
    "attribution_for_action",
    "explain_attribution",
    "project_record",
]
