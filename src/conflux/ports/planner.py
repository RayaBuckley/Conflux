"""Pure planner boundary for initial plans and typed continuations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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


class PlannerPort(Protocol):
    def initial_plan(self, request: PlanningRequest) -> InitialPlanResponse:
        """Return a typed plan without performing provider effects."""
        ...

    def continue_plan(self, request: ContinuationRequest) -> ContinuationResponse:
        """Return a typed patch without performing provider effects."""
        ...


__all__ = [
    "ContinuationResponse",
    "InitialPlanResponse",
    "PlannerPort",
]
