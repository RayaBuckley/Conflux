"""Cross-validate the Z3 backend against the reference interpreter on delegation IR variants.

For each delegation IR variant both backends run and their verdicts are compared; a disagreement is a
bug in one of them. Every row keeps both verdicts raw and in class form: the bounded checker reports
``bounded_safe`` where the interpreter reports ``safe``, which is the same class with a narrower scope
of guarantee, and comparing the raw strings alone would read as a disagreement.

Agreement here is evidence about two encodings of one fixed family of hand-built variants, not a proof
of the IR semantics: the reference interpreter is the definition the encoding is checked against, so
agreement says the encoding reproduces it on these variants and nothing about variants outside them.

Usage:
    python scripts/generate_backend_cross_validation.py [--output DIR]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from conflux.verification.delegation_ir import (
    DelegationIRResult,
    all_delegation_ir_variants,
)
from conflux.verification.reduction import reference_safety_check
from conflux.verification.z3_backend import verify_with_z3

OUTPUT = Path("research/output/runs/backend-cross-validation-v1")
"""Retained bundle directory; curated into git by an un-ignore rule in .gitignore."""

SAFE_FAMILY = frozenset({"safe", "bounded_safe"})
"""Verdicts that mean "no violation found within the stated bounds".

The reference interpreter reports ``safe`` and the bounded model checker reports ``bounded_safe``: same
class, different scope of guarantee. The raw strings stay in every row so the two are never conflated
inside the artefact. This set is pinned equal to the sibling generator's set by a test.
"""

BOUNDARY = (
    "Agreement between these two encodings on this fixed family is not a proof of the IR semantics: "
    "the reference interpreter is the definition, and the family is a hand-built enumeration."
)


def verdict_class(verdict: str) -> str:
    """Map a verdict onto its class for cross-backend comparison."""
    return "safe" if verdict in SAFE_FAMILY else verdict


def _source_commit() -> str:
    """Return the commit that produced this bundle, or ``"unknown"`` outside a repository."""
    probe = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return probe.stdout.strip() if probe.returncode == 0 else "unknown"


def _row(variant: DelegationIRResult) -> dict[str, Any]:
    """Measure one variant with both backends and return its row."""
    ir = variant.ir
    reference = reference_safety_check(ir)
    z3 = verify_with_z3(ir)
    reference_verdict = reference.verdict.value
    z3_verdict = z3.verdict.value
    witness = z3.counterexample or ()
    return {
        "mutation": variant.mutation.value,
        "ir_id": ir.id,
        "ir_fingerprint": ir.fingerprint,
        "reference_verdict": reference_verdict,
        "reference_states": reference.states,
        "z3_verdict": z3_verdict,
        "z3_error": z3.error,
        "z3_measured": z3_verdict != "unknown",
        "z3_counterexample": bool(witness),
        "z3_counterexample_length": len(witness),
        "verdicts_agree_raw": reference_verdict == z3_verdict,
        "verdicts_agree_class": verdict_class(reference_verdict) == verdict_class(z3_verdict),
    }


def build(rows: Sequence[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return the bundle for *rows*, measuring every variant when rows are not supplied."""
    measured = list(rows) if rows is not None else [_row(variant) for variant in all_delegation_ir_variants()]
    raw_disagreements = [row["ir_id"] for row in measured if not row["verdicts_agree_raw"]]
    class_disagreements = [row["ir_id"] for row in measured if not row["verdicts_agree_class"]]
    unmeasured = [row["ir_id"] for row in measured if not row["z3_measured"]]
    refuted = [row["ir_id"] for row in measured if verdict_class(str(row["reference_verdict"])) == "unsafe"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_commit": _source_commit(),
        "module": "conflux.verification.z3_backend + conflux.verification.reduction",
        "suite": "delegation-ir-variants",
        "boundary": BOUNDARY,
        "total_variants": len(measured),
        "agreements": len(measured) - len(class_disagreements),
        "disagreements": len(class_disagreements),
        "raw_agreements": len(measured) - len(raw_disagreements),
        "raw_disagreements": len(raw_disagreements),
        "raw_disagreement_ids": raw_disagreements,
        "unmeasured": unmeasured,
        "all_agree": not class_disagreements,
        "positive_control": len(refuted),
        "results": measured,
    }


def summarise(evidence: dict[str, Any]) -> str:
    """Return the SUMMARY.md text for *evidence*."""
    return "\n".join(
        [
            "# Cross-backend validation: z3 against the reference interpreter",
            "",
            f"Suite: {evidence['suite']} (`all_delegation_ir_variants`), {evidence['total_variants']} variants.",
            f"Source commit: `{evidence['source_commit']}`.",
            "",
            f"Verdict classes agree on {evidence['agreements']} of {evidence['total_variants']} variants"
            f" ({evidence['disagreements']} class disagreements). The raw verdict strings agree on"
            f" {evidence['raw_agreements']}; they differ on {evidence['raw_disagreements']} variant(s),"
            " which is the bounded checker's `bounded_safe` against the interpreter's `safe`: one class,"
            " two scopes of guarantee. Both strings and both comparisons are recorded per variant.",
            "",
            f"Positive control: {evidence['positive_control']} variant(s) carry an unsafe reference verdict,"
            " so an all-clear reading cannot come from a family that nothing can refute."
            + (
                f" Unmeasured: {len(evidence['unmeasured'])} variant(s) returned no z3 verdict."
                if evidence["unmeasured"]
                else " Every variant was measured by z3."
            ),
            "",
            "What this shows: the z3 encoding reproduces the reference interpreter's verdict class on every",
            "variant in this fixed, hand-built family.",
            "",
            "What this does not show: it is not a proof of the IR semantics. The reference interpreter is",
            "the definition the encoding is checked against, the family is an enumeration rather than a",
            "closed grammar, and agreement on it says nothing about variants outside it.",
            "",
            "Rerun: `python scripts/generate_backend_cross_validation.py`",
            "Detail: `evidence.json` in this directory.",
            "",
        ],
    )


def generate(output: Path, rows: Sequence[dict[str, Any]] | None = None) -> int:
    """Write the bundle into *output* and return the process exit code.

    *rows* exists so a test can drive the positive control without editing the variant family.
    """
    evidence = build(rows)
    output.mkdir(parents=True, exist_ok=True)
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "SUMMARY.md").write_text(summarise(evidence), encoding="utf-8", newline="\n")
    print(
        f"cross-backend validation: {evidence['agreements']}/{evidence['total_variants']} class agreements,"
        f" {evidence['raw_disagreements']} raw difference(s), positive control {evidence['positive_control']}",
    )
    return 0 if evidence["all_agree"] and evidence["positive_control"] else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args(argv)
    return generate(Path(args.output))


if __name__ == "__main__":
    sys.exit(main())
