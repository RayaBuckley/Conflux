"""Versioned immutable records for reproducible evaluation traces."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

TRACE_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class TraceRecord:
    """One append-only evaluation event with stable JSON-compatible fields."""

    event: str
    run_id: str
    sequence: int
    payload: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = TRACE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.event or not self.run_id:
            raise ValueError("TraceRecord event and run_id must be non-empty")
        if self.sequence < 0:
            raise ValueError("TraceRecord.sequence must be non-negative")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        """Return a detached mapping suitable for JSON serialization."""
        return asdict(self)


__all__ = ["TRACE_SCHEMA_VERSION", "TraceRecord"]
