#!/usr/bin/env python3
"""Parameter-general plan-IR verdicts, with the controls that keep them honest.

Every other verification bundle in this repository records a verdict about a bounded model, and
``ir_bound`` says which bound. This bundle records the opposite kind of row: the step counter of the
plan IR is declared without a range, so the model has an infinite-precision integer, and the nuXmv
SMT route (``go_msat`` then ``msat_check_invar_bmc``) settles the invariants without naming a bound or
a depth. The guards, not the type, keep each run finite.

Each row therefore records three things a bounded row does not need:

* ``symbolic_parameter`` - the quantity that was left symbolic, in words;
* ``auxiliary_invariant`` - the extra invariant the proof rests on, in words;
* ``expectation`` - the verdict the row is expected to carry, so a mismatch is visible.

Two controls are retained beside the positive row: a weakened invariant, which the route must not
report safe, and the same unbounded model on the BDD route, which must fail closed instead of
claiming a verdict. A row is never evidence of a bound it did not use.

Usage:
    python scripts/generate_parameter_general_evidence.py
    python scripts/generate_parameter_general_evidence.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:  # pragma: no cover - import bootstrap for direct invocation
    sys.path.insert(0, str(ROOT / "src"))

OUTPUT = ROOT / "research" / "output" / "runs" / "parameter-general-v1"
BINARY = "nuXmv"
DEFAULT_TIMEOUT_SECONDS = 300.0
SMT_COMMANDS = "go_msat\nmsat_check_invar_bmc\nquit\n"
BDD_COMMANDS = "go\nbuild_boolean_model\ncheck_invar_ic3\nquit\n"

from conflux.verification import abstract_plan  # noqa: E402
from conflux.verification.ir import Expression, SafetyInvariant, VerificationIR  # noqa: E402
from conflux.verification.nuxmv_backend import NuXmvBackend  # noqa: E402


def _load_script(name: str) -> Any:
    """Load a sibling script by path, as its documented invocation does."""
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_text(text: str) -> str:
    """Return the SHA-256 hex digest of ``text``."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def plan_ir(case: str, effect_case: str, bound: int, *, unbounded_step: bool) -> VerificationIR:
    """Rebuild the plan abstraction IR, optionally without a declared range on the step counter."""
    from conflux.domain import Principal, Provenance
    from conflux.planning import OperationCatalogue

    plan = _load_script("generate_plan_ir_evidence.py")
    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="evidence")
    write, code = plan._operations()  # noqa: SLF001
    built = plan._build_plan(case, source, write, code)  # noqa: SLF001
    abstraction = abstract_plan(
        built,
        catalogue=OperationCatalogue((write, code)),
        effect_summaries=plan._summaries(case, built, effect_case),  # noqa: SLF001
        bound=bound,
        unbounded_step=unbounded_step,
    )
    if abstraction.ir is None:
        raise RuntimeError(f"plan abstraction unsupported: {list(abstraction.unsupported)}")
    return abstraction.ir


def with_weakened_invariant(ir: VerificationIR) -> VerificationIR:
    """Return the same model with the liveness invariant weakened to a claim the model never makes."""
    weakened = tuple(
        SafetyInvariant(item.id, Expression.variable("terminated")) if item.id == "bounded-liveness" else item
        for item in ir.invariants
    )
    return VerificationIR(
        f"{ir.id}:weakened",
        ir.variables,
        ir.transitions,
        weakened,
        ir.bound,
        ir.assumptions,
    )


def probe_row(
    row_id: str,
    family: str,
    ir: VerificationIR,
    *,
    expectation: str,
    symbolic_parameter: str,
    auxiliary_invariant: str,
    route: str,
    smt: bool,
    also_evidence: str,
    binary: str = BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Verify one IR on the requested route and return its retained record."""
    ic3 = _load_script("generate_ic3_unbounded_evidence.py")
    runner = ic3.RecordingNuXmvRunner(timeout)
    backend = NuXmvBackend(binary=binary, runner=runner)
    result = backend.verify(ir, smt=smt)
    record: dict[str, Any] = {
        "row_id": row_id,
        "family": family,
        "route": route,
        "model_id": ir.id,
        "ir_fingerprint": ir.fingerprint,
        "guard_constant": ir.bound,
        "step_counter_has_declared_range": any(
            variable.name == "step" and variable.maximum is not None for variable in ir.variables
        ),
        "symbolic_parameter": symbolic_parameter,
        "auxiliary_invariant": auxiliary_invariant,
        "expectation": expectation,
        "also_evidence": also_evidence,
        "verdict": result.verdict.value,
        "backend": result.backend,
        "status": ic3._status(result, binary),  # noqa: SLF001
        "error": result.error,
        "counterexample_present": bool(result.counterexample),
        "solver_hash": result.solver_hash,
        "invariants": [item.id for item in ir.invariants],
    }
    record["smv_sha256"] = runner.record.get("smv_sha256")
    for key in ("requested_commands", "nuXmv_version", "stdout_sha256", "exit_code", "timed_out", "raw_result_lines"):
        record[key] = runner.record.get(key)
    return record


def build_bundle(*, binary: str = BINARY, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Build the parameter-general bundle: one positive row and its two controls."""
    plan = _load_script("generate_plan_ir_evidence.py")
    case = plan.PLAN_CASES[0]
    effect_case = plan.EFFECT_CASES[0]
    bound = plan.BOUNDS[-1]
    unbounded = plan_ir(case, effect_case, bound, unbounded_step=True)
    positive = probe_row(
        f"plan-ir:{case}:{effect_case}:smt:symbolic-step-bound",
        "plan_ir",
        unbounded,
        expectation="safe",
        symbolic_parameter=(
            "the plan's declared node bound, which stays a constant in the guards while the step "
            "counter itself has no declared range"
        ),
        auxiliary_invariant=(
            "bounded-liveness (step >= bound - 1 -> terminated) together with the transition guard "
            "step <= bound - 1; the property alone is not inductive"
        ),
        route="nuxmv-msat",
        smt=True,
        also_evidence=(
            "notes/ic3-msat-probe.md and notes/induction-probe.md in .conflux-investigation; "
            "writing/unbounded-obstructions.md states which families have no such route"
        ),
        binary=binary,
        timeout=timeout,
    )
    weakened = probe_row(
        "plan-ir:control:weakened-liveness:smt",
        "plan_ir",
        with_weakened_invariant(unbounded),
        expectation="not_safe",
        symbolic_parameter=positive["symbolic_parameter"],
        auxiliary_invariant="none: the liveness implication was replaced by a bare terminated claim",
        route="nuxmv-msat",
        smt=True,
        also_evidence="control row: it shows the route can withhold a verdict rather than always agree",
        binary=binary,
        timeout=timeout,
    )
    bdd = probe_row(
        "plan-ir:control:unbounded-bdd-fail-closed",
        "plan_ir",
        unbounded,
        expectation="unknown_fail_closed",
        symbolic_parameter=positive["symbolic_parameter"],
        auxiliary_invariant="none: this route does not accept an unbounded integer",
        route="nuxmv-ic3",
        smt=False,
        also_evidence="control row: the finite-domain route must refuse the model instead of guessing",
        binary=binary,
        timeout=timeout,
    )
    rows = sorted((positive, weakened, bdd), key=lambda item: item["row_id"])
    by_verdict: dict[str, int] = {}
    by_expectation: dict[str, int] = {}
    for row in rows:
        by_verdict[row["verdict"]] = by_verdict.get(row["verdict"], 0) + 1
        by_expectation[row["expectation"]] = by_expectation.get(row["expectation"], 0) + 1
    return {
        "schema_version": "1",
        "id": OUTPUT.name,
        "source": str(Path(__file__).resolve().relative_to(ROOT)),
        "route": "nuXmv SMT (go_msat + msat_check_invar_bmc)",
        "commands": SMT_COMMANDS,
        "control_commands": BDD_COMMANDS,
        "timeout_seconds": timeout,
        "rows": rows,
        "summary": {
            "total": len(rows),
            "by_verdict": dict(sorted(by_verdict.items())),
            "by_expectation": dict(sorted(by_expectation.items())),
            "positive_rows": [row["row_id"] for row in rows if row["expectation"] == "safe"],
            "control_rows": [row["row_id"] for row in rows if row["expectation"] != "safe"],
            "rows_without_declared_range": [
                row["row_id"] for row in rows if not row["step_counter_has_declared_range"]
            ],
            "errors": [row["row_id"] for row in rows if row["error"] and row["expectation"] == "safe"],
        },
    }


def build_protocol(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return the protocol that describes how the bundle was produced."""
    return {
        "schema_version": "1",
        "id": OUTPUT.name,
        "generator": str(Path(__file__).resolve().relative_to(ROOT)),
        "backend": "conflux.verification.nuxmv_backend.NuXmvBackend(smt=True)",
        "binary": BINARY,
        "commands": SMT_COMMANDS,
        "control_commands": BDD_COMMANDS,
        "timeout_seconds": bundle["timeout_seconds"],
        "claim": (
            "Each positive row is a verdict about a model whose step counter has no declared range, "
            "so the verdict names no bound and no depth. It is not a verdict about a bounded model "
            "and must not be quoted as one."
        ),
        "controls": (
            "A weakened invariant must not be reported safe, and the finite-domain route must fail "
            "closed on an unbounded model. Both controls are retained in the bundle."
        ),
    }


def write_bundle(bundle: dict[str, Any], destination: Path) -> None:
    """Write the bundle, its protocol, and a checksum file."""
    destination.mkdir(parents=True, exist_ok=True)
    result = destination / "result.json"
    protocol = destination / "protocol.json"
    result.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    protocol.write_text(json.dumps(build_protocol(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksums = destination / "CHECKSUMS.sha256"
    checksums.write_text(
        "".join(f"{_sha256_text(path.read_text(encoding='utf-8'))}  {path.name}\n" for path in (result, protocol)),
        encoding="utf-8",
    )


def check(bundle: dict[str, Any]) -> list[str]:
    """Return the differences between the retained bundle and a freshly built one."""
    retained_path = OUTPUT / "result.json"
    if not retained_path.exists():
        return [f"missing retained bundle: {retained_path}"]
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    fresh = {row["row_id"]: row for row in bundle["rows"]}
    problems: list[str] = []
    for row in retained["rows"]:
        current = fresh.get(row["row_id"])
        if current is None:
            problems.append(f"{row['row_id']}: missing from the fresh run")
            continue
        for key in ("verdict", "status", "smv_sha256", "expectation"):
            if row[key] != current[key]:
                problems.append(f"{row['row_id']}: {key} {row[key]!r} != {current[key]!r}")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Generate the bundle, or check the retained one, and report what happened."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare a fresh run with the retained bundle")
    parser.add_argument("--binary", default=BINARY, help="nuXmv binary to run")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="seconds per model")
    arguments = parser.parse_args(argv)
    binary = arguments.binary
    if shutil.which(binary) is None and not Path(binary).exists():
        print(f"nuXmv binary not found: {binary}; rows will record status nuxmv_unavailable", flush=True)
    bundle = build_bundle(binary=binary, timeout=arguments.timeout)
    for row in bundle["rows"]:
        print(f"{row['status']:18s} {row['verdict']:8s} {row['row_id']} (expect {row['expectation']})", flush=True)
    if arguments.check:
        problems = check(bundle)
        for problem in problems:
            print(f"MISMATCH {problem}", flush=True)
        print(f"checked: {len(problems)} problem(s)", flush=True)
        return 1 if problems else 0
    write_bundle(bundle, OUTPUT)
    print(f"wrote {OUTPUT.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
