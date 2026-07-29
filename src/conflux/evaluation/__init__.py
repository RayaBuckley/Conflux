"""Benchmark-independent evaluation and native bounded verification."""

from .evaluator import EvaluationResult, Evaluator, VerificationEvaluator
from .model_checking import (
    Counterexample,
    ExplicitStateChecker,
    SafetyProperty,
    Transition,
    TransitionSystem,
    VerificationBounds,
    VerificationResult,
    VerificationVerdict,
)
from .properties import (
    ITESVerificationSystem,
    NoForbiddenObservation,
    NoUnauthorisedAuthorisation,
    PrincipalContextMonotonicity,
    ProvenancePreserved,
)

__all__ = [
    "Counterexample",
    "EvaluationResult",
    "Evaluator",
    "ExplicitStateChecker",
    "ITESVerificationSystem",
    "NoForbiddenObservation",
    "NoUnauthorisedAuthorisation",
    "PrincipalContextMonotonicity",
    "ProvenancePreserved",
    "SafetyProperty",
    "Transition",
    "TransitionSystem",
    "VerificationBounds",
    "VerificationEvaluator",
    "VerificationResult",
    "VerificationVerdict",
]
