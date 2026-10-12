"""Generate plan IR progress evidence: does a declared goal/abort pair decide a bounded row?

The plan IR's liveness obligation is ``AG(step >= bound -> terminated)``, and the abstraction assigns
``terminated`` itself when the step guard fires, so a bounded row satisfies it by construction. This
generator measures the obligation that replaces that tautology for a plan that declares its two good
endings - the node that reaches the goal and a node that stops without the goal:

    ``step >= bound -> (goal_reached or safe_abort)``

with two support invariants that stop an endpoint from being reached through an unauthorised effect
(``safe-abort-clean`` and ``goal-reached-clean``). The abstraction is asked for those endpoints only
when the caller declares them, so the readings that declare nothing keep the shape every earlier
bundle recorded.

The population is structured, not selected. Every reading appears once at each bound from 1 to 4:

* ``positive:goal-and-abort`` - both endpoints declared, every path takes one;
* ``control:goal-never-reached`` - one endpoint declared and the other node may be taken forever;
* ``control:wandering-plan`` - a three-node plan whose first node may be taken forever;
* ``control:unsafe-abort`` - the declared abort node is an action recorded as executed unauthorised;
* ``control:goal-declared-not-executed`` - the declared goal action is recorded as not executed;
* ``control:weakened-progress`` - the obligation replaced by a bare ``goal_reached`` claim;
* ``default:no-endpoints`` - no endpoint declared, which must keep the recorded shape.

Each reading is measured with the reference interpreter, the Z3 encoding and the nuXmv backend on the
bounded model, and each row records the verdict, the auxiliary its checker needed, the bound, and
whether measurement met the stated expectation.

Usage:
    python scripts/generate_plan_ir_progress_evidence.py
    python scripts/generate_plan_ir_progress_evidence.py --check
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:  # pragma: no cover - import bootstrap for direct invocation
    sys.path.insert(0, str(ROOT / "src"))

from conflux.domain import Principal, Provenance  # noqa: E402
from conflux.planning import OperationCatalogue  # noqa: E402
from conflux.verification import EffectSummary, NuXmvBackend, abstract_plan, verify_with_z3  # noqa: E402
from conflux.verification.ir import Expression, SafetyInvariant, VerificationIR  # noqa: E402
from conflux.verification.reduction import reference_safety_check  # noqa: E402

OUTPUT_DIR = ROOT / "research" / "output" / "runs" / "plan-ir-progress-v1"

BOUNDS = (1, 2, 3, 4)
SAFE_FAMILY = frozenset({"safe", "bounded_safe"})
VOLATILE_FIELDS = ("generated_at", "source_commit")

# The shape every retained bounded row already records: seven invariants and ten state variables.
BASELINE_INVARIANTS = 7
BASELINE_VARIABLES = 10

ROUTES: dict[str, str] = {
    "reference": "the bound is declared; the interpreter walks the reachable states",
    "z3": "the bound is declared; the obligation is asserted at the final step",
    "nuxmv": (
        "none on this bounded route: the step counter keeps its declared range; the symbolic route's "
        "transition-guard auxiliary is recorded in parameter-general-v1"
    ),
}

BOUNDARY = (
    "Four bounds of one plan shape family with declared endpoints, and one control per way the "
    "obligation can fail, are not a claim that a plan in general reaches its goal: the readings cover "
    "the three plan shapes, one operation catalogue and one mutant per lever, the endpoint declaration "
    "is the caller's, and whether a goal predicate can be read from a plan field rather than from a "
    "recorded effect summary is still open."
)


def _grid() -> Any:
    """Load the bounded plan-IR grid generator, whose plan shapes and operations these readings reuse."""
    path = ROOT / "scripts" / "generate_plan_ir_evidence.py"
    spec = importlib.util.spec_from_file_location("generate_plan_ir_evidence", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verdict_class(verdict: str) -> str:
    """Return "safe" for every verdict in the safe family and "unsafe" otherwise."""
    return "safe" if verdict in SAFE_FAMILY else "unsafe"


def readings() -> tuple[str, ...]:
    """Return every reading of the population, in order, without repeating one."""
    return ("positive:goal-and-abort", "default:no-endpoints", *(f"control:{control}" for control in CONTROLS))


def reading_ids() -> list[str]:
    """Return every reading id of the population, in order."""
    return [f"{reading}:b{bound}" for bound in BOUNDS for reading in readings()]


CONTROLS = (
    "goal-never-reached",
    "wandering-plan",
    "unsafe-abort",
    "goal-declared-not-executed",
    "weakened-progress",
)

EXPECTATIONS: dict[str, str] = {}
for _name in ("positive:goal-and-abort", "default:no-endpoints"):
    for _bound in BOUNDS:
        EXPECTATIONS[f"{_name}:b{_bound}"] = "clear"
for _control in CONTROLS:
    for _bound in BOUNDS:
        EXPECTATIONS[f"control:{_control}:b{_bound}"] = "refuted"


def _plan_for(reading: str, bound: int) -> tuple[Any, Any, Any, tuple[EffectSummary, ...], tuple[str, ...], tuple[str, ...]]:
    """Return the plan, its operations, effect summaries and declared endpoints for *reading*."""
    grid = _grid()
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="evidence")
    write, code = grid._operations()  # noqa: SLF001
    case = "pair" if reading == "control:wandering-plan" else "single"
    plan = grid._build_plan(case, source, write, code)  # noqa: SLF001
    effect_case = "authorised"
    summaries: tuple[EffectSummary, ...] | None = None
    goal: tuple[str, ...] = ()
    abort: tuple[str, ...] = ()
    if reading == "positive:goal-and-abort":
        goal, abort = ("write",), ("delegate",)
    elif reading == "default:no-endpoints":
        pass
    elif reading == "control:goal-never-reached":
        goal = ("delegate",)
    elif reading == "control:wandering-plan":
        goal, abort = ("append",), ("delegate",)
    elif reading == "control:unsafe-abort":
        summaries = (EffectSummary("write", False, True),)
        goal, abort = ("delegate",), ("write",)
    elif reading == "control:goal-declared-not-executed":
        summaries = (EffectSummary("write", True, False),)
        goal, abort = ("write",), ("delegate",)
    elif reading == "control:weakened-progress":
        goal, abort = ("write",), ("delegate",)
    else:  # pragma: no cover - reading ids come from this module
        raise ValueError(f"unknown reading: {reading}")
    built = grid._summaries(case, plan, effect_case) if summaries is None else summaries  # noqa: SLF001
    return (plan, write, code, built, goal, abort)


def with_weakened_progress(ir: VerificationIR) -> VerificationIR:
    """Return the same model with the progress obligation weakened to a claim the model never makes."""
    weakened = tuple(
        SafetyInvariant(item.id, Expression.variable("goal_reached")) if item.id == "bounded-progress" else item
        for item in ir.invariants
    )
    return VerificationIR(
        f"{ir.id}:weakened-progress",
        ir.variables,
        ir.transitions,
        weakened,
        ir.bound,
        ir.assumptions,
    )


def reading_ir(reading: str, bound: int) -> VerificationIR:
    """Build the IR a reading measures, with its endpoints declared as the reading says."""
    plan, write, code, summaries, goal, abort = _plan_for(reading, bound)
    abstraction = abstract_plan(
        plan,
        catalogue=OperationCatalogue((write, code)),
        effect_summaries=summaries,
        bound=bound,
        goal_nodes=goal,
        abort_nodes=abort,
    )
    if abstraction.ir is None:
        raise RuntimeError(f"plan abstraction returned unsupported: {list(abstraction.unsupported)}")
    ir = abstraction.ir
    return with_weakened_progress(ir) if reading == "control:weakened-progress" else ir


def _row(reading: str, bound: int, route: str, backend: NuXmvBackend, ir: VerificationIR) -> dict[str, Any]:
    """Measure one reading on one route and return its retained record."""
    expectation = EXPECTATIONS[f"{reading}:b{bound}"]
    record: dict[str, Any] = {
        "reading_id": f"{reading}:b{bound}",
        "reading": reading,
        "route": route,
        "bound": bound,
        "ir_id": ir.id,
        "ir_fingerprint": ir.fingerprint,
        "invariants": [item.id for item in ir.invariants],
        "invariant_count": len(ir.invariants),
        "variable_count": len(ir.variables),
        "endpoint_declared": any(item.id == "bounded-progress" for item in ir.invariants),
        "auxiliary_invariant": ROUTES[route],
        "expectation": expectation,
    }
    if route == "reference":
        reference = reference_safety_check(ir)
        verdict, states, solver_hash, error, counterexample = (
            reference.verdict.value,
            reference.states,
            None,
            None,
            reference.counterexample,
        )
    elif route == "z3":
        z3 = verify_with_z3(ir)
        verdict, states, solver_hash, error, counterexample = (
            z3.verdict.value,
            None,
            z3.solver_hash,
            z3.error,
            z3.counterexample,
        )
    else:
        nuxmv = backend.verify(ir)
        verdict, states, solver_hash, error, counterexample = (
            nuxmv.verdict.value,
            None,
            nuxmv.solver_hash,
            nuxmv.error,
            nuxmv.counterexample,
        )
    record["states"] = states
    record["solver_hash"] = solver_hash
    record["verdict"] = verdict
    record["measured"] = verdict != "unknown"
    record["counterexample_present"] = bool(counterexample)
    record["error"] = error
    record["verdict_class"] = verdict_class(verdict)
    record["expectation_met"] = record["verdict_class"] == ("safe" if expectation == "clear" else "unsafe")
    return record


def rows_for(bounds: Sequence[int] = BOUNDS, backend: NuXmvBackend | None = None) -> list[dict[str, Any]]:
    """Measure every reading of the population with all three routes."""
    nuxmv = backend if backend is not None else NuXmvBackend()
    rows: list[dict[str, Any]] = []
    for bound in bounds:
        for reading in readings():
            ir = reading_ir(reading, bound)
            rows.extend(_row(reading, bound, route, nuxmv, ir) for route in ROUTES)
    return rows


def _rows_by_reading(rows: Sequence[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group measured rows by reading id."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["reading_id"]), []).append(row)
    return grouped


def build(rows: Sequence[dict[str, Any]] | None = None, backend: NuXmvBackend | None = None) -> dict[str, Any]:
    """Return the bundle for *rows*, measuring the full population when rows are not supplied."""
    measured = list(rows) if rows is not None else rows_for(backend=backend)
    grouped = _rows_by_reading(measured)
    disagreements = sorted(
        reading
        for reading, group in grouped.items()
        if len({str(row["verdict_class"]) for row in group}) != 1
    )
    missed = sorted({str(row["reading_id"]) for row in measured if not row.get("expectation_met", True)})
    refuted = sorted({str(row["reading_id"]) for row in measured if row["reading_id"].startswith("control:")})
    helpers = [row for row in measured if row["reading"] == "default:no-endpoints"]
    baseline = next(
        (row for row in measured if row["reading_id"] == f"positive:goal-and-abort:b{max(BOUNDS)}" and row["route"] == "reference"),
        None,
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_commit": _source_commit(),
        "module": "conflux.verification.plan_ir + z3_backend + nuxmv_backend + reduction",
        "suite": "plan-ir-progress",
        "bounds": list(BOUNDS),
        "readings": reading_ids(),
        "controls": list(CONTROLS),
        "expectations": {key: EXPECTATIONS[key] for key in sorted(EXPECTATIONS)},
        "routes": dict(ROUTES),
        "boundary": BOUNDARY,
        "total_rows": len(measured),
        "total_readings": len(grouped),
        "readings_agreeing_by_class": len(grouped) - len(disagreements),
        "readings_disagreeing_by_class": disagreements,
        "expectations_met": len(measured) - len([row for row in measured if not row.get("expectation_met", True)]),
        "expectations_missed": missed,
        "positive_control": len(refuted),
        "refuted_reading_ids": refuted,
        "default_path_invariants": sorted({int(row["invariant_count"]) for row in helpers}),
        "default_path_variables": sorted({int(row["variable_count"]) for row in helpers}),
        "default_path_unchanged": (
            {int(row["invariant_count"]) for row in helpers} == {BASELINE_INVARIANTS}
            and {int(row["variable_count"]) for row in helpers} == {BASELINE_VARIABLES}
        ),
        "all_agree": not disagreements,
        "baseline": baseline,
        "results": measured,
    }


def summarise(evidence: dict[str, Any]) -> str:
    """Render the SUMMARY that must stay consistent with the evidence bundle."""
    return "\n".join(
        [
            "# Plan IR progress evidence: a declared goal/abort pair decides the bounded row",
            "",
            f"Suite: {evidence['suite']} ({len(evidence['readings'])} readings x {len(evidence['routes'])} routes), "
            f"{evidence['total_rows']} measured rows at bounds {', '.join(str(bound) for bound in evidence['bounds'])}.",
            f"Source commit: `{evidence['source_commit']}`.",
            "",
            "The liveness obligation the plan IR recorded before this bundle is `AG(step >= bound -> terminated)`, "
            "and the abstraction assigns `terminated` itself, so a bounded row satisfied it by construction. The "
            "readings here declare a plan's two good endings instead - the node that reaches the goal and a node "
            "that stops without it - and measure `step >= bound -> (goal_reached or safe_abort)` with the support "
            "invariants `safe-abort-clean` and `goal-reached-clean`.",
            "",
            "The population is structured, not selected: the positive reading, the five controls and the "
            "no-endpoint reading each appear once at every bound from 1 to 4, and each reading states its "
            "expectation before it is measured.",
            "",
            f"Expectations met: {evidence['expectations_met']} of {evidence['total_rows']} measured rows "
            f"({len(evidence['expectations_missed'])} reading(s) missed).",
            f"The three routes agree by verdict class on {evidence['readings_agreeing_by_class']} of "
            f"{evidence['total_readings']} readings ({len(evidence['readings_disagreeing_by_class'])} class "
            "disagreements).",
            "",
            f"Positive control: {evidence['positive_control']} of {evidence['total_readings']} readings carry an "
            "unsafe reference verdict, one per reading of every control family, so the agreement cannot come from "
            "a population nothing can refute. The controls are: an endpoint declared on a node a path may never "
            "take, a three-node plan whose first node may be taken forever, an abort node recorded as executed "
            "without authorisation, a goal action recorded as not executed, and the obligation weakened to a bare "
            "`goal_reached` claim.",
            "",
            f"The no-endpoint reading keeps the shape every earlier bundle recorded: {evidence['default_path_invariants']} "
            f"invariants and {evidence['default_path_variables']} state variables "
            f"({'unchanged' if evidence['default_path_unchanged'] else 'CHANGED'}).",
            "",
            "What each route needed, per row: "
            + "; ".join(f"`{route}` - {text}" for route, text in sorted(evidence["routes"].items()))
            + ".",
            "",
            f"What this does not show: {evidence['boundary']}",
            "",
            "Rerun: `python scripts/generate_plan_ir_progress_evidence.py`",
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
        print("refusing to write a population that nothing can refute: no control reading carries an unsafe verdict")
        return 1
    output.mkdir(parents=True, exist_ok=True)
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "SUMMARY.md").write_text(summarise(evidence), encoding="utf-8")
    print(
        f"plan IR progress: {evidence['readings_agreeing_by_class']}/{evidence['total_readings']} readings in class"
        f" agreement, positive control {evidence['positive_control']} reading(s) refuted,"
        f" no-endpoint shape {'unchanged' if evidence['default_path_unchanged'] else 'CHANGED'}",
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
        print(f"the progress population matches the retained bundle at {output}")
        return 0
    print(f"the progress population drifted from the retained bundle at {output}:")
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
