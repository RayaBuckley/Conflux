"""Tests for COI scaling evidence generation."""

from __future__ import annotations

import importlib.util
import json
from typing import Any

import pytest

from scripts.generate_coi_scaling import NOISE_COUNTS, generate

pytestmark = pytest.mark.reproducibility

UNAVAILABLE_Z3 = "optional_dependency_unavailable:z3"
SAFE_VERDICTS = ("safe", "bounded_safe")
UNSAFE_VERDICTS = ("unsafe",)


@pytest.fixture(scope="module")
def bundle() -> dict[str, Any]:
    """Build the scaling bundle once; a single generation re-runs every fixture."""
    return generate()


def _measured_z3_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Rows where the optional solver answered both the original and reduced query."""
    return [
        row
        for row in bundle["fixtures"]
        if row["z3"]["original_error"] is None and row["z3"]["reduced_error"] is None
    ]


class TestCoiScalingBundle:
    """Test the full scaling evidence bundle generation."""

    def test_bundle_has_correct_schema(self, bundle: dict[str, Any]) -> None:
        assert bundle["schema_version"] == "1"
        assert bundle["id"] == "coi-scaling-v1"

    def test_bundle_covers_every_noise_count(self, bundle: dict[str, Any]) -> None:
        assert len(bundle["fixtures"]) == 2 * len(NOISE_COUNTS)
        assert bundle["summary"]["total_fixtures"] == len(bundle["fixtures"])
        assert bundle["noise_counts"] == list(NOISE_COUNTS)

    def test_every_row_records_z3_provenance(self, bundle: dict[str, Any]) -> None:
        """Every row records the solver verdicts *and* the solver errors."""
        assert bundle["fixtures"]
        for row in bundle["fixtures"]:
            assert set(row["z3"]) == {
                "original_verdict",
                "reduced_verdict",
                "original_error",
                "reduced_error",
            }, row["fixture_id"]

    def test_z3_all_agree_covers_measured_rows_only(self, bundle: dict[str, Any]) -> None:
        """Assert the z3 agreement flag, or the documented unavailable state.

        Without the optional solver every row records
        ``optional_dependency_unavailable:z3``, so the ``all(...)`` behind the flag
        is vacuously true.  Asserting the flag alone would report a guarantee
        nobody measured, which the optional-evidence rule forbids; assert the
        documented marker, the measured count and the null flag instead, and
        require every fixture to be measured before trusting the flag.
        """
        measured = _measured_z3_rows(bundle)
        assert bundle["fixtures"], "the bundle must contain fixtures"
        assert bundle["summary"]["z3_measured"] == len(measured)
        if importlib.util.find_spec("z3") is None:
            assert not measured, "no row may report a z3 measurement while the solver is absent"
            assert {row["z3"]["original_error"] for row in bundle["fixtures"]} == {UNAVAILABLE_Z3}
            assert {row["z3"]["reduced_error"] for row in bundle["fixtures"]} == {UNAVAILABLE_Z3}
            assert bundle["summary"]["z3_measured"] == 0
            assert bundle["summary"]["z3_all_agree"] is None, "an unmeasured agreement flag must not claim agreement"
            assert bundle["formal_backends"]["z3"] == {"available": False, "reason": "unavailable"}
            assert bundle["available_formal_backends"] == []
            return
        assert len(measured) == len(bundle["fixtures"]), "every fixture must be measured before the flag is trusted"
        assert bundle["summary"]["z3_all_agree"] is True
        assert bundle["formal_backends"]["z3"] == {"available": True, "reason": None}
        assert bundle["available_formal_backends"] == ["z3"]

    def test_reference_verdicts_agree_on_every_fixture(self, bundle: dict[str, Any]) -> None:
        """The reference interpreter is not optional, so every row must be measured."""
        assert bundle["fixtures"]
        for row in bundle["fixtures"]:
            assert row["reference"]["original_verdict"] in SAFE_VERDICTS + UNSAFE_VERDICTS, row["fixture_id"]
            assert row["reference"]["equivalent"] is True, row["fixture_id"]
        assert bundle["summary"]["all_equivalent"] is True

    def test_deterministic_regeneration(self, bundle: dict[str, Any]) -> None:
        regenerated = generate()
        assert json.dumps(bundle, sort_keys=True) == json.dumps(regenerated, sort_keys=True)
