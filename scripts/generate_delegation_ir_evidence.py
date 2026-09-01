"""Generate delegation IR verification evidence.

Produces JSON evidence for each delegation IR mutation variant, recording
the reference interpreter verdict, state count, and counterexample.

Usage:
    python scripts/generate_delegation_ir_evidence.py
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

OUTPUT_DIR = Path("research/output/runs/delegation_ir")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for variant in all_delegation_ir_variants():
        ir = variant.ir
        ref_result = reference_safety_check(ir)
        entry: dict[str, object] = {
            "mutation": variant.mutation.value,
            "ir_id": ir.id,
            "ir_fingerprint": ir.fingerprint,
            "bound": ir.bound,
            "reference_verdict": ref_result.verdict.value,
            "reference_states": ref_result.states,
            "reference_transitions": ref_result.transitions,
            "reference_duplicates": ref_result.duplicate_states,
            "invariants": [inv.id for inv in ir.invariants],
            "assumptions": list(ir.assumptions),
        }
        if ref_result.counterexample:
            entry["counterexample_length"] = len(ref_result.counterexample)
        results.append(entry)

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.verification.delegation_ir",
        "total_variants": len(results),
        "canonical_verdict": next(r["reference_verdict"] for r in results if r["mutation"] == "canonical"),
        "all_mutants_unsafe": all(r["reference_verdict"] == "unsafe" for r in results if r["mutation"] != "canonical"),
        "variants": results,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Generated delegation IR evidence: {output_path}")
    print(f"  Variants: {evidence['total_variants']}")
    print(f"  Canonical verdict: {evidence['canonical_verdict']}")
    print(f"  All mutants unsafe: {evidence['all_mutants_unsafe']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
