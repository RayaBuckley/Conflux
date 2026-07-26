"""Environment catalogue and suite definitions for SLED.

This module defines reusable environment scenarios that can be iterated by the
evaluator. It supports both:
- a suite of distinct environments, and
- an optional superset environment that contains multiple scenarios.

The purpose of this layer is to keep environment construction declarative and
stable so that trace exploration, task classification, and reporting can all
share the same scenario metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .task_sets import ALL_TASKS, RepresentativeTask, get_task


class EnvironmentKind(str, Enum):
    """High-level kind of environment."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    SUPERNET = "supernet"
    BENCHMARK = "benchmark"
    CUSTOM = "custom"


@dataclass(frozen=True)
class EnvironmentScenario:
    """A single evaluation scenario within SLED."""

    id: str
    name: str
    description: str

    kind: EnvironmentKind
    task_ids: tuple[str, ...] = field(default_factory=tuple)

    principals: tuple[str, ...] = field(default_factory=tuple)
    data_items: tuple[str, ...] = field(default_factory=tuple)
    tools: tuple[str, ...] = field(default_factory=tuple)

    access_control_backend: str = "abstract"
    policy_profile: str = "default"

    max_depth: int = 3
    max_traces: int | None = None

    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def tasks(self) -> tuple[RepresentativeTask, ...]:
        """Return the representative tasks attached to this scenario."""
        resolved: list[RepresentativeTask] = []
        for task_id in self.task_ids:
            try:
                resolved.append(get_task(task_id))
            except KeyError:
                continue
        return tuple(resolved)

    @property
    def task_names(self) -> tuple[str, ...]:
        """Return the names of tasks attached to this scenario."""
        return tuple(task.name for task in self.tasks)

    def has_task(self, task_id: str) -> bool:
        """Return True if the scenario includes a task."""
        return task_id in self.task_ids

    def with_task_ids(self, task_ids: Sequence[str]) -> "EnvironmentScenario":
        """Return a copy of the scenario with different task identifiers."""
        return EnvironmentScenario(
            id=self.id,
            name=self.name,
            description=self.description,
            kind=self.kind,
            task_ids=tuple(task_ids),
            principals=self.principals,
            data_items=self.data_items,
            tools=self.tools,
            access_control_backend=self.access_control_backend,
            policy_profile=self.policy_profile,
            max_depth=self.max_depth,
            max_traces=self.max_traces,
            labels=self.labels,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class EnvironmentSuite:
    """A collection of scenarios evaluated together."""

    id: str
    name: str
    description: str
    scenarios: tuple[EnvironmentScenario, ...] = field(default_factory=tuple)
    labels: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __iter__(self) -> Iterator[EnvironmentScenario]:
        return iter(self.scenarios)

    def __len__(self) -> int:
        return len(self.scenarios)

    def scenario_ids(self) -> tuple[str, ...]:
        """Return all scenario identifiers in the suite."""
        return tuple(s.id for s in self.scenarios)

    def get_scenario(self, scenario_id: str) -> EnvironmentScenario:
        """Return a scenario by identifier."""
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        raise KeyError(scenario_id)

    def extend(self, extra: Sequence[EnvironmentScenario]) -> "EnvironmentSuite":
        """Return a new suite with additional scenarios appended."""
        return EnvironmentSuite(
            id=self.id,
            name=self.name,
            description=self.description,
            scenarios=tuple(self.scenarios) + tuple(extra),
            labels=self.labels,
            metadata=self.metadata,
        )


#
# Canonical scenario catalogue
#

READ_ONLY_SCENARIO = EnvironmentScenario(
    id="read_only_basic",
    name="Read-only basic environment",
    description=(
        "A minimal environment in which a requester can read already-authorised "
        "data and produce a summary."
    ),
    kind=EnvironmentKind.SMALL,
    task_ids=("read_summary", "document_search"),
    principals=("alice", "bob", "assistant"),
    data_items=("public_docs", "confidential_notes"),
    tools=("search", "summarise"),
    access_control_backend="abstract",
    policy_profile="read_only",
    max_depth=3,
    labels=frozenset({"read", "summary", "baseline"}),
)

AUTHORISED_WRITE_SCENARIO = EnvironmentScenario(
    id="authorised_write_basic",
    name="Authorised write environment",
    description=(
        "An environment where some actions are authorised, but only within the "
        "intersection of all influencing principals."
    ),
    kind=EnvironmentKind.SMALL,
    task_ids=("authorised_email", "authorised_modification"),
    principals=("alice", "bob", "assistant"),
    data_items=("draft_email", "editable_record"),
    tools=("email", "editor", "filesystem"),
    access_control_backend="abstract",
    policy_profile="authorised_write",
    max_depth=3,
    labels=frozenset({"write", "baseline"}),
)

CROSS_PRINCIPAL_SCENARIO = EnvironmentScenario(
    id="cross_principal_analysis",
    name="Cross-principal analysis environment",
    description=(
        "Multiple principals contribute information that must be analysed "
        "without exceeding the resulting authority intersection."
    ),
    kind=EnvironmentKind.MEDIUM,
    task_ids=("cross_principal_analysis",),
    principals=("alice", "bob", "carol", "assistant"),
    data_items=("alice_doc", "bob_doc", "carol_doc"),
    tools=("search", "analysis", "report"),
    access_control_backend="abstract",
    policy_profile="multi_principal",
    max_depth=3,
    labels=frozenset({"multi_principal", "analysis"}),
)

EXFILTRATION_SCENARIO = EnvironmentScenario(
    id="exfiltration_attack",
    name="Exfiltration attack environment",
    description=(
        "A scenario designed to test whether the defence blocks disclosure of "
        "information that is not authorised for the requester."
    ),
    kind=EnvironmentKind.MEDIUM,
    task_ids=("exfiltration", "privilege_escalation"),
    principals=("alice", "bob", "assistant"),
    data_items=("secret_plan", "restricted_message"),
    tools=("email", "filesystem", "chat"),
    access_control_backend="abstract",
    policy_profile="attack",
    max_depth=3,
    labels=frozenset({"attack", "security"}),
)

DELEGATION_SCENARIO = EnvironmentScenario(
    id="delegation_required",
    name="Delegation-required workflow",
    description=(
        "A workflow that cannot complete without an explicit delegation or "
        "policy transition."
    ),
    kind=EnvironmentKind.MEDIUM,
    task_ids=("delegated_workflow",),
    principals=("manager", "staff", "assistant"),
    data_items=("approval_request", "restricted_resource"),
    tools=("approval", "filesystem", "workflow"),
    access_control_backend="abstract",
    policy_profile="delegation",
    max_depth=3,
    labels=frozenset({"delegation", "workflow"}),
)

BENCHMARK_SUPERSET_SCENARIO = EnvironmentScenario(
    id="benchmark_superset",
    name="Benchmark superset environment",
    description=(
        "A broader environment that contains the representative tasks used "
        "across all standard scenarios."
    ),
    kind=EnvironmentKind.SUPERNET,
    task_ids=tuple(task.id for task in ALL_TASKS),
    principals=("alice", "bob", "carol", "dave", "assistant", "service_account"),
    data_items=(
        "public_docs",
        "alice_doc",
        "bob_doc",
        "carol_doc",
        "restricted_message",
        "secret_plan",
        "editable_record",
        "approval_request",
    ),
    tools=("search", "summarise", "email", "filesystem", "analysis", "approval"),
    access_control_backend="abstract",
    policy_profile="superset",
    max_depth=3,
    labels=frozenset({"superset", "representative"}),
    metadata={
        "includes_attack_tasks": True,
        "includes_secure_tasks": True,
        "includes_delegation": True,
    },
)


DEFAULT_ENVIRONMENT_SUITE = EnvironmentSuite(
    id="default_suite",
    name="Default SLED suite",
    description=(
        "A representative suite of environments covering secure tasks, "
        "cross-principal workflows, attacks, and delegation."
    ),
    scenarios=(
        READ_ONLY_SCENARIO,
        AUTHORISED_WRITE_SCENARIO,
        CROSS_PRINCIPAL_SCENARIO,
        EXFILTRATION_SCENARIO,
        DELEGATION_SCENARIO,
    ),
    labels=frozenset({"default", "representative"}),
)


def all_environment_scenarios() -> tuple[EnvironmentScenario, ...]:
    """Return every built-in environment scenario."""
    return DEFAULT_ENVIRONMENT_SUITE.scenarios


def get_environment_scenario(scenario_id: str) -> EnvironmentScenario:
    """Return a built-in scenario by identifier."""
    return DEFAULT_ENVIRONMENT_SUITE.get_scenario(scenario_id)


def iter_environment_scenarios(
    suite: EnvironmentSuite | None = None,
) -> Iterable[EnvironmentScenario]:
    """Iterate through scenarios from a suite or the default suite."""
    return suite.scenarios if suite is not None else DEFAULT_ENVIRONMENT_SUITE.scenarios


def benchmark_superset_environment() -> EnvironmentScenario:
    """Return the built-in superset environment."""
    return BENCHMARK_SUPERSET_SCENARIO


def suite_for_tasks(
    task_ids: Sequence[str],
    *,
    scenario_id: str = "custom_suite",
    name: str = "Custom task suite",
    description: str = "A suite constructed from an explicit set of task identifiers.",
    kind: EnvironmentKind = EnvironmentKind.CUSTOM,
    principals: Sequence[str] = ("assistant",),
    data_items: Sequence[str] = (),
    tools: Sequence[str] = (),
    access_control_backend: str = "abstract",
    policy_profile: str = "custom",
    max_depth: int = 3,
) -> EnvironmentSuite:
    """Construct a suite from a chosen set of task identifiers."""
    scenario = EnvironmentScenario(
        id=f"{scenario_id}_scenario",
        name=name,
        description=description,
        kind=kind,
        task_ids=tuple(task_ids),
        principals=tuple(principals),
        data_items=tuple(data_items),
        tools=tuple(tools),
        access_control_backend=access_control_backend,
        policy_profile=policy_profile,
        max_depth=max_depth,
    )

    return EnvironmentSuite(
        id=scenario_id,
        name=name,
        description=description,
        scenarios=(scenario,),
        labels=frozenset({"custom"}),
    )


def suite_for_environment_kind(
    kind: EnvironmentKind,
) -> tuple[EnvironmentScenario, ...]:
    """Return built-in scenarios matching a given kind."""
    return tuple(
        scenario
        for scenario in DEFAULT_ENVIRONMENT_SUITE.scenarios
        if scenario.kind == kind
    )


def scenario_index(
    scenarios: Sequence[EnvironmentScenario],
) -> dict[str, EnvironmentScenario]:
    """Create a dictionary keyed by scenario identifier."""
    return {scenario.id: scenario for scenario in scenarios}


def task_ids_for_scenario(
    scenario: EnvironmentScenario,
) -> tuple[str, ...]:
    """Return task identifiers for a scenario."""
    return scenario.task_ids
