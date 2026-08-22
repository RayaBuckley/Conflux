from __future__ import annotations

import json
from pathlib import Path

import pytest

from conflux.domain import canonical_json
from conflux.experiments import (
    ExperimentManifest,
    completion_marker,
    expand_cases,
    materialise_jobs,
    plan_resume,
)


def _manifest(*, model: dict[str, object] | None = None) -> ExperimentManifest:
    return ExperimentManifest(
        id="resume-test",
        suite="canonical",
        suite_version="1",
        source_commit="abcdef1",
        defence="ites",
        bounds={"cases": ["case-b", "case-a"]},
        model=model or {"adapter": "scripted"},
        provider={"adapter": "in-memory"},
        policy={"adapter": "in-memory"},
        seed=41,
        machine={"execution": "offline"},
        output_directory="output/runs/resume",
        rerun_command=("python", "scripts/cluster_jobs.py"),
    )


def test_case_expansion_has_stable_order_indices_and_seeds() -> None:
    cases = expand_cases(_manifest())
    assert [(case.index, case.case_id, case.seed) for case in cases] == [
        (0, "case-b", 41),
        (1, "case-a", 42),
    ]


def test_materialisation_skips_only_checksum_valid_completion(tmp_path: Path) -> None:
    manifest = _manifest()
    first = materialise_jobs(manifest, tmp_path)
    case = first.pending[0]
    directory = tmp_path / case.case_id
    directory.mkdir()
    marker = completion_marker(case, "a" * 64)
    (directory / "complete.json").write_text(canonical_json(marker), encoding="utf-8")
    resumed = materialise_jobs(manifest, tmp_path)
    assert [item.case_id for item in resumed.completed] == ["case-b"]
    assert [item.case_id for item in resumed.pending] == ["case-a"]
    assert json.loads((tmp_path / "resume-plan.json").read_text())["completed"][0]["seed"] == 41


def test_stale_or_corrupt_marker_is_rerun(tmp_path: Path) -> None:
    manifest = _manifest()
    case = expand_cases(manifest)[0]
    directory = tmp_path / case.case_id
    directory.mkdir(parents=True)
    (directory / "complete.json").write_text('{"status":"complete"}', encoding="utf-8")
    plan = plan_resume(manifest, tmp_path)
    assert case in plan.pending
    assert plan.rejected_markers == (case.case_id,)


def test_manifest_secrets_are_rejected() -> None:
    with pytest.raises(ValueError, match="secret material"):
        expand_cases(_manifest(model={"api_key": "actual-secret"}))


def test_duplicate_cases_and_bad_checksums_are_rejected() -> None:
    manifest = _manifest()
    object.__setattr__(manifest, "bounds", {"cases": ["same", "same"]})
    with pytest.raises(ValueError, match="unique"):
        expand_cases(manifest)
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        completion_marker(expand_cases(_manifest())[0], "bad")
