"""Comparative defence verification: Dual-LLM, CaMeL, Progent, PACT, and ITES reference.

All external defence models are unvalidated candidate abstractions, not
implementation-conformance evidence for the published systems.  See
``docs/evidence/defence-model-fidelity.json`` for model-fidelity status.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from conflux.verification import (
    FormalVerdict,
    VerificationIR,
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

VALIDATION_STATUS = "unvalidated_external_abstraction"

ModelFactory = Callable[[], VerificationIR]

# Candidate abstractions that satisfy their own intended property Q but admit a PE
# counterexample.  The ``executes_action`` flag marks the model whose counterexample must
# also show that the unauthorised action ran (the Dual-LLM planner consumes attacker data).
UNSAFE_PE_MODELS: dict[str, tuple[ModelFactory, bool]] = {
    "dual_llm": (dual_llm_baseline_ir, True),
    "ites_requester_only": (ites_defective_requester_only_ir, False),
    "camel": (camel_ir, False),
    "progent": (progent_ir, False),
    "pact": (pact_ir, False),
}

# Candidate abstractions that satisfy their own intended property Q.
NATIVE_PROPERTY_MODELS: dict[str, ModelFactory] = {
    "dual_llm": dual_llm_native_property_ir,
    "camel": camel_native_property_ir,
    "progent": progent_native_property_ir,
    "pact": pact_native_property_ir,
}


class TestUnsafePEModels:
    """Unvalidated candidate abstractions that admit a PE counterexample."""

    @pytest.mark.parametrize(
        "factory",
        [factory for factory, _executes_action in UNSAFE_PE_MODELS.values()],
        ids=list(UNSAFE_PE_MODELS),
    )
    def test_pe_property_is_unsafe(self, factory: ModelFactory) -> None:
        """The model admits a PE violation when attacker data reaches the effect."""
        result = reference_safety_check(factory())
        assert result.verdict == FormalVerdict.UNSAFE

    @pytest.mark.parametrize(
        ("factory", "executes_action"),
        list(UNSAFE_PE_MODELS.values()),
        ids=list(UNSAFE_PE_MODELS),
    )
    def test_counterexample_shows_pe_violation(self, factory: ModelFactory, executes_action: bool) -> None:
        """The counterexample records the PE violation, and the executed action for Dual-LLM."""
        result = reference_safety_check(factory())
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("pe_violation") is True
        if executes_action:
            assert final_state.get("action_executed") is True

    def test_dual_llm_counterexample_shows_the_action_executed(self) -> None:
        """Dual-LLM: the counterexample must show the unauthorised action ran.

        Asserted directly, not through the ``executes_action`` flag, so that changing
        the table cannot silently stop this guarantee from being checked.
        """
        result = reference_safety_check(dual_llm_baseline_ir())
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        assert final_state.get("pe_violation") is True
        assert final_state.get("action_executed") is True

    def test_dual_llm_counterexample_exists(self) -> None:
        """The Dual-LLM model has a non-empty counterexample."""
        result = reference_safety_check(dual_llm_baseline_ir())
        assert len(result.counterexample) > 0


class TestNativePropertyModels:
    """Candidate abstractions that satisfy their own intended property Q."""

    @pytest.mark.parametrize(
        "factory",
        list(NATIVE_PROPERTY_MODELS.values()),
        ids=list(NATIVE_PROPERTY_MODELS),
    )
    def test_native_property_is_safe(self, factory: ModelFactory) -> None:
        """Satisfying the model's own guarantee Q does not imply satisfying PE."""
        result = reference_safety_check(factory())
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_dual_llm_processor_never_executes(self) -> None:
        """Q for Dual-LLM: the quarantined processor never directly executes effects."""
        result = reference_safety_check(dual_llm_native_property_ir())
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


class TestITESWithReadCheck:
    """ITES with read-check ablation: PE-safe but stricter than plain ITES."""

    def test_read_check_model_is_safe(self) -> None:
        ir = ites_with_read_check_ir()
        result = reference_safety_check(ir)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_read_check_model_uses_set_sorts(self) -> None:
        ir = ites_with_read_check_ir()
        from conflux.verification import Sort

        set_vars = [v for v in ir.variables if v.sort == Sort.SET]
        assert len(set_vars) >= 2


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
