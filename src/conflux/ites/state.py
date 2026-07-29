"""Immutable branch state, trace, certificate, and report values for ITES."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any

from conflux.domain import (
    Action,
    ActionDecision,
    Artifact,
    PrincipalContext,
    action_fingerprint,
    fingerprint,
    provenance_union,
)

TRACE_SCHEMA_VERSION = "2"
CERTIFICATE_SCHEMA_VERSION = "1"


class BranchStatus(StrEnum):
    ACTIVE = "active"
    AUTHORISED = "authorised"
    BLOCKED = "blocked"
    EXECUTED = "executed"
    PROVIDER_FAILED = "provider_failed"
    TERMINAL = "terminal"
    INCOMPLETE = "incomplete"


class ActionOutcome(StrEnum):
    PROPOSED = "proposed"
    AUTHORISED = "authorised"
    BLOCKED = "blocked"
    EXECUTED = "executed"
    PROVIDER_FAILED = "provider_failed"
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class TraceEvent:
    sequence: int
    branch_id: str
    parent_branch_id: str | None
    depth: int
    outcome: ActionOutcome
    context: PrincipalContext
    action: Action | None = None
    decision: ActionDecision | None = None
    reason: str = ""
    schema_version: str = TRACE_SCHEMA_VERSION

    @property
    def id(self) -> str:
        return fingerprint(
            {
                "branch_id": self.branch_id,
                "sequence": self.sequence,
                "outcome": self.outcome.value,
                "action_id": self.action.id if self.action else None,
            }
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "sequence": self.sequence,
            "branch_id": self.branch_id,
            "parent_branch_id": self.parent_branch_id,
            "depth": self.depth,
            "outcome": self.outcome.value,
            "context": self.context.to_dict(),
            "action_id": self.action.id if self.action else None,
            "action_fingerprint": action_fingerprint(self.action) if self.action else None,
            "decision": self.decision.to_dict() if self.decision else None,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class DecisionCertificate:
    id: str
    action_fingerprint: str
    context_fingerprint: str
    branch_id: str
    policy_versions: tuple[str, ...]
    decision: ActionDecision
    schema_version: str = CERTIFICATE_SCHEMA_VERSION

    @classmethod
    def issue(
        cls,
        *,
        action: Action,
        context: PrincipalContext,
        branch_id: str,
        decision: ActionDecision,
    ) -> "DecisionCertificate":
        policy_versions = tuple(
            f"{item.policy_id}@{item.policy_version}" for item in decision.decisions
        )
        action_hash = action_fingerprint(action)
        context_hash = context.fingerprint
        payload = {
            "action_fingerprint": action_hash,
            "context_fingerprint": context_hash,
            "branch_id": branch_id,
            "policy_versions": policy_versions,
            "decision": decision.to_dict(),
        }
        return cls(
            id=fingerprint(payload),
            action_fingerprint=action_hash,
            context_fingerprint=context_hash,
            branch_id=branch_id,
            policy_versions=policy_versions,
            decision=decision,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "action_fingerprint": self.action_fingerprint,
            "context_fingerprint": self.context_fingerprint,
            "branch_id": self.branch_id,
            "policy_versions": list(self.policy_versions),
            "decision": self.decision.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class AuthorisedStep:
    action: Action
    decision: ActionDecision
    certificate: DecisionCertificate


@dataclass(frozen=True, slots=True)
class BranchState:
    branch_id: str
    parent_branch_id: str | None
    depth: int
    inputs: tuple[Artifact[Any], ...]
    context: PrincipalContext
    status: BranchStatus = BranchStatus.ACTIVE
    model_calls: int = 0
    trace: tuple[TraceEvent, ...] = ()
    action: Action | None = None
    decision: ActionDecision | None = None
    certificate: DecisionCertificate | None = None
    authorised_steps: tuple[AuthorisedStep, ...] = ()

    @classmethod
    def initial(cls, inputs: tuple[Artifact[Any], ...]) -> "BranchState":
        if inputs:
            provenance = provenance_union(*(artifact.provenance for artifact in inputs))
            context = provenance.context
        else:
            context = PrincipalContext(unknown=True)
        return cls("root", None, 0, tuple(inputs), context)

    @property
    def state_key(self) -> str:
        return fingerprint(
            {
                "inputs": [artifact.fingerprint for artifact in self.inputs],
                "context": self.context.to_dict(),
                "depth": self.depth,
                "status": self.status.value,
                "model_calls": self.model_calls,
            }
        )

    def append(self, event: TraceEvent) -> "BranchState":
        return replace(self, trace=self.trace + (event,))


@dataclass(frozen=True, slots=True)
class AuthorisedBranch:
    action: Action
    decision: ActionDecision
    certificate: DecisionCertificate
    branch_id: str


@dataclass(frozen=True, slots=True)
class AuthorisedPlan:
    steps: tuple[AuthorisedStep, ...]
    branch_id: str


@dataclass(frozen=True, slots=True)
class SafetyAssessment:
    name: str
    holds: bool
    details: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "holds": self.holds,
            "details": self.details,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class ITESReport:
    run_id: str
    branches: tuple[BranchState, ...]
    assessments: tuple[SafetyAssessment, ...]
    model_calls: int
    max_model_calls: int
    incomplete: bool
    trace_schema_version: str = TRACE_SCHEMA_VERSION

    @property
    def authorised_branches(self) -> tuple[AuthorisedBranch, ...]:
        result: list[AuthorisedBranch] = []
        for branch in self.branches:
            if (
                branch.status == BranchStatus.AUTHORISED
                and branch.action is not None
                and branch.decision is not None
                and branch.certificate is not None
            ):
                result.append(
                    AuthorisedBranch(
                        branch.action,
                        branch.decision,
                        branch.certificate,
                        branch.branch_id,
                    )
                )
        return tuple(result)

    @property
    def authorised_plans(self) -> tuple[AuthorisedPlan, ...]:
        return tuple(
            AuthorisedPlan(branch.authorised_steps, branch.branch_id)
            for branch in self.branches
            if branch.status == BranchStatus.AUTHORISED and len(branch.authorised_steps) > 1
        )

    @property
    def proposed_count(self) -> int:
        return sum(
            event.outcome == ActionOutcome.PROPOSED
            for branch in self.branches
            for event in branch.trace
        )

    @property
    def blocked_count(self) -> int:
        return sum(branch.status == BranchStatus.BLOCKED for branch in self.branches)

    @property
    def authorised_count(self) -> int:
        return sum(branch.status == BranchStatus.AUTHORISED for branch in self.branches)

    @property
    def executed_count(self) -> int:
        return sum(branch.status == BranchStatus.EXECUTED for branch in self.branches)

    @property
    def provider_failed_count(self) -> int:
        return sum(branch.status == BranchStatus.PROVIDER_FAILED for branch in self.branches)

    @property
    def incomplete_count(self) -> int:
        return sum(branch.status == BranchStatus.INCOMPLETE for branch in self.branches)

    def record_execution(
        self,
        *,
        branch_id: str,
        success: bool,
        reason: str = "",
    ) -> "ITESReport":
        """Return a report containing one certificate-bound provider outcome."""
        updated: list[BranchState] = []
        found = False
        for branch in self.branches:
            if branch.branch_id != branch_id:
                updated.append(branch)
                continue
            if branch.status != BranchStatus.AUTHORISED:
                raise ValueError("only an authorised branch may record execution")
            if branch.action is None or branch.decision is None or branch.certificate is None:
                raise ValueError("authorised branch is missing decision evidence")
            found = True
            outcome = ActionOutcome.EXECUTED if success else ActionOutcome.PROVIDER_FAILED
            status = BranchStatus.EXECUTED if success else BranchStatus.PROVIDER_FAILED
            event = TraceEvent(
                sequence=len(branch.trace),
                branch_id=branch.branch_id,
                parent_branch_id=branch.parent_branch_id,
                depth=branch.depth,
                outcome=outcome,
                context=branch.context,
                action=branch.action,
                decision=branch.decision,
                reason=reason or ("provider_succeeded" if success else "provider_failed"),
            )
            updated.append(replace(branch, status=status, trace=branch.trace + (event,)))
        if not found:
            raise ValueError(f"unknown branch: {branch_id}")
        branches = tuple(updated)
        assessments = tuple(
            _execution_assessment(branches) if item.name == "no_unauthorised_execution" else item
            for item in self.assessments
        )
        return replace(self, branches=branches, assessments=assessments)

    def to_dict(self) -> dict[str, object]:
        return {
            "trace_schema_version": self.trace_schema_version,
            "run_id": self.run_id,
            "model_calls": self.model_calls,
            "max_model_calls": self.max_model_calls,
            "incomplete": self.incomplete,
            "proposed_count": self.proposed_count,
            "authorised_count": self.authorised_count,
            "blocked_count": self.blocked_count,
            "executed_count": self.executed_count,
            "provider_failed_count": self.provider_failed_count,
            "incomplete_count": self.incomplete_count,
            "assessments": [assessment.to_dict() for assessment in self.assessments],
            "branches": [
                {
                    "branch_id": branch.branch_id,
                    "parent_branch_id": branch.parent_branch_id,
                    "depth": branch.depth,
                    "status": branch.status.value,
                    "input_ids": [item.id for item in branch.inputs],
                    "context": branch.context.to_dict(),
                    "model_calls": branch.model_calls,
                    "action_id": branch.action.id if branch.action else None,
                    "certificate": branch.certificate.to_dict() if branch.certificate else None,
                    "authorised_steps": [
                        {
                            "action_id": step.action.id,
                            "certificate": step.certificate.to_dict(),
                        }
                        for step in branch.authorised_steps
                    ],
                    "trace": [event.to_dict() for event in branch.trace],
                }
                for branch in sorted(self.branches, key=lambda item: item.branch_id)
            ],
        }


def _execution_assessment(branches: tuple[BranchState, ...]) -> SafetyAssessment:
    events = tuple(
        event
        for branch in branches
        for event in branch.trace
        if event.outcome == ActionOutcome.EXECUTED
    )
    holds = all(event.decision is not None and event.decision.allowed for event in events)
    return SafetyAssessment(
        "no_unauthorised_execution",
        holds,
        "Executed actions, not rejected proposals, determine this property.",
        (f"executed={len(events)}",),
    )


__all__ = [
    "ActionOutcome",
    "AuthorisedBranch",
    "AuthorisedPlan",
    "AuthorisedStep",
    "BranchState",
    "BranchStatus",
    "CERTIFICATE_SCHEMA_VERSION",
    "DecisionCertificate",
    "ITESReport",
    "SafetyAssessment",
    "TRACE_SCHEMA_VERSION",
    "TraceEvent",
]
