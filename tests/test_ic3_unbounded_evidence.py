"""IC3 evidence bundle: retained nuXmv verdicts over the recorded finite-IR families."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "research" / "output" / "runs" / "ic3-unbounded-v1"


def _load_generator() -> Any:
    """Load the generator module without importing the scripts directory as a package."""
    path = ROOT / "scripts" / "generate_ic3_unbounded_evidence.py"
    spec = importlib.util.spec_from_file_location("generate_ic3_unbounded_evidence", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    """Return the retained IC3 evidence bundle."""
    data: dict[str, Any] = json.loads((BUNDLE / "result.json").read_text(encoding="utf-8"))
    return data


def test_bundle_counts_are_complete_and_record_witness_lengths(bundle: dict[str, Any]) -> None:
    summary = bundle["summary"]
    assert summary["total"] == 689
    assert summary["by_verdict"] == {"safe": 99, "unsafe": 590}
    assert summary["by_status"] == {"complete": 689}
    assert summary["errors"] == []
    assert len(bundle["models"]) == summary["total"]
    assert len({model["row_id"] for model in bundle["models"]}) == summary["total"]
    for model in bundle["models"]:
        lengths = model["witness_lengths"]
        assert isinstance(lengths, list)
        assert all(isinstance(length, int) and length >= 1 for length in lengths)
        if model["verdict"] == "unsafe":
            assert lengths
        else:
            assert lengths == []
        assert model["smv_sha256"]
        assert model["stdout_sha256"]
        assert model["verdict"] in {"safe", "unsafe", "unknown"}


def test_protocol_states_the_measured_witness_rule() -> None:
    protocol: dict[str, Any] = json.loads((BUNDLE / "protocol.json").read_text(encoding="utf-8"))
    assert "witness_rule" in protocol
    assert "no_witness_rule" not in protocol
    assert "witness_lengths" in protocol["witness_rule"]


def test_every_refutation_records_a_trace_and_no_safe_row_does(bundle: dict[str, Any]) -> None:
    unsafe = [model for model in bundle["models"] if model["verdict"] == "unsafe"]
    safe = [model for model in bundle["models"] if model["verdict"] == "safe"]
    assert len(unsafe) == 590
    assert len(safe) == 99
    assert all(model["witness_lengths"] for model in unsafe)
    assert all(not model["witness_lengths"] for model in safe)
    assert sum(len(model["witness_lengths"]) for model in unsafe) == 3204


def test_depth_family_carries_no_unsafe_control(bundle: dict[str, Any]) -> None:
    depth = [model for model in bundle["models"] if "depth" in model["row_id"]]
    unsafe_rows = [model for model in depth if "unsafe" in model["row_id"]]
    assert len(unsafe_rows) == 10
    assert {model["verdict"] for model in unsafe_rows} == {"safe"}


def test_missing_binary_claims_no_verdict() -> None:
    module = _load_generator()
    bundle = module.generate(("defence",), "nuXmv-that-does-not-exist", 5.0)
    assert bundle["summary"]["total"] == 10
    assert set(bundle["summary"]["by_status"]) == {"nuxmv_unavailable"}
    assert set(bundle["summary"]["by_verdict"]) == {"unknown"}
