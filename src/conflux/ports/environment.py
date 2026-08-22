"""Provider materialisation boundary."""

from __future__ import annotations

from typing import Protocol

from conflux.domain import EnvironmentSnapshot


class EnvironmentPort(Protocol):
    """Provider materialisation boundary for environment snapshots."""

    def snapshot(self) -> EnvironmentSnapshot:
        """Capture the current provider environment as an immutable snapshot."""
        ...


__all__ = ["EnvironmentPort"]
