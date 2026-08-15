"""Deterministic retained-evidence packaging for native SLED reproduction."""

from __future__ import annotations

import hashlib
from pathlib import Path

from conflux.domain import canonical_json, fingerprint

from .native_sled import run_native_reproduction
from .protocol import ExperimentProtocol, ResolvedRunManifest

_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_OUTPUT = Path("runs/native-sled-reproduction-v1")
NATIVE_EVIDENCE_FILES = (
    "CHECKSUMS.sha256",
    "RERUN.txt",
    "manifest.json",
    "protocol.json",
    "raw-events.jsonl",
    "result.json",
    "table.md",
)
_CONTENT_FILES = (
    "RERUN.txt",
    "protocol.json",
    "raw-events.jsonl",
    "result.json",
    "table.md",
)


def generate_native_sled_bundle(source_commit: str, output: Path, *, repo_root: Path | None = None) -> tuple[Path, ...]:
    """Generate the complete native bundle from repository fixtures."""

    root = repo_root or _ROOT
    protocol = _protocol(source_commit, root)
    output.mkdir(parents=True, exist_ok=True)
    protocol.materialise(output)
    result = run_native_reproduction(protocol, root)
    _write_json(output / "result.json", result)
    (output / "raw-events.jsonl").write_text(
        _raw_events(result),
        encoding="utf-8",
        newline="\n",
    )
    (output / "table.md").write_text(
        _table(result),
        encoding="utf-8",
        newline="\n",
    )
    checksums = {name: _file_sha256(output / name) for name in _CONTENT_FILES}
    manifest = ResolvedRunManifest(
        run_id=fingerprint(
            {
                "protocol": protocol.fingerprint,
                "result": checksums["result.json"],
            }
        ),
        track="native_sled",
        protocol_fingerprint=protocol.fingerprint,
        source_commit=source_commit,
        status="complete" if result["complete"] else "incomplete",
        complete=bool(result["complete"]),
        exclusions=("wall_clock_and_peak_memory_omitted_for_byte_determinism",),
        failures=(),
        environment={
            "execution": "offline_abstract_state",
            "measurement": "deterministic_fixture",
            "python": "3.12+",
        },
        checksums=checksums,
    )
    _write_json(output / "manifest.json", manifest.to_dict())
    _write_checksum_file(output)
    return tuple(output / name for name in NATIVE_EVIDENCE_FILES)


def compare_native_sled_bundle(expected: Path, regenerated: Path) -> tuple[str, ...]:
    """Return files that are missing or differ after newline normalization."""

    changed = []
    for name in NATIVE_EVIDENCE_FILES:
        retained = expected / name
        candidate = regenerated / name
        if not retained.is_file() or not candidate.is_file():
            changed.append(name)
            continue
        if _canonical_bytes(retained) != _canonical_bytes(candidate):
            changed.append(name)
    return tuple(changed)


def verify_native_sled_checksums(directory: Path) -> tuple[str, ...]:
    """Return malformed, missing, or mismatched checksum entries."""

    checksum_file = directory / "CHECKSUMS.sha256"
    if not checksum_file.is_file():
        return ("CHECKSUMS.sha256",)
    errors = []
    names = set()
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, separator, name = line.partition("  ")
        path = directory / name
        if not separator or name in names or not path.is_file():
            errors.append(name or line)
            continue
        names.add(name)
        if _file_sha256(path) != expected:
            errors.append(name)
    expected_names = set(NATIVE_EVIDENCE_FILES) - {"CHECKSUMS.sha256"}
    errors.extend(sorted(expected_names - names))
    errors.extend(sorted(names - expected_names))
    return tuple(errors)


def _protocol(source_commit: str, root: Path) -> ExperimentProtocol:
    inputs = {
        path.relative_to(root).as_posix(): _file_sha256(path)
        for path in _input_paths(root)
    }
    rerun = (
        "python",
        "scripts/generate_native_sled_evidence.py",
        CANONICAL_OUTPUT.as_posix(),
        "--source-commit",
        source_commit,
    )
    return ExperimentProtocol(
        id="native-sled-reproduction-v1",
        track="native_sled",
        suite={"id": "paired-legacy-canonical", "version": "1"},
        source_commit=source_commit,
        inputs=inputs,
        model=None,
        prompts={},
        seeds=(0,),
        repetitions=1,
        bounds={
            "max_depth": 4,
            "max_states": 1_000,
            "max_transitions": 5_000,
            "max_model_calls": 4,
        },
        environment={
            "execution": "offline_abstract_state",
            "model": "none",
            "provider": "none",
        },
        output_directory=CANONICAL_OUTPUT.as_posix(),
        rerun_command=rerun,
    )


def _input_paths(root: Path) -> tuple[Path, ...]:
    fixtures = tuple(
        sorted((root / "experiments" / "suites" / suite).glob("*.yaml"))
        for suite in ("legacy-reproduction", "canonical")
    )
    return (
        *fixtures[0],
        *fixtures[1],
        root / "experiments" / "baselines" / "sled-historical-v1.json",
    )


def _raw_events(result: dict[str, object]) -> str:
    records: list[dict[str, object]] = []
    sequence = 0
    pairs = result["pairs"]
    if not isinstance(pairs, list):
        raise TypeError("native_result_pairs_invalid")
    for pair in pairs:
        if not isinstance(pair, dict) or not isinstance(pair.get("results"), list):
            raise TypeError("native_result_pair_invalid")
        for row in pair["results"]:
            if not isinstance(row, dict):
                raise TypeError("native_result_row_invalid")
            records.append(
                {
                    "event_type": "sled_defence_result",
                    "pair_id": pair["pair_id"],
                    "sequence": sequence,
                    **row,
                }
            )
            sequence += 1
    controls = result["negative_controls"]
    if not isinstance(controls, list):
        raise TypeError("native_result_controls_invalid")
    for control in controls:
        if not isinstance(control, dict):
            raise TypeError("native_result_control_invalid")
        records.append(
            {
                "event_type": "negative_control_result",
                "sequence": sequence,
                **control,
            }
        )
        sequence += 1
    return "".join(canonical_json(record) + "\n" for record in records)


def _table(result: dict[str, object]) -> str:
    comparison = result["historical_comparison"]
    controls = result["negative_controls"]
    pairs = result["pairs"]
    if not isinstance(comparison, dict) or not isinstance(controls, list) or not isinstance(pairs, list):
        raise TypeError("native_result_summary_invalid")
    return "\n".join(
        (
            "# Native SLED reproduction v1",
            "",
            "| Measure | Retained value |",
            "|---|---:|",
            f"| Paired fixtures | {len(pairs)} |",
            f"| Defective monitors detected | {sum(bool(row['killed']) for row in controls)} / {len(controls)} |",
            f"| Current explored transitions | {comparison['current_transitions']} |",
            f"| Historical trace claim | {comparison['historical_trace_claim']} |",
            f"| Historical comparison valid | {comparison['comparable']} |",
            "",
            "All values are generated from `result.json`. The historical trace claim is retained but not comparable.",
            "",
        )
    )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")


def _write_checksum_file(output: Path) -> None:
    names = tuple(name for name in NATIVE_EVIDENCE_FILES if name != "CHECKSUMS.sha256")
    content = "".join(f"{_file_sha256(output / name)}  {name}\n" for name in names)
    (output / "CHECKSUMS.sha256").write_text(content, encoding="utf-8", newline="\n")


def _canonical_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest()


__all__ = [
    "NATIVE_EVIDENCE_FILES",
    "compare_native_sled_bundle",
    "generate_native_sled_bundle",
    "verify_native_sled_checksums",
]
