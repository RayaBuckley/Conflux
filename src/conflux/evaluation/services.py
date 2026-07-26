"""Canonical evaluation service imports over the current SLED implementation.

Purpose
Layer: evaluation/application boundary
Dependencies: canonical ITES contract and the staged SLED compatibility facade.
Public API: one-shot and exhaustive evaluator/result classes.
Security/data invariants: evaluation invokes mediation and never defines policy.
Related documentation and tests: docs/EVALUATION.md, tests/test_evaluation_contract.py.
"""

from conflux.sled.evaluator import (
    EvaluationResult,
    Evaluator,
    ExhaustiveEvaluationResult,
    ExhaustiveEvaluator,
)

__all__ = ["EvaluationResult", "Evaluator", "ExhaustiveEvaluationResult", "ExhaustiveEvaluator"]
