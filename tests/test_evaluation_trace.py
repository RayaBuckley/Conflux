"""Regression tests for deterministic one-shot evaluation traces."""

from __future__ import annotations

from conflux.core import Principal
from conflux.ites import MediatingITES
from conflux.sled.environment import Data, Environment
from conflux.sled.evaluator import Evaluator


def test_one_shot_evaluator_emits_deterministic_completion_trace() -> None:
    principal = Principal("p", "Principal")
    evaluator = Evaluator(
        environment=Environment(name="fixture"),
        defence=MediatingITES(),
        llm_call=lambda _inputs: frozenset(),
    )

    result = evaluator.run([Data(authors=frozenset({principal}), readers=frozenset({principal}), tag="x")])

    assert result.trace[0].run_id == "fixture:one-shot"
    assert result.trace[0].to_dict()["schema_version"] == "1"
