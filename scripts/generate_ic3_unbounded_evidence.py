"""IC3 (nuXmv ``check_invar_ic3``) evidence over the recorded finite-IR families.

Every model in this bundle is a finite Boolean IR built by an existing Conflux
generator or shipped in ``research/experiments``.  The bundle records the
nuXmv IC3 outcome for each model: the verdict, the rendered model hash, the
hash of nuXmv's own output, and the invariant lines that decide the verdict.

Scope and honesty rules enforced here:

* A verdict is about the bounded model that was rendered.  ``ir_bound`` is
  recorded per model; families whose bound grows with a scaling parameter are
  bounded by that value, not unbounded.
* The native-SLED explicit-state families have no IR and are absent.
* A refutation records the state count of every execution sequence nuXmv
  printed, one count per refuted invariant (``witness_lengths``); n states
  reach the violation after n - 1 transitions.  A model that prints no
  sequence records an empty list, so no length is claimed without a trace,
  and no printed trace is claimed to be the shortest.
* When nuXmv is missing or a model errors, the run records no verdict.
* Models with no variables or no transitions are listed in ``trivial_models``
  and no verdict is recorded for them: ``_smv`` refuses to render a model with
  no transition rules. Rows whose invariants are all ``checked_by_construction``
  are listed in ``unexercised_rows``; their verdict is decided by the initial
  state alone.

Usage::

    python scripts/generate_ic3_unbounded_evidence.py
    python scripts/generate_ic3_unbounded_evidence.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "ic3-unbounded-v1"
COMMANDS = "go\nbuild_boolean_model\ncheck_invar_ic3\nquit\n"
BINARY = "nuXmv"
DEFAULT_TIMEOUT_SECONDS = 300.0

from conflux.verification.ir import VerificationIR  # noqa: E402
from conflux.verification.nuxmv_backend import NuXmvBackend, NuXmvOutcome, _render, _smv  # noqa: E402
from conflux.verification.reduction import compare_cone_of_influence  # noqa: E402
from conflux.verification.sensitivity import CLASS_CHECKED_BY_CONSTRUCTION, classify_ir  # noqa: E402


class RecordingNuXmvRunner:
    """``SubprocessNuXmvRunner`` shape that keeps the rendered model and raw output."""

    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        self.record: dict[str, Any] = {}

    def run(self, binary: str, model_path: Path, commands: str) -> NuXmvOutcome:
        """Run nuXmv on the rendered model and record what it printed."""
        smv_text = model_path.read_text(encoding="utf-8")
        version_probe = subprocess.run((binary, "-h"), check=False, capture_output=True, text=True, timeout=10, shell=False)
        version_lines = (version_probe.stdout or version_probe.stderr).splitlines()
        version = version_lines[0] if version_lines else "unknown"
        started = time.perf_counter()
        timed_out = False
        try:
            process = subprocess.run(
                (binary, "-int", str(model_path)),
                input=commands,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                shell=False,
            )
            elapsed = time.perf_counter() - started
            stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired as error:
            elapsed = time.perf_counter() - started
            timed_out = True
            stdout = (error.stdout or b"").decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
            stderr = (error.stderr or b"").decode("utf-8", "replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
            exit_code = 124
        self.record.update(
            {
                "smv_sha256": _sha256_text(smv_text),
                "requested_commands": commands,
                "nuXmv_version": version,
                "stdout_sha256": _sha256_text(stdout + "\n" + stderr),
                "exit_code": exit_code,
                "timed_out": timed_out,
                "seconds": round(elapsed, 6),
                "raw_result_lines": [
                    line.strip()
                    for line in stdout.splitlines()
                    if line.strip().startswith("-- invariant") or " is true" in line or " is false" in line
                ][:12],
            },
        )
        return NuXmvOutcome(exit_code, stdout, stderr, version)


def _witness_lengths(result: Any) -> list[int]:
    """Return the per-refutation witness lengths recorded on the result, or an empty list."""
    for entry in result.counterexample:
        if isinstance(entry, dict) and "witness_lengths" in entry:
            return [int(value) for value in entry["witness_lengths"]]
    return []


def _status(result: Any, binary: str) -> str:
    """Return the run status, which never overstates an outcome."""
    error = result.error or ""
    if error.startswith("optional_binary_unavailable") or shutil.which(binary) is None:
        return "nuxmv_unavailable"
    if error:
        return "error"
    if result.verdict.value == "unknown":
        return "unknown"
    return "complete"


def _rendered_sha256(ir: VerificationIR, recorded: str | None) -> str | None:
    """Return the rendered-model hash, rendering the model when the runner did not run."""
    if recorded is not None:
        return recorded
    try:
        return _sha256_text(_smv(ir))
    except ValueError:
        return None


def probe_model(
    row_id: str,
    family: str,
    source: str,
    ir: VerificationIR,
    timeout: float,
    notes: str = "",
    binary: str = BINARY,
) -> dict[str, Any]:
    """Verify one IR and return its retained record."""
    runner = RecordingNuXmvRunner(timeout)
    backend = NuXmvBackend(binary=binary, runner=runner)
    result = backend.verify(ir)
    record: dict[str, Any] = {
        "row_id": row_id,
        "family": family,
        "source": source,
        "model_id": ir.id,
        "ir_fingerprint": ir.fingerprint,
        "ir_bound": ir.bound,
        "variables": len(ir.variables),
        "rules": len(ir.transitions),
        "invariants": [item.id for item in ir.invariants],
        "invariant_classes": {item.invariant_id: item.exercise_class for item in classify_ir(ir)},
        "properties_rendered": [_render(item.expression) for item in ir.invariants],
        "verdict": result.verdict.value,
        "backend": result.backend,
        "status": _status(result, binary),
        "error": result.error,
        "counterexample_present": bool(result.counterexample),
        "witness_lengths": _witness_lengths(result),
        "solver_hash": result.solver_hash,
        "notes": notes,
    }
    record["smv_sha256"] = _rendered_sha256(ir, runner.record.get("smv_sha256"))
    for key in ("requested_commands", "nuXmv_version", "stdout_sha256", "exit_code", "timed_out", "raw_result_lines"):
        if key in runner.record:
            record[key] = runner.record[key]
    return record


def _load_script(name: str) -> Any:
    """Load a sibling script by path, as its documented invocation does."""
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _reduced(ir: VerificationIR) -> VerificationIR:
    return compare_cone_of_influence(ir, ()).reduction.reduced_ir


def _family_defence() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    from conflux.verification import defence_models

    factories = [
        ("Dual-LLM", "pe", defence_models.dual_llm_baseline_ir),
        ("Dual-LLM", "native", defence_models.dual_llm_native_property_ir),
        ("CaMeL", "pe", defence_models.camel_ir),
        ("CaMeL", "native", defence_models.camel_native_property_ir),
        ("Progent", "pe", defence_models.progent_ir),
        ("Progent", "native", defence_models.progent_native_property_ir),
        ("PACT", "pe", defence_models.pact_ir),
        ("PACT", "native", defence_models.pact_native_property_ir),
        ("Requester-only", "pe", defence_models.ites_defective_requester_only_ir),
        ("ITES", "pe", defence_models.ites_reference_ir),
    ]
    for model, kind, factory in factories:
        ir = factory()
        yield (f"defence:{model}:{kind}", "defence-models-v1", f"conflux.verification.defence_models.{factory.__name__}", ir, "")


def _family_delegation_variants() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    from conflux.verification.delegation_ir import all_delegation_ir_variants

    for variant in all_delegation_ir_variants():
        yield (
            f"delegation-variant:{variant.ir.id}",
            "three-way-agreement-v1",
            "conflux.verification.delegation_ir.all_delegation_ir_variants",
            variant.ir,
            f"mutation={variant.mutation.value}",
        )


def _family_delegation_defects() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    sweep = _load_script("generate_delegation_defect_sweep.py")

    for defects in sweep.defect_subsets():
        ir = sweep.build_combined_delegation_ir(defects)
        names = ",".join(sorted(d.value for d in defects)) or "none"
        yield (
            f"delegation-defect:{names}",
            "delegation-defect-sweep-v1",
            "scripts.generate_delegation_defect_sweep.build_combined_delegation_ir",
            ir,
            f"defect_count={len(defects)}",
        )


def _family_sledv_scaling() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    scaling = _load_script("generate_sledv_scaling_evidence.py")
    builders = [
        ("noise", "safe", scaling._safe_noise_fixture, scaling.NOISE_COUNTS),  # noqa: SLF001
        ("noise", "unsafe", scaling._unsafe_noise_fixture, scaling.NOISE_COUNTS),  # noqa: SLF001
        ("principal", "safe", scaling._safe_principal_fixture, scaling.PRINCIPAL_COUNTS),  # noqa: SLF001
        ("principal", "unsafe", scaling._unsafe_principal_fixture, scaling.PRINCIPAL_COUNTS),  # noqa: SLF001
        ("depth", "safe", scaling._safe_depth_fixture, scaling.DEPTH_VALUES),  # noqa: SLF001
        ("depth", "unsafe", scaling._unsafe_depth_fixture, scaling.DEPTH_VALUES),  # noqa: SLF001
    ]
    for kind, safety, builder, values in builders:
        for value in values:
            ir = VerificationIR.from_dict(builder(value))
            base = f"sledv-scaling:{kind}-{safety}-{value}"
            yield (
                base,
                "sledv-scaling-v1",
                f"scripts.generate_sledv_scaling_evidence.{builder.__name__}",
                ir,
                f"family={kind}_scaling value={value} safety={safety}",
            )
    for kind, safety, builder, values in builders:
        for value in values:
            ir = VerificationIR.from_dict(builder(value))
            base = f"sledv-scaling:{kind}-{safety}-{value}:coi-reduced"
            yield (
                base,
                "sledv-scaling-v1-coi-reduced",
                f"scripts.generate_sledv_scaling_evidence.{builder.__name__}+COI",
                _reduced(ir),
                f"family={kind}_scaling value={value} safety={safety} coi_reduced=yes",
            )


def _family_coi_scaling() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    scaling = _load_script("generate_coi_scaling.py")
    builders = [("safe", scaling._safe_noise_fixture), ("unsafe", scaling._unsafe_control_fixture)]  # noqa: SLF001
    for kind, builder in builders:
        for n in scaling.NOISE_COUNTS:
            ir = VerificationIR.from_dict(builder(n))
            yield (f"coi-scaling:{kind}-noise-{n}", "coi-scaling-v1", f"scripts.generate_coi_scaling.{builder.__name__}", ir, f"noise={n}")
    for kind, builder in builders:
        for n in scaling.NOISE_COUNTS:
            ir = VerificationIR.from_dict(builder(n))
            yield (
                f"coi-scaling:{kind}-noise-{n}:coi-reduced",
                "coi-scaling-v1-coi-reduced",
                f"scripts.generate_coi_scaling.{builder.__name__}+COI",
                _reduced(ir),
                f"noise={n} coi_reduced=yes",
            )


def _family_sled_coi_reduction() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    for path in sorted((ROOT / "research" / "experiments" / "suites" / "sled-coi-v1").glob("*.json")):
        ir = VerificationIR.from_dict(json.loads(path.read_text(encoding="utf-8")))
        yield (f"sled-coi:{ir.id}", "sled-coi-reduction-v1", f"research/experiments/suites/sled-coi-v1/{path.name}", ir, "")
    for path in sorted((ROOT / "research" / "experiments" / "suites" / "sled-coi-v1").glob("*.json")):
        ir = VerificationIR.from_dict(json.loads(path.read_text(encoding="utf-8")))
        yield (
            f"sled-coi:{ir.id}:coi-reduced",
            "sled-coi-reduction-v1-coi-reduced",
            f"research/experiments/suites/sled-coi-v1/{path.name}+COI",
            _reduced(ir),
            "coi_reduced=yes",
        )


def _plan_ir(plan: Any, case: str, effect_case: str, bound: int) -> VerificationIR:
    """Rebuild the plan abstraction IR exactly as scripts/generate_plan_ir_evidence._row does."""
    from conflux.domain import Principal, Provenance
    from conflux.planning import OperationCatalogue
    from conflux.verification import abstract_plan

    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="evidence")
    write, code = plan._operations()  # noqa: SLF001
    built = plan._build_plan(case, source, write, code)  # noqa: SLF001
    abstraction = abstract_plan(
        built,
        catalogue=OperationCatalogue((write, code)),
        effect_summaries=plan._summaries(case, built, effect_case),  # noqa: SLF001
        bound=bound,
    )
    if abstraction.ir is None:
        raise RuntimeError(f"plan abstraction unsupported: {list(abstraction.unsupported)}")
    return abstraction.ir


def _family_plan_ir() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    plan = _load_script("generate_plan_ir_evidence.py")
    for case in plan.PLAN_CASES:
        for effect_case in plan.EFFECT_CASES:
            for bound in plan.BOUNDS:
                ir = _plan_ir(plan, case, effect_case, bound)
                yield (
                    f"plan-ir:{case}:{effect_case}:b{bound}",
                    "plan_ir",
                    "scripts.generate_plan_ir_evidence._row (IR rebuilt by probe)",
                    ir,
                    f"expectation={plan.EXPECTATIONS.get((case, effect_case))}",
                )


def _family_plan_ir_coi() -> Iterator[tuple[str, str, str, VerificationIR, str]]:
    plan = _load_script("generate_plan_ir_evidence.py")
    for case in plan.PLAN_CASES:
        for effect_case in plan.EFFECT_CASES:
            for bound in plan.BOUNDS:
                ir = _plan_ir(plan, case, effect_case, bound)
                yield (
                    f"plan-ir:{case}:{effect_case}:b{bound}:coi-reduced",
                    "plan_ir-coi-reduced",
                    "scripts.generate_plan_ir_evidence._row (IR rebuilt by probe)+COI",
                    _reduced(ir),
                    f"expectation={plan.EXPECTATIONS.get((case, effect_case))} coi_reduced=yes",
                )


FAMILIES: dict[str, Callable[[], Iterator[tuple[str, str, str, VerificationIR, str]]]] = {
    "defence": _family_defence,
    "delegation-variants": _family_delegation_variants,
    "delegation-defects": _family_delegation_defects,
    "sledv-scaling": _family_sledv_scaling,
    "coi-scaling": _family_coi_scaling,
    "sled-coi-reduction": _family_sled_coi_reduction,
    "plan-ir": _family_plan_ir,
    "plan-ir-coi": _family_plan_ir_coi,
}


def generate(
    families: tuple[str, ...] | None = None,
    binary: str = BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Verify every model of every selected family and return the bundle."""
    selected = families if families is not None else tuple(FAMILIES)
    models: list[dict[str, Any]] = []
    for name in selected:
        for row_id, family, source, ir, notes in FAMILIES[name]():
            record = probe_model(row_id, family, source, ir, timeout, notes, binary)
            models.append(record)
            print(f"{record['status']:18s} {record['verdict']:8s} {row_id}", flush=True)
    models.sort(key=lambda item: item["row_id"])
    by_status: dict[str, int] = {}
    by_verdict: dict[str, int] = {}
    by_family: dict[str, int] = {}
    for model in models:
        by_status[model["status"]] = by_status.get(model["status"], 0) + 1
        by_verdict[model["verdict"]] = by_verdict.get(model["verdict"], 0) + 1
        by_family[model["family"]] = by_family.get(model["family"], 0) + 1
    return {
        "schema_version": "1",
        "id": OUTPUT.name,
        "source": str(Path(__file__).resolve().relative_to(ROOT)),
        "backend": "nuXmv-check_invar_ic3",
        "commands": COMMANDS,
        "timeout_seconds": timeout,
        "families": list(selected),
        "models": models,
        "summary": {
            "total": len(models),
            "by_status": dict(sorted(by_status.items())),
            "by_verdict": dict(sorted(by_verdict.items())),
            "by_family": dict(sorted(by_family.items())),
            "unique_ir_fingerprints": len({model["ir_fingerprint"] for model in models}),
            "unique_smv_sha256": len({model["smv_sha256"] for model in models if model["smv_sha256"]}),
            "trivial_models": [model["row_id"] for model in models if not model["variables"] or not model["rules"]],
            "unexercised_rows": [
                model["row_id"]
                for model in models
                if model["invariant_classes"] and set(model["invariant_classes"].values()) == {CLASS_CHECKED_BY_CONSTRUCTION}
            ],
            "errors": [model["row_id"] for model in models if model["error"]],
        },
    }


def build_protocol(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return the protocol that describes how the bundle was produced."""
    return {
        "schema_version": "1",
        "id": OUTPUT.name,
        "generator": str(Path(__file__).resolve().relative_to(ROOT)),
        "backend": "conflux.verification.nuxmv_backend.NuXmvBackend",
        "commands": COMMANDS,
        "binary": BINARY,
        "timeout_seconds": bundle["timeout_seconds"],
        "families": bundle["families"],
        "nuXmv_version": sorted({model.get("nuXmv_version") for model in bundle["models"] if model.get("nuXmv_version")}),
        "scope": [
            "Every model is a finite Boolean IR rendered by _smv and checked with check_invar_ic3.",
            "ir_bound is retained per model; a verdict covers that bounded model only.",
            "Families whose bound grows with a scaling parameter are bounded by the recorded parameter value.",
            "The native-SLED explicit-state families define no IR and are absent from this bundle.",
        ],
        "witness_rule": (
            "For each refuted invariant nuXmv's IC3 prints an execution sequence; witness_lengths records the number "
            "of states in each printed sequence, so a length of n means the violation is reached after n - 1 "
            "transitions. An empty list means nuXmv printed no sequence, so no length is claimed. The count describes "
            "the printed trace only and is not an independent proof that the trace is shortest."
        ),
        "unavailable_rule": ("When nuXmv is missing or a model errors, status is nuxmv_unavailable or error and no verdict is claimed."),
        "vacuous_rule": (
            "Models with no variables or no transitions are listed in summary.trivial_models and no verdict is recorded "
            "for them: _smv refuses to render a model with no transition rules, so the run records UNKNOWN with "
            "unsupported_ir. Rows whose invariants are all checked_by_construction under the declared mutation alphabet "
            "(scripts/property_sensitivity.py, SEM-017) are listed in summary.unexercised_rows: a safety verdict over "
            "such a row is decided by the initial state alone and proves nothing about the family it names. Every row "
            "also records invariant_classes so either list can be audited from the file alone."
        ),
        "check_semantics": (
            "--check re-runs every model and compares result.json and protocol.json byte for byte. No timing and no "
            "outside path is retained, so the comparison is timing independent."
        ),
        "negated_claims": [
            "This bundle does not prove any unbounded-system property; it reports bounded IC3 verdicts.",
            "This bundle does not claim that any printed nuXmv trace is shortest, and lifts no witness beyond the printed state count.",
            "This bundle is not an AgentDojo or benchmark result.",
        ],
    }


def _write_bundle(output: Path, bundle: dict[str, Any], protocol: dict[str, Any]) -> None:
    """Write the bundle and its checksums."""
    output.mkdir(parents=True, exist_ok=True)
    (output / "result.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output / "protocol.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    names = ["result.json", "protocol.json"]
    checksums = "".join(f"{_sha256((output / name).read_bytes())}  {name}\n" for name in names)
    (output / "CHECKSUMS.sha256").write_text(checksums, encoding="utf-8", newline="\n")
    print(f"wrote {output}: {sum((output / name).stat().st_size for name in names)} bytes", flush=True)


def check(output: Path) -> bool:
    """Re-run the bundle and report whether the retained bytes still reproduce."""
    result_path = output / "result.json"
    protocol_path = output / "protocol.json"
    if not result_path.is_file() or not protocol_path.is_file():
        return False
    bundle = generate()
    protocol = build_protocol(bundle)
    if result_path.read_text(encoding="utf-8") != json.dumps(bundle, indent=2, sort_keys=True) + "\n":
        return False
    return protocol_path.read_text(encoding="utf-8") == json.dumps(protocol, indent=2, sort_keys=True) + "\n"


def main() -> int:
    """Run the IC3 evidence generator."""
    parser = argparse.ArgumentParser(description="Generate the IC3 evidence bundle.")
    parser.add_argument("--check", action="store_true", help="Verify the retained bundle matches regeneration.")
    parser.add_argument("--families", default="", help="Comma separated family subset.")
    parser.add_argument("--limit", type=int, default=0, help="Cap the models per family (smoke runs only).")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Per-model nuXmv timeout.")
    arguments = parser.parse_args()

    if arguments.check:
        if check(OUTPUT):
            print("IC3 evidence regeneration check passed")
            return 0
        print("IC3 evidence is stale or missing", file=sys.stderr)
        return 1

    families = tuple(name for name in arguments.families.split(",") if name) or None
    bundle = generate(families, BINARY, arguments.timeout)
    if arguments.limit:
        bundle["models"] = bundle["models"][: arguments.limit]
    protocol = build_protocol(bundle)
    _write_bundle(OUTPUT, bundle, protocol)
    summary = bundle["summary"]
    print(f"models {summary['total']} | by_verdict {summary['by_verdict']} | by_status {summary['by_status']}")
    print(f"trivial models {len(summary['trivial_models'])} | errors {len(summary['errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
