"""The retained smoke bundle producer is deterministic and schema-valid."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from conflux.adapters.scenarios import load_schema
from conflux.experiments import ExperimentManifest, generate_smoke_bundle

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]


def _manifest(output: Path) -> ExperimentManifest:
    return ExperimentManifest(
        id="m3-smoke",
        suite="canonical-v1",
        suite_version="1",
        source_commit="b" * 40,
        defence="ites",
        bounds={"max_model_calls": 3},
        model={"adapter": "scripted", "cases": ["authorised", "blocked"]},
        provider={"adapter": "in-memory", "version": "1"},
        policy={"adapter": "in-memory", "version": "1"},
        seed=0,
        machine={"class": "test"},
        output_directory=str(output),
        rerun_command=("python", "scripts/generate_smoke_evidence.py"),
    )


def test_smoke_bundle_is_deterministic_linked_and_schema_valid(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_smoke_bundle(_manifest(first), first, repo_root=ROOT)
    generate_smoke_bundle(_manifest(first), second, repo_root=ROOT)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {path.name: path.read_bytes() for path in second.iterdir()}

    result = json.loads((first / "result.json").read_text(encoding="utf-8"))
    Draft202012Validator(load_schema("result.schema.json")).validate(result)
    assert result["security"] == {
        "attack_blocked": True,
        "authorised_task_executed": True,
        "negative_control_counterexample": True,
    }
    raw = (first / "raw.jsonl").read_bytes()
    assert result["trace"]["sha256"] == hashlib.sha256(raw).hexdigest()
    trace_validator = Draft202012Validator(load_schema("trace-event-v3.schema.json"))
    for line in raw.decode("utf-8").splitlines():
        trace_validator.validate(json.loads(line))

    for line in (first / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == expected
