"""Fail-closed parser boundary for unvalidated external benchmark output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ExternalBenchmarkRecord:
    schema: str
    task_id: str
    secure: bool
    useful: bool


def parse_external_record(payload: Mapping[str, Any], *, supported_schema: str) -> ExternalBenchmarkRecord:
    if payload.get("schema") != supported_schema:
        raise ValueError("unsupported external benchmark schema")
    required = ("task_id", "secure", "useful")
    if any(key not in payload for key in required):
        raise ValueError("incomplete external benchmark record")
    if not isinstance(payload["secure"], bool) or not isinstance(payload["useful"], bool):
        raise TypeError("security and utility outcomes must be Boolean")
    return ExternalBenchmarkRecord(
        schema=supported_schema,
        task_id=str(payload["task_id"]),
        secure=payload["secure"],
        useful=payload["useful"],
    )


__all__ = ["ExternalBenchmarkRecord", "parse_external_record"]
