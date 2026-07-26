"""
Native benchmark runner.

This module provides the reference benchmark pipeline for the project's own
SLED environments.

The native benchmark runner is intentionally generic:
- it accepts a collection of benchmark cases,
- runs each case through the exhaustive evaluator,
- converts the result into the shared benchmark result schema,
- and returns an aggregate run summary.

This is the baseline adapter that later benchmark integrations should follow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Mapping

from conflux.ites import ITES
from conflux.sled.environment import Data, Environment
from conflux.sled.evaluator import ExhaustiveEvaluationResult, ExhaustiveEvaluator
from conflux.sled.reporting import EvaluationSummary, summarise_branching

from .results import (
    BenchmarkCaseResult,
    BenchmarkRunMetadata,
    BenchmarkRunSummary,
    build_case_result,
    build_run_summary,
)


@dataclass(frozen=True, slots=True)
class NativeBenchmarkCase:
    """
    One benchmark task or scenario.

    Attributes
    ----------
    case_id:
        Stable identifier for the case.
    environment:
        The SLED environment to evaluate.
    initial_inputs:
        The initial data items visible to the defence.
    primitive_actions:
        Optional explicit primitive action vocabulary. If omitted, the
        environment's aggregated permissions are used.
    metadata:
        Arbitrary metadata for reporting and debugging.
    """

    case_id: str
    environment: Environment
    initial_inputs: tuple[Data, ...] = field(default_factory=tuple)
    primitive_actions: frozenset[str] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_inputs", tuple(self.initial_inputs))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def with_metadata(self, **updates: Any) -> "NativeBenchmarkCase":
        """
        Return a copy with updated metadata.
        """
        merged = dict(self.metadata)
        merged.update(updates)
        return NativeBenchmarkCase(
            case_id=self.case_id,
            environment=self.environment,
            initial_inputs=self.initial_inputs,
            primitive_actions=self.primitive_actions,
            metadata=merged,
        )

    def derived_primitive_actions(self) -> frozenset[str]:
        """
        Derive a primitive action vocabulary if one was not supplied.
        """
        if self.primitive_actions is not None:
            return frozenset(self.primitive_actions)
        return frozenset(permission.name for permission in self.environment.total_actions)


@dataclass(frozen=True, slots=True)
class NativeBenchmarkSuite:
    """
    A collection of native benchmark cases.

    Attributes
    ----------
    name:
        Human-readable benchmark suite name.
    cases:
        The cases to evaluate.
    metadata:
        Arbitrary suite-level metadata.
    """

    name: str
    cases: tuple[NativeBenchmarkCase, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def __iter__(self) -> Iterator[NativeBenchmarkCase]:
        return iter(self.cases)

    def case_ids(self) -> tuple[str, ...]:
        return tuple(case.case_id for case in self.cases)


@dataclass(frozen=True, slots=True)
class NativeBenchmarkCaseOutcome:
    """
    Full output for a single native benchmark case.
    """

    case: NativeBenchmarkCase
    evaluator_result: ExhaustiveEvaluationResult
    report_summary: EvaluationSummary
    result: BenchmarkCaseResult

    @property
    def succeeded(self) -> bool:
        return self.result.succeeded


@dataclass(frozen=True, slots=True)
class NativeBenchmarkRun:
    """
    Complete native benchmark run output.
    """

    suite: NativeBenchmarkSuite
    cases: tuple[NativeBenchmarkCaseOutcome, ...]
    summary: BenchmarkRunSummary
    metadata: BenchmarkRunMetadata

    @property
    def succeeded(self) -> bool:
        return self.summary.succeeded

    def case_result(self, case_id: str) -> NativeBenchmarkCaseOutcome | None:
        for outcome in self.cases:
            if outcome.case.case_id == case_id:
                return outcome
        return None


def _default_case_declare(_: Any) -> None:
    """
    Default declare hook used when callers do not need to observe proposals.
    """
    return None


def _summarise_case(
    case: NativeBenchmarkCase,
    result: ExhaustiveEvaluationResult,
) -> EvaluationSummary:
    """
    Convert an evaluator result into the shared evaluation summary schema.
    """
    branching = summarise_branching(
        branches_explored=result.branches_explored,
        terminal_branches=result.terminal_branches,
        max_depth_reached=result.max_depth_reached,
        branch_option_count=result.branch_option_count,
        terminal_option_count=result.terminal_option_count,
        used_representative_environment=result.used_representative_environment,
        compression_factor=(
            result.representative_environment.compression_factor
            if result.representative_environment is not None
            else None
        ),
    )

    return EvaluationSummary.from_run(
        run_name=case.case_id,
        report=result.report,
        branching=branching,
        declared_actions=result.declared,
        blocked_actions=result.report.blocked_actions,
        metadata={
            "case_id": case.case_id,
            "case_metadata": dict(case.metadata),
            "environment_name": case.environment.name,
        },
    )


def run_native_case(
    case: NativeBenchmarkCase,
    *,
    defence: ITES,
    evaluator_factory: Callable[[ITES, frozenset[str]], ExhaustiveEvaluator] | None = None,
) -> NativeBenchmarkCaseOutcome:
    """
    Run one native benchmark case.

    The default evaluator configuration uses the case's primitive action
    vocabulary and the evaluator's representative-environment compression.
    """
    primitive_actions = case.derived_primitive_actions()

    if evaluator_factory is None:
        evaluator = ExhaustiveEvaluator(
            defence=defence,
            primitive_actions=primitive_actions,
            use_representative_environment=True,
            include_control_actions=True,
        )
    else:
        evaluator = evaluator_factory(defence, primitive_actions)

    evaluator_result = evaluator.run(
        environment=case.environment,
        initial_inputs=case.initial_inputs,
    )
    summary = _summarise_case(case, evaluator_result)
    benchmark_result = build_case_result(
        case.case_id,
        summary,
        metadata={
            "environment_name": case.environment.name,
            "primitive_actions": sorted(primitive_actions),
            "compression_factor": (
                evaluator_result.representative_environment.compression_factor
                if evaluator_result.representative_environment is not None
                else None
            ),
        },
    )

    return NativeBenchmarkCaseOutcome(
        case=case,
        evaluator_result=evaluator_result,
        report_summary=summary,
        result=benchmark_result,
    )


def run_native_suite(
    suite: NativeBenchmarkSuite,
    *,
    defence: ITES,
    evaluator_factory: Callable[[ITES, frozenset[str]], ExhaustiveEvaluator] | None = None,
    metadata: BenchmarkRunMetadata | None = None,
) -> NativeBenchmarkRun:
    """
    Run a complete native benchmark suite.
    """
    outcomes = tuple(
        run_native_case(
            case,
            defence=defence,
            evaluator_factory=evaluator_factory,
        )
        for case in suite.cases
    )

    case_results = tuple(outcome.result for outcome in outcomes)
    summary = build_run_summary(
        suite.name,
        case_results,
        metadata=metadata,
        extra={
            "suite_metadata": dict(suite.metadata),
            "case_ids": suite.case_ids(),
        },
    )

    run_metadata = metadata or BenchmarkRunMetadata(
        benchmark_name=suite.name,
        runner_name="native",
        extra={"suite_metadata": dict(suite.metadata)},
    )

    return NativeBenchmarkRun(
        suite=suite,
        cases=outcomes,
        summary=summary,
        metadata=run_metadata,
    )


def build_native_suite(
    name: str,
    cases: Iterable[NativeBenchmarkCase],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> NativeBenchmarkSuite:
    """
    Convenience helper for creating a native benchmark suite.
    """
    return NativeBenchmarkSuite(
        name=name,
        cases=tuple(cases),
        metadata={} if metadata is None else dict(metadata),
    )


def build_native_case(
    case_id: str,
    environment: Environment,
    initial_inputs: Iterable[Data] = (),
    *,
    primitive_actions: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> NativeBenchmarkCase:
    """
    Convenience helper for creating a benchmark case.
    """
    return NativeBenchmarkCase(
        case_id=case_id,
        environment=environment,
        initial_inputs=tuple(initial_inputs),
        primitive_actions=None if primitive_actions is None else frozenset(primitive_actions),
        metadata={} if metadata is None else dict(metadata),
    )


def native_suite_to_dict(run: NativeBenchmarkRun) -> dict[str, Any]:
    """
    Convert a completed native benchmark run to a JSON-friendly dictionary.
    """
    return {
        "suite": {
            "name": run.suite.name,
            "metadata": dict(run.suite.metadata),
            "case_ids": run.suite.case_ids(),
        },
        "metadata": run.metadata.to_dict(),
        "summary": run.summary.to_dict(),
        "cases": [
            {
                "case_id": outcome.case.case_id,
                "succeeded": outcome.succeeded,
                "summary": outcome.report_summary.to_dict(),
                "result": outcome.result.to_dict(),
                "metadata": dict(outcome.case.metadata),
                "environment_name": outcome.case.environment.name,
                "compression_factor": (
                    outcome.evaluator_result.representative_environment.compression_factor
                    if outcome.evaluator_result.representative_environment is not None
                    else None
                ),
            }
            for outcome in run.cases
        ],
    }


__all__ = [
    "NativeBenchmarkCase",
    "NativeBenchmarkCaseOutcome",
    "NativeBenchmarkRun",
    "NativeBenchmarkSuite",
    "build_native_case",
    "build_native_suite",
    "native_suite_to_dict",
    "run_native_case",
    "run_native_suite",
]
