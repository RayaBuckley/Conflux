"""Fail-closed parser boundary for unvalidated external benchmark output."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ExternalBenchmarkRecord:
    """Validated record from an external benchmark run."""

    schema: str
    task_id: str
    secure: bool
    useful: bool


def parse_external_record(payload: Mapping[str, Any], *, supported_schema: str) -> ExternalBenchmarkRecord:
    """Parse and validate an external benchmark record, raising on mismatch."""
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
