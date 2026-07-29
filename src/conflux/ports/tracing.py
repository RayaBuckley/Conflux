"""Append-only trace boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class TraceSink(Protocol):
    def append(self, record: Mapping[str, Any]) -> None: ...


__all__ = ["TraceSink"]
