"""Contracts for the plan IR evidence bundle.

The plan IR has its own encoding in the bounded model checker and in nuXmv, and its retained bundle used
to be a single reading of a single plan. This generator measures a structured grid instead - two plan
shapes x two effect summaries x four bounds - so the reading is agreement over a population with a
positive control, not a single all-clear. These tests pin the grid, the class comparison, the control,
the recorded numbers and the boundary sentence the SUMMARY must carry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import generate_backend_cross_validation as cross
from scripts import generate_delegation_defect_sweep as sweep
from scripts import generate_plan_ir_evidence as plan_ir
from scripts import generate_three_way_agreement as three_way

pytestmark = pytest.mark.integration


def test_safe_family_matches_the_sibling_generators() -> None:
    """Four generators must not disagree about which verdicts mean "no violation found"."""
    assert plan_ir.SAFE_FAMILY == cross.SAFE_FAMILY == sweep.SAFE_FAMILY == three_way.SAFE_FAMILY


def test_the_grid_is_every_combination_of_plans_effects_and_bounds() -> None:
    """The population is closed by construction: 2 x 2 x 4 readings, each appearing once."""
    rows = plan_ir.rows_for()
    assert len(rows) == 16
    keys = {(row["plan_case"], row["effect_case"], row["bound"]) for row in rows}
    assert len(keys) == 16
    assert keys == {
        (case, effect_case, bound) for case in plan_ir.PLAN_CASES for effect_case in plan_ir.EFFECT_CASES for bound in plan_ir.BOUNDS
    }


def test_every_reading_agrees_across_all_three_backends() -> None:
    """The claim is class agreement on every reading, with the encodings measured, not assumed."""
    rows = plan_ir.rows_for()
    assert all(row["all_three_agree_class"] for row in rows)
    assert all(row["verdicts_agree_class"] for row in rows)
    assert all(row["nuxmv_agrees_class"] for row in rows)
    assert all(row["z3_measured"] and row["nuxmv_measured"] for row in rows)
    assert all(row["nuxmv_solver_hash"] for row in rows)


def test_unauthorised_readings_are_refuted_and_authorised_ones_are_not() -> None:
    """The positive control: the grid cannot be an all-clear, because half of it must fail."""
    rows = plan_ir.rows_for()
    refuted = [row for row in rows if row["reference_verdict"] == "unsafe"]
    cleared = [row for row in rows if row["reference_verdict"] in plan_ir.SAFE_FAMILY]
    assert len(refuted) == 8
    assert len(cleared) == 8
    assert {row["effect_case"] for row in refuted} == {"unauthorised"}
    assert {row["effect_case"] for row in cleared} == {"authorised"}
    assert all(row["z3_verdict"] == "unsafe" and row["nuxmv_verdict"] == "unsafe" for row in refuted)


def test_generate_writes_a_bundle_and_documents_the_boundary(tmp_path: Path) -> None:
    """The write path records the counts, the control and the boundary text."""
    rows = plan_ir.rows_for()
    assert plan_ir.generate(tmp_path, rows=rows) == 0
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["all_agree"] is True
    assert evidence["total_readings"] == 16
    assert evidence["three_way_agreements"] == 16
    assert evidence["positive_control"] == 8
    assert evidence["baseline"]["bound"] == max(plan_ir.BOUNDS)
    summary = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    assert evidence["boundary"] in summary
    assert "not a claim" in summary
    assert "structured, not selected" in summary
    assert "Rerun:" in summary


def test_generate_refuses_a_grid_that_nothing_can_refute(tmp_path: Path) -> None:
    """An all-clear over a grid with no refuted reading is refused, not reported as agreement."""

    def row(identifier: str, verdict: str) -> dict[str, object]:
        return {
            "ir_id": identifier,
            "plan_case": "single",
            "effect_case": "authorised",
            "bound": 1,
            "reference_verdict": verdict,
            "verdicts_agree_class": True,
            "nuxmv_agrees_class": True,
            "all_three_agree_class": True,
        }

    assert plan_ir.generate(tmp_path, [row("only-safe", "safe")]) == 1
    assert plan_ir.generate(tmp_path, [row("refuted", "unsafe")]) == 0


def test_check_reports_drift_and_matches_after_a_write(tmp_path: Path) -> None:
    """The retained bundle is only trustworthy if --check can fail: pin both directions."""
    rows = plan_ir.rows_for()
    assert plan_ir.check(tmp_path, rows) == 1  # nothing retained yet
    assert plan_ir.generate(tmp_path, rows=rows) == 0
    assert plan_ir.check(tmp_path, rows) == 0
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    evidence["results"][0]["reference_verdict"] = "unknown"
    (tmp_path / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    assert plan_ir.check(tmp_path, rows) == 1
