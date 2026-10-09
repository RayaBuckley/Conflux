"""Tests for defence model verification evidence generation."""

from __future__ import annotations

import importlib.util
import json
from typing import Any

import pytest

from scripts.generate_defence_evidence import generate

pytestmark = pytest.mark.reproducibility

UNAVAILABLE_Z3 = "optional_dependency_unavailable:z3"
SAFE_VERDICTS = ("safe", "bounded_safe")
UNSAFE_VERDICTS = ("unsafe",)


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    """Build the defence bundle once; a single generation re-runs every model."""
    return generate()


def _pe_results(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [model["pe_property"] for model in bundle["models"]]


def _native_results(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [model["native_property"] for model in bundle["models"] if model["native_property"] is not None]


def _measured(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows where the optional solver answered the property query."""
    return [row for row in rows if row["error"] is None]


def _safe_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row["verdict"] in SAFE_VERDICTS)


def _unsafe_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row["verdict"] in UNSAFE_VERDICTS)


class TestDefenceEvidenceBundle:
    """Test the full defence model evidence bundle generation."""

    def test_bundle_has_correct_schema(self, bundle: dict[str, Any]) -> None:
        assert bundle["schema_version"] == "1"
        assert bundle["id"] == "defence-models-v1"

    def test_bundle_covers_every_model(self, bundle: dict[str, Any]) -> None:
        assert bundle["models"]
        assert bundle["summary"]["total_models"] == len(bundle["models"])
        assert all(model["pe_property"] is not None for model in bundle["models"])

    def test_every_property_records_solver_provenance(self, bundle: dict[str, Any]) -> None:
        """Every property result records the solver verdict *and* the solver error."""
        for model in bundle["models"]:
            for key in ("pe_property", "native_property"):
                result = model[key]
                if result is None:
                    continue
                assert set(result) == {
                    "verdict",
                    "error",
                    "counterexample",
                    "counterexample_length",
                    "reference_verdict",
                    "reference_states",
                    "nuxmv_verdict",
                    "nuxmv_error",
                }, (model["name"], key)

    def test_pe_counters_cover_measured_models_only(self, bundle: dict[str, Any]) -> None:
        """UNKNOWN must never count as safe, and unmeasured models must not be counted."""
        measured = _measured(_pe_results(bundle))
        summary = bundle["summary"]
        assert summary["pe_measured"] == len(measured)
        assert summary["pe_safe"] == _safe_count(measured)
        assert summary["pe_unsafe"] == _unsafe_count(measured)
        assert summary["pe_unknown"] == len(measured) - _safe_count(measured) - _unsafe_count(measured)
        assert summary["pe_safe"] + summary["pe_unsafe"] + summary["pe_unknown"] == summary["pe_measured"]

    def test_native_counter_covers_measured_models_only(self, bundle: dict[str, Any]) -> None:
        measured = _measured(_native_results(bundle))
        summary = bundle["summary"]
        assert summary["native_measured"] == len(measured)
        assert summary["native_satisfied"] == _safe_count(measured)
        assert summary["native_unknown"] == len(measured) - _safe_count(measured) - _unsafe_count(measured)
        assert summary["native_satisfied"] + summary["native_unknown"] <= summary["native_measured"]

    def test_unmeasured_models_never_count_as_safe(self, bundle: dict[str, Any]) -> None:
        """Assert the counters, or the documented unavailable state where z3 is absent.

        Without the optional solver every property returns UNKNOWN with
        ``optional_dependency_unavailable:z3``, so a counter that treats every
        non-unsafe verdict as safe would report ``pe_safe: 6`` and
        ``native_satisfied: 4`` for measurements nobody made.  Assert the
        documented marker and zero measured counters instead.
        """
        pe_results = _pe_results(bundle)
        measured = _measured(pe_results)
        summary = bundle["summary"]
        if importlib.util.find_spec("z3") is None:
            assert not measured, "no model may report a z3 measurement while the solver is absent"
            assert {row["error"] for row in pe_results} == {UNAVAILABLE_Z3}
            assert summary["pe_measured"] == 0
            assert summary["pe_safe"] == 0, "UNKNOWN must not be counted as safe"
            assert summary["pe_unsafe"] == 0
            assert summary["pe_unknown"] == 0
            assert summary["native_measured"] == 0
            assert summary["native_satisfied"] == 0, "UNKNOWN must not be counted as satisfied"
            assert bundle["formal_backends"]["z3"] == {"available": False, "reason": "unavailable"}
            assert bundle["available_formal_backends"] == []
            return
        assert len(measured) == len(pe_results), "every model must be measured before the counters are trusted"
        assert bundle["formal_backends"]["z3"] == {"available": True, "reason": None}
        assert "z3" in bundle["available_formal_backends"]

    def test_ites_and_requester_only_rows_agree_with_the_reference_where_measured(self, bundle: dict[str, Any]) -> None:
        """The ITES claim rows are solver-backed, so check them wherever z3 answered."""
        by_name = {model["name"]: model["pe_property"] for model in bundle["models"]}
        expected = {"ITES": (SAFE_VERDICTS, False), "Requester-only": (UNSAFE_VERDICTS, True)}
        for name, (verdicts, witness_expected) in expected.items():
            result = by_name[name]
            assert result["reference_verdict"] in verdicts, name
            if result["error"] is None:
                assert result["verdict"] in verdicts, name
                assert result["counterexample"] == witness_expected, name
                assert (result["counterexample_length"] > 0) == witness_expected, name
        if all(by_name[name]["error"] is None for name in expected):
            assert bundle["summary"]["pe_safe"] >= 1
            assert bundle["summary"]["pe_unsafe"] >= 1

    def test_counterexample_flag_tracks_witness_length(self, bundle: dict[str, Any]) -> None:
        """A bounded-safe row must not report a counterexample.

        ``FormalVerificationResult.counterexample`` defaults to an empty tuple, so
        ``is not None`` reports a witness for bounded-safe rows; the flag must
        follow the recorded witness instead.
        """
        for model in bundle["models"]:
            for key in ("pe_property", "native_property"):
                result = model[key]
                if result is None:
                    continue
                assert result["counterexample"] == (result["counterexample_length"] > 0), (model["name"], key)
                if result["error"] is None:
                    assert result["counterexample"] == (result["verdict"] in UNSAFE_VERDICTS), (model["name"], key)

    def test_deterministic_regeneration(self, bundle: dict[str, Any]) -> None:
        regenerated = generate()
        assert json.dumps(bundle, sort_keys=True) == json.dumps(regenerated, sort_keys=True)
