"""Union-of-permissions baseline defence.

This intentionally incorrect defence authorises an operation whenever *any*
influencing principal appears to be authorised.

In contrast, ITES requires *every* influencing principal to be authorised.

This defence demonstrates why taking the union of permissions is unsound under
the ITES threat model: authority can increase as additional influence is
introduced, permitting privilege escalation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .base import DecisionRecord, Defence, allow, deny


def _extract_principals(trace_context: Any) -> set[Any]:
    """Extract influencing principals from the trace context."""
    if trace_context is None:
        return set()

    keys = (
        "principals",
        "influencing_principals",
        "authors",
        "influence",
        "authority",
    )

    principals: set[Any] = set()

    for key in keys:
        if isinstance(trace_context, dict):
            value = trace_context.get(key)
        else:
            value = getattr(trace_context, key, None)

        if value is None:
            continue

        if isinstance(value, (set, frozenset, list, tuple)):
            principals.update(value)
        else:
            principals.add(value)

    return principals


def _extract_authorised_principals(obj: Any) -> set[Any]:
    """Extract principals authorised for a proposed operation."""

    if obj is None:
        return set()

    keys = (
        "authorised_principals",
        "authorized_principals",
        "allowed_principals",
        "principals",
    )

    principals: set[Any] = set()

    for key in keys:
        if isinstance(obj, dict):
            value = obj.get(key)
        else:
            value = getattr(obj, key, None)

        if value is None:
            continue

        if isinstance(value, (set, frozenset, list, tuple)):
            principals.update(value)
        else:
            principals.add(value)

    return principals


def _intersects(left: Iterable[Any], right: Iterable[Any]) -> bool:
    """Return True if the two collections intersect."""
    return not set(left).isdisjoint(right)


@dataclass
class UnionPermissionsDefence(Defence):
    """Unsound baseline using permission union."""

    name: str = "Union Permissions"

    description: str = (
        "Allows an operation whenever any influencing principal appears to be "
        "authorised."
    )

    def reset(self) -> None:
        """Reset any internal state.

        This implementation is stateless.
        """
        return

    def clone(self) -> "UnionPermissionsDefence":
        """Return a fresh copy."""
        return UnionPermissionsDefence()

    def allow_read(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        datum: Any,
    ) -> DecisionRecord:
        influencing = _extract_principals(trace_context)
        authorised = _extract_authorised_principals(datum)

        if not influencing:
            return deny(
                "No influencing principals available.",
                labels=frozenset({"baseline", "union_permissions"}),
            )

        if _intersects(influencing, authorised):
            return allow(
                "Read permitted because at least one influencing principal is authorised.",
                labels=frozenset({"baseline", "union_permissions"}),
            )

        return deny(
            "No influencing principal is authorised.",
            labels=frozenset({"baseline", "union_permissions"}),
        )

    def allow_action(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        action: Any,
    ) -> DecisionRecord:
        influencing = _extract_principals(trace_context)
        authorised = _extract_authorised_principals(action)

        if not influencing:
            return deny(
                "No influencing principals available.",
                labels=frozenset({"baseline", "union_permissions"}),
            )

        if _intersects(influencing, authorised):
            return allow(
                "Action permitted because at least one influencing principal is authorised.",
                labels=frozenset({"baseline", "union_permissions"}),
            )

        return deny(
            "No influencing principal is authorised.",
            labels=frozenset({"baseline", "union_permissions"}),
        )

    def observe(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        event: Any,
    ) -> None:
        """Observe an event.

        This baseline deliberately ignores observations.
        """
        return


def make_union_permissions_defence() -> UnionPermissionsDefence:
    """Construct the union-of-permissions baseline."""
    return UnionPermissionsDefence()
