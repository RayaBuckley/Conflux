"""Contracts for the cross-backend validation bundle (z3 against the reference interpreter).

The generator compares two encodings of the delegation IR on one fixed family. Only one reading of
"agreement" is sound: the bounded checker reports ``bounded_safe`` where the interpreter reports
``safe``, so a raw string comparison reports a disagreement on a run that has none. These tests pin the
class comparison, keep the raw comparison in the record, pin the positive control and the unsafe-family
guard, and pin the boundary sentence the SUMMARY must carry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import generate_backend_cross_validation as cross
from scripts import generate_z3_agreement as z3_agreement

pytestmark = pytest.mark.integration


def test_verdict_classes_match_the_sibling_generator() -> None:
    """Two generators must not disagree about which verdicts mean "no violation found"."""
    assert cross.SAFE_FAMILY == z3_agreement.SAFE_FAMILY
    for verdict in ("safe", "bounded_safe", "unsafe", "unknown"):
        assert cross.verdict_class(verdict) == z3_agreement.verdict_class(verdict)


def test_the_family_agrees_by_class_with_a_positive_control() -> None:
    """Every variant agrees by class, the raw difference stays visible, and refusal is possible."""
    evidence = cross.build()
    assert evidence["total_variants"] >= 2
    assert evidence["all_agree"] is True
    assert evidence["disagreements"] == 0
    assert evidence["positive_control"] >= 1
    assert evidence["raw_disagreements"] >= 1
    assert evidence["raw_disagreement_ids"]
    assert evidence["unmeasured"] == []
    for row in evidence["results"]:
        assert row["verdicts_agree_class"] is True
        assert isinstance(row["verdicts_agree_raw"], bool)
        assert isinstance(row["z3_counterexample"], bool)


def test_generate_writes_a_bundle_and_documents_the_boundary(tmp_path: Path) -> None:
    """The retained bundle records the counts and states what agreement does not prove."""
    assert cross.generate(tmp_path) == 0
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["all_agree"] is True
    summary = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    assert "not a proof of the IR semantics" in summary
    assert "Rerun:" in summary


def test_generate_refuses_a_family_that_nothing_can_refute(tmp_path: Path) -> None:
    """An all-clear over a family with no unsafe variant is refused, not reported as agreement."""

    def row(identifier: str, verdict: str) -> dict[str, object]:
        return {
            "ir_id": identifier,
            "reference_verdict": verdict,
            "verdicts_agree_raw": True,
            "verdicts_agree_class": True,
            "z3_measured": True,
        }

    assert cross.generate(tmp_path, [row("only-safe", "safe")]) == 1
    assert cross.generate(tmp_path, [row("refuted", "unsafe")]) == 0
