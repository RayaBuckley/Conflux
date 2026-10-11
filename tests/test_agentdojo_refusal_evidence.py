"""Offline policy-refusal evidence stays deterministic, checksummed and claim-limited."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from conflux.domain import canonical_json
from conflux.experiments import (
    AGENTDOJO_REFUSAL_EVIDENCE_FILES,
    compare_agentdojo_refusal_evidence_bundle,
    generate_agentdojo_refusal_evidence_bundle,
    refusing_rule_from_report_summary,
    refusing_rule_from_retained_report,
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


def test_the_retained_records_report_unexercised_properties_as_unexercised(tmp_path: Path) -> None:
    """A reader can tell a refusal with nothing executed from a violated property, from the file alone."""
    executed, refused = cast(list[dict[str, Any]], _records(_generate(tmp_path))["records"])

    def verdicts(record: dict[str, Any]) -> dict[str, str]:
        report = cast(dict[str, Any], record["report"])
        return {item["name"]: item["verdict"] for item in cast(list[dict[str, Any]], report["assessments"])}

    assert verdicts(executed) == {
        "no_unauthorised_execution": "holds",
        "no_unauthorised_authorisation": "holds",
        "bounded_model_calls": "holds",
    }
    refused_verdicts = verdicts(refused)
    assert refused_verdicts["no_unauthorised_execution"] == "not_exercised"
    assert refused_verdicts["no_unauthorised_authorisation"] == "not_exercised"
    assert refused_verdicts["bounded_model_calls"] == "holds"
    flags = {
        item["name"]: item["holds"]
        for item in cast(list[dict[str, Any]], cast(dict[str, Any], refused["report"])["assessments"])
    }
    assert flags == {
        "no_unauthorised_execution": False,
        "no_unauthorised_authorisation": False,
        "bounded_model_calls": True,
    }


def test_bundle_asserts_its_own_checks(tmp_path: Path) -> None:
    """Every retained check is a Boolean, and all of them hold in the pinned scenario."""
    output = _generate(tmp_path)
    checks = cast(dict[str, bool], _records(output)["checks"])
    assert set(checks) == {
        "one_executor_call",
        "refusal_category_is_policy",
        "refusal_dimension_is_recorded",
        "refusal_matches_the_retained_report",
        "refusal_names_a_rule",
        "refusal_reason_is_outside_the_adapter_vocabulary",
    }
    assert all(checks.values())


def test_bundle_file_set_is_the_declared_one(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    assert set(AGENTDOJO_REFUSAL_EVIDENCE_FILES) == GENERATED_FILES
    assert {path.name for path in output.iterdir()} == GENERATED_FILES


def test_checksum_manifest_pins_the_hashes_and_their_order(tmp_path: Path) -> None:
    """The manifest is written in one host-independent order, so its bytes can be compared."""
    output = _generate(tmp_path)
    names = sorted(GENERATED_FILES - {"CHECKSUMS.sha256"}, key=str.casefold)
    assert names == ["README.md", "records.json"]
    expected = "".join(f"{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}\n" for name in names)
    assert (output / "CHECKSUMS.sha256").read_text(encoding="utf-8") == expected


def test_the_retained_excerpt_rechecks_the_recorded_rule(tmp_path: Path) -> None:
    """A reader can re-derive the refused rule from the retained report excerpt alone."""
    refused = cast(list[dict[str, Any]], _records(_generate(tmp_path))["records"])[-1]
    fields = {key: refused[key] for key in ("reason", "policy_id", "policy_dimension")}
    fabricated = dict(refused, reason="banana")
    assert refusing_rule_from_report_summary(refused) == fields
    assert refusing_rule_from_report_summary(fabricated) != {
        key: fabricated[key] for key in ("reason", "policy_id", "policy_dimension")
    }


def _retained_report(decisions: list[dict[str, Any]], *, with_a_blank_event: bool = False) -> dict[str, Any]:
    trace: list[dict[str, Any]] = [{"decision": None}] if with_a_blank_event else []
    trace.append({"decision": {"decisions": decisions}})
    return {"branches": [{"trace": trace}]}


def test_the_retained_report_walk_finds_the_first_denying_decision() -> None:
    """A reader can re-derive the rule from a stored report without the code that wrote it."""
    allowed = {"allowed": True, "reason": "authorised", "policy_id": "allow-all", "category": "authorisation"}
    denied = {"allowed": False, "reason": "read_denied", "policy_id": "in-memory-read", "category": "read"}
    later = {"allowed": False, "reason": "principal_denied", "policy_id": "in-memory-authorisation", "category": "visibility"}
    report = _retained_report([allowed, denied, later], with_a_blank_event=True)
    assert refusing_rule_from_retained_report(report) == {
        "reason": "read_denied",
        "policy_id": "in-memory-read",
        "policy_dimension": "read",
    }


def test_the_retained_report_walk_names_no_rule_without_a_denial() -> None:
    allowed = {"allowed": True, "reason": "authorised", "policy_id": "allow-all", "category": "authorisation"}
    assert refusing_rule_from_retained_report(_retained_report([allowed])) is None
    assert refusing_rule_from_retained_report({}) is None
    assert refusing_rule_from_retained_report({"branches": [{"trace": []}]}) is None


def test_a_record_without_an_excerpt_names_no_rule(tmp_path: Path) -> None:
    executed = cast(list[dict[str, Any]], _records(_generate(tmp_path))["records"])[0]
    assert refusing_rule_from_report_summary(executed) is None


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
