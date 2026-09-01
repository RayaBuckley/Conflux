"""Generate refinement conformance evidence.

Produces JSON evidence for assume/guarantee contracts, compositional
verification, and CEGAR loops on delegation IR variants.

Usage:
    python scripts/generate_refinement_evidence.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from conflux.verification.assume_guarantee import build_contract, check_contract
from conflux.verification.counterexample_refinement import cegar_verify, classify_counterexample
from conflux.verification.delegation_ir import DelegationIRMutation, build_delegation_ir
from conflux.verification.reduction import reference_safety_check

OUTPUT_DIR = Path("research/output/runs/refinement")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for mutation in DelegationIRMutation:
        ir = build_delegation_ir(mutation)
        contract = build_contract(ir)
        contract_result = check_contract(ir, ())
        ref_result = reference_safety_check(ir)
        classification = classify_counterexample(ir, ref_result)
        cegar_result, cegar_class = cegar_verify(ir)

        entry: dict[str, object] = {
            "mutation": mutation.value,
            "ir_id": ir.id,
            "ir_fingerprint": ir.fingerprint,
            "contract": contract.to_dict(),
            "contract_all_hold": contract_result.all_assumptions_hold,
            "reference_verdict": ref_result.verdict.value,
            "counterexample_is_real": classification.is_real,
            "counterexample_reason": classification.reason,
            "cegar_verdict": cegar_result.verdict.value,
            "cegar_classification": cegar_class.to_dict() if cegar_class else None,
        }
        results.append(entry)

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.verification.assume_guarantee + counterexample_refinement",
        "total_variants": len(results),
        "all_contracts_hold": all(r["contract_all_hold"] for r in results),
        "results": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Generated refinement evidence: {output_path}")
    print(f"  Variants: {len(results)}")
    print(f"  All contracts hold: {evidence['all_contracts_hold']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
