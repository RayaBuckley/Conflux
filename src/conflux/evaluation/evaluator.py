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
    report: ITESReport

    @property
    def secure(self) -> bool:
        return all(assessment.holds for assessment in self.report.assessments)


@dataclass(frozen=True, slots=True)
class Evaluator:
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
    checker: ExplicitStateChecker = ExplicitStateChecker()

    def verify(
        self,
        system: TransitionSystem[StateT, ActionT],
        properties: tuple[SafetyProperty[StateT, ActionT], ...],
        bounds: VerificationBounds = VerificationBounds(),
    ) -> VerificationResult[StateT, ActionT]:
        return self.checker.verify(system, properties, bounds)


__all__ = ["EvaluationResult", "Evaluator", "VerificationEvaluator"]
