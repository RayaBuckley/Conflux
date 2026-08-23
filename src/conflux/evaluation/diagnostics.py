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


__all__ = [
    "BranchClassification",
    "DIAGNOSTIC_SCHEMA_VERSION",
    "DiagnosticCategory",
    "DiagnosticConfig",
    "DiagnosticReport",
    "classify_branches",
]
