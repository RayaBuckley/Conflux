"""Comparative defence verification: Dual-LLM, CaMeL, Progent, PACT, and ITES reference."""

from __future__ import annotations

import pytest

from conflux.verification import (
    FormalVerdict,
    camel_ir,
    camel_native_property_ir,
    dual_llm_baseline_ir,
    dual_llm_native_property_ir,
    ites_defective_requester_only_ir,
    ites_reference_ir,
    ites_with_read_check_ir,
    pact_ir,
    pact_native_property_ir,
    progent_ir,
    progent_native_property_ir,
    reference_safety_check,
)

pytestmark = pytest.mark.security


class TestDualLLMBaselinePE:
    """Dual-LLM satisfies its own property Q but violates Conflux PE."""

    def test_pe_property_is_unsafe(self) -> None:
        """The Dual-LLM model admits a PE violation.

        The planner consumes attacker data and executes an action.
        Since the attacker is not authorised, PE is violated.
        """
        ir = dual_llm_baseline_ir()
        result = reference_safety_check(ir)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_counterexample_exists(self) -> None:
        ir = dual_llm_baseline_ir()
        result = reference_safety_check(ir)
        assert len(result.counterexample) > 0

    def test_counterexample_shows_pe_violation(self) -> None:
        ir = dual_llm_baseline_ir()
        result = reference_safety_check(ir)
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("pe_violation") is True
        assert final_state.get("action_executed") is True


class TestDualLLMNativeProperty:
    """The Dual-LLM model satisfies its own intended property Q."""

    def test_native_property_is_safe(self) -> None:
        """Q: the quarantined processor never directly executes effects.

        This is the Dual-LLM's own guarantee.  It holds, demonstrating that
        satisfying Q does not imply satisfying PE.
        """
        ir = dual_llm_native_property_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_processor_never_executes(self) -> None:
        ir = dual_llm_native_property_ir()
        result = reference_safety_check(ir)
        # No counterexample should exist
        assert len(result.counterexample) == 0


class TestITESReferencePE:
    """ITES reference model preserves the PE invariant."""

    def test_pe_property_is_safe(self) -> None:
        """ITES blocks execution when an influencing principal lacks authorisation.

        The PE invariant should hold: no action is executed when the attacker
        is in the context but not authorised.
        """
        ir = ites_reference_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_blocked_not_executed(self) -> None:
        ir = ites_reference_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)


class TestDefectiveRequesterOnly:
    """REQUESTER_ONLY negative control: checks only the requester."""

    def test_pe_property_is_unsafe(self) -> None:
        """The requester-only check violates PE because it ignores the
        attacker's influence on the planner."""
        ir = ites_defective_requester_only_ir()
        result = reference_safety_check(ir)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_counterexample_shows_pe_violation(self) -> None:
        ir = ites_defective_requester_only_ir()
        result = reference_safety_check(ir)
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("pe_violation") is True


class TestCaMeLBaselinePE:
    """CaMeL satisfies its own property Q but violates Conflux PE."""

    def test_pe_property_is_unsafe(self) -> None:
        ir = camel_ir()
        result = reference_safety_check(ir)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_counterexample_shows_pe_violation(self) -> None:
        ir = camel_ir()
        result = reference_safety_check(ir)
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("pe_violation") is True


class TestCaMeLNativeProperty:
    """CaMeL satisfies its own property Q: processor never executes."""

    def test_native_property_is_safe(self) -> None:
        ir = camel_native_property_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)


class TestProgentBaselinePE:
    """Progent satisfies its own property Q but violates Conflux PE."""

    def test_pe_property_is_unsafe(self) -> None:
        ir = progent_ir()
        result = reference_safety_check(ir)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_counterexample_shows_pe_violation(self) -> None:
        ir = progent_ir()
        result = reference_safety_check(ir)
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("pe_violation") is True


class TestProgentNativeProperty:
    """Progent satisfies its own property Q: all calls satisfy policy."""

    def test_native_property_is_safe(self) -> None:
        ir = progent_native_property_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)


class TestPACTBaselinePE:
    """PACT satisfies its own property Q but violates Conflux PE."""

    def test_pe_property_is_unsafe(self) -> None:
        ir = pact_ir()
        result = reference_safety_check(ir)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_counterexample_shows_pe_violation(self) -> None:
        ir = pact_ir()
        result = reference_safety_check(ir)
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("pe_violation") is True


class TestPACTNativeProperty:
    """PACT satisfies its own property Q: argument provenance preserved."""

    def test_native_property_is_safe(self) -> None:
        ir = pact_native_property_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)


class TestITESWithReadCheck:
    """ITES with read-check ablation: PE-safe but stricter than plain ITES."""

    def test_read_check_model_is_safe(self) -> None:
        ir = ites_with_read_check_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_read_check_model_round_trips(self) -> None:
        ir = ites_with_read_check_ir()
        restored = type(ir).from_dict(ir.to_dict())
        assert restored.fingerprint == ir.fingerprint

    def test_read_check_model_uses_set_sorts(self) -> None:
        ir = ites_with_read_check_ir()
        from conflux.verification import Sort

        set_vars = [v for v in ir.variables if v.sort == Sort.SET]
        assert len(set_vars) >= 2

    def test_all_models_round_trip_includes_read_check(self) -> None:
        """The read-check model is included in the round-trip test."""
        ir = ites_with_read_check_ir()
        restored = type(ir).from_dict(ir.to_dict())
        assert restored.fingerprint == ir.fingerprint


class TestDefenceModelStructure:
    """Structural validation of the defence IR models."""

    def test_dual_llm_has_pe_invariant(self) -> None:
        ir = dual_llm_baseline_ir()
        inv_ids = {inv.id for inv in ir.invariants}
        assert "no-pe-violation" in inv_ids

    def test_dual_llm_native_has_q_invariant(self) -> None:
        ir = dual_llm_native_property_ir()
        inv_ids = {inv.id for inv in ir.invariants}
        assert "processor-never-executes" in inv_ids

    def test_ites_reference_has_pe_invariant(self) -> None:
        ir = ites_reference_ir()
        inv_ids = {inv.id for inv in ir.invariants}
        assert "no-pe-violation" in inv_ids

    def test_ites_reference_has_blocked_not_executed(self) -> None:
        ir = ites_reference_ir()
        inv_ids = {inv.id for inv in ir.invariants}
        assert "blocked-not-executed" in inv_ids

    def test_all_models_round_trip(self) -> None:
        """All defence models serialise and deserialise correctly."""
        for factory in (
            dual_llm_baseline_ir,
            dual_llm_native_property_ir,
            ites_reference_ir,
            ites_defective_requester_only_ir,
            ites_with_read_check_ir,
            camel_ir,
            camel_native_property_ir,
            progent_ir,
            progent_native_property_ir,
            pact_ir,
            pact_native_property_ir,
        ):
            ir = factory()
            restored = type(ir).from_dict(ir.to_dict())
            assert restored.fingerprint == ir.fingerprint
