"""Deterministic authority-minimising plan selection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .model import Plan


class CandidateSecurity(StrEnum):
    """Enumerates security classifications for plan candidates."""

    SAFE = "safe"
    BOUNDED_SAFE = "bounded_safe"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"

    @property
    def eligible(self) -> bool:
        """Return True if the candidate is eligible for selection."""
        return self in {CandidateSecurity.SAFE, CandidateSecurity.BOUNDED_SAFE}


@dataclass(frozen=True, slots=True)
class PlanCandidate:
    """A scored plan candidate with security and cost metadata."""

    plan: Plan
    security: CandidateSecurity
    utility: float
    authority_footprint: frozenset[str]
    sensitive_observations: int
    cost: float
    irreversible_effects: int
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "authority_footprint",
            frozenset(self.authority_footprint),
        )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        if self.sensitive_observations < 0 or self.cost < 0 or self.irreversible_effects < 0:
            raise ValueError("candidate cost and risk counts cannot be negative")

    def objective_vector(
        self,
        *,
        omit: str | None = None,
    ) -> tuple[object, ...]:
        """Return the lexicographic objective vector, optionally omitting one objective."""
        objectives: list[object] = [
            0 if self.security == CandidateSecurity.SAFE else 1,
        ]
        values = (
            ("utility", -self.utility),
            ("authority", len(self.authority_footprint)),
            ("sensitive_observations", self.sensitive_observations),
            ("irreversible_effects", self.irreversible_effects),
            ("cost", self.cost),
        )
        objectives.extend(value for name, value in values if name != omit)
        objectives.append(self.plan.fingerprint)
        return tuple(objectives)

    def to_dict(self) -> dict[str, object]:
        """Serialise the candidate to a canonical dictionary."""
        return {
            "plan_id": self.plan.id,
            "plan_fingerprint": self.plan.fingerprint,
            "security": self.security.value,
            "utility": self.utility,
            "authority_footprint": sorted(self.authority_footprint),
            "sensitive_observations": self.sensitive_observations,
            "cost": self.cost,
            "irreversible_effects": self.irreversible_effects,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True, slots=True)
class PlanSelection:
    """Result of plan selection: the chosen candidate and ranking metadata."""

    selected: PlanCandidate | None
    ranked_plan_ids: tuple[str, ...]
    objective_vectors: tuple[tuple[str, tuple[object, ...]], ...]
    excluded: tuple[tuple[str, str], ...]
    ablation: tuple[tuple[str, str | None], ...] = ()
    schema_version: str = "1"

    def to_dict(self) -> dict[str, object]:
        """Serialise the plan selection to a canonical dictionary."""
        return {
            "schema_version": self.schema_version,
            "selected_plan_id": self.selected.plan.id if self.selected else None,
            "ranked_plan_ids": list(self.ranked_plan_ids),
            "objective_vectors": [{"plan_id": plan_id, "vector": list(vector)} for plan_id, vector in self.objective_vectors],
            "excluded": [{"plan_id": plan_id, "reason": reason} for plan_id, reason in self.excluded],
            "ablation": [{"omitted_objective": objective, "selected_plan_id": plan_id} for objective, plan_id in self.ablation],
        }


def select_plan(
    candidates: tuple[PlanCandidate, ...],
    *,
    include_ablation: bool = False,
) -> PlanSelection:
    """Select the best eligible candidate by lexicographic objective ordering."""
    candidates = tuple(candidates)
    eligible = tuple(candidate for candidate in candidates if candidate.security.eligible)
    excluded = tuple(
        sorted(
            (
                candidate.plan.id,
                f"hard_security_constraint:{candidate.security.value}",
            )
            for candidate in candidates
            if not candidate.security.eligible
        )
    )
    ranked = tuple(sorted(eligible, key=lambda item: item.objective_vector()))
    vectors = tuple((candidate.plan.id, candidate.objective_vector()) for candidate in ranked)
    ablation: tuple[tuple[str, str | None], ...] = ()
    if include_ablation:
        objectives = (
            "utility",
            "authority",
            "sensitive_observations",
            "irreversible_effects",
            "cost",
        )
        ablation = tuple(
            (
                objective,
                (
                    min(
                        eligible,
                        key=lambda item: item.objective_vector(omit=objective),
                    ).plan.id
                    if eligible
                    else None
                ),
            )
            for objective in objectives
        )
    return PlanSelection(
        ranked[0] if ranked else None,
        tuple(item.plan.id for item in ranked),
        vectors,
        excluded,
        ablation,
    )


__all__ = [
    "CandidateSecurity",
    "PlanCandidate",
    "PlanSelection",
    "select_plan",
]
