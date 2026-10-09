"""Measure three-way verdict agreement on the delegation IR family.

The reference interpreter, the Z3 bounded model checker and the optional nuXmv IC3 backend decide
the same delegation IR variants: the canonical one plus ten mutations that each break a different
guarantee. Agreement is compared by verdict class, so Z3's ``bounded_safe`` agrees with the
reference interpreter's ``safe``, and the raw verdict strings stay in the artefact.

A backend that did not run is recorded ``unavailable`` and never counted as agreeing. The run also
fails when no variant is refuted, because a battery that produces no violation proves nothing.

Usage::

    python scripts/generate_three_way_agreement.py
    python scripts/generate_three_way_agreement.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from conflux.verification.delegation_ir import all_delegation_ir_variants
from conflux.verification.ir import VerificationIR
from conflux.verification.nuxmv_backend import NuXmvBackend
from conflux.verification.reduction import reference_safety_check
from conflux.verification.results import FormalVerdict
from conflux.verification.z3_backend import verify_with_z3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "three-way-agreement-v1"

# Volatile fields are excluded from a --check comparison.
VOLATILE = ("generated_at",)

SAFE_FAMILY = frozenset({"safe", "bounded_safe"})
"""Verdicts that mean "no violation found within the stated bounds".

The reference interpreter and nuXmv report ``safe`` while the bounded model checker reports
``bounded_safe``: same class, different scope of guarantee. ``scripts/generate_z3_agreement.py``
carries the same pair for the cone-of-influence battery, and a test pins the two copies equal, so
there is one meaning and no drift.
"""


def verdict_class(verdict: str) -> str:
    """Map a verdict onto its class for cross-backend comparison."""
    return "safe" if verdict in SAFE_FAMILY else verdict


def _measured(verdict: FormalVerdict) -> bool:
    return verdict is not FormalVerdict.UNKNOWN


def _z3_row(ir: VerificationIR) -> dict[str, Any]:
    result = verify_with_z3(ir)
    counterexample = result.counterexample or ()
    return {
        "verdict": result.verdict.value,
        "backend": result.backend,
        "solver_hash": result.solver_hash,
        "bound": result.bound,
        "measured": _measured(result.verdict),
        "counterexample": bool(counterexample),
        "counterexample_length": len(counterexample),
    }


def _nuxmv_row(ir: VerificationIR, backend: NuXmvBackend) -> dict[str, Any]:
    result = backend.verify(ir)
    counterexample = result.counterexample or ()
    return {
        "verdict": result.verdict.value,
        "backend": result.backend,
        "solver_hash": result.solver_hash,
        "bound": result.bound,
        "measured": _measured(result.verdict),
        "error": result.error,
        "counterexample": bool(counterexample),
        "counterexample_length": len(counterexample),
    }


def collect(backend: NuXmvBackend | None = None) -> list[dict[str, Any]]:
    """Measure every delegation IR variant with the reference interpreter, Z3 and nuXmv."""
    nuxmv = backend if backend is not None else NuXmvBackend()
    rows: list[dict[str, Any]] = []
    for variant in all_delegation_ir_variants():
        reference = reference_safety_check(variant.ir)
        rows.append(
            {
                "ir_id": variant.ir.id,
                "ir_fingerprint": variant.ir.fingerprint,
                "mutation": variant.mutation.value,
                "reference": reference.verdict.value,
                "reference_states": reference.states,
                "z3": _z3_row(variant.ir),
                "nuxmv": _nuxmv_row(variant.ir, nuxmv),
            },
        )
    return rows


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise agreement. An unmeasured backend is excluded, never counted as agreeing."""
    total = len(rows)
    both = [row for row in rows if row["z3"]["measured"] and row["nuxmv"]["measured"]]
    ref_z3 = [row for row in rows if row["z3"]["measured"]]
    ref_nuxmv = [row for row in rows if row["nuxmv"]["measured"]]
    agree_ref_z3 = [row for row in ref_z3 if verdict_class(row["reference"]) == verdict_class(row["z3"]["verdict"])]
    agree_ref_nuxmv = [row for row in ref_nuxmv if verdict_class(row["reference"]) == verdict_class(row["nuxmv"]["verdict"])]
    agree_all = [
        row
        for row in both
        if verdict_class(row["reference"]) == verdict_class(row["z3"]["verdict"]) == verdict_class(row["nuxmv"]["verdict"])
    ]
    refuted = [row for row in rows if verdict_class(row["reference"]) != "safe"]
    return {
        "total_variants": total,
        "z3_measured": len(ref_z3),
        "nuxmv_measured": len(ref_nuxmv),
        "refuted_variants": len(refuted),
        "agree_reference_z3": len(agree_ref_z3) if ref_z3 else None,
        "agree_reference_nuxmv": len(agree_ref_nuxmv) if ref_nuxmv else None,
        "agree_all_three": len(agree_all) if both else None,
        "all_agree": len(agree_all) == len(both) if both else None,
        "control_ok": bool(refuted),
    }


def build(backend: NuXmvBackend | None = None) -> dict[str, Any]:
    """Build the evidence without writing anything."""
    rows = collect(backend)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.verification.reduction + conflux.verification.z3_backend + conflux.verification.nuxmv_backend",
        "summary": summarise(rows),
        "results": rows,
    }


def generate(output: Path = OUTPUT, backend: NuXmvBackend | None = None) -> dict[str, Any]:
    """Generate the three-way agreement bundle and write it to ``output``."""
    evidence = build(backend)
    output.mkdir(parents=True, exist_ok=True)
    (output / "result.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def _comparable(evidence: dict[str, Any]) -> str:
    return json.dumps(
        {key: value for key, value in evidence.items() if key not in VOLATILE},
        indent=2,
        sort_keys=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument("--check", action="store_true", help="compare against the retained bundle")
    args = parser.parse_args(argv)

    output = Path(args.output)
    evidence = build() if args.check else generate(output)
    summary = evidence["summary"]
    for key in sorted(summary):
        print(f"{key}: {summary[key]}")
    if summary["all_agree"] is not True:
        print("disagreement: backends do not agree on every variant they both measured")
        return 1
    if not summary["control_ok"]:
        print("control failed: no variant was refuted, so the battery proves nothing")
        return 1
    if args.check:
        retained = output / "result.json"
        try:
            previous = json.loads(retained.read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"{retained} does not exist; run without --check to write it")
            return 1
        if _comparable(previous) != _comparable(evidence):
            print(f"{retained} differs from a fresh run")
            return 1
        print("retained bundle matches a fresh run (nothing was written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
