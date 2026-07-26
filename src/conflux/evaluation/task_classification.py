"""Trace classification for SLED.

This module converts raw execution traces into stable task and outcome labels
that can be aggregated into utility and security statistics.

The evaluator should remain responsible for exploring traces. This module only
interprets finished traces and should therefore stay free of search logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class SecurityOutcome(str, Enum):
    """Security-level classification for a trace."""

    SECURE = "secure"
    BLOCKED = "blocked"
    VIOLATION = "violation"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"


class UtilityOutcome(str, Enum):
    """Utility-level classification for a trace."""

    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    TASK_FAILED = "task_failed"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class TaskFamily(str, Enum):
    """Representative task family for reporting."""

    READ_ONLY = "read_only"
    AUTHORISED_WRITE = "authorised_write"
    CROSS_PRINCIPAL = "cross_principal"
    EXFILTRATION_ATTEMPT = "exfiltration_attempt"
    DELEGATION_REQUIRED = "delegation_required"
    MIXED_INFLUENCE = "mixed_influence"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TraceClassification:
    """Normalised classification for a single trace."""

    trace_id: str | None
    task_name: str | None
    environment_name: str | None
    task_family: TaskFamily
    security_outcome: SecurityOutcome
    utility_outcome: UtilityOutcome
    labels: frozenset[str] = field(default_factory=frozenset)
    reason: str = ""


class TraceClassifier:
    """Heuristic classifier for SLED traces.

    The classifier is intentionally conservative:
    - if a trace looks incomplete, it is classified as incomplete;
    - if a trace contains any signal of successful unauthorised action, it is a
      security violation;
    - if a trace appears blocked by policy, it is classified as blocked;
    - otherwise it is classified as secure if the task completed.

    The classifier accepts either a mapping or a simple object with attributes.
    It uses duck typing so that it can be plugged into the current evaluator
    without forcing a rigid trace schema immediately.
    """

    _EXFILTRATION_HINTS = (
        "exfiltrate",
        "exfiltration",
        "leak",
        "steal",
        "send confidential",
        "email contents",
        "export secret",
        "dump secret",
        "copy secret",
    )

    _DELEGATION_HINTS = (
        "delegate",
        "delegation",
        "approve",
        "approval",
        "grant access",
        "temporary permission",
        "escalate privilege",
    )

    _READ_ONLY_HINTS = (
        "summarise",
        "summarize",
        "read",
        "inspect",
        "report",
        "answer question",
        "search",
        "retrieve",
        "classify",
    )

    _WRITE_HINTS = (
        "write",
        "send",
        "modify",
        "delete",
        "update",
        "post",
        "commit",
        "create",
        "transfer",
        "deploy",
    )

    def classify(self, trace: Any) -> TraceClassification:
        trace_id = self._first_text(trace, "trace_id", "id", "traceId")
        task_name = self._first_text(trace, "task_name", "task", "goal", "objective", "name")
        environment_name = self._first_text(trace, "environment_name", "environment", "scenario", "env")

        task_text = self._collect_text(trace)
        labels = set(self._collect_labels(trace))

        security_outcome = self._classify_security_outcome(trace, task_text, labels)
        utility_outcome = self._classify_utility_outcome(trace, task_text, labels, security_outcome)
        task_family = self._classify_task_family(trace, task_text, labels, security_outcome, utility_outcome)

        reason = self._build_reason(task_family, security_outcome, utility_outcome, trace, task_text, labels)

        return TraceClassification(
            trace_id=trace_id,
            task_name=task_name,
            environment_name=environment_name,
            task_family=task_family,
            security_outcome=security_outcome,
            utility_outcome=utility_outcome,
            labels=frozenset(labels),
            reason=reason,
        )

    def classify_many(self, traces: Sequence[Any]) -> list[TraceClassification]:
        return [self.classify(trace) for trace in traces]

    def _classify_security_outcome(
        self,
        trace: Any,
        task_text: str,
        labels: set[str],
    ) -> SecurityOutcome:
        if self._flag(trace, "incomplete", "depth_bound_reached", "truncated", "partial"):
            return SecurityOutcome.INCOMPLETE

        if self._flag(
            trace,
            "security_violation",
            "privilege_escalation_succeeded",
            "unauthorised_action_succeeded",
            "unauthorized_action_succeeded",
            "exfiltration_succeeded",
            "policy_broken",
        ):
            return SecurityOutcome.VIOLATION

        if self._flag(
            trace,
            "blocked",
            "policy_denied",
            "action_blocked",
            "privilege_escalation_blocked",
            "unauthorised_action_blocked",
            "unauthorized_action_blocked",
            "exfiltration_blocked",
        ):
            return SecurityOutcome.BLOCKED

        if self._contains_any(task_text, self._EXFILTRATION_HINTS) or "blocked exfiltration" in labels:
            if self._flag(trace, "exfiltration_attempted", "exfiltration_requested"):
                return SecurityOutcome.BLOCKED

        if self._flag(trace, "completed", "task_completed", "goal_reached", "success"):
            return SecurityOutcome.SECURE

        if labels & {"secure", "safe", "allowed"}:
            return SecurityOutcome.SECURE

        return SecurityOutcome.UNKNOWN

    def _classify_utility_outcome(
        self,
        trace: Any,
        task_text: str,
        labels: set[str],
        security_outcome: SecurityOutcome,
    ) -> UtilityOutcome:
        if security_outcome == SecurityOutcome.INCOMPLETE:
            return UtilityOutcome.TASK_FAILED

        if self._flag(trace, "completed", "task_completed", "goal_reached", "success"):
            return UtilityOutcome.TASK_COMPLETED

        if self._flag(trace, "blocked", "policy_denied", "action_blocked"):
            return UtilityOutcome.TASK_BLOCKED

        if labels & {"blocked", "denied"}:
            return UtilityOutcome.TASK_BLOCKED

        if self._contains_any(task_text, self._EXFILTRATION_HINTS) and security_outcome == SecurityOutcome.BLOCKED:
            return UtilityOutcome.TASK_BLOCKED

        if self._flag(trace, "failed", "task_failed", "error", "exception"):
            return UtilityOutcome.TASK_FAILED

        return UtilityOutcome.UNKNOWN

    def _classify_task_family(
        self,
        trace: Any,
        task_text: str,
        labels: set[str],
        security_outcome: SecurityOutcome,
        utility_outcome: UtilityOutcome,
    ) -> TaskFamily:
        influencer_count = self._int(trace, "influencer_count", "num_influencers", "principal_count")
        if influencer_count is not None and influencer_count > 1:
            return TaskFamily.CROSS_PRINCIPAL

        if self._contains_any(task_text, self._EXFILTRATION_HINTS) or "exfiltration" in labels:
            return TaskFamily.EXFILTRATION_ATTEMPT

        if self._contains_any(task_text, self._DELEGATION_HINTS) or "delegation" in labels:
            return TaskFamily.DELEGATION_REQUIRED

        if self._contains_any(task_text, self._WRITE_HINTS) or "write" in labels:
            return TaskFamily.AUTHORISED_WRITE

        if self._contains_any(task_text, self._READ_ONLY_HINTS) or "read" in labels:
            return TaskFamily.READ_ONLY

        if security_outcome == SecurityOutcome.INCOMPLETE:
            return TaskFamily.MIXED_INFLUENCE

        if security_outcome == SecurityOutcome.VIOLATION and utility_outcome == UtilityOutcome.TASK_COMPLETED:
            return TaskFamily.MIXED_INFLUENCE

        return TaskFamily.UNKNOWN

    def _build_reason(
        self,
        task_family: TaskFamily,
        security_outcome: SecurityOutcome,
        utility_outcome: UtilityOutcome,
        trace: Any,
        task_text: str,
        labels: set[str],
    ) -> str:
        reasons: list[str] = []

        if task_family != TaskFamily.UNKNOWN:
            reasons.append(f"task_family={task_family.value}")

        reasons.append(f"security={security_outcome.value}")
        reasons.append(f"utility={utility_outcome.value}")

        if self._flag(trace, "depth_bound_reached", "truncated"):
            reasons.append("trace reached exploration bound")

        if self._flag(trace, "security_violation", "privilege_escalation_succeeded", "exfiltration_succeeded"):
            reasons.append("trace includes successful unauthorised behaviour")

        if self._flag(trace, "blocked", "policy_denied", "action_blocked"):
            reasons.append("trace includes policy block")

        if labels:
            reasons.append(f"labels={sorted(labels)!r}")

        if not reasons and task_text:
            reasons.append(task_text[:160])

        return "; ".join(reasons)

    def _collect_text(self, trace: Any) -> str:
        parts: list[str] = []

        for key in (
            "task_name",
            "task",
            "goal",
            "objective",
            "name",
            "description",
            "summary",
            "scenario",
            "environment_name",
        ):
            value = self._first_text(trace, key)
            if value:
                parts.append(value)

        for key in ("labels", "tags", "task_labels"):
            values = self._iter_values(trace, key)
            if values:
                parts.extend(str(v) for v in values if v is not None)

        events = self._iter_values(trace, "events", "trace_events", "steps", "actions")
        for event in events:
            if isinstance(event, str):
                parts.append(event)
                continue
            if isinstance(event, Mapping):
                for key in ("type", "name", "action", "label", "description", "message", "role"):
                    value = event.get(key)
                    if isinstance(value, str):
                        parts.append(value)
            else:
                for key in ("type", "name", "action", "label", "description", "message", "role"):
                    value = getattr(event, key, None)
                    if isinstance(value, str):
                        parts.append(value)

        return " ".join(parts).lower()

    def _collect_labels(self, trace: Any) -> list[str]:
        labels: list[str] = []
        for key in ("labels", "tags", "task_labels", "classification_labels"):
            values = self._iter_values(trace, key)
            for value in values:
                if value is None:
                    continue
                labels.append(str(value).strip().lower())
        return [label for label in labels if label]

    def _flag(self, trace: Any, *names: str) -> bool:
        for name in names:
            value = self._value(trace, name)
            if isinstance(value, bool):
                if value:
                    return True
            elif value is not None:
                if str(value).strip().lower() in {"1", "true", "yes", "y", "on", "completed", "blocked", "success"}:
                    return True
        return False

    def _int(self, trace: Any, *names: str) -> int | None:
        for name in names:
            value = self._value(trace, name)
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        return None

    def _first_text(self, trace: Any, *names: str) -> str | None:
        for name in names:
            value = self._value(trace, name)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _iter_values(self, trace: Any, *names: str) -> list[Any]:
        values: list[Any] = []
        for name in names:
            value = self._value(trace, name)
            if value is None:
                continue
            if isinstance(value, (list, tuple, set, frozenset)):
                values.extend(list(value))
            else:
                values.append(value)
        return values

    def _value(self, obj: Any, name: str) -> Any:
        if isinstance(obj, Mapping):
            if name in obj:
                return obj[name]
            return None
        return getattr(obj, name, None)

    @staticmethod
    def _contains_any(text: str, phrases: Sequence[str]) -> bool:
        return any(phrase in text for phrase in phrases)


DEFAULT_TRACE_CLASSIFIER = TraceClassifier()


def classify_trace(trace: Any) -> TraceClassification:
    """Classify a single trace using the default classifier."""
    return DEFAULT_TRACE_CLASSIFIER.classify(trace)


def classify_traces(traces: Sequence[Any]) -> list[TraceClassification]:
    """Classify multiple traces using the default classifier."""
    return DEFAULT_TRACE_CLASSIFIER.classify_many(traces)


def group_classifications(
    classifications: Sequence[TraceClassification],
) -> dict[tuple[TaskFamily, SecurityOutcome, UtilityOutcome], list[TraceClassification]]:
    """Group classifications by the tuple used for statistics reporting."""
    grouped: dict[tuple[TaskFamily, SecurityOutcome, UtilityOutcome], list[TraceClassification]] = {}
    for classification in classifications:
        key = (
            classification.task_family,
            classification.security_outcome,
            classification.utility_outcome,
        )
        grouped.setdefault(key, []).append(classification)
    return grouped
