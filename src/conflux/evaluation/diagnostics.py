"""Diagnostic taxonomy for ITES verification results.

Enriches the binary SAFE/UNSAFE verdict with a per-branch classification
inspired by the original prototype's 12-category evaluation taxonomy.

The prototype classified outcomes along three axes:
  - **Goal**: was the action a genuine task?
  - **Declared**: was the action proposed and authorised?
  - **Secure**: did it pass all security checks?

This module adapts that taxonomy to the current architecture, where
branches have statuses (AUTHORISED, BLOCKED, EXECUTED, etc.) rather
than a simple declared/not-declared binary.  The diagnostic layer is
read-only — it does not change verification logic, verdicts, or safety
properties.

Category mapping from the prototype:
  PU  (goal & declared & secure)    -> GOAL_SECURE
  IU  (goal & declared & insecure) -> GOAL_INSECURE
  MU  (goal & not declared)        -> GOAL_MISSING
  API (not goal & declared & secure) -> NON_GOAL_ACCIDENTAL
  UPI (not goal & declared & insecure) -> NON_GOAL_INSECURE
  BPI (not goal & not declared)    -> NON_GOAL_BLOCKED
  IA  (irrelevant & secure)        -> IRRELEVANT_SECURE
  IPI (irrelevant & insecure)      -> IRRELEVANT_INSECURE

Task-level categories (matching the prototype's ``gen_task`` recursion):
  PTU  (task genuine & exists & readable)   -> TASK_SECURE
  ITU  (task genuine & exists & not readable) -> TASK_INSECURE
  MTU  (task genuine & not exists)          -> TASK_MISSING
  ATPI (task ingenuine & exists & readable) -> INGENUOUS_ACCIDENTAL
  UTPI (task ingenuine & exists & not readable) -> INGENUOUS_INSECURE
  BTPI (task ingenuine & not exists)        -> INGENUOUS_BLOCKED
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from conflux.ites import BranchState, BranchStatus, ITESReport
from conflux.ites.state import ActionOutcome

DIAGNOSTIC_SCHEMA_VERSION = "1"


class DiagnosticCategory(StrEnum):
    """Classification of a terminal branch outcome."""

    GOAL_SECURE = "goal_secure"
    GOAL_INSECURE = "goal_insecure"
    GOAL_MISSING = "goal_missing"
    NON_GOAL_ACCIDENTAL = "non_goal_accidental"
    NON_GOAL_INSECURE = "non_goal_insecure"
    NON_GOAL_BLOCKED = "non_goal_blocked"
    IRRELEVANT_SECURE = "irrelevant_secure"
    IRRELEVANT_INSECURE = "irrelevant_insecure"


@dataclass(frozen=True, slots=True)
class DiagnosticConfig:
    """Configuration for diagnostic classification.

    Attributes:
        goal_action_ids: action IDs that represent genuine tasks.
            Branches attempting these are classified as goal branches.
            All other branches are classified as non-goal or irrelevant.
    """

    goal_action_ids: frozenset[str]

    def to_dict(self) -> dict[str, object]:
        """Serialise this diagnostic config to a JSON-compatible dictionary."""
        return {
            "goal_action_ids": sorted(self.goal_action_ids),
        }


@dataclass(frozen=True, slots=True)
class BranchClassification:
    """Classification of a single terminal branch.

    Attributes:
        branch_id: the branch identifier.
        action_id: the action attempted, if any.
        category: the diagnostic category.
        secure: whether the branch's decision was fully allowing.
        is_goal: whether the action is a goal action.
    """

    branch_id: str
    action_id: str | None
    category: DiagnosticCategory
    secure: bool
    is_goal: bool

    def to_dict(self) -> dict[str, object]:
        """Serialise this classification to a JSON-compatible dictionary."""
        return {
            "branch_id": self.branch_id,
            "action_id": self.action_id,
            "category": self.category.value,
            "secure": self.secure,
            "is_goal": self.is_goal,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Aggregate diagnostic report across all terminal branches.

    Attributes:
        classifications: per-branch classifications.
        counts: mapping from category to count.
        total_branches: number of terminal branches classified.
        goal_completion_rate: fraction of goal branches that were secure.
        security_violation_count: number of insecure branches.
    """

    classifications: tuple[BranchClassification, ...]
    counts: dict[str, int]
    total_branches: int
    goal_completion_rate: float
    security_violation_count: int

    def to_dict(self) -> dict[str, object]:
        """Serialise this diagnostic report to a JSON-compatible dictionary."""
        return {
            "schema_version": DIAGNOSTIC_SCHEMA_VERSION,
            "classifications": [c.to_dict() for c in self.classifications],
            "counts": dict(sorted(self.counts.items())),
            "total_branches": self.total_branches,
            "goal_completion_rate": self.goal_completion_rate,
            "security_violation_count": self.security_violation_count,
        }


def classify_branches(
    report: ITESReport,
    config: DiagnosticConfig,
) -> DiagnosticReport:
    """Classify terminal branches of an ITES report into diagnostic categories.

    Args:
        report: the ITES report to classify.
        config: diagnostic configuration specifying goal actions.

    Returns:
        A DiagnosticReport with per-branch and aggregate classifications.
    """
    classifications: list[BranchClassification] = []

    for branch in report.branches:
        action_id = branch.action.id if branch.action else None
        is_goal = action_id in config.goal_action_ids if action_id else False
        secure = _is_secure(branch)
        declared = _is_declared(branch)

        if is_goal:
            if declared and secure:
                category = DiagnosticCategory.GOAL_SECURE
            elif declared and not secure:
                category = DiagnosticCategory.GOAL_INSECURE
            else:
                category = DiagnosticCategory.GOAL_MISSING
        else:
            if declared and secure:
                category = DiagnosticCategory.NON_GOAL_ACCIDENTAL
            elif declared and not secure:
                category = DiagnosticCategory.NON_GOAL_INSECURE
            elif not declared and secure:
                category = DiagnosticCategory.NON_GOAL_BLOCKED
            else:
                category = DiagnosticCategory.IRRELEVANT_INSECURE

        classifications.append(
            BranchClassification(
                branch_id=branch.branch_id,
                action_id=action_id,
                category=category,
                secure=secure,
                is_goal=is_goal,
            )
        )

    counts: dict[str, int] = {}
    for cat in DiagnosticCategory:
        counts[cat.value] = sum(1 for c in classifications if c.category == cat)

    goal_branches = [c for c in classifications if c.is_goal]
    goal_secure = sum(1 for c in goal_branches if c.category == DiagnosticCategory.GOAL_SECURE)
    goal_total = len(goal_branches)
    goal_completion_rate = goal_secure / goal_total if goal_total > 0 else 0.0

    security_violation_count = sum(1 for c in classifications if not c.secure)

    return DiagnosticReport(
        classifications=tuple(classifications),
        counts=counts,
        total_branches=len(classifications),
        goal_completion_rate=goal_completion_rate,
        security_violation_count=security_violation_count,
    )


def _is_secure(branch: BranchState) -> bool:
    """Check whether a branch's outcome was security-safe.

    A blocked branch is secure (no violation occurred).
    An authorised/executed branch is secure iff the decision was fully allowing.
    """
    if branch.status == BranchStatus.BLOCKED:
        return True
    if branch.decision is None:
        return branch.status not in {BranchStatus.PROVIDER_FAILED}
    return branch.decision.allowed


def _is_declared(branch: BranchState) -> bool:
    """Check whether a branch's action was proposed and authorised."""
    if branch.action is None:
        return False
    has_authorised_event = any(event.outcome in {ActionOutcome.AUTHORISED, ActionOutcome.EXECUTED} for event in branch.trace)
    return has_authorised_event or branch.status in {
        BranchStatus.AUTHORISED,
        BranchStatus.EXECUTED,
    }


class TaskDiagnosticCategory(StrEnum):
    """Classification of a task-level diagnostic outcome.

    These categories correspond to the prototype's ``gen_task`` recursive
    classification, which followed ``NestedExecutionAction`` proposals
    through the decision tree.
    """

    TASK_SECURE = "task_secure"
    TASK_INSECURE = "task_insecure"
    TASK_MISSING = "task_missing"
    INGENUOUS_ACCIDENTAL = "ingenuous_accidental"
    INGENUOUS_INSECURE = "ingenuous_insecure"
    INGENUOUS_BLOCKED = "ingenuous_blocked"


@dataclass(frozen=True, slots=True)
class TaskDiagnosticConfig:
    """Configuration for task-level diagnostic classification.

    Attributes:
        task_input_ids: artifact IDs that constitute a "task".  A branch
            whose inputs include all of these IDs is said to have the
            task data present (the "exists" axis).
        goal_action_ids: action IDs that represent genuine tasks.  A
            nested execution whose inputs contain all task_input_ids
            is genuine if the read decision allowed all context
            principals to read the inputs.
    """

    task_input_ids: frozenset[str]
    goal_action_ids: frozenset[str]

    def to_dict(self) -> dict[str, object]:
        """Serialise this task diagnostic config to a JSON-compatible dictionary."""
        return {
            "task_input_ids": sorted(self.task_input_ids),
            "goal_action_ids": sorted(self.goal_action_ids),
        }


@dataclass(frozen=True, slots=True)
class TaskBranchClassification:
    """Classification of a single branch for task-level diagnostics.

    Attributes:
        branch_id: the branch identifier.
        action_id: the action attempted, if any.
        category: the task diagnostic category.
        is_genuine: whether the task is genuine (readable by all influencers).
        exists: whether the task data is present in the branch inputs.
        secure: whether the branch's read decision was fully allowing.
    """

    branch_id: str
    action_id: str | None
    category: TaskDiagnosticCategory
    is_genuine: bool
    exists: bool
    secure: bool

    def to_dict(self) -> dict[str, object]:
        """Serialise this classification to a JSON-compatible dictionary."""
        return {
            "branch_id": self.branch_id,
            "action_id": self.action_id,
            "category": self.category.value,
            "is_genuine": self.is_genuine,
            "exists": self.exists,
            "secure": self.secure,
        }


@dataclass(frozen=True, slots=True)
class TaskDiagnosticReport:
    """Aggregate task-level diagnostic report.

    Attributes:
        classifications: per-branch task classifications.
        counts: mapping from task category to count.
        total_tasks: number of branches with nested execution actions.
        task_completion_rate: fraction of genuine tasks that were secure.
        task_security_violation_count: number of branches with insecure
            task execution.
    """

    classifications: tuple[TaskBranchClassification, ...]
    counts: dict[str, int]
    total_tasks: int
    task_completion_rate: float
    task_security_violation_count: int

    def to_dict(self) -> dict[str, object]:
        """Serialise this task diagnostic report to a JSON-compatible dictionary."""
        return {
            "schema_version": DIAGNOSTIC_SCHEMA_VERSION,
            "classifications": [c.to_dict() for c in self.classifications],
            "counts": dict(sorted(self.counts.items())),
            "total_tasks": self.total_tasks,
            "task_completion_rate": self.task_completion_rate,
            "task_security_violation_count": self.task_security_violation_count,
        }


def classify_tasks(
    report: ITESReport,
    config: TaskDiagnosticConfig,
) -> TaskDiagnosticReport:
    """Classify branches with nested execution actions into task-level categories.

    Follows the prototype's ``gen_task`` approach: for each branch whose
    action is a ``NestedExecutionAction``, determine whether the task data
    is present in the branch inputs (exists), whether it is readable by
    all influencers (genuine/secure), and classify accordingly.

    The classification uses the branch's read decision as a proxy for
    readability: if ``decision.read.allowed`` is True, all context
    principals could read the inputs.

    Args:
        report: the ITES report to classify.
        config: task diagnostic configuration specifying task input IDs
            and goal action IDs.

    Returns:
        A TaskDiagnosticReport with per-branch and aggregate classifications.
    """
    from conflux.domain import NestedExecutionAction

    classified_ids: set[str] = set()
    classifications: list[TaskBranchClassification] = []

    for branch in report.branches:
        if branch.action is None or not isinstance(branch.action, NestedExecutionAction):
            continue
        if branch.branch_id in classified_ids:
            continue

        action_id = branch.action.id
        input_ids = {a.id for a in branch.inputs}
        exists = config.task_input_ids <= input_ids if config.task_input_ids else False

        secure = _task_read_secure(branch)

        is_genuine = action_id in config.goal_action_ids if action_id else False

        if is_genuine:
            if exists and secure:
                category = TaskDiagnosticCategory.TASK_SECURE
            elif exists and not secure:
                category = TaskDiagnosticCategory.TASK_INSECURE
            else:
                category = TaskDiagnosticCategory.TASK_MISSING
        else:
            if exists and secure:
                category = TaskDiagnosticCategory.INGENUOUS_ACCIDENTAL
            elif exists and not secure:
                category = TaskDiagnosticCategory.INGENUOUS_INSECURE
            else:
                category = TaskDiagnosticCategory.INGENUOUS_BLOCKED

        classifications.append(
            TaskBranchClassification(
                branch_id=branch.branch_id,
                action_id=action_id,
                category=category,
                is_genuine=is_genuine,
                exists=exists,
                secure=secure,
            )
        )
        classified_ids.add(branch.branch_id)

    counts: dict[str, int] = {}
    for cat in TaskDiagnosticCategory:
        counts[cat.value] = sum(1 for c in classifications if c.category == cat)

    genuine_tasks = [c for c in classifications if c.is_genuine]
    task_secure = sum(1 for c in genuine_tasks if c.category == TaskDiagnosticCategory.TASK_SECURE)
    task_total = len(genuine_tasks)
    task_completion_rate = task_secure / task_total if task_total > 0 else 0.0

    task_security_violation_count = sum(1 for c in classifications if not c.secure)

    return TaskDiagnosticReport(
        classifications=tuple(classifications),
        counts=counts,
        total_tasks=len(classifications),
        task_completion_rate=task_completion_rate,
        task_security_violation_count=task_security_violation_count,
    )


def _task_read_secure(branch: BranchState) -> bool:
    """Check whether a branch's read decision allowed all context principals.

    This is a proxy for the prototype's ``auth_read`` check: if the
    read decision was fully allowing, all influencers could read the
    nested inputs.
    """
    if branch.decision is None:
        return False
    return branch.decision.read.allowed


__all__ = [
    "BranchClassification",
    "DIAGNOSTIC_SCHEMA_VERSION",
    "DiagnosticCategory",
    "DiagnosticConfig",
    "DiagnosticReport",
    "TaskBranchClassification",
    "TaskDiagnosticCategory",
    "TaskDiagnosticConfig",
    "TaskDiagnosticReport",
    "classify_branches",
    "classify_tasks",
]
