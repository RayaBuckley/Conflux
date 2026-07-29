"""Immutable mediation-session context."""

from __future__ import annotations

from dataclasses import dataclass, field

from .identity import Principal


@dataclass(frozen=True, slots=True)
class Session:
    id: str
    participants: frozenset[Principal] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Session.id must be non-empty")
        object.__setattr__(self, "participants", frozenset(self.participants))


__all__ = ["Session"]
