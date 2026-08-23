"""Deterministic branch exploration over the canonical ITES kernel."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from conflux.domain import Artifact, EnvironmentSnapshot, Session, fingerprint
from conflux.ports import ModelPort

from .kernel import TransitionKernel
from .state import (
    ActionOutcome,
    BranchState,
    BranchStatus,
    ITESReport,
    SafetyAssessment,
    TraceEvent,
)


@dataclass(frozen=True, slots=True)
class MediatingITES:
    """Deterministic branch exploration driver over the canonical ITES kernel."""

    kernel: TransitionKernel

    def run(
        self,
        *,
        environment: EnvironmentSnapshot,
        session: Session,
        initial_inputs: tuple[Artifact[Any], ...],
        model: ModelPort,
        max_model_calls: int = 3,
    ) -> ITESReport:
        """Run the kernel against *model* proposals until bound or terminal."""
        if max_model_calls < 1:
            raise ValueError("max_model_calls must be at least 1")
        root = BranchState.initial(initial_inputs)
        queue: list[BranchState] = [root]
        terminal: list[BranchState] = []
        calls = 0
        while queue:
            state = queue.pop(0)
            if state.status != BranchStatus.ACTIVE:
                terminal.append(state)
                continue
            if calls >= max_model_calls:
                terminal.append(_incomplete(state, calls))
                continue
            calls += 1
            try:
                batch = model.propose(state.inputs)
            except Exception as error:
                terminal.append(_model_error(state, calls, error))
                continue
            if not batch.proposals:
                terminal.append(_complete(state, calls))
                continue
            children = self.kernel.expand_batch(
                parent=state,
                batch=batch,
                session=session,
                environment=environment,
                model_calls=calls,
            )
            queue.extend(child for child in children if child.status == BranchStatus.ACTIVE)
            terminal.extend(child for child in children if child.status != BranchStatus.ACTIVE)

        branches = tuple(sorted(terminal, key=lambda branch: branch.branch_id))
        incomplete = any(branch.status == BranchStatus.INCOMPLETE for branch in branches)
        run_id = fingerprint(
            {
                "environment": environment.id,
                "environment_version": environment.version,
                "session": session.id,
                "inputs": [item.fingerprint for item in initial_inputs],
                "max_model_calls": max_model_calls,
                "branches": [
                    {
                        "branch_id": branch.branch_id,
                        "state_key": branch.state_key,
                        "trace_event_ids": [event.id for event in branch.trace],
                    }
                    for branch in branches
                ],
            },
        )
        assessments = _assess(branches, calls, max_model_calls)
        return ITESReport(
            run_id=run_id,
            branches=branches,
            assessments=assessments,
            model_calls=calls,
            max_model_calls=max_model_calls,
            incomplete=incomplete,
        )


def _complete(state: BranchState, calls: int) -> BranchState:
    event = TraceEvent(
        len(state.trace),
        state.branch_id,
        state.parent_branch_id,
        state.depth,
        ActionOutcome.COMPLETE,
        state.context,
        reason="no_proposals",
    )
    return replace(state, status=BranchStatus.TERMINAL, model_calls=calls, trace=state.trace + (event,))


def _incomplete(state: BranchState, calls: int) -> BranchState:
    event = TraceEvent(
        len(state.trace),
        state.branch_id,
        state.parent_branch_id,
        state.depth,
        ActionOutcome.INCOMPLETE,
        state.context,
        reason="model_call_bound",
    )
    return replace(state, status=BranchStatus.INCOMPLETE, model_calls=calls, trace=state.trace + (event,))


def _model_error(state: BranchState, calls: int, error: Exception) -> BranchState:
    event = TraceEvent(
        len(state.trace),
        state.branch_id,
        state.parent_branch_id,
        state.depth,
        ActionOutcome.BLOCKED,
        state.context,
        reason=f"model_error:{type(error).__name__}",
    )
    return replace(state, status=BranchStatus.BLOCKED, model_calls=calls, trace=state.trace + (event,))


def _assess(
    branches: tuple[BranchState, ...],
    calls: int,
    max_calls: int,
) -> tuple[SafetyAssessment, ...]:
    authorised = tuple(branch for branch in branches if branch.status == BranchStatus.AUTHORISED)
    no_bad_authorisation = all(branch.decision is not None and branch.decision.allowed for branch in authorised)
    no_unauthorised_execution = all(
        event.decision is None or event.decision.allowed
        for branch in branches
        for event in branch.trace
        if event.outcome == ActionOutcome.EXECUTED
    )
    return (
        SafetyAssessment(
            "no_unauthorised_execution",
            no_unauthorised_execution,
            "Executed actions, not rejected proposals, determine this property.",
            (f"executed={sum(event.outcome == ActionOutcome.EXECUTED for branch in branches for event in branch.trace)}",),
        ),
        SafetyAssessment(
            "no_unauthorised_authorisation",
            no_bad_authorisation,
            "Every authorised branch has a fully allowing independent decision.",
            (f"authorised={len(authorised)}",),
        ),
        SafetyAssessment(
            "bounded_model_calls",
            calls <= max_calls,
            "The shared run-level model-call bound was respected.",
            (f"calls={calls}", f"bound={max_calls}"),
        ),
    )


__all__ = ["MediatingITES"]
