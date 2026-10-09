"""Tests for defence model verification evidence generation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import scripts.generate_defence_evidence as generator
from conflux.verification.results import FormalVerdict
from scripts.generate_defence_evidence import generate

pytestmark = pytest.mark.reproducibility

UNAVAILABLE_Z3 = "optional_dependency_unavailable:z3"
NUXMV_UNAVAILABLE = "optional_binary_unavailable:nuXmv"
SAFE_VERDICTS = ("safe", "bounded_safe")
UNSAFE_VERDICTS = ("unsafe",)
INCONCLUSIVE_VERDICT = "unknown"

# The corpus's only nuXmv measurement, taken on a nuXmv-capable host and retained
# in the bundle committed at bbd59a2.  It is not reproducible on this host, which
# has no nuXmv binary.
PRESERVED_NUXMV = {
    "Dual-LLM": {"pe": "unsafe", "native": "safe"},
    "CaMeL": {"pe": "unsafe", "native": "safe"},
    "Progent": {"pe": "unsafe", "native": "safe"},
    "PACT": {"pe": "unsafe", "native": "safe"},
    "Requester-only": {"pe": "unsafe", "native": None},
    "ITES": {"pe": "safe", "native": None},
}


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

    def test_measured_verdicts_are_conclusive(self, bundle: dict[str, Any]) -> None:
        """A measured verdict must be conclusive, so UNKNOWN can never count.

        The safe-or-unsafe vocabulary is the only verdict class a counter may use:
        an inconclusive verdict must never appear in it, and every measured verdict
        -- this host's solver rows plus the preserved nuXmv measurement -- must
        belong to it.  Adding ``unknown`` to ``SAFE_VERDICTS`` would let an
        inconclusive result be counted as a safety result.

        ``pe_unknown`` counts the *measured* rows whose verdict is inconclusive, not
        the rows no backend answered; those are ``total_models - pe_measured``.  With
        the solver absent ``pe_measured`` and ``pe_unknown`` are both 0 while all six
        models report UNKNOWN.
        """
        conclusive = set(generator.SAFE_VERDICTS) | set(generator.UNSAFE_VERDICTS)
        assert INCONCLUSIVE_VERDICT not in conclusive, "an inconclusive verdict must never be counted as a result"
        assert set(SAFE_VERDICTS) | set(UNSAFE_VERDICTS) <= conclusive, "the counters must cover this test's verdict classes"
        pe_results = _pe_results(bundle)
        measured = _measured(pe_results) + _measured(_native_results(bundle))
        assert {row["verdict"] for row in measured} <= conclusive
        preserved = bundle["nuxmv_evidence"]["recorded"]
        if preserved is not None:
            retained_verdicts = {verdict for row in preserved["verdicts"].values() for verdict in row.values() if verdict}
            assert retained_verdicts <= conclusive, "a preserved measurement must be a conclusive verdict"
        summary = bundle["summary"]
        assert summary["pe_unknown"] == sum(1 for row in measured if row["verdict"] not in conclusive)
        if importlib.util.find_spec("z3") is None:
            assert summary["pe_measured"] == 0
            assert summary["pe_unknown"] == 0
            assert sum(1 for row in pe_results if row["verdict"] == INCONCLUSIVE_VERDICT) == summary["total_models"]

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

    def test_nuxmv_measurement_is_preserved_when_the_binary_is_absent(self, bundle: dict[str, Any]) -> None:
        """Keep the marker *and* the last nuXmv measurement with its provenance.

        nuXmv is not installed on this host, so every row records the unavailability
        marker and the bundle carries the measured verdicts under
        ``nuxmv_evidence.recorded``.  Dropping that record would delete the corpus's
        only nuXmv measurement.
        """
        evidence = bundle["nuxmv_evidence"]
        pe_results = _pe_results(bundle)
        if evidence["available_here"]:
            assert evidence["unavailable_reason"] is None
            assert all(row["nuxmv_error"] is None for row in pe_results)
            assert evidence["recorded"]["reproducible_here"] is True
            return
        assert evidence["unavailable_reason"] == NUXMV_UNAVAILABLE
        assert {row["nuxmv_error"] for row in pe_results} == {NUXMV_UNAVAILABLE}
        assert {row["nuxmv_verdict"] for row in pe_results} == {INCONCLUSIVE_VERDICT}
        assert bundle["formal_backends"]["nuxmv"] == {"available": False, "reason": "unavailable"}
        recorded = evidence["recorded"]
        assert recorded is not None, "the last nuXmv measurement must be preserved"
        assert recorded["verdicts"] == PRESERVED_NUXMV
        assert recorded["source_revision"] == "bbd59a2"
        assert recorded["origin"] == "nuXmv-capable host"
        assert recorded["reproducible_here"] is False
        assert "not reproducible" in recorded["note"]

    def test_a_later_regeneration_carries_the_preserved_measurement_forward(self, tmp_path: Path) -> None:
        """The provenance record outlives regeneration, its revision included.

        A bundle that already records provenance is copied verbatim, a bundle whose
        rows still carry measured nuXmv verdicts recovers them, and a missing bundle
        falls back to the historical measurement -- so regenerating on a host without
        the binary cannot drop the values.
        """
        assert generator._preserved_nuxmv(tmp_path)["verdicts"] == PRESERVED_NUXMV
        legacy = {
            "models": [
                {
                    "name": "Model-A",
                    "pe_property": {"nuxmv_verdict": "safe", "nuxmv_error": None},
                    "native_property": {"nuxmv_verdict": "unsafe", "nuxmv_error": None},
                },
                {
                    "name": "Model-B",
                    "pe_property": {"nuxmv_verdict": INCONCLUSIVE_VERDICT, "nuxmv_error": NUXMV_UNAVAILABLE},
                    "native_property": None,
                },
            ],
        }
        (tmp_path / "result.json").write_text(json.dumps(legacy), encoding="utf-8")
        recovered = generator._preserved_nuxmv(tmp_path)
        assert recovered["verdicts"] == {"Model-A": {"pe": "safe", "native": "unsafe"}}
        assert recovered["source_revision"] == "bbd59a2"
        assert recovered["reproducible_here"] is False
        carried = {
            "nuxmv_evidence": {
                "available_here": False,
                "unavailable_reason": NUXMV_UNAVAILABLE,
                "recorded": {
                    "origin": "a later host",
                    "source_revision": "cafebabe",
                    "reproducible_here": False,
                    "note": "kept",
                    "verdicts": {"Model-A": {"pe": "unsafe", "native": None}},
                },
            },
        }
        (tmp_path / "result.json").write_text(json.dumps(carried), encoding="utf-8")
        assert generator._preserved_nuxmv(tmp_path) == carried["nuxmv_evidence"]["recorded"]

    def test_a_host_with_nuxmv_overwrites_the_preserved_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Availability must replace the preserved record with a fresh measurement.

        The stub backend stands in for a nuXmv-capable host, the only host where the
        recorded values are reproducible.
        """

        class _AvailableNuXmv:
            """Stand-in backend for a host that has the nuXmv binary."""

            def verify(self, ir: Any) -> Any:
                return SimpleNamespace(verdict=FormalVerdict.SAFE, error=None)

        monkeypatch.setattr(generator, "_nuxmv", _AvailableNuXmv())
        available = generator.generate()
        evidence = available["nuxmv_evidence"]
        assert evidence["available_here"] is True
        assert evidence["unavailable_reason"] is None
        assert "nuxmv" in available["available_formal_backends"]
        assert {row["nuxmv_error"] for row in _pe_results(available)} == {None}
        recorded = evidence["recorded"]
        assert recorded["origin"] == "this host"
        assert recorded["source_revision"] is None, "a fresh measurement must not claim a retained revision"
        assert recorded["reproducible_here"] is True
        assert set(recorded["verdicts"]) == {model["name"] for model in available["models"]}
        assert recorded["verdicts"]["Dual-LLM"] == {"pe": "safe", "native": "safe"}
        assert recorded["verdicts"]["ITES"] == {"pe": "safe", "native": None}
        assert recorded["verdicts"] != PRESERVED_NUXMV, "a fresh measurement must overwrite the preserved values"

    def test_deterministic_regeneration(self, bundle: dict[str, Any]) -> None:
        regenerated = generate()
        assert json.dumps(bundle, sort_keys=True) == json.dumps(regenerated, sort_keys=True)
