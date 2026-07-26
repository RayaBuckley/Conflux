"""Trace model for SLED.

This module defines the immutable trace objects used by SLED to represent both
simulated internal model mechanics and real execution artefacts.

The design goal is to keep the trace layer generic enough to support:

- worst-case branching over possible model behaviours,
- explicit plan generation,
- capability or authority tokens,
- parser / router / executor style architectures,
- provenance-aware influence tracking,
- and adapters for real external defence repositories.

Downstream modules should treat these objects as the canonical representation of
an explored execution trace.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence


class TraceKind(str, Enum):
    """High-level trace family."""

    SIMULATED = "simulated"
    REAL = "real"
    HYBRID = "hybrid"
    COUNTEREXAMPLE = "counterexample"
    UNKNOWN = "unknown"


class TraceEventKind(str, Enum):
    """Kinds of events that may appear in a trace."""

    MODEL_INPUT = "model_input"
    MODEL_OUTPUT = "model_output"
    PLAN = "plan"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    READ = "read"
    WRITE = "write"
    ACTION = "action"
    POLICY_DECISION = "policy_decision"
    CAPABILITY_ISSUED = "capability_issued"
    CAPABILITY_CONSUMED = "capability_consumed"
    PROMPT = "prompt"
    MESSAGE = "message"
    NESTED_EXECUTION = "nested_execution"
    BOUND_REACHED = "bound_reached"
    ERROR = "error"
    OTHER = "other"


class DecisionOutcome(str, Enum):
    """Normalised decision outcome for trace events."""

    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CapabilityToken:
    """A capability-like artefact used by some defences or model architectures."""

    id: str
    issued_by: str | None = None
    owner: str | None = None
    scope: str | None = None
    action: str | None = None
    resource: str | None = None
    expires_at: datetime | None = None
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def is_expired(self, at: datetime | None = None) -> bool:
        """Return True if the token has expired."""
        if self.expires_at is None:
            return False
        if at is None:
            at = datetime.now(timezone.utc)
        return at >= self.expires_at


@dataclass(frozen=True)
class PlanStep:
    """One step in a generated execution plan."""

    id: str
    description: str
    expected_action: str | None = None
    expected_tool: str | None = None
    expected_resource: str | None = None
    required_tokens: tuple[str, ...] = field(default_factory=tuple)
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TraceEvent:
    """A single event in a SLED trace."""

    id: str
    kind: TraceEventKind
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    principal: str | None = None
    subject: str | None = None
    action: str | None = None
    resource: str | None = None

    input_text: str | None = None
    output_text: str | None = None
    decision: DecisionOutcome = DecisionOutcome.UNKNOWN

    plan_step: PlanStep | None = None
    capability: CapabilityToken | None = None
    nested_trace_id: str | None = None

    blocked: bool = False
    incomplete: bool = False
    error: str | None = None

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def is_security_relevant(self) -> bool:
        """Return True if this event is relevant to security analysis."""
        return self.kind in {
            TraceEventKind.TOOL_CALL,
            TraceEventKind.READ,
            TraceEventKind.WRITE,
            TraceEventKind.ACTION,
            TraceEventKind.POLICY_DECISION,
            TraceEventKind.CAPABILITY_ISSUED,
            TraceEventKind.CAPABILITY_CONSUMED,
            TraceEventKind.NESTED_EXECUTION,
            TraceEventKind.ERROR,
        }


@dataclass(frozen=True)
class TraceContext:
    """Context accumulated during a trace."""

    initiator: str | None = None
    latest_principal: str | None = None
    principal_history: tuple[str, ...] = field(default_factory=tuple)
    influencing_principals: frozenset[str] = field(default_factory=frozenset)

    plan_id: str | None = None
    capability_ids: frozenset[str] = field(default_factory=frozenset)
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def with_principal(self, principal: str) -> "TraceContext":
        """Return a new context with an additional principal appended."""
        history = self.principal_history + (principal,)
        return replace(
            self,
            latest_principal=principal,
            principal_history=history,
            influencing_principals=frozenset(set(self.influencing_principals) | {principal}),
        )

    def with_capability(self, capability_id: str) -> "TraceContext":
        """Return a new context with an additional capability token id."""
        return replace(
            self,
            capability_ids=frozenset(set(self.capability_ids) | {capability_id}),
        )


@dataclass(frozen=True)
class TraceSummary:
    """A compact summary of an execution trace."""

    trace_id: str
    kind: TraceKind = TraceKind.UNKNOWN

    task_name: str | None = None
    environment_name: str | None = None
    defence_name: str | None = None

    complete: bool = True
    blocked: bool = False
    violation: bool = False
    max_depth_reached: bool = False

    steps: int = 0
    model_calls: int = 0
    tool_calls: int = 0

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionTrace:
    """Canonical immutable trace object used by SLED."""

    trace_id: str
    kind: TraceKind = TraceKind.UNKNOWN

    context: TraceContext = field(default_factory=TraceContext)
    events: tuple[TraceEvent, ...] = field(default_factory=tuple)

    task_name: str | None = None
    environment_name: str | None = None
    defence_name: str | None = None

    complete: bool = True
    blocked: bool = False
    violation: bool = False
    max_depth_reached: bool = False

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def steps(self) -> int:
        """Return the number of trace events."""
        return len(self.events)

    @property
    def model_calls(self) -> int:
        """Return the number of model input events."""
        return sum(1 for event in self.events if event.kind == TraceEventKind.MODEL_INPUT)

    @property
    def tool_calls(self) -> int:
        """Return the number of tool call events."""
        return sum(1 for event in self.events if event.kind == TraceEventKind.TOOL_CALL)

    @property
    def latest_event(self) -> TraceEvent | None:
        """Return the most recent event if the trace is non-empty."""
        return self.events[-1] if self.events else None

    def add_event(self, event: TraceEvent) -> "ExecutionTrace":
        """Return a new trace with one extra event appended."""
        context = self.context
        if event.principal:
            context = context.with_principal(event.principal)
        if event.capability:
            context = context.with_capability(event.capability.id)

        labels = frozenset(set(self.labels) | set(event.labels))
        return replace(
            self,
            context=context,
            events=self.events + (event,),
            labels=labels,
        )

    def summarise(self) -> TraceSummary:
        """Convert the trace into a compact summary object."""
        return TraceSummary(
            trace_id=self.trace_id,
            kind=self.kind,
            task_name=self.task_name,
            environment_name=self.environment_name,
            defence_name=self.defence_name,
            complete=self.complete,
            blocked=self.blocked,
            violation=self.violation,
            max_depth_reached=self.max_depth_reached,
            steps=self.steps,
            model_calls=self.model_calls,
            tool_calls=self.tool_calls,
            labels=self.labels,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class TraceBranch:
    """A possible branch from a trace state.

    This is useful when SLED explores multiple model behaviours from the same
    partial execution.
    """

    id: str
    trace: ExecutionTrace
    probability: float | None = None
    weight: float | None = None
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


def make_trace(
    trace_id: str,
    *,
    kind: TraceKind = TraceKind.UNKNOWN,
    task_name: str | None = None,
    environment_name: str | None = None,
    defence_name: str | None = None,
    labels: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ExecutionTrace:
    """Convenience constructor for an empty trace."""
    return ExecutionTrace(
        trace_id=trace_id,
        kind=kind,
        task_name=task_name,
        environment_name=environment_name,
        defence_name=defence_name,
        labels=frozenset(labels or ()),
        metadata=metadata or {},
    )


def make_event(
    event_id: str,
    kind: TraceEventKind,
    *,
    principal: str | None = None,
    action: str | None = None,
    resource: str | None = None,
    input_text: str | None = None,
    output_text: str | None = None,
    decision: DecisionOutcome = DecisionOutcome.UNKNOWN,
    blocked: bool = False,
    incomplete: bool = False,
    error: str | None = None,
    labels: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> TraceEvent:
    """Convenience constructor for a trace event."""
    return TraceEvent(
        id=event_id,
        kind=kind,
        principal=principal,
        action=action,
        resource=resource,
        input_text=input_text,
        output_text=output_text,
        decision=decision,
        blocked=blocked,
        incomplete=incomplete,
        error=error,
        labels=frozenset(labels or ()),
        metadata=metadata or {},
    )
