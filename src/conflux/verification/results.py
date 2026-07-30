"""Deterministic formal-backend result records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FormalVerdict(StrEnum):
    SAFE = "safe"
    BOUNDED_SAFE = "bounded_safe"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FormalVerificationResult:
    verdict: FormalVerdict
    backend: str
    ir_hash: str
    query_hash: str
    solver_hash: str
    model_hash: str | None
    bound: int
    assumptions: tuple[str, ...]
    counterexample: tuple[dict[str, object], ...] = ()
    error: str | None = None
    schema_version: str = "1"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "verdict": self.verdict.value,
            "backend": self.backend,
            "ir_hash": self.ir_hash,
            "query_hash": self.query_hash,
            "solver_hash": self.solver_hash,
            "model_hash": self.model_hash,
            "bound": self.bound,
            "assumptions": list(self.assumptions),
            "counterexample": list(self.counterexample),
            "error": self.error,
        }


__all__ = ["FormalVerdict", "FormalVerificationResult"]
