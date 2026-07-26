"""Benchmark-independent evaluation value types and trace contracts."""

from .records import TRACE_SCHEMA_VERSION, TraceRecord


def __getattr__(name: str) -> object:
    """Load evaluator/reporting services lazily to avoid initialization cycles."""
    if name in {"EvaluationResult", "Evaluator", "ExhaustiveEvaluationResult", "ExhaustiveEvaluator"}:
        from .services import EvaluationResult, Evaluator, ExhaustiveEvaluationResult, ExhaustiveEvaluator

        return {
            "EvaluationResult": EvaluationResult,
            "Evaluator": Evaluator,
            "ExhaustiveEvaluationResult": ExhaustiveEvaluationResult,
            "ExhaustiveEvaluator": ExhaustiveEvaluator,
        }[name]
    if name in {"EvaluationSummary", "summarise_branching"}:
        from .reporting import EvaluationSummary, summarise_branching

        return {"EvaluationSummary": EvaluationSummary, "summarise_branching": summarise_branching}[name]
    raise AttributeError(name)

__all__ = [
    "EvaluationResult",
    "Evaluator",
    "EvaluationSummary",
    "ExhaustiveEvaluationResult",
    "ExhaustiveEvaluator",
    "TRACE_SCHEMA_VERSION",
    "TraceRecord",
    "summarise_branching",
]
