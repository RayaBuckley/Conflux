"""
ITES execution state.

This module makes the semantics of an ITES run explicit.

The mediator should transform immutable state rather than mutating local
variables. That makes the defence easier to test, easier to trace, and easier
to connect to SLED benchmark reporting.

The state objects here are intentionally generic and lightweight. They are not a
scheduler or planner; they simply capture what happened during a defence run.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, FrozenSet, Tuple

from conflux.core import Artifact, Principal, Session
from conflux.core.actions import Action

from . import Guarantee


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    """
    A single step in an ITES run.

    Attributes
    ----------
    depth:
        Recursion depth or execution nesting level.
    inputs:
        The artifacts seen at this step.
    proposals:
        The proposals returned by the LLM for this step.
    declared:
        Proposals accepted by the defence at this step.
    blocked:
        Proposals rejected by the defence at this step.
    influencers:
        Principals contributing authority at the time of the step.
    note:
        Optional human-readable explanation.
    """

    depth: int
    inputs: FrozenSet[Artifact[Any]] = field(default_factory=frozenset)
    proposals: FrozenSet[Action[Any]] = field(default_factory=frozenset)
    declared: FrozenSet[Action[Any]] = field(default_factory=frozenset)
    blocked: FrozenSet[Action[Any]] = field(default_factory=frozenset)
    influencers: FrozenSet[Principal] = field(default_factory=frozenset)
    note: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionTrace:
    """
    Immutable execution trace.

    The trace is append-only. Each modification returns a new trace instance.
    """

    steps: Tuple[ExecutionStep, ...] = field(default_factory=tuple)

    def add_step(self, step: ExecutionStep) -> "ExecutionTrace":
        """
        Return a new trace with one additional step appended.
        """
        return ExecutionTrace(steps=self.steps + (step,))

    def last(self) -> ExecutionStep | None:
        """
        Return the most recent step, if any.
        """
        return self.steps[-1] if self.steps else None

    @property
    def depth(self) -> int:
        """
        Return the number of recorded steps.
        """
        return len(self.steps)


@dataclass(frozen=True, slots=True)
class ExecutionState:
    """
    Immutable ITES state.

    Attributes
    ----------
    environment:
        The evaluation environment supplied by SLED.
    session:
        The conversation/session context for visibility and consent.
    initial_inputs:
        Initial artifacts given to the defence.
    max_llm_calls:
        Maximum number of LLM invocations permitted.
    llm_calls_used:
        Number of LLM calls consumed so far.
    active_influencers:
        Principals currently contributing authority.
    declared_actions:
        Proposals accepted by the defence.
    blocked_actions:
        Proposals rejected by the defence.
    guarantees:
        Guarantee objects accumulated during the run.
    trace:
        Full execution trace.
    """

    environment: Any
    session: Session | None = None
    initial_inputs: FrozenSet[Artifact[Any]] = field(default_factory=frozenset)
    max_llm_calls: int = 3
    llm_calls_used: int = 0
    active_influencers: FrozenSet[Principal] = field(default_factory=frozenset)
    declared_actions: FrozenSet[Action[Any]] = field(default_factory=frozenset)
    blocked_actions: FrozenSet[Action[Any]] = field(default_factory=frozenset)
    guarantees: FrozenSet[Guarantee] = field(default_factory=frozenset)
    trace: ExecutionTrace = field(default_factory=ExecutionTrace)

    def __post_init__(self) -> None:
        if self.max_llm_calls < 1:
            raise ValueError("max_llm_calls must be at least 1")
        if self.llm_calls_used < 0:
            raise ValueError("llm_calls_used must be non-negative")

    def with_initial_inputs(
        self,
        initial_inputs: FrozenSet[Artifact[Any]],
    ) -> "ExecutionState":
        """
        Return a copy of the state with a new initial input set.
        """
        return replace(self, initial_inputs=initial_inputs)

    def with_session(self, session: Session | None) -> "ExecutionState":
        """
        Return a copy of the state with a new session context.
        """
        return replace(self, session=session)

    def with_influencers(
        self,
        influencers: FrozenSet[Principal],
    ) -> "ExecutionState":
        """
        Return a copy of the state with updated active influencers.
        """
        return replace(self, active_influencers=influencers)

    def increment_llm_calls(self, count: int = 1) -> "ExecutionState":
        """
        Return a copy of the state with more LLM calls consumed.
        """
        if count < 0:
            raise ValueError("count must be non-negative")
        return replace(self, llm_calls_used=self.llm_calls_used + count)

    def record_declared(self, proposal: Action[Any]) -> "ExecutionState":
        """
        Return a copy of the state with one more declared action.
        """
        return replace(
            self,
            declared_actions=self.declared_actions | frozenset({proposal}),
        )

    def record_blocked(self, proposal: Action[Any]) -> "ExecutionState":
        """
        Return a copy of the state with one more blocked action.
        """
        return replace(
            self,
            blocked_actions=self.blocked_actions | frozenset({proposal}),
        )

    def add_guarantee(self, guarantee: Guarantee) -> "ExecutionState":
        """
        Return a copy of the state with one more guarantee.
        """
        return replace(
            self,
            guarantees=self.guarantees | frozenset({guarantee}),
        )

    def add_step(self, step: ExecutionStep) -> "ExecutionState":
        """
        Return a copy of the state with an appended execution step.
        """
        return replace(self, trace=self.trace.add_step(step))

    def can_call_llm(self) -> bool:
        """
        Check whether another LLM call is still permitted.
        """
        return self.llm_calls_used < self.max_llm_calls

    @property
    def current_influencers(self) -> FrozenSet[Principal]:
        """
        Compatibility alias for the current influencer set.
        """
        return self.active_influencers

    @property
    def trace_length(self) -> int:
        """
        Return the number of recorded steps.
        """
        return self.trace.depth

    def has_declared(self, proposal: Action[Any]) -> bool:
        """
        Return True if the action has already been declared.
        """
        return proposal in self.declared_actions

    def has_blocked(self, proposal: Action[Any]) -> bool:
        """
        Return True if the action has already been blocked.
        """
        return proposal in self.blocked_actions

    def with_trace(self, trace: ExecutionTrace) -> "ExecutionState":
        """
        Return a copy with a replaced trace.
        """
        return replace(self, trace=trace)


__all__ = [
    "ExecutionState",
    "ExecutionStep",
    "ExecutionTrace",
]
