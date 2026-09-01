"""Tests for refinement conformance: assume/guarantee and CEGAR."""

from __future__ import annotations

from conflux.verification.assume_guarantee import (
    build_contract,
    check_contract,
    verify_subplan_in_isolation,
)
from conflux.verification.counterexample_refinement import (
    cegar_verify,
    classify_counterexample,
    refine_ir,
)
from conflux.verification.delegation_ir import (
    DelegationIRMutation,
    build_delegation_ir,
)
from conflux.verification.reduction import reference_safety_check


def test_build_contract() -> None:
    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    contract = build_contract(ir)
    assert contract.ir_id == ir.id
    assert len(contract.soundness_assumptions) >= 2
    assert len(contract.sufficiency_assumptions) >= 2


def test_check_contract_with_empty_records() -> None:
    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    result = check_contract(ir, ())
    assert result.contract.ir_id == ir.id
    assert result.all_assumptions_hold


def test_verify_subplan_in_isolation() -> None:
    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    subplan_ir = verify_subplan_in_isolation(ir, ("attempt_use",))
    assert subplan_ir.id != ir.id
    assert "--subplan--" in subplan_ir.id


def test_classify_counterexample_safe() -> None:
    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    result = reference_safety_check(ir)
    classification = classify_counterexample(ir, result)
    assert not classification.is_real
    assert "no counterexample" in classification.reason


def test_classify_counterexample_unsafe() -> None:
    ir = build_delegation_ir(DelegationIRMutation.WIDENED_SCOPE)
    result = reference_safety_check(ir)
    classification = classify_counterexample(ir, result)
    assert classification.is_real
    assert "real violation" in classification.reason


def test_refine_ir_returns_same_for_real() -> None:
    ir = build_delegation_ir(DelegationIRMutation.WIDENED_SCOPE)
    result = reference_safety_check(ir)
    classification = classify_counterexample(ir, result)
    refined = refine_ir(ir, classification)
    assert refined.fingerprint == ir.fingerprint


def test_cegar_verify_safe_ir() -> None:
    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    result, classification = cegar_verify(ir)
    assert result.verdict.value == "safe"
    assert classification is None


def test_cegar_verify_unsafe_ir() -> None:
    ir = build_delegation_ir(DelegationIRMutation.REUSE)
    result, classification = cegar_verify(ir)
    assert result.verdict.value == "unsafe"
    assert classification is not None
    assert classification.is_real
