"""Structured task-level results for SLED.

This module sits between raw trace classification and higher-level reporting.
It normalises the outcome of a single explored trace into a task-aware record
that can be aggregated across environments, defences, and benchmark runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .task_classification import (
    SecurityOutcome,
    TaskFamily,
    TraceClassification,
    UtilityOutcome,
)
from .task_sets import RepresentativeTask, TaskCategory, get_task


@dataclass(frozen=True)
class TaskResult:
    """A normalised result for one trace against one representative task."""

    trace_id: str | None
    task_id: str
    task_name: str
    task_family: TaskFamily
    environment_name: str | None

    security_outcome: SecurityOutcome
    utility_outcome: UtilityOutcome

    success: bool = False
    blocked: bool = False
    violation: bool = False
    incomplete: bool = False

    trace_counted: bool = True
    task_counted: bool = True

    explored_steps: int | None = None
    max_depth_reached: bool = False

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    reason: str = ""

    @property
    def is_secure(self) -> bool:
        return self.security_outcome == SecurityOutcome.SECURE

    @property
    def is_blocked(self) -> bool:
        return self.security_outcome == SecurityOutcome.BLOCKED

    @property
    def is_violation(self) -> bool:
        return self.security_outcome == SecurityOutcome.VIOLATION

    @property
    def is_incomplete(self) -> bool:
        return self.security_outcome == SecurityOutcome.INCOMPLETE

    @property
    def is_task_success(self) -> bool:
        return self.success and not self.violation and not self.incomplete

    @classmethod
    def from_classification(
        cls,
        classification: TraceClassification,
        task: RepresentativeTask | None = None,
        *,
        success: bool | None = None,
        blocked: bool | None = None,
        violation: bool | None = None,
        incomplete: bool | None = None,
        explored_steps: int | None = None,
        max_depth_reached: bool = False,
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> "TaskResult":
        """Create a task result from a trace classification.

        If a representative task is not supplied, the task id is inferred from
        the classification task name when possible, otherwise a generic unknown
        task is used.
        """

        resolved_task = task
        if resolved_task is None:
            resolved_task = _infer_task_from_classification(classification)

        resolved_success = (
            success
            if success is not None
            else classification.utility_outcome == UtilityOutcome.TASK_COMPLETED
        )
        resolved_blocked = (
            blocked
            if blocked is not None
            else classification.security_outcome == SecurityOutcome.BLOCKED
            or classification.utility_outcome == UtilityOutcome.TASK_BLOCKED
        )
        resolved_violation = (
            violation
            if violation is not None
            else classification.security_outcome == SecurityOutcome.VIOLATION
        )
        resolved_incomplete = (
            incomplete
            if incomplete is not None
            else classification.security_outcome == SecurityOutcome.INCOMPLETE
        )

        return cls(
            trace_id=classification.trace_id,
            task_id=resolved_task.id,
            task_name=resolved_task.name,
            task_family=classification.task_family,
            environment_name=classification.environment_name,
            security_outcome=classification.security_outcome,
            utility_outcome=classification.utility_outcome,
            success=resolved_success,
            blocked=resolved_blocked,
            violation=resolved_violation,
            incomplete=resolved_incomplete,
            explored_steps=explored_steps,
            max_depth_reached=max_depth_reached,
            labels=classification.labels,
            metadata=metadata or {},
            created_at=created_at,
            reason=classification.reason,
        )

    @classmethod
    def from_trace(
        cls,
        trace: Any,
        classifier: Any,
        *,
        task: RepresentativeTask | None = None,
        success: bool | None = None,
        blocked: bool | None = None,
        violation: bool | None = None,
        incomplete: bool | None = None,
        explored_steps: int | None = None,
        max_depth_reached: bool = False,
        metadata: Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> "TaskResult":
        """Classify a trace and convert it directly into a task result."""
        classification = classifier.classify(trace)
        return cls.from_classification(
            classification,
            task=task,
            success=success,
            blocked=blocked,
            violation=violation,
            incomplete=incomplete,
            explored_steps=explored_steps,
            max_depth_reached=max_depth_reached,
            metadata=metadata,
            created_at=created_at,
        )


def _infer_task_from_classification(
    classification: TraceClassification,
) -> RepresentativeTask:
    """Resolve a representative task using only classification metadata."""
    task_name = (classification.task_name or "").strip().lower()

    # Try exact registered identifiers first.
    if task_name:
        try:
            return get_task(task_name)
        except KeyError:
            pass

    # Try a looser match against known task names.
    for task_id in (
        "read_summary",
        "document_search",
        "authorised_email",
        "authorised_modification",
        "cross_principal_analysis",
        "exfiltration",
        "privilege_escalation",
        "delegated_workflow",
    ):
        try:
            task = get_task(task_id)
        except KeyError:
            continue

        if task.name.lower() in task_name:
            return task

    # Fallback to a generic synthetic task.
    return RepresentativeTask(
        id="unknown",
        name=classification.task_name or "Unknown task",
        description="Task could not be resolved from classification metadata.",
        category=_fallback_category(classification.task_family),
        expected_secure=classification.security_outcome != SecurityOutcome.VIOLATION,
        labels=classification.labels,
    )


def _fallback_category(task_family: TaskFamily) -> TaskCategory:
    """Map a task family to the closest representative task category."""
    from .task_sets import TaskCategory

    mapping = {
        TaskFamily.READ_ONLY: TaskCategory.READ,
        TaskFamily.AUTHORISED_WRITE: TaskCategory.WRITE,
        TaskFamily.CROSS_PRINCIPAL: TaskCategory.ANALYSIS,
        TaskFamily.EXFILTRATION_ATTEMPT: TaskCategory.EXFILTRATION,
        TaskFamily.DELEGATION_REQUIRED: TaskCategory.DELEGATION,
        TaskFamily.MIXED_INFLUENCE: TaskCategory.ANALYSIS,
        TaskFamily.UNKNOWN: TaskCategory.UNKNOWN,
    }
    return mapping.get(task_family, TaskCategory.UNKNOWN)


def merge_task_results(results: list[TaskResult]) -> dict[str, list[TaskResult]]:
    """Group task results by task id for downstream aggregation."""
    grouped: dict[str, list[TaskResult]] = {}
    for result in results:
        grouped.setdefault(result.task_id, []).append(result)
    return grouped
