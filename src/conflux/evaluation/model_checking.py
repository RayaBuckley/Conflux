"""Native bounded explicit-state model checker for SLED."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, Protocol, TypeVar

StateT = TypeVar("StateT")
ActionT = TypeVar("ActionT")


@dataclass(frozen=True, slots=True)
class Transition(Generic[StateT, ActionT]):
    """A labelled state transition from a source to a target via an action."""

    source: StateT
    action: ActionT
    target: StateT
    label: str = ""


class TransitionSystem(Protocol[StateT, ActionT]):
    """Protocol for a finite transition system explored by the model checker."""

    def initial_states(self) -> tuple[StateT, ...]:
        """Return the initial states of the transition system."""
        ...

    def enabled(self, state: StateT) -> tuple[ActionT, ...]:
        """Return the actions enabled in the given state."""
        ...

    def step(self, state: StateT, action: ActionT) -> tuple[StateT, ...]:
        """Apply an action to a state and return the successor states."""
        ...

    def is_terminal(self, state: StateT) -> bool:
        """Return whether the state is terminal."""
        ...

    def state_key(self, state: StateT) -> str:
        """Return a canonical key for deduplicating states."""
        ...

    def action_key(self, action: ActionT) -> tuple[object, ...]:
        """Return a sortable key for ordering actions."""
        ...

    def model_calls(self, state: StateT) -> int:
        """Return the number of model calls consumed to reach the state."""
        ...


class SafetyProperty(Protocol[StateT, ActionT]):
    """Protocol for a stateless safety property checked on each transition."""

    @property
    def name(self) -> str:
        """Return the human-readable name of the property."""
        ...

    def violation(self, transition: Transition[StateT, ActionT]) -> str | None:
        """Return a violation reason if the transition violates the property, else None."""
        ...


@dataclass(frozen=True, slots=True)
class VerificationBounds:
    """Resource limits bounding the explicit-state exploration."""

    max_depth: int = 8
    max_states: int = 10_000
    max_transitions: int = 50_000
    max_model_calls: int = 8

    def __post_init__(self) -> None:
        if min(self.max_depth, self.max_states, self.max_transitions, self.max_model_calls) < 1:
            raise ValueError("verification bounds must be positive")


class VerificationVerdict(StrEnum):
    """Outcome classification of a bounded verification run."""

    SAFE = "safe"
    BOUNDED_SAFE = "bounded_safe"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Counterexample(Generic[StateT, ActionT]):
    """A minimal violating transition trace for a safety property."""

    property_name: str
    reason: str
    transitions: tuple[Transition[StateT, ActionT], ...]

    @property
    def length(self) -> int:
        """Number of transitions in the counterexample trace."""
        return len(self.transitions)


@dataclass(frozen=True, slots=True)
class VerificationResult(Generic[StateT, ActionT]):
    """Full result of a bounded verification run including statistics and witnesses."""

    verdict: VerificationVerdict
    unique_states: int
    transitions: int
    duplicate_states: int
    truncated: bool
    bounds: VerificationBounds
    counterexample: Counterexample[StateT, ActionT] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialise the result to a schema-compliant dictionary."""
        return {
            "schema_version": "1",
            "verdict": self.verdict.value,
            "statistics": {
                "unique_states": self.unique_states,
                "transitions": self.transitions,
                "duplicate_states": self.duplicate_states,
                "truncated": self.truncated,
            },
            "bounds": {
                "max_depth": self.bounds.max_depth,
                "max_states": self.bounds.max_states,
                "max_transitions": self.bounds.max_transitions,
                "max_model_calls": self.bounds.max_model_calls,
            },
            "counterexample": (
                {
                    "property": self.counterexample.property_name,
                    "reason": self.counterexample.reason,
                    "length": self.counterexample.length,
                    "labels": [item.label for item in self.counterexample.transitions],
                }
                if self.counterexample
                else None
            ),
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class ExplicitStateChecker:
    """Explore reachable states breadth-first and retain shortest witnesses."""

    def verify(
        self,
        system: TransitionSystem[StateT, ActionT],
        properties: tuple[SafetyProperty[StateT, ActionT], ...],
        bounds: VerificationBounds = VerificationBounds(),
    ) -> VerificationResult[StateT, ActionT]:
        """Run bounded model checking, catching errors as unknown verdicts."""
        try:
            return self._verify(system, properties, bounds)
        except Exception as error:
            return VerificationResult(
                VerificationVerdict.UNKNOWN,
                0,
                0,
                0,
                False,
                bounds,
                error=f"{type(error).__name__}: {error}",
            )

    def _verify(
        self,
        system: TransitionSystem[StateT, ActionT],
        properties: tuple[SafetyProperty[StateT, ActionT], ...],
        bounds: VerificationBounds,
    ) -> VerificationResult[StateT, ActionT]:
        initial = tuple(sorted(system.initial_states(), key=system.state_key))
        queue: deque[tuple[StateT, int]] = deque((state, 0) for state in initial)
        visited: dict[str, StateT] = {system.state_key(state): state for state in initial}
        predecessor: dict[str, tuple[str, Transition[StateT, ActionT]]] = {}
        transitions = 0
        duplicates = 0
        truncated = False

        while queue:
            state, depth = queue.popleft()
            source_key = system.state_key(state)
            if system.is_terminal(state):
                continue
            system_bound = getattr(system, "bound_reached", None)
            if callable(system_bound) and bool(system_bound(state)):
                truncated = True
                continue
            if depth >= bounds.max_depth or system.model_calls(state) >= bounds.max_model_calls:
                truncated = True
                continue
            for action in sorted(system.enabled(state), key=system.action_key):
                for target in system.step(state, action):
                    if transitions >= bounds.max_transitions:
                        truncated = True
                        queue.clear()
                        break
                    transitions += 1
                    transition = Transition(state, action, target, label=str(system.action_key(action)))
                    for property_ in properties:
                        reason = property_.violation(transition)
                        if reason is not None:
                            path = _path(predecessor, source_key) + (transition,)
                            return VerificationResult(
                                VerificationVerdict.UNSAFE,
                                len(visited),
                                transitions,
                                duplicates,
                                truncated,
                                bounds,
                                Counterexample(property_.name, reason, path),
                            )
                    target_key = system.state_key(target)
                    if target_key in visited:
                        duplicates += 1
                        continue
                    if len(visited) >= bounds.max_states:
                        truncated = True
                        queue.clear()
                        break
                    visited[target_key] = target
                    predecessor[target_key] = (source_key, transition)
                    queue.append((target, depth + 1))
                if truncated and (transitions >= bounds.max_transitions or len(visited) >= bounds.max_states):
                    break

        verdict = VerificationVerdict.BOUNDED_SAFE if truncated else VerificationVerdict.SAFE
        return VerificationResult(
            verdict,
            len(visited),
            transitions,
            duplicates,
            truncated,
            bounds,
        )


def _path(
    predecessor: dict[str, tuple[str, Transition[StateT, ActionT]]],
    target_key: str,
) -> tuple[Transition[StateT, ActionT], ...]:
    result: list[Transition[StateT, ActionT]] = []
    current = target_key
    while current in predecessor:
        parent, transition = predecessor[current]
        result.append(transition)
        current = parent
    result.reverse()
    return tuple(result)


__all__ = [
    "Counterexample",
    "ExplicitStateChecker",
    "SafetyProperty",
    "Transition",
    "TransitionSystem",
    "VerificationBounds",
    "VerificationResult",
    "VerificationVerdict",
]
