"""
Benchmark result schema.

This module defines the canonical result objects used by native benchmarks and
benchmark adapters.

The goal is to keep evaluation output stable even when the underlying
environment, provider adapter, or report formatting changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from conflux.sled.reporting import EvaluationSummary


@dataclass(frozen=True, slots=True)
class BenchmarkCaseResult:
    """
    Result for one benchmark case or task.
    """

    case_id: str
    succeeded: bool
    summary: EvaluationSummary
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "succeeded": self.succeeded,
            "summary": self.summary.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkRunMetadata:
    """
    Metadata describing how a benchmark run was produced.
    """

    benchmark_name: str
    runner_name: str
    model_name: str | None = None
    provider_name: str | None = None
    environment_name: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", dict(self.extra))

    def with_finished_at(self, finished_at: datetime | None = None) -> "BenchmarkRunMetadata":
        """
        Return a copy with a completed timestamp.
        """
        completed = finished_at or datetime.now(timezone.utc)
        return BenchmarkRunMetadata(
            benchmark_name=self.benchmark_name,
            runner_name=self.runner_name,
            model_name=self.model_name,
            provider_name=self.provider_name,
            environment_name=self.environment_name,
            started_at=self.started_at,
            finished_at=completed.isoformat(),
            extra=dict(self.extra),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BenchmarkRunSummary:
    """
    Aggregate summary for a benchmark run.
    """

    benchmark_name: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    case_results: tuple[BenchmarkCaseResult, ...] = field(default_factory=tuple)
    metadata: BenchmarkRunMetadata | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", dict(self.extra))

    @property
    def succeeded(self) -> bool:
        return self.failed_cases == 0

    @property
    def pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.passed_cases / self.total_cases

    @classmethod
    def from_case_results(
        cls,
        *,
        benchmark_name: str,
        case_results: tuple[BenchmarkCaseResult, ...],
        metadata: BenchmarkRunMetadata | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> "BenchmarkRunSummary":
        passed = sum(1 for case in case_results if case.succeeded)
        failed = len(case_results) - passed
        return cls(
            benchmark_name=benchmark_name,
            total_cases=len(case_results),
            passed_cases=passed,
            failed_cases=failed,
            case_results=case_results,
            metadata=metadata,
            extra={} if extra is None else dict(extra),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_name": self.benchmark_name,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "pass_rate": self.pass_rate,
            "succeeded": self.succeeded,
            "case_results": [case.to_dict() for case in self.case_results],
            "metadata": None if self.metadata is None else self.metadata.to_dict(),
            "extra": dict(self.extra),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    """
    Comparison between two benchmark runs.
    """

    baseline: BenchmarkRunSummary
    candidate: BenchmarkRunSummary
    delta_passed: int
    delta_failed: int
    delta_pass_rate: float
    note: str = ""

    @classmethod
    def between(
        cls,
        baseline: BenchmarkRunSummary,
        candidate: BenchmarkRunSummary,
        *,
        note: str = "",
    ) -> "BenchmarkComparison":
        return cls(
            baseline=baseline,
            candidate=candidate,
            delta_passed=candidate.passed_cases - baseline.passed_cases,
            delta_failed=candidate.failed_cases - baseline.failed_cases,
            delta_pass_rate=candidate.pass_rate - baseline.pass_rate,
            note=note,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline": self.baseline.to_dict(),
            "candidate": self.candidate.to_dict(),
            "delta_passed": self.delta_passed,
            "delta_failed": self.delta_failed,
            "delta_pass_rate": self.delta_pass_rate,
            "note": self.note,
        }


def build_case_result(
    case_id: str,
    summary: EvaluationSummary,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> BenchmarkCaseResult:
    """
    Convenience helper for creating a benchmark case result.
    """
    return BenchmarkCaseResult(
        case_id=case_id,
        succeeded=summary.succeeded,
        summary=summary,
        metadata={} if metadata is None else dict(metadata),
    )


def build_run_summary(
    benchmark_name: str,
    case_results: tuple[BenchmarkCaseResult, ...],
    *,
    metadata: BenchmarkRunMetadata | None = None,
    extra: Mapping[str, Any] | None = None,
) -> BenchmarkRunSummary:
    """
    Convenience helper for creating a run summary.
    """
    return BenchmarkRunSummary.from_case_results(
        benchmark_name=benchmark_name,
        case_results=case_results,
        metadata=metadata,
        extra=extra,
    )


def now_utc() -> datetime:
    """
    Return the current UTC time.
    """
    return datetime.now(timezone.utc)


__all__ = [
    "BenchmarkCaseResult",
    "BenchmarkComparison",
    "BenchmarkRunMetadata",
    "BenchmarkRunSummary",
    "build_case_result",
    "build_run_summary",
    "now_utc",
]
