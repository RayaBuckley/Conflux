"""Local artifact resolution is deterministic and never acquires weights."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import conflux.cli as cli_module
from conflux.adapters.models import (
    ResolvedLocalModel,
    load_resolved_local_model,
    resolve_transformers_snapshot,
    write_resolved_local_model,
)
from conflux.cli import main
from conflux.experiments import ExperimentProtocol
from conflux.ports import LocalModelPreflight, LocalModelSpec

MODEL_ID = "HuggingFaceTB/SmolLM2-360M-Instruct"
REVISION = "c38281e01d0c0b0c36eac2f5bcb5b51fa2e803fc"


def _snapshot(root: Path) -> Path:
    snapshot = root / "model" / "snapshots" / REVISION
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text("{}", encoding="utf-8")
    (snapshot / "tokenizer.json").write_text("{}", encoding="utf-8")
    (snapshot / "model.safetensors").write_bytes(b"weights")
    return snapshot


def _spec(digest: str) -> LocalModelSpec:
    return LocalModelSpec(
        "transformers",
        MODEL_ID,
        REVISION,
        digest,
        MODEL_ID,
        REVISION,
        "planning-diagnostic-v1",
        0,
        0.0,
        1.0,
        256,
        4096,
        "cpu",
        "float32",
        "transformers-test",
    )


def test_resolution_is_stable_round_trippable_and_reports_incomplete_cache(
    tmp_path: Path,
) -> None:
    snapshot = _snapshot(tmp_path)
    incomplete = snapshot.parent.parent / "blobs" / "partial.incomplete"
    incomplete.parent.mkdir()
    incomplete.write_bytes(b"partial")
    first, warnings = resolve_transformers_snapshot(
        snapshot,
        model_id=MODEL_ID,
        revision=REVISION,
    )
    second, _ = resolve_transformers_snapshot(
        snapshot,
        model_id=MODEL_ID,
        revision=REVISION,
    )
    assert first.fingerprint == second.fingerprint
    assert first.total_size == len(b"{}{}weights")
    assert warnings == ("unreferenced_incomplete_cache_entries:1",)
    path = tmp_path / "resolved.json"
    write_resolved_local_model(
        ResolvedLocalModel(_spec(first.fingerprint), snapshot, first, warnings),
        path,
    )
    assert load_resolved_local_model(path).manifest == first


@pytest.mark.parametrize(
    ("removed", "reason"),
    (
        ("config.json", "config_missing"),
        ("tokenizer.json", "tokenizer_missing"),
        ("model.safetensors", "weights_missing"),
    ),
)
def test_resolution_requires_complete_identity(
    tmp_path: Path,
    removed: str,
    reason: str,
) -> None:
    snapshot = _snapshot(tmp_path)
    (snapshot / removed).unlink()
    with pytest.raises(ValueError, match=reason):
        resolve_transformers_snapshot(
            snapshot,
            model_id=MODEL_ID,
            revision=REVISION,
        )


def test_resolution_rejects_revision_mismatch_and_cache_escape(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="revision_mismatch"):
        resolve_transformers_snapshot(snapshot, model_id=MODEL_ID, revision="wrong")
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    link = snapshot / "escaped.json"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("symbolic links unavailable on this Windows installation")
    with pytest.raises(ValueError, match="cache_escape"):
        resolve_transformers_snapshot(snapshot, model_id=MODEL_ID, revision=REVISION)


def test_resolution_rejects_changed_and_dangling_files(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    manifest, _ = resolve_transformers_snapshot(
        snapshot,
        model_id=MODEL_ID,
        revision=REVISION,
    )
    resolved = ResolvedLocalModel(_spec(manifest.fingerprint), snapshot, manifest)
    path = tmp_path / "resolved.json"
    write_resolved_local_model(resolved, path)
    (snapshot / "config.json").write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="manifest_changed"):
        load_resolved_local_model(path)


def test_model_resolve_cli_writes_reviewable_configuration(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    output = tmp_path / "resolved"
    assert main(
        [
            "model",
            "resolve",
            "transformers",
            "--model-id",
            MODEL_ID,
            "--revision",
            REVISION,
            "--snapshot",
            str(snapshot),
            "--runtime-version",
            "transformers-test",
            "--output",
            str(output),
        ]
    ) == 0
    assert (output / "artifact-manifest.json").is_file()
    resolved = load_resolved_local_model(output / "transformers.json")
    assert resolved.spec.device == "cpu"
    assert resolved.spec.temperature == 0


def test_agentdojo_preflight_builds_six_cell_protocol_from_resolved_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _snapshot(tmp_path)
    manifest, _ = resolve_transformers_snapshot(
        snapshot,
        model_id=MODEL_ID,
        revision=REVISION,
    )
    configuration = tmp_path / "transformers.json"
    write_resolved_local_model(
        ResolvedLocalModel(_spec(manifest.fingerprint), snapshot, manifest),
        configuration,
    )
    monkeypatch.setattr(
        cli_module,
        "load_pinned_suite",
        lambda _: SimpleNamespace(to_dict=lambda: {"schema_version": "fixture"}),
    )
    output = tmp_path / "agentdojo"
    assert main(
        [
            "benchmark",
            "agentdojo",
            "preflight",
            "--model-config",
            str(configuration),
            "--source-commit",
            "a" * 40,
            "--output",
            str(output),
        ]
    ) == 0
    protocol = json.loads((output / "protocol.json").read_text())
    preflight = json.loads((output / "preflight.json").read_text())
    assert protocol["schema_version"] == "2"
    assert protocol["seeds"] == [0]
    assert len(preflight["matrix"]) == 6
    assert preflight["annotation_profiles"] == ["conservative", "oracle"]


def test_cpu_pilot_preflights_eight_cells_and_retains_fake_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _snapshot(tmp_path)
    manifest, _ = resolve_transformers_snapshot(
        snapshot,
        model_id=MODEL_ID,
        revision=REVISION,
    )
    configuration = tmp_path / "transformers.json"
    write_resolved_local_model(
        ResolvedLocalModel(_spec(manifest.fingerprint), snapshot, manifest),
        configuration,
    )
    output = tmp_path / "pilot"

    class AvailableModel:
        records = [{"request_id": "fake", "content": "{}", "raw_sha256": "a" * 64}]

        def __init__(self, *args: object, **kwargs: object) -> None:
            _ = args, kwargs

        def preflight(self) -> LocalModelPreflight:
            return LocalModelPreflight(
                "transformers",
                MODEL_ID,
                True,
                "none",
                None,
                True,
                True,
                True,
                True,
            )

    def comparison(
        protocol: ExperimentProtocol,
        model: object,
        scenarios: object,
    ) -> dict[str, object]:
        _ = model, scenarios
        observations = []
        for task in ("direct-authorised-effect", "blocked-action-recovery"):
            for mode in ("reactive", "static", "dynamic", "dynamic_code"):
                observations.append(
                    {
                        "case_id": f"{task}:{mode}:r0:s0",
                        "task_id": task,
                        "mode": mode,
                        "repetition": 0,
                        "seed": 0,
                        "status": "complete",
                        "utility_completed": True,
                        "security_violations": 0,
                        "legitimate_blocks": 0,
                        "sensitive_reads": 0,
                        "max_context_size": 1,
                        "cumulative_authority_footprint": 1,
                        "model_calls": 1,
                        "prompt_tokens": 10,
                        "output_tokens": 2,
                        "latency_ms": 3,
                        "replans": 0,
                        "plan_nodes": 1,
                        "modeled_effects": 1,
                        "bound_reached": False,
                        "parse_failures": 0,
                        "modeled_program_failures": 0,
                    }
                )
        return {
            "schema_version": "2",
            "protocol_fingerprint": protocol.fingerprint,
            "complete": True,
            "model_id": MODEL_ID,
            "task_ids": ["blocked-action-recovery", "direct-authorised-effect"],
            "observations": observations,
        }

    monkeypatch.setattr(cli_module, "TransformersLocalModel", AvailableModel)
    monkeypatch.setattr(cli_module, "run_planning_comparison", comparison)
    arguments = [
        "plan",
        "pilot",
        "--model-config",
        str(configuration),
        "--source-commit",
        "a" * 40,
        "--output",
        str(output),
    ]
    assert main(arguments) == 0
    assert len(json.loads((output / "preflight.json").read_text())["matrix"]) == 8
    assert main([*arguments, "--execute-local"]) == 0
    assert len((output / "raw-model.jsonl").read_text().splitlines()) == 1
    assert (output / "manifest.json").is_file()
    assert (output / "CHECKSUMS.sha256").is_file()
