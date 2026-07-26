"""
ITES security properties.

This module defines first-class security properties for ITES runs.

The goal is to separate:
- the execution of the defence,
- the evidence gathered during execution, and
- the properties that the defence is expected to satisfy.

That separation is important for benchmark reporting, because SLED should be
able to ask which properties held for a given run instead of relying only on a
single opaque pass/fail label.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import FrozenSet, Iterable

from .state import ExecutionState


@dataclass(frozen=True, slots=True)
class PropertyResult:
    """
    Result of evaluating a security property.

    Attributes
    ----------
    name:
        Stable property identifier.

    holds:
        Whether the property was satisfied.

    details:
        Human-readable explanation.

    evidence:
        Short evidence strings that can be surfaced in reports.
    """

    name: str
    holds: bool
    details: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)


class SecurityProperty(ABC):
    """
    Base interface for ITES security properties.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Stable identifier for the property.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, state: ExecutionState) -> PropertyResult:
        """
        Evaluate the property against a completed execution state.
        """
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class BoundedLLMCalls(SecurityProperty):
    """
    Property stating that the defence stayed within its LLM budget.
    """

    @property
    def name(self) -> str:
        return "bounded_llm_calls"

    def evaluate(self, state: ExecutionState) -> PropertyResult:
        holds = state.llm_calls_used <= state.max_llm_calls
        return PropertyResult(
            name="bounded_llm_calls",
            holds=holds,
            details=(
                f"Used {state.llm_calls_used} LLM call(s) with limit "
                f"{state.max_llm_calls}."
            ),
            evidence=(
                f"llm_calls_used={state.llm_calls_used}",
                f"max_llm_calls={state.max_llm_calls}",
            ),
        )


@dataclass(frozen=True, slots=True)
class NoActionOverlap(SecurityProperty):
    """
    Property stating that a proposal was not both declared and blocked.

    This is a lightweight consistency property for the execution trace.
    """

    @property
    def name(self) -> str:
        return "no_action_overlap"

    def evaluate(self, state: ExecutionState) -> PropertyResult:
        overlap = state.declared_actions & state.blocked_actions
        holds = len(overlap) == 0
        return PropertyResult(
            name="no_action_overlap",
            holds=holds,
            details="Declared and blocked action sets are disjoint.",
            evidence=(f"overlap_size={len(overlap)}",),
        )


@dataclass(frozen=True, slots=True)
class TraceRecorded(SecurityProperty):
    """
    Property stating that the run produced an execution trace.

    This is useful for benchmark reporting and debugging, even before richer
    semantic checks are implemented.
    """

    @property
    def name(self) -> str:
        return "trace_recorded"

    def evaluate(self, state: ExecutionState) -> PropertyResult:
        step_count = len(state.trace.steps)
        holds = step_count > 0 or state.llm_calls_used == 0
        return PropertyResult(
            name="trace_recorded",
            holds=holds,
            details="The run produced a trace of execution steps.",
            evidence=(f"step_count={step_count}",),
        )


@dataclass(frozen=True, slots=True)
class PropertySuite:
    """
    A fixed set of properties to evaluate for a run.
    """

    properties: FrozenSet[SecurityProperty] = field(default_factory=frozenset)

    def evaluate(self, state: ExecutionState) -> tuple[PropertyResult, ...]:
        """
        Evaluate every property in the suite.
        """
        return tuple(property_.evaluate(state) for property_ in sorted(
            self.properties,
            key=lambda prop: prop.name,
        ))


def evaluate_properties(
    state: ExecutionState,
    properties: Iterable[SecurityProperty],
) -> tuple[PropertyResult, ...]:
    """
    Convenience helper for evaluating a collection of properties.
    """
    return tuple(
        property_.evaluate(state)
        for property_ in sorted(properties, key=lambda prop: prop.name)
    )
