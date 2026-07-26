"""Port for provider materialisation into the domain environment contract."""

from __future__ import annotations

from typing import Protocol

from conflux.domain.environment import EnvironmentSnapshot


class EnvironmentPort(Protocol):
    """Expose a read-only provider snapshot without SLED dependencies."""

    def snapshot(self) -> EnvironmentSnapshot:
        """Return the current immutable provider snapshot."""
        ...


__all__ = ["EnvironmentPort"]
