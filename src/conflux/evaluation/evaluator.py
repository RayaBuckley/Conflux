"""Explicit one-shot mediation and verification services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from conflux.domain import Artifact, EnvironmentSnapshot, Session
from conflux.ites import ITESReport, MediatingITES
from conflux.ports import ModelPort

from .model_checking import (
    ActionT,
    ExplicitStateChecker,
    SafetyProperty,
    StateT,
    TransitionSystem,
    VerificationBounds,
    VerificationResult,
)


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Outcome of a one-shot ITES mediation run."""

    report: ITESReport

    @property
    def secure(self) -> bool:
        """Whether all security assessments in the report hold."""
        return all(assessment.holds for assessment in self.report.assessments)


@dataclass(frozen=True, slots=True)
class Evaluator:
    """Runs explicit one-shot mediation over an ITES mediator."""

    mediator: MediatingITES

    def evaluate(
        self,
        *,
        environment: EnvironmentSnapshot,
        session: Session,
        initial_inputs: tuple[Artifact[Any], ...],
        model: ModelPort,
        max_model_calls: int = 3,
    ) -> EvaluationResult:
        """Execute the mediator against the given session and inputs."""
        return EvaluationResult(
            self.mediator.run(
                environment=environment,
                session=session,
                initial_inputs=initial_inputs,
                model=model,
                max_model_calls=max_model_calls,
            )
        )


@dataclass(frozen=True, slots=True)
class VerificationEvaluator:
    """Verifies a transition system against safety properties via model checking."""

    checker: ExplicitStateChecker = ExplicitStateChecker()

    def verify(
        self,
        system: TransitionSystem[StateT, ActionT],
        properties: tuple[SafetyProperty[StateT, ActionT], ...],
        bounds: VerificationBounds = VerificationBounds(),
    ) -> VerificationResult[StateT, ActionT]:
        """Run the explicit-state checker and return the verification result."""
        return self.checker.verify(system, properties, bounds)


__all__ = ["EvaluationResult", "Evaluator", "VerificationEvaluator"]
