"""Adapter that exposes the existing ITES implementation through the SLED
defence interface.

This file should stay thin. Its role is to let SLED evaluate the current
provenance-based defence without forcing the evaluator to know about ITES
internals.

The adapter is intentionally permissive about the shape of the underlying ITES
object. It assumes the wrapped implementation exposes authorisation methods or a
single decision method that can be mapped onto read and action checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .base import Decision, DecisionRecord, Defence, abstain, allow, deny


@runtime_checkable
class _ITESLike(Protocol):
    """Minimal protocol for the wrapped ITES implementation."""

    name: str
    description: str

    def reset(self) -> None: ...

    def clone(self) -> Any: ...

    def allow_read(self, *, scenario: Any, trace_context: Any, datum: Any) -> Any: ...

    def allow_action(self, *, scenario: Any, trace_context: Any, action: Any) -> Any: ...

    def observe(self, *, scenario: Any, trace_context: Any, event: Any) -> None: ...


@dataclass
class ITESAdapter(Defence):
    """Wrap an ITES implementation so it can be compared against baselines."""

    implementation: Any
    name: str = "ITES"
    description: str = (
        "Provenance-based defence that derives authority from the intersection "
        "of all influencing principals."
    )

    def _coerce(self, result: Any, fallback_reason: str = "") -> DecisionRecord:
        """Normalise wrapped implementation outputs into a DecisionRecord."""
        if isinstance(result, DecisionRecord):
            return result

        if isinstance(result, Decision):
            if result is Decision.ALLOW:
                return allow(fallback_reason)
            if result is Decision.DENY:
                return deny(fallback_reason)
            return abstain(fallback_reason)

        if isinstance(result, bool):
            return allow(fallback_reason) if result else deny(fallback_reason)

        if result is None:
            return abstain(fallback_reason)

        decision = getattr(result, "decision", None)
        if decision is not None:
            if isinstance(decision, Decision):
                mapped = decision
            else:
                mapped_text = str(decision).strip().lower()
                if mapped_text == "allow":
                    mapped = Decision.ALLOW
                elif mapped_text == "deny":
                    mapped = Decision.DENY
                else:
                    mapped = Decision.ABSTAIN

            reason = getattr(result, "reason", fallback_reason) or fallback_reason
            labels: frozenset[str] = frozenset(getattr(result, "labels", frozenset()) or frozenset())
            metadata = getattr(result, "metadata", {}) or {}

            return DecisionRecord(
                decision=mapped,
                reason=reason,
                labels=frozenset(labels),
                metadata=metadata,
            )

        return abstain(fallback_reason)

    def reset(self) -> None:
        if hasattr(self.implementation, "reset"):
            self.implementation.reset()

    def clone(self) -> "ITESAdapter":
        if hasattr(self.implementation, "clone"):
            cloned = self.implementation.clone()
        else:
            cloned = self.implementation
        return ITESAdapter(
            implementation=cloned,
            name=self.name,
            description=self.description,
        )

    def allow_read(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        datum: Any,
    ) -> DecisionRecord:
        if hasattr(self.implementation, "allow_read"):
            result = self.implementation.allow_read(
                scenario=scenario,
                trace_context=trace_context,
                datum=datum,
            )
            return self._coerce(result, "ITES read check")

        if hasattr(self.implementation, "authorise_read"):
            result = self.implementation.authorise_read(
                scenario=scenario,
                trace_context=trace_context,
                datum=datum,
            )
            return self._coerce(result, "ITES read check")

        if hasattr(self.implementation, "authorize_read"):
            result = self.implementation.authorize_read(
                scenario=scenario,
                trace_context=trace_context,
                datum=datum,
            )
            return self._coerce(result, "ITES read check")

        return abstain("Wrapped ITES implementation does not expose a read check.")

    def allow_action(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        action: Any,
    ) -> DecisionRecord:
        if hasattr(self.implementation, "allow_action"):
            result = self.implementation.allow_action(
                scenario=scenario,
                trace_context=trace_context,
                action=action,
            )
            return self._coerce(result, "ITES action check")

        if hasattr(self.implementation, "authorise_action"):
            result = self.implementation.authorise_action(
                scenario=scenario,
                trace_context=trace_context,
                action=action,
            )
            return self._coerce(result, "ITES action check")

        if hasattr(self.implementation, "authorize_action"):
            result = self.implementation.authorize_action(
                scenario=scenario,
                trace_context=trace_context,
                action=action,
            )
            return self._coerce(result, "ITES action check")

        return abstain("Wrapped ITES implementation does not expose an action check.")

    def observe(
        self,
        *,
        scenario: Any,
        trace_context: Any,
        event: Any,
    ) -> None:
        if hasattr(self.implementation, "observe"):
            self.implementation.observe(
                scenario=scenario,
                trace_context=trace_context,
                event=event,
            )

    @classmethod
    def from_implementation(cls, implementation: Any) -> "ITESAdapter":
        """Construct an adapter with defaults derived from the wrapped object."""
        name = getattr(implementation, "name", "ITES")
        description = getattr(
            implementation,
            "description",
            "Provenance-based defence wrapped for SLED evaluation.",
        )
        return cls(
            implementation=implementation,
            name=name,
            description=description,
        )
