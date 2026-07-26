"""Aggregation of SLED task, security, and utility statistics.

This module consumes TaskResult objects and produces compact summaries at the
task, environment, and suite levels. It is intentionally independent from trace
exploration so that it can be reused across SLED runs, benchmark adapters, and
future report generation.

The main design goal is to keep the aggregation layer stable even as the
underlying evaluator grows more sophisticated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .task_classification import SecurityOutcome, TaskFamily, UtilityOutcome
from .task_result import TaskResult
from .task_sets import RepresentativeTask


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _sum_bool(values: Iterable[bool]) -> int:
    return sum(1 for value in values if value)


@dataclass(frozen=True)
class TaskStatistics:
    """Aggregate statistics for one representative task."""

    task_id: str
    task_name: str
    task_family: TaskFamily

    total_results: int
    secure_results: int
    blocked_results: int
    violation_results: int
    incomplete_results: int

    completed_results: int
    blocked_task_results: int
    failed_task_results: int

    trace_counted: int
    task_counted: int

    max_depth_reached: int
    average_explored_steps: float | None = None

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def secure_rate(self) -> float:
        return _rate(self.secure_results, self.total_results)

    @property
    def violation_rate(self) -> float:
        return _rate(self.violation_results, self.total_results)

    @property
    def completion_rate(self) -> float:
        return _rate(self.completed_results, self.total_results)

    @property
    def blocked_rate(self) -> float:
        return _rate(self.blocked_results, self.total_results)

    @property
    def incomplete_rate(self) -> float:
        return _rate(self.incomplete_results, self.total_results)


@dataclass(frozen=True)
class EnvironmentStatistics:
    """Aggregate statistics for one environment or scenario."""

    environment_id: str
    environment_name: str
    task_results: tuple[TaskResult, ...]

    total_results: int
    total_tasks: int
    secure_results: int
    blocked_results: int
    violation_results: int
    incomplete_results: int
    completed_results: int
    failed_results: int

    max_depth_reached: int
    average_explored_steps: float | None = None

    task_statistics: tuple[TaskStatistics, ...] = field(default_factory=tuple)
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def secure_rate(self) -> float:
        return _rate(self.secure_results, self.total_results)

    @property
    def violation_rate(self) -> float:
        return _rate(self.violation_results, self.total_results)

    @property
    def completion_rate(self) -> float:
        return _rate(self.completed_results, self.total_results)

    @property
    def incomplete_rate(self) -> float:
        return _rate(self.incomplete_results, self.total_results)


@dataclass(frozen=True)
class SuiteStatistics:
    """Aggregate statistics across all environments in a suite."""

    suite_id: str
    suite_name: str
    environment_statistics: tuple[EnvironmentStatistics, ...]

    total_environments: int
    total_results: int
    secure_results: int
    blocked_results: int
    violation_results: int
    incomplete_results: int
    completed_results: int

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def secure_rate(self) -> float:
        return _rate(self.secure_results, self.total_results)

    @property
    def violation_rate(self) -> float:
        return _rate(self.violation_results, self.total_results)

    @property
    def completion_rate(self) -> float:
        return _rate(self.completed_results, self.total_results)

    @property
    def incomplete_rate(self) -> float:
        return _rate(self.incomplete_results, self.total_results)


def aggregate_task_results(
    task_id: str,
    task_name: str,
    task_family: TaskFamily,
    results: Sequence[TaskResult],
    *,
    labels: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> TaskStatistics:
    """Aggregate all results belonging to one representative task."""
    results = tuple(results)

    secure_results = _sum_bool(result.is_secure for result in results)
    blocked_results = _sum_bool(result.is_blocked for result in results)
    violation_results = _sum_bool(result.is_violation for result in results)
    incomplete_results = _sum_bool(result.is_incomplete for result in results)
    completed_results = _sum_bool(result.success for result in results)
    blocked_task_results = _sum_bool(result.blocked for result in results)
    failed_task_results = _sum_bool(
        result.utility_outcome == UtilityOutcome.TASK_FAILED for result in results
    )
    trace_counted = _sum_bool(result.trace_counted for result in results)
    task_counted = _sum_bool(result.task_counted for result in results)
    max_depth_reached = _sum_bool(result.max_depth_reached for result in results)

    explored_steps_values = [
        result.explored_steps
        for result in results
        if result.explored_steps is not None
    ]
    average_explored_steps = (
        sum(explored_steps_values) / len(explored_steps_values)
        if explored_steps_values
        else None
    )

    merged_labels = frozenset(
        label.strip().lower()
        for result in results
        for label in result.labels
        if label.strip()
    ) | frozenset(label.strip().lower() for label in labels if label.strip())

    return TaskStatistics(
        task_id=task_id,
        task_name=task_name,
        task_family=task_family,
        total_results=len(results),
        secure_results=secure_results,
        blocked_results=blocked_results,
        violation_results=violation_results,
        incomplete_results=incomplete_results,
        completed_results=completed_results,
        blocked_task_results=blocked_task_results,
        failed_task_results=failed_task_results,
        trace_counted=trace_counted,
        task_counted=task_counted,
        max_depth_reached=max_depth_reached,
        average_explored_steps=average_explored_steps,
        labels=merged_labels,
        metadata=metadata or {},
    )


def aggregate_environment_results(
    environment_id: str,
    environment_name: str,
    results: Sequence[TaskResult],
    *,
    labels: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
    representative_tasks: Sequence[RepresentativeTask] | None = None,
) -> EnvironmentStatistics:
    """Aggregate all results belonging to one environment."""
    results = tuple(results)

    by_task: dict[str, list[TaskResult]] = {}
    for result in results:
        by_task.setdefault(result.task_id, []).append(result)

    task_statistics: list[TaskStatistics] = []
    if representative_tasks is not None:
        ordered_task_ids = [task.id for task in representative_tasks]
    else:
        ordered_task_ids = sorted(by_task)

    task_lookup = {
        task.id: task
        for task in representative_tasks or ()
    }

    for task_id in ordered_task_ids:
        task_results = by_task.get(task_id, [])
        if not task_results:
            continue

        task = task_lookup.get(task_id)
        task_name = task.name if task is not None else task_results[0].task_name
        task_family = (
            task.task_family
            if task is not None and hasattr(task, "task_family")
            else task_results[0].task_family
        )

        task_statistics.append(
            aggregate_task_results(
                task_id=task_id,
                task_name=task_name,
                task_family=task_family,
                results=task_results,
                labels=task.labels if task is not None else (),
                metadata=getattr(task, "metadata", None) or {},
            )
        )

    secure_results = _sum_bool(result.is_secure for result in results)
    blocked_results = _sum_bool(result.is_blocked for result in results)
    violation_results = _sum_bool(result.is_violation for result in results)
    incomplete_results = _sum_bool(result.is_incomplete for result in results)
    completed_results = _sum_bool(result.success for result in results)
    failed_results = _sum_bool(
        result.utility_outcome == UtilityOutcome.TASK_FAILED for result in results
    )
    max_depth_reached = _sum_bool(result.max_depth_reached for result in results)

    explored_steps_values = [
        result.explored_steps
        for result in results
        if result.explored_steps is not None
    ]
    average_explored_steps = (
        sum(explored_steps_values) / len(explored_steps_values)
        if explored_steps_values
        else None
    )

    merged_labels = frozenset(
        label.strip().lower()
        for result in results
        for label in result.labels
        if label.strip()
    ) | frozenset(label.strip().lower() for label in labels if label.strip())

    return EnvironmentStatistics(
        environment_id=environment_id,
        environment_name=environment_name,
        task_results=results,
        total_results=len(results),
        total_tasks=len(task_statistics),
        secure_results=secure_results,
        blocked_results=blocked_results,
        violation_results=violation_results,
        incomplete_results=incomplete_results,
        completed_results=completed_results,
        failed_results=failed_results,
        max_depth_reached=max_depth_reached,
        average_explored_steps=average_explored_steps,
        task_statistics=tuple(task_statistics),
        labels=merged_labels,
        metadata=metadata or {},
    )


def aggregate_suite_results(
    suite_id: str,
    suite_name: str,
    environment_statistics: Sequence[EnvironmentStatistics],
    *,
    labels: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> SuiteStatistics:
    """Aggregate statistics across a whole suite of environments."""
    environment_statistics = tuple(environment_statistics)

    total_results = sum(env.total_results for env in environment_statistics)
    secure_results = sum(env.secure_results for env in environment_statistics)
    blocked_results = sum(env.blocked_results for env in environment_statistics)
    violation_results = sum(env.violation_results for env in environment_statistics)
    incomplete_results = sum(env.incomplete_results for env in environment_statistics)
    completed_results = sum(env.completed_results for env in environment_statistics)

    merged_labels = frozenset(
        label.strip().lower()
        for env in environment_statistics
        for label in env.labels
        if label.strip()
    ) | frozenset(label.strip().lower() for label in labels if label.strip())

    return SuiteStatistics(
        suite_id=suite_id,
        suite_name=suite_name,
        environment_statistics=environment_statistics,
        total_environments=len(environment_statistics),
        total_results=total_results,
        secure_results=secure_results,
        blocked_results=blocked_results,
        violation_results=violation_results,
        incomplete_results=incomplete_results,
        completed_results=completed_results,
        labels=merged_labels,
        metadata=metadata or {},
    )


def count_task_families(
    results: Sequence[TaskResult],
) -> dict[TaskFamily, int]:
    """Count task results by family."""
    counts: dict[TaskFamily, int] = {}
    for result in results:
        counts[result.task_family] = counts.get(result.task_family, 0) + 1
    return counts


def count_security_outcomes(
    results: Sequence[TaskResult],
) -> dict[SecurityOutcome, int]:
    """Count task results by security outcome."""
    counts: dict[SecurityOutcome, int] = {}
    for result in results:
        counts[result.security_outcome] = counts.get(result.security_outcome, 0) + 1
    return counts


def count_utility_outcomes(
    results: Sequence[TaskResult],
) -> dict[UtilityOutcome, int]:
    """Count task results by utility outcome."""
    counts: dict[UtilityOutcome, int] = {}
    for result in results:
        counts[result.utility_outcome] = counts.get(result.utility_outcome, 0) + 1
    return counts
