"""Tests for delegation safety verification IR encoding."""

from __future__ import annotations

import pytest

from conflux.verification.delegation_ir import (
    DELEGATION_IR_BOUND,
    DelegationIRMutation,
    all_delegation_ir_variants,
    build_delegation_ir,
)
from conflux.verification.interpreter import evaluate, initial_state, successors
from conflux.verification.reduction import reference_safety_check


@pytest.mark.parametrize(
    "mutation",
    list(DelegationIRMutation),
)
def test_ir_builds_for_every_mutation(mutation: DelegationIRMutation) -> None:
    ir = build_delegation_ir(mutation)
    assert ir.id == f"delegation-ir:{mutation.value}"
    assert len(ir.variables) == 11
    assert len(ir.transitions) == 3
    assert len(ir.invariants) == 11
    assert ir.bound == DELEGATION_IR_BOUND


def test_canonical_delegation_ir_is_safe() -> None:
    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    result = reference_safety_check(ir)
    assert result.verdict.value == "safe"
    assert result.states > 0


@pytest.mark.parametrize(
    "mutation",
    [m for m in DelegationIRMutation if m != DelegationIRMutation.CANONICAL],
)
def test_every_mutant_is_unsafe(mutation: DelegationIRMutation) -> None:
    ir = build_delegation_ir(mutation)
    result = reference_safety_check(ir)
    assert result.verdict.value == "unsafe", f"{mutation.value} should be unsafe"


def test_all_variants_return_eleven_results() -> None:
    variants = all_delegation_ir_variants()
    assert len(variants) == 11


def test_ir_serialization_round_trip() -> None:
    from conflux.verification.ir import VerificationIR

    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    d = ir.to_dict()
    assert d["id"] == "delegation-ir:canonical"
    assert d["bound"] == DELEGATION_IR_BOUND
    ir2 = VerificationIR.from_dict(d)
    assert ir2.fingerprint == ir.fingerprint


def test_toctou_invariant_uses_implies() -> None:
    from conflux.verification.ir import ExpressionKind

    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    toctou = next(inv for inv in ir.invariants if inv.id == "toctou_drift_detection")
    assert toctou.expression.kind == ExpressionKind.IMPLIES


def test_canonical_initial_state_satisfies_all_invariants() -> None:
    ir = build_delegation_ir(DelegationIRMutation.CANONICAL)
    state = initial_state(ir)
    for inv in ir.invariants:
        assert evaluate(inv.expression, state) is True, f"{inv.id} fails at initial state"


def test_stale_context_mutation_sets_context_verified_false() -> None:
    ir = build_delegation_ir(DelegationIRMutation.STALE_CONTEXT)
    state = initial_state(ir)
    succs = successors(ir, state)
    use_succ = next(s for rid, s in succs if rid == "attempt_use")
    assert use_succ["context_verified"] is False
    assert use_succ["context_preserved"] is False


def test_reuse_mutation_sets_use_count_to_two() -> None:
    ir = build_delegation_ir(DelegationIRMutation.REUSE)
    state = initial_state(ir)
    succs = successors(ir, state)
    use_succ = next(s for rid, s in succs if rid == "attempt_use")
    assert use_succ["use_count"] == 2
