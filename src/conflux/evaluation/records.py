"""Versioned deterministic trace and result records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from conflux.domain import Decision, EventClass, canonical_json, fingerprint
from conflux.ites import ActionOutcome, ITESReport, TraceEvent
from conflux.planning.state import PlanExecutionState, PlanTraceEvent

RESULT_SCHEMA_VERSION = "1"


class SerializableRecord(Protocol):
    """Protocol for records that can serialise to a dictionary."""

    def to_dict(self) -> dict[str, object]: ...


class RunStatus(StrEnum):
    """Terminal status of an evaluation run."""

    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class UtilityOutcome:
    """Captures whether the task completed and any utility details."""

    completed: bool
    details: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialise the utility outcome to a dictionary."""
        return {"completed": self.completed, "details": self.details}


@dataclass(frozen=True, slots=True)
class RunResult:
    """Versioned summary of a complete evaluation run with security and utility metrics."""

    run_id: str
    status: RunStatus
    source: dict[str, object]
    manifest_hash: str
    security: dict[str, object]
    utility: UtilityOutcome
    bounds: dict[str, object]
    diagnostics: dict[str, object]
    trace_path: str
    trace_sha256: str
    schema_version: str = RESULT_SCHEMA_VERSION

    @classmethod
    def from_report(
        cls,
        report: ITESReport,
        *,
        source: dict[str, object] | None = None,
        manifest: dict[str, object] | None = None,
        utility: UtilityOutcome = UtilityOutcome(False, "not_evaluated"),
        trace_path: str = "trace.jsonl",
        trace_sha256: str = "",
    ) -> "RunResult":
        """Build a run result from an ITES report and optional provenance metadata."""
        assessments: dict[str, object] = {
            item.name: {
                "holds": item.holds,
                "details": item.details,
                "evidence": list(item.evidence),
            }
            for item in report.assessments
        }
        failed = report.provider_failed_count > 0 or any(
            event.action is None and event.reason.startswith("model_error:") for branch in report.branches for event in branch.trace
        )
        status = RunStatus.FAILED if failed else (RunStatus.INCOMPLETE if report.incomplete else RunStatus.COMPLETED)
        return cls(
            report.run_id,
            status,
            source or {},
            fingerprint(manifest or {}),
            assessments,
            utility,
            {
                "model_calls": report.model_calls,
                "max_model_calls": report.max_model_calls,
                "incomplete": report.incomplete,
            },
            {
                "proposed": report.proposed_count,
                "authorised": report.authorised_count,
                "blocked": report.blocked_count,
                "executed": report.executed_count,
                "provider_failed": report.provider_failed_count,
                "incomplete": report.incomplete_count,
            },
            trace_path,
            trace_sha256,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise the run result to a schema-compliant dictionary."""
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status.value,
            "source": self.source,
            "manifest_hash": self.manifest_hash,
            "security": self.security,
            "utility": self.utility.to_dict(),
            "bounds": self.bounds,
            "diagnostics": self.diagnostics,
            "trace": {"path": self.trace_path, "sha256": self.trace_sha256},
        }


@dataclass(frozen=True, slots=True)
class DeterministicClock:
    """Reproducible timestamp generator with a fixed start and step."""

    start: datetime = field(default_factory=lambda: datetime(2000, 1, 1, tzinfo=UTC))
    step: timedelta = timedelta(microseconds=1)

    def at(self, sequence: int) -> str:
        """Return the ISO timestamp at the given sequence offset."""
        return (self.start + self.step * sequence).isoformat().replace("+00:00", "Z")


def action_event_type(event: TraceEvent) -> str:
    """Map a trace event's outcome to a canonical event type string."""
    if event.outcome == ActionOutcome.BLOCKED and event.action is None:
        if "ModelOutputError" in event.reason:
            return "model.parse_failed"
        if event.reason.startswith("model_error:"):
            return "run.failed"
    return {
        ActionOutcome.PROPOSED: "proposal.observed",
        ActionOutcome.AUTHORISED: "action.allowed",
        ActionOutcome.BLOCKED: "action.blocked",
        ActionOutcome.EXECUTED: "action.executed",
        ActionOutcome.PROVIDER_FAILED: "action.failed",
        ActionOutcome.INCOMPLETE: "bound.reached",
        ActionOutcome.COMPLETE: "branch.completed",
    }[event.outcome]


def _record(
    *,
    schema_version: str,
    event_type: str,
    run_id: str,
    branch_id: str,
    sequence: int,
    timestamp: str,
    causal_parent_ids: tuple[str, ...],
    payload: dict[str, object],
) -> dict[str, object]:
    event_id = fingerprint(
        {
            "schema_version": schema_version,
            "event_type": event_type,
            "run_id": run_id,
            "branch_id": branch_id,
            "causal_parent_ids": causal_parent_ids,
            "payload": payload,
        }
    )
    return {
        "schema_version": schema_version,
        "event_type": event_type,
        "event_class": _event_class(event_type).value,
        "event_id": event_id,
        "run_id": run_id,
        "branch_id": branch_id,
        "sequence": sequence,
        "timestamp": timestamp,
        "causal_parent_ids": list(causal_parent_ids),
        "payload": payload,
    }


def _policy_event_type(decision: Decision) -> str:
    if decision.category.value == "authorisation":
        if "argument" in decision.reason:
            return "policy.argument_decided"
        return "policy.action_decided"
    return f"policy.{decision.category.value}_decided"


def _event_class(event_type: str) -> EventClass:
    if event_type in {"proposal.observed", "run.started", "branch.created"}:
        return EventClass.DECLARATION
    if event_type.startswith("policy.") or event_type in {"action.allowed", "action.blocked"}:
        return EventClass.DECISION
    if event_type.endswith("failed") or event_type in {"model.parse_failed", "bound.reached"}:
        return EventClass.ERROR
    if event_type in {"action.executed", "code.completed", "model.responded"}:
        return EventClass.OUTPUT
    return EventClass.OUTCOME


def trace_records(
    report: ITESReport,
    clock: DeterministicClock = DeterministicClock(),
) -> tuple[dict[str, object], ...]:
    """Convert an ITES report into a flat, causally ordered sequence of trace records."""
    records: list[dict[str, object]] = []
    sequence = 0
    last_by_branch: dict[str, str] = {}

    def emit(
        event_type: str,
        branch_id: str,
        payload: dict[str, object],
        parents: tuple[str, ...] = (),
    ) -> str:
        nonlocal sequence
        record = _record(
            schema_version=report.trace_schema_version,
            event_type=event_type,
            run_id=report.run_id,
            branch_id=branch_id,
            sequence=sequence,
            timestamp=clock.at(sequence),
            causal_parent_ids=parents,
            payload=payload,
        )
        records.append(record)
        sequence += 1
        identifier = str(record["event_id"])
        last_by_branch[branch_id] = identifier
        return identifier

    run_start = emit(
        "run.started",
        "run",
        {
            "max_model_calls": report.max_model_calls,
            "trace_schema_version": report.trace_schema_version,
        },
    )
    unique_events = {(event.branch_id, event.id): event for branch in report.branches for event in branch.trace}
    created: set[str] = set()
    for event in sorted(
        unique_events.values(),
        key=lambda item: (item.depth, item.branch_id, item.sequence, item.id),
    ):
        if event.branch_id not in created:
            parent_id = last_by_branch.get(event.parent_branch_id, run_start) if event.parent_branch_id else run_start
            emit(
                "branch.created",
                event.branch_id,
                {
                    "parent_branch_id": event.parent_branch_id,
                    "depth": event.depth,
                },
                (parent_id,),
            )
            created.add(event.branch_id)
        parent = last_by_branch[event.branch_id]
        if event.decision is not None:
            for decision in event.decision.decisions:
                parent = emit(
                    _policy_event_type(decision),
                    event.branch_id,
                    {
                        "action_event_id": event.id,
                        "context_fingerprint": event.context.fingerprint,
                        "decision": decision.to_dict(),
                    },
                    (parent,),
                )
        emit(
            action_event_type(event),
            event.branch_id,
            event.to_dict(),
            (parent,),
        )
    for branch in sorted(report.branches, key=lambda item: item.branch_id):
        parent = last_by_branch.get(branch.branch_id, run_start)
        emit(
            "branch.completed",
            branch.branch_id,
            {
                "status": branch.status.value,
                "state_key": branch.state_key,
                "model_calls": branch.model_calls,
            },
            (parent,),
        )
    run_failed = any(event.action is None and event.reason.startswith("model_error:") for event in unique_events.values())
    emit(
        "run.failed" if run_failed else "run.completed",
        "run",
        {
            "incomplete": report.incomplete,
            "model_calls": report.model_calls,
            "branch_count": len(report.branches),
        },
        tuple(last_by_branch[branch.branch_id] for branch in sorted(report.branches, key=lambda item: item.branch_id)),
    )
    return tuple(records)


def write_trace(report: ITESReport, path: Path) -> str:
    """Write trace records to a JSONL file and return its SHA-256 hash."""
    content = "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in trace_records(report))
    path.write_text(content, encoding="utf-8", newline="\n")
    return sha256(content.encode("utf-8")).hexdigest()


def write_result(result: RunResult, path: Path) -> None:
    """Write a run result as canonical JSON to the given path."""
    path.write_text(canonical_json(result.to_dict()) + "\n", encoding="utf-8", newline="\n")


def plan_trace_records(
    state: PlanExecutionState,
    clock: DeterministicClock = DeterministicClock(),
) -> tuple[dict[str, object], ...]:
    """Convert planner events to the common timestamped trace envelope."""
    return tuple(
        {
            "schema_version": "3",
            "event_type": event.event_type,
            "event_class": _event_class(event.event_type).value,
            "event_id": event.id,
            "run_id": event.run_id,
            "plan_id": event.plan_id,
            "node_id": event.node_id,
            "branch_id": event.branch_id,
            "sequence": event.sequence,
            "timestamp": clock.at(event.sequence),
            "causal_parent_ids": list(event.causal_parent_ids),
            "payload": event.payload,
        }
        for event in state.events
    )


def replay_plan_trace(
    initial_plan: dict[str, object],
    events: tuple[PlanTraceEvent, ...],
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    """Reconstruct the final plan and node-state summary from retained events."""
    plan = initial_plan
    node_states: tuple[dict[str, object], ...] = ()
    for event in events:
        if event.event_type == "plan.patch_applied":
            candidate = event.payload.get("plan")
            if isinstance(candidate, dict):
                plan = candidate
        if event.event_type in {
            "plan.completed",
            "plan.failed",
            "bound.reached",
        }:
            final_plan = event.payload.get("final_plan")
            if isinstance(final_plan, dict):
                plan = final_plan
            states = event.payload.get("node_states")
            if isinstance(states, list) and all(isinstance(item, dict) for item in states):
                node_states = tuple(states)
    return plan, node_states


def write_plan_trace(
    state: PlanExecutionState,
    path: Path,
    clock: DeterministicClock = DeterministicClock(),
) -> str:
    """Write planner trace records to a JSONL file and return its SHA-256 hash."""
    content = "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in plan_trace_records(state, clock))
    path.write_text(content, encoding="utf-8", newline="\n")
    return sha256(content.encode("utf-8")).hexdigest()


def write_plan_result(result: SerializableRecord, path: Path) -> None:
    """Write a plan result as canonical JSON to the given path."""
    path.write_text(
        canonical_json(result.to_dict()) + "\n",
        encoding="utf-8",
        newline="\n",
    )


__all__ = [
    "DeterministicClock",
    "RESULT_SCHEMA_VERSION",
    "RunResult",
    "RunStatus",
    "UtilityOutcome",
    "action_event_type",
    "trace_records",
    "plan_trace_records",
    "replay_plan_trace",
    "write_plan_trace",
    "write_plan_result",
    "write_result",
    "write_trace",
]
