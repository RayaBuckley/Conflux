"""Deterministic evidence packaging for verification COI reduction."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
from pathlib import Path
from typing import Callable, cast

from conflux.domain import canonical_json, fingerprint
from conflux.verification import (
    FormalVerdict,
    FormalVerificationResult,
    NuXmvBackend,
    VerificationIR,
    compare_cone_of_influence,
    verify_with_z3,
)

from .protocol import ExperimentProtocol, ResolvedRunManifest, RunFailure

ROOT = Path(__file__).resolve().parents[3]
CANONICAL_OUTPUT = Path("runs/sled-coi-reduction-v1")
COI_EVIDENCE_ROOT_FILES = (
    "CHECKSUMS.sha256",
    "RERUN.txt",
    "manifest.json",
    "protocol.json",
    "raw-results.jsonl",
    "result.json",
    "table.md",
)


def generate_coi_evidence_bundle(source_commit: str, output: Path) -> tuple[Path, ...]:
    """Generate original/reduced models and normalized comparison evidence."""

    fixture_paths = tuple(sorted((ROOT / "experiments/suites/sled-coi-v1").glob("*.json")))
    protocol = _protocol(source_commit, fixture_paths)
    output.mkdir(parents=True, exist_ok=True)
    protocol.materialise(output)
    original_directory = output / "models" / "original"
    reduced_directory = output / "models" / "reduced"
    original_directory.mkdir(parents=True, exist_ok=True)
    reduced_directory.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    failures: list[RunFailure] = []
    equivalent = 0
    measurable = 0
    available_backends: set[str] = set()
    for path in fixture_paths:
        ir = VerificationIR.from_dict(_load_json(path))
        comparison = compare_cone_of_influence(ir, ())
        original_path = original_directory / f"{ir.id}.json"
        reduced_path = reduced_directory / f"{ir.id}.json"
        _write_json(original_path, ir.to_dict())
        _write_json(reduced_path, comparison.reduction.reduced_ir.to_dict())
        backend_results, backend_failures = _formal_comparisons(
            ir,
            comparison.reduction.reduced_ir,
        )
        failures.extend(RunFailure("verification", failure, ir.id) for failure in backend_failures)
        metrics: dict[str, int] = {
            "original_variables": len(ir.variables),
            "reduced_variables": len(comparison.reduction.reduced_ir.variables),
            "original_rules": len(ir.transitions),
            "reduced_rules": len(comparison.reduction.reduced_ir.transitions),
            "original_states": comparison.original.states,
            "reduced_states": comparison.reduced.states,
        }
        row: dict[str, object] = {
            "fixture_id": ir.id,
            "reference": comparison.to_dict(),
            "formal_backends": backend_results,
            "metrics": metrics,
        }
        rows.append(row)
        equivalent += int(comparison.equivalent)
        measurable += int(
            any(
                metrics[left] > metrics[right]
                for left, right in (
                    ("original_variables", "reduced_variables"),
                    ("original_rules", "reduced_rules"),
                    ("original_states", "reduced_states"),
                )
            )
        )
        for name, value in backend_results.items():
            if cast(dict[str, object], value).get("available") is True:
                available_backends.add(name)
    complete = equivalent == len(rows) and measurable > 0 and not failures
    result = {
        "schema_version": "1",
        "id": "sled-coi-reduction-v1",
        "protocol_fingerprint": protocol.fingerprint,
        "complete": complete,
        "summary": {
            "fixtures": len(rows),
            "reference_verdict_agreements": equivalent,
            "fixtures_with_measurable_reduction": measurable,
            "available_formal_backends": sorted(available_backends),
        },
        "fixtures": rows,
        "failures": [failure.to_dict() for failure in failures],
    }
    _write_json(output / "result.json", result)
    (output / "raw-results.jsonl").write_text(
        "".join(
            canonical_json(
                {
                    "sequence": index,
                    "event_type": "coi_reduction_comparison",
                    **row,
                }
            )
            + "\n"
            for index, row in enumerate(rows)
        ),
        encoding="utf-8",
        newline="\n",
    )
    (output / "table.md").write_text(_table(rows), encoding="utf-8", newline="\n")
    content_paths = tuple(
        sorted(path for path in output.rglob("*") if path.is_file() and path.name not in {"CHECKSUMS.sha256", "manifest.json"})
    )
    checksums = {path.relative_to(output).as_posix(): _file_sha256(path) for path in content_paths}
    manifest = ResolvedRunManifest(
        run_id=fingerprint({"protocol": protocol.fingerprint, "result": checksums["result.json"]}),
        track="verification_reduction",
        protocol_fingerprint=protocol.fingerprint,
        source_commit=source_commit,
        status="complete" if complete else "incomplete",
        complete=complete,
        exclusions=(
            "unavailable optional formal backends are not treated as successful runs",
            "wall-clock and peak-memory measurements are omitted for determinism",
        ),
        failures=tuple(failures),
        environment={
            "execution": "offline_serialisable_ir",
            "reference_interpreter": "conflux.verification.v1",
            "python": "3.12+",
        },
        checksums=checksums,
    )
    _write_json(output / "manifest.json", manifest.to_dict())
    _write_checksums(output)
    return tuple(path for path in sorted(output.rglob("*")) if path.is_file())


def compare_coi_evidence_bundle(expected: Path, regenerated: Path) -> tuple[str, ...]:
    expected_files = {path.relative_to(expected).as_posix(): path for path in expected.rglob("*") if path.is_file()}
    regenerated_files = {path.relative_to(regenerated).as_posix(): path for path in regenerated.rglob("*") if path.is_file()}
    changed = set(expected_files) ^ set(regenerated_files)
    for name in set(expected_files) & set(regenerated_files):
        if _canonical_bytes(expected_files[name]) != _canonical_bytes(regenerated_files[name]):
            changed.add(name)
    return tuple(sorted(changed))


def verify_coi_evidence_checksums(directory: Path) -> tuple[str, ...]:
    checksum_file = directory / "CHECKSUMS.sha256"
    if not checksum_file.is_file():
        return ("CHECKSUMS.sha256",)
    errors: set[str] = set()
    indexed: set[str] = set()
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, separator, name = line.partition("  ")
        path = directory / name
        if not separator or name in indexed or not path.is_file():
            errors.add(name or line)
            continue
        indexed.add(name)
        if _file_sha256(path) != expected:
            errors.add(name)
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file() and path.name != "CHECKSUMS.sha256"}
    errors.update(actual ^ indexed)
    return tuple(sorted(errors))


def _formal_comparisons(
    original: VerificationIR,
    reduced: VerificationIR,
    *,
    discover_optional: bool = False,
) -> tuple[dict[str, object], tuple[str, ...]]:
    z3_available = importlib.util.find_spec("z3") is not None if discover_optional else False
    nuxmv_available = shutil.which("nuXmv") is not None if discover_optional else False
    adapters: tuple[tuple[str, bool, Callable[[VerificationIR], FormalVerificationResult]], ...] = (
        ("z3", z3_available, verify_with_z3),
        ("nuxmv", nuxmv_available, NuXmvBackend().verify),
    )
    results: dict[str, object] = {}
    failures: list[str] = []
    for name, available, verify in adapters:
        if not available:
            results[name] = {"available": False, "reason": "unavailable"}
            continue
        original_result = verify(original)
        reduced_result = verify(reduced)
        equivalent = original_result.verdict != FormalVerdict.UNKNOWN and original_result.verdict == reduced_result.verdict
        results[name] = {
            "available": True,
            "equivalent": equivalent,
            "original": original_result.to_dict(),
            "reduced": reduced_result.to_dict(),
        }
        if not equivalent:
            failures.append(f"{name}_verdict_comparison_failed")
    return results, tuple(failures)


def _protocol(source_commit: str, paths: tuple[Path, ...]) -> ExperimentProtocol:
    return ExperimentProtocol(
        id="sled-coi-reduction-v1",
        track="verification_reduction",
        suite={"id": "sled-coi", "version": "1"},
        source_commit=source_commit,
        inputs={path.relative_to(ROOT).as_posix(): _file_sha256(path) for path in paths},
        model=None,
        prompts={},
        seeds=(0,),
        repetitions=1,
        bounds={"max_depth": 4, "max_states": 64, "max_transitions": 256},
        environment={"network": "disabled", "optional_backends": "discover_only"},
        output_directory=CANONICAL_OUTPUT.as_posix(),
        rerun_command=(
            "python",
            "scripts/generate_coi_evidence.py",
            CANONICAL_OUTPUT.as_posix(),
            "--source-commit",
            source_commit,
        ),
    )


def _table(rows: list[dict[str, object]]) -> str:
    lines = [
        "# SLED COI reduction v1",
        "",
        "| Fixture | Verdict | Variables | Rules | States | Witness lifted |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        comparison = cast(dict[str, object], row["reference"])
        original = cast(dict[str, object], comparison["original"])
        reduction = cast(dict[str, object], comparison["reduction"])
        witness_lifting = cast(dict[str, object], reduction["witness_lifting"])
        metrics = cast(dict[str, int], row["metrics"])
        lines.append(
            f"| {row['fixture_id']} | {original['verdict']} | "
            f"{metrics['original_variables']} -> {metrics['reduced_variables']} | "
            f"{metrics['original_rules']} -> {metrics['reduced_rules']} | "
            f"{metrics['original_states']} -> {metrics['reduced_states']} | "
            f"{witness_lifting['validated']} |"
        )
    return "\n".join((*lines, "", "Values derive only from `result.json`.", ""))


def _write_checksums(output: Path) -> None:
    paths = tuple(sorted(path for path in output.rglob("*") if path.is_file() and path.name != "CHECKSUMS.sha256"))
    (output / "CHECKSUMS.sha256").write_text(
        "".join(f"{_file_sha256(path)}  {path.relative_to(output).as_posix()}\n" for path in paths),
        encoding="utf-8",
        newline="\n",
    )


def _load_json(path: Path) -> object:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")


def _canonical_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest()


__all__ = [
    "COI_EVIDENCE_ROOT_FILES",
    "compare_coi_evidence_bundle",
    "generate_coi_evidence_bundle",
    "verify_coi_evidence_checksums",
]
