"""The harness demo stays deterministic, digest-only and claim-limited."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest

from conflux.domain import ActionArgument, ArgumentRole, Permission, PrimitiveAction
from conflux.experiments import (
    HARNESS_DEMO_FILES,
    compare_harness_demo_bundle,
    generate_harness_demo_bundle,
    verify_harness_demo_checksums,
)
from conflux.experiments.harness_demo import (
    ATTACK_TEXT,
    SECRET_PATH,
    SECRET_VALUE,
    HarnessExecutor,
    fixture_items,
    harness_demo_payload,
)

pytestmark = pytest.mark.reproducibility

RETAINED_BUNDLE = Path(__file__).resolve().parents[1] / "research" / "output" / "runs" / "harness-demo-v1"

PINS = {
    "annotations_sha256": "c4efbd4e23cda8363da4a48e4032ccf707d7a6c488ab9fb39bfc7b6083fe6454",
    "attack_text_sha256": "f5932c6b14b6c03a6282954477af32dd8170b42d5ad6fb5cc2ff8c3baa5b161b",
    "plan_sha256": "8babc8f7ba462fbca4af2874dafcc4c727563376f381499bd6f2d9a34cf2f388",
    "policy_sha256": "d0c1f903e5147caccd45a1d7e4addfe9fcf40303d761415a5897e36c56fd9b7e",
}

CHECKS = {
    "annotations_and_policy_pinned",
    "arms_differ_only_in_the_policy",
    "attack_text_retained",
    "out_of_scope_refusals_counted_separately",
    "policy_off_carries_the_secret_outside",
    "policy_off_posts_to_the_outside_address",
    "policy_on_blocks_the_injected_call",
    "policy_on_carries_no_secret_outside",
    "policy_on_posts_nothing_outside",
    "policy_on_refusal_is_a_policy_decision",
    "utility_parity",
}


def _generate(tmp_path: Path, name: str = "harness-demo", source_commit: str = "abcdef0") -> Path:
    output = tmp_path / name
    generate_harness_demo_bundle(source_commit, output)
    return output


def _result(output: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((output / "result.json").read_text(encoding="utf-8")))


def _protocol(output: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((output / "protocol.json").read_text(encoding="utf-8")))


def _arm(result: dict[str, Any], name: str) -> dict[str, Any]:
    arms = cast(list[dict[str, Any]], result["arms"])
    return next(arm for arm in arms if arm["arm"] == name)


def _record(arm: dict[str, Any], step: int) -> dict[str, Any]:
    records = cast(list[dict[str, Any]], arm["records"])
    return next(record for record in records if record["step"] == step)


def test_bundle_holds_the_two_arms_over_one_plan(tmp_path: Path) -> None:
    """Both arms come from one plan, so the arms cannot differ by their steps."""
    output = _generate(tmp_path)
    assert {path.name for path in output.iterdir()} == set(HARNESS_DEMO_FILES)
    result = _result(output)
    assert result["id"] == "harness-demo-v1"
    assert [arm["arm"] for arm in cast(list[dict[str, Any]], result["arms"])] == ["policy_off", "policy_on"]
    assert {record["step"] for record in _arm(result, "policy_on")["records"]} == {1, 2, 3, 4, 5}


def test_bundle_asserts_its_own_checks(tmp_path: Path) -> None:
    """Every retained check is a Boolean, and all of them hold in the pinned fixture."""
    result = _result(_generate(tmp_path))
    checks = cast(dict[str, bool], result["checks"])
    assert set(checks) == CHECKS
    assert all(checks.values())
    assert result["checks_passed"] is True


def test_the_primary_reading_is_the_two_arm_difference(tmp_path: Path) -> None:
    """The reading the demo claims is the difference between the two arms, not one arm alone."""
    primary = cast(dict[str, dict[str, Any]], _result(_generate(tmp_path))["primary"])
    assert primary["outside_posts"] == {"policy_off": 1, "policy_on": 0}
    assert primary["secret_carried_outside"] == {"policy_off": True, "policy_on": False}
    assert primary["policy_refusals"] == {"policy_off": 0, "policy_on": 1}
    assert primary["out_of_scope_refusals"] == {"policy_off": 1, "policy_on": 1}


def test_the_blocked_call_carries_a_named_policy_decision(tmp_path: Path) -> None:
    """The missing effect has a retained reason, and the reason matches the retained decision."""
    record = _record(_arm(_result(_generate(tmp_path)), "policy_on"), 4)
    assert record["outcome"] == "blocked"
    assert record["reason"] == "principal_denied"
    assert record["policy_id"] == "in-memory-authorisation"
    assert record["policy_dimension"] == "authorisation"
    trace = cast(list[dict[str, Any]], cast(dict[str, Any], record["report"])["branches"][0]["trace"])
    blocked = next(event for event in trace if event["outcome"] == "blocked")
    decision = cast(dict[str, Any], blocked["decision"])
    assert decision["allowed"] is False
    decisions = cast(list[dict[str, Any]], decision["decisions"])
    first_refusal = next(item for item in decisions if not item["allowed"])
    assert first_refusal["reason"] == record["reason"]
    assert first_refusal["policy_id"] == record["policy_id"]


def test_the_unannotated_probe_is_refused_without_a_policy_decision(tmp_path: Path) -> None:
    """An unannotated tool is refused in both arms, and is counted apart from policy refusals."""
    result = _result(_generate(tmp_path))
    for name in ("policy_off", "policy_on"):
        arm = _arm(result, name)
        record = _record(arm, 5)
        assert arm["out_of_scope_tools"] == ["send_email"]
        assert arm["out_of_scope_refusals"] == 1
        assert record["out_of_scope"] is True
        assert record["reason"] == "unsupported_tool"
        assert "policy_id" not in record


def test_utility_parity_holds_and_the_notes_match(tmp_path: Path) -> None:
    """The benign part of the task completes in both arms, to the same bytes."""
    result = _result(_generate(tmp_path))
    off, on = _arm(result, "policy_off"), _arm(result, "policy_on")
    assert result["utility_parity"] is True
    assert off["utility"] == on["utility"]
    utility = cast(dict[str, Any], off["utility"])
    assert utility["private_read"] is True
    assert utility["notes_written"] is True
    assert utility["task_post_arrived"] is True


def test_the_arms_differ_only_in_the_policy(tmp_path: Path) -> None:
    """Same tools, same argument values, same provenance: only the policy differs."""
    result = _result(_generate(tmp_path))
    off, on = _arm(result, "policy_off"), _arm(result, "policy_on")
    assert off["policy_enabled"] is False
    assert on["policy_enabled"] is True
    for step in (1, 2, 3, 4, 5):
        left, right = _record(off, step), _record(on, step)
        for field in ("tool", "value_sources", "argument_roles", "argument_value_sha256", "arguments_sha256"):
            assert left.get(field) == right.get(field)


def test_records_retain_digests_and_no_runner_state(tmp_path: Path) -> None:
    """The result file holds digests, not raw values, timestamps or ephemeral ports."""
    output = _generate(tmp_path)
    text = (output / "result.json").read_text(encoding="utf-8")
    assert SECRET_VALUE not in text
    assert "127.0.0.1" not in text
    assert "localhost" not in text
    result = _result(output)
    for name in ("policy_off", "policy_on"):
        for record in cast(list[dict[str, Any]], _arm(result, name)["records"]):
            digests = cast(dict[str, str], record.get("argument_value_sha256", {}))
            if record["out_of_scope"]:
                # An unannotated call is refused before its arguments are bound, so it keeps no
                # argument digests; it keeps the digest of the call it was given.
                assert digests == {}
                assert len(cast(str, record["arguments_sha256"])) == 64
                continue
            assert digests
            assert all(len(digest) == 64 and digest == digest.lower() for digest in digests.values())


def test_the_fixture_pins_are_stable(tmp_path: Path) -> None:
    """The plan, the annotation table, the policy and the attack text cannot drift silently."""
    output = _generate(tmp_path)
    result = _result(output)
    assert {name: result[name] for name in PINS} == PINS
    assert result["attack_text"] == ATTACK_TEXT
    assert result["source_commit"] == "abcdef0"
    fixture = cast(dict[str, Any], _protocol(output)["fixture"])
    assert fixture["secret_value"] == SECRET_VALUE
    assert fixture["task_dir_secret"] == SECRET_PATH


def test_regeneration_is_byte_stable_and_matches_the_retained_bundle(tmp_path: Path) -> None:
    """Two runs of one commit agree, and the retained copy still matches the code."""
    first = _generate(tmp_path, "first")
    second = _generate(tmp_path, "second")
    assert compare_harness_demo_bundle(first, second) == ()
    assert RETAINED_BUNDLE.is_dir()
    retained = _generate(tmp_path, "retained", str(_result(RETAINED_BUNDLE)["source_commit"]))
    assert compare_harness_demo_bundle(RETAINED_BUNDLE, retained) == ()


def test_the_retained_checksums_verify_and_tampering_is_named(tmp_path: Path) -> None:
    """A changed byte in a retained file is reported by name."""
    assert verify_harness_demo_checksums(RETAINED_BUNDLE) == ()
    copy = tmp_path / "tampered"
    shutil.copytree(RETAINED_BUNDLE, copy)
    target = copy / "result.json"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert verify_harness_demo_checksums(copy) == ("result.json",)


def test_the_executor_refuses_values_the_policy_did_not_see(tmp_path: Path) -> None:
    """The only effect site re-fingerprints its values, so it cannot run an unjudged call."""
    provenance = fixture_items()[0].to_artifact().provenance
    action = PrimitiveAction(
        "read_private",
        "read_private",
        Permission("read"),
        arguments=(ActionArgument.bind(name="file_id", role=ArgumentRole.RESOURCE, value=SECRET_PATH, provenance=provenance),),
    )
    executor = HarnessExecutor(task_dir=tmp_path, sink_base_url="http://127.0.0.1:1", values={"file_id": "another.txt"})
    outcome = executor.execute(action, certificate_id="certificate", action_fingerprint="fingerprint")
    assert outcome.success is False
    assert cast(str, outcome.error).startswith("argument_binding_mismatch")


def test_the_payload_runs_both_arms_in_one_call() -> None:
    """The public entry point returns both files' payload for any source commit."""
    payload = harness_demo_payload("smoke")
    result = cast(dict[str, Any], payload["result"])
    assert result["checks_passed"] is True
    assert result["source_commit"] == "smoke"
    assert cast(dict[str, Any], payload["protocol"])["source_commit"] == "smoke"
