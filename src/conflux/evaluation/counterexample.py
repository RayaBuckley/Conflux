"""Counterexample objects for SLED.

This module captures concrete violating traces discovered during exhaustive
search or real execution runs. Counterexamples are the main artefact used to
show that a defence fails on a specific task or environment.

The design goal is to make violation reporting explicit and portable:
- keep the violating trace attached,
- record the first offending event when available,
- preserve the defence, environment, and task context,
- and expose a stable serialisable structure for reports and regression tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from .trace import ExecutionTrace, TraceEvent


class CounterexampleKind(str, Enum):
    """High-level type of violation observed in a trace."""

    PRIVILEGE_ESCALATION = "privilege_escalation"
    INFORMATION_EXFILTRATION = "information_exfiltration"
    UNAUTHORISED_ACTION = "unauthorised_action"
    POLICY_BYPASS = "policy_bypass"
    READ_VIOLATION = "read_violation"
    WRITE_VIOLATION = "write_violation"
    INCOMPLETE_BUT_SUSPICIOUS = "incomplete_but_suspicious"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CounterexampleWitness:
    """A single event or artefact that explains the violation."""

    event_id: str | None = None
    event: TraceEvent | None = None
    description: str = ""
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Counterexample:
    """A concrete violating execution trace."""

    counterexample_id: str
    kind: CounterexampleKind
    trace: ExecutionTrace

    task_name: str | None = None
    environment_name: str | None = None
    defence_name: str | None = None

    blocked: bool = False
    complete: bool = True
    max_depth_reached: bool = False

    first_offending_event: TraceEvent | None = None
    witnesses: tuple[CounterexampleWitness, ...] = field(default_factory=tuple)

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def trace_id(self) -> str:
        """Return the identifier of the underlying trace."""
        return self.trace.trace_id

    @property
    def is_blocked(self) -> bool:
        """Return True if the defence blocked the violating branch."""
        return self.blocked

    @property
    def is_complete(self) -> bool:
        """Return True if the violating trace completed."""
        return self.complete and not self.max_depth_reached

    def to_dict(self) -> dict[str, Any]:
        """Serialise the counterexample into a JSON-friendly structure."""
        return {
            "counterexample_id": self.counterexample_id,
            "kind": self.kind.value,
            "trace_id": self.trace.trace_id,
            "task_name": self.task_name,
            "environment_name": self.environment_name,
            "defence_name": self.defence_name,
            "blocked": self.blocked,
            "complete": self.complete,
            "max_depth_reached": self.max_depth_reached,
            "first_offending_event": (
                None
                if self.first_offending_event is None
                else _event_to_dict(self.first_offending_event)
            ),
            "witnesses": [
                _witness_to_dict(witness)
                for witness in self.witnesses
            ],
            "labels": sorted(self.labels),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "trace": _trace_to_dict(self.trace),
        }


@dataclass(frozen=True)
class CounterexampleSet:
    """A collection of counterexamples discovered in one evaluation run."""

    run_id: str
    environment_name: str | None = None
    defence_name: str | None = None
    kind: CounterexampleKind = CounterexampleKind.UNKNOWN

    counterexamples: tuple[Counterexample, ...] = field(default_factory=tuple)
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.counterexamples)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the set into a JSON-friendly structure."""
        return {
            "run_id": self.run_id,
            "environment_name": self.environment_name,
            "defence_name": self.defence_name,
            "kind": self.kind.value,
            "count": self.count,
            "counterexamples": [item.to_dict() for item in self.counterexamples],
            "labels": sorted(self.labels),
            "metadata": dict(self.metadata),
        }


def make_counterexample(
    counterexample_id: str,
    trace: ExecutionTrace,
    *,
    kind: CounterexampleKind = CounterexampleKind.UNKNOWN,
    task_name: str | None = None,
    environment_name: str | None = None,
    defence_name: str | None = None,
    blocked: bool = False,
    complete: bool = True,
    max_depth_reached: bool = False,
    first_offending_event: TraceEvent | None = None,
    witnesses: Sequence[CounterexampleWitness] | None = None,
    labels: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> Counterexample:
    """Convenience constructor for a counterexample."""
    return Counterexample(
        counterexample_id=counterexample_id,
        kind=kind,
        trace=trace,
        task_name=task_name or trace.task_name,
        environment_name=environment_name or trace.environment_name,
        defence_name=defence_name or trace.defence_name,
        blocked=blocked,
        complete=complete,
        max_depth_reached=max_depth_reached,
        first_offending_event=first_offending_event,
        witnesses=tuple(witnesses or ()),
        labels=frozenset(labels or ()),
        metadata=metadata or {},
    )


def _trace_to_dict(trace: ExecutionTrace) -> dict[str, Any]:
    """Convert a trace into a serialisable dictionary."""
    return {
        "trace_id": trace.trace_id,
        "kind": trace.kind.value,
        "task_name": trace.task_name,
        "environment_name": trace.environment_name,
        "defence_name": trace.defence_name,
        "complete": trace.complete,
        "blocked": trace.blocked,
        "violation": trace.violation,
        "max_depth_reached": trace.max_depth_reached,
        "labels": sorted(trace.labels),
        "metadata": dict(trace.metadata),
        "context": {
            "initiator": trace.context.initiator,
            "latest_principal": trace.context.latest_principal,
            "principal_history": list(trace.context.principal_history),
            "influencing_principals": sorted(trace.context.influencing_principals),
            "plan_id": trace.context.plan_id,
            "capability_ids": sorted(trace.context.capability_ids),
            "labels": sorted(trace.context.labels),
            "metadata": dict(trace.context.metadata),
        },
        "events": [_event_to_dict(event) for event in trace.events],
    }


def _event_to_dict(event: TraceEvent) -> dict[str, Any]:
    """Convert a trace event into a serialisable dictionary."""
    return {
        "id": event.id,
        "kind": event.kind.value,
        "timestamp": event.timestamp.isoformat(),
        "principal": event.principal,
        "subject": event.subject,
        "action": event.action,
        "resource": event.resource,
        "input_text": event.input_text,
        "output_text": event.output_text,
        "decision": event.decision.value,
        "plan_step": None
        if event.plan_step is None
        else {
            "id": event.plan_step.id,
            "description": event.plan_step.description,
            "expected_action": event.plan_step.expected_action,
            "expected_tool": event.plan_step.expected_tool,
            "expected_resource": event.plan_step.expected_resource,
            "required_tokens": list(event.plan_step.required_tokens),
            "labels": sorted(event.plan_step.labels),
            "metadata": dict(event.plan_step.metadata),
        },
        "capability": None
        if event.capability is None
        else {
            "id": event.capability.id,
            "issued_by": event.capability.issued_by,
            "owner": event.capability.owner,
            "scope": event.capability.scope,
            "action": event.capability.action,
            "resource": event.capability.resource,
            "expires_at": None if event.capability.expires_at is None else event.capability.expires_at.isoformat(),
            "labels": sorted(event.capability.labels),
            "metadata": dict(event.capability.metadata),
        },
        "nested_trace_id": event.nested_trace_id,
        "blocked": event.blocked,
        "incomplete": event.incomplete,
        "error": event.error,
        "labels": sorted(event.labels),
        "metadata": dict(event.metadata),
    }


def _witness_to_dict(witness: CounterexampleWitness) -> dict[str, Any]:
    """Convert a witness into a serialisable dictionary."""
    return {
        "event_id": witness.event_id,
        "event": None if witness.event is None else _event_to_dict(witness.event),
        "description": witness.description,
        "labels": sorted(witness.labels),
        "metadata": dict(witness.metadata),
    }
