"""Interactive state uses canonical mediation and certificate-bound execution."""

from __future__ import annotations

from pathlib import Path

import pytest

from conflux.adapters.models import ScriptedModel
from conflux.adapters.providers import RecordingExecutor
from conflux.adapters.scenarios import load_scenario
from conflux.application import ChatRuntime
from conflux.cli import EXIT_OK, EXIT_USAGE, main
from conflux.domain import Principal
from conflux.ites import MediatingITES, TransitionKernel

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples" / "basic.yaml"


def test_chat_turn_retains_session_and_mediates_the_only_effect() -> None:
    scenario = load_scenario(SCENARIO)
    human = min(scenario.session.participants)
    executor = RecordingExecutor()
    runtime = ChatRuntime(
        scenario.environment,
        scenario.session,
        human,
        MediatingITES(TransitionKernel(scenario.pipeline)),
        ScriptedModel((scenario.model,), repeat_last=True),
        executor,
    )
    original_data = len(runtime.environment.data)
    turn = runtime.submit("write the output")
    assert turn.executed
    assert executor.executed == ["write-output"]
    assert len(runtime.environment.data) == original_data + 1
    assert runtime.environment.data[-1].authors == frozenset({human})
    assert runtime.reports == [turn.report]


def test_chat_rejects_empty_input_and_nonparticipant() -> None:
    scenario = load_scenario(SCENARIO)
    runtime = ChatRuntime(
        scenario.environment,
        scenario.session,
        min(scenario.session.participants),
        MediatingITES(TransitionKernel(scenario.pipeline)),
        ScriptedModel((scenario.model,)),
        RecordingExecutor(),
    )
    with pytest.raises(ValueError, match="non-empty"):
        runtime.submit("")
    with pytest.raises(ValueError, match="participant"):
        ChatRuntime(
            scenario.environment,
            scenario.session,
            Principal("mallory", "Mallory"),
            MediatingITES(TransitionKernel(scenario.pipeline)),
            ScriptedModel((scenario.model,)),
            RecordingExecutor(),
        )


def test_chat_cli_fails_closed_without_optional_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MISSING_MODEL_KEY", raising=False)
    assert (
        main(
            [
                "chat",
                "--scenario",
                str(SCENARIO),
                "--endpoint",
                "https://model.example/v1/chat/completions",
                "--model",
                "test",
                "--api-key-env",
                "MISSING_MODEL_KEY",
            ]
        )
        == EXIT_USAGE
    )


def test_chat_cli_ctrl_c_is_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_MODEL_KEY", "key")
    monkeypatch.setattr(OpenAICompatibleAvailable, "available", lambda self: True)
    monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(
        "conflux.cli.OpenAICompatibleModel",
        OpenAICompatibleAvailable,
    )
    assert (
        main(
            [
                "chat",
                "--scenario",
                str(SCENARIO),
                "--endpoint",
                "https://model.example/v1/chat/completions",
                "--model",
                "test",
                "--api-key-env",
                "TEST_MODEL_KEY",
            ]
        )
        == EXIT_OK
    )


class OpenAICompatibleAvailable:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.api_key_env = str(kwargs["api_key_env"])

    def available(self) -> bool:
        return True

    def propose(self, inputs: tuple[object, ...]) -> object:
        raise AssertionError("Ctrl-C happens before proposal")
