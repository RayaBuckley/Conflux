"""Defence-centric evaluation orchestration for SLED.

This module runs a single defence, or a collection of defences, over a suite of
environments. It connects:

- environment scenarios,
- a trace explorer,
- trace classification,
- task-level results,
- counterexample extraction,
- and aggregated statistics.

The intent is to support comparisons between ITES and weaker baselines, while
also leaving room for simulated model internals and real model-backed runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence

from .counterexample import (
    Counterexample,
    CounterexampleKind,
    CounterexampleSet,
    CounterexampleWitness,
    make_counterexample,
)
from .environment_suite import EnvironmentScenario, EnvironmentSuite, iter_environment_scenarios
from .reporting import (
    EnvironmentReport,
    SuiteReport,
    environment_report_from_statistics,
    suite_report_from_statistics,
)
from .statistics import (
    EnvironmentStatistics,
    SuiteStatistics,
    aggregate_environment_results,
    aggregate_suite_results,
)
from .task_classification import DEFAULT_TRACE_CLASSIFIER, TraceClassification
from .task_result import TaskResult
from .task_sets import RepresentativeTask
from .trace import ExecutionTrace, TraceContext, TraceEvent, TraceEventKind, TraceKind


class TraceExplorer(Protocol):
    """Protocol for trace generation.

    An explorer receives an environment scenario and a defence, then returns a
    sequence of raw traces. The raw traces may be ExecutionTrace instances or
    duck-typed objects that expose the same security-relevant fields.
    """

    def __call__(
        self,
        scenario: EnvironmentScenario,
        defence: Any | None = None,
    ) -> Sequence[Any]:
        ...


@dataclass(frozen=True)
class DefenceEvaluationConfig:
    """Configuration for one defence evaluation run."""

    suite_id: str
    suite_name: str
    defence_name: str
    description: str = ""

    max_traces_per_environment: int | None = None
    include_incomplete: bool = True
    include_blocked: bool = True
    include_violations: bool = True

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioEvaluation:
    """Results from evaluating one scenario under one defence."""

    scenario: EnvironmentScenario
    defence_name: str

    raw_traces: tuple[Any, ...]
    classifications: tuple[TraceClassification, ...]
    task_results: tuple[TaskResult, ...]
    counterexamples: tuple[Counterexample, ...]

    statistics: EnvironmentStatistics
    report: EnvironmentReport

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DefenceSuiteEvaluation:
    """Results from evaluating a defence across an entire suite."""

    config: DefenceEvaluationConfig
    scenario_evaluations: tuple[ScenarioEvaluation, ...]
    statistics: SuiteStatistics
    report: SuiteReport
    counterexample_sets: tuple[CounterexampleSet, ...] = field(default_factory=tuple)

    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialise the evaluation into a JSON-friendly structure."""
        return {
            "config": {
                "suite_id": self.config.suite_id,
                "suite_name": self.config.suite_name,
                "defence_name": self.config.defence_name,
                "description": self.config.description,
                "max_traces_per_environment": self.config.max_traces_per_environment,
                "include_incomplete": self.config.include_incomplete,
                "include_blocked": self.config.include_blocked,
                "include_violations": self.config.include_violations,
                "labels": sorted(self.config.labels),
                "metadata": dict(self.config.metadata),
            },
            "generated_at": self.generated_at.isoformat(),
            "report": self.report.to_dict(),
            "scenario_evaluations": [
                {
                    "environment_id": evaluation.scenario.id,
                    "environment_name": evaluation.scenario.name,
                    "description": evaluation.scenario.description,
                    "kind": evaluation.scenario.kind.value,
                    "task_ids": evaluation.scenario.task_ids,
                    "defence_name": evaluation.defence_name,
                    "report": evaluation.report.to_dict(),
                    "counterexamples": [item.to_dict() for item in evaluation.counterexamples],
                    "metadata": dict(evaluation.metadata),
                }
                for evaluation in self.scenario_evaluations
            ],
            "counterexample_sets": [item.to_dict() for item in self.counterexample_sets],
        }


@dataclass(frozen=True)
class DefenceComparison:
    """Comparison across multiple defences for the same suite."""

    suite_id: str
    suite_name: str
    evaluations: tuple[DefenceSuiteEvaluation, ...]

    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "generated_at": self.generated_at.isoformat(),
            "evaluations": [evaluation.to_dict() for evaluation in self.evaluations],
        }


def evaluate_scenario(
    scenario: EnvironmentScenario,
    explorer: TraceExplorer,
    *,
    defence: Any | None = None,
    defence_name: str | None = None,
    classifier: Any = DEFAULT_TRACE_CLASSIFIER,
    representative_tasks: Sequence[RepresentativeTask] | None = None,
    config: DefenceEvaluationConfig | None = None,
) -> ScenarioEvaluation:
    """Evaluate one scenario under one defence."""
    traces = tuple(explorer(scenario, defence))
    if config is not None and config.max_traces_per_environment is not None:
        traces = traces[: config.max_traces_per_environment]

    classifications: list[TraceClassification] = []
    task_results: list[TaskResult] = []
    counterexamples: list[Counterexample] = []

    resolved_defence_name: str = str(defence_name or getattr(defence, "name", "unknown"))

    for trace in traces:
        classification = classifier.classify(trace)
        classifications.append(classification)

        result = TaskResult.from_classification(
            classification,
            task=None,
            explored_steps=_infer_explored_steps(trace),
            max_depth_reached=_infer_max_depth_reached(trace),
            metadata=_infer_trace_metadata(trace),
        )

        if not _include_result(result, config=config):
            continue

        task_results.append(result)

        counterexample = _maybe_make_counterexample(
            trace=trace,
            classification=classification,
            result=result,
            defence_name=resolved_defence_name,
        )
        if counterexample is not None:
            counterexamples.append(counterexample)

    env_stats = aggregate_environment_results(
        scenario.id,
        scenario.name,
        task_results,
        labels=scenario.labels,
        metadata={
            **dict(scenario.metadata),
            "access_control_backend": scenario.access_control_backend,
            "policy_profile": scenario.policy_profile,
            "kind": scenario.kind.value,
            "max_depth": scenario.max_depth,
            "max_traces": scenario.max_traces,
            "defence_name": resolved_defence_name,
        },
        representative_tasks=representative_tasks,
    )
    env_report = environment_report_from_statistics(env_stats)

    return ScenarioEvaluation(
        scenario=scenario,
        defence_name=resolved_defence_name,
        raw_traces=traces,
        classifications=tuple(classifications),
        task_results=tuple(task_results),
        counterexamples=tuple(counterexamples),
        statistics=env_stats,
        report=env_report,
        labels=scenario.labels,
        metadata=scenario.metadata,
    )


def evaluate_suite(
    suite: EnvironmentSuite,
    explorer: TraceExplorer,
    *,
    defence: Any | None = None,
    defence_name: str | None = None,
    classifier: Any = DEFAULT_TRACE_CLASSIFIER,
    config: DefenceEvaluationConfig | None = None,
) -> DefenceSuiteEvaluation:
    """Evaluate one defence across a whole suite of scenarios."""
    if config is None:
        config = DefenceEvaluationConfig(
            suite_id=suite.id,
            suite_name=suite.name,
            defence_name=str(defence_name or getattr(defence, "name", "unknown")),
            description=suite.description,
            labels=suite.labels,
            metadata=suite.metadata,
        )

    scenario_evaluations: list[ScenarioEvaluation] = []
    for scenario in iter_environment_scenarios(suite):
        adjusted = _apply_environment_filters(
            scenario,
            max_traces_per_environment=config.max_traces_per_environment,
        )
        evaluation = evaluate_scenario(
            adjusted,
            explorer,
            defence=defence,
            defence_name=config.defence_name,
            classifier=classifier,
            representative_tasks=adjusted.tasks,
            config=config,
        )
        scenario_evaluations.append(evaluation)

    suite_stats = aggregate_suite_results(
        config.suite_id,
        config.suite_name,
        [evaluation.statistics for evaluation in scenario_evaluations],
        labels=config.labels,
        metadata=config.metadata,
    )
    suite_report = suite_report_from_statistics(suite_stats)

    counterexample_sets = tuple(
        CounterexampleSet(
            run_id=f"{config.suite_id}:{evaluation.scenario.id}:{config.defence_name}",
            environment_name=evaluation.scenario.name,
            defence_name=config.defence_name,
            kind=_dominant_counterexample_kind(evaluation.counterexamples),
            counterexamples=evaluation.counterexamples,
            labels=evaluation.labels,
            metadata=evaluation.metadata,
        )
        for evaluation in scenario_evaluations
        if evaluation.counterexamples
    )

    return DefenceSuiteEvaluation(
        config=config,
        scenario_evaluations=tuple(scenario_evaluations),
        statistics=suite_stats,
        report=suite_report,
        counterexample_sets=counterexample_sets,
    )


def evaluate_defences(
    suite: EnvironmentSuite,
    explorer: TraceExplorer,
    defences: Sequence[Any],
    *,
    classifier: Any = DEFAULT_TRACE_CLASSIFIER,
    suite_id: str | None = None,
    suite_name: str | None = None,
    description: str = "",
    labels: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DefenceComparison:
    """Evaluate multiple defences over the same suite."""
    evaluations: list[DefenceSuiteEvaluation] = []

    for defence in defences:
        defence_name = getattr(defence, "name", "unknown")
        config = DefenceEvaluationConfig(
            suite_id=suite_id or suite.id,
            suite_name=suite_name or suite.name,
            defence_name=defence_name,
            description=description or suite.description,
            labels=frozenset(labels or suite.labels),
            metadata=metadata or suite.metadata,
        )
        evaluation = evaluate_suite(
            suite,
            explorer,
            defence=defence,
            defence_name=defence_name,
            classifier=classifier,
            config=config,
        )
        evaluations.append(evaluation)

    return DefenceComparison(
        suite_id=suite_id or suite.id,
        suite_name=suite_name or suite.name,
        evaluations=tuple(evaluations),
    )


def evaluate_selected_scenarios(
    scenarios: Sequence[EnvironmentScenario],
    explorer: TraceExplorer,
    *,
    suite_id: str = "custom_suite",
    suite_name: str = "Custom suite",
    description: str = "A suite built from an explicit list of scenarios.",
    defence: Any | None = None,
    defence_name: str | None = None,
    classifier: Any = DEFAULT_TRACE_CLASSIFIER,
    labels: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DefenceSuiteEvaluation:
    """Evaluate an explicit set of scenarios without constructing a named suite."""
    suite = EnvironmentSuite(
        id=suite_id,
        name=suite_name,
        description=description,
        scenarios=tuple(scenarios),
        labels=frozenset(labels or ()),
        metadata=metadata or {},
    )
    return evaluate_suite(
        suite,
        explorer,
        defence=defence,
        defence_name=defence_name,
        classifier=classifier,
        config=DefenceEvaluationConfig(
            suite_id=suite_id,
            suite_name=suite_name,
            defence_name=str(defence_name or getattr(defence, "name", "unknown")),
            description=description,
            labels=frozenset(labels or ()),
            metadata=metadata or {},
        ),
    )


def _include_result(result: TaskResult, *, config: DefenceEvaluationConfig | None) -> bool:
    """Apply coarse filtering rules to a task result."""
    if config is None:
        return True

    if not config.include_incomplete and result.incomplete:
        return False
    if not config.include_blocked and result.blocked:
        return False
    if not config.include_violations and result.violation:
        return False
    return True


def _apply_environment_filters(
    scenario: EnvironmentScenario,
    *,
    max_traces_per_environment: int | None = None,
) -> EnvironmentScenario:
    """Return a scenario adjusted for the current configuration."""
    if max_traces_per_environment is None:
        return scenario
    if scenario.max_traces == max_traces_per_environment:
        return scenario
    return EnvironmentScenario(
        id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        kind=scenario.kind,
        task_ids=scenario.task_ids,
        principals=scenario.principals,
        data_items=scenario.data_items,
        tools=scenario.tools,
        access_control_backend=scenario.access_control_backend,
        policy_profile=scenario.policy_profile,
        max_depth=scenario.max_depth,
        max_traces=max_traces_per_environment,
        labels=scenario.labels,
        metadata=scenario.metadata,
    )


def _infer_explored_steps(trace: Any) -> int | None:
    """Best-effort extraction of a step count."""
    for key in ("explored_steps", "num_steps", "steps_taken", "step_count", "depth"):
        value = _extract(trace, key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _infer_max_depth_reached(trace: Any) -> bool:
    """Best-effort extraction of a depth-bound signal."""
    for key in ("max_depth_reached", "depth_bound_reached", "truncated", "incomplete"):
        value = _extract(trace, key)
        if isinstance(value, bool):
            return value
        if value is not None:
            text = str(value).strip().lower()
            if text in {"1", "true", "yes", "y", "on"}:
                return True
    return False


def _infer_trace_metadata(trace: Any) -> dict[str, Any]:
    """Best-effort extraction of trace metadata."""
    metadata = _extract(trace, "metadata")
    if isinstance(metadata, Mapping):
        return dict(metadata)

    extras: dict[str, Any] = {}
    for key in (
        "trace_id",
        "id",
        "task_name",
        "task",
        "environment_name",
        "environment",
        "scenario",
        "labels",
        "tags",
        "reason",
    ):
        value = _extract(trace, key)
        if value is not None:
            extras[key] = value
    return extras


def _maybe_make_counterexample(
    *,
    trace: Any,
    classification: TraceClassification,
    result: TaskResult,
    defence_name: str,
) -> Counterexample | None:
    """Construct a counterexample when a trace appears to violate security."""
    if not (result.violation or classification.security_outcome.value == "violation"):
        return None

    execution_trace = _coerce_execution_trace(trace, defence_name=defence_name, result=result)
    offending = _first_offending_event(execution_trace)
    witness = CounterexampleWitness(
        event_id=None if offending is None else offending.id,
        event=offending,
        description="First security-relevant offending event discovered in the trace.",
        labels=frozenset({"security_violation"}),
    )

    counterexample_id = f"{result.trace_id or execution_trace.trace_id}:counterexample"
    return make_counterexample(
        counterexample_id=counterexample_id,
        trace=execution_trace,
        kind=_counterexample_kind_from_classification(classification),
        task_name=result.task_name,
        environment_name=result.environment_name,
        defence_name=defence_name,
        blocked=result.blocked,
        complete=not result.incomplete,
        max_depth_reached=result.max_depth_reached,
        first_offending_event=offending,
        witnesses=(witness,),
        labels=tuple(sorted(set(result.labels) | {"counterexample"})),
        metadata={
            "security_outcome": classification.security_outcome.value,
            "utility_outcome": classification.utility_outcome.value,
            "reason": classification.reason,
        },
    )


def _coerce_execution_trace(trace: Any, *, defence_name: str, result: TaskResult) -> ExecutionTrace:
    """Convert a duck-typed trace into an ExecutionTrace when possible."""
    if isinstance(trace, ExecutionTrace):
        return trace

    trace_id = getattr(trace, "trace_id", None) or result.trace_id or f"{defence_name}:{result.task_id}"
    events = tuple(_coerce_events(getattr(trace, "events", None)))
    context = getattr(trace, "context", None)
    if not isinstance(context, TraceContext):
        context = TraceContext()

    kind = getattr(trace, "kind", TraceKind.UNKNOWN)
    if not isinstance(kind, TraceKind):
        kind = TraceKind.UNKNOWN

    return ExecutionTrace(
        trace_id=str(trace_id),
        kind=kind,
        context=context,
        events=events,
        task_name=getattr(trace, "task_name", None) or result.task_name,
        environment_name=getattr(trace, "environment_name", None) or result.environment_name,
        defence_name=getattr(trace, "defence_name", None) or defence_name,
        complete=bool(getattr(trace, "complete", True)),
        blocked=bool(getattr(trace, "blocked", False)),
        violation=bool(getattr(trace, "violation", result.violation)),
        max_depth_reached=bool(getattr(trace, "max_depth_reached", result.max_depth_reached)),
        labels=frozenset(getattr(trace, "labels", result.labels) or result.labels),
        metadata=getattr(trace, "metadata", {}) or {},
    )


def _coerce_events(events: Any) -> Sequence[TraceEvent]:
    """Best-effort conversion of event-like objects to TraceEvent instances."""
    if not events:
        return ()

    coerced: list[TraceEvent] = []
    for index, event in enumerate(events):
        if isinstance(event, TraceEvent):
            coerced.append(event)
            continue

        event_id = getattr(event, "id", None) or getattr(event, "event_id", None) or f"event_{index}"
        kind = getattr(event, "kind", TraceEventKind.OTHER)
        if not isinstance(kind, TraceEventKind):
            try:
                kind = TraceEventKind(str(kind))
            except Exception:
                kind = TraceEventKind.OTHER

        coerced.append(
            TraceEvent(
                id=str(event_id),
                kind=kind,
                principal=getattr(event, "principal", None),
                subject=getattr(event, "subject", None),
                action=getattr(event, "action", None),
                resource=getattr(event, "resource", None),
                input_text=getattr(event, "input_text", None),
                output_text=getattr(event, "output_text", None),
                blocked=bool(getattr(event, "blocked", False)),
                incomplete=bool(getattr(event, "incomplete", False)),
                error=getattr(event, "error", None),
                labels=frozenset(getattr(event, "labels", ()) or ()),
                metadata=getattr(event, "metadata", {}) or {},
            )
        )
    return tuple(coerced)


def _first_offending_event(trace: ExecutionTrace) -> TraceEvent | None:
    """Return the first event that looks security-relevant and problematic."""
    for event in trace.events:
        if event.blocked or event.error or event.kind in {
            TraceEventKind.WRITE,
            TraceEventKind.ACTION,
            TraceEventKind.POLICY_DECISION,
            TraceEventKind.ERROR,
        }:
            return event
    return trace.latest_event


def _counterexample_kind_from_classification(
    classification: TraceClassification,
) -> CounterexampleKind:
    """Map a trace classification to a counterexample kind."""
    value = classification.security_outcome.value
    if value == "violation":
        return CounterexampleKind.PRIVILEGE_ESCALATION
    if value == "blocked":
        return CounterexampleKind.POLICY_BYPASS
    if value == "incomplete":
        return CounterexampleKind.INCOMPLETE_BUT_SUSPICIOUS
    return CounterexampleKind.UNKNOWN


def _dominant_counterexample_kind(
    counterexamples: Sequence[Counterexample],
) -> CounterexampleKind:
    """Choose a dominant kind for a set of counterexamples."""
    if not counterexamples:
        return CounterexampleKind.UNKNOWN

    precedence = (
        CounterexampleKind.PRIVILEGE_ESCALATION,
        CounterexampleKind.INFORMATION_EXFILTRATION,
        CounterexampleKind.UNAUTHORISED_ACTION,
        CounterexampleKind.POLICY_BYPASS,
        CounterexampleKind.READ_VIOLATION,
        CounterexampleKind.WRITE_VIOLATION,
        CounterexampleKind.INCOMPLETE_BUT_SUSPICIOUS,
        CounterexampleKind.UNKNOWN,
    )
    present = {item.kind for item in counterexamples}
    for kind in precedence:
        if kind in present:
            return kind
    return CounterexampleKind.UNKNOWN


def _extract(obj: Any, key: str) -> Any:
    """Extract a value from a mapping or attribute-bearing object."""
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)
