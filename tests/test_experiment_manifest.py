"""Strict manifest loading, hashing, and materialisation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conflux.adapters.scenarios import load_scenario
from conflux.cli import EXIT_OK, main
from conflux.domain import fingerprint
from conflux.experiments import ExperimentManifest, load_manifest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]


def _manifest(output: Path) -> ExperimentManifest:
    return ExperimentManifest(
        id="smoke",
        suite="examples/basic.yaml",
        suite_version="1",
        source_commit="a" * 40,
        defence="ites",
        bounds={"max_model_calls": 3},
        model={"adapter": "scripted", "version": "1"},
        provider={"adapter": "memory", "version": "1"},
        policy={"adapter": "in-memory", "version": "1"},
        seed=0,
        machine={"class": "test"},
        output_directory=str(output),
        rerun_command=(
            "conflux",
            "demo",
            "--scenario",
            "examples/basic.yaml",
        ),
    )


def test_manifest_is_immutable_stable_and_materialised(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path / "run")
    assert manifest.fingerprint == fingerprint(manifest.to_dict())
    path = manifest.materialise(tmp_path / "run")
    assert load_manifest(path) == manifest
    assert (tmp_path / "run" / "RERUN.txt").read_text(encoding="utf-8").endswith("\n")
    with pytest.raises(TypeError):
        manifest.bounds["max_model_calls"] = 9  # type: ignore[index]


def test_manifest_unknown_fields_and_versions_fail_closed(tmp_path: Path) -> None:
    payload = _manifest(tmp_path).to_dict()
    payload["unknown"] = True
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest_schema_error"):
        load_manifest(path)
    payload.pop("unknown")
    payload["schema_version"] = "2"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest_schema_error"):
        load_manifest(path)


def test_demo_copies_manifest_and_links_hash(tmp_path: Path) -> None:
    output = tmp_path / "run"
    manifest = _manifest(output)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
    assert (
        main(
            [
                "demo",
                "--scenario",
                str(ROOT / "examples" / "basic.yaml"),
                "--manifest",
                str(manifest_path),
            ]
        )
        == EXIT_OK
    )
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert result["manifest_hash"] == manifest.fingerprint
    assert load_manifest(output / "manifest.json") == manifest


def test_all_versioned_suite_scenarios_load_with_stable_distinct_ids() -> None:
    suites = ROOT / "experiments" / "suites"
    scenarios = tuple(load_scenario(path) for path in sorted(suites.glob("*/*.yaml")))
    identifiers = {scenario.id for scenario in scenarios}
    assert len(scenarios) == 6
    assert len(identifiers) == 6
    assert all(identifier.startswith(("legacy-env-", "canonical-env-")) for identifier in identifiers)
