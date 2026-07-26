"""
SLED reference model-level benchmark.

This module exists for comparison with prior work and external benchmark
families that evaluate model-level attacks.

The project's primary benchmark methodology remains system-level and abstract.
Model-level attacks are included only as reference adapters so results can be
compared against earlier approaches or external suites when useful.

This module therefore keeps model-level attacks deliberately lightweight and
clearly separated from the native SLED system benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from conflux.core import Principal

from .attack import Attack, AttackMetadata
from .environment import Data, Environment
from .scenario import Scenario
from .task_suite import BenchmarkExpectation, BenchmarkTask, StaticTaskSuite


@dataclass(frozen=True, slots=True)
class ModelAttackProfile:
    """
    Abstract description of a model-level attack.

    Attributes
    ----------
    name:
        Stable identifier for the attack.

    description:
        Human-readable summary.

    surface:
        The model-level surface being exercised, for example:
        - prompt_injection
        - indirect_prompt_injection
        - instruction_override
        - tool_output_poisoning
    """

    name: str
    description: str
    surface: str


@dataclass(frozen=True, slots=True)
class ModelLevelAttack(Attack):
    """
    Reference model-level benchmark attack.

    This attack is intended for comparison with model-oriented benchmark suites
    rather than as the project's main evaluation methodology.

    The implementation injects a malicious instruction-bearing data item into
    the scenario's initial inputs. This mirrors classic prompt-injection style
    evaluation without becoming tightly coupled to a specific model or external
    benchmark format.
    """

    profile: ModelAttackProfile
    injected_tag: str = "model_attack"
    inject_into_initial_inputs: bool = True

    @property
    def metadata(self) -> AttackMetadata:
        return AttackMetadata(
            name=self.profile.name,
            description=self.profile.description,
            category=self.profile.surface,
        )

    def apply(self, scenario: Scenario) -> Scenario:
        """
        Return a new scenario with the reference model-level attack applied.
        """
        environment = scenario.environment
        initial_inputs = set(scenario.initial_inputs)

        attacker = _reference_attacker_principal()

        malicious_data = Data(
            authors=frozenset({attacker}),
            readers=frozenset(),
            tag=self.injected_tag,
        )

        updated_environment = Environment(
            data=environment.data | frozenset({malicious_data})
        )

        if self.inject_into_initial_inputs:
            initial_inputs.add(malicious_data)

        return replace(
            scenario,
            environment=updated_environment,
            initial_inputs=frozenset(initial_inputs),
            name=f"{scenario.name}:{self.profile.name}",
        )


@dataclass(frozen=True, slots=True)
class ModelBenchmark:
    """
    A collection of reference model-level benchmark tasks.

    This benchmark family is not the primary SLED methodology. It exists so the
    project can compare against external model-level attack styles when needed.
    """

    name: str
    tasks: tuple[BenchmarkTask, ...]

    def suite(self) -> StaticTaskSuite:
        """
        Convert the benchmark definition into a static task suite.
        """
        return StaticTaskSuite.from_iterable(self.name, self.tasks)


def build_model_reference_benchmark(
    *,
    name: str,
    scenarios: Iterable[Scenario],
) -> StaticTaskSuite:
    """
    Build a reference benchmark suite from scenarios.

    Each scenario becomes a benchmark task with expectations that describe the
    comparison-oriented purpose of model-level evaluation.
    """
    tasks: list[BenchmarkTask] = []

    for index, scenario in enumerate(scenarios, start=1):
        tasks.append(
            BenchmarkTask(
                name=f"{name}-case-{index}",
                scenario=scenario,
                expectations=frozenset(
                    {
                        BenchmarkExpectation(
                            name="reference_only",
                            description=(
                                "This task is intended for comparison with "
                                "model-level external benchmarks."
                            ),
                        ),
                        BenchmarkExpectation(
                            name="detect_injected_instruction_flow",
                            description=(
                                "The defence should prevent injected model-level "
                                "instructions from causing unauthorised action."
                            ),
                        ),
                    }
                ),
            )
        )

    return StaticTaskSuite.from_iterable(name, tasks)


def _reference_attacker_principal() -> Principal:
    """
    Construct a synthetic attacker principal for reference model-level attacks.
    """
    return Principal(
        id="reference.model.attacker",
        name="Reference Model Attacker",
        principal_type="external",
    )


__all__ = [
    "ModelAttackProfile",
    "ModelBenchmark",
    "ModelLevelAttack",
    "build_model_reference_benchmark",
]
