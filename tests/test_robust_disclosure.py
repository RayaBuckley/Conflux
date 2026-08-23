"""Tests for robust disclosure verification (Zdancewic & Myers connection)."""

from __future__ import annotations

import pytest

from conflux.verification import (
    FormalVerdict,
    defective_disclosure_ir,
    robust_disclosure_ir,
    run_robust_disclosure_experiment,
    verify_robust_disclosure,
)

pytestmark = pytest.mark.security


class TestRobustDisclosureModel:
    """The robust disclosure model blocks attacker-controlled disclosure."""

    def test_robust_model_is_safe(self) -> None:
        ir = robust_disclosure_ir()
        result = verify_robust_disclosure(ir)
        assert result.robust
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_no_counterexample_in_robust_model(self) -> None:
        ir = robust_disclosure_ir()
        result = verify_robust_disclosure(ir)
        assert len(result.counterexample) == 0

    def test_robust_model_has_invariants(self) -> None:
        ir = robust_disclosure_ir()
        inv_ids = {inv.id for inv in ir.invariants}
        assert "no-unauthorised-disclosure" in inv_ids

    def test_robust_model_round_trips(self) -> None:
        ir = robust_disclosure_ir()
        restored = type(ir).from_dict(ir.to_dict())
        assert restored.fingerprint == ir.fingerprint


class TestDefectiveDisclosureModel:
    """The defective disclosure model allows attacker-controlled disclosure."""

    def test_defective_model_is_unsafe(self) -> None:
        ir = defective_disclosure_ir()
        result = verify_robust_disclosure(ir)
        assert result.verdict == FormalVerdict.UNSAFE
        assert not result.robust

    def test_counterexample_exists(self) -> None:
        ir = defective_disclosure_ir()
        result = verify_robust_disclosure(ir)
        assert len(result.counterexample) > 0

    def test_counterexample_shows_unauthorised_disclosure(self) -> None:
        ir = defective_disclosure_ir()
        result = verify_robust_disclosure(ir)
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("unauthorised_disclosure") is True
        assert final_state.get("disclosed") is True

    def test_defective_model_round_trips(self) -> None:
        ir = defective_disclosure_ir()
        restored = type(ir).from_dict(ir.to_dict())
        assert restored.fingerprint == ir.fingerprint


class TestExperimentResult:
    """The full robust-disclosure experiment is well-formed."""

    def test_experiment_returns_valid_dict(self) -> None:
        result = run_robust_disclosure_experiment()
        assert result["schema_version"] == "1"
        assert "robust_model" in result
        assert "defective_model" in result
        assert "summary" in result

    def test_robust_is_safe(self) -> None:
        result = run_robust_disclosure_experiment()
        assert result["summary"]["robust_is_safe"] is True

    def test_defective_is_unsafe(self) -> None:
        result = run_robust_disclosure_experiment()
        assert result["summary"]["defective_is_unsafe"] is True

    def test_defective_has_counterexample(self) -> None:
        result = run_robust_disclosure_experiment()
        assert result["summary"]["defective_has_counterexample"] is True

    def test_experiment_has_fingerprint(self) -> None:
        result = run_robust_disclosure_experiment()
        assert "fingerprint" in result
        assert len(result["fingerprint"]) == 64
