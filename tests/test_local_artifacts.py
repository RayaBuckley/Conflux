"""Local artifact resolution is deterministic and never acquires weights."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conflux.adapters.models import (
    ResolvedLocalModel,
    load_resolved_local_model,
    resolve_transformers_snapshot,
    write_resolved_local_model,
)
from conflux.cli import main
from conflux.ports import LocalModelSpec

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
