"""Application facade for mediation and certificate-bound execution."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import EnvironmentSnapshot, Session, action_fingerprint
from conflux.ites import (
    ActionOutcome,
    AuthorisedBranch,
    AuthorisedPlan,
    BranchStatus,
    DecisionCertificate,
    ITESReport,
    MediatingITES,
)
from conflux.ports import ExecutorPort, ModelPort, ProviderResult


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Outcome of executing a single authorised branch through the executor."""

    provider: ProviderResult
    report: ITESReport


@dataclass(frozen=True, slots=True)
class PlanExecutionResult:
    """Outcome of executing a multi-step authorised plan through the executor."""

    providers: tuple[ProviderResult, ...]
    report: ITESReport
    completed: bool


@dataclass(frozen=True, slots=True)
class MediationService:
    """Application facade that evaluates and executes actions through the ITES boundary."""

    mediator: MediatingITES

    def evaluate(
        self,
        *,
        environment: EnvironmentSnapshot,
        session: Session,
        initial_inputs: tuple[object, ...],
        model: ModelPort,
        max_model_calls: int = 3,
    ) -> ITESReport:
        """Run the mediator over the environment and inputs, returning the ITES report."""
        from conflux.domain import Artifact

        if not all(isinstance(item, Artifact) for item in initial_inputs):
            raise TypeError("initial_inputs must contain Artifacts")
        artifacts = tuple(item for item in initial_inputs if isinstance(item, Artifact))
        return self.mediator.run(
            environment=environment,
            session=session,
            initial_inputs=artifacts,
            model=model,
            max_model_calls=max_model_calls,
        )

    def execute(
        self,
        *,
        report: ITESReport,
        branch: AuthorisedBranch,
        executor: ExecutorPort,
        environment: EnvironmentSnapshot,
        session: Session,
    ) -> ExecutionResult:
        """Execute a single authorised branch after re-validating its certificate."""
        if branch.certificate.action_fingerprint != action_fingerprint(branch.action):
            return ExecutionResult(
                ProviderResult(False, error="certificate_action_mismatch"),
                report,
            )
        report_branch = next(
            (item for item in report.branches if item.branch_id == branch.branch_id),
            None,
        )
        if report_branch is None or report_branch.certificate is None or report_branch.certificate.id != branch.certificate.id:
            return ExecutionResult(
                ProviderResult(False, error="certificate_report_mismatch"),
                report,
            )
        fresh = self.mediator.kernel.decisions.decide(
            session=session,
            action=branch.action,
            context=branch.decision.context,
            environment=environment,
        )
        fresh_certificate = DecisionCertificate.issue(
            action=branch.action,
            context=fresh.context,
            branch_id=branch.branch_id,
            decision=fresh,
        )
        if not fresh.allowed or fresh_certificate.id != branch.certificate.id:
            recorded = report.record_step_outcome(
                branch_id=branch.branch_id,
                action=branch.action,
                decision=fresh,
                outcome=ActionOutcome.BLOCKED,
                reason="execution_reauthorisation_denied",
                terminal=True,
            )
            return ExecutionResult(
                ProviderResult(False, error="execution_reauthorisation_denied"),
                recorded,
            )
        provider = executor.execute(
            branch.action,
            certificate_id=branch.certificate.id,
            action_fingerprint=branch.certificate.action_fingerprint,
        )
        recorded = report.record_step_outcome(
            branch_id=branch.branch_id,
            action=branch.action,
            decision=fresh,
            outcome=(ActionOutcome.EXECUTED if provider.success else ActionOutcome.PROVIDER_FAILED),
            reason=provider.error or "provider_succeeded",
            terminal=True,
        )
        return ExecutionResult(provider, recorded)

    def execute_plan(
        self,
        *,
        report: ITESReport,
        plan: AuthorisedPlan,
        executor: ExecutorPort,
        environment: EnvironmentSnapshot,
        session: Session,
    ) -> PlanExecutionResult:
        """Execute a multi-step authorised plan, re-authorising each step before dispatch."""
        branch = next(
            (item for item in report.branches if item.branch_id == plan.branch_id),
            None,
        )
        expected = tuple(step.certificate.id for step in plan.steps)
        if (
            branch is None
            or branch.status != BranchStatus.AUTHORISED
            or tuple(step.certificate.id for step in branch.authorised_steps) != expected
        ):
            return PlanExecutionResult(
                (ProviderResult(False, error="plan_report_mismatch"),),
                report,
                False,
            )
        current = report
        providers: list[ProviderResult] = []
        for index, step in enumerate(plan.steps):
            terminal = index == len(plan.steps) - 1
            fresh = self.mediator.kernel.decisions.decide(
                session=session,
                action=step.action,
                context=step.decision.context,
                environment=environment,
            )
            fresh_certificate = DecisionCertificate.issue(
                action=step.action,
                context=fresh.context,
                branch_id=step.certificate.branch_id,
                decision=fresh,
            )
            if not fresh.allowed or fresh_certificate.id != step.certificate.id:
                provider = ProviderResult(False, error="execution_reauthorisation_denied")
                providers.append(provider)
                current = current.record_step_outcome(
                    branch_id=plan.branch_id,
                    action=step.action,
                    decision=fresh,
                    outcome=ActionOutcome.BLOCKED,
                    reason="execution_reauthorisation_denied",
                    terminal=True,
                )
                return PlanExecutionResult(tuple(providers), current, False)
            provider = executor.execute(
                step.action,
                certificate_id=step.certificate.id,
                action_fingerprint=step.certificate.action_fingerprint,
            )
            providers.append(provider)
            current = current.record_step_outcome(
                branch_id=plan.branch_id,
                action=step.action,
                decision=fresh,
                outcome=(ActionOutcome.EXECUTED if provider.success else ActionOutcome.PROVIDER_FAILED),
                reason=provider.error or "provider_succeeded",
                terminal=terminal or not provider.success,
            )
            if not provider.success:
                return PlanExecutionResult(tuple(providers), current, False)
        return PlanExecutionResult(tuple(providers), current, True)


__all__ = ["ExecutionResult", "MediationService", "PlanExecutionResult"]
