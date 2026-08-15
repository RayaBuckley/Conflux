"""COI reduction evidence is schema-linked and byte-regenerable."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator

from conflux.experiments import (
    compare_coi_evidence_bundle,
    generate_coi_evidence_bundle,
    verify_coi_evidence_checksums,
)

ROOT = Path(__file__).resolve().parents[1]


def test_coi_bundle_is_deterministic_complete_and_reduced(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_coi_evidence_bundle("a" * 40, first, repo_root=ROOT)
    generate_coi_evidence_bundle("a" * 40, second, repo_root=ROOT)
    assert compare_coi_evidence_bundle(first, second) == ()
    assert verify_coi_evidence_checksums(first) == ()

    result = cast(
        dict[str, object],
        json.loads((first / "result.json").read_text(encoding="utf-8")),
    )
    schema = cast(
        dict[str, object],
        json.loads(
            (ROOT / "schemas/verification-reduction-result.schema.json").read_text(
                encoding="utf-8"
            )
        ),
    )
    Draft202012Validator(schema).validate(result)
    summary = cast(dict[str, object], result["summary"])
    assert result["complete"] is True
    assert summary["fixtures"] == summary["reference_verdict_agreements"]
    assert cast(int, summary["fixtures_with_measurable_reduction"]) >= 1


def test_coi_bundle_detects_changed_and_missing_content(tmp_path: Path) -> None:
    retained = tmp_path / "retained"
    regenerated = tmp_path / "regenerated"
    generate_coi_evidence_bundle("b" * 40, retained, repo_root=ROOT)
    generate_coi_evidence_bundle("b" * 40, regenerated, repo_root=ROOT)
    (retained / "table.md").write_text("changed", encoding="utf-8")
    (retained / "models/reduced/safe-noise.json").unlink()
    changed = compare_coi_evidence_bundle(retained, regenerated)
    assert changed == ("models/reduced/safe-noise.json", "table.md")
    checksum_errors = verify_coi_evidence_checksums(retained)
    assert set(checksum_errors) == {"models/reduced/safe-noise.json", "table.md"}
