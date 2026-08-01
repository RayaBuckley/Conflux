"""Self-hosted AgentDojo matrix orchestration tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from conflux.experiments import (
    AgentDojoCell,
    AgentDojoCellResult,
    ExperimentProtocol,
    LocalModelSpec,
    agentdojo_matrix,
    run_agentdojo_comparison,
)
from conflux.ports import LocalModelPreflight, LocalModelRequest, LocalModelResponse


def _protocol() -> ExperimentProtocol:
    return ExperimentProtocol(
        id="agentdojo-local-v1",
        track="agentdojo",
        suite={"id": "workspace:user_task_17:injection_task_1", "version": "v1.2.2"},
        source_commit="a" * 40,
        inputs={},
        model=LocalModelSpec(
            "transformers",
            "local/test",
            "revision",
            "b" * 64,
            "local/test",
            "revision",
            "1",
            0,
            0.0,
            1.0,
            128,
            2048,
            "cpu",
            "float32",
            "test",
        ),
        prompts={"agent": "1"},
        seeds=(1, 2),
        repetitions=2,
        bounds={"max_model_calls": 4, "max_steps": 8},
        environment={"agentdojo": "0.1.35"},
        output_directory="runs/agentdojo-local-v1",
        rerun_command=("conflux", "benchmark", "agentdojo", "--execute-local"),
    )


@dataclass
class _Model:
    model_id: str = "local/test"

    def preflight(self) -> LocalModelPreflight:
        return LocalModelPreflight("transformers", self.model_id, True, "none", None)

    def generate(self, request: LocalModelRequest) -> LocalModelResponse:
        raise AssertionError(f"fake cell executor owns calls: {request.request_id}")


@dataclass
class _Executor:
    seen: list[str]

    def execute(self, cell: AgentDojoCell, model: _Model, max_model_calls: int) -> AgentDojoCellResult:
        assert model.model_id == "local/test"
        assert max_model_calls == 4
        self.seen.append(cell.id)
        return AgentDojoCellResult(
            cell,
            "complete",
            True,
            not cell.attacked or cell.defence == "ites",
            f"raw/{cell.id}.json",
            "c" * 64,
            ({"principal_context": ["user"], "decision": "allow"},),
            () if not cell.attacked or cell.defence == "ites" else ("security",),
            1,
            10,
            3,
            5,
        )


def test_matrix_is_complete_stable_and_uses_identical_model() -> None:
    protocol = _protocol()
    matrix = agentdojo_matrix(protocol)
    assert len(matrix) == 16
    assert matrix == agentdojo_matrix(protocol)
    executor = _Executor([])
    result = run_agentdojo_comparison(protocol, _Model(), executor)  # type: ignore[arg-type]
    assert executor.seen == [cell.id for cell in matrix]
    assert len(result["cells"]) == 16  # type: ignore[arg-type]
    assert result["failure_counts"]["security"] == 4  # type: ignore[index]
    assert result["complete"] is True


def test_preflight_identity_and_failure_taxonomy_fail_closed() -> None:
    executor = _Executor([])
    with pytest.raises(ValueError, match="identity"):
        run_agentdojo_comparison(_protocol(), _Model("wrong"), executor)  # type: ignore[arg-type]
    cell = agentdojo_matrix(_protocol())[0]
    with pytest.raises(ValueError, match="unknown_agentdojo_failure"):
        AgentDojoCellResult(cell, "incomplete", None, None, None, None, (), ("invented",), 0, None, None, 0)


def test_matrix_requires_model_protocol() -> None:
    protocol = _protocol()
    object.__setattr__(protocol, "model", None)
    with pytest.raises(ValueError, match="with_model"):
        agentdojo_matrix(protocol)
