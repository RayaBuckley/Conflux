"""
Tests for the reference model-level benchmark layer.

These tests ensure the model-oriented benchmark utilities remain available for
comparison with external benchmark suites, while staying clearly separated from
the native system-level SLED methodology.
"""

from __future__ import annotations

from conflux.core import Principal
from conflux.evaluation.environment import Data, Environment
from conflux.evaluation.model_benchmark import (
    ModelAttackProfile,
    ModelLevelAttack,
    build_model_reference_benchmark,
)
from conflux.evaluation.scenario import Scenario


def _make_scenario() -> Scenario:
    alice = Principal("alice", "Alice")
    seed = Data(
        authors=frozenset({alice}),
        readers=frozenset({alice}),
        tag="seed",
    )
    return Scenario(
        name="reference-scenario",
        environment=Environment(data=frozenset({seed})),
        initial_inputs=frozenset({seed}),
        max_llm_calls=3,
    )


def test_model_level_attack_adds_malicious_input() -> None:
    scenario = _make_scenario()

    attack = ModelLevelAttack(
        profile=ModelAttackProfile(
            name="prompt-injection-reference",
            description="Reference prompt injection for comparison.",
            surface="prompt_injection",
        ),
    )

    updated = attack.apply(scenario)

    assert updated.name == "reference-scenario:prompt-injection-reference"
    assert len(updated.environment.data) == len(scenario.environment.data) + 1
    assert len(updated.initial_inputs) == len(scenario.initial_inputs) + 1
    assert any(item.tag == "model_attack" for item in updated.environment.data)
    assert any(item.tag == "model_attack" for item in updated.initial_inputs)


def test_model_level_attack_metadata_reflects_profile() -> None:
    attack = ModelLevelAttack(
        profile=ModelAttackProfile(
            name="instruction-override",
            description="Reference instruction override attack.",
            surface="instruction_override",
        ),
    )

    assert attack.metadata.name == "instruction-override"
    assert attack.metadata.description == "Reference instruction override attack."
    assert attack.metadata.category == "instruction_override"


def test_build_model_reference_benchmark_creates_suite() -> None:
    scenario_one = _make_scenario()
    scenario_two = _make_scenario()

    suite = build_model_reference_benchmark(
        name="reference-model-suite",
        scenarios=[scenario_one, scenario_two],
    )

    tasks = list(suite.tasks())

    assert suite.name == "reference-model-suite"
    assert len(tasks) == 2
    assert tasks[0].name == "reference-model-suite-case-1"
    assert tasks[1].name == "reference-model-suite-case-2"
    assert any(
        expectation.name == "reference_only"
        for expectation in tasks[0].expectations
    )
    assert any(
        expectation.name == "detect_injected_instruction_flow"
        for expectation in tasks[0].expectations
    )
