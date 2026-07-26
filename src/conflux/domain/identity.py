"""Principal identity and explicit Principal Context domain values."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.core.principals import Principal


@dataclass(frozen=True, slots=True)
class PrincipalContext:
    """The immutable set of Principals influencing one decision."""

    principals: frozenset[Principal] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principals", frozenset(self.principals))

    def extend(self, *principals: Principal) -> "PrincipalContext":
        """Return a context containing the current and added Principals."""
        return PrincipalContext(self.principals | frozenset(principals))

    def contains(self, principal: Principal) -> bool:
        """Return whether a Principal contributes to this context."""
        return principal in self.principals


__all__ = ["Principal", "PrincipalContext"]
