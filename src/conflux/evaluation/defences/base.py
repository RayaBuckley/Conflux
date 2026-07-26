"""Base interfaces for SLED defences.

SLED evaluates defences by exploring the same environment under multiple
authorisation strategies. This module defines the shared contract that all
defence implementations should satisfy.

The interface is intentionally small. A defence decides whether a proposed read
or action is allowed, given the current scenario and the trace context that led
to the proposal. The evaluator can then compare the behaviour of different
defences without depending on their internal implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


class Decision(str, Enum):
    """Normalised authorisation decision."""

    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class DecisionRecord:
    """Structured explanation for a defence decision."""

    decision: Decision
    reason: str = ""
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class Defence(Protocol):
    """Shared contract for all SLED defences.

    The evaluator should treat a defence as a pure policy object:
    - it must be safe to construct once and reuse across many traces,
    - it should be deterministic for a fixed input state,
    - it should not mutate external state,
    - it should return normalised allow/deny decisions.

    A defence may be conservative and return DENY when it cannot justify an
    action. Returning ABSTAIN is permitted for implementations that want to
    delegate to a fallback policy, but the evaluator should normally treat
    ABSTAIN as denial unless explicitly configured otherwise.
    """

    name: str
    description: str

    def reset(self) -> None:
        """Reset any per-run state held by the defence."""

    def clone(self) -> "Defence":
        """Return a fresh defence instance with the same configuration."""

    def allow_read(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        datum: Any,
    ) -> DecisionRecord:
        """Decide whether a datum may be read in the current context."""

    def allow_action(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        action: Any,
    ) -> DecisionRecord:
        """Decide whether an externally visible action may be executed."""

    def observe(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        event: Any,
    ) -> None:
        """Observe a trace event after the fact.

        This hook is optional for pure policy implementations, but it is useful
        for weaker or stateful baselines that need to remember earlier inputs or
        actions.
        """


def abstain(reason: str = "", *, labels: frozenset[str] | None = None) -> DecisionRecord:
    """Return a standard abstention record."""
    return DecisionRecord(
        decision=Decision.ABSTAIN,
        reason=reason,
        labels=labels or frozenset(),
    )


def allow(reason: str = "", *, labels: frozenset[str] | None = None) -> DecisionRecord:
    """Return a standard allow record."""
    return DecisionRecord(
        decision=Decision.ALLOW,
        reason=reason,
        labels=labels or frozenset(),
    )


def deny(reason: str = "", *, labels: frozenset[str] | None = None) -> DecisionRecord:
    """Return a standard deny record."""
    return DecisionRecord(
        decision=Decision.DENY,
        reason=reason,
        labels=labels or frozenset(),
    )
