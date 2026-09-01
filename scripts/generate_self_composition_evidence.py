"""Generate self-composition optimization evidence.

Compares original product IR vs symmetry-reduced product IR,
recording variable counts, invariant counts, and reference verdicts.

Usage:
    python scripts/generate_self_composition_evidence.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from conflux.verification.ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)
from conflux.verification.reduction import reference_safety_check
from conflux.verification.self_composition import SecretPartition, construct_product_ir
from conflux.verification.symmetry_reduction import add_symmetry_breaking_constraints

OUTPUT_DIR = Path("research/output/runs/self_composition")


def _build_base_ir() -> VerificationIR:
    return VerificationIR(
        id="sc-evidence-base",
        variables=(
            StateVariable("secret", Sort.BOOLEAN, False),
            StateVariable("output", Sort.BOOLEAN, False),
            StateVariable("step", Sort.INTEGER, 0, 0, 4),
        ),
        transitions=(
            TransitionRule(
                "step",
                Expression.operator(ExpressionKind.LESS_EQUAL, Expression.variable("step"), Expression.constant(3)),
                (
                    Assignment("step", Expression.operator(ExpressionKind.ADD, Expression.variable("step"), Expression.constant(1))),
                    Assignment("output", Expression.variable("secret")),
                ),
            ),
        ),
        invariants=(SafetyInvariant("no-leak", Expression.operator(ExpressionKind.NOT, Expression.variable("output")), "no leak"),),
        bound=4,
    )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    base = _build_base_ir()
    partition = SecretPartition(
        observable_variable_ids=frozenset({"output"}),
        secret_variable_ids=frozenset({"secret"}),
        observer_description="unauthorised observer for evidence",
    )

    product = construct_product_ir(base, partition)
    sym_reduced = add_symmetry_breaking_constraints(product, partition)

    product_result = reference_safety_check(product)
    sym_result = reference_safety_check(sym_reduced)

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.verification.symmetry_reduction",
        "base_ir_id": base.id,
        "base_ir_fingerprint": base.fingerprint,
        "product_ir_id": product.id,
        "product_ir_fingerprint": product.fingerprint,
        "product_variables": len(product.variables),
        "product_invariants": len(product.invariants),
        "product_verdict": product_result.verdict.value,
        "product_states": product_result.states,
        "symmetry_reduced_ir_id": sym_reduced.id,
        "symmetry_reduced_ir_fingerprint": sym_reduced.fingerprint,
        "symmetry_reduced_variables": len(sym_reduced.variables),
        "symmetry_reduced_invariants": len(sym_reduced.invariants),
        "symmetry_reduced_verdict": sym_result.verdict.value,
        "symmetry_reduced_states": sym_result.states,
        "verdicts_agree": product_result.verdict == sym_result.verdict,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Generated self-composition evidence: {output_path}")
    print(f"  Product: {len(product.variables)} vars, {len(product.invariants)} invs, {product_result.verdict.value}")
    print(f"  Symmetry-reduced: {len(sym_reduced.variables)} vars, {len(sym_reduced.invariants)} invs, {sym_result.verdict.value}")
    print(f"  Verdicts agree: {evidence['verdicts_agree']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
