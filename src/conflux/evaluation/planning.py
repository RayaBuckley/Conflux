"""Finite worst-case abstraction for open-ended dynamic planning."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from conflux.domain import fingerprint

from .model_checking import Transition


class AbstractPlanStatus(StrEnum):
    """Status of the abstract planning model state machine."""

    CONTINUATION = "continuation"
    EFFECT_PENDING = "effect_pending"
    BLOCKED = "blocked"
    TERMINATED = "terminated"
    BOUND_REACHED = "bound_reached"


class AbstractPatchKind(StrEnum):
    """Kind of abstract plan patch applied during exploration."""

    APPEND_EFFECT = "append_effect"
    APPEND_CODE_EFFECT = "append_code_effect"
    TERMINATE = "terminate"


@dataclass(frozen=True, slots=True)
class AbstractEffect:
    """Worst-case abstraction of a plan effect with its permission and principals."""

    id: str
    permission: str
    resource: str
    influencing_principals: frozenset[str]
    authorised: bool
    code_effect: bool = False
    within_capability_envelope: bool = True

    def __post_init__(self) -> None:
        if not self.id or not self.permission or not self.resource:
            raise ValueError("abstract effect identity, permission, and resource are required")
        object.__setattr__(
            self,
            "influencing_principals",
            frozenset(self.influencing_principals),
        )

    @property
    def key(self) -> tuple[object, ...]:
        """Return a stable deduplication key for this effect."""
        return (
            self.id,
            self.permission,
            self.resource,
            tuple(sorted(self.influencing_principals)),
            self.authorised,
            self.code_effect,
            self.within_capability_envelope,
        )


@dataclass(frozen=True, slots=True)
class AbstractPlanPatch:
    """A typed patch that appends an effect or terminates a plan branch."""

    id: str
    kind: AbstractPatchKind
    control_principals: frozenset[str]
    effect: AbstractEffect | None = None
    added_nodes: int = 1

    def __post_init__(self) -> None:
        if not self.id or self.added_nodes < 1:
            raise ValueError("abstract patch identity and positive node count are required")
        object.__setattr__(
            self,
            "control_principals",
            frozenset(self.control_principals),
        )
        if (
            self.kind
            in {
                AbstractPatchKind.APPEND_EFFECT,
                AbstractPatchKind.APPEND_CODE_EFFECT,
            }
            and self.effect is None
        ):
            raise ValueError("effect patch requires an abstract effect")
        if self.kind == AbstractPatchKind.TERMINATE and self.effect is not None:
            raise ValueError("terminal patch cannot contain an effect")

    @property
    def key(self) -> tuple[object, ...]:
        """Return a stable deduplication key for this patch."""
        return (
            self.kind.value,
            self.id,
            tuple(sorted(self.control_principals)),
            self.effect.key if self.effect is not None else (),
            self.added_nodes,
        )


@dataclass(frozen=True, slots=True)
class PlanningModelState:
    """Mutable state of the abstract planning model between transitions."""

    status: AbstractPlanStatus
    context: frozenset[str]
    plan_nodes: int
    planner_calls: int
    continuation_depth: int
    effects_attempted: int = 0
    effects_executed: int = 0
    pending_effect: AbstractEffect | None = None
    executed_unauthorised: bool = False
    capability_violation: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", frozenset(self.context))

    def to_dict(self) -> dict[str, object]:
        """Serialise the planning model state to a dictionary."""
        return {
            "status": self.status.value,
            "context": sorted(self.context),
            "plan_nodes": self.plan_nodes,
            "planner_calls": self.planner_calls,
            "continuation_depth": self.continuation_depth,
            "effects_attempted": self.effects_attempted,
            "effects_executed": self.effects_executed,
            "pending_effect": self.pending_effect.key if self.pending_effect else None,
            "executed_unauthorised": self.executed_unauthorised,
            "capability_violation": self.capability_violation,
        }


@dataclass(frozen=True, slots=True)
class PlanningAction:
    """An action in the planning model, optionally carrying a plan patch."""

    name: str
    patch: AbstractPlanPatch | None = None

    @property
    def key(self) -> tuple[object, ...]:
        """Return a stable deduplication key for this action."""
        return (self.name, self.patch.key if self.patch is not None else ())


@dataclass(frozen=True, slots=True)
class WorstCasePlanningSystem:
    """Explore any configured well-formed patch and capability effect."""

    initial_context: frozenset[str]
    patches: tuple[AbstractPlanPatch, ...]
    max_plan_nodes: int = 8
    max_continuation_depth: int = 4
    max_planner_calls: int = 4
    max_effects: int = 4
    enforce_authorisation: bool = True
    enforce_capability_envelope: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_context", frozenset(self.initial_context))
        object.__setattr__(self, "patches", tuple(self.patches))
        if (
            min(
                self.max_plan_nodes,
                self.max_continuation_depth,
                self.max_planner_calls,
                self.max_effects,
            )
            < 1
        ):
            raise ValueError("planning-model bounds must be positive")

    def initial_states(self) -> tuple[PlanningModelState, ...]:
        """Return the initial continuation state with the starting context."""
        return (
            PlanningModelState(
                AbstractPlanStatus.CONTINUATION,
                self.initial_context,
                1,
                0,
                0,
            ),
        )

    def enabled(self, state: PlanningModelState) -> tuple[PlanningAction, ...]:
        """Return the actions available in the current planning status."""
        if state.status == AbstractPlanStatus.CONTINUATION:
            return tuple(PlanningAction("apply_patch", patch) for patch in self.patches)
        if state.status == AbstractPlanStatus.EFFECT_PENDING:
            return (PlanningAction("mediate_effect"),)
        return ()

    def step(
        self,
        state: PlanningModelState,
        action: PlanningAction,
    ) -> tuple[PlanningModelState, ...]:
        """Apply a planning action, returning successor planning model states."""
        if state.status == AbstractPlanStatus.CONTINUATION:
            if action.name != "apply_patch" or action.patch is None:
                raise ValueError("continuation requires a typed patch")
            patch = action.patch
            context = state.context | patch.control_principals
            nodes = state.plan_nodes + patch.added_nodes
            calls = state.planner_calls + 1
            depth = state.continuation_depth + 1
            if nodes > self.max_plan_nodes or calls > self.max_planner_calls or depth > self.max_continuation_depth:
                return (
                    replace(
                        state,
                        status=AbstractPlanStatus.BOUND_REACHED,
                        context=context,
                        plan_nodes=nodes,
                        planner_calls=calls,
                        continuation_depth=depth,
                    ),
                )
            if patch.kind == AbstractPatchKind.TERMINATE:
                return (
                    replace(
                        state,
                        status=AbstractPlanStatus.TERMINATED,
                        context=context,
                        plan_nodes=nodes,
                        planner_calls=calls,
                        continuation_depth=depth,
                    ),
                )
            return (
                replace(
                    state,
                    status=AbstractPlanStatus.EFFECT_PENDING,
                    context=context,
                    plan_nodes=nodes,
                    planner_calls=calls,
                    continuation_depth=depth,
                    pending_effect=patch.effect,
                ),
            )
        if state.status != AbstractPlanStatus.EFFECT_PENDING or action.name != "mediate_effect" or state.pending_effect is None:
            raise ValueError("invalid planning-model transition")
        effect = state.pending_effect
        context = state.context | effect.influencing_principals
        attempts = state.effects_attempted + 1
        if attempts > self.max_effects:
            return (
                replace(
                    state,
                    status=AbstractPlanStatus.BOUND_REACHED,
                    context=context,
                    effects_attempted=attempts,
                    pending_effect=None,
                ),
            )
        allowed = effect.authorised or not self.enforce_authorisation
        capability_allowed = effect.within_capability_envelope or not self.enforce_capability_envelope
        if not allowed or not capability_allowed:
            return (
                replace(
                    state,
                    status=AbstractPlanStatus.BLOCKED,
                    context=context,
                    effects_attempted=attempts,
                    pending_effect=None,
                ),
            )
        return (
            replace(
                state,
                status=AbstractPlanStatus.CONTINUATION,
                context=context,
                effects_attempted=attempts,
                effects_executed=state.effects_executed + 1,
                pending_effect=None,
                executed_unauthorised=(state.executed_unauthorised or not effect.authorised),
                capability_violation=(state.capability_violation or (effect.code_effect and not effect.within_capability_envelope)),
            ),
        )

    def is_terminal(self, state: PlanningModelState) -> bool:
        """Whether the planning model has reached a blocked or terminated state."""
        return state.status in {
            AbstractPlanStatus.BLOCKED,
            AbstractPlanStatus.TERMINATED,
        }

    def bound_reached(self, state: PlanningModelState) -> bool:
        """Whether the planning model hit a resource bound."""
        return state.status == AbstractPlanStatus.BOUND_REACHED

    def state_key(self, state: PlanningModelState) -> str:
        """Return a canonical deduplication key for a planning state."""
        return fingerprint(state.to_dict())

    def action_key(self, action: PlanningAction) -> tuple[object, ...]:
        """Return a stable sort key for a planning action."""
        return action.key

    def model_calls(self, state: PlanningModelState) -> int:
        """Return the number of planner calls consumed by a state."""
        return state.planner_calls


@dataclass(frozen=True, slots=True)
class NoUnauthorisedPlanningEffect:
    """Ensures no unauthorised effect is executed after replanning."""

    name: str = "no_unauthorised_planning_effect"

    def violation(
        self,
        transition: Transition[PlanningModelState, PlanningAction],
    ) -> str | None:
        """Return a reason if an unauthorised effect was executed."""
        if transition.target.executed_unauthorised:
            return "an unauthorised effect was executed after replanning"
        return None


@dataclass(frozen=True, slots=True)
class PlanningContextMonotonicity:
    """Ensures the planning Principal Context grows monotonically."""

    name: str = "planning_context_monotonicity"

    def violation(
        self,
        transition: Transition[PlanningModelState, PlanningAction],
    ) -> str | None:
        """Return a reason if replanning removed an influencing Principal."""
        if not transition.source.context.issubset(transition.target.context):
            return "replanning removed an influencing Principal"
        return None


@dataclass(frozen=True, slots=True)
class CodeCapabilityPreserved:
    """Ensures generated code stays within its capability envelope."""

    name: str = "code_capability_preserved"

    def violation(
        self,
        transition: Transition[PlanningModelState, PlanningAction],
    ) -> str | None:
        """Return a reason if generated code exceeded its capability envelope."""
        if transition.target.capability_violation:
            return "generated code exceeded its capability envelope"
        return None


__all__ = [
    "AbstractEffect",
    "AbstractPatchKind",
    "AbstractPlanPatch",
    "AbstractPlanStatus",
    "CodeCapabilityPreserved",
    "NoUnauthorisedPlanningEffect",
    "PlanningAction",
    "PlanningContextMonotonicity",
    "PlanningModelState",
    "WorstCasePlanningSystem",
]
