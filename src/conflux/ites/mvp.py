"""Normative MVP semantics for ITES.

This module deliberately implements only the security-critical core: immutable
provenance, Principal Context accumulation, nested execution, primitive
authorisation, a shared call budget, and isolated proposal branches. The richer
ITES action surface remains available through the compatibility implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TypeAlias

from conflux.auth.authorisation import all_principals_authorised
from conflux.core import Artifact, Principal, Provenance, Resource
from conflux.core.permissions import Permission, normalise_permission

Environment: TypeAlias = object
MVPInput: TypeAlias = Artifact[object]


class MVPStatus(StrEnum):
    ACTIVE = "active"
    TERMINAL = "terminal"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class MVPPrimitive:
    """A primitive action in the normative MVP."""

    permission: Permission
    resource: Resource | None = None
    operation: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "permission", normalise_permission(self.permission))
        if not self.operation:
            raise ValueError("MVPPrimitive.operation must be non-empty")


@dataclass(frozen=True, slots=True)
class MVPNested:
    """A request to execute the model over another immutable input set."""

    inputs: frozenset[MVPInput]


MVPProposal: TypeAlias = MVPPrimitive | MVPNested


class MVPModel(Protocol):
    """Deterministic or real model boundary used by the MVP evaluator."""

    def __call__(self, inputs: frozenset[MVPInput]) -> tuple[MVPProposal, ...]: ...


@dataclass(frozen=True, slots=True)
class MVPEvent:
    """One immutable proposal decision in a branch trace."""

    branch_id: str
    depth: int
    influencers: frozenset[Principal]
    inputs: frozenset[MVPInput]
    proposal: MVPProposal | None
    declared: bool
    reason: str


@dataclass(frozen=True, slots=True)
class MVPTransition:
    """Typed transition result for one proposal from one parent state."""

    parent_branch_id: str
    proposal: MVPProposal
    event: MVPEvent
    successors: tuple["MVPExecutionState", ...] = ()


@dataclass(frozen=True, slots=True)
class MVPExecutionState:
    """Immutable state for one branch of an MVP evaluation."""

    environment: Environment
    inputs: frozenset[MVPInput]
    influencers: frozenset[Principal]
    branch_id: str = "root"
    depth: int = 0
    calls_used: int = 0
    trace: tuple[MVPEvent, ...] = ()
    status: MVPStatus = MVPStatus.ACTIVE

    @classmethod
    def initial(
        cls, environment: Environment, inputs: frozenset[MVPInput]
    ) -> "MVPExecutionState":
        principals = frozenset(
            principal for item in inputs for principal in item.provenance.principals
        )
        return cls(environment=environment, inputs=inputs, influencers=principals)

    def with_event(
        self, event: MVPEvent, *, status: MVPStatus | None = None
    ) -> "MVPExecutionState":
        return MVPExecutionState(
            environment=self.environment,
            inputs=self.inputs,
            influencers=self.influencers,
            branch_id=self.branch_id,
            depth=self.depth,
            calls_used=self.calls_used,
            trace=self.trace + (event,),
            status=status or self.status,
        )


@dataclass(frozen=True, slots=True)
class MVPReport:
    """Aggregate output from exhaustive MVP exploration."""

    semantics_version: str
    max_calls: int
    calls_used: int
    terminal_states: tuple[MVPExecutionState, ...]
    blocked: tuple[MVPEvent, ...]
    declared: tuple[MVPEvent, ...]
    incomplete: bool

    @property
    def branch_count(self) -> int:
        return len(self.terminal_states)

    @property
    def privilege_escalation(self) -> bool:
        return any(
            event.declared
            and isinstance(event.proposal, MVPPrimitive)
            and not all_principals_authorised(
                event.influencers, event.proposal.permission
            )
            for event in self.declared
        )

    def to_dict(self) -> dict[str, object]:
        def principal_ids(principals: frozenset[Principal]) -> list[str]:
            return sorted(principal.id for principal in principals)

        def event_dict(event: MVPEvent) -> dict[str, object]:
            proposal = event.proposal
            if isinstance(proposal, MVPPrimitive):
                proposal_data: dict[str, object] = {
                    "kind": "primitive",
                    "operation": proposal.operation,
                    "permission": proposal.permission.name,
                    "resource": proposal.resource.id if proposal.resource else None,
                }
            elif isinstance(proposal, MVPNested):
                proposal_data = {"kind": "nested", "input_count": len(proposal.inputs)}
            else:
                proposal_data = {"kind": "none"}
            return {
                "branch_id": event.branch_id,
                "depth": event.depth,
                "influencers": principal_ids(event.influencers),
                "input_count": len(event.inputs),
                "proposal": proposal_data,
                "declared": event.declared,
                "reason": event.reason,
            }

        return {
            "semantics_version": self.semantics_version,
            "max_calls": self.max_calls,
            "calls_used": self.calls_used,
            "branch_count": self.branch_count,
            "incomplete": self.incomplete,
            "privilege_escalation": self.privilege_escalation,
            "declared": [event_dict(event) for event in self.declared],
            "blocked": [event_dict(event) for event in self.blocked],
            "terminal_states": [
                {
                    "branch_id": state.branch_id,
                    "status": state.status.value,
                    "depth": state.depth,
                    "calls_used": state.calls_used,
                    "influencers": principal_ids(state.influencers),
                    "trace_length": len(state.trace),
                }
                for state in self.terminal_states
            ],
        }


@dataclass(slots=True)
class MVPExplorer:
    """Exhaustively explore typed proposals with branch isolation."""

    model: MVPModel
    max_calls: int = 3
    semantics_version: str = "ites-mvp-1"

    def __post_init__(self) -> None:
        if self.max_calls < 1:
            raise ValueError("max_calls must be at least 1")

    def run(self, environment: Environment, inputs: frozenset[MVPInput]) -> MVPReport:
        root = MVPExecutionState.initial(environment, inputs)
        terminals: list[MVPExecutionState] = []
        blocked: list[MVPEvent] = []
        declared: list[MVPEvent] = []
        calls_used = 0
        incomplete = False

        def visit(state: MVPExecutionState, remaining: int) -> None:
            nonlocal calls_used, incomplete
            if remaining == 0:
                incomplete = True
                terminals.append(
                    state.with_event(
                        MVPEvent(
                            state.branch_id,
                            state.depth,
                            state.influencers,
                            state.inputs,
                            None,
                            False,
                            "call_budget_exhausted",
                        ),
                        status=MVPStatus.INCOMPLETE,
                    )
                )
                return

            calls_used += 1
            proposals = tuple(sorted(self.model(state.inputs), key=self._proposal_key))
            if not proposals:
                terminals.append(
                    MVPExecutionState(
                        environment=state.environment,
                        inputs=state.inputs,
                        influencers=state.influencers,
                        branch_id=state.branch_id,
                        depth=state.depth,
                        calls_used=calls_used,
                        trace=state.trace,
                        status=MVPStatus.TERMINAL,
                    )
                )
                return

            for index, proposal in enumerate(proposals):
                branch_id = f"{state.branch_id}.{index + 1}"
                event_base = dict(
                    branch_id=branch_id,
                    depth=state.depth,
                    influencers=state.influencers,
                    inputs=state.inputs,
                    proposal=proposal,
                )
                if isinstance(proposal, MVPPrimitive):
                    allowed = all_principals_authorised(
                        state.influencers, proposal.permission
                    )
                    event = MVPEvent(
                        **event_base,
                        declared=allowed,
                        reason=(
                            "intersection_rule"
                            if allowed
                            else "principal_lacks_permission"
                        ),
                    )
                    child = MVPExecutionState(
                        environment=state.environment, inputs=state.inputs,
                        influencers=state.influencers, branch_id=branch_id,
                        depth=state.depth, calls_used=calls_used,
                        trace=state.trace + (event,),
                        status=MVPStatus.TERMINAL if allowed else MVPStatus.BLOCKED,
                    )
                    (declared if allowed else blocked).append(event)
                    terminals.append(child)
                    continue

                readable = all(
                    principal in item.provenance.principals
                    for principal in state.influencers
                    for item in proposal.inputs
                )
                next_influencers = state.influencers | frozenset(
                    principal
                    for item in proposal.inputs
                    for principal in item.provenance.principals
                )
                event = MVPEvent(
                    **event_base,
                    declared=readable,
                    reason=(
                        "nested_inputs_readable"
                        if readable
                        else "nested_input_unreadable"
                    ),
                )
                if not readable:
                    blocked.append(event)
                    terminals.append(
                        MVPExecutionState(
                            environment=state.environment,
                            inputs=state.inputs,
                            influencers=state.influencers,
                            branch_id=branch_id,
                            depth=state.depth,
                            calls_used=calls_used,
                            trace=state.trace + (event,),
                            status=MVPStatus.BLOCKED,
                        )
                    )
                    continue
                child = MVPExecutionState(
                    environment=state.environment, inputs=proposal.inputs,
                    influencers=next_influencers, branch_id=branch_id,
                    depth=state.depth + 1, calls_used=calls_used,
                    trace=state.trace + (event,), status=MVPStatus.ACTIVE,
                )
                declared.append(event)
                visit(child, self.max_calls - calls_used)

        visit(root, self.max_calls)
        return MVPReport(
            self.semantics_version,
            self.max_calls,
            calls_used,
            tuple(terminals),
            tuple(blocked),
            tuple(declared),
            incomplete,
        )

    @staticmethod
    def _proposal_key(proposal: MVPProposal) -> tuple[object, ...]:
        if isinstance(proposal, MVPPrimitive):
            return (
                "primitive",
                proposal.operation,
                proposal.permission.name,
                proposal.resource.id if proposal.resource else "",
            )
        return ("nested", tuple(sorted(item.label or "" for item in proposal.inputs)))


def artifact(value: object, principal: Principal, *, label: str = "input") -> MVPInput:
    """Construct a labelled MVP input with one originating Principal."""
    return Artifact(value=value, label=label, provenance=Provenance.from_principal(principal))


__all__ = [
    "MVPExplorer",
    "MVPExecutionState",
    "MVPEvent",
    "MVPInput",
    "MVPModel",
    "MVPNested",
    "MVPPrimitive",
    "MVPProposal",
    "MVPReport",
    "MVPStatus",
    "MVPTransition",
    "artifact",
]
