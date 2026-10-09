"""Guard the z3 agreement evidence bundle and the provenance it records.

The bundle is the repository's record that the bounded model checker and the
reference interpreter agree on the cone-of-influence fixtures. Two defects made
that record misleading before this test existed:

* ``all_agree`` compared raw verdict strings, so the bounded checker's
  ``bounded_safe`` could never agree with the reference interpreter's ``safe``
  and the flag read ``false`` for every safe fixture;
* ``counterexample`` was ``result.counterexample is not None``, which is ``true``
  for every result because the dataclass default is an empty tuple, so a
  ``bounded_safe`` verdict was reported as carrying a counterexample.

The tests below pin the corrected semantics: agreement is compared by verdict
class, the raw comparison is retained separately, an unmeasured run claims
nothing, and a counterexample flag is only set when a witness exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from scripts.generate_z3_agreement import SAFE_FAMILY, generate, verdict_class

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "research" / "output" / "runs" / "z3-agreement-v1" / "result.json"


def _bundle() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(BUNDLE.read_text(encoding="utf-8")))



def test_retained_bundle_agrees_under_verdict_classes() -> None:
    """Every measured fixture agrees once bounded and unbounded verdicts are classed."""
    summary = _bundle()["summary"]
    assert summary["z3_measured"] == summary["total_fixtures"]
    assert summary["all_agree"] is True


def test_retained_bundle_keeps_the_raw_comparison_separate() -> None:
    """The raw-string comparison is recorded, so the vocabulary gap stays visible."""
    bundle = _bundle()
    measured = [f for f in bundle["fixtures"] if f["z3_original"]["measured"] and f["z3_reduced"]["measured"]]
    raw = all(
        f["z3_original"]["verdict"] == f["z3_reduced"]["verdict"] == f["reference_verdict"] for f in measured
    )
    assert bundle["summary"]["raw_verdict_agreement"] is raw
    assert any(f["reference_verdict"] in SAFE_FAMILY for f in bundle["fixtures"]), (
        "the bundle must keep a safe fixture, otherwise the class comparison is untested"
    )


def test_counterexample_flag_is_only_set_when_a_witness_exists() -> None:
    """A bounded_safe verdict carries no counterexample; an unsafe one does."""
    for fixture in _bundle()["fixtures"]:
        for side in ("z3_original", "z3_reduced"):
            result = fixture[side]
            if result["verdict"] in SAFE_FAMILY:
                assert result["counterexample"] is False
                assert result["counterexample_length"] == 0
            else:
                assert result["counterexample"] is True
                assert result["counterexample_length"] >= 1


def test_unmeasured_solver_never_claims_agreement() -> None:
    """With no solver installed the summary reports nothing measured and no agreement."""
    if "z3" in sys.modules:
        del sys.modules["z3"]
    with patch.dict(sys.modules, {"z3": None}):
        bundle = generate()
    assert bundle["summary"]["z3_measured"] == 0
    assert bundle["summary"]["all_agree"] is None
    assert bundle["summary"]["raw_verdict_agreement"] is None
    assert {f["z3_original"]["verdict"] for f in bundle["fixtures"]} == {"unknown"}


def test_verdict_class_treats_bounded_safe_as_safe() -> None:
    """The class mapping is the whole point of the comparison, so pin it."""
    assert verdict_class("bounded_safe") == "safe"
    assert verdict_class("safe") == "safe"
    assert verdict_class("unsafe") == "unsafe"
    assert verdict_class("unknown") == "unknown"
