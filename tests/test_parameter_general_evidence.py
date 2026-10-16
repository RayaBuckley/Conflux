"""Checks for the parameter-general bundle: the rows must keep the claim honest."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "research" / "output" / "runs" / "parameter-general-v1" / "result.json"


def _generator() -> Any:
    """Load the bundle generator by path, as its documented invocation does."""
    path = ROOT / "scripts" / "generate_parameter_general_evidence.py"
    spec = importlib.util.spec_from_file_location("generate_parameter_general_evidence", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    if not BUNDLE_PATH.exists():
        pytest.skip("parameter-general bundle has not been generated")
    data: dict[str, Any] = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    return data


def test_rows_name_their_parameter_and_invariant(bundle: dict[str, Any]) -> None:
    assert bundle["rows"], "bundle carries no rows"
    for row in bundle["rows"]:
        assert row["route"] in {"nuxmv-msat", "nuxmv-ic3", "nuxmv-predabs"}
        assert row["symbolic_parameter"].strip()
        assert row["auxiliary_invariant"].strip()
        assert row["expectation"]
        if row["expectation"] == "unknown_fail_closed":
            # The finite-domain route refuses the model before rendering it, so no model hash exists
            # for this row: a model that could not be rendered is not evidence of anything.
            assert row["smv_sha256"] is None
            assert row["stdout_sha256"] is None
        else:
            assert row["smv_sha256"]
            assert row["stdout_sha256"]


def test_positive_rows_name_no_bound_and_no_depth(bundle: dict[str, Any]) -> None:
    """One positive row per unbounded route, over the same model, and neither names a bound."""
    positive = [row for row in bundle["rows"] if row["expectation"] == "safe"]
    assert {row["route"] for row in positive} == {"nuxmv-msat", "nuxmv-predabs"}
    assert len({row["ir_fingerprint"] for row in positive}) == 1, "positive rows must be one model"
    for row in positive:
        assert row["verdict"] == "safe"
        assert row["status"] == "complete"
        assert row["step_counter_has_declared_range"] is False
    for forbidden in ("bound", "depth", "checked_steps", "unrolling", "counterexample_length"):
        assert forbidden not in bundle, f"bundle smuggles {forbidden}"
        for row in positive:
            assert forbidden not in row, f"positive row smuggles {forbidden}"
    assert bundle["summary"]["errors"] == []


def test_the_route_that_withholds_is_paired_with_the_route_that_settles(bundle: dict[str, Any]) -> None:
    """The bundle shows the difference between the two unbounded routes over one model.

    The code/capability family carries two rows with the same IR fingerprint: k-induction reports
    an incomplete induction, CEGAR returns a counterexample for the same model. Without the pair a
    reader could take "we have an unbounded route" for "we have a verdict for this family".
    """
    rows = {row["row_id"]: row for row in bundle["rows"]}
    incomplete = rows["plan-ir:code:capability:smt:induction-incomplete"]
    refuted = rows["plan-ir:code:capability:predabs:counterexample"]
    assert incomplete["ir_fingerprint"] == refuted["ir_fingerprint"]
    assert incomplete["route"] == "nuxmv-msat"
    assert incomplete["verdict"] == "unknown"
    assert (incomplete["error"] or "").startswith("nuxmv_incomplete")
    assert refuted["route"] == "nuxmv-predabs"
    assert refuted["verdict"] == "unsafe"
    assert refuted["counterexample_present"] is True


def test_controls_withhold_a_verdict(bundle: dict[str, Any]) -> None:
    controls = [row for row in bundle["rows"] if row["expectation"] != "safe"]
    assert {row["expectation"] for row in controls} == {"not_safe", "unknown_fail_closed", "unknown_incomplete"}
    assert all(row["verdict"] != "safe" for row in controls)
    fail_closed = next(row for row in controls if row["expectation"] == "unknown_fail_closed")
    assert fail_closed["verdict"] == "unknown"
    assert (fail_closed["error"] or "").startswith("unsupported_ir")
    # The weakened control is carried on both unbounded routes over one fingerprint:
    # k-induction only withholds agreement, CEGAR refutes it.
    weakened = {
        row["route"]: row for row in controls if "weakened" in row["row_id"]
    }
    assert set(weakened) == {"nuxmv-msat", "nuxmv-predabs"}
    assert len({row["ir_fingerprint"] for row in weakened.values()}) == 1
    assert weakened["nuxmv-msat"]["verdict"] == "unknown"
    assert weakened["nuxmv-predabs"]["verdict"] == "unsafe"


def test_missing_binary_claims_no_verdict(tmp_path: Path) -> None:
    fresh = _generator().build_bundle(binary=str(tmp_path / "nuXmv-missing"), timeout=5.0)
    positive = next(row for row in fresh["rows"] if row["expectation"] == "safe")
    assert positive["status"] == "nuxmv_unavailable"
    assert positive["verdict"] == "unknown"
