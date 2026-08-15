"""Self-hosted model port tests; no network or weights are used."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import pytest

from conflux.adapters.models import (
    LocalArtifactFile,
    LocalArtifactManifest,
    LocalModelFailure,
    LocalTextGeneration,
    SelfHostedOpenAIModel,
    TransformersLocalModel,
)
from conflux.adapters.models.openai_compatible import HTTPResponse
from conflux.experiments import LocalModelSpec
from conflux.ports import LocalModelRequest


def _spec(backend: str = "openai_compatible", endpoint: str | None = "http://127.0.0.1:8000/v1") -> LocalModelSpec:
    return LocalModelSpec(
        backend=backend,
        model_id="local/model",
        revision="revision",
        weight_manifest_sha256="a" * 64,
        tokenizer_id="local/model",
        tokenizer_revision="revision",
        prompt_template_version="1",
        seed=3,
        temperature=0.0,
        top_p=1.0,
        max_output_tokens=32,
        context_limit=1024,
        device="cpu",
        dtype="float32",
        runtime_version="test",
        endpoint=endpoint,
    )


def _request() -> LocalModelRequest:
    return LocalModelRequest(
        "request-1",
        "Return structured output.",
        "test",
        "answer_v1",
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["answer"],
            "properties": {"answer": {"type": "string"}},
        },
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
    response: Response
    calls: list[dict[str, object]] = field(default_factory=list)

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, object],
        timeout: float,
    ) -> HTTPResponse:
        self.calls.append({"url": url, "headers": headers, "body": json, "timeout": timeout})
        return self.response


def _body(*, model: str = "local/model", content: str = '{"answer":"ok"}') -> dict[str, object]:
    return {
        "model": model,
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 2},
    }


def test_openai_compatible_local_model_has_no_secret_and_checks_identity() -> None:
    transport = Transport(Response(200, _body()))
    model = SelfHostedOpenAIModel(_spec(), transport=transport, clock=lambda: 1.0)
    assert model.preflight().network_scope == "loopback"
    response = model.generate(_request())
    assert response.payload == {"answer": "ok"}
    assert response.prompt_tokens == 4
    assert transport.calls[0]["headers"] == {"Content-Type": "application/json"}
    assert transport.calls[0]["url"] == "http://127.0.0.1:8000/v1/chat/completions"

    mismatch = SelfHostedOpenAIModel(_spec(), transport=Transport(Response(200, _body(model="other"))))
    with pytest.raises(LocalModelFailure, match="identity:reported_model_mismatch"):
        mismatch.generate(_request())


def test_local_endpoint_scope_and_malformed_output_fail_closed() -> None:
    with pytest.raises(ValueError, match="explicit"):
        SelfHostedOpenAIModel(_spec(endpoint="https://gpu.internal/v1"))
    private = _spec(endpoint="http://10.0.0.4:8000/v1")
    object.__setattr__(private, "allow_private_remote", True)
    assert SelfHostedOpenAIModel(private, transport=Transport(Response(200, _body()))).preflight().network_scope == "private_remote"
    with pytest.raises(ValueError, match="public"):
        public = _spec(endpoint="https://8.8.8.8/v1")
        object.__setattr__(public, "allow_private_remote", True)
        SelfHostedOpenAIModel(public)
    malformed = SelfHostedOpenAIModel(_spec(), transport=Transport(Response(200, _body(content="not-json"))))
    with pytest.raises(LocalModelFailure, match="malformed_output"):
        malformed.generate(_request())


def test_transformers_adapter_is_local_deterministic_and_strict() -> None:
    seen: dict[str, object] = {}

    def generate(
        prompt: str,
        *,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        seed: int,
    ) -> LocalTextGeneration:
        seen.update(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
        )
        return LocalTextGeneration('{"answer":"local"}', 11, 4)

    model = TransformersLocalModel(_spec("transformers", None), generator=generate, clock=lambda: 2.0)
    assert model.preflight().network_scope == "none"
    response = model.generate(_request())
    assert response.payload == {"answer": "local"}
    assert (response.prompt_tokens, response.output_tokens) == (11, 4)
    assert model.records[0]["content"] == '{"answer":"local"}'
    assert seen["seed"] == 3
    assert seen["max_new_tokens"] == 32
    model.generator = lambda *args, **kwargs: '{"wrong":true}'
    with pytest.raises(LocalModelFailure, match="malformed_output"):
        model.generate(_request())


def test_transformers_adapter_strips_markdown_fences() -> None:
    def generate_fenced(
        prompt: str,
        *,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        seed: int,
    ) -> LocalTextGeneration:
        return LocalTextGeneration('```json\n{"answer":"fenced"}\n```', 11, 4)

    model = TransformersLocalModel(_spec("transformers", None), generator=generate_fenced, clock=lambda: 2.0)
    response = model.generate(_request())
    assert response.payload == {"answer": "fenced"}
    assert model.records[0]["content"] == '```json\n{"answer":"fenced"}\n```'


def test_transformers_adapter_strips_plain_fences() -> None:
    def generate_plain(
        prompt: str,
        *,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        seed: int,
    ) -> LocalTextGeneration:
        return LocalTextGeneration('```\n{"answer":"plain"}\n```', 11, 4)

    model = TransformersLocalModel(_spec("transformers", None), generator=generate_plain, clock=lambda: 2.0)
    response = model.generate(_request())
    assert response.payload == {"answer": "plain"}


def test_transformers_adapter_preserves_unfenced_json() -> None:
    def generate_unfenced(
        prompt: str,
        *,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        seed: int,
    ) -> LocalTextGeneration:
        return LocalTextGeneration('{"answer":"raw"}', 11, 4)

    model = TransformersLocalModel(_spec("transformers", None), generator=generate_unfenced, clock=lambda: 2.0)
    response = model.generate(_request())
    assert response.payload == {"answer": "raw"}


def test_transformers_dependency_is_optional_and_loading_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    model = TransformersLocalModel(_spec("transformers", None))
    monkeypatch.setattr("conflux.adapters.models.local_transformers.find_spec", lambda name: None)
    monkeypatch.setitem(sys.modules, "transformers", None)
    assert model.preflight().reason == "optional_dependency_unavailable:transformers"
    with pytest.raises(LocalModelFailure, match="dependency"):
        model.generate(_request())


def test_transformers_direct_loading_forbids_downloads_and_remote_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class Loader:
        @classmethod
        def from_pretrained(cls, model_id: str, **kwargs: object) -> object:
            calls.append((model_id, kwargs))
            return object()

    fake = ModuleType("transformers")
    fake.AutoModelForCausalLM = Loader  # type: ignore[attr-defined]
    fake.AutoTokenizer = Loader  # type: ignore[attr-defined]
    fake.set_seed = lambda seed: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "transformers", fake)

    manifest = LocalArtifactManifest(
        "local/model",
        "revision",
        "local/model",
        "revision",
        (
            LocalArtifactFile("config.json", 0, "a" * 64),
            LocalArtifactFile("model.safetensors", 0, "b" * 64),
            LocalArtifactFile("tokenizer.json", 0, "c" * 64),
        ),
        0,
    )
    monkeypatch.setattr(
        "conflux.adapters.models.local_transformers.verify_transformers_snapshot",
        lambda path, value: (),
    )
    model = TransformersLocalModel(
        _spec("transformers", None),
        snapshot_path=Path("snapshot"),
        artifact_manifest=manifest,
    )
    model._load_generator()
    assert len(calls) == 2
    assert all(call[1]["local_files_only"] is True for call in calls)
    assert all(call[1]["trust_remote_code"] is False for call in calls)
