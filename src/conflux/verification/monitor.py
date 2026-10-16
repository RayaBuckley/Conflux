"""Runtime monitor emitted from a verification IR (E4: one IR, two artifacts).

The design is `writing/proof-plus-monitor-design.md` (E4, 2026-10-11); the emitter is additive
and changes no existing verification path. The design projection table was written when the plan
IR carried seven invariants and ten variables; the P5 change set then removed two declarations no
rule could assign and one duplicate invariant, so the plan IR now carries five invariants and eight
variables (eight and ten on the progress shape), and the table below is the current one.

A monitor is the tuple (IR fingerprint, invariants, projection, bound). The projection maps
runtime trace facts to IR variables; the table names the runtime source of each variable and
whether that source exists today. An invariant that needs a variable the trace cannot supply
reports ``not_exercised``, never ``holds``. That is what stops a quiet run from being recorded as
a passed check - the failure E7 measured in `writing/verdict-classes.md`, where 132 of 318
retained cells executed nothing and every one reported the property as holding.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from .interpreter import evaluate
from .ir import Expression, ExpressionKind, IRValue, SafetyInvariant, VerificationIR


class Availability(StrEnum):
    """Whether a runtime source for an IR variable exists today."""

    DERIVABLE = "derivable"
    NEEDS_PARENT_LINK = "needs_parent_link"
    NEEDS_NODE_ID = "needs_node_id"
    NO_RUNTIME_EVENT = "no_runtime_event"
    NO_EFFECT_SUMMARY = "no_effect_summary"


@dataclass(frozen=True, slots=True)
class ProjectionSource:
    """One row of the projection table: an IR variable, its runtime source, its availability."""

    variable: str
    source: str
    availability: Availability

    def to_dict(self) -> dict[str, str]:
        """Serialize this row to a JSON-compatible dictionary."""
        return {
            "variable": self.variable,
            "source": self.source,
            "availability": self.availability.value,
        }


# The plan-IR projection. The sources named here are the ones the E4 design records; five
# variables have no runtime source today, and the availability column says so rather than
# hiding it.
PLAN_PROJECTION: tuple[ProjectionSource, ...] = (
    ProjectionSource("step", "count of authorised or executed trace events", Availability.DERIVABLE),
    ProjectionSource(
        "unauthorised_executed",
        "an executed event whose decision is missing or does not allow",
        Availability.DERIVABLE,
    ),
    ProjectionSource(
        "terminated",
        "a terminal event (outcome complete or incomplete)",
        Availability.DERIVABLE,
    ),
    ProjectionSource(
        "authority_set",
        "size of the principal set in the event context",
        Availability.DERIVABLE,
    ),
    ProjectionSource(
        "context_narrowed",
        "a continuation event whose context is a strict subset of its parent",
        Availability.NEEDS_PARENT_LINK,
    ),
    ProjectionSource(
        "continuation_seen",
        "a continuation patch was seen",
        Availability.NEEDS_NODE_ID,
    ),
    ProjectionSource(
        "delegation_consumed",
        "the plan delegation node ran",
        Availability.NEEDS_NODE_ID,
    ),
    ProjectionSource(
        "delegation_authority_gained",
        "the plan delegation node ran",
        Availability.NEEDS_NODE_ID,
    ),
    ProjectionSource("goal_reached", "the plan goal node completed", Availability.NEEDS_NODE_ID),
    ProjectionSource("safe_abort", "the plan abort node ran", Availability.NEEDS_NODE_ID),
    ProjectionSource(
        "revocation_received",
        "a revocation event happened",
        Availability.NO_RUNTIME_EVENT,
    ),
    ProjectionSource(
        "capability_violated",
        "an executed code effect outside its declared envelope",
        Availability.NO_EFFECT_SUMMARY,
    ),
)

DEFAULT_EXERCISE = "any_event"

# Which runtime fact exercises an invariant. An invariant whose fact never arrives is
# ``not_exercised``: the check ran on a run that did not ask it a question.
EXERCISE_TABLE: dict[str, str] = {
    "no-unauthorised-execution": "executed_event",
    "capability-envelope-preserved": "code_effect",
    "delegation-authority-requires-grant": "delegation_event",
    "revocation-propagation": "revocation_event",
    "bounded-progress": "step",
    "bounded-liveness": "step",
    "goal-reached-clean": "goal_event",
    "safe-abort-clean": "abort_event",
}

EXERCISE_REASON: dict[str, str] = {
    "executed_event": "no executed event was observed",
    "step": "no step was observed",
    "any_event": "no event was observed",
    "code_effect": "the trace carries no effect summary, so a code effect cannot be observed",
    "delegation_event": "the trace carries no plan node id, so a delegation node cannot be observed",
    "revocation_event": "the trace has no revocation event type",
    "goal_event": "the trace carries no plan node id, so a goal node cannot be observed",
    "abort_event": "the trace carries no plan node id, so an abort node cannot be observed",
}


class MonitorVerdict(StrEnum):
    """Verdict of one invariant on an observed trace.

    The values match ``conflux.ites.state.AssessmentVerdict``; a test pins the agreement so the two
    enums cannot drift. ``NOT_EXERCISED`` is deliberately not a pass.
    """

    HOLDS = "holds"
    BROKEN = "broken"
    NOT_EXERCISED = "not_exercised"


@dataclass(frozen=True, slots=True)
class MonitorSpec:
    """A monitor emitted from one IR: fingerprint, invariants, projection and bound."""

    ir_id: str
    ir_fingerprint: str
    bound: int
    invariants: tuple[SafetyInvariant, ...]
    projection: tuple[ProjectionSource, ...]

    def to_dict(self) -> dict[str, object]:
        """Serialize this monitor to a JSON-compatible dictionary."""
        return {
            "ir_id": self.ir_id,
            "ir_fingerprint": self.ir_fingerprint,
            "bound": self.bound,
            "invariants": [invariant.to_dict() for invariant in self.invariants],
            "projection": [row.to_dict() for row in self.projection],
        }


def emit_monitor(
    ir: VerificationIR,
    *,
    projection: tuple[ProjectionSource, ...] | None = None,
) -> MonitorSpec:
    """Emit a runtime monitor from a verification IR.

    The projection defaults to ``PLAN_PROJECTION``, which names the runtime source of every plan-IR
    variable. An IR with other variables is still emitted; an invariant over a variable the
    projection does not name reports ``not_exercised`` when checked.
    """
    rows = projection if projection is not None else PLAN_PROJECTION
    return MonitorSpec(ir.id, ir.fingerprint, ir.bound, tuple(ir.invariants), tuple(rows))


@dataclass(frozen=True, slots=True)
class MonitorEvent:
    """The runtime facts one trace event supplies, in the shape the projection needs.

    These are exactly the facts a runtime trace carries today; the adapter from a real trace is a
    later change set, not this one.
    """

    sequence: int
    outcome: str
    decision_present: bool = True
    decision_allowed: bool | None = None
    certificate_present: bool = False
    context_principals: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize this event to a JSON-compatible dictionary."""
        return {
            "sequence": self.sequence,
            "outcome": self.outcome,
            "decision_present": self.decision_present,
            "decision_allowed": self.decision_allowed,
            "certificate_present": self.certificate_present,
            "context_principals": self.context_principals,
        }


@dataclass(frozen=True, slots=True)
class InvariantOutcome:
    """The monitor verdict for one invariant, with its evidence."""

    invariant_id: str
    verdict: MonitorVerdict
    details: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize this outcome to a JSON-compatible dictionary."""
        return {
            "invariant_id": self.invariant_id,
            "verdict": self.verdict.value,
            "details": self.details,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class MonitorReport:
    """The monitor report on one observed trace."""

    ir_id: str
    ir_fingerprint: str
    bound: int
    observed_steps: int
    bound_reached: bool
    outcomes: tuple[InvariantOutcome, ...]

    def tally(self) -> dict[str, int]:
        """Return the count of each verdict."""
        counts = {verdict.value: 0 for verdict in MonitorVerdict}
        for outcome in self.outcomes:
            counts[outcome.verdict.value] += 1
        return counts

    def to_dict(self) -> dict[str, object]:
        """Serialize this report to a JSON-compatible dictionary."""
        return {
            "ir_id": self.ir_id,
            "ir_fingerprint": self.ir_fingerprint,
            "bound": self.bound,
            "observed_steps": self.observed_steps,
            "bound_reached": self.bound_reached,
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "tally": self.tally(),
        }


def project(spec: MonitorSpec, events: Sequence[MonitorEvent]) -> dict[str, IRValue | None]:
    """Project trace events onto IR variables; ``None`` means the trace cannot supply the value."""
    state: dict[str, IRValue | None] = {row.variable: None for row in spec.projection}
    executed = tuple(event for event in events if event.outcome == "executed")
    state["step"] = sum(1 for event in events if event.outcome in ("authorised", "executed"))
    state["unauthorised_executed"] = any((not event.decision_present) or event.decision_allowed is False for event in executed)
    state["terminated"] = any(event.outcome in ("complete", "incomplete") for event in events)
    contexts = [event.context_principals for event in events if event.context_principals is not None]
    state["authority_set"] = max(contexts) if contexts else None
    return state


def check_monitor(spec: MonitorSpec, events: Sequence[MonitorEvent]) -> MonitorReport:
    """Check every invariant of *spec* against the projected *events*."""
    state = project(spec, events)
    steps = state.get("step")
    observed_steps = int(steps) if isinstance(steps, int) else 0
    outcomes = tuple(_check_invariant(invariant, state, events) for invariant in spec.invariants)
    return MonitorReport(
        spec.ir_id,
        spec.ir_fingerprint,
        spec.bound,
        observed_steps,
        observed_steps >= spec.bound,
        outcomes,
    )


def _check_invariant(
    invariant: SafetyInvariant,
    state: dict[str, IRValue | None],
    events: Sequence[MonitorEvent],
) -> InvariantOutcome:
    referenced = sorted(_references(invariant.expression))
    unknown = [name for name in referenced if state.get(name) is None]
    if unknown:
        return InvariantOutcome(
            invariant.id,
            MonitorVerdict.NOT_EXERCISED,
            "the trace does not supply " + ", ".join(unknown),
            tuple(f"unknown={name}" for name in unknown),
        )
    requirement = EXERCISE_TABLE.get(invariant.id, DEFAULT_EXERCISE)
    if not _exercised(requirement, state, events):
        return InvariantOutcome(
            invariant.id,
            MonitorVerdict.NOT_EXERCISED,
            EXERCISE_REASON[requirement],
            (f"events={len(events)}",),
        )
    known = {name: cast(IRValue, state[name]) for name in referenced}
    holds = bool(evaluate(invariant.expression, known))
    return InvariantOutcome(
        invariant.id,
        MonitorVerdict.HOLDS if holds else MonitorVerdict.BROKEN,
        invariant.description or "predicate evaluated on the projected state",
        (f"events={len(events)}",),
    )


def _exercised(
    requirement: str,
    state: dict[str, IRValue | None],
    events: Sequence[MonitorEvent],
) -> bool:
    if requirement == "executed_event":
        return any(event.outcome == "executed" for event in events)
    if requirement == "step":
        steps = state.get("step")
        return isinstance(steps, int) and steps > 0
    if requirement == "any_event":
        return bool(events)
    return False


def _references(expression: Expression) -> frozenset[str]:
    """Return the variable names an expression reads."""
    if expression.kind == ExpressionKind.VARIABLE:
        return frozenset({str(expression.value)})
    names: set[str] = set()
    for argument in expression.arguments:
        names |= _references(argument)
    return frozenset(names)
