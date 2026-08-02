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
from .reduction import (
    REDUCTION_SCHEMA_VERSION,
    ReductionComparison,
    ReferenceSafetyResult,
    VerificationReduction,
    WitnessLiftingEvidence,
    compare_cone_of_influence,
    expression_variables,
    reduce_cone_of_influence,
    reference_safety_check,
)
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
    "REDUCTION_SCHEMA_VERSION",
    "ReductionComparison",
    "ReferenceSafetyResult",
    "RuntimeTransitionRecord",
    "SafetyInvariant",
    "Sort",
    "StateVariable",
    "TransitionRule",
    "VerificationIR",
    "VerificationReduction",
    "WitnessLiftingEvidence",
    "abstract_plan",
    "compare_cone_of_influence",
    "differential_conformance",
    "evaluate",
    "expression_variables",
    "initial_state",
    "reduce_cone_of_influence",
    "reference_safety_check",
    "successors",
    "verify_with_z3",
    "verify_plan",
]
