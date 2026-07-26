"""Baseline defence that skips read checks.

This defence still performs action checks, but it allows every read. It is a
useful negative control because it lets SLED demonstrate information leakage
and provenance mistakes even when action authorisation appears to be present.

A defence of this shape is unrealistic but common in partial security
implementations: developers protect the final action while allowing the model
to consume arbitrary data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import DecisionRecord, Defence, allow, deny


def _extract_authorised_principals(obj: Any) -> set[Any]:
    """Best-effort extraction of authorised principals for an action."""
    if obj is None:
        return set()

    principals: set[Any] = set()
    for key in (
        "authorised_principals",
        "authorized_principals",
        "allowed_principals",
        "principals",
    ):
        if isinstance(obj, dict):
            raw = obj.get(key)
        else:
            raw = getattr(obj, key, None)

        if raw is None:
            continue

        if isinstance(raw, (set, frozenset, list, tuple)):
            principals.update(raw)
        else:
            principals.add(raw)

    return principals


def _extract_influencing_principals(trace_context: Any) -> set[Any]:
    """Best-effort extraction of influencing principals from trace context."""
    if trace_context is None:
        return set()

    principals: set[Any] = set()
    for key in (
        "principals",
        "influencing_principals",
        "authors",
        "influence",
        "authority",
        "principal_history",
    ):
        if isinstance(trace_context, dict):
            raw = trace_context.get(key)
        else:
            raw = getattr(trace_context, key, None)

        if raw is None:
            continue

        if isinstance(raw, (set, frozenset, list, tuple)):
            principals.update(raw)
        else:
            principals.add(raw)

    return principals


@dataclass
class NoReadCheckDefence(Defence):
    """A defence that ignores read authorisation entirely."""

    name: str = "No Read Check"

    description: str = (
        "Permits every read, but still checks whether proposed actions are "
        "authorised for the current trace."
    )

    def reset(self) -> None:
        """This defence is stateless."""
        return

    def clone(self) -> "NoReadCheckDefence":
        """Return a fresh copy of this defence."""
        return NoReadCheckDefence()

    def allow_read(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        datum: Any,
    ) -> DecisionRecord:
        """Always allow reads."""
        return allow(
            "Read checks are disabled in this baseline.",
            labels=frozenset({"baseline", "no_read_check", "allow"}),
        )

    def allow_action(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        action: Any,
    ) -> DecisionRecord:
        """Allow only when the action appears authorised for the current trace."""
        influencing = _extract_influencing_principals(trace_context)
        authorised = _extract_authorised_principals(action)

        if not influencing:
            return deny(
                "No influencing principals found in trace context.",
                labels=frozenset({"baseline", "no_read_check", "deny"}),
            )

        if authorised and not influencing.issubset(authorised):
            return deny(
                "At least one influencing principal is not authorised for the action.",
                labels=frozenset({"baseline", "no_read_check", "deny"}),
            )

        return allow(
            "Action permitted; only read checks are disabled.",
            labels=frozenset({"baseline", "no_read_check", "allow"}),
        )

    def observe(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        event: Any,
    ) -> None:
        """Observe an event without changing state."""
        return


def make_no_read_check_defence() -> NoReadCheckDefence:
    """Convenience constructor for the baseline defence."""
    return NoReadCheckDefence()
