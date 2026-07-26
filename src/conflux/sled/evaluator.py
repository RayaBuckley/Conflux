"""
Deprecated SLED evaluator implementation facade.

Canonical ownership is ``conflux.evaluation``. This implementation remains
temporarily while callers migrate and must not gain new evaluation semantics.

This module explores a bounded combinatorial search space over ITES proposal
patterns. It compresses the environment into representative equivalence
classes so search depth increases by reducing redundant data items.

The evaluator keeps the old exhaustive semantics:
- nested execution is explored combinatorially,
- primitive actions and nested LLM requests are branch points,
- the evaluator records every branch that it traverses,
- representative environments reduce redundant branching when several data
  items share the same security-relevant structure.

The evaluator does not alter the intersection rule itself; that is enforced by
the authorisation layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Callable, Iterable, Iterator, Sequence, TypeVar

from conflux.core import Artifact, Principal
from conflux.core.actions import (
    ActionVisibility,
    ClarificationRequestAction,
    DelegationAction,
    MessageUserAction,
    NestedExecutionAction,
    NoOpAction,
    PrimitiveAction,
    Proposal,
    RequestConsentAction,
    StopAction,
)
from conflux.core.permissions import normalise_permission
from conflux.evaluation.trace import TraceRecord
from conflux.ites import ITES, Guarantee, ITESReport

from .environment import Data, Environment

T = TypeVar("T")


@dataclass(slots=True)
class EvaluationResult:
    """Result of one bounded, non-exhaustive SLED evaluation.

    This is the compatibility facade used by :mod:`benchmark_runner`. New
    exhaustive experiments should use :class:`ExhaustiveEvaluator` directly.
    """

    report: ITESReport
    declared: list[Any] = field(default_factory=list)
    trace: tuple[TraceRecord, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class Evaluator:
    """Run one defence once for the benchmark runner compatibility path."""

    environment: Environment
    defence: ITES
    llm_call: Callable[[frozenset[Artifact[Any]]], frozenset[Any]]

    def run(self, initial_inputs: Iterable[Data]) -> EvaluationResult:
        declared: list[Any] = []

        def declare(item: Any) -> None:
            declared.append(item)

        report = self.defence.run(
            environment=self.environment,
            initial_inputs=frozenset(item.to_artifact() for item in initial_inputs),
            llm_call=self.llm_call,
            declare=declare,
        )
        trace = (
            TraceRecord(
                event="evaluation.completed",
                run_id=f"{self.environment.name}:one-shot",
                sequence=0,
                payload={
                    "declared_actions": len(declared),
                    "blocked_actions": len(report.blocked_actions),
                    "guarantees": {guarantee.name: guarantee.holds for guarantee in report.guarantees},
                },
            ),
        )
        return EvaluationResult(report=report, declared=declared, trace=trace)


@dataclass(frozen=True, slots=True)
class RepresentativeClass:
    """
    A group of environment items that share the same security-relevant
    authorisation structure.

    Items in the same class are behaviourally similar for exhaustive search
    purposes, so one representative can stand in for the whole class.
    """

    signature: tuple[frozenset[str], frozenset[str], bool]
    representative: Data
    members: frozenset[Data] = field(default_factory=frozenset)

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass(frozen=True, slots=True)
class RepresentativeEnvironment:
    """A compressed environment built from equivalence classes of data."""

    environment: Environment
    classes: frozenset[RepresentativeClass] = field(default_factory=frozenset)
    projection: dict[Data, Data] = field(default_factory=dict)

    @property
    def compression_factor(self) -> float:
        original = sum(len(cls.members) for cls in self.classes)
        if original == 0:
            return 1.0
        return original / max(1, len(self.environment.data))

    def project_inputs(self, inputs: Iterable[Data]) -> frozenset[Data]:
        """
        Project original inputs onto the representative environment.
        """
        return frozenset(self.projection.get(item, item) for item in inputs)


@dataclass(slots=True)
class ExhaustiveEvaluationResult:
    """Outcome of a complete exhaustive evaluation run."""

    report: ITESReport
    branches_explored: int
    terminal_branches: int
    max_depth_reached: int
    branch_option_count: int
    terminal_option_count: int
    used_representative_environment: bool
    llm_inputs: list[frozenset[Artifact[Any]]] = field(default_factory=list)
    declared: list[Any] = field(default_factory=list)
    representative_environment: RepresentativeEnvironment | None = None


def _powerset(
    items: Sequence[T],
    *,
    min_size: int = 0,
    max_size: int | None = None,
) -> Iterator[tuple[T, ...]]:
    """Yield subsets of items in increasing size order."""
    n = len(items)
    if max_size is None:
        max_size = n
    upper = min(n, max_size)
    for r in range(min_size, upper + 1):
        yield from combinations(items, r)


def _data_signature(item: Data) -> tuple[frozenset[str], frozenset[str], bool]:
    """Return the security-relevant signature for a data item."""
    authors = frozenset(author.id for author in item.authors)
    readers = frozenset(reader.id for reader in item.readers)
    return authors, readers, item.confidential


def _artifact_signature(artifact: Artifact[Any]) -> tuple[Any, ...]:
    """Return a stable signature for an artifact."""
    value = artifact.value
    if isinstance(value, Data):
        return ("data", _data_signature(value), artifact.label, artifact.confidential)
    return ("artifact", repr(value), artifact.label, artifact.confidential)


def _proposal_signature(proposal: Proposal) -> tuple[Any, ...]:
    """Return a stable signature for a proposal."""
    if isinstance(proposal, PrimitiveAction):
        resource_id = getattr(proposal.resource, "id", None) if proposal.resource is not None else None
        return (
            "primitive",
            proposal.provider_operation,
            proposal.permission.name,
            resource_id,
            proposal.visibility.value,
        )

    if isinstance(proposal, NestedExecutionAction):
        nested_sig = tuple(sorted(_artifact_signature(artifact) for artifact in proposal.nested_inputs))
        return (
            "nested",
            nested_sig,
            proposal.max_depth_hint,
            proposal.visibility.value,
        )

    if isinstance(proposal, DelegationAction):
        delegate_id = proposal.delegate_to.id if proposal.delegate_to is not None else None
        return (
            "delegation",
            delegate_id,
            proposal.scope,
            tuple(sorted(permission.name for permission in proposal.delegated_permissions)),
            proposal.visibility.value,
        )

    if isinstance(proposal, MessageUserAction):
        return ("message", proposal.message, proposal.visibility.value)

    if isinstance(proposal, ClarificationRequestAction):
        return ("clarify", proposal.prompt, proposal.visibility.value)

    if isinstance(proposal, RequestConsentAction):
        resource_id = proposal.target_resource.id if proposal.target_resource is not None else None
        return (
            "consent",
            proposal.requested_permission.name,
            resource_id,
            proposal.reason,
            proposal.visibility.value,
        )

    if isinstance(proposal, StopAction):
        return ("stop", proposal.reason, proposal.visibility.value)

    if isinstance(proposal, NoOpAction):
        return ("noop", proposal.label, proposal.visibility.value)

    return ("unknown", repr(proposal))


def _materialise_inputs(inputs: Iterable[Data]) -> frozenset[Artifact[Any]]:
    """Convert raw SLED inputs into provenance-bearing artifacts."""
    return frozenset(item.to_artifact() for item in inputs)


def compress_environment(environment: Environment) -> RepresentativeEnvironment:
    """
    Compress an environment into representative equivalence classes.

    Items with identical authors/readers/confidentiality signatures are grouped
    together. This preserves the relevant security structure while reducing
    branching.
    """
    groups: dict[tuple[frozenset[str], frozenset[str], bool], list[Data]] = {}
    for item in environment.data:
        groups.setdefault(_data_signature(item), []).append(item)

    classes: list[RepresentativeClass] = []
    representatives: set[Data] = set()
    projection: dict[Data, Data] = {}

    for signature, members in groups.items():
        representative = min(
            members,
            key=lambda d: (
                d.tag is None,
                d.tag or "",
                len(d.authors),
                len(d.readers),
            ),
        )
        representatives.add(representative)
        for member in members:
            projection[member] = representative
        classes.append(
            RepresentativeClass(
                signature=signature,
                representative=representative,
                members=frozenset(members),
            )
        )

    return RepresentativeEnvironment(
        environment=Environment(
            data=frozenset(representatives),
            name=f"{environment.name}:representative",
            metadata=dict(environment.metadata),
        ),
        classes=frozenset(classes),
        projection=projection,
    )


def _llm_inputs_readable(
    inputs: frozenset[Artifact[Any]],
    influencers: frozenset[Principal],
) -> bool:
    """
    Exact nested-call readability rule from the previous prototype.

    A nested execution request is allowed only when every current influencer
    can read every proposed input.
    """
    for artifact in inputs:
        value = artifact.value
        if not isinstance(value, Data):
            continue
        for principal in influencers:
            if principal not in value.readers:
                return False
    return True


def _build_option_space(
    atoms: Sequence[Proposal],
    *,
    max_size: int,
) -> tuple[frozenset[Proposal], ...]:
    """
    Build a deterministic, deduplicated option space from a sequence of atoms.
    """
    ordered_atoms = sorted(atoms, key=_proposal_signature)
    seen: set[tuple[Any, ...]] = set()
    options: list[frozenset[Proposal]] = []

    for combo in _powerset(ordered_atoms, min_size=0, max_size=max_size):
        option = frozenset(combo)
        signature = tuple(sorted(_proposal_signature(item) for item in option))
        if signature in seen:
            continue
        seen.add(signature)
        options.append(option)

    return tuple(options)


def _build_primitive_atoms(primitive_actions: frozenset[str]) -> tuple[PrimitiveAction, ...]:
    """
    Create primitive action atoms from a set of provider operation names.
    """
    atoms: list[PrimitiveAction] = []
    for name in sorted(primitive_actions):
        atoms.append(
            PrimitiveAction(
                permission=normalise_permission(name),
                provider_operation=name,
                visibility=ActionVisibility.INTERNAL,
            )
        )
    return tuple(atoms)


def _build_control_atoms() -> tuple[Proposal, ...]:
    """
    Create a small fixed control-action vocabulary.
    """
    return (
        MessageUserAction(
            message="message",
            visibility=ActionVisibility.USER_VISIBLE,
        ),
        ClarificationRequestAction(
            prompt="clarify",
            visibility=ActionVisibility.USER_VISIBLE,
        ),
        RequestConsentAction(
            reason="request_consent",
            visibility=ActionVisibility.USER_VISIBLE,
        ),
        DelegationAction(
            scope="delegate",
            visibility=ActionVisibility.INTERNAL,
        ),
        StopAction(
            reason="stop",
            visibility=ActionVisibility.INTERNAL,
        ),
        NoOpAction(
            label="noop",
            visibility=ActionVisibility.INTERNAL,
        ),
    )


@dataclass(slots=True)
class ExhaustiveEvaluator:
    """
    Exhaustively explore the branching behaviour of a defence across one
    environment.
    """

    defence: ITES
    primitive_actions: frozenset[str]
    max_llm_calls: int = 3
    option_width: int = 2
    terminal_option_width: int = 3
    use_representative_environment: bool = True
    max_execution_input_size: int | None = None
    include_control_actions: bool = True

    def __post_init__(self) -> None:
        if self.max_llm_calls < 1:
            raise ValueError("max_llm_calls must be at least 1")
        if self.option_width < 0:
            raise ValueError("option_width must be non-negative")
        if self.terminal_option_width < 0:
            raise ValueError("terminal_option_width must be non-negative")

    def run(
        self,
        environment: Environment,
        initial_inputs: Iterable[Data],
    ) -> ExhaustiveEvaluationResult:
        """
        Run an exhaustive search over the defence's execution tree.
        """
        representative_environment = compress_environment(environment)

        if self.use_representative_environment:
            search_environment = representative_environment.environment
            projection = representative_environment.projection
        else:
            search_environment = environment
            projection = {item: item for item in environment.data}

        selected_inputs = frozenset(initial_inputs)
        if not selected_inputs <= environment.data:
            missing = selected_inputs - environment.data
            raise ValueError(f"Initial inputs are not in the environment: {missing!r}")

        selected_inputs = frozenset(projection.get(item, item) for item in selected_inputs)
        if not selected_inputs <= search_environment.data:
            missing = selected_inputs - search_environment.data
            raise ValueError(
                f"Projected initial inputs are not in the evaluation environment: {missing!r}"
            )

        llm_inputs: list[frozenset[Artifact[Any]]] = []
        declared: list[Any] = []

        primitive_atoms = _build_primitive_atoms(self.primitive_actions)
        control_atoms = _build_control_atoms() if self.include_control_actions else ()

        execution_sources = tuple(sorted(search_environment.data, key=_data_signature))
        if self.max_execution_input_size is None:
            execution_subsets = tuple(_powerset(execution_sources, min_size=1))
        else:
            execution_subsets = tuple(
                _powerset(
                    execution_sources,
                    min_size=1,
                    max_size=self.max_execution_input_size,
                )
            )

        nested_atoms = tuple(
            NestedExecutionAction(
                nested_inputs=_materialise_inputs(subset),
                inputs=_materialise_inputs(subset),
                visibility=ActionVisibility.INTERNAL,
            )
            for subset in execution_subsets
        )

        branch_atoms = primitive_atoms + nested_atoms + control_atoms
        terminal_atoms = primitive_atoms + control_atoms

        branch_options = _build_option_space(branch_atoms, max_size=self.option_width)
        terminal_options = _build_option_space(terminal_atoms, max_size=self.terminal_option_width)

        if not branch_options:
            branch_options = (frozenset(),)
        if not terminal_options:
            terminal_options = (frozenset(),)

        decision_path: list[int] = [0] * self.max_llm_calls
        branches_explored = 0
        terminal_branches = 0
        max_depth_reached = 0
        final_report: ITESReport | None = None

        def tracked_declare(item: Any) -> None:
            declared.append(item)

        while True:
            branches_explored += 1
            terminal_branches += 1
            current_index = 0
            llm_inputs.clear()

            def branching_llm_call(inputs: frozenset[Artifact[Any]]) -> frozenset[Proposal]:
                nonlocal current_index, max_depth_reached
                llm_inputs.append(inputs)
                max_depth_reached = max(max_depth_reached, current_index + 1)

                options = (
                    terminal_options
                    if current_index >= self.max_llm_calls - 1
                    else branch_options
                )
                choice = decision_path[current_index]
                if choice >= len(options):
                    return frozenset()

                current_index += 1
                return options[choice]

            input_artifacts = _materialise_inputs(selected_inputs)

            report = self.defence.run(
                environment=search_environment,
                initial_inputs=input_artifacts,
                llm_call=branching_llm_call,
                declare=tracked_declare,
            )
            final_report = report

            if current_index == 0:
                max_depth_reached = max(max_depth_reached, 1)

            i = current_index - 1 if current_index > 0 else self.max_llm_calls - 1
            while i >= 0:
                decision_path[i] += 1
                limit = len(terminal_options) if i == self.max_llm_calls - 1 else len(branch_options)
                if decision_path[i] < limit:
                    break
                decision_path[i] = 0
                i -= 1

            if i < 0:
                break

        if final_report is None:
            final_report = ITESReport(
                guarantees=frozenset(
                    {
                        Guarantee(
                            name="no_runs_executed",
                            holds=False,
                            details="No branches were explored.",
                        )
                    }
                ),
                declared_actions=frozenset(),
                blocked_actions=frozenset(),
            )

        return ExhaustiveEvaluationResult(
            report=final_report,
            branches_explored=branches_explored,
            terminal_branches=terminal_branches,
            max_depth_reached=max_depth_reached,
            branch_option_count=len(branch_options),
            terminal_option_count=len(terminal_options),
            used_representative_environment=self.use_representative_environment,
            llm_inputs=llm_inputs.copy(),
            declared=declared.copy(),
            representative_environment=representative_environment,
        )


__all__ = [
    "EvaluationResult",
    "Evaluator",
    "ExhaustiveEvaluationResult",
    "ExhaustiveEvaluator",
    "RepresentativeClass",
    "RepresentativeEnvironment",
    "compress_environment",
]
