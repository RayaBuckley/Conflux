"""Canonical evaluation services.

Purpose
Layer: evaluation/application boundary
Dependencies: canonical ITES contract and evaluation implementations.
Public API: one-shot and exhaustive evaluator/result classes.
Security/data invariants: evaluation invokes mediation and never defines policy.
Related documentation and tests: docs/EVALUATION.md, tests/test_evaluation_contract.py.
"""

from .evaluator import (
    EvaluationResult,
    Evaluator,
    ExhaustiveEvaluationResult,
    ExhaustiveEvaluator,
)

__all__ = ["EvaluationResult", "Evaluator", "ExhaustiveEvaluationResult", "ExhaustiveEvaluator"]
