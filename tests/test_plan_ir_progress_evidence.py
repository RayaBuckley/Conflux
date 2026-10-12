"""Contracts for the plan IR progress evidence bundle.

The liveness obligation the plan IR recorded before this bundle was satisfied by construction: the
abstraction assigned ``terminated`` itself. This generator measures the obligation that replaces it
for a plan with declared endpoints, and this file pins the population, the controls, the unchanged
no-endpoint shape, the validation of the endpoint declaration, and the write/check paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts import generate_backend_cross_validation as cross
from scripts import generate_delegation_defect_sweep as sweep
from scripts import generate_plan_ir_evidence as plan_ir
from scripts import generate_plan_ir_progress_evidence as progress
from scripts import generate_three_way_agreement as three_way

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def rows() -> list[dict[str, Any]]:
    """Measure the population once and share it across the contract tests."""
    return progress.rows_for()


@pytest.fixture(scope="module")
def evidence(rows: list[dict[str, Any]]) -> dict[str, object]:
    """Build the bundle from the shared measurement."""
    return progress.build(rows)


def test_safe_family_matches_the_sibling_generators() -> None:
    """Five generators must not disagree about which verdicts mean "no violation found"."""
    assert progress.SAFE_FAMILY == plan_ir.SAFE_FAMILY == cross.SAFE_FAMILY == sweep.SAFE_FAMILY == three_way.SAFE_FAMILY


def test_the_population_is_closed(rows: list[dict[str, Any]]) -> None:
    """Every reading appears once per route, at every bound, and nothing else appears."""
    assert [row["reading_id"] for row in rows] != []
    assert len(rows) == len(progress.reading_ids()) * len(progress.ROUTES)
    keys = {(row["reading_id"], row["route"]) for row in rows}
    assert len(keys) == len(rows)
    assert {row["reading_id"] for row in rows} == set(progress.reading_ids())
    assert {row["bound"] for row in rows} == set(progress.BOUNDS)


def test_expectations_are_pinned_and_met(rows: list[dict[str, Any]]) -> None:
    """Every reading states what it should show before measurement, and measurement agrees."""
    assert set(progress.EXPECTATIONS) == set(progress.reading_ids())
    assert progress.EXPECTATIONS["positive:goal-and-abort:b1"] == "clear"
    assert progress.EXPECTATIONS["control:weakened-progress:b1"] == "refuted"
    assert all(row["expectation_met"] for row in rows)
    assert {row["expectation"] for row in rows} == {"clear", "refuted"}


def test_declaring_endpoints_adds_the_progress_obligation_and_two_variables(rows: list[dict[str, Any]]) -> None:
    """The declared reading is the one that carries the new obligation; the controls keep it too."""
    positives = [row for row in rows if row["reading_id"] == "positive:goal-and-abort:b1"]
    helpers = [row for row in rows if row["reading_id"] == "default:no-endpoints:b1"]
    assert positives and helpers
    for row in positives:
        assert row["invariant_count"] == progress.BASELINE_INVARIANTS + 3
        assert row["variable_count"] == progress.BASELINE_VARIABLES + 2
        assert row["endpoint_declared"] is True
        assert {"bounded-progress", "safe-abort-clean", "goal-reached-clean"} <= set(row["invariants"])
    for row in helpers:
        assert row["invariant_count"] == progress.BASELINE_INVARIANTS
        assert row["variable_count"] == progress.BASELINE_VARIABLES
        assert row["endpoint_declared"] is False
        assert "bounded-progress" not in row["invariants"]


def test_every_reading_agrees_across_all_three_routes(rows: list[dict[str, Any]]) -> None:
    """The claim is class agreement per reading, with the encodings measured, not assumed."""
    grouped = progress._rows_by_reading(rows)
    assert len(grouped) == len(progress.reading_ids())
    assert all(len({row["verdict_class"] for row in group}) == 1 for group in grouped.values())
    assert all(row["measured"] and row["solver_hash"] for row in rows if row["route"] != "reference")
    assert all(row["auxiliary_invariant"] == progress.ROUTES[str(row["route"])] for row in rows)


def test_the_controls_are_refuted_and_the_positive_reading_is_not(rows: list[dict[str, Any]]) -> None:
    """A population nothing can refute would prove nothing: every control family is refuted."""
    refuted = {row["reading_id"] for row in rows if row["verdict_class"] == "unsafe"}
    assert refuted == {rid for rid in progress.reading_ids() if rid.startswith("control:")}
    positive = {row["reading_id"] for row in rows if row["reading_id"].startswith("positive:")}
    assert positive and not (positive & refuted)
    helpers = {row["reading_id"] for row in rows if row["reading_id"].startswith("default:")}
    assert helpers and not (helpers & refuted)
    assert {rid.split(":")[1] for rid in refuted} == set(progress.CONTROLS)


def test_the_no_endpoint_reading_keeps_the_recorded_shape(evidence: dict[str, object]) -> None:
    """Declaring nothing leaves the abstraction every earlier bundle recorded."""
    assert evidence["default_path_invariants"] == [progress.BASELINE_INVARIANTS]
    assert evidence["default_path_variables"] == [progress.BASELINE_VARIABLES]
    assert evidence["default_path_unchanged"] is True
    assert evidence["positive_control"] == len(progress.CONTROLS) * len(progress.BOUNDS)
    assert evidence["all_agree"] is True
    assert evidence["expectations_met"] == evidence["total_rows"]


def test_an_endpoint_declaration_is_validated() -> None:
    """A node declared twice, or a node the plan does not have, is refused rather than ignored."""
    from conflux.domain import Principal, Provenance
    from conflux.planning import OperationCatalogue
    from conflux.verification import abstract_plan

    grid = progress._grid()
    write, code = grid._operations()
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="test")
    plan = grid._build_plan("single", source, write, code)
    summaries = grid._summaries("single", plan, "authorised")
    common = {"catalogue": OperationCatalogue((write, code)), "effect_summaries": summaries, "bound": 2}
    with pytest.raises(ValueError, match="both a goal and an abort"):
        abstract_plan(plan, goal_nodes=("write",), abort_nodes=("write",), **common)
    with pytest.raises(ValueError, match="unknown plan endpoint node"):
        abstract_plan(plan, goal_nodes=("nope",), **common)


def test_generate_writes_a_bundle_and_documents_the_boundary(tmp_path: Path, rows: list[dict[str, Any]]) -> None:
    """The write path records the counts, the control and the boundary text."""
    assert progress.generate(tmp_path, rows=rows) == 0
    written = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert written["total_readings"] == len(progress.reading_ids())
    assert written["total_rows"] == len(rows)
    assert written["refuted_reading_ids"] == sorted(rid for rid in progress.reading_ids() if rid.startswith("control:"))
    summary = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    assert written["boundary"] in summary
    assert "not a claim" in summary
    assert "structured, not selected" in summary
    assert f"Expectations met: {len(rows)} of {len(rows)}" in summary
    assert "Rerun:" in summary


def test_generate_refuses_a_population_that_nothing_can_refute(tmp_path: Path) -> None:
    """An all-clear over a population with no refuted reading is refused, not reported as agreement."""

    def row(identifier: str, verdict: str) -> dict[str, Any]:
        return {
            "reading_id": identifier,
            "reading": "positive:goal-and-abort",
            "route": "reference",
            "bound": 1,
            "invariant_count": 10,
            "variable_count": 12,
            "expectation": "clear",
            "expectation_met": True,
            "verdict": verdict,
            "verdict_class": "safe" if verdict in progress.SAFE_FAMILY else "unsafe",
        }

    assert progress.generate(tmp_path, [row("positive:goal-and-abort:b1", "safe")]) == 1
    assert progress.generate(tmp_path, [row("control:unsafe-abort:b1", "unsafe")]) == 0


def test_check_reports_drift_and_matches_after_a_write(tmp_path: Path, rows: list[dict[str, Any]]) -> None:
    """The retained bundle is only trustworthy if --check can fail: pin both directions."""
    assert progress.check(tmp_path, rows) == 1  # nothing retained yet
    assert progress.generate(tmp_path, rows=rows) == 0
    assert progress.check(tmp_path, rows) == 0
    written = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    written["results"][0]["verdict"] = "unknown"
    (tmp_path / "evidence.json").write_text(json.dumps(written, indent=2, sort_keys=True), encoding="utf-8")
    assert progress.check(tmp_path, rows) == 1
