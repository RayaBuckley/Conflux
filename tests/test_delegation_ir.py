"""Tests for delegation safety verification IR encoding."""

from __future__ import annotations

import hashlib

import pytest

from conflux.verification.delegation_ir import (
    DELEGATION_IR_BOUND,
    DelegationIRMutation,
    all_delegation_ir_variants,
    build_delegation_ir,
)
from conflux.verification.interpreter import evaluate, initial_state, successors
from conflux.verification.ir import VerificationIR
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


def test_multi_grant_ir_builds() -> None:
    from conflux.verification.delegation_ir import build_multi_grant_ir

    ir = build_multi_grant_ir(2)
    assert "multi-grant-2" in ir.id
    # 2 grants x 4 flags + the symbolic grant_count + step
    assert len(ir.variables) == 10
    # 2 issue rules + 2 grants x (consume, revoke, expire)
    assert len(ir.transitions) == 8
    # 2 grants x (no_revoked_consume, no_expired_consume, scope_narrowed, respects_count)
    assert len(ir.invariants) == 8


def test_multi_grant_ir_is_safe() -> None:
    from conflux.verification.delegation_ir import build_multi_grant_ir

    ir = build_multi_grant_ir(2)
    result = reference_safety_check(ir)
    assert result.verdict.value == "safe"
    assert result.states > 1


def test_multi_grant_ir_scales_exponentially() -> None:
    from conflux.verification.delegation_ir import build_multi_grant_ir

    ir2 = build_multi_grant_ir(2)
    ir3 = build_multi_grant_ir(3)
    r2 = reference_safety_check(ir2)
    r3 = reference_safety_check(ir3)
    assert r3.states > r2.states


def test_the_grant_count_is_symbolic_over_the_run() -> None:
    from conflux.verification.delegation_ir import build_multi_grant_ir
    from conflux.verification.sensitivity import reachable_states

    for n_grants in (2, 3):
        ir = build_multi_grant_ir(n_grants)
        counts = sorted({state["grant_count"] for state in reachable_states(ir)})
        assert counts == list(range(n_grants + 1)), counts


def _grant_projection(ir: VerificationIR, count: int) -> set[tuple[object, ...]]:
    from conflux.verification.sensitivity import reachable_states

    keys = tuple(
        f"g{i}_{field}" for i in range(count) for field in ("consumed", "revoked", "expired", "scope_match")
    )
    return {tuple(state[key] for key in keys) for state in reachable_states(ir)}


def test_the_wide_encoding_reproduces_each_narrow_model() -> None:
    """One encoding shape covers every count.

    The first ``count`` grants of the 4-grant model reach exactly the configurations of the
    ``count``-grant model, so the family no longer needs one hand-built IR per ``n``.
    """
    from conflux.verification.delegation_ir import build_multi_grant_ir

    for count in (1, 2, 3):
        wide = _grant_projection(build_multi_grant_ir(4), count)
        narrow = _grant_projection(build_multi_grant_ir(count), count)
        assert wide == narrow, count


def test_the_count_invariant_is_protected_by_a_live_guard() -> None:
    """The symbolic count is load-bearing, not decorative.

    With a fixed count the same sentence is either trivially true or true by construction.
    With the count symbolic the index guard is live somewhere in the run, and a mutant that
    drops it refutes the invariant. Measured, so the claim cannot regress to a vacuous one.
    """
    from conflux.verification.delegation_ir import build_multi_grant_ir
    from conflux.verification.sensitivity import CLASS_CHECKED, classify_ir

    rows = {row.invariant_id: row for row in classify_ir(build_multi_grant_ir(2))}
    for i in (0, 1):
        row = rows[f"grant_{i}_respects_count"]
        assert row.exercise_class == CLASS_CHECKED, row.exercise_class
        assert any(falsifier.guard_satisfiable_at_reachable_state for falsifier in row.falsifiers), i


def test_the_eleven_variants_cover_ten_distinct_bodies() -> None:
    """Eleven variants, ten behaviours: redelegation and redelegation_chain share one body.

    The cross-validation bundle and the paper both count eleven variants, and a reader
    who reads eleven as eleven distinct behaviours over-reads the evidence. This test
    keeps the two numbers apart. If a later change makes the pair distinct, update this
    test, the note in VERIFICATION.md section 29 and the sentence in the manuscript
    together.
    """
    bodies: dict[str, list[str]] = {}
    for result in all_delegation_ir_variants():
        body = repr((result.ir.variables, result.ir.transitions, result.ir.invariants))
        bodies.setdefault(hashlib.sha256(body.encode()).hexdigest(), []).append(result.mutation.value)
    shared = sorted(names for names in bodies.values() if len(names) > 1)
    assert len(bodies) == 10
    assert shared == [["redelegation", "redelegation_chain"]]


def test_composition_reproduces_every_named_mutation() -> None:
    """build_combined_delegation_ir({m}) must build exactly what build_delegation_ir(m) builds.

    The combination sweep reads the defect space as composable, so the single-mutation readings have to
    stay the same objects they always were: a drift here would silently change what the retained bundles
    mean without touching them.
    """
    from conflux.verification.delegation_ir import build_combined_delegation_ir

    def body(ir: VerificationIR) -> tuple[object, ...]:
        return (ir.variables, ir.transitions, ir.invariants, ir.bound)

    canonical = build_combined_delegation_ir(frozenset())
    assert body(canonical) == body(build_delegation_ir(DelegationIRMutation.CANONICAL))
    for mutation in DelegationIRMutation:
        if mutation is DelegationIRMutation.CANONICAL:
            continue
        assert body(build_combined_delegation_ir({mutation})) == body(build_delegation_ir(mutation))


def test_the_defect_space_has_nine_entries() -> None:
    """The composable defects are nine: the tenth mutation duplicates redelegation's body.

    See test_the_eleven_variants_cover_ten_distinct_bodies: counting the duplicate as its own defect
    would put a body that is already in the population into a combination sweep twice.
    """
    from conflux.verification.delegation_ir import DELEGATION_IR_DEFECTS

    assert len(DELEGATION_IR_DEFECTS) == 9
    assert DelegationIRMutation.REDELEGATION in DELEGATION_IR_DEFECTS
    assert DelegationIRMutation.REDELEGATION_CHAIN not in DELEGATION_IR_DEFECTS
    assert DelegationIRMutation.CANONICAL not in DELEGATION_IR_DEFECTS


def test_two_defects_compose_and_the_result_is_unsafe() -> None:
    """A combination keeps both effects, and any defect at all leaves the variant refutable."""
    from conflux.verification.delegation_ir import build_combined_delegation_ir

    combined = build_combined_delegation_ir(
        {DelegationIRMutation.REUSE, DelegationIRMutation.STALE_CONTEXT},
    )
    consume = next(rule for rule in combined.transitions if rule.id == "attempt_use")
    assignments = {assignment.variable: assignment.expression.value for assignment in consume.assignments}
    assert assignments["use_count"] == 2
    assert assignments["context_verified"] is False
    assert reference_safety_check(combined).verdict.value == "unsafe"
    assert reference_safety_check(build_combined_delegation_ir(frozenset())).verdict.value == "safe"
