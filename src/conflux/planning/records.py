"""Deterministic records for initial and continuation planner calls."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint


@dataclass(frozen=True, slots=True)
class PlannerRecord:
    """Deterministic record of a single planner call (initial or continuation)."""

    planner_id: str
    planner_version: str
    configuration_hash: str
    request_hash: str
    response_hash: str
    parsed_hash: str | None
    raw_response: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    error: str | None = None
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if not self.planner_id or not self.planner_version:
            raise ValueError("planner identity and version must be non-empty")
        usage = tuple(item for item in (self.input_tokens, self.output_tokens, self.latency_ms) if item is not None)
        if usage and min(usage) < 0:
            raise ValueError("planner usage values cannot be negative")

    @classmethod
    def create(
        cls,
        *,
        planner_id: str,
        planner_version: str,
        configuration: object,
        request: object,
        response: object,
        parsed: object | None,
        raw_response: str,
        error: str | None = None,
    ) -> PlannerRecord:
        """Construct a PlannerRecord by fingerprinting configuration, request, and response."""
        return cls(
            planner_id,
            planner_version,
            fingerprint(configuration),
            fingerprint(request),
            fingerprint(response),
            fingerprint(parsed) if parsed is not None else None,
            raw_response,
            error=error,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise the planner record to a canonical dictionary."""
        return {
            "schema_version": self.schema_version,
            "planner_id": self.planner_id,
            "planner_version": self.planner_version,
            "configuration_hash": self.configuration_hash,
            "request_hash": self.request_hash,
            "response_hash": self.response_hash,
            "parsed_hash": self.parsed_hash,
            "raw_response": self.raw_response,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


__all__ = ["PlannerRecord"]
