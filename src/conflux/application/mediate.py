"""Application facade for mediation and certificate-bound execution."""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import EnvironmentSnapshot, Session, action_fingerprint
from conflux.ites import AuthorisedBranch, ITESReport, MediatingITES
from conflux.ports import ExecutorPort, ModelPort, ProviderResult


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    provider: ProviderResult
    report: ITESReport


@dataclass(frozen=True, slots=True)
class MediationService:
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
    ) -> ExecutionResult:
        if branch.certificate.action_fingerprint != action_fingerprint(branch.action):
            return ExecutionResult(
                ProviderResult(False, error="certificate_action_mismatch"),
                report,
            )
        report_branch = next(
            (item for item in report.branches if item.branch_id == branch.branch_id),
            None,
        )
        if (
            report_branch is None
            or report_branch.certificate is None
            or report_branch.certificate.id != branch.certificate.id
        ):
            return ExecutionResult(
                ProviderResult(False, error="certificate_report_mismatch"),
                report,
            )
        provider = executor.execute(
            branch.action,
            certificate_id=branch.certificate.id,
            action_fingerprint=branch.certificate.action_fingerprint,
        )
        recorded = report.record_execution(
            branch_id=branch.branch_id,
            success=provider.success,
            reason=provider.error or "provider_succeeded",
        )
        return ExecutionResult(provider, recorded)


__all__ = ["ExecutionResult", "MediationService"]
