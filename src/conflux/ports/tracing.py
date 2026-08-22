"""Append-only trace boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class TraceSink(Protocol):
    """Append-only trace boundary for structured records."""

    def append(self, record: Mapping[str, Any]) -> None:
        """Append one structured trace record."""
        ...


__all__ = ["TraceSink"]
