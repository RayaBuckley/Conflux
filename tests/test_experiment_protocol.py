"""Version-two protocol and resolved-manifest contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conflux.experiments import (
    ExperimentProtocol,
    LocalModelSpec,
    ResolvedRunManifest,
    RunFailure,
    load_protocol,
)


def _model() -> LocalModelSpec:
    return LocalModelSpec(
        backend="openai_compatible",
        model_id="local/test",
        revision="revision-1",
        weight_manifest_sha256="a" * 64,
        tokenizer_id="local/test",
        tokenizer_revision="revision-1",
        prompt_template_version="1",
        seed=7,
        temperature=0.0,
        top_p=1.0,
        max_output_tokens=128,
        context_limit=2048,
        device="cpu",
        dtype="float32",
        runtime_version="test-1",
        endpoint="http://127.0.0.1:8080/v1",
    )


def _protocol(model: LocalModelSpec | None = None) -> ExperimentProtocol:
    return ExperimentProtocol(
        id="native-reproduction",
        track="native_sled",
        suite={"id": "paired", "version": "1"},
        source_commit="a" * 40,
        inputs={"fixture.yaml": "b" * 64},
        model=model,
        prompts={},
        seeds=(0,),
        repetitions=1,
        bounds={"max_states": 100, "max_transitions": 200},
        environment={"python": "3.12", "platform": "test"},
        output_directory="runs/native",
        rerun_command=("conflux", "sled", "reproduce", "--protocol", "protocol.json"),
    )


def test_protocol_round_trip_is_immutable_and_deterministic(tmp_path: Path) -> None:
    protocol = _protocol(_model())
    first = protocol.materialise(tmp_path / "one")
    second = protocol.materialise(tmp_path / "two")
    assert first.read_bytes() == second.read_bytes()
    assert load_protocol(first) == protocol
    assert len(protocol.fingerprint) == 64
    with pytest.raises(TypeError):
        protocol.bounds["max_states"] = 1  # type: ignore[index]


def test_protocol_rejects_unknown_version_field_and_missing_identity(tmp_path: Path) -> None:
    payload = _protocol(_model()).to_dict()
    path = tmp_path / "protocol.json"
    for key, value in (("schema_version", "3"), ("unexpected", True)):
        changed = dict(payload)
        changed[key] = value
        path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match="protocol_schema_error"):
            load_protocol(path)
    changed = dict(payload)
    changed_model = dict(_model().to_dict())
    changed_model.pop("weight_manifest_sha256")
    changed["model"] = changed_model
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="protocol_schema_error"):
        load_protocol(path)


def test_v1_manifest_reader_remains_available(tmp_path: Path) -> None:
    from conflux.experiments import ExperimentManifest, load_manifest

    old = ExperimentManifest(
        id="old",
        suite="suite",
        suite_version="1",
        source_commit="a" * 40,
        defence="ites",
        bounds={},
        model={},
        provider={},
        policy={},
        seed=0,
        machine={},
        output_directory="runs/old",
        rerun_command=("conflux", "demo"),
    )
    path = old.materialise(tmp_path)
    assert load_manifest(path) == old


def test_resolved_manifest_enforces_completeness_and_failure_taxonomy() -> None:
    manifest = ResolvedRunManifest(
        run_id="run-1",
        track="planning",
        protocol_fingerprint="a" * 64,
        source_commit="b" * 40,
        status="incomplete",
        complete=False,
        exclusions=("model evidence deferred",),
        failures=(RunFailure("model", "weights unavailable", "case-1"),),
        environment={"python": "3.12"},
        checksums={"result.json": "c" * 64},
    )
    assert manifest.to_dict()["failures"] == [
        {"category": "model", "detail": "weights unavailable", "case_id": "case-1"}
    ]
    with pytest.raises(ValueError, match="completeness_mismatch"):
        ResolvedRunManifest(
            run_id="bad",
            track="planning",
            protocol_fingerprint="a" * 64,
            source_commit="b" * 40,
            status="complete",
            complete=False,
            exclusions=(),
            failures=(),
            environment={},
            checksums={},
        )
