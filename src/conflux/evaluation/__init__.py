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
from .records import (
    DeterministicClock,
    RunResult,
    RunStatus,
    UtilityOutcome,
    trace_records,
    write_result,
    write_trace,
)

__all__ = [
    "Counterexample",
    "DeterministicClock",
    "EvaluationResult",
    "Evaluator",
    "ExplicitStateChecker",
    "ITESVerificationSystem",
    "NoForbiddenObservation",
    "NoUnauthorisedAuthorisation",
    "PrincipalContextMonotonicity",
    "ProvenancePreserved",
    "RunResult",
    "RunStatus",
    "SafetyProperty",
    "Transition",
    "TransitionSystem",
    "UtilityOutcome",
    "VerificationBounds",
    "VerificationEvaluator",
    "VerificationResult",
    "VerificationVerdict",
    "trace_records",
    "write_result",
    "write_trace",
]
