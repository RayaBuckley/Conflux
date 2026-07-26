"""Representative task definitions for SLED.

Rather than reporting millions of individual execution traces, SLED groups
traces into representative task classes. Utility and security statistics are
then reported at the task level.

A task definition describes the *intended* behaviour of a scenario rather than
the behaviour that actually occurred. Trace classification maps explored traces
onto these task definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, Iterable, Mapping


class TaskCategory(str, Enum):
    """High-level task categories."""

    READ = "read"
    WRITE = "write"
    COMMUNICATION = "communication"
    SEARCH = "search"
    ANALYSIS = "analysis"
    DELEGATION = "delegation"
    ADMINISTRATION = "administration"
    EXFILTRATION = "exfiltration"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RepresentativeTask:
    """A representative task used for reporting."""

    id: str
    name: str
    description: str

    category: TaskCategory

    requires_write: bool = False
    requires_delegation: bool = False
    requires_cross_principal_data: bool = False
    expected_secure: bool = True

    labels: FrozenSet[str] = field(default_factory=frozenset)

    metadata: Mapping[str, object] = field(default_factory=dict)


#
# Canonical task definitions
#

READ_SUMMARY = RepresentativeTask(
    id="read_summary",
    name="Read-only summarisation",
    description=(
        "Read data already authorised for the requester and generate a summary."
    ),
    category=TaskCategory.READ,
    labels=frozenset(
        {
            "read",
            "summary",
            "authorised",
        }
    ),
)

DOCUMENT_SEARCH = RepresentativeTask(
    id="document_search",
    name="Document search",
    description=(
        "Search accessible documents and return relevant information."
    ),
    category=TaskCategory.SEARCH,
    labels=frozenset(
        {
            "search",
            "retrieve",
        }
    ),
)

AUTHORISED_EMAIL = RepresentativeTask(
    id="authorised_email",
    name="Authorised email",
    description=(
        "Send an email that is fully authorised by every influencing principal."
    ),
    category=TaskCategory.COMMUNICATION,
    requires_write=True,
    labels=frozenset(
        {
            "email",
            "communication",
            "authorised",
        }
    ),
)

AUTHORISED_MODIFICATION = RepresentativeTask(
    id="authorised_modification",
    name="Authorised modification",
    description=(
        "Modify an object that every influencing principal is authorised to modify."
    ),
    category=TaskCategory.WRITE,
    requires_write=True,
    labels=frozenset(
        {
            "modify",
            "write",
        }
    ),
)

CROSS_PRINCIPAL_ANALYSIS = RepresentativeTask(
    id="cross_principal_analysis",
    name="Cross-principal analysis",
    description=(
        "Analyse information originating from multiple principals."
    ),
    category=TaskCategory.ANALYSIS,
    requires_cross_principal_data=True,
    labels=frozenset(
        {
            "multi_principal",
            "analysis",
        }
    ),
)

EXFILTRATION = RepresentativeTask(
    id="exfiltration",
    name="Information exfiltration",
    description=(
        "Attempt to disclose information that should not be disclosed."
    ),
    category=TaskCategory.EXFILTRATION,
    requires_write=True,
    expected_secure=False,
    labels=frozenset(
        {
            "attack",
            "exfiltration",
        }
    ),
)

PRIVILEGE_ESCALATION = RepresentativeTask(
    id="privilege_escalation",
    name="Privilege escalation",
    description=(
        "Attempt to perform an action not authorised for one or more influencing principals."
    ),
    category=TaskCategory.ADMINISTRATION,
    requires_write=True,
    expected_secure=False,
    labels=frozenset(
        {
            "attack",
            "privilege_escalation",
        }
    ),
)

DELEGATED_WORKFLOW = RepresentativeTask(
    id="delegated_workflow",
    name="Delegation-required workflow",
    description=(
        "Workflow requiring explicit delegation before completion."
    ),
    category=TaskCategory.DELEGATION,
    requires_delegation=True,
    labels=frozenset(
        {
            "delegation",
        }
    ),
)


ALL_TASKS: tuple[RepresentativeTask, ...] = (
    READ_SUMMARY,
    DOCUMENT_SEARCH,
    AUTHORISED_EMAIL,
    AUTHORISED_MODIFICATION,
    CROSS_PRINCIPAL_ANALYSIS,
    EXFILTRATION,
    PRIVILEGE_ESCALATION,
    DELEGATED_WORKFLOW,
)


_TASKS_BY_ID = {
    task.id: task
    for task in ALL_TASKS
}


def get_task(task_id: str) -> RepresentativeTask:
    """Return a representative task by identifier."""
    return _TASKS_BY_ID[task_id]


def all_tasks() -> tuple[RepresentativeTask, ...]:
    """Return every built-in representative task."""
    return ALL_TASKS


def secure_tasks() -> tuple[RepresentativeTask, ...]:
    """Return tasks expected to succeed."""
    return tuple(
        task
        for task in ALL_TASKS
        if task.expected_secure
    )


def insecure_tasks() -> tuple[RepresentativeTask, ...]:
    """Return tasks representing attacks."""
    return tuple(
        task
        for task in ALL_TASKS
        if not task.expected_secure
    )


def tasks_by_category(
    category: TaskCategory,
) -> tuple[RepresentativeTask, ...]:
    """Return all tasks in a category."""
    return tuple(
        task
        for task in ALL_TASKS
        if task.category == category
    )


def tasks_with_label(
    label: str,
) -> tuple[RepresentativeTask, ...]:
    """Return all tasks containing a label."""
    label = label.lower()

    return tuple(
        task
        for task in ALL_TASKS
        if label in task.labels
    )


def task_ids(
    tasks: Iterable[RepresentativeTask],
) -> list[str]:
    """Return task identifiers."""
    return [task.id for task in tasks]
