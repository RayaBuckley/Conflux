"""End-to-end evaluation driver for SLED.

This module ties together:

- environment suites,
- trace exploration,
- trace classification,
- task result construction,
- statistical aggregation, and
- final reporting.

It intentionally does not implement trace exploration itself. Instead, callers
provide an exploration callback that yields raw traces for each environment.
That keeps the orchestration layer reusable across:

- the built-in SLED evaluator,
- benchmark adapters,
- weaker defence baselines,
- future policy backends.

The expected pipeline is:

    environment -> raw traces -> classification -> task results -> statistics -> report
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence

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


class TraceExplorer(Protocol):
    """Protocol for raw trace generation.

    The explorer receives an environment scenario and optional defence object,
    then yields raw trace objects. The trace objects may be dictionaries,
    dataclass instances, or any duck-typed structure understood by the trace
    classifier and task-result layer.
    """

    def __call__(
        self,
        scenario: EnvironmentScenario,
        defence: Any | None = None,
    ) -> Sequence[Any]:
        ...


@dataclass(frozen=True)
class EvaluationConfig:
    """Configuration for a SLED evaluation run."""

    suite_id: str
    suite_name: str
    description: str = ""

    max_traces_per_environment: int | None = None
    include_incomplete: bool = True
    include_blocked: bool = True
    include_violations: bool = True

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvironmentEvaluation:
    """Results from evaluating one environment scenario."""

    scenario: EnvironmentScenario
    raw_traces: tuple[Any, ...]
    classifications: tuple[TraceClassification, ...]
    task_results: tuple[TaskResult, ...]
    statistics: EnvironmentStatistics
    report: EnvironmentReport

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SuiteEvaluation:
    """Results from evaluating an entire suite."""

    config: EvaluationConfig
    environment_evaluations: tuple[EnvironmentEvaluation, ...]
    statistics: SuiteStatistics
    report: SuiteReport

    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialise the evaluation result into a JSON-friendly dictionary."""
        return {
            "config": {
                "suite_id": self.config.suite_id,
                "suite_name": self.config.suite_name,
                "description": self.config.description,
                "max_traces_per_environment": self.config.max_traces_per_environment,
                "include_incomplete": self.config.include_incomplete,
                "include_blocked": self.config.include_blocked,
                "include_violations": self.config.include_violations,
                "labels": sorted(self.config.labels),
                "metadata": dict(self.config.metadata),
            },
            "generated_at": self.generated_at.isoformat(),
            "statistics": self.report.to_dict(),
            "environments": [
                {
                    "environment_id": env.scenario.id,
                    "environment_name": env.scenario.name,
                    "description": env.scenario.description,
                    "kind": env.scenario.kind.value,
                    "task_ids": env.scenario.task_ids,
                    "report": env.report.to_dict(),
                    "metadata": dict(env.metadata),
                }
                for env in self.environment_evaluations
            ],
        }


def _apply_environment_filters(
    scenario: EnvironmentScenario,
    *,
    max_traces_per_environment: int | None = None,
) -> EnvironmentScenario:
    """Return a scenario adjusted for the current evaluation configuration."""
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


def evaluate_environment(
    scenario: EnvironmentScenario,
    explorer: TraceExplorer,
    *,
    defence: Any | None = None,
    classifier: Any = DEFAULT_TRACE_CLASSIFIER,
    representative_tasks: Sequence[RepresentativeTask] | None = None,
    config: EvaluationConfig | None = None,
) -> EnvironmentEvaluation:
    """Evaluate one environment scenario and return structured results."""
    traces = tuple(explorer(scenario, defence))
    if scenario.max_traces is not None:
        traces = traces[: scenario.max_traces]

    classifications: list[TraceClassification] = []
    task_results: list[TaskResult] = []

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
        },
        representative_tasks=representative_tasks,
    )
    env_report = environment_report_from_statistics(env_stats)

    return EnvironmentEvaluation(
        scenario=scenario,
        raw_traces=traces,
        classifications=tuple(classifications),
        task_results=tuple(task_results),
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
    classifier: Any = DEFAULT_TRACE_CLASSIFIER,
    config: EvaluationConfig | None = None,
) -> SuiteEvaluation:
    """Evaluate an entire suite of environments."""
    if config is None:
        config = EvaluationConfig(
            suite_id=suite.id,
            suite_name=suite.name,
            description=suite.description,
            labels=suite.labels,
            metadata=suite.metadata,
        )

    environment_evaluations: list[EnvironmentEvaluation] = []
    for scenario in iter_environment_scenarios(suite):
        adjusted = _apply_environment_filters(
            scenario,
            max_traces_per_environment=config.max_traces_per_environment,
        )
        env_eval = evaluate_environment(
            adjusted,
            explorer,
            defence=defence,
            classifier=classifier,
            representative_tasks=adjusted.tasks,
            config=config,
        )
        environment_evaluations.append(env_eval)

    suite_stats = aggregate_suite_results(
        config.suite_id,
        config.suite_name,
        [env.statistics for env in environment_evaluations],
        labels=config.labels,
        metadata=config.metadata,
    )
    suite_report = suite_report_from_statistics(suite_stats)

    return SuiteEvaluation(
        config=config,
        environment_evaluations=tuple(environment_evaluations),
        statistics=suite_stats,
        report=suite_report,
    )


def evaluate_scenarios(
    scenarios: Sequence[EnvironmentScenario],
    explorer: TraceExplorer,
    *,
    suite_id: str = "custom_suite",
    suite_name: str = "Custom suite",
    description: str = "A suite constructed from an explicit list of scenarios.",
    defence: Any | None = None,
    classifier: Any = DEFAULT_TRACE_CLASSIFIER,
    labels: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SuiteEvaluation:
    """Evaluate an explicit list of scenarios without building a named suite."""
    suite = EnvironmentSuite(
        id=suite_id,
        name=suite_name,
        description=description,
        scenarios=tuple(scenarios),
        labels=frozenset(labels or ()),
        metadata=metadata or {},
    )
    config = EvaluationConfig(
        suite_id=suite_id,
        suite_name=suite_name,
        description=description,
        labels=frozenset(labels or ()),
        metadata=metadata or {},
    )
    return evaluate_suite(
        suite,
        explorer,
        defence=defence,
        classifier=classifier,
        config=config,
    )


def _include_result(result: TaskResult, *, config: EvaluationConfig | None) -> bool:
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


def _infer_explored_steps(trace: Any) -> int | None:
    """Best-effort extraction of explored step count from a trace object."""
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
    """Best-effort extraction of max-depth information from a trace object."""
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


def _extract(obj: Any, key: str) -> Any:
    """Extract a value from either a mapping or an attribute-bearing object."""
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)
