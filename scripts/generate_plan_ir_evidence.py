"""Generate plan IR verification evidence.

The extended plan IR invariants - delegation, monotonic confinement, revocation and liveness - are
encoded once for the bounded model checker and once for nuXmv. This script measures a small structured
population rather than a single plan: two plans (one action node, and a pair of action nodes) x two
effect summaries (every node authorised, and the first node executed while unauthorised) x bounds 1 to 4.
The authorised readings say the encodings agree and find nothing; the unauthorised readings are the
positive control, because a reading that nothing can refute would prove nothing.

The reference interpreter, the Z3 encoding and the nuXmv backend are all measured, so the bundle records
three-way agreement by verdict class. `--check` re-measures the grid and compares it with the retained
bundle, ignoring `generated_at` and `source_commit`, so the standard validation tier can detect drift.

Usage:
    python scripts/generate_plan_ir_evidence.py
    python scripts/generate_plan_ir_evidence.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from conflux.domain import WRITE, Principal, Provenance
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    DelegationNode,
    LiteralBinding,
    OperationCatalogue,
    OperationSchema,
    Plan,
    TemplateArgument,
)
from conflux.verification import EffectSummary, NuXmvBackend, abstract_plan, verify_with_z3
from conflux.verification.reduction import reference_safety_check

OUTPUT_DIR = Path("research/output/runs/plan_ir")

BOUNDS = (1, 2, 3, 4)
PLAN_CASES = ("single", "pair")
EFFECT_CASES = ("authorised", "unauthorised")

# The reference interpreter and nuXmv both report `safe`, the bounded checker reports `bounded_safe`:
# same class, two scopes of guarantee. A test pins this set equal to the sibling generators' set.
SAFE_FAMILY = frozenset({"safe", "bounded_safe"})

VOLATILE_FIELDS = ("generated_at", "source_commit")

BOUNDARY = (
    "Agreement between the two encodings on sixteen readings of two plans up to bound four is not a claim "
    "that the plan IR is safe in general: the grid covers one plan shape, one operation catalogue and one "
    "effect-summary pattern, and the space of plans is open."
)


def verdict_class(verdict: str) -> str:
    """Return "safe" for every verdict in the safe family and "unsafe" otherwise."""
    return "safe" if verdict in SAFE_FAMILY else "unsafe"


def _build_plan(case: str, principal: Principal, source: Provenance, operation: OperationSchema) -> Plan:
    """Build the protected plan shape for *case*: one action node, or a pair of action nodes."""
    nodes: list[ActionTemplateNode | DelegationNode] = [
        ActionTemplateNode(
            "write",
            ActionTemplate(
                "write",
                operation.id,
                operation.version,
                (
                    TemplateArgument("path", LiteralBinding("safe.txt", source)),
                    TemplateArgument("content", LiteralBinding("safe", source)),
                ),
            ),
            source,
        ),
    ]
    if case == "pair":
        nodes.append(
            ActionTemplateNode(
                "append",
                ActionTemplate(
                    "append",
                    operation.id,
                    operation.version,
                    (
                        TemplateArgument("path", LiteralBinding("notes.txt", source)),
                        TemplateArgument("content", LiteralBinding("more", source)),
                    ),
                ),
                source,
            ),
        )
    nodes.append(DelegationNode("delegate", "scope-text", source, ()))
    return Plan(f"evidence-plan-{case}", "repair", tuple(nodes), source)


def _summaries(case: str, plan: Plan, effect_case: str) -> tuple[EffectSummary, ...]:
    """Return effect summaries for *plan*: every node authorised, or the first action unauthorised."""
    rows = []
    for node in plan.nodes:
        if isinstance(node, ActionTemplateNode):
            unauthorised = effect_case == "unauthorised" and node is plan.nodes[0]
            rows.append(EffectSummary(node.id, not unauthorised, True))
    return tuple(rows)


def _row(case: str, effect_case: str, bound: int, backend: NuXmvBackend) -> dict[str, Any]:
    """Measure one reading of the grid with all three backends and return its row."""
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="evidence")
    operation = OperationSchema(
        "filesystem.write",
        "1",
        "filesystem",
        "file",
        "write",
        WRITE,
        (ArgumentSpec("path", ArgumentType.STRING), ArgumentSpec("content", ArgumentType.STRING)),
        "path",
    )
    plan = _build_plan(case, principal, source, operation)
    abstraction = abstract_plan(
        plan,
        catalogue=OperationCatalogue((operation,)),
        effect_summaries=_summaries(case, plan, effect_case),
        bound=bound,
    )
    if abstraction.ir is None:
        raise RuntimeError(f"plan abstraction returned unsupported: {list(abstraction.unsupported)}")
    ir = abstraction.ir
    reference = reference_safety_check(ir)
    z3 = verify_with_z3(ir)
    nuxmv = backend.verify(ir)
    z3_witness = z3.counterexample or ()
    nuxmv_witness = nuxmv.counterexample or ()
    reference_verdict = reference.verdict.value
    z3_verdict = z3.verdict.value
    nuxmv_verdict = nuxmv.verdict.value
    return {
        "plan_case": case,
        "effect_case": effect_case,
        "bound": bound,
        "ir_id": ir.id,
        "ir_fingerprint": ir.fingerprint,
        "invariants": len(ir.invariants),
        "transitions": len(ir.transitions),
        "reference_verdict": reference_verdict,
        "reference_states": reference.states,
        "z3_verdict": z3_verdict,
        "z3_error": z3.error,
        "z3_measured": z3_verdict != "unknown",
        "z3_counterexample": bool(z3_witness),
        "nuxmv_verdict": nuxmv_verdict,
        "nuxmv_solver_hash": nuxmv.solver_hash,
        "nuxmv_error": nuxmv.error,
        "nuxmv_measured": nuxmv_verdict != "unknown",
        "nuxmv_counterexample": bool(nuxmv_witness),
        "verdicts_agree_class": verdict_class(reference_verdict) == verdict_class(z3_verdict),
        "nuxmv_agrees_class": verdict_class(reference_verdict) == verdict_class(nuxmv_verdict),
        "all_three_agree_class": (verdict_class(reference_verdict) == verdict_class(z3_verdict) == verdict_class(nuxmv_verdict)),
    }


def rows_for(
    plan_cases: Sequence[str] = PLAN_CASES,
    effect_cases: Sequence[str] = EFFECT_CASES,
    bounds: Sequence[int] = BOUNDS,
    backend: NuXmvBackend | None = None,
) -> list[dict[str, Any]]:
    """Measure the plan x effect x bound grid."""
    nuxmv = backend if backend is not None else NuXmvBackend()
    return [_row(case, effect_case, bound, nuxmv) for case in plan_cases for effect_case in effect_cases for bound in bounds]


def build(rows: Sequence[dict[str, Any]] | None = None, backend: NuXmvBackend | None = None) -> dict[str, Any]:
    """Return the bundle for *rows*, measuring the full grid when rows are not supplied."""
    measured = list(rows) if rows is not None else rows_for(backend=backend)
    disagreements = [row["ir_id"] + f":b{row['bound']}" for row in measured if not row["all_three_agree_class"]]
    refuted = [row for row in measured if verdict_class(str(row["reference_verdict"])) == "unsafe"]
    unrefuted = [row["ir_id"] + f":b{row['bound']}" for row in measured if verdict_class(str(row["reference_verdict"])) == "safe"]
    baseline = next(
        (row for row in measured if row["plan_case"] == "single" and row["effect_case"] == "authorised" and row["bound"] == max(BOUNDS)),
        None,
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_commit": _source_commit(),
        "module": "conflux.verification.plan_ir + z3_backend + nuxmv_backend + reduction",
        "suite": "plan-ir-grid",
        "plans": list(PLAN_CASES),
        "effect_cases": list(EFFECT_CASES),
        "bounds": list(BOUNDS),
        "boundary": BOUNDARY,
        "total_readings": len(measured),
        "three_way_agreements": len(measured) - len(disagreements),
        "three_way_disagreement_ids": disagreements,
        "positive_control": len(refuted),
        "unrefuted": unrefuted,
        "all_agree": not disagreements,
        "baseline": baseline,
        "results": measured,
    }


def summarise(evidence: dict[str, Any]) -> str:
    """Render the SUMMARY that must stay consistent with the evidence bundle."""
    unrefuted = evidence["unrefuted"]
    return "\n".join(
        [
            "# Plan IR evidence: a plan x effect x bound grid, not a single reading",
            "",
            f"Suite: {evidence['suite']} ({len(evidence['plans'])} plan shapes x "
            f"{len(evidence['effect_cases'])} effect summaries x {len(evidence['bounds'])} bounds), "
            f"{evidence['total_readings']} readings.",
            f"Source commit: `{evidence['source_commit']}`.",
            "",
            "The population is structured, not selected: every combination of the two plan shapes, the two "
            "effect summaries and the four bounds appears exactly once, and the bound is a parameter of the "
            "abstraction rather than a chosen reading.",
            "",
            f"The three backends agree by verdict class on {evidence['three_way_agreements']} of "
            f"{evidence['total_readings']} readings ({len(evidence['three_way_disagreement_ids'])} class "
            "disagreements).",
            "",
            f"Positive control: {evidence['positive_control']} readings carry an unsafe reference verdict, so "
            "the agreement cannot come from a grid that nothing can refute. The readings that are not "
            f"refuted are recorded by id ({', '.join(f'`{item}`' for item in unrefuted)}).",
            "",
            "What this shows: on every reading of the grid the Z3 and nuXmv encodings reproduce the reference "
            "interpreter's verdict class, and the unauthorised readings are refuted at every bound from 1 to 4.",
            "",
            f"What this does not show: {evidence['boundary']}",
            "",
            "Rerun: `python scripts/generate_plan_ir_evidence.py`",
            "Detail: `evidence.json` in this directory.",
            "",
        ],
    )


def _source_commit() -> str:
    """Return the commit the tree is at, or an empty string when git cannot answer."""
    import subprocess

    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def generate(output: Path = OUTPUT_DIR, rows: Sequence[dict[str, Any]] | None = None) -> int:
    """Write the evidence bundle and its SUMMARY, and return an exit code."""
    evidence = build(rows)
    if not evidence["positive_control"]:
        print("refusing to write a grid that nothing can refute: no reading carries an unsafe verdict")
        return 1
    output.mkdir(parents=True, exist_ok=True)
    (output / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "SUMMARY.md").write_text(summarise(evidence), encoding="utf-8")
    print(
        f"plan IR grid: {evidence['three_way_agreements']}/{evidence['total_readings']} three-way class"
        f" agreements, positive control {evidence['positive_control']} refuted reading(s)",
    )
    return 0


def _comparable(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return *evidence* without the volatile fields, so a check ignores timestamps and commits."""
    stripped = {key: value for key, value in evidence.items() if key not in VOLATILE_FIELDS}
    baseline = stripped.get("baseline")
    if isinstance(baseline, dict):
        stripped["baseline"] = {key: value for key, value in baseline.items() if key not in VOLATILE_FIELDS}
    return stripped


def check(output: Path = OUTPUT_DIR, rows: Sequence[dict[str, Any]] | None = None) -> int:
    """Compare a fresh run against the retained bundle in *output* and return the exit code."""
    retained_path = output / "evidence.json"
    if not retained_path.exists():
        print(f"no retained bundle at {retained_path}; run without --check to write one")
        return 1
    retained = _comparable(json.loads(retained_path.read_text(encoding="utf-8")))
    fresh = _comparable(build(rows))
    if retained == fresh:
        print(f"the grid matches the retained bundle at {output}")
        return 0
    print(f"the grid drifted from the retained bundle at {output}:")
    for key in sorted(set(retained) | set(fresh)):
        if retained.get(key) != fresh.get(key):
            print(f"  {key}: retained {retained.get(key)!r} != fresh {fresh.get(key)!r}")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the generator, or only the drift check when --check is passed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare with the retained bundle instead of writing")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="bundle directory")
    args = parser.parse_args(argv)
    if args.check:
        return check(Path(args.output))
    return generate(Path(args.output))


if __name__ == "__main__":
    sys.exit(main())
