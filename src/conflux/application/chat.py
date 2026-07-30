"""Interactive turns routed through the same ITES and executor boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from conflux.domain import DataItem, EnvironmentSnapshot, Principal, Session
from conflux.ites import ITESReport, MediatingITES
from conflux.ports import ExecutorPort, ModelPort

from .mediate import MediationService


@dataclass(frozen=True, slots=True)
class ChatTurn:
    report: ITESReport
    executed: bool
    reason: str


@dataclass(slots=True)
class ChatRuntime:
    environment: EnvironmentSnapshot
    session: Session
    human: Principal
    mediator: MediatingITES
    model: ModelPort
    executor: ExecutorPort
    reports: list[ITESReport] = field(default_factory=list)
    turn: int = 0

    def __post_init__(self) -> None:
        if self.human not in self.session.participants:
            raise ValueError("chat Principal must be a session participant")

    def submit(self, text: str) -> ChatTurn:
        if not text:
            raise ValueError("chat input must be non-empty")
        self.turn += 1
        item = DataItem(
            id=f"chat-turn-{self.turn}",
            value=text,
            authors=frozenset({self.human}),
            readers=self.session.participants,
            label=f"Chat turn {self.turn}",
        )
        self.environment = replace(
            self.environment,
            data=self.environment.data + (item,),
            version=f"{self.environment.version}.{self.turn}",
        )
        service = MediationService(self.mediator)
        report = service.evaluate(
            environment=self.environment,
            session=self.session,
            initial_inputs=self.environment.artifacts(),
            model=self.model,
        )
        executed = False
        reason = "no_authorised_branch"
        if len(report.authorised_plans) == 1:
            plan_result = service.execute_plan(
                report=report,
                plan=report.authorised_plans[0],
                executor=self.executor,
                environment=self.environment,
                session=self.session,
            )
            report = plan_result.report
            executed = plan_result.completed
            reason = (
                "authorised_plan_executed"
                if executed
                else "plan_stopped_fail_closed"
            )
        elif len(report.authorised_branches) == 1:
            result = service.execute(
                report=report,
                branch=report.authorised_branches[0],
                executor=self.executor,
                environment=self.environment,
                session=self.session,
            )
            report = result.report
            executed = result.provider.success
            reason = (
                "authorised_branch_executed"
                if executed
                else result.provider.error or "provider_failed"
            )
        elif len(report.authorised_branches) > 1:
            reason = "branch_selection_required"
        self.reports.append(report)
        return ChatTurn(report, executed, reason)


__all__ = ["ChatRuntime", "ChatTurn"]
