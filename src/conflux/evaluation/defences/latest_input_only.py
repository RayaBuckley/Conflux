"""Latest-input-only baseline defence.

This defence is intentionally unsound. It authorises a proposed read or action
based only on the most recent input that influenced the current execution,
ignoring any earlier influences.

It is useful as a negative control because it captures a common mistake in
agent security implementations: treating the latest prompt, message, or tool
result as the only relevant source of authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import DecisionRecord, Defence, allow, deny


def _extract_latest_principal(trace_context: Any) -> Any:
    """Best-effort extraction of the latest influencing principal."""
    if trace_context is None:
        return None

    for key in (
        "latest_principal",
        "latest_influencer",
        "current_principal",
        "last_principal",
        "initiator",
        "principal",
        "user",
        "requester",
    ):
        if isinstance(trace_context, dict):
            value = trace_context.get(key)
        else:
            value = getattr(trace_context, key, None)
        if value is not None:
            return value

    history_keys = ("principal_history", "influencer_history", "influence_history")
    for key in history_keys:
        if isinstance(trace_context, dict):
            history = trace_context.get(key)
        else:
            history = getattr(trace_context, key, None)

        if isinstance(history, (list, tuple)) and history:
            return history[-1]

    return None


def _extract_authorised_principals(obj: Any) -> set[Any]:
    """Best-effort extraction of authorised principals for the datum/action."""
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


@dataclass
class LatestInputOnlyDefence(Defence):
    """A baseline that trusts only the latest input."""

    name: str = "Latest Input Only"

    description: str = (
        "Allows operations when the most recent influencing principal appears "
        "authorised, ignoring earlier influences."
    )

    def reset(self) -> None:
        """This defence is stateless."""
        return

    def clone(self) -> "LatestInputOnlyDefence":
        """Return a fresh copy of this defence."""
        return LatestInputOnlyDefence()

    def allow_read(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        datum: Any,
    ) -> DecisionRecord:
        latest = _extract_latest_principal(trace_context)
        authorised = _extract_authorised_principals(datum)

        if latest is None:
            return deny(
                "No latest principal found in trace context.",
                labels=frozenset({"baseline", "latest_input_only", "deny"}),
            )

        if authorised and latest not in authorised:
            return deny(
                "Latest principal is not authorised to read the datum.",
                labels=frozenset({"baseline", "latest_input_only", "deny"}),
            )

        return allow(
            "Allowed because only the latest input is considered relevant.",
            labels=frozenset({"baseline", "latest_input_only", "allow"}),
        )

    def allow_action(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        action: Any,
    ) -> DecisionRecord:
        latest = _extract_latest_principal(trace_context)
        authorised = _extract_authorised_principals(action)

        if latest is None:
            return deny(
                "No latest principal found in trace context.",
                labels=frozenset({"baseline", "latest_input_only", "deny"}),
            )

        if authorised and latest not in authorised:
            return deny(
                "Latest principal is not authorised for the proposed action.",
                labels=frozenset({"baseline", "latest_input_only", "deny"}),
            )

        return allow(
            "Allowed because only the latest input is considered relevant.",
            labels=frozenset({"baseline", "latest_input_only", "allow"}),
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


def make_latest_input_only_defence() -> LatestInputOnlyDefence:
    """Convenience constructor for the baseline defence."""
    return LatestInputOnlyDefence()
