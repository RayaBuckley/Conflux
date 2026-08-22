"""Small SLED model for selector, disclosure, attribution, and redaction monitors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from conflux.domain import DisclosureLevel, fingerprint

from .model_checking import Transition


class DisclosureMutation(StrEnum):
    """Canonical or defective disclosure variant under verification."""

    CANONICAL = "canonical"
    UNAUTHORISED_SELECTOR = "unauthorised_selector"
    HIDDEN_ERROR_LEAK = "hidden_error_leak"
    INCOMPLETE_ATTRIBUTION = "incomplete_attribution"
    UNSAFE_REDACTION = "unsafe_redaction"


@dataclass(frozen=True, slots=True)
class DisclosureState:
    """Snapshot of selector, disclosure, and attribution fields for model checking."""

    selector_allowed: bool = False
    selector_authorised: bool = False
    disclosure_level: DisclosureLevel = DisclosureLevel.NONE
    disclosed_fields: frozenset[str] = frozenset()
    sensitive_fields: frozenset[str] = frozenset({"policy_detail", "secret_value"})
    required_attribution: frozenset[str] = frozenset({"verified_inputs", "influence", "principal_context", "uncertainty"})
    attribution_fields: frozenset[str] = frozenset()
    terminal: bool = False


@dataclass(frozen=True, slots=True)
class DisclosureVerificationSystem:
    """Transition system modelling a single observation under a mutation."""

    mutation: DisclosureMutation = DisclosureMutation.CANONICAL

    def initial_states(self) -> tuple[DisclosureState, ...]:
        """Return the single initial disclosure state."""
        return (DisclosureState(),)

    def enabled(self, state: DisclosureState) -> tuple[str, ...]:
        """Return the observe action when the state is non-terminal."""
        return () if state.terminal else ("observe",)

    def step(self, state: DisclosureState, action: str) -> tuple[DisclosureState, ...]:
        """Execute an observation, producing a terminal state under the mutation."""
        if action != "observe":
            raise ValueError("unsupported disclosure action")
        selector_authorised = self.mutation == DisclosureMutation.UNAUTHORISED_SELECTOR
        level = DisclosureLevel.REDACTED
        disclosed = frozenset({"redacted", "payload_fingerprint"})
        attribution = state.required_attribution
        if self.mutation == DisclosureMutation.HIDDEN_ERROR_LEAK:
            disclosed |= {"policy_detail"}
        if self.mutation == DisclosureMutation.UNSAFE_REDACTION:
            disclosed |= {"secret_value"}
        if self.mutation == DisclosureMutation.INCOMPLETE_ATTRIBUTION:
            attribution = frozenset({"principal_context"})
        return (
            DisclosureState(
                selector_allowed=False,
                selector_authorised=selector_authorised,
                disclosure_level=level,
                disclosed_fields=disclosed,
                sensitive_fields=state.sensitive_fields,
                required_attribution=state.required_attribution,
                attribution_fields=attribution,
                terminal=True,
            ),
        )

    def is_terminal(self, state: DisclosureState) -> bool:
        """Whether the disclosure model has reached its terminal state."""
        return state.terminal

    def state_key(self, state: DisclosureState) -> str:
        """Return a canonical deduplication key for a disclosure state."""
        return fingerprint(state)

    def action_key(self, action: str) -> tuple[object, ...]:
        """Return a stable sort key for a disclosure action."""
        return (action,)

    def model_calls(self, state: DisclosureState) -> int:
        """Return the model-call count for a disclosure state."""
        return int(state.terminal)


@dataclass(frozen=True, slots=True)
class NoUnauthorisedSelector:
    """Ensures a denied selector is never authorised."""

    name: str = "no_unauthorised_selector"

    def violation(self, transition: Transition[DisclosureState, str]) -> str | None:
        """Return a reason if a denied selector was authorised."""
        target = transition.target
        return "a denied selector was authorised" if target.selector_authorised and not target.selector_allowed else None


@dataclass(frozen=True, slots=True)
class NoHiddenDecisionLeakage:
    """Ensures sensitive decision fields are not disclosed."""

    name: str = "no_hidden_decision_leakage"

    def violation(self, transition: Transition[DisclosureState, str]) -> str | None:
        """Return a reason if hidden sensitive fields were disclosed."""
        target = transition.target
        leaked = target.disclosed_fields & target.sensitive_fields
        return f"hidden fields disclosed: {sorted(leaked)}" if leaked else None


@dataclass(frozen=True, slots=True)
class CompleteAttribution:
    """Ensures all required attribution fields are present."""

    name: str = "complete_attribution"

    def violation(self, transition: Transition[DisclosureState, str]) -> str | None:
        """Return a reason if any required attribution field is missing."""
        missing = transition.target.required_attribution - transition.target.attribution_fields
        return f"attribution fields missing: {sorted(missing)}" if missing else None


@dataclass(frozen=True, slots=True)
class SafeRedaction:
    """Ensures redacted projections do not disclose secret values."""

    name: str = "safe_redaction"

    def violation(self, transition: Transition[DisclosureState, str]) -> str | None:
        """Return a reason if a redacted projection disclosed a secret value."""
        target = transition.target
        if target.disclosure_level == DisclosureLevel.REDACTED and "secret_value" in target.disclosed_fields:
            return "redacted projection disclosed a secret value"
        return None


__all__ = [
    "CompleteAttribution",
    "DisclosureMutation",
    "DisclosureState",
    "DisclosureVerificationSystem",
    "NoHiddenDecisionLeakage",
    "NoUnauthorisedSelector",
    "SafeRedaction",
]
