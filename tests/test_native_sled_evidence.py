"""Native SLED evidence is schema-linked and byte-regenerable."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conflux.experiments import (
    NATIVE_EVIDENCE_FILES,
    compare_native_sled_bundle,
    generate_native_sled_bundle,
    verify_native_sled_checksums,
)

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]


def test_native_bundle_is_deterministic_complete_and_linked(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_native_sled_bundle("a" * 40, first, repo_root=ROOT)
    generate_native_sled_bundle("a" * 40, second, repo_root=ROOT)
    assert compare_native_sled_bundle(first, second) == ()
    assert verify_native_sled_checksums(first) == ()
    assert {path.name for path in first.iterdir()} == set(NATIVE_EVIDENCE_FILES)

    protocol = json.loads((first / "protocol.json").read_text(encoding="utf-8"))
    result = json.loads((first / "result.json").read_text(encoding="utf-8"))
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert protocol["source_commit"] == "a" * 40
    assert protocol["model"] is None
    assert manifest["protocol_fingerprint"] == result["protocol_fingerprint"]
    assert manifest["complete"] is True
    assert len((first / "raw-events.jsonl").read_text().splitlines()) == 41


def test_native_bundle_detects_changed_and_missing_content(tmp_path: Path) -> None:
    retained = tmp_path / "retained"
    regenerated = tmp_path / "regenerated"
    generate_native_sled_bundle("b" * 40, retained, repo_root=ROOT)
    generate_native_sled_bundle("b" * 40, regenerated, repo_root=ROOT)
    (retained / "table.md").write_text("changed", encoding="utf-8")
    (retained / "raw-events.jsonl").unlink()
    assert compare_native_sled_bundle(retained, regenerated) == (
        "raw-events.jsonl",
        "table.md",
    )
    assert set(verify_native_sled_checksums(retained)) == {
        "raw-events.jsonl",
        "table.md",
    }
