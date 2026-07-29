"""Provider materialisation boundary."""

from __future__ import annotations

from typing import Protocol

from conflux.domain import EnvironmentSnapshot


class EnvironmentPort(Protocol):
    def snapshot(self) -> EnvironmentSnapshot: ...


__all__ = ["EnvironmentPort"]
