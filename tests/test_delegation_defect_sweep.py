"""Contracts for the delegation defect sweep bundle.

The sibling cross-validation measures one hand-built mutation at a time; this generator closes the
population, so every subset of the nine independent defects is measured and the reading is agreement
over a space rather than over a chosen list. These tests pin the population size, the class comparison,
the positive control, the recorded numbers and the boundary sentence the SUMMARY must carry.

The heavy assertion - all three backends over all 512 subsets - is what the retained bundle records, and
the standard-tier `--check` step re-measures it on every run. These tests measure a sample so the suite
stays cheap; the population itself is asserted by enumeration, which costs nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conflux.verification.delegation_ir import DELEGATION_IR_DEFECTS
from conflux.verification.nuxmv_backend import NuXmvBackend
from scripts import generate_backend_cross_validation as cross
from scripts import generate_delegation_defect_sweep as sweep
from scripts import generate_three_way_agreement as three_way

pytestmark = pytest.mark.integration


def test_safe_family_matches_the_sibling_generators() -> None:
    """Three generators must not disagree about which verdicts mean "no violation found"."""
    assert sweep.SAFE_FAMILY == cross.SAFE_FAMILY == three_way.SAFE_FAMILY


def test_the_population_is_every_subset_of_the_defect_space() -> None:
    """512 subsets, closed by construction: no duplicates, and both ends of the space present."""
    subsets = sweep.defect_subsets()
    assert len(subsets) == 512
    assert len(set(subsets)) == 512
    assert frozenset() in subsets
    assert frozenset(DELEGATION_IR_DEFECTS) in subsets


def test_a_measured_sample_agrees_across_all_three_backends() -> None:
    """Canonical, one defect, a pair and the composition of all nine agree, as the bundle records."""
    backend = NuXmvBackend()
    sample = [
        (frozenset(), "safe", "bounded_safe", "safe"),
        (frozenset({DELEGATION_IR_DEFECTS[0]}), "unsafe", "unsafe", "unsafe"),
        (frozenset(DELEGATION_IR_DEFECTS[:2]), "unsafe", "unsafe", "unsafe"),
        (frozenset(DELEGATION_IR_DEFECTS), "unsafe", "unsafe", "unsafe"),
    ]
    for defects, reference, z3, nuxmv in sample:
        row = sweep._row(defects, backend)
        assert row["reference_verdict"] == reference
        assert row["z3_verdict"] == z3
        assert row["nuxmv_verdict"] == nuxmv
        assert row["nuxmv_measured"] is True
        assert row["all_three_agree_class"] is True
        assert row["nuxmv_agrees_class"] is True
        assert row["verdicts_agree_class"] is True
        assert row["defect_count"] == len(defects)
        assert row["ir_id"] == f"delegation-ir:combined:{'+'.join(sorted(d.value for d in defects)) or 'none'}"


def test_canonical_is_the_only_raw_difference_between_the_interpreter_and_z3() -> None:
    """The bounded checker's `bounded_safe` is a scope difference, and nuXmv does not share it."""
    backend = NuXmvBackend()
    canonical = sweep._row(frozenset(), backend)
    assert canonical["verdicts_agree_raw"] is False
    assert canonical["verdicts_agree_class"] is True
    assert canonical["nuxmv_agrees_raw"] is True


def test_generate_writes_a_bundle_and_documents_the_boundary(tmp_path: Path) -> None:
    """The write path records counts, the closed-population sentence and the boundary text."""
    backend = NuXmvBackend()
    rows = [sweep._row(frozenset(), backend), sweep._row(frozenset({DELEGATION_IR_DEFECTS[0]}), backend)]
    assert sweep.generate(tmp_path, rows=rows) == 0
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["all_agree"] is True
    assert evidence["total_subsets"] == 2
    assert evidence["three_way_agreements"] == 2
    summary = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    assert evidence["boundary"] in summary
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
            "nuxmv_agrees_raw": True,
            "nuxmv_agrees_class": True,
            "all_three_agree_class": True,
            "nuxmv_measured": True,
            "z3_measured": True,
        }

    assert sweep.generate(tmp_path, [row("only-safe", "safe")]) == 1
    assert sweep.generate(tmp_path, [row("refuted", "unsafe")]) == 0


def test_check_reports_drift_and_matches_after_a_write(tmp_path: Path) -> None:
    """The retained bundle is only trustworthy if --check can fail: pin both directions."""
    backend = NuXmvBackend()
    rows = [sweep._row(frozenset(), backend), sweep._row(frozenset(DELEGATION_IR_DEFECTS), backend)]
    assert sweep.check(tmp_path, rows) == 1  # nothing retained yet
    assert sweep.generate(tmp_path, rows=rows) == 0
    assert sweep.check(tmp_path, rows) == 0
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    evidence["results"][0]["reference_verdict"] = "unknown"
    (tmp_path / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    assert sweep.check(tmp_path, rows) == 1
