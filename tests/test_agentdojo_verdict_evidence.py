"""Offline verdict evidence stays deterministic, checksummed and claim-limited."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from conflux.domain import canonical_json
from conflux.experiments import (
    AGENTDOJO_VERDICT_EVIDENCE_FILES,
    compare_agentdojo_verdict_evidence_bundle,
    generate_agentdojo_verdict_evidence_bundle,
    verify_agentdojo_verdict_evidence_checksums,
)
from conflux.experiments.agentdojo_verdict_evidence import MUTATION, mutant_record, verdict_evidence_payload

pytestmark = pytest.mark.reproducibility

GENERATED_FILES = {"CHECKSUMS.sha256", "README.md", "records.json"}

RETAINED_BUNDLE = Path(__file__).resolve().parents[1] / "research" / "output" / "runs" / "agentdojo-verdict-evidence-v1"


def _generate(tmp_path: Path, name: str = "verdict-evidence") -> Path:
    output = tmp_path / name
    generate_agentdojo_verdict_evidence_bundle("abcdef0", output)
    return output


def _records(output: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((output / "records.json").read_text(encoding="utf-8")))


def _constructed(output: Path) -> dict[str, Any]:
    records = cast(list[dict[str, Any]], _records(output)["records"])
    return records[-1]


def _allowed_event(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {"outcome": "executed", "decision": {"allowed": True, "decisions": decisions}}


def test_bundle_holds_all_three_verdicts(tmp_path: Path) -> None:
    """The bundle carries one record per verdict class, so no class is left unexercised."""
    payload = _records(_generate(tmp_path))
    counts = cast(dict[str, int], payload["verdict_counts"])
    assert counts == {"holds": 4, "not_exercised": 2, "broken": 1}
    assert all(count > 0 for count in counts.values())


def test_bundle_asserts_its_own_checks(tmp_path: Path) -> None:
    """Every retained check is a Boolean, and all of them hold in the pinned scenario."""
    checks = cast(dict[str, bool], _records(_generate(tmp_path))["checks"])
    assert set(checks) == {
        "all_three_verdicts_present",
        "counts_match_the_records",
        "executed_record_holds",
        "mutant_keeps_the_tool_and_arguments",
        "mutant_names_its_mutation",
        "mutant_record_broken",
        "mutant_removes_a_decision_that_allowed",
        "mutant_removes_every_allowing_rule",
        "one_executor_call",
        "refused_record_not_exercised",
    }
    assert all(checks.values())


def test_bundle_file_set_is_the_declared_one(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    assert set(AGENTDOJO_VERDICT_EVIDENCE_FILES) == GENERATED_FILES
    assert {path.name for path in output.iterdir()} == GENERATED_FILES


def test_executed_record_holds_and_refused_record_is_unexercised(tmp_path: Path) -> None:
    """The two runs show the two verdicts a real mediated scenario produces."""
    records = cast(list[dict[str, Any]], _records(_generate(tmp_path))["records"])
    executed, refused = records[0], records[1]
    assert executed["outcome"] == "executed"
    assert [item["verdict"] for item in executed["report"]["assessments"]] == ["holds", "holds", "holds"]
    assert refused["outcome"] == "blocked"
    assert [item["verdict"] for item in refused["report"]["assessments"]] == [
        "not_exercised",
        "not_exercised",
        "holds",
    ]
    assert refused["report"]["assessments"][1]["holds"] is False


def test_constructed_record_removes_only_the_decision(tmp_path: Path) -> None:
    """The third record is the first one with its allowing decision taken away."""
    payload = _records(_generate(tmp_path))
    executed = cast(list[dict[str, Any]], payload["records"])[0]
    constructed = _constructed(_generate(tmp_path, "second"))
    assert constructed["kind"] == "constructed_mutant"
    assert constructed["mutation"] == MUTATION
    assert constructed["source_record_index"] == 1
    assert constructed["tool"] == executed["tool"]
    assert constructed["arguments_sha256"] == executed["arguments_sha256"]
    assert constructed["counters"] == {"executed": 1, "unauthorised": 1}
    assert constructed["verdict"] == "broken"
    assert constructed["holds"] is False


def test_constructed_record_names_the_decision_it_removes(tmp_path: Path) -> None:
    """A reader can see which rules allowed the executed call before the mutation."""
    source_event = cast(dict[str, Any], _constructed(_generate(tmp_path))["source_event"])
    assert source_event["outcome"] == "executed"
    assert source_event["decision_allowed"] is True
    removed = cast(dict[str, Any], source_event["removed_decision"])
    assert removed["allowed"] is True
    rules = cast(list[dict[str, Any]], removed["rules"])
    assert [rule["policy_id"] for rule in rules] == [
        "in-memory-authorisation",
        "snapshot-read-policy",
        "session-visibility-policy",
        "explicit-consent-policy",
    ]


def _report(trace: list[dict[str, Any]]) -> dict[str, Any]:
    return {"branches": [{"trace": trace}]}


def test_a_report_without_an_executed_event_cannot_be_mutated() -> None:
    """The constructed record needs the executed event it claims to have taken the decision from."""
    with pytest.raises(ValueError, match="executed trace event"):
        mutant_record({}, _report([{"outcome": "blocked", "decision": None}]), source_index=1)


def test_a_report_whose_executed_event_never_allowed_cannot_be_mutated() -> None:
    """Removing a decision only explains a ``broken`` record when the decision allowed the call."""
    trace = [_allowed_event([{"allowed": True}]), {"outcome": "executed", "decision": None}]
    with pytest.raises(ValueError, match="allowing decision"):
        mutant_record({}, _report(trace), source_index=1)


def test_the_constructed_verdict_follows_the_library_class_rule() -> None:
    """One executed and one unauthorised observation is the ``broken`` class, not ``holds``."""
    trace = [_allowed_event([{"allowed": True, "policy_id": "allow-all", "category": "authorisation"}])]
    constructed = mutant_record({"tool": "search_emails", "arguments_sha256": "x"}, _report(trace), source_index=1)
    assert constructed["verdict_source"] == "conflux.ites.state.verdict_for_counts"
    assert constructed["counters"] == {"executed": 1, "unauthorised": 1}
    assert constructed["verdict"] == "broken"
    assert constructed["holds"] is False


def test_readme_states_the_limit_of_the_constructed_record(tmp_path: Path) -> None:
    """The page says the third record is not a run, so no reader over-reads it."""
    readme = (_generate(tmp_path) / "README.md").read_text(encoding="utf-8")
    assert "constructed" in readme
    assert "is not evidence that a live defence failed" in readme
    assert MUTATION in readme


def test_checksum_manifest_pins_the_hashes_and_their_order(tmp_path: Path) -> None:
    """The manifest is written in one host-independent order, so its bytes can be compared."""
    output = _generate(tmp_path)
    names = sorted(GENERATED_FILES - {"CHECKSUMS.sha256"}, key=str.casefold)
    assert names == ["README.md", "records.json"]
    expected = "".join(f"{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}\n" for name in names)
    assert (output / "CHECKSUMS.sha256").read_text(encoding="utf-8") == expected


def test_bundle_regenerates_byte_identically_and_verifies(tmp_path: Path) -> None:
    first = _generate(tmp_path, "first")
    second = _generate(tmp_path, "second")
    assert compare_agentdojo_verdict_evidence_bundle(first, second) == ()
    assert verify_agentdojo_verdict_evidence_checksums(first) == ()
    assert verify_agentdojo_verdict_evidence_checksums(second) == ()


def test_payload_is_deterministic() -> None:
    """A pinned scenario with a stub model produces the same payload on every call."""
    assert canonical_json(verdict_evidence_payload("abcdef0")) == canonical_json(verdict_evidence_payload("abcdef0"))


def test_checksum_verification_notices_a_tampered_file(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    payload = _records(output)
    payload["complete"] = False
    (output / "records.json").write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
    assert verify_agentdojo_verdict_evidence_checksums(output) == ("records.json",)


def test_checksum_verification_notices_a_missing_file(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    (output / "README.md").unlink()
    assert verify_agentdojo_verdict_evidence_checksums(output) == ("README.md",)


def test_checksum_verification_notices_an_unlisted_file(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    (output / "stray.md").write_text("stray\n", encoding="utf-8", newline="\n")
    assert verify_agentdojo_verdict_evidence_checksums(output) == ("stray.md",)


def test_checksum_verification_requires_the_manifest(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    (output / "CHECKSUMS.sha256").unlink()
    assert verify_agentdojo_verdict_evidence_checksums(output) == ("CHECKSUMS.sha256",)


def test_comparison_notices_changed_and_added_files(tmp_path: Path) -> None:
    retained = _generate(tmp_path, "retained")
    regenerated = _generate(tmp_path, "regenerated")
    (regenerated / "stray.md").write_text("stray\n", encoding="utf-8", newline="\n")
    payload = _records(regenerated)
    payload["source_commit"] = "1234567"
    (regenerated / "records.json").write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")
    assert compare_agentdojo_verdict_evidence_bundle(retained, regenerated) == ("records.json", "stray.md")


def test_the_retained_bundle_is_current(tmp_path: Path) -> None:
    """The bundle kept in the repository matches a fresh run of its own scenario."""
    if not RETAINED_BUNDLE.is_dir():
        pytest.skip("the retained verdict-evidence bundle is not present")
    assert verify_agentdojo_verdict_evidence_checksums(RETAINED_BUNDLE) == ()
    source_commit = str(_records(RETAINED_BUNDLE)["source_commit"])
    regenerated = tmp_path / "regenerated"
    generate_agentdojo_verdict_evidence_bundle(source_commit, regenerated)
    assert compare_agentdojo_verdict_evidence_bundle(RETAINED_BUNDLE, regenerated) == ()
