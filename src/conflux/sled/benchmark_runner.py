"""
SLED benchmark runner.

This module orchestrates benchmark execution over task suites.

The benchmark runner is intentionally separate from both the defence and the
evaluation harness:
- the defence (ITES) decides what is permitted,
- the evaluator executes a defence against a scenario,
- the benchmark runner coordinates tasks, attacks, and reporting.

This is the layer that benchmark scripts should call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from conflux.ites import ITES

from .attack import Attack
from .evaluator import EvaluationResult, Evaluator
from .scenario import Scenario
from .task_suite import TaskSuite


@dataclass(frozen=True, slots=True)
class BenchmarkCaseResult:
    """
    Result of running one benchmark task.

    Attributes
    ----------
    suite_name:
        Name of the task suite.

    task_name:
        Name of the benchmark task.

    attack_name:
        Name of the applied attack, or an empty string if none was applied.

    scenario:
        The scenario that was evaluated.

    result:
        The evaluation output returned by SLED.
    """

    suite_name: str
    task_name: str
    attack_name: str = ""
    scenario: Scenario | None = None
    result: EvaluationResult | None = None


@dataclass(frozen=True, slots=True)
class BenchmarkRunResult:
    """
    Aggregate result for a benchmark suite run.

    Attributes
    ----------
    suite_name:
        Name of the suite that was executed.

    cases:
        Per-task results.

    total_tasks:
        Number of benchmark tasks processed.

    total_declared:
        Total number of declared actions across all cases.

    total_blocked:
        Total number of blocked actions across all cases.
    """

    suite_name: str
    cases: tuple[BenchmarkCaseResult, ...] = field(default_factory=tuple)
    total_tasks: int = 0
    total_declared: int = 0
    total_blocked: int = 0

    @property
    def passed_cases(self) -> int:
        """
        Count cases where every reported property held.
        """
        passed = 0
        for case in self.cases:
            if case.result is None:
                continue
            if all(guarantee.holds for guarantee in case.result.report.guarantees):
                passed += 1
        return passed

    @property
    def failed_cases(self) -> int:
        """
        Count cases where at least one reported property failed.
        """
        return self.total_tasks - self.passed_cases


@dataclass(frozen=True, slots=True)
class BenchmarkRunner:
    """
    Run a task suite against a defence.

    This class keeps the benchmark layer independent of any particular defence
    implementation or attack taxonomy.
    """

    suite: TaskSuite
    defence: ITES
    llm_call: Any

    def run(
        self,
        *,
        attack: Attack | None = None,
    ) -> BenchmarkRunResult:
        """
        Run the benchmark suite.

        Parameters
        ----------
        attack:
            Optional attack to apply to every task before evaluation.
        """
        cases: list[BenchmarkCaseResult] = []
        total_declared = 0
        total_blocked = 0

        for task in self.suite.tasks():
            scenario = task.scenario
            if attack is not None:
                scenario = attack.apply(scenario)

            evaluator = Evaluator(
                environment=scenario.environment,
                defence=self.defence,
                llm_call=self.llm_call,
            )

            evaluation = evaluator.run(scenario.initial_inputs)
            total_declared += len(evaluation.declared)
            total_blocked += len(evaluation.report.blocked_actions)

            cases.append(
                BenchmarkCaseResult(
                    suite_name=self.suite.name,
                    task_name=task.name,
                    attack_name=attack.metadata.name if attack is not None else "",
                    scenario=scenario,
                    result=evaluation,
                )
            )

        return BenchmarkRunResult(
            suite_name=self.suite.name,
            cases=tuple(cases),
            total_tasks=len(cases),
            total_declared=total_declared,
            total_blocked=total_blocked,
        )


def run_suite(
    suite: TaskSuite,
    defence: ITES,
    llm_call: Any,
    attack: Attack | None = None,
) -> BenchmarkRunResult:
    """
    Convenience helper for running a benchmark suite in one call.
    """
    return BenchmarkRunner(
        suite=suite,
        defence=defence,
        llm_call=llm_call,
    ).run(attack=attack)


def iter_case_results(result: BenchmarkRunResult) -> Iterator[BenchmarkCaseResult]:
    """
    Iterate over benchmark case results.
    """
    yield from result.cases


__all__ = [
    "BenchmarkCaseResult",
    "BenchmarkRunResult",
    "BenchmarkRunner",
    "iter_case_results",
    "run_suite",
]
