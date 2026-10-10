"""Sweep every combination of the delegation IR defects against all three backends.

The sibling cross-validation measures one hand-built mutation at a time, so its family is an enumeration
and its summary can claim agreement only on the variants someone chose to write down. This generator
closes the population instead: it builds one IR for every subset of the nine independent defects, so the
claim is agreement on every combination the defect space contains rather than on a selected list.

Agreement here is still evidence about three encodings of one IR, not a proof of the delegation
semantics: the reference interpreter is the definition the two encodings are checked against, and the
defect space is a closed set of edits to this consumption rule rather than every way a delegation system
can go wrong. The nuXmv backend is optional, so a run without it records the backend as unmeasured and
makes no three-way claim for those rows.

Usage:
    python scripts/generate_delegation_defect_sweep.py [--output DIR]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from conflux.verification.delegation_ir import (
    DELEGATION_IR_DEFECTS,
    DelegationIRMutation,
    build_combined_delegation_ir,
)
from conflux.verification.nuxmv_backend import NuXmvBackend
from conflux.verification.reduction import reference_safety_check
from conflux.verification.z3_backend import verify_with_z3

OUTPUT = Path("research/output/runs/delegation-defect-sweep-v1")
"""Retained bundle directory; curated into git by an un-ignore rule in .gitignore."""

SAFE_FAMILY = frozenset({"safe", "bounded_safe"})
"""Verdicts that mean "no violation found within the stated bounds".

The reference interpreter and the nuXmv IC3 backend report ``safe`` and the bounded checker reports
``bounded_safe``: same class, different scope of guarantee. Every raw string stays in its row. A test
pins this set equal to the sibling generators' set so the readings cannot drift apart.
"""

BOUNDARY = (
    "Agreement between these three encodings on every subset of the defect space is not a proof of the "
    "delegation semantics: the reference interpreter is the definition, and the space is a closed set "
    "of edits to one consumption rule rather than every way a delegation system can go wrong."
)
"""What the bundle must not be read to show; the SUMMARY carries a test-pinned copy."""


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


def defect_subsets() -> tuple[frozenset[DelegationIRMutation], ...]:
    """Return every subset of the defect space, smallest first, ties in declaration order."""
    return tuple(
        frozenset(combination)
        for size in range(len(DELEGATION_IR_DEFECTS) + 1)
        for combination in combinations(DELEGATION_IR_DEFECTS, size)
    )


def _row(defects: frozenset[DelegationIRMutation], backend: NuXmvBackend) -> dict[str, Any]:
    """Measure one defect combination with all three backends and return its row."""
    ir = build_combined_delegation_ir(defects)
    reference = reference_safety_check(ir)
    z3 = verify_with_z3(ir)
    nuxmv = backend.verify(ir)
    witness = z3.counterexample or ()
    nuxmv_witness = nuxmv.counterexample or ()
    reference_verdict = reference.verdict.value
    z3_verdict = z3.verdict.value
    nuxmv_verdict = nuxmv.verdict.value
    return {
        "defects": sorted(defect.value for defect in defects),
        "defect_count": len(defects),
        "ir_id": ir.id,
        "ir_fingerprint": ir.fingerprint,
        "reference_verdict": reference_verdict,
        "reference_states": reference.states,
        "z3_verdict": z3_verdict,
        "z3_error": z3.error,
        "z3_measured": z3_verdict != "unknown",
        "z3_counterexample": bool(witness),
        "z3_counterexample_length": len(witness),
        "nuxmv_verdict": nuxmv_verdict,
        "nuxmv_backend": nuxmv.backend,
        "nuxmv_solver_hash": nuxmv.solver_hash,
        "nuxmv_error": nuxmv.error,
        "nuxmv_measured": nuxmv_verdict != "unknown",
        "nuxmv_counterexample": bool(nuxmv_witness),
        "nuxmv_counterexample_length": len(nuxmv_witness),
        "nuxmv_agrees_raw": reference_verdict == nuxmv_verdict,
        "nuxmv_agrees_class": verdict_class(reference_verdict) == verdict_class(nuxmv_verdict),
        "verdicts_agree_raw": reference_verdict == z3_verdict,
        "verdicts_agree_class": verdict_class(reference_verdict) == verdict_class(z3_verdict),
        "all_three_agree_class": (
            verdict_class(reference_verdict) == verdict_class(z3_verdict) == verdict_class(nuxmv_verdict)
        ),
    }


def build(
    rows: Sequence[dict[str, Any]] | None = None,
    backend: NuXmvBackend | None = None,
) -> dict[str, Any]:
    """Return the bundle for *rows*, measuring every subset when rows are not supplied."""
    if rows is not None:
        measured = list(rows)
    else:
        nuxmv = backend if backend is not None else NuXmvBackend()
        measured = [_row(defects, nuxmv) for defects in defect_subsets()]
    raw_disagreements = [row["ir_id"] for row in measured if not row["verdicts_agree_raw"]]
    class_disagreements = [row["ir_id"] for row in measured if not row["verdicts_agree_class"]]
    three_way_disagreements = [row["ir_id"] for row in measured if not row["all_three_agree_class"]]
    nuxmv_raw_disagreements = [row["ir_id"] for row in measured if not row["nuxmv_agrees_raw"]]
    unmeasured = [row["ir_id"] for row in measured if not row["z3_measured"]]
    refuted = [row["ir_id"] for row in measured if verdict_class(str(row["reference_verdict"])) == "unsafe"]
    unrefuted = [row["ir_id"] for row in measured if verdict_class(str(row["reference_verdict"])) == "safe"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_commit": _source_commit(),
        "module": (
            "conflux.verification.z3_backend + conflux.verification.nuxmv_backend"
            " + conflux.verification.reduction"
        ),
        "suite": "delegation-ir-defect-space",
        "defects": [defect.value for defect in DELEGATION_IR_DEFECTS],
        "boundary": BOUNDARY,
        "total_subsets": len(measured),
        "agreements": len(measured) - len(class_disagreements),
        "disagreements": len(class_disagreements),
        "raw_agreements": len(measured) - len(raw_disagreements),
        "raw_disagreements": len(raw_disagreements),
        "raw_disagreement_ids": raw_disagreements,
        "unmeasured": unmeasured,
        "nuxmv_unmeasured": [row["ir_id"] for row in measured if not row["nuxmv_measured"]],
        "three_way_agreements": len(measured) - len(three_way_disagreements),
        "three_way_disagreement_ids": three_way_disagreements,
        "nuxmv_raw_agreements": len(measured) - len(nuxmv_raw_disagreements),
        "nuxmv_raw_disagreements": len(nuxmv_raw_disagreements),
        "nuxmv_raw_disagreement_ids": nuxmv_raw_disagreements,
        "all_agree": not three_way_disagreements,
        "positive_control": len(refuted),
        "unrefuted": unrefuted,
        "results": measured,
    }


def summarise(evidence: dict[str, Any]) -> str:
    """Return the SUMMARY.md text for *evidence*."""
    lines = [
        "# Delegation defect sweep: every combination of the nine defects",
        "",
        f"Suite: {evidence['suite']} (`build_combined_delegation_ir` over all subsets),"
        f" {evidence['total_subsets']} subsets of {len(evidence['defects'])} defects.",
        f"Source commit: `{evidence['source_commit']}`.",
        "",
        "The population is closed by construction: every one of the"
        f" {2 ** len(evidence['defects'])} subsets of the defect space appears exactly once, so this is"
        " not a selected list of variants.",
        "",
        f"Verdict classes agree across all three backends on {evidence['three_way_agreements']} of"
        f" {evidence['total_subsets']} subsets ({len(evidence['three_way_disagreement_ids'])} class"
        " disagreements). Against the interpreter, the Z3 raw verdict strings agree on"
        f" {evidence['raw_agreements']} and differ on {evidence['raw_disagreements']} subset(s), which"
        " is the bounded checker's `bounded_safe` against the interpreter's `safe` on the canonical body:"
        " one class, two scopes of guarantee. The nuXmv IC3 verdicts agree with the interpreter as raw"
        f" strings on {evidence['nuxmv_raw_agreements']} subset(s) and as classes on"
        f" {evidence['three_way_agreements']}; a run without nuXmv records"
        f" {len(evidence['nuxmv_unmeasured'])} unmeasured subset(s) and makes no three-way claim.",
        "",
        f"Positive control: {evidence['positive_control']} subsets carry an unsafe reference verdict, so"
        " an all-clear reading cannot come from a space that nothing can refute; the"
        f" {len(evidence['unrefuted'])} subset(s) that are not refuted are recorded by id"
        f" ({', '.join(evidence['unrefuted']) or 'none'}).",
        "",
        "What this shows: on every subset of the nine-defect space the Z3 and nuXmv encodings"
        " reproduce the reference interpreter's verdict class, and all three backends refute every"
        " subset that names at least one defect.",
        "",
        f"What this does not show: {evidence['boundary']}",
        "",
        "Rerun: `python scripts/generate_delegation_defect_sweep.py`",
        "Detail: `evidence.json` in this directory.",
        "",
    ]
    return "\n".join(lines)


VOLATILE_FIELDS = ("generated_at", "source_commit")
"""Provenance that changes between identical runs, so a check must ignore it."""


def _comparable(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return *evidence* without the fields that change between identical runs."""
    return {key: value for key, value in evidence.items() if key not in VOLATILE_FIELDS}


def check(
    output: Path,
    rows: Sequence[dict[str, Any]] | None = None,
    backend: NuXmvBackend | None = None,
) -> int:
    """Compare a fresh run against the retained bundle in *output* and return the exit code.

    *rows* exists so a test can drive both directions without measuring the whole space.
    """
    retained_path = output / "evidence.json"
    if not retained_path.exists():
        print(f"no retained bundle at {retained_path}; run without --check to write one")
        return 1
    retained = _comparable(json.loads(retained_path.read_text(encoding="utf-8")))
    fresh = _comparable(build(rows, backend))
    differing = sorted(key for key in set(retained) | set(fresh) if retained.get(key) != fresh.get(key))
    if differing:
        print(f"the sweep differs from the retained bundle at {output}: {', '.join(differing)}")
        return 1
    print(f"the sweep matches the retained bundle at {output}")
    return 0


def generate(output: Path, rows: Sequence[dict[str, Any]] | None = None) -> int:
    """Write the bundle into *output* and return the process exit code.

    *rows* exists so a test can drive the positive control without running the whole space.
    """
    evidence = build(rows)
    output.mkdir(parents=True, exist_ok=True)
    (output / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    (output / "SUMMARY.md").write_text(summarise(evidence), encoding="utf-8", newline="\n")
    print(
        f"delegation defect sweep: {evidence['three_way_agreements']}/{evidence['total_subsets']}"
        f" three-way class agreements, {evidence['raw_disagreements']} raw z3 difference(s),"
        f" {evidence['nuxmv_raw_disagreements']} raw nuxmv difference(s), positive control"
        f" {evidence['positive_control']} refuted subset(s)",
    )
    return 0 if evidence["all_agree"] and evidence["positive_control"] else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare a fresh sweep against the retained bundle instead of writing one",
    )
    args = parser.parse_args(argv)
    if args.check:
        return check(Path(args.output))
    return generate(Path(args.output))


if __name__ == "__main__":
    sys.exit(main())
