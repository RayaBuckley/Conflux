"""
AgentDojo benchmark adapter.

This module provides a thin integration layer between the project's internal
benchmark machinery and AgentDojo-style tasks.

The implementation is intentionally generic because AgentDojo task formats can
vary across versions and runners. The adapter therefore works through a small
set of conversion hooks rather than assuming a specific upstream package
layout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Protocol, runtime_checkable

from conflux.compatibility.environment import Data, Environment
from conflux.evaluation.reporting import EvaluationSummary
from conflux.evaluation.services import ExhaustiveEvaluator
from conflux.ites import ITES

from .native import (
    NativeBenchmarkCase,
    NativeBenchmarkCaseOutcome,
    NativeBenchmarkSuite,
    build_native_case,
    build_native_suite,
    run_native_case,
    run_native_suite,
)
from .results import (
    BenchmarkCaseResult,
    BenchmarkRunMetadata,
    BenchmarkRunSummary,
    build_run_summary,
)


@runtime_checkable
class AgentDojoTaskLike(Protocol):
    """
    Minimal interface for an AgentDojo-style task object.
    """

    task_id: str
    environment: Environment
    initial_inputs: Iterable[Data]
    metadata: Mapping[str, Any]

    def primitive_actions(self) -> Iterable[str]:
        """
        Return the primitive action vocabulary for the task.
        """
        ...


@runtime_checkable
class AgentDojoSuiteLike(Protocol):
    """
    Minimal interface for an AgentDojo-style suite object.
    """

    name: str
    tasks: Iterable[AgentDojoTaskLike]
    metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class AgentDojoTask:
    """
    Concrete internal representation of an AgentDojo task.
    """

    task_id: str
    environment: Environment
    initial_inputs: tuple[Data, ...] = field(default_factory=tuple)
    primitive_actions: frozenset[str] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_inputs", tuple(self.initial_inputs))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def derived_primitive_actions(self) -> frozenset[str]:
        if self.primitive_actions is not None:
            return frozenset(self.primitive_actions)
        return frozenset(permission.name for permission in self.environment.total_actions)


@dataclass(frozen=True, slots=True)
class AgentDojoSuite:
    """
    Internal suite wrapper for AgentDojo-style tasks.
    """

    name: str
    tasks: tuple[AgentDojoTask, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tasks", tuple(self.tasks))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def case_ids(self) -> tuple[str, ...]:
        return tuple(task.task_id for task in self.tasks)


@dataclass(frozen=True, slots=True)
class AgentDojoCaseOutcome:
    """
    Result for one AgentDojo task.
    """

    task: AgentDojoTask
    native_outcome: NativeBenchmarkCaseOutcome

    @property
    def succeeded(self) -> bool:
        return self.native_outcome.succeeded

    @property
    def result(self) -> BenchmarkCaseResult:
        return self.native_outcome.result

    @property
    def summary(self) -> EvaluationSummary:
        return self.native_outcome.report_summary


@dataclass(frozen=True, slots=True)
class AgentDojoRun:
    """
    Complete run result for an AgentDojo-style benchmark suite.
    """

    suite: AgentDojoSuite
    cases: tuple[AgentDojoCaseOutcome, ...]
    summary: BenchmarkRunSummary
    metadata: BenchmarkRunMetadata

    @property
    def succeeded(self) -> bool:
        return self.summary.succeeded

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": {
                "name": self.suite.name,
                "metadata": dict(self.suite.metadata),
                "case_ids": self.suite.case_ids(),
            },
            "metadata": self.metadata.to_dict(),
            "summary": self.summary.to_dict(),
            "cases": [
                {
                    "task_id": outcome.task.task_id,
                    "succeeded": outcome.succeeded,
                    "summary": outcome.summary.to_dict(),
                    "result": outcome.result.to_dict(),
                    "metadata": dict(outcome.task.metadata),
                    "environment_name": outcome.task.environment.name,
                }
                for outcome in self.cases
            ],
        }


def _task_to_native_case(task: AgentDojoTask) -> NativeBenchmarkCase:
    """
    Convert an AgentDojo task into the project's native benchmark case type.
    """
    return build_native_case(
        task.task_id,
        task.environment,
        task.initial_inputs,
        primitive_actions=task.derived_primitive_actions(),
        metadata=task.metadata,
    )


def _suite_to_native_suite(suite: AgentDojoSuite) -> NativeBenchmarkSuite:
    """
    Convert an AgentDojo suite into a native benchmark suite.
    """
    return build_native_suite(
        suite.name,
        (_task_to_native_case(task) for task in suite.tasks),
        metadata=suite.metadata,
    )


def adapt_task_like(task: AgentDojoTaskLike) -> AgentDojoTask:
    """
    Convert a task-like upstream object into the internal AgentDojoTask.
    """
    primitive_actions = tuple(task.primitive_actions()) if hasattr(task, "primitive_actions") else ()
    return AgentDojoTask(
        task_id=task.task_id,
        environment=task.environment,
        initial_inputs=tuple(task.initial_inputs),
        primitive_actions=frozenset(primitive_actions) if primitive_actions else None,
        metadata=task.metadata,
    )


def adapt_suite_like(suite: AgentDojoSuiteLike) -> AgentDojoSuite:
    """
    Convert a suite-like upstream object into the internal AgentDojoSuite.
    """
    return AgentDojoSuite(
        name=suite.name,
        tasks=tuple(adapt_task_like(task) for task in suite.tasks),
        metadata=suite.metadata,
    )


def run_agentdojo_task(
    task: AgentDojoTask,
    *,
    defence: ITES,
    evaluator_factory: Callable[[ITES, frozenset[str]], ExhaustiveEvaluator] | None = None,
) -> AgentDojoCaseOutcome:
    """
    Run one AgentDojo task through the native benchmark pipeline.
    """
    native_case = _task_to_native_case(task)
    native_outcome = run_native_case(
        native_case,
        defence=defence,
        evaluator_factory=evaluator_factory,
    )
    return AgentDojoCaseOutcome(task=task, native_outcome=native_outcome)


def run_agentdojo_suite(
    suite: AgentDojoSuite,
    *,
    defence: ITES,
    evaluator_factory: Callable[[ITES, frozenset[str]], ExhaustiveEvaluator] | None = None,
    metadata: BenchmarkRunMetadata | None = None,
) -> AgentDojoRun:
    """
    Run a complete AgentDojo suite through the native benchmark pipeline.
    """
    native_suite = _suite_to_native_suite(suite)
    native_run = run_native_suite(
        native_suite,
        defence=defence,
        evaluator_factory=evaluator_factory,
        metadata=metadata
        or BenchmarkRunMetadata(
            benchmark_name=suite.name,
            runner_name="agentdojo",
            provider_name="agentdojo",
            extra={"suite_metadata": dict(suite.metadata)},
        ),
    )

    cases = tuple(
        AgentDojoCaseOutcome(task=task, native_outcome=outcome)
        for task, outcome in zip(suite.tasks, native_run.cases, strict=False)
    )

    summary = build_run_summary(
        suite.name,
        tuple(outcome.result for outcome in cases),
        metadata=metadata
        or BenchmarkRunMetadata(
            benchmark_name=suite.name,
            runner_name="agentdojo",
            provider_name="agentdojo",
            extra={"suite_metadata": dict(suite.metadata)},
        ),
        extra={
            "suite_metadata": dict(suite.metadata),
            "case_ids": suite.case_ids(),
        },
    )

    run_metadata = metadata or BenchmarkRunMetadata(
        benchmark_name=suite.name,
        runner_name="agentdojo",
        provider_name="agentdojo",
        extra={"suite_metadata": dict(suite.metadata)},
    )

    return AgentDojoRun(
        suite=suite,
        cases=cases,
        summary=summary,
        metadata=run_metadata,
    )


def agentdojo_to_dict(run: AgentDojoRun) -> dict[str, Any]:
    """
    Convert an AgentDojo run into a JSON-friendly dictionary.
    """
    return run.to_dict()


def make_agentdojo_task(
    task_id: str,
    environment: Environment,
    initial_inputs: Iterable[Data] = (),
    *,
    primitive_actions: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> AgentDojoTask:
    """
    Convenience helper for building an internal AgentDojo task.
    """
    return AgentDojoTask(
        task_id=task_id,
        environment=environment,
        initial_inputs=tuple(initial_inputs),
        primitive_actions=None if primitive_actions is None else frozenset(primitive_actions),
        metadata={} if metadata is None else dict(metadata),
    )


def make_agentdojo_suite(
    name: str,
    tasks: Iterable[AgentDojoTask],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> AgentDojoSuite:
    """
    Convenience helper for building an internal AgentDojo suite.
    """
    return AgentDojoSuite(
        name=name,
        tasks=tuple(tasks),
        metadata={} if metadata is None else dict(metadata),
    )


__all__ = [
    "AgentDojoCaseOutcome",
    "AgentDojoRun",
    "AgentDojoSuite",
    "AgentDojoTask",
    "adapt_suite_like",
    "adapt_task_like",
    "agentdojo_to_dict",
    "make_agentdojo_suite",
    "make_agentdojo_task",
    "run_agentdojo_suite",
    "run_agentdojo_task",
]
