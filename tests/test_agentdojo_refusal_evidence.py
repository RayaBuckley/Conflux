"""Offline policy-refusal evidence stays deterministic, checksummed and claim-limited."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from conflux.domain import canonical_json
from conflux.experiments import (
    AGENTDOJO_REFUSAL_EVIDENCE_FILES,
    compare_agentdojo_refusal_evidence_bundle,
    generate_agentdojo_refusal_evidence_bundle,
    verify_agentdojo_refusal_evidence_checksums,
)
from conflux.experiments.agentdojo_refusal_evidence import refusal_record_payload

pytestmark = pytest.mark.reproducibility

GENERATED_FILES = {"CHECKSUMS.sha256", "README.md", "records.json"}


def _generate(tmp_path: Path, name: str = "refusal-record") -> Path:
    output = tmp_path / name
    generate_agentdojo_refusal_evidence_bundle("abcdef0", output)
    return output


def _records(output: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((output / "records.json").read_text(encoding="utf-8")))


def test_bundle_records_the_refusing_rule(tmp_path: Path) -> None:
    """The refused record names the policy rule, and the executed record keeps its certificate."""
    output = _generate(tmp_path)
    payload = _records(output)
    assert payload["classification"] == "adapter_evidence"
    assert payload["complete"] is True
    assert payload["source_commit"] == "abcdef0"
    executed, refused = cast(list[dict[str, Any]], payload["records"])
    assert executed["outcome"] == "executed"
    assert executed["certificate_id"]
    assert refused["outcome"] == "blocked"
    assert refused["reason"] == "principal_denied"
    assert refused["policy_id"] == "in-memory-authorisation"
    assert refused["policy_dimension"] == "authorisation"
    assert "certificate_id" not in refused
    assert payload["adapter_refusal_vocabulary"] == ["unsupported_arguments", "unsupported_tool"]


def test_bundle_asserts_its_own_checks(tmp_path: Path) -> None:
    """Every retained check is a Boolean, and all of them hold in the pinned scenario."""
    output = _generate(tmp_path)
    checks = cast(dict[str, bool], _records(output)["checks"])
    assert set(checks) == {
        "one_executor_call",
        "refusal_category_is_policy",
        "refusal_dimension_is_recorded",
        "refusal_names_a_rule",
        "refusal_reason_is_outside_the_adapter_vocabulary",
    }
    assert all(checks.values())


def test_bundle_file_set_is_the_declared_one(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    assert set(AGENTDOJO_REFUSAL_EVIDENCE_FILES) == GENERATED_FILES
    assert {path.name for path in output.iterdir()} == GENERATED_FILES


def test_bundle_regenerates_byte_identically_and_verifies(tmp_path: Path) -> None:
    first = _generate(tmp_path, "first")
    second = _generate(tmp_path, "second")
    assert compare_agentdojo_refusal_evidence_bundle(first, second) == ()
    assert verify_agentdojo_refusal_evidence_checksums(first) == ()
    assert verify_agentdojo_refusal_evidence_checksums(second) == ()


def test_payload_is_deterministic(tmp_path: Path) -> None:
    """A pinned scenario with a stub model produces the same payload on every call."""
    assert canonical_json(refusal_record_payload("abcdef0")) == canonical_json(refusal_record_payload("abcdef0"))


def test_checksum_verification_notices_a_tampered_file(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    payload = _records(output)
    payload["complete"] = False
    (output / "records.json").write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
    assert verify_agentdojo_refusal_evidence_checksums(output) == ("records.json",)


def test_checksum_verification_notices_a_missing_file(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    (output / "README.md").unlink()
    assert verify_agentdojo_refusal_evidence_checksums(output) == ("README.md",)


def test_checksum_verification_notices_an_unlisted_file(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    (output / "stray.md").write_text("stray\n", encoding="utf-8", newline="\n")
    assert verify_agentdojo_refusal_evidence_checksums(output) == ("stray.md",)


def test_checksum_verification_requires_the_manifest(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    (output / "CHECKSUMS.sha256").unlink()
    assert verify_agentdojo_refusal_evidence_checksums(output) == ("CHECKSUMS.sha256",)


def test_comparison_notices_changed_and_added_files(tmp_path: Path) -> None:
    retained = _generate(tmp_path, "retained")
    regenerated = _generate(tmp_path, "regenerated")
    (regenerated / "stray.md").write_text("stray\n", encoding="utf-8", newline="\n")
    payload = _records(regenerated)
    payload["source_commit"] = "1234567"
    (regenerated / "records.json").write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
    assert compare_agentdojo_refusal_evidence_bundle(retained, regenerated) == ("records.json", "stray.md")
