"""Deterministic retained bundle for offline Cedar evaluation readiness."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import cast

from conflux.domain import canonical_json, fingerprint

from .cedar_preflight import cedar_differential_preflight, load_cedar_bundle, load_cedar_corpus
from .protocol import ExperimentProtocol, ResolvedRunManifest, RunFailure

_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_OUTPUT = Path("runs/cedar-differential-preflight-v1")
CEDAR_EVIDENCE_FILES = frozenset(
    {
        "CHECKSUMS.sha256",
        "RERUN.txt",
        "corpus.json",
        "manifest.json",
        "policy-bundle.json",
        "protocol.json",
        "result.json",
        "table.md",
    }
)


def generate_cedar_preflight_bundle(source_commit: str, output: Path, *, repo_root: Path | None = None) -> None:
    """Generate the offline Cedar preflight evidence bundle into *output*."""
    root = repo_root or _ROOT
    bundle_source = root / "experiments" / "manifests" / "cedar-policy-bundle-v1.json"
    corpus_source = root / "experiments" / "suites" / "cedar-differential-v1.json"
    output.mkdir(parents=True, exist_ok=True)
    bundle = load_cedar_bundle(bundle_source)
    corpus = load_cedar_corpus(corpus_source)
    protocol = ExperimentProtocol(
        id="cedar-differential-preflight-v1",
        track="cedar",
        suite={"id": corpus.id, "version": corpus.schema_version},
        source_commit=source_commit,
        inputs={
            "policy_bundle": _file_sha256(bundle_source),
            "corpus": _file_sha256(corpus_source),
        },
        model=None,
        prompts={},
        seeds=(0,),
        repetitions=1,
        bounds={"max_transitions": corpus.max_requests, "timeout_seconds": 5},
        environment={"network": "disabled", "cedar_binary": "unavailable_not_invoked"},
        output_directory=CANONICAL_OUTPUT.as_posix(),
        rerun_command=(
            "python",
            "scripts/generate_cedar_preflight.py",
            CANONICAL_OUTPUT.as_posix(),
            "--source-commit",
            source_commit,
        ),
    )
    protocol.materialise(output)
    shutil.copyfile(bundle_source, output / "policy-bundle.json")
    shutil.copyfile(corpus_source, output / "corpus.json")
    result = cedar_differential_preflight(bundle, corpus)
    _write_json(output / "result.json", result)
    (output / "table.md").write_text(_table(result), encoding="utf-8", newline="\n")
    checksums = {
        path.name: _file_sha256(path)
        for path in sorted(output.iterdir())
        if path.is_file() and path.name not in {"manifest.json", "CHECKSUMS.sha256"}
    }
    manifest = ResolvedRunManifest(
        run_id=fingerprint({"protocol": protocol.fingerprint, "result": result}),
        track="cedar",
        protocol_fingerprint=protocol.fingerprint,
        source_commit=source_commit,
        status="unavailable",
        complete=False,
        exclusions=tuple(cast(list[str], result["exclusions"])),
        failures=(RunFailure("setup", "optional Cedar CLI not supplied", None),),
        environment={"execution": "offline_preflight", "network": "disabled"},
        checksums=checksums,
    )
    _write_json(output / "manifest.json", manifest.to_dict())
    _write_checksums(output)


def compare_cedar_preflight_bundle(retained: Path, regenerated: Path) -> tuple[str, ...]:
    """Return file names that are missing or differ between two Cedar evidence bundles."""
    names = {path.name for path in retained.iterdir() if path.is_file()} | {path.name for path in regenerated.iterdir() if path.is_file()}
    return tuple(
        name
        for name in sorted(names)
        if not (retained / name).is_file()
        or not (regenerated / name).is_file()
        or _canonical_bytes(retained / name) != _canonical_bytes(regenerated / name)
    )


def verify_cedar_preflight_checksums(output: Path) -> tuple[str, ...]:
    """Return file names whose checksums are missing or mismatched in the bundle."""
    checksum_path = output / "CHECKSUMS.sha256"
    if not checksum_path.is_file():
        return ("CHECKSUMS.sha256",)
    failures: list[str] = []
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", maxsplit=1)
        path = output / name
        if not path.is_file() or _file_sha256(path) != expected:
            failures.append(name)
    actual = {path.name for path in output.iterdir() if path.is_file()}
    failures.extend(sorted(CEDAR_EVIDENCE_FILES - actual))
    return tuple(sorted(set(failures)))


def _table(result: dict[str, object]) -> str:
    rows = cast(list[dict[str, object]], result["cases"])
    lines = [
        "# Cedar differential preflight v1",
        "",
        "| Case | In-memory oracle | Cedar | Requests |",
        "|---|---|---|---:|",
    ]
    lines.extend(
        f"| {row['case_id']} | {'allow' if row['oracle_allowed'] else 'deny'} | unavailable | "
        f"{len(cast(list[object], row['translated_requests']))} |"
        for row in rows
    )
    return "\n".join((*lines, "", "Cedar was not invoked; this table is readiness evidence, not parity evidence.", ""))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")


def _write_checksums(output: Path) -> None:
    paths = tuple(sorted(path for path in output.iterdir() if path.is_file() and path.name != "CHECKSUMS.sha256"))
    (output / "CHECKSUMS.sha256").write_text(
        "".join(f"{_file_sha256(path)}  {path.name}\n" for path in paths),
        encoding="utf-8",
        newline="\n",
    )


def _file_sha256(path: Path) -> str:
    content = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _canonical_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")


__all__ = [
    "CEDAR_EVIDENCE_FILES",
    "compare_cedar_preflight_bundle",
    "generate_cedar_preflight_bundle",
    "verify_cedar_preflight_checksums",
]
