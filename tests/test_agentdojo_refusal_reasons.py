"""Tests for the refusal-reasons evidence derived from the retained bundles."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conflux.experiments import (
    AGENTDOJO_REFUSAL_REASONS_FILES,
    compare_agentdojo_refusal_reasons_bundle,
    derive_refusal_reason_rows,
    generate_agentdojo_refusal_reasons_bundle,
    refusal_reason_checks,
    refusal_reason_payload,
    refusal_reason_totals,
    verify_agentdojo_refusal_reasons_checksums,
)

SHIPPED_BUNDLE = Path("research/output/runs/agentdojo-refusal-reasons-v1")
RUNS_ROOT = Path("research/output/runs")


def _record(outcome: str, *, reason: str | None = None, tool: str = "search_emails") -> dict[str, object]:
    return {
        "outcome": outcome,
        "reason": reason,
        "tool": tool,
        "arguments_sha256": "0" * 64,
        "annotations_sha256": "1" * 64,
    }


def _report_with_a_denying_decision(
    *,
    policy_id: str = "snapshot-read-policy",
    category: str = "read",
    reason: str = "read_denied",
) -> dict[str, object]:
    return {
        "branches": [
            {
                "trace": [
                    {
                        "decision": {
                            "allowed": False,
                            "decisions": [
                                {
                                    "allowed": True,
                                    "policy_id": "in-memory-authorisation",
                                    "category": "authorisation",
                                    "reason": "all_principals_authorised",
                                },
                                {"allowed": False, "policy_id": policy_id, "category": category, "reason": reason},
                            ],
                        },
                    },
                ],
            },
        ],
    }


def _write_bundle(runs_root: Path, name: str, cells: list[dict[str, object]]) -> Path:
    directory = runs_root / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "result.json").write_text(json.dumps({"cells": cells}), encoding="utf-8")
    return directory


def _cell(records: list[dict[str, object]], *, case_id: str = "user_task_0") -> dict[str, object]:
    return {"case_id": case_id, "defence": "ites_conservative", "augmentation": records}


def test_a_blocked_record_without_a_reason_is_derived_from_its_report(tmp_path: Path) -> None:
    blocked = _record("blocked", tool="delete_file")
    blocked["report"] = _report_with_a_denying_decision(
        policy_id="in-memory-argument-policy",
        category="authorisation",
        reason="argument_denied",
    )
    _write_bundle(tmp_path, "agentdojo-a-v1", [_cell([_record("executed"), blocked])])
    payload = refusal_reason_payload("deadbeef", tmp_path)
    assert payload["totals"]["records_listed"] == 1
    assert payload["totals"]["records_derived"] == 1
    assert payload["totals"]["by_policy_id"] == {"in-memory-argument-policy": 1}
    assert payload["totals"]["by_policy_dimension"] == {"authorisation": 1}
    assert payload["totals"]["by_tool"] == {"delete_file": 1}
    row = payload["records"][0]
    assert row["bundle"] == "agentdojo-a-v1"
    assert (row["cell"], row["record"]) == (0, 1)
    assert row["reason"] is None
    assert row["derived_policy_id"] == "in-memory-argument-policy"
    assert row["derived_policy_dimension"] == "authorisation"
    assert row["derived_reason"] == "argument_denied"
    assert all(payload["checks"].values())


def test_a_blocked_record_whose_report_names_no_denial_is_counted_underivable(tmp_path: Path) -> None:
    blocked = _record("blocked")
    blocked["report"] = {"branches": [{"trace": [{"decision": {"allowed": True, "decisions": []}}]}]}
    _write_bundle(tmp_path, "agentdojo-a-v1", [_cell([blocked])])
    payload = refusal_reason_payload("deadbeef", tmp_path)
    assert payload["totals"]["records_listed"] == 1
    assert payload["totals"]["records_derived"] == 0
    assert payload["totals"]["records_underivable"] == 1
    row = payload["records"][0]
    assert (row["derived_reason"], row["derived_policy_id"], row["derived_policy_dimension"]) == (None, None, None)
    assert all(payload["checks"].values())


def test_a_blocked_record_without_a_report_is_counted_underivable(tmp_path: Path) -> None:
    _write_bundle(tmp_path, "agentdojo-a-v1", [_cell([_record("blocked")])])
    payload = refusal_reason_payload("deadbeef", tmp_path)
    assert payload["totals"]["records_underivable"] == 1
    assert payload["checks"]["each_row_is_either_fully_derived_or_not_derived_at_all"] is True


def test_a_blocked_record_that_already_names_a_reason_is_not_listed(tmp_path: Path) -> None:
    named = _record("blocked", reason="read_denied")
    named["report"] = _report_with_a_denying_decision()
    _write_bundle(tmp_path, "agentdojo-a-v1", [_cell([named])])
    payload = refusal_reason_payload("deadbeef", tmp_path)
    assert payload["records"] == []
    assert payload["bundles"][0]["blocked"] == 1
    assert payload["bundles"][0]["blocked_named"] == 1
    assert payload["bundles"][0]["blocked_unnamed"] == 0
    assert all(payload["checks"].values())


def test_the_first_denial_in_the_first_branch_wins(tmp_path: Path) -> None:
    blocked = _record("blocked")
    blocked["report"] = {
        "branches": [
            {
                "trace": [
                    {"decision": {"allowed": True, "decisions": [{"allowed": True, "policy_id": "p", "category": "read", "reason": "ok"}]}},
                ],
            },
            {
                "trace": [
                    {
                        "decision": {
                            "allowed": False,
                            "decisions": [{"allowed": False, "policy_id": "second", "category": "read", "reason": "later"}],
                        },
                    },
                ],
            },
            {
                "trace": [
                    {
                        "decision": {
                            "allowed": False,
                            "decisions": [{"allowed": False, "policy_id": "third", "category": "read", "reason": "last"}],
                        },
                    },
                ],
            },
        ],
    }
    _write_bundle(tmp_path, "agentdojo-a-v1", [_cell([blocked])])
    payload = refusal_reason_payload("deadbeef", tmp_path)
    assert payload["records"][0]["derived_policy_id"] == "second"


def test_rows_follow_bundle_name_then_cell_then_record(tmp_path: Path) -> None:
    first = _record("blocked")
    first["report"] = _report_with_a_denying_decision()
    second = _record("blocked")
    second["report"] = _report_with_a_denying_decision(
        policy_id="in-memory-authorisation",
        category="authorisation",
        reason="principal_denied",
    )
    _write_bundle(tmp_path, "agentdojo-b-v1", [_cell([first])])
    _write_bundle(tmp_path, "agentdojo-a-v1", [_cell([first]), _cell([second])])
    rows, bundles = derive_refusal_reason_rows(tmp_path)
    assert [bundle["bundle"] for bundle in bundles] == ["agentdojo-a-v1", "agentdojo-b-v1"]
    assert [(row["bundle"], row["cell"], row["record"]) for row in rows] == [
        ("agentdojo-a-v1", 0, 0),
        ("agentdojo-a-v1", 1, 0),
        ("agentdojo-b-v1", 0, 0),
    ]
    assert all(refusal_reason_checks(rows, bundles, refusal_reason_totals(rows, bundles)).values())


def test_a_bundle_without_a_result_file_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "agentdojo-empty-v1").mkdir()
    _write_bundle(tmp_path, "agentdojo-a-v1", [_cell([])])
    payload = refusal_reason_payload("deadbeef", tmp_path)
    assert payload["totals"]["bundles_read"] == 1


def test_the_bundle_writes_three_files_and_rebuilds_to_the_same_bytes(tmp_path: Path) -> None:
    blocked = _record("blocked")
    blocked["report"] = _report_with_a_denying_decision()
    runs_root = tmp_path / "runs"
    _write_bundle(runs_root, "agentdojo-a-v1", [_cell([blocked])])
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_agentdojo_refusal_reasons_bundle("deadbeef", first, runs_root)
    generate_agentdojo_refusal_reasons_bundle("deadbeef", second, runs_root)
    assert {path.name for path in first.iterdir()} == set(AGENTDOJO_REFUSAL_REASONS_FILES)
    assert compare_agentdojo_refusal_reasons_bundle(first, second) == ()
    assert verify_agentdojo_refusal_reasons_checksums(first) == ()


def test_checksum_verification_reports_a_changed_missing_or_extra_file(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    _write_bundle(runs_root, "agentdojo-a-v1", [_cell([])])
    bundle = tmp_path / "bundle"
    generate_agentdojo_refusal_reasons_bundle("deadbeef", bundle, runs_root)
    (bundle / "README.md").write_text("changed\n", encoding="utf-8")
    assert verify_agentdojo_refusal_reasons_checksums(bundle) == ("README.md",)
    (bundle / "extra.md").write_text("extra\n", encoding="utf-8")
    assert verify_agentdojo_refusal_reasons_checksums(bundle) == ("README.md", "extra.md")
    (bundle / "CHECKSUMS.sha256").unlink()
    assert verify_agentdojo_refusal_reasons_checksums(bundle) == ("CHECKSUMS.sha256",)


def test_the_comparison_reports_a_changed_file(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    _write_bundle(runs_root, "agentdojo-a-v1", [_cell([])])
    expected = tmp_path / "expected"
    regenerated = tmp_path / "regenerated"
    generate_agentdojo_refusal_reasons_bundle("deadbeef", expected, runs_root)
    generate_agentdojo_refusal_reasons_bundle("deadbeef", regenerated, runs_root)
    (regenerated / "refusal-reasons.json").write_text("{}\n", encoding="utf-8")
    assert compare_agentdojo_refusal_reasons_bundle(expected, regenerated) == ("refusal-reasons.json",)


def test_the_readme_states_the_counts_the_payload_holds(tmp_path: Path) -> None:
    blocked = _record("blocked")
    blocked["report"] = _report_with_a_denying_decision()
    runs_root = tmp_path / "runs"
    _write_bundle(runs_root, "agentdojo-a-v1", [_cell([blocked])])
    bundle = tmp_path / "bundle"
    generate_agentdojo_refusal_reasons_bundle("deadbeef", bundle, runs_root)
    readme = (bundle / "README.md").read_text(encoding="utf-8")
    assert "| bundles read | 1 |" in readme
    assert "| blocked records with no reason, listed below | 1 |" in readme
    assert "| `snapshot-read-policy` | read | `read_denied` | 1 |" in readme
    assert "| **total** | | | **1** |" in readme


@pytest.mark.skipif(not SHIPPED_BUNDLE.is_dir(), reason="the retained refusal-reasons bundle is not present")
def test_the_shipped_bundle_matches_a_fresh_derivation(tmp_path: Path) -> None:
    shipped = json.loads((SHIPPED_BUNDLE / "refusal-reasons.json").read_text(encoding="utf-8"))
    regenerate = tmp_path / "regenerated"
    generate_agentdojo_refusal_reasons_bundle(str(shipped["source_commit"]), regenerate, RUNS_ROOT)
    fresh = json.loads((regenerate / "refusal-reasons.json").read_text(encoding="utf-8"))
    assert [row["bundle"] for row in fresh["records"]] == [row["bundle"] for row in shipped["records"]]
    assert [(row["cell"], row["record"]) for row in fresh["records"]] == [(row["cell"], row["record"]) for row in shipped["records"]]
    assert fresh["totals"] == shipped["totals"]
    assert fresh["bundles"] == shipped["bundles"]
    assert all(shipped["checks"].values())


@pytest.mark.skipif(not SHIPPED_BUNDLE.is_dir(), reason="the retained refusal-reasons bundle is not present")
def test_the_shipped_bundle_keeps_its_file_set_and_checksums() -> None:
    assert {path.name for path in SHIPPED_BUNDLE.iterdir()} == set(AGENTDOJO_REFUSAL_REASONS_FILES)
    assert verify_agentdojo_refusal_reasons_checksums(SHIPPED_BUNDLE) == ()


def test_the_recorded_paths_do_not_depend_on_how_the_runs_root_is_given(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    blocked = _record("blocked")
    blocked["report"] = _report_with_a_denying_decision()
    _write_bundle(tmp_path / "runs", "agentdojo-a-v1", [_cell([blocked])])
    monkeypatch.chdir(tmp_path)
    relative = refusal_reason_payload("deadbeef", Path("runs"))
    absolute = refusal_reason_payload("deadbeef", tmp_path / "runs")
    assert relative == absolute
    assert relative["bundles"][0]["result_json"] == "agentdojo-a-v1/result.json"
    assert relative["records"][0]["result_json"] == "agentdojo-a-v1/result.json"


def test_a_runs_root_inside_the_repository_is_recorded_relative_to_it() -> None:
    assert refusal_reason_payload("deadbeef", RUNS_ROOT)["runs_root"] == "research/output/runs"
    assert refusal_reason_payload("deadbeef", RUNS_ROOT.resolve())["runs_root"] == "research/output/runs"
