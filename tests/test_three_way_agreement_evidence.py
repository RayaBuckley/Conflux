"""Guard the three-way agreement bundle and the rules that keep it honest.

The bundle records that the reference interpreter, the Z3 bounded model checker and the nuXmv IC3
backend agree on every delegation IR variant they both measured, and that the battery contains
refuted variants, so it is not a set of trivially safe cases. These tests pin the rules around it:
an unmeasured backend never counts as agreement, a disagreement is reported, the safe-verdict class
means the same thing here as in the cone-of-influence bundle, and a battery with no violation fails.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from scripts import generate_three_way_agreement as three
from scripts.generate_z3_agreement import SAFE_FAMILY, verdict_class

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "research" / "output" / "runs" / "three-way-agreement-v1" / "result.json"


def _bundle() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(BUNDLE.read_text(encoding="utf-8")))


def _row(
    reference: str,
    z3: str,
    nuxmv: str,
    *,
    z3_measured: bool = True,
    nuxmv_measured: bool = True,
) -> dict[str, Any]:
    return {
        "ir_id": "delegation-ir:test",
        "ir_fingerprint": "f" * 16,
        "mutation": "canonical",
        "reference": reference,
        "reference_states": 1,
        "z3": {
            "verdict": z3,
            "measured": z3_measured,
            "counterexample": False,
            "counterexample_length": 0,
        },
        "nuxmv": {
            "verdict": nuxmv,
            "measured": nuxmv_measured,
            "error": None,
            "counterexample": False,
            "counterexample_length": 0,
        },
    }


def test_safe_family_matches_the_cone_of_influence_copy() -> None:
    assert three.SAFE_FAMILY == SAFE_FAMILY
    for verdict in ("safe", "bounded_safe", "unsafe", "unknown"):
        assert three.verdict_class(verdict) == verdict_class(verdict)


def test_retained_bundle_agrees_on_every_variant_it_measured() -> None:
    summary = _bundle()["summary"]
    assert summary["total_variants"] == 11
    assert summary["z3_measured"] == 11
    assert summary["nuxmv_measured"] == 11
    assert summary["all_agree"] is True
    assert summary["agree_all_three"] == summary["total_variants"]


def test_retained_bundle_carries_a_refuted_control() -> None:
    bundle = _bundle()
    assert bundle["summary"]["control_ok"] is True
    assert bundle["summary"]["refuted_variants"] >= 1
    canonical = [row for row in bundle["results"] if row["mutation"] == "canonical"]
    assert len(canonical) == 1
    assert canonical[0]["reference"] == "safe"
    assert canonical[0]["z3"]["verdict"] == "bounded_safe"


def test_retained_bundle_keeps_raw_verdicts_and_fingerprints() -> None:
    for row in _bundle()["results"]:
        assert row["ir_fingerprint"]
        assert row["reference"] in {"safe", "unsafe", "unknown"}
        assert row["z3"]["verdict"]
        assert row["nuxmv"]["verdict"]
        assert isinstance(row["z3"]["counterexample"], bool)


def test_an_unmeasured_backend_never_counts_as_agreement() -> None:
    summary = three.summarise([_row("safe", "safe", "unknown", nuxmv_measured=False)])
    assert summary["z3_measured"] == 1
    assert summary["nuxmv_measured"] == 0
    assert summary["agree_all_three"] is None
    assert summary["all_agree"] is None


def test_disagreement_is_reported() -> None:
    summary = three.summarise([_row("unsafe", "unsafe", "safe")])
    assert summary["agree_reference_z3"] == 1
    assert summary["agree_reference_nuxmv"] == 0
    assert summary["all_agree"] is False


def test_control_fails_when_no_variant_is_refuted() -> None:
    summary = three.summarise([_row("safe", "safe", "safe")])
    assert summary["refuted_variants"] == 0
    assert summary["control_ok"] is False


def test_main_fails_the_run_when_the_battery_holds_no_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(three, "collect", lambda backend=None: [_row("safe", "safe", "safe")])
    assert three.main(["--output", str(tmp_path)]) == 1


def test_check_reports_a_difference_and_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "bundle"
    out.mkdir()
    retained = out / "result.json"
    retained.write_text(json.dumps({"summary": {"total_variants": 999}}), encoding="utf-8")
    monkeypatch.setattr(three, "collect", lambda backend=None: [_row("unsafe", "unsafe", "unsafe")])
    before = retained.read_text(encoding="utf-8")
    assert three.main(["--output", str(out), "--check"]) == 1
    assert retained.read_text(encoding="utf-8") == before
