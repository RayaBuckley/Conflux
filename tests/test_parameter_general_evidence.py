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
        assert row["route"] in {"nuxmv-msat", "nuxmv-ic3"}
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


def test_positive_row_names_no_bound_and_no_depth(bundle: dict[str, Any]) -> None:
    positive = [row for row in bundle["rows"] if row["expectation"] == "safe"]
    assert len(positive) == 1
    row = positive[0]
    assert row["verdict"] == "safe"
    assert row["status"] == "complete"
    assert row["step_counter_has_declared_range"] is False
    for forbidden in ("bound", "depth", "checked_steps", "unrolling", "counterexample_length"):
        assert forbidden not in row, f"positive row smuggles {forbidden}"
        assert forbidden not in bundle, f"bundle smuggles {forbidden}"
    assert bundle["summary"]["errors"] == []


def test_controls_withhold_a_verdict(bundle: dict[str, Any]) -> None:
    controls = [row for row in bundle["rows"] if row["expectation"] != "safe"]
    assert len(controls) == 2
    weakened = next(row for row in controls if row["expectation"] == "not_safe")
    assert weakened["verdict"] != "safe"
    fail_closed = next(row for row in controls if row["expectation"] == "unknown_fail_closed")
    assert fail_closed["verdict"] == "unknown"
    assert (fail_closed["error"] or "").startswith("unsupported_ir")


def test_missing_binary_claims_no_verdict(tmp_path: Path) -> None:
    fresh = _generator().build_bundle(binary=str(tmp_path / "nuXmv-missing"), timeout=5.0)
    positive = next(row for row in fresh["rows"] if row["expectation"] == "safe")
    assert positive["status"] == "nuxmv_unavailable"
    assert positive["verdict"] == "unknown"
