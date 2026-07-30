"""Serializable formal-verification IR and optional backends."""

from .interpreter import (
    DifferentialConformanceResult,
    RuntimeTransitionRecord,
    differential_conformance,
    evaluate,
    initial_state,
    successors,
)
from .ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)
from .nuxmv_backend import NuXmvBackend, NuXmvOutcome, NuXmvRunner
from .plan_ir import EffectSummary, PlanAbstraction, abstract_plan, verify_plan
from .results import FormalVerdict, FormalVerificationResult
from .z3_backend import verify_with_z3

__all__ = [
    "Assignment",
    "DifferentialConformanceResult",
    "Expression",
    "ExpressionKind",
    "EffectSummary",
    "FormalVerdict",
    "FormalVerificationResult",
    "NuXmvBackend",
    "NuXmvOutcome",
    "NuXmvRunner",
    "PlanAbstraction",
    "RuntimeTransitionRecord",
    "SafetyInvariant",
    "Sort",
    "StateVariable",
    "TransitionRule",
    "VerificationIR",
    "abstract_plan",
    "differential_conformance",
    "evaluate",
    "initial_state",
    "successors",
    "verify_with_z3",
    "verify_plan",
]
