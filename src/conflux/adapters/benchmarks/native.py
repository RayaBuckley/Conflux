"""Small offline native benchmark for the canonical evaluator."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.evaluation import VerificationResult


@dataclass(frozen=True, slots=True)
class NativeBenchmarkResult:
    name: str
    verification: VerificationResult[object, object]

    @property
    def passed(self) -> bool:
        return self.verification.verdict.value in {"safe", "bounded_safe"}


__all__ = ["NativeBenchmarkResult"]
