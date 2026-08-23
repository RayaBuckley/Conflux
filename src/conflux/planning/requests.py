"""Side-effect-free planner requests and explicit budgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from conflux.domain import Artifact, Provenance, fingerprint, provenance_union

from .model import Plan


@dataclass(frozen=True, slots=True)
class PlanBudgets:
    """Immutable resource bounds for a plan execution."""

    max_nodes: int = 128
    max_transitions: int = 512
    max_planner_calls: int = 16
    max_continuation_depth: int = 8
    max_loop_iterations: int = 32
    max_effects: int = 64
    max_output_bytes: int = 1_048_576
    max_elapsed_seconds: float = 300.0

    def __post_init__(self) -> None:
        if (
            min(
                self.max_nodes,
                self.max_transitions,
                self.max_planner_calls,
                self.max_continuation_depth,
                self.max_loop_iterations,
                self.max_effects,
                self.max_output_bytes,
                self.max_elapsed_seconds,
            )
            <= 0
        ):
            raise ValueError("all planning bounds must be positive")

    def to_dict(self) -> dict[str, object]:
        """Serialise the budgets to a canonical dictionary."""
        return {
            "max_nodes": self.max_nodes,
            "max_transitions": self.max_transitions,
            "max_planner_calls": self.max_planner_calls,
            "max_continuation_depth": self.max_continuation_depth,
            "max_loop_iterations": self.max_loop_iterations,
            "max_effects": self.max_effects,
            "max_output_bytes": self.max_output_bytes,
            "max_elapsed_seconds": self.max_elapsed_seconds,
        }


@dataclass(frozen=True, slots=True)
class PlanningRequest:
    """Side-effect-free request for an initial plan from the planner."""

    request_id: str
    goal: str
    observations: tuple[Artifact[Any], ...]
    catalogue_fingerprint: str
    budgets: PlanBudgets
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.request_id or not self.goal or not self.catalogue_fingerprint:
            raise ValueError("planning request identity, goal, and catalogue are required")
        object.__setattr__(self, "observations", tuple(self.observations))

    def to_dict(self) -> dict[str, object]:
        """Serialise the planning request to a canonical dictionary."""
        return {
            "request_id": self.request_id,
            "goal": self.goal,
            "observation_ids": [item.id for item in self.observations],
            "observation_fingerprints": [item.fingerprint for item in self.observations],
            "catalogue_fingerprint": self.catalogue_fingerprint,
            "budgets": self.budgets.to_dict(),
            "provenance": self.provenance.to_dict(),
        }

    @property
    def fingerprint(self) -> str:
        """Return the content fingerprint of the planning request."""
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class ContinuationRequest:
    """Request for a continuation patch from the planner mid-execution."""

    request_id: str
    plan: Plan
    completed_node_ids: tuple[str, ...]
    observations: tuple[Artifact[Any], ...]
    catalogue_fingerprint: str
    remaining_budgets: PlanBudgets
    trigger: str
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.request_id or not self.trigger or not self.catalogue_fingerprint:
            raise ValueError("continuation identity, trigger, and catalogue are required")
        object.__setattr__(self, "completed_node_ids", tuple(self.completed_node_ids))
        object.__setattr__(self, "observations", tuple(self.observations))
        unknown = set(self.completed_node_ids) - self.plan.node_ids
        if unknown:
            raise ValueError(f"completed summary references unknown nodes: {sorted(unknown)}")

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        plan: Plan,
        completed_node_ids: tuple[str, ...],
        observations: tuple[Artifact[Any], ...],
        catalogue_fingerprint: str,
        remaining_budgets: PlanBudgets,
        trigger: str,
        control_provenance: Provenance,
    ) -> ContinuationRequest:
        """Construct a ContinuationRequest with derived provenance."""
        sources = [plan.invocation_provenance, control_provenance]
        sources.extend(observation.provenance for observation in observations)
        provenance = provenance_union(*sources).with_activity(f"continuation:{request_id}")
        return cls(
            request_id,
            plan,
            completed_node_ids,
            observations,
            catalogue_fingerprint,
            remaining_budgets,
            trigger,
            provenance,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise the continuation request to a canonical dictionary."""
        return {
            "request_id": self.request_id,
            "plan_id": self.plan.id,
            "plan_fingerprint": self.plan.fingerprint,
            "completed_node_ids": list(self.completed_node_ids),
            "observations": [{"id": item.id, "fingerprint": item.fingerprint} for item in self.observations],
            "catalogue_fingerprint": self.catalogue_fingerprint,
            "remaining_budgets": self.remaining_budgets.to_dict(),
            "trigger": self.trigger,
            "provenance": self.provenance.to_dict(),
        }

    @property
    def fingerprint(self) -> str:
        """Return the content fingerprint of the continuation request."""
        return fingerprint(self.to_dict())


__all__ = ["ContinuationRequest", "PlanBudgets", "PlanningRequest"]
