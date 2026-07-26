"""Null defence for SLED.

This defence performs no authorisation whatsoever. Every proposed read and
action is permitted.

It exists primarily as a negative control to validate that SLED can discover
security violations. If this defence performs similarly to ITES under SLED,
then either:

- the evaluated environments contain no meaningful attacks,
- or the evaluator is failing to detect violations.

This should therefore always be included in comparative evaluations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import DecisionRecord, Defence, allow


@dataclass
class NoDefence(Defence):
    """A defence that allows every operation."""

    name: str = "No Defence"

    description: str = (
        "Permits every read and every action without any policy checks."
    )

    def reset(self) -> None:
        """Reset any internal state.

        This defence is stateless.
        """
        return

    def clone(self) -> "NoDefence":
        """Return a fresh copy of this defence."""
        return NoDefence()

    def allow_read(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        datum: Any,
    ) -> DecisionRecord:
        """Always allow reads."""
        return allow(
            "No defence: all reads permitted.",
            labels=frozenset({"baseline", "allow_all"}),
        )

    def allow_action(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        action: Any,
    ) -> DecisionRecord:
        """Always allow actions."""
        return allow(
            "No defence: all actions permitted.",
            labels=frozenset({"baseline", "allow_all"}),
        )

    def observe(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        event: Any,
    ) -> None:
        """Observe an event.

        This implementation deliberately ignores all observations.
        """
        return
