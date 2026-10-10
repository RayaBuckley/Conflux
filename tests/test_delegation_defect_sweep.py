"""Contracts for the delegation defect sweep bundle.

The sibling cross-validation measures one hand-built mutation at a time; this generator closes the
population, so every subset of the nine independent defects is measured and the reading is agreement
over a space rather than over a chosen list. These tests pin the population size, the class comparison,
the positive control, the recorded numbers and the boundary sentence the SUMMARY must carry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import generate_backend_cross_validation as cross
from scripts import generate_delegation_defect_sweep as sweep
from scripts import generate_three_way_agreement as three_way

pytestmark = pytest.mark.integration


def test_safe_family_matches_the_sibling_generators() -> None:
    """Three generators must not disagree about which verdicts mean "no violation found"."""
    assert sweep.SAFE_FAMILY == cross.SAFE_FAMILY == three_way.SAFE_FAMILY


def test_the_population_is_every_subset_of_the_defect_space() -> None:
    """512 subsets, closed by construction: no duplicates, and both ends of the space present."""
    from conflux.verification.delegation_ir import DELEGATION_IR_DEFECTS

    subsets = sweep.defect_subsets()
    assert len(subsets) == 512
    assert len(set(subsets)) == 512
    assert frozenset() in subsets
    assert frozenset(DELEGATION_IR_DEFECTS) in subsets


def test_every_subset_that_names_a_defect_is_refuted_by_both_backends() -> None:
    """The measurement the bundle records: 511 refuted subsets and one safe canonical body."""
    evidence = sweep.build()
    assert evidence["total_subsets"] == 512
    assert evidence["agreements"] == 512
    assert evidence["all_agree"] is True
    assert evidence["disagreements"] == 0
    assert evidence["raw_agreements"] == 511
    assert evidence["raw_disagreements"] == 1
    assert evidence["positive_control"] == 511
    assert evidence["unrefuted"] == ["delegation-ir:combined:none"]
    assert evidence["unmeasured"] == []
    for row in evidence["results"]:
        assert row["verdicts_agree_class"] is True
        if row["defect_count"]:
            assert row["reference_verdict"] == "unsafe"
            assert row["z3_verdict"] == "unsafe"
        else:
            assert row["reference_verdict"] == "safe"
            assert row["z3_verdict"] == "bounded_safe"


def test_generate_writes_a_bundle_and_documents_the_boundary(tmp_path: Path) -> None:
    """The retained bundle records the counts and states what agreement does not prove."""
    assert sweep.generate(tmp_path) == 0
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["all_agree"] is True
    assert evidence["boundary"] in (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    summary = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    assert "not a proof of the delegation semantics" in summary
    assert "closed by construction" in summary
    assert "Rerun:" in summary


def test_generate_refuses_a_space_that_nothing_can_refute(tmp_path: Path) -> None:
    """An all-clear over a space with no refuted subset is refused, not reported as agreement."""

    def row(identifier: str, verdict: str) -> dict[str, object]:
        return {
            "ir_id": identifier,
            "defect_count": 0,
            "reference_verdict": verdict,
            "verdicts_agree_raw": True,
            "verdicts_agree_class": True,
            "z3_measured": True,
        }

    assert sweep.generate(tmp_path, [row("only-safe", "safe")]) == 1
    assert sweep.generate(tmp_path, [row("refuted", "unsafe")]) == 0


def test_check_reports_drift_and_matches_after_a_write(tmp_path: Path) -> None:
    """The retained bundle is only trustworthy if --check can fail: pin both directions."""
    assert sweep.check(tmp_path) == 1  # nothing retained yet
    assert sweep.generate(tmp_path) == 0
    assert sweep.check(tmp_path) == 0
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    evidence["results"][0]["reference_verdict"] = "unknown"
    (tmp_path / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    assert sweep.check(tmp_path) == 1
