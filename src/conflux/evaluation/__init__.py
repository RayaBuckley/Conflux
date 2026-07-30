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
    plan_trace_records,
    replay_plan_trace,
    trace_records,
    write_plan_result,
    write_plan_trace,
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
    "plan_trace_records",
    "replay_plan_trace",
    "write_plan_trace",
    "write_plan_result",
    "write_result",
    "write_trace",
]
