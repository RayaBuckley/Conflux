"""Port for append-only execution and decision traces."""

from __future__ import annotations

from typing import Protocol


class TraceSink(Protocol):
    """Receive immutable, serializable trace records."""

    def append(self, record: object) -> None:
        """Append one record in evaluation order."""
        ...


__all__ = ["TraceSink"]
