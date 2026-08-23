"""Tests for endorsement / trusted-transform verification models."""

from __future__ import annotations

from typing import Any

import pytest

from conflux.verification import (
    FormalVerdict,
    defective_endorsement_ir,
    run_endorsement_experiment,
    sound_endorsement_ir,
    verify_endorsement,
)

pytestmark = pytest.mark.security


class TestSoundEndorsement:
    """The sound endorsement model preserves PE and requires authorised endorser."""

    def test_sound_model_is_safe(self) -> None:
        ir = sound_endorsement_ir()
        result = verify_endorsement(ir)
        assert result.sound
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_no_counterexample_in_sound_model(self) -> None:
        ir = sound_endorsement_ir()
        result = verify_endorsement(ir)
        assert len(result.counterexample) == 0

    def test_sound_model_has_invariants(self) -> None:
        ir = sound_endorsement_ir()
        inv_ids = {inv.id for inv in ir.invariants}
        assert "no-pe-violation" in inv_ids
        assert "endorsement-requires-authorised-endorser" in inv_ids

    def test_sound_model_round_trips(self) -> None:
        ir = sound_endorsement_ir()
        restored = type(ir).from_dict(ir.to_dict())
        assert restored.fingerprint == ir.fingerprint


class TestDefectiveEndorsement:
    """The defective endorsement model allows attacker-controlled endorsement."""

    def test_defective_model_is_unsafe(self) -> None:
        ir = defective_endorsement_ir()
        result = verify_endorsement(ir)
        assert result.verdict == FormalVerdict.UNSAFE
        assert not result.sound

    def test_counterexample_exists(self) -> None:
        ir = defective_endorsement_ir()
        result = verify_endorsement(ir)
        assert len(result.counterexample) > 0

    def test_defective_model_round_trips(self) -> None:
        ir = defective_endorsement_ir()
        restored = type(ir).from_dict(ir.to_dict())
        assert restored.fingerprint == ir.fingerprint


class TestExperimentResult:
    """The full endorsement experiment is well-formed."""

    def test_experiment_returns_valid_dict(self) -> None:
        result = run_endorsement_experiment()
        assert result["schema_version"] == "1"
        assert "safe_model" in result
        assert "defective_model" in result
        assert "summary" in result

    def test_safe_is_sound(self) -> None:
        result: dict[str, Any] = run_endorsement_experiment()
        assert result["summary"]["safe_is_sound"] is True

    def test_defective_is_unsafe(self) -> None:
        result: dict[str, Any] = run_endorsement_experiment()
        assert result["summary"]["defective_is_unsafe"] is True

    def test_defective_has_counterexample(self) -> None:
        result: dict[str, Any] = run_endorsement_experiment()
        assert result["summary"]["defective_has_counterexample"] is True

    def test_experiment_has_fingerprint(self) -> None:
        result: dict[str, Any] = run_endorsement_experiment()
        assert "fingerprint" in result
        assert len(result["fingerprint"]) == 64
