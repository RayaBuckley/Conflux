"""Offline structured-output tests for optional model adapters."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field

import pytest

from conflux.adapters.models import (
    HuggingFaceCausalModel,
    ModelOutputError,
    ModelProviderError,
    OpenAICompatibleModel,
)
from conflux.adapters.models.openai_compatible import HTTPResponse
from conflux.application import DecisionPipeline
from conflux.domain import Artifact, EnvironmentSnapshot, Provenance, Session
from conflux.evaluation import RunResult, trace_records
from conflux.ites import MediatingITES, TransitionKernel


def _proposal(*, resource: bool = False) -> str:
    action: dict[str, object] = {
        "id": "noop",
        "kind": "no_op",
        "visibility": "internal",
        "input_ids": [],
        "label": "safe",
    }
    if resource:
        action = {
            "id": "write",
            "kind": "primitive",
            "visibility": "internal",
            "input_ids": ["input"],
            "operation": "write",
            "permission": "write",
            "resource": {
                "provider": "filesystem",
                "resource_id": "out.txt",
                "resource_type": "document",
                "attributes": {},
            },
        }
    return json.dumps(
        {
            "schema_version": "1",
            "mode": "alternatives",
            "proposals": [action],
        }
    )


@dataclass
class Response:
    status_code: int
    payload: object

    @property
    def text(self) -> str:
        return json.dumps(self.payload)

    def json(self) -> object:
        return self.payload


@dataclass
class Transport:
    responses: list[Response]
    calls: list[dict[str, object]] = field(default_factory=list)

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, object],
        timeout: float,
    ) -> HTTPResponse:
        self.calls.append(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        return self.responses.pop(0)


def _body(content: str, *, secret: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "choices": [{"message": {"content": content}}],
    }
    if secret:
        result["debug_token"] = secret
    return result


def test_openai_compatible_uses_environment_secret_and_redacts_retention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "secret-value"
    monkeypatch.setenv("TEST_MODEL_KEY", secret)
    transport = Transport([Response(200, _body(_proposal(), secret=secret))])
    model = OpenAICompatibleModel(
        "https://model.example/v1/chat/completions",
        "test-model",
        frozenset(),
        api_key_env="TEST_MODEL_KEY",
        transport=transport,
    )
    batch = model.propose(())
    assert batch.proposals[0].id == "noop"
    assert transport.calls[0]["headers"] == {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
    }
    retained = json.dumps(model.responses[0].to_dict())
    assert secret not in retained
    assert "[REDACTED]" in retained
    assert secret not in repr(model)


def test_openai_compatible_retries_transient_status_and_rejects_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_MODEL_KEY", "key")
    transport = Transport(
        [
            Response(429, {"error": "busy"}),
            Response(200, _body(_proposal())),
        ]
    )
    model = OpenAICompatibleModel(
        "http://127.0.0.1:8000/v1/chat/completions",
        "local",
        frozenset(),
        api_key_env="TEST_MODEL_KEY",
        max_retries=1,
        backoff_seconds=0,
        transport=transport,
    )
    assert model.propose(()).proposals[0].id == "noop"
    assert len(transport.calls) == 2

    malformed = OpenAICompatibleModel(
        "https://model.example/v1/chat/completions",
        "test",
        frozenset(),
        api_key_env="TEST_MODEL_KEY",
        transport=Transport([Response(200, _body('{"unknown":true}'))]),
    )
    with pytest.raises(ModelOutputError, match="malformed"):
        malformed.propose(())


def test_openai_compatible_blocks_unknown_resources_and_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_MODEL_KEY", "key")
    artifact = Artifact("input", "x", Provenance.unknown())
    unknown = OpenAICompatibleModel(
        "https://model.example/v1/chat/completions",
        "test",
        frozenset(),
        api_key_env="TEST_MODEL_KEY",
        transport=Transport([Response(200, _body(_proposal(resource=True)))]),
    )
    with pytest.raises(ModelOutputError, match="unknown_resource"):
        unknown.propose((artifact,))

    denied = OpenAICompatibleModel(
        "https://model.example/v1/chat/completions",
        "test",
        frozenset(),
        api_key_env="TEST_MODEL_KEY",
        max_retries=0,
        transport=Transport([Response(401, {"error": "denied"})]),
    )
    with pytest.raises(ModelProviderError, match="401"):
        denied.propose(())
    monkeypatch.delenv("TEST_MODEL_KEY")
    assert not denied.available()
    with pytest.raises(ModelProviderError, match="missing_secret"):
        denied.propose(())


def test_openai_configuration_transport_failures_and_known_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        OpenAICompatibleModel("http://remote.example/v1", "test", frozenset())
    with pytest.raises(ValueError, match="retry"):
        OpenAICompatibleModel(
            "https://model.example/v1",
            "test",
            frozenset(),
            timeout_seconds=0,
        )
    monkeypatch.setenv("TEST_MODEL_KEY", "key")
    artifact = Artifact("input", "x", Provenance.unknown())
    allowed = OpenAICompatibleModel(
        "https://model.example/v1",
        "test",
        frozenset({("filesystem", "document", "out.txt")}),
        api_key_env="TEST_MODEL_KEY",
        transport=Transport([Response(200, _body(_proposal(resource=True)))]),
    )
    assert allowed.available()
    assert allowed.propose((artifact,)).proposals[0].id == "write"

    class BrokenTransport:
        def post(
            self,
            url: str,
            *,
            headers: dict[str, str],
            json: dict[str, object],
            timeout: float,
        ) -> HTTPResponse:
            _ = url, headers, json, timeout
            raise OSError("offline")

    failed = OpenAICompatibleModel(
        "https://model.example/v1",
        "test",
        frozenset(),
        api_key_env="TEST_MODEL_KEY",
        max_retries=1,
        backoff_seconds=0,
        transport=BrokenTransport(),
    )
    with pytest.raises(ModelProviderError, match="transport_error"):
        failed.propose(())


def test_huggingface_path_is_lazy_strict_and_records_compute_metadata() -> None:
    prompt_seen = ""

    def generate(
        prompt: str,
        *,
        max_new_tokens: int,
        do_sample: bool,
    ) -> list[dict[str, object]]:
        nonlocal prompt_seen
        prompt_seen = prompt
        assert max_new_tokens == 32
        assert not do_sample
        return [{"generated_text": prompt + _proposal()}]

    model = HuggingFaceCausalModel(
        frozenset(),
        device="cpu",
        dtype="auto",
        max_new_tokens=32,
        generator=generate,
    )
    assert model.propose(()).proposals[0].id == "noop"
    assert "proposal-batch schema version 1" in prompt_seen
    assert model.metadata()["device"] == "cpu"
    assert model.metadata()["dtype"] == "auto"

    model.generator = lambda prompt, **kwargs: [{"generated_text": prompt + "not-json"}]
    with pytest.raises(ModelOutputError):
        model.propose(())


def test_huggingface_configuration_resource_and_dependency_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="configuration"):
        HuggingFaceCausalModel(frozenset(), max_new_tokens=0)
    artifact = Artifact("input", "x", Provenance.unknown())

    def resource_generator(
        prompt: str,
        *,
        max_new_tokens: int,
        do_sample: bool,
    ) -> list[dict[str, object]]:
        _ = max_new_tokens, do_sample
        return [{"generated_text": prompt + _proposal(resource=True)}]

    allowed = HuggingFaceCausalModel(
        frozenset({("filesystem", "document", "out.txt")}),
        generator=resource_generator,
    )
    assert allowed.propose((artifact,)).proposals[0].id == "write"
    blocked = HuggingFaceCausalModel(frozenset(), generator=resource_generator)
    with pytest.raises(ModelOutputError, match="unknown_resource"):
        blocked.propose((artifact,))
    monkeypatch.setitem(sys.modules, "transformers", None)
    with pytest.raises(RuntimeError, match="optional_dependency"):
        HuggingFaceCausalModel(frozenset()).propose(())


def test_malformed_model_output_is_explicit_failed_trace_evidence(
    monkeypatch: pytest.MonkeyPatch,
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
) -> None:
    monkeypatch.setenv("TEST_MODEL_KEY", "key")
    model = OpenAICompatibleModel(
        "https://model.example/v1/chat/completions",
        "test",
        frozenset(),
        api_key_env="TEST_MODEL_KEY",
        transport=Transport([Response(200, _body("not-json"))]),
    )
    report = MediatingITES(TransitionKernel(pipeline)).run(
        environment=environment,
        session=session,
        initial_inputs=environment.artifacts(),
        model=model,
    )
    types = [record["event_type"] for record in trace_records(report)]
    assert "model.parse_failed" in types
    assert types[-1] == "run.failed"
    assert RunResult.from_report(report).status.value == "failed"
