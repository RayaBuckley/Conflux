"""
Tests for the SLED benchmark runner.

These tests verify that benchmark orchestration connects task suites,
scenarios, evaluators, and defences without mutating the underlying objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.core import Artifact, Principal
from conflux.ites import ITES, Guarantee, ITESReport
from conflux.sled import Data, Environment, Scenario, StaticTaskSuite
from conflux.sled.benchmark_runner import BenchmarkRunner, run_suite
from conflux.sled.task_suite import BenchmarkTask


@dataclass(frozen=True, slots=True)
class PrimitiveProposal:
    action: str


class RecordingITES(ITES):
    def __init__(self) -> None:
        self.seen_calls: list[frozenset[Artifact[object]]] = []
        self.seen_environments: list[object] = []

    def run(
        self,
        environment: object,
        initial_inputs: frozenset[Artifact[object]],
        llm_call,
        declare,
    ) -> ITESReport:
        self.seen_environments.append(environment)
        self.seen_calls.append(initial_inputs)

        proposals = llm_call(initial_inputs)
        for proposal in proposals:
            declare(proposal)

        return ITESReport(
            guarantees=frozenset(
                {
                    Guarantee(
                        name="bounded_llm_calls",
                        holds=True,
                        details="dummy defence report",
                    )
                }
            ),
            declared_actions=frozenset(proposals),
            blocked_actions=frozenset(),
        )


def _make_suite() -> tuple[StaticTaskSuite, Data]:
    alice = Principal("alice", "Alice")
    seed = Data(
        authors=frozenset({alice}),
        readers=frozenset({alice}),
        tag="seed",
    )
    scenario = Scenario(
        name="basic-scenario",
        environment=Environment(data=frozenset({seed})),
        initial_inputs=frozenset({seed}),
        max_llm_calls=3,
    )
    task = BenchmarkTask(name="basic-task", scenario=scenario)
    suite = StaticTaskSuite.from_iterable("basic-suite", [task])
    return suite, seed


def test_benchmark_runner_executes_one_task() -> None:
    suite, seed = _make_suite()
    defence = RecordingITES()

    def llm_call(inputs: frozenset[Artifact[object]]) -> frozenset[object]:
        _ = inputs
        return frozenset({PrimitiveProposal(action="approve")})

    result = BenchmarkRunner(
        suite=suite,
        defence=defence,
        llm_call=llm_call,
    ).run()

    assert result.suite_name == "basic-suite"
    assert result.total_tasks == 1
    assert result.total_declared == 1
    assert result.total_blocked == 0
    assert len(result.cases) == 1
    assert result.cases[0].task_name == "basic-task"
    assert result.cases[0].scenario is not None
    assert result.cases[0].scenario.initial_inputs == frozenset({seed})
    assert result.cases[0].result is not None
    assert result.cases[0].result.report.declared_actions == frozenset(
        {PrimitiveProposal(action="approve")}
    )


def test_benchmark_runner_calls_defence_with_environment_and_inputs() -> None:
    suite, seed = _make_suite()
    defence = RecordingITES()

    def llm_call(inputs: frozenset[Artifact[object]]) -> frozenset[object]:
        _ = inputs
        return frozenset({PrimitiveProposal(action="approve")})

    result = run_suite(
        suite=suite,
        defence=defence,
        llm_call=llm_call,
    )

    assert defence.seen_environments == [result.cases[0].scenario.environment]
    assert len(defence.seen_calls) == 1
    assert len(defence.seen_calls[0]) == 1
    artifact = next(iter(defence.seen_calls[0]))
    assert artifact.value == seed
    assert artifact.provenance.principals == frozenset({Principal("alice", "Alice")})
    assert artifact.provenance.operations == frozenset({"sled_input"})
    assert artifact.provenance.tags == frozenset({"seed"})


def test_benchmark_runner_reports_passed_cases() -> None:
    suite, _ = _make_suite()
    defence = RecordingITES()

    def llm_call(inputs: frozenset[Artifact[object]]) -> frozenset[object]:
        _ = inputs
        return frozenset({PrimitiveProposal(action="approve")})

    result = run_suite(
        suite=suite,
        defence=defence,
        llm_call=llm_call,
    )

    assert result.passed_cases == 1
    assert result.failed_cases == 0
