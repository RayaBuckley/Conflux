"""Deterministic dynamic-plan executor that mediates every grounded effect."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Any, Callable

from conflux.application import MediationService
from conflux.domain import (
    Action,
    Artifact,
    EnvironmentSnapshot,
    ProposalBatch,
    Provenance,
    Session,
    provenance_union,
)
from conflux.ites import ITESReport
from conflux.ports import ExecutorPort, PlannerPort, ValueModelPort, ValueRequest

from .actions import BindingEnvironment, OperationCatalogue, ground_action, resolve_binding
from .continuation import HistoricalNodeStatus, apply_patch
from .model import (
    ActionTemplateNode,
    ApprovalNode,
    BranchNode,
    ContinuePlanningNode,
    DelegationNode,
    LoopNode,
    ModelCallNode,
    Plan,
    PlanNode,
    SubplanNode,
    TerminalNode,
    TerminalOutcome,
)
from .requests import ContinuationRequest, PlanBudgets, PlanningRequest
from .state import (
    NodeOutput,
    NodeStatus,
    PlanExecutionState,
    PlanRunStatus,
    ready_nodes,
)


@dataclass(frozen=True, slots=True)
class DynamicPlanResult:
    state: PlanExecutionState
    mediation_reports: tuple[ITESReport, ...]
    completed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1",
            "completed": self.completed,
            "state": self.state.to_dict(),
            "mediation_run_ids": [report.run_id for report in self.mediation_reports],
        }


@dataclass(frozen=True, slots=True)
class DynamicPlanExecutor:
    planner: PlannerPort
    value_model: ValueModelPort
    mediation: MediationService
    provider: ExecutorPort
    catalogue: OperationCatalogue
    environment: EnvironmentSnapshot
    session: Session
    budgets: PlanBudgets = PlanBudgets()
    clock: Callable[[], float] = time.monotonic

    def run(self, request: PlanningRequest) -> DynamicPlanResult:
        if request.catalogue_fingerprint != self.catalogue.fingerprint:
            return self._initial_failure(
                request,
                "catalogue_mismatch",
                "authenticated catalogue fingerprint does not match",
            )
        response = self.planner.initial_plan(request)
        if response.plan is None:
            return self._initial_failure(
                request,
                "planner_output_invalid",
                response.record.error or "planner returned no plan",
            )
        state = PlanExecutionState.initial(response.plan, request.observations)
        state = replace(state, planner_calls=1).emit(
            "plan.planner_responded",
            payload={"record": response.record.to_dict()},
        )
        return self.execute(response.plan, artifacts=request.observations, state=state)

    def execute(
        self,
        plan: Plan,
        *,
        artifacts: tuple[Artifact[Any], ...] = (),
        state: PlanExecutionState | None = None,
    ) -> DynamicPlanResult:
        current = state or PlanExecutionState.initial(plan, artifacts)
        reports: list[ITESReport] = []
        started = self.clock()
        while current.status == PlanRunStatus.RUNNING:
            current = self._refresh_loops(current)
            bounded = self._check_global_bounds(current, started)
            if bounded is not None:
                current = bounded
                break
            ready = ready_nodes(current)
            if not ready:
                current = self._settle(current)
                break
            if current.transitions >= self.budgets.max_transitions:
                current = self._incomplete(current, "transition_bound")
                break
            node_id = ready[0]
            node = current.plan.node(node_id)
            current = (
                current.with_node(node_id, NodeStatus.READY)
                .emit(
                    "plan.node_ready",
                    node_id=node_id,
                    payload={"node_kind": node.kind.value},
                )
                .with_node(
                    node_id,
                    NodeStatus.RUNNING,
                    increment_attempts=True,
                )
                .emit(
                    "plan.node_started",
                    node_id=node_id,
                    payload={"node_kind": node.kind.value},
                )
            )
            current = replace(current, transitions=current.transitions + 1)
            current, report = self._execute_node(current, node)
            if report is not None:
                reports.append(report)
        event_type = {
            PlanRunStatus.SUCCEEDED: "plan.completed",
            PlanRunStatus.SAFE_STOP: "plan.completed",
            PlanRunStatus.RUNNING: "plan.failed",
            PlanRunStatus.FAILED: "plan.failed",
            PlanRunStatus.BLOCKED: "plan.failed",
            PlanRunStatus.INCOMPLETE: "bound.reached",
        }[current.status]
        current = current.emit(
            event_type,
            payload={
                "status": current.status.value,
                "failure_category": current.failure_category,
                "final_plan": current.plan.to_dict(),
                "node_states": [item.to_dict() for item in current.nodes],
            },
        )
        return DynamicPlanResult(
            current,
            tuple(reports),
            current.status in {PlanRunStatus.SUCCEEDED, PlanRunStatus.SAFE_STOP},
        )

    def _execute_node(
        self,
        state: PlanExecutionState,
        node: PlanNode,
    ) -> tuple[PlanExecutionState, ITESReport | None]:
        try:
            if isinstance(node, ModelCallNode):
                return self._model_node(state, node), None
            if isinstance(node, ActionTemplateNode):
                return self._action_node(state, node)
            if isinstance(node, BranchNode):
                return self._branch_node(state, node), None
            if isinstance(node, LoopNode):
                return self._loop_node(state, node), None
            if isinstance(node, ContinuePlanningNode):
                return self._continuation_node(state, node), None
            if isinstance(node, ApprovalNode):
                return self._blocked(
                    state,
                    node.id,
                    "approval_unavailable",
                    "no approval adapter is configured",
                ), None
            if isinstance(node, DelegationNode):
                return self._blocked(
                    state,
                    node.id,
                    "delegation_unsupported",
                    "formal delegation remains unsupported",
                ), None
            if isinstance(node, SubplanNode):
                return self._subplan_node(state, node), None
            return self._terminal_node(state, node), None
        except (TypeError, ValueError) as error:
            return self._failed(
                state,
                node.id,
                "plan_node_invalid",
                f"{type(error).__name__}: {error}",
            ), None

    def _model_node(
        self,
        state: PlanExecutionState,
        node: ModelCallNode,
    ) -> PlanExecutionState:
        if state.planner_calls >= self.budgets.max_planner_calls:
            return self._incomplete(state, "planner_call_bound", node_id=node.id)
        prompt = resolve_binding(node.prompt, self._bindings(state))
        response = self.value_model.produce(
            ValueRequest(f"{state.run_id}:{node.id}:{state.node_state(node.id).attempts}", node.id, prompt)
        )
        state = replace(state, planner_calls=state.planner_calls + 1).emit(
            "plan.model_responded",
            node_id=node.id,
            payload={"record": response.record.to_dict()},
        )
        if response.output is None:
            return self._failed(
                state,
                node.id,
                "model_output_invalid",
                response.record.error or "value model returned no output",
            )
        provenance = provenance_union(
            state.plan.invocation_provenance,
            node.control_provenance,
            prompt.provenance,
            response.output.provenance,
        ).with_activity(f"model:{node.id}")
        output = Artifact(
            f"{state.plan.id}:{node.id}:{node.output_name}",
            response.output.value,
            provenance,
            response.output.label,
            response.output.confidential,
        )
        return (
            state.with_output(NodeOutput(node.id, node.output_name, output))
            .with_node(node.id, NodeStatus.SUCCEEDED, reason="model_value_produced")
            .emit(
                "plan.node_succeeded",
                node_id=node.id,
                payload={"output_fingerprint": output.fingerprint},
            )
        )

    def _action_node(
        self,
        state: PlanExecutionState,
        node: ActionTemplateNode,
    ) -> tuple[PlanExecutionState, ITESReport | None]:
        if state.effects >= self.budgets.max_effects:
            return self._incomplete(state, "effect_bound", node_id=node.id), None
        ground = ground_action(
            node.template,
            catalogue=self.catalogue,
            environment=self._bindings(state),
            invocation_provenance=state.plan.invocation_provenance,
            control_provenance=node.control_provenance,
        )
        action = ground.to_action()
        context_artifact = Artifact(
            f"context:{ground.fingerprint}",
            {"ground_action": ground.fingerprint},
            ground.provenance,
        )
        state = state.emit(
            "plan.action_grounded",
            node_id=node.id,
            payload={
                "ground_action_fingerprint": ground.fingerprint,
                "context_fingerprint": ground.provenance.context.fingerprint,
            },
        )
        report = self.mediation.evaluate(
            environment=self.environment,
            session=self.session,
            initial_inputs=(context_artifact,),
            model=_OneActionModel(action),
            max_model_calls=1,
        )
        authorised = report.authorised_branches
        if not authorised:
            reason = _report_denial(report)
            state = (
                state.with_node(node.id, NodeStatus.BLOCKED, reason=reason)
                .emit(
                    "plan.node_blocked",
                    node_id=node.id,
                    payload={"reason": reason, "mediation_run_id": report.run_id},
                )
            )
            if node.on_block is not None:
                state = state.activate(node.on_block)
            else:
                state = replace(
                    state,
                    status=PlanRunStatus.BLOCKED,
                    failure_category="policy_denial",
                )
            return state, report
        branch = authorised[0]
        execution = self.mediation.execute(
            report=report,
            branch=branch,
            executor=self.provider,
            environment=self.environment,
            session=self.session,
        )
        state = replace(state, effects=state.effects + 1)
        if not execution.provider.success:
            reason = execution.provider.error or "provider_failed"
            state = (
                state.with_node(node.id, NodeStatus.FAILED, reason=reason)
                .emit(
                    "plan.node_failed",
                    node_id=node.id,
                    payload={
                        "reason": reason,
                        "mediation_run_id": execution.report.run_id,
                    },
                )
            )
            if node.on_failure is not None:
                state = state.activate(node.on_failure)
            else:
                state = replace(
                    state,
                    status=PlanRunStatus.FAILED,
                    failure_category="provider_failure",
                )
            return state, execution.report
        output = Artifact(
            f"{state.plan.id}:{node.id}:{node.output_name}",
            execution.provider.outcome,
            ground.provenance.with_activity(f"provider:{node.id}"),
        )
        state = (
            state.with_output(NodeOutput(node.id, node.output_name, output))
            .with_node(node.id, NodeStatus.SUCCEEDED, reason="effect_executed")
            .emit(
                "plan.node_succeeded",
                node_id=node.id,
                payload={
                    "output_fingerprint": output.fingerprint,
                    "mediation_run_id": execution.report.run_id,
                    "certificate_id": branch.certificate.id,
                },
            )
        )
        unused = tuple(
            target for target in (node.on_block, node.on_failure) if target is not None
        )
        return state.skip(*unused, reason="action_succeeded"), execution.report

    def _branch_node(
        self,
        state: PlanExecutionState,
        node: BranchNode,
    ) -> PlanExecutionState:
        condition = resolve_binding(node.condition, self._bindings(state))
        if not isinstance(condition.value, bool):
            raise ValueError("branch condition must resolve to a boolean")
        selected = node.when_true if condition.value else node.when_false
        rejected = node.when_false if condition.value else node.when_true
        state = self._propagate_control(state, selected, condition.provenance)
        return (
            state.activate(selected)
            .skip(rejected, reason=f"branch_not_selected:{node.id}")
            .with_node(node.id, NodeStatus.SUCCEEDED, reason=f"selected:{selected}")
            .emit(
                "plan.node_succeeded",
                node_id=node.id,
                payload={
                    "selected_node_id": selected,
                    "condition_fingerprint": condition.fingerprint,
                },
            )
        )

    def _loop_node(
        self,
        state: PlanExecutionState,
        node: LoopNode,
    ) -> PlanExecutionState:
        condition = resolve_binding(node.condition, self._bindings(state))
        if not isinstance(condition.value, bool):
            raise ValueError("loop condition must resolve to a boolean")
        count = state.loop_count(node.id)
        if not condition.value:
            return (
                state.activate(node.exit_node_id)
                .skip(node.body_node_id, reason=f"loop_not_entered:{node.id}")
                .with_node(node.id, NodeStatus.SUCCEEDED, reason="loop_complete")
                .emit(
                    "plan.node_succeeded",
                    node_id=node.id,
                    payload={"iterations": count},
                )
            )
        if count >= min(node.max_iterations, self.budgets.max_loop_iterations):
            return self._incomplete(
                state,
                "loop_iteration_bound",
                node_id=node.id,
            )
        state = self._propagate_control(state, node.body_node_id, condition.provenance)
        return (
            state.increment_loop(node.id)
            .activate(node.body_node_id)
            .with_node(node.id, NodeStatus.RUNNING, reason="loop_body_active")
            .emit(
                "plan.loop_iteration",
                node_id=node.id,
                payload={"iteration": count + 1, "body_node_id": node.body_node_id},
            )
        )

    def _continuation_node(
        self,
        state: PlanExecutionState,
        node: ContinuePlanningNode,
    ) -> PlanExecutionState:
        if state.planner_calls >= self.budgets.max_planner_calls:
            return self._incomplete(state, "planner_call_bound", node_id=node.id)
        if state.continuation_depth >= self.budgets.max_continuation_depth:
            return self._incomplete(state, "continuation_depth_bound", node_id=node.id)
        observations = tuple(
            resolve_binding(binding, self._bindings(state))
            for binding in node.observation_bindings
        )
        completed = tuple(
            item.node_id
            for item in state.nodes
            if item.status in {NodeStatus.SUCCEEDED, NodeStatus.FAILED, NodeStatus.BLOCKED}
        )
        request = ContinuationRequest.create(
            request_id=f"{state.run_id}:{node.id}:{state.node_state(node.id).attempts}",
            plan=state.plan,
            completed_node_ids=completed,
            observations=observations,
            catalogue_fingerprint=self.catalogue.fingerprint,
            remaining_budgets=self.budgets,
            trigger=node.trigger,
            control_provenance=node.control_provenance,
        )
        state = state.emit(
            "plan.continuation_requested",
            node_id=node.id,
            payload={
                "request_fingerprint": request.fingerprint,
                "request_provenance": request.provenance.to_dict(),
            },
        )
        response = self.planner.continue_plan(request)
        state = replace(
            state,
            planner_calls=state.planner_calls + 1,
            continuation_depth=state.continuation_depth + 1,
        ).emit(
            "plan.patch_received",
            node_id=node.id,
            payload={"record": response.record.to_dict()},
        )
        if response.patch is None:
            return self._failed(
                state,
                node.id,
                "plan_patch_invalid",
                response.record.error or "planner returned no patch",
            ).emit(
                "plan.patch_rejected",
                node_id=node.id,
                payload={"reason": response.record.error or "missing_patch"},
            )
        history = {
            item.node_id: HistoricalNodeStatus(item.status.value)
            for item in state.nodes
        }
        try:
            application = apply_patch(
                state.plan,
                response.patch,
                history=history,
                request_provenance=request.provenance,
            )
        except ValueError as error:
            return self._failed(
                state,
                node.id,
                "plan_patch_rejected",
                str(error),
            ).emit(
                "plan.patch_rejected",
                node_id=node.id,
                payload={"reason": str(error)},
            )
        state = state.replace_plan(
            application.plan,
            removed_node_ids=application.removed_node_ids,
        )
        if node.id in application.removed_node_ids:
            raise ValueError("continuation patch removed its running node")
        return (
            state.with_node(node.id, NodeStatus.SUCCEEDED, reason="patch_applied")
            .emit(
                "plan.patch_applied",
                node_id=node.id,
                payload={
                    "patch_fingerprint": response.patch.fingerprint,
                    "added_node_ids": list(application.added_node_ids),
                    "removed_node_ids": list(application.removed_node_ids),
                    "added_subplan_ids": list(application.added_subplan_ids),
                    "plan": application.plan.to_dict(),
                },
            )
        )

    def _subplan_node(
        self,
        state: PlanExecutionState,
        node: SubplanNode,
    ) -> PlanExecutionState:
        child = next(
            (plan for plan in state.plan.subplans if plan.id == node.child_plan_id),
            None,
        )
        if child is None:
            raise ValueError("subplan is not present")
        result = self.execute(child, artifacts=tuple(state.artifacts().values()))
        state = replace(
            state,
            effects=state.effects + result.state.effects,
            planner_calls=state.planner_calls + result.state.planner_calls,
            transitions=state.transitions + result.state.transitions,
        ).emit(
            "plan.subplan_completed",
            node_id=node.id,
            payload={
                "child_plan_id": child.id,
                "child_run_id": result.state.run_id,
                "status": result.state.status.value,
            },
        )
        if not result.completed:
            return self._failed(
                state,
                node.id,
                "subplan_failed",
                result.state.failure_category or result.state.status.value,
            )
        return state.with_node(
            node.id,
            NodeStatus.SUCCEEDED,
            reason=f"subplan:{result.state.status.value}",
        )

    def _terminal_node(
        self,
        state: PlanExecutionState,
        node: TerminalNode,
    ) -> PlanExecutionState:
        status = {
            TerminalOutcome.SUCCEEDED: PlanRunStatus.SUCCEEDED,
            TerminalOutcome.SAFE_STOP: PlanRunStatus.SAFE_STOP,
            TerminalOutcome.FAILED: PlanRunStatus.FAILED,
        }[node.outcome]
        return replace(
            state.with_node(node.id, NodeStatus.SUCCEEDED, reason=node.reason).emit(
                "plan.node_succeeded",
                node_id=node.id,
                payload={"terminal_outcome": node.outcome.value, "reason": node.reason},
            ),
            status=status,
            failure_category="terminal_failure" if status == PlanRunStatus.FAILED else None,
        )

    def _bindings(self, state: PlanExecutionState) -> BindingEnvironment:
        return BindingEnvironment(state.artifacts(), state.node_outputs())

    def _refresh_loops(self, state: PlanExecutionState) -> PlanExecutionState:
        for node in state.plan.nodes:
            if not isinstance(node, LoopNode):
                continue
            loop_state = state.node_state(node.id)
            if loop_state.status != NodeStatus.RUNNING:
                continue
            body = state.node_state(node.body_node_id)
            if not body.status.terminal:
                continue
            if body.status != NodeStatus.SUCCEEDED:
                return self._failed(
                    state,
                    node.id,
                    "loop_body_failed",
                    body.reason or body.status.value,
                )
            state = (
                state.with_node(node.body_node_id, NodeStatus.PENDING, reason="")
                .with_node(node.id, NodeStatus.PENDING, reason="")
                .deactivate(node.body_node_id)
                .activate(node.id)
            )
        return state

    def _propagate_control(
        self,
        state: PlanExecutionState,
        node_id: str,
        provenance: Provenance,
    ) -> PlanExecutionState:
        updated: list[PlanNode] = []
        for node in state.plan.nodes:
            if node.id == node_id:
                updated.append(
                    replace(
                        node,
                        control_provenance=provenance_union(
                            node.control_provenance,
                            provenance,
                        ).with_activity(f"control:{node_id}"),
                    )
                )
            else:
                updated.append(node)
        plan = replace(state.plan, nodes=tuple(updated))
        return state.replace_plan(plan, removed_node_ids=())

    def _check_global_bounds(
        self,
        state: PlanExecutionState,
        started: float,
    ) -> PlanExecutionState | None:
        checks = (
            (len(state.plan.nodes) > self.budgets.max_nodes, "plan_node_bound"),
            (self.clock() - started >= self.budgets.max_elapsed_seconds, "elapsed_time_bound"),
        )
        for reached, category in checks:
            if reached:
                return self._incomplete(state, category)
        return None

    def _settle(self, state: PlanExecutionState) -> PlanExecutionState:
        statuses = tuple(item.status for item in state.nodes)
        if any(status == NodeStatus.FAILED for status in statuses):
            return replace(
                state,
                status=PlanRunStatus.FAILED,
                failure_category="unrecovered_node_failure",
            )
        if any(status == NodeStatus.BLOCKED for status in statuses):
            return replace(
                state,
                status=PlanRunStatus.BLOCKED,
                failure_category="unrecovered_node_block",
            )
        if all(status.terminal for status in statuses):
            return replace(state, status=PlanRunStatus.SUCCEEDED)
        return replace(
            state,
            status=PlanRunStatus.FAILED,
            failure_category="inconsistent_plan_graph",
        )

    def _blocked(
        self,
        state: PlanExecutionState,
        node_id: str,
        category: str,
        reason: str,
    ) -> PlanExecutionState:
        return replace(
            state.with_node(node_id, NodeStatus.BLOCKED, reason=reason).emit(
                "plan.node_blocked",
                node_id=node_id,
                payload={"reason": reason, "failure_category": category},
            ),
            status=PlanRunStatus.BLOCKED,
            failure_category=category,
        )

    def _failed(
        self,
        state: PlanExecutionState,
        node_id: str,
        category: str,
        reason: str,
    ) -> PlanExecutionState:
        return replace(
            state.with_node(node_id, NodeStatus.FAILED, reason=reason).emit(
                "plan.node_failed",
                node_id=node_id,
                payload={"reason": reason, "failure_category": category},
            ),
            status=PlanRunStatus.FAILED,
            failure_category=category,
        )

    def _incomplete(
        self,
        state: PlanExecutionState,
        category: str,
        *,
        node_id: str | None = None,
    ) -> PlanExecutionState:
        return replace(
            state.emit(
                "bound.reached",
                node_id=node_id,
                payload={"bound": category},
            ),
            status=PlanRunStatus.INCOMPLETE,
            failure_category=category,
        )

    def _initial_failure(
        self,
        request: PlanningRequest,
        category: str,
        reason: str,
    ) -> DynamicPlanResult:
        empty = Plan(
            f"failed:{request.request_id}",
            request.goal,
            (),
            request.provenance,
        )
        state = replace(
            PlanExecutionState.initial(empty, request.observations).emit(
                "plan.failed",
                payload={"failure_category": category, "reason": reason},
            ),
            status=PlanRunStatus.FAILED,
            failure_category=category,
        )
        return DynamicPlanResult(state, (), False)


@dataclass(frozen=True, slots=True)
class _OneActionModel:
    action: Action

    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        _ = inputs
        return ProposalBatch.alternatives(self.action)


def _report_denial(report: ITESReport) -> str:
    for branch in report.branches:
        if branch.trace:
            reason = branch.trace[-1].reason
            if reason:
                return reason
    return "policy_denial"


__all__ = ["DynamicPlanExecutor", "DynamicPlanResult"]
