"""Tests for canonical evaluation service exports."""

from conflux.evaluation import EvaluationResult, Evaluator, ExhaustiveEvaluationResult, ExhaustiveEvaluator


def test_evaluation_services_have_distinct_result_types() -> None:
    assert Evaluator is not ExhaustiveEvaluator
    assert EvaluationResult is not ExhaustiveEvaluationResult
