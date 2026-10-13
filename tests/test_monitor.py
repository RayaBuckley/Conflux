"""Tests for the runtime monitor emitted from a verification IR (E4: one IR, two artifacts).

The monitor is additive: ``emit_monitor`` reads an IR and returns a spec, and ``check_monitor``
reports one of ``holds``, ``broken`` or ``not_exercised`` per invariant. An invariant the trace
cannot exercise is never reported as holding - that is the vacuity E7 measured.
"""

from __future__ import annotations

import pytest

from conflux.domain import WRITE, Principal, Provenance
from conflux.ites.state import AssessmentVerdict
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    LiteralBinding,
    OperationCatalogue,
    OperationSchema,
    Plan,
    TemplateArgument,
)
from conflux.verification import (
    PLAN_PROJECTION,
    EffectSummary,
    InvariantOutcome,
    MonitorEvent,
    MonitorReport,
    MonitorVerdict,
    VerificationIR,
    abstract_plan,
    check_monitor,
    emit_monitor,
)

pytestmark = pytest.mark.security


def _plan_ir() -> VerificationIR:
    """A minimal supported plan IR with one action node."""
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="fixture")
    operation = OperationSchema(
        "filesystem.write",
        "1",
        "filesystem",
        "file",
        "write",
        WRITE,
        (
            ArgumentSpec("path", ArgumentType.STRING),
            ArgumentSpec("content", ArgumentType.STRING),
        ),
        "path",
    )
    action = ActionTemplateNode(
        "write",
        ActionTemplate(
            "write",
            operation.id,
            operation.version,
            (
                TemplateArgument("path", LiteralBinding("safe.txt", source)),
                TemplateArgument("content", LiteralBinding("safe", source)),
            ),
        ),
        source,
    )
    plan = Plan("monitor-fixture", "repair", (action,), source)
    abstraction = abstract_plan(
        plan,
        catalogue=OperationCatalogue((operation,)),
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )
    assert abstraction.supported
    assert abstraction.ir is not None
    return abstraction.ir


def _outcome(
    ir: VerificationIR,
    events: tuple[MonitorEvent, ...],
    invariant_id: str,
) -> tuple[MonitorReport, InvariantOutcome]:
    report = check_monitor(emit_monitor(ir), events)
    by_id = {outcome.invariant_id: outcome for outcome in report.outcomes}
    return report, by_id[invariant_id]


def test_projection_names_every_plan_ir_variable() -> None:
    ir = _plan_ir()
    rows = {row.variable for row in PLAN_PROJECTION}
    assert {variable.name for variable in ir.variables} <= rows


def test_projection_rows_are_unique() -> None:
    variables = [row.variable for row in PLAN_PROJECTION]
    assert len(set(variables)) == len(variables)


def test_emitter_records_the_ir_it_came_from() -> None:
    ir = _plan_ir()
    spec = emit_monitor(ir)
    assert spec.ir_fingerprint == ir.fingerprint
    assert spec.bound == ir.bound
    assert {invariant.id for invariant in spec.invariants} == {invariant.id for invariant in ir.invariants}


def test_quiet_run_is_not_exercised_not_holds() -> None:
    ir = _plan_ir()
    events = (
        MonitorEvent(0, "proposed"),
        MonitorEvent(1, "blocked", decision_allowed=False),
    )
    _, outcome = _outcome(ir, events, "no-unauthorised-execution")
    assert outcome.verdict is MonitorVerdict.NOT_EXERCISED


def test_executed_event_without_a_decision_is_broken() -> None:
    ir = _plan_ir()
    events = (MonitorEvent(0, "executed", decision_present=False),)
    _, outcome = _outcome(ir, events, "no-unauthorised-execution")
    assert outcome.verdict is MonitorVerdict.BROKEN


def test_executed_event_with_a_disallowing_decision_is_broken() -> None:
    ir = _plan_ir()
    events = (MonitorEvent(0, "executed", decision_present=True, decision_allowed=False),)
    _, outcome = _outcome(ir, events, "no-unauthorised-execution")
    assert outcome.verdict is MonitorVerdict.BROKEN


def test_executed_event_with_an_allowing_decision_holds() -> None:
    ir = _plan_ir()
    events = (MonitorEvent(0, "executed", decision_present=True, decision_allowed=True),)
    _, outcome = _outcome(ir, events, "no-unauthorised-execution")
    assert outcome.verdict is MonitorVerdict.HOLDS


def test_blocked_variable_reports_not_exercised_not_holds() -> None:
    ir = _plan_ir()
    events = (MonitorEvent(0, "executed", decision_allowed=True),)
    _, outcome = _outcome(ir, events, "capability-envelope-preserved")
    assert outcome.verdict is MonitorVerdict.NOT_EXERCISED
    assert "capability_violated" in outcome.details


def test_bound_reached_is_reported_as_a_fact() -> None:
    ir = _plan_ir()
    below = tuple(MonitorEvent(i, "authorised", decision_allowed=True) for i in range(ir.bound - 1))
    at_bound = tuple(MonitorEvent(i, "authorised", decision_allowed=True) for i in range(ir.bound))
    assert check_monitor(emit_monitor(ir), below).bound_reached is False
    report = check_monitor(emit_monitor(ir), at_bound)
    assert report.bound_reached is True
    assert report.observed_steps == ir.bound


def test_monitor_verdicts_match_the_ites_assessment_verdicts() -> None:
    assert {verdict.value for verdict in MonitorVerdict} == {verdict.value for verdict in AssessmentVerdict}


def test_report_serialises_with_a_verdict_tally() -> None:
    ir = _plan_ir()
    report = check_monitor(emit_monitor(ir), (MonitorEvent(0, "proposed"),))
    payload = report.to_dict()
    assert payload["ir_fingerprint"] == ir.fingerprint
    tally = payload["tally"]
    assert isinstance(tally, dict)
    assert tally["not_exercised"] >= 1
