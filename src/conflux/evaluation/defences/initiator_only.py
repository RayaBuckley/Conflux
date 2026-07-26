"""Initiator-only baseline defence for SLED.

This defence is intentionally weaker than ITES. It only checks whether the
action or read appears to be authorised for the principal that initiated the
current execution, and ignores influence accumulated from other principals.

It is useful as a negative control because it models a common but unsound
simplification: treating the first requester as the only authority that matters.
If SLED cannot distinguish this baseline from ITES, the evaluator is not
sensitive enough.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import DecisionRecord, Defence, allow, deny


def _extract_initiator(trace_context: Any) -> Any:
    """Best-effort extraction of the initiating principal from trace context."""
    if trace_context is None:
        return None

    for key in ("initiator", "principal", "user", "requester", "actor", "author"):
        if isinstance(trace_context, dict):
            value = trace_context.get(key)
        else:
            value = getattr(trace_context, key, None)
        if value is not None:
            return value

    return None


def _extract_authorised_principals(trace_context: Any) -> set[Any]:
    """Best-effort extraction of principals considered authorised for the trace."""
    values: set[Any] = set()

    if trace_context is None:
        return values

    for key in ("authorised_principals", "authorized_principals", "allowed_principals", "principals"):
        if isinstance(trace_context, dict):
            raw = trace_context.get(key)
        else:
            raw = getattr(trace_context, key, None)

        if raw is None:
            continue

        if isinstance(raw, (set, frozenset, list, tuple)):
            values.update(raw)
        else:
            values.add(raw)

    return values


@dataclass
class InitiatorOnlyDefence(Defence):
    """A baseline that only trusts the initiator of the trace."""

    name: str = "Initiator Only"

    description: str = (
        "Allows operations only when they appear authorised for the initiating "
        "principal, ignoring additional influence."
    )

    def reset(self) -> None:
        """This defence is stateless."""
        return

    def clone(self) -> "InitiatorOnlyDefence":
        """Return a fresh copy of this defence."""
        return InitiatorOnlyDefence()

    def allow_read(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        datum: Any,
    ) -> DecisionRecord:
        initiator = _extract_initiator(trace_context)
        authorised = _extract_authorised_principals(trace_context)

        if initiator is None:
            return deny(
                "No initiator found in trace context.",
                labels=frozenset({"baseline", "initiator_only", "deny"}),
            )

        if authorised and initiator not in authorised:
            return deny(
                "Initiator is not in the authorised principal set.",
                labels=frozenset({"baseline", "initiator_only", "deny"}),
            )

        return allow(
            "Allowed because the initiator is treated as the only relevant principal.",
            labels=frozenset({"baseline", "initiator_only", "allow"}),
        )

    def allow_action(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        action: Any,
    ) -> DecisionRecord:
        initiator = _extract_initiator(trace_context)
        authorised = _extract_authorised_principals(trace_context)

        if initiator is None:
            return deny(
                "No initiator found in trace context.",
                labels=frozenset({"baseline", "initiator_only", "deny"}),
            )

        if authorised and initiator not in authorised:
            return deny(
                "Initiator is not authorised for the proposed action.",
                labels=frozenset({"baseline", "initiator_only", "deny"}),
            )

        return allow(
            "Allowed because the action is judged solely against the initiator.",
            labels=frozenset({"baseline", "initiator_only", "allow"}),
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


def make_initiator_only_defence() -> InitiatorOnlyDefence:
    """Convenience constructor for the baseline defence."""
    return InitiatorOnlyDefence()
