"""Cross-validate Z3 BMC vs reference interpreter on delegation IR variants.

For each delegation IR variant, runs both backends and compares verdicts.
Any disagreement is a bug in either the Z3 encoding or the reference
interpreter.

Usage:
    python scripts/generate_backend_cross_validation.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from conflux.verification.delegation_ir import (
    all_delegation_ir_variants,
)
from conflux.verification.reduction import reference_safety_check
from conflux.verification.z3_backend import verify_with_z3

OUTPUT_DIR = Path("research/output/runs/backend_cross_validation")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    agreements = 0
    disagreements = 0

    for variant in all_delegation_ir_variants():
        ir = variant.ir
        ref_result = reference_safety_check(ir)
        z3_result = verify_with_z3(ir)

        ref_verdict = ref_result.verdict.value
        z3_verdict = z3_result.verdict.value
        agree = ref_verdict == z3_verdict

        if agree:
            agreements += 1
        else:
            disagreements += 1

        results.append(
            {
                "mutation": variant.mutation.value,
                "ir_id": ir.id,
                "ir_fingerprint": ir.fingerprint,
                "reference_verdict": ref_verdict,
                "reference_states": ref_result.states,
                "z3_verdict": z3_verdict,
                "z3_error": z3_result.error,
                "verdicts_agree": agree,
            },
        )

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.verification.z3_backend + conflux.verification.reduction",
        "total_variants": len(results),
        "agreements": agreements,
        "disagreements": disagreements,
        "all_agree": disagreements == 0,
        "results": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Generated cross-backend validation evidence: {output_path}")
    print(f"  Variants: {len(results)}")
    print(f"  Agreements: {agreements}")
    print(f"  Disagreements: {disagreements}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
