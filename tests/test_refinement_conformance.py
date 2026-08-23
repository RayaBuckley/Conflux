"""Tests for implementation conformance and refinement relation (RQ9)."""

from __future__ import annotations

from typing import Any

import pytest

from conflux.verification import (
    RuntimeTransitionRecord,
    check_refinement,
    check_sound_abstraction,
    ites_reference_ir,
    run_refinement_experiment,
)

pytestmark = pytest.mark.security


class TestSoundAbstraction:
    """The IR is a sound overapproximation of the kernel."""

    def test_ites_reference_is_sound_abstraction(self) -> None:
        ir = ites_reference_ir()
        result = check_sound_abstraction(ir)
        assert result.sound
        assert result.ir_id == ir.id
        assert result.ir_state_count > 0

    def test_sound_abstraction_has_transitions(self) -> None:
        ir = ites_reference_ir()
        result = check_sound_abstraction(ir)
        assert result.ir_transition_count > 0
        assert result.reachable_transition_count > 0

    def test_sound_abstraction_round_trips(self) -> None:
        ir = ites_reference_ir()
        result = check_sound_abstraction(ir)
        d = result.to_dict()
        assert d["schema_version"] == "1"
        assert d["ir_id"] == ir.id
        assert d["sound"] is True


class TestRefinement:
    """Runtime kernel traces refine the verification IR."""

    def test_conforming_records_refine_ir(self) -> None:
        """Runtime records that match IR transitions should conform."""
        ir = ites_reference_ir()
        from conflux.verification import initial_state, successors

        start = initial_state(ir)
        records: list[RuntimeTransitionRecord] = []
        for rule_id, target in successors(ir, start):
            records.append(RuntimeTransitionRecord(start, rule_id, target))

        result = check_refinement(ir, tuple(records))
        assert result.refinement_holds
        assert result.conforms
        assert len(result.mismatches) == 0

    def test_non_conforming_record_fails_refinement(self) -> None:
        """A record with a wrong rule_id should not conform."""
        ir = ites_reference_ir()
        from conflux.verification import initial_state, successors

        start = initial_state(ir)
        valid = successors(ir, start)
        if valid:
            rule_id, target = valid[0]
            bogus_target = dict(target)
            bogus_target["bogus_var"] = 999
            record = RuntimeTransitionRecord(start, "nonexistent-rule", bogus_target)
            result = check_refinement(ir, (record,))
            assert not result.refinement_holds
            assert len(result.mismatches) > 0

    def test_empty_records_trivially_conform(self) -> None:
        ir = ites_reference_ir()
        result = check_refinement(ir, ())
        assert result.conforms
        assert result.refinement_holds
        assert result.record_count == 0

    def test_refinement_round_trips(self) -> None:
        ir = ites_reference_ir()
        result = check_refinement(ir, ())
        d = result.to_dict()
        assert d["schema_version"] == "1"
        assert d["refinement_holds"] is True


class TestExperiment:
    """The full refinement experiment is well-formed."""

    def test_experiment_returns_valid_dict(self) -> None:
        ir = ites_reference_ir()
        from conflux.verification import initial_state, successors

        start = initial_state(ir)
        records = tuple(RuntimeTransitionRecord(start, rule_id, target) for rule_id, target in successors(ir, start))
        result = run_refinement_experiment(ir, records)
        assert result["schema_version"] == "1"
        assert "sound_abstraction" in result
        assert "refinement" in result
        assert "summary" in result

    def test_experiment_ir_is_sound(self) -> None:
        ir = ites_reference_ir()
        result: dict[str, Any] = run_refinement_experiment(ir, ())
        assert result["summary"]["ir_is_sound_abstraction"] is True

    def test_experiment_kernel_refines_ir(self) -> None:
        ir = ites_reference_ir()
        from conflux.verification import initial_state, successors

        start = initial_state(ir)
        records = tuple(RuntimeTransitionRecord(start, rule_id, target) for rule_id, target in successors(ir, start))
        result: dict[str, Any] = run_refinement_experiment(ir, records)
        assert result["summary"]["kernel_refines_ir"] is True

    def test_experiment_has_fingerprint(self) -> None:
        ir = ites_reference_ir()
        result: dict[str, Any] = run_refinement_experiment(ir, ())
        assert "fingerprint" in result
        assert len(result["fingerprint"]) == 64
