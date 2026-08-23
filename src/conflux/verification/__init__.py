"""Serializable formal-verification IR and optional backends."""

from .defence_models import (
    dual_llm_baseline_ir,
    dual_llm_native_property_ir,
    ites_defective_requester_only_ir,
    ites_reference_ir,
)
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
from .self_composition import (
    SELF_COMPOSITION_SCHEMA_VERSION,
    SecretPartition,
    construct_product_ir,
)
from .synthesis import (
    SYNTHESIS_SCHEMA_VERSION,
    ControllerDecision,
    ControllerStrategy,
    FiniteInstance,
    SynthesisResult,
    default_instance,
    evaluate_strategy,
    run_synthesis_experiment,
    synthesise_controller,
)
from .z3_backend import verify_with_z3

__all__ = [
    "Assignment",
    "ControllerDecision",
    "ControllerStrategy",
    "DifferentialConformanceResult",
    "Expression",
    "ExpressionKind",
    "EffectSummary",
    "FiniteInstance",
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
    "SELF_COMPOSITION_SCHEMA_VERSION",
    "SYNTHESIS_SCHEMA_VERSION",
    "SafetyInvariant",
    "SecretPartition",
    "Sort",
    "StateVariable",
    "SynthesisResult",
    "TransitionRule",
    "VerificationIR",
    "VerificationReduction",
    "WitnessLiftingEvidence",
    "abstract_plan",
    "compare_cone_of_influence",
    "construct_product_ir",
    "default_instance",
    "differential_conformance",
    "dual_llm_baseline_ir",
    "dual_llm_native_property_ir",
    "evaluate",
    "evaluate_strategy",
    "expression_variables",
    "initial_state",
    "ites_defective_requester_only_ir",
    "ites_reference_ir",
    "reduce_cone_of_influence",
    "reference_safety_check",
    "run_synthesis_experiment",
    "successors",
    "synthesise_controller",
    "verify_with_z3",
    "verify_plan",
]
