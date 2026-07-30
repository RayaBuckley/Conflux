"""Pure planner boundary for initial plans and typed continuations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from conflux.domain import Artifact

if TYPE_CHECKING:
    from conflux.planning.continuation import PlanPatch
    from conflux.planning.model import Plan
    from conflux.planning.records import PlannerRecord
    from conflux.planning.requests import ContinuationRequest, PlanningRequest


@dataclass(frozen=True, slots=True)
class InitialPlanResponse:
    plan: Plan | None
    record: PlannerRecord


@dataclass(frozen=True, slots=True)
class ContinuationResponse:
    patch: PlanPatch | None
    record: PlannerRecord


@dataclass(frozen=True, slots=True)
class ValueRequest:
    request_id: str
    node_id: str
    prompt: Artifact[Any]


@dataclass(frozen=True, slots=True)
class ValueResponse:
    output: Artifact[Any] | None
    record: PlannerRecord


class PlannerPort(Protocol):
    def initial_plan(self, request: PlanningRequest) -> InitialPlanResponse:
        """Return a typed plan without performing provider effects."""
        ...

    def continue_plan(self, request: ContinuationRequest) -> ContinuationResponse:
        """Return a typed patch without performing provider effects."""
        ...


class ValueModelPort(Protocol):
    def produce(self, request: ValueRequest) -> ValueResponse:
        """Produce one provenance-bearing value without provider effects."""
        ...


__all__ = [
    "ContinuationResponse",
    "InitialPlanResponse",
    "PlannerPort",
    "ValueModelPort",
    "ValueRequest",
    "ValueResponse",
]
