"""Deterministic, manifest-driven job expansion and safe resumption."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from conflux.domain import canonical_json, fingerprint

from .manifest import ExperimentManifest

_SECRET_MARKERS = ("api_key", "password", "secret", "token", "credential")


@dataclass(frozen=True, slots=True)
class ExperimentCase:
    index: int
    case_id: str
    seed: int
    manifest_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1",
            "index": self.index,
            "case_id": self.case_id,
            "seed": self.seed,
            "manifest_fingerprint": self.manifest_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ResumePlan:
    pending: tuple[ExperimentCase, ...]
    completed: tuple[ExperimentCase, ...]
    rejected_markers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1",
            "pending": [case.to_dict() for case in self.pending],
            "completed": [case.to_dict() for case in self.completed],
            "rejected_markers": list(self.rejected_markers),
        }


def expand_cases(manifest: ExperimentManifest) -> tuple[ExperimentCase, ...]:
    """Expand explicit cases with a stable index-to-seed mapping."""
    assert_manifest_has_no_secrets(manifest)
    raw_cases = manifest.bounds.get("cases", manifest.model.get("cases", ()))
    if not isinstance(raw_cases, (list, tuple)) or not raw_cases:
        raw_cases = (manifest.id,)
    if any(not isinstance(case_id, str) or not case_id for case_id in raw_cases):
        raise ValueError("experiment cases must be non-empty strings")
    if len(set(raw_cases)) != len(raw_cases):
        raise ValueError("experiment cases must be unique")
    cases = cast(tuple[str, ...] | list[str], raw_cases)
    return tuple(
        ExperimentCase(index, case_id, manifest.seed + index, manifest.fingerprint)
        for index, case_id in enumerate(cases)
    )


def plan_resume(manifest: ExperimentManifest, output: Path) -> ResumePlan:
    pending: list[ExperimentCase] = []
    completed: list[ExperimentCase] = []
    rejected: list[str] = []
    for case in expand_cases(manifest):
        marker = output / case.case_id / "complete.json"
        if not marker.exists():
            pending.append(case)
            continue
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            rejected.append(case.case_id)
            pending.append(case)
            continue
        if not isinstance(payload, dict) or not _valid_marker(case, cast(dict[str, object], payload)):
            rejected.append(case.case_id)
            pending.append(case)
            continue
        completed.append(case)
    return ResumePlan(tuple(pending), tuple(completed), tuple(rejected))


def materialise_jobs(manifest: ExperimentManifest, output: Path) -> ResumePlan:
    """Write self-contained pending job records without executing them."""
    plan = plan_resume(manifest, output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(
        canonical_json(manifest.to_dict()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    jobs = output / "jobs"
    jobs.mkdir(exist_ok=True)
    for case in plan.pending:
        (jobs / f"{case.index:05d}.json").write_text(
            canonical_json(case.to_dict()) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    (output / "resume-plan.json").write_text(
        canonical_json(plan.to_dict()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return plan


def completion_marker(case: ExperimentCase, result_sha256: str) -> dict[str, object]:
    if len(result_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in result_sha256
    ):
        raise ValueError("result checksum must be lowercase SHA-256")
    payload: dict[str, object] = {
        "schema_version": "1",
        "case_id": case.case_id,
        "seed": case.seed,
        "manifest_fingerprint": case.manifest_fingerprint,
        "result_sha256": result_sha256,
        "status": "complete",
    }
    payload["marker_fingerprint"] = fingerprint(payload)
    return payload


def assert_manifest_has_no_secrets(manifest: ExperimentManifest) -> None:
    def inspect(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                lowered = str(key).lower()
                allowed_marker = item is None or item in ("environment-only", "unavailable")
                if any(marker in lowered for marker in _SECRET_MARKERS) and not allowed_marker:
                    raise ValueError(f"manifest may not contain secret material:{path}.{key}")
                inspect(item, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                inspect(item, f"{path}[{index}]")

    inspect(manifest.to_dict(), "manifest")


def _valid_marker(case: ExperimentCase, payload: dict[str, object]) -> bool:
    candidate = dict(payload)
    marker_fingerprint = candidate.pop("marker_fingerprint", None)
    return (
        candidate.get("schema_version") == "1"
        and candidate.get("case_id") == case.case_id
        and candidate.get("seed") == case.seed
        and candidate.get("manifest_fingerprint") == case.manifest_fingerprint
        and candidate.get("status") == "complete"
        and isinstance(candidate.get("result_sha256"), str)
        and marker_fingerprint == fingerprint(candidate)
    )


__all__ = [
    "ExperimentCase",
    "ResumePlan",
    "assert_manifest_has_no_secrets",
    "completion_marker",
    "expand_cases",
    "materialise_jobs",
    "plan_resume",
]
