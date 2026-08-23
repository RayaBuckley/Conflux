"""Deterministic plan, patch, and value fixtures for replay and conformance."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from conflux.domain import Artifact, canonical_json
from conflux.planning import (
    ContinuationRequest,
    PlannerRecord,
    PlanningRequest,
    parse_plan,
    parse_plan_patch,
)
from conflux.ports import (
    ContinuationResponse,
    InitialPlanResponse,
    ValueRequest,
    ValueResponse,
)


@dataclass(slots=True)
class ScriptedPlanner:
    """Deterministic planner that replays scripted plan and patch fixtures."""

    initial: Mapping[str, object]
    continuations: Mapping[str, object]
    planner_id: str = "scripted-planner"
    planner_version: str = "1"
    records: list[PlannerRecord] = field(default_factory=list)

    def initial_plan(self, request: PlanningRequest) -> InitialPlanResponse:
        """Return a scripted initial plan for the given planning request."""
        payload = self._lookup(self.initial, request.request_id, request.fingerprint)
        try:
            plan = parse_plan(payload, trusted_provenance=request.provenance)
        except (TypeError, ValueError) as error:
            record = self._record(request.to_dict(), payload, None, error)
            return InitialPlanResponse(None, record)
        record = self._record(request.to_dict(), payload, plan.to_dict(), None)
        return InitialPlanResponse(plan, record)

    def continue_plan(self, request: ContinuationRequest) -> ContinuationResponse:
        """Return a scripted plan patch for the given continuation request."""
        payload = self._lookup(self.continuations, request.request_id, request.fingerprint)
        try:
            patch = parse_plan_patch(payload, trusted_provenance=request.provenance)
        except (TypeError, ValueError) as error:
            record = self._record(request.to_dict(), payload, None, error)
            return ContinuationResponse(None, record)
        record = self._record(request.to_dict(), payload, patch.to_dict(), None)
        return ContinuationResponse(patch, record)

    def _lookup(
        self,
        source: Mapping[str, object],
        request_id: str,
        request_hash: str,
    ) -> object:
        if request_id in source:
            return source[request_id]
        if request_hash in source:
            return source[request_hash]
        if "*" in source:
            return source["*"]
        return {"error": "scripted_response_missing"}

    def _record(
        self,
        request: object,
        response: object,
        parsed: object | None,
        error: Exception | None,
    ) -> PlannerRecord:
        record = PlannerRecord.create(
            planner_id=self.planner_id,
            planner_version=self.planner_version,
            configuration={
                "initial_keys": sorted(self.initial),
                "continuation_keys": sorted(self.continuations),
            },
            request=request,
            response=response,
            parsed=parsed,
            raw_response=canonical_json(response),
            error=f"{type(error).__name__}: {error}" if error is not None else None,
        )
        self.records.append(record)
        return record


@dataclass(slots=True)
class ScriptedValueModel:
    """Deterministic value model that replays scripted output artifacts."""

    outputs: Mapping[str, Artifact[Any]]
    planner_id: str = "scripted-value-model"
    planner_version: str = "1"
    records: list[PlannerRecord] = field(default_factory=list)

    def produce(self, request: ValueRequest) -> ValueResponse:
        """Return a scripted output artifact for the given value request."""
        output = self.outputs.get(request.request_id, self.outputs.get(request.node_id))
        error = None if output is not None else "scripted_value_missing"
        record = PlannerRecord.create(
            planner_id=self.planner_id,
            planner_version=self.planner_version,
            configuration={"keys": sorted(self.outputs)},
            request={
                "request_id": request.request_id,
                "node_id": request.node_id,
                "prompt": request.prompt.fingerprint,
            },
            response=output.to_dict() if output is not None else {"error": error},
            parsed=output.to_dict() if output is not None else None,
            raw_response=canonical_json(output.to_dict() if output is not None else {"error": error}),
            error=error,
        )
        self.records.append(record)
        return ValueResponse(output, record)


__all__ = ["ScriptedPlanner", "ScriptedValueModel"]
