"""Deterministic runtime adapters and strict scenario loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from conflux.adapters.models import ScriptedModel
from conflux.adapters.providers import ConfinedFilesystemExecutor, InMemoryExecutor
from conflux.adapters.scenarios import load_scenario
from conflux.domain import (
    Artifact,
    DelegationAction,
    MessageAction,
    NestedExecutionAction,
    NoOpAction,
    Permission,
    PrimitiveAction,
    Provenance,
    ResourceRef,
    StopAction,
    action_fingerprint,
)
from conflux.ites import MediatingITES, TransitionKernel

pytestmark = pytest.mark.adapter

ROOT = Path(__file__).resolve().parents[1]


def _write_action(resource_id: str, *, precondition: str | None = "missing") -> PrimitiveAction:
    attributes = {} if precondition is None else {"precondition_sha256": precondition}
    return PrimitiveAction(
        "write",
        "write",
        Permission("write"),
        ResourceRef("filesystem", resource_id, "document", attributes),
        (Artifact("content", "hello", Provenance.unknown()),),
    )


def test_scripted_model_is_deterministic_and_fails_when_exhausted() -> None:
    batch = load_scenario(ROOT / "tests" / "fixtures" / "scenarios" / "basic.yaml").model
    model = ScriptedModel((batch,))
    assert model.propose(()) is batch
    with pytest.raises(RuntimeError, match="exhausted"):
        model.propose(())
    repeating = ScriptedModel((batch,), repeat_last=True)
    assert repeating.propose(()) is repeating.propose(())
    with pytest.raises(ValueError, match="at least one"):
        ScriptedModel(())


def test_scenario_loader_builds_a_mediatable_canonical_scenario() -> None:
    scenario = load_scenario(ROOT / "tests" / "fixtures" / "scenarios" / "basic.yaml")
    report = MediatingITES(TransitionKernel(scenario.pipeline)).run(
        environment=scenario.environment,
        session=scenario.session,
        initial_inputs=(scenario.environment.artifacts()[0],),
        model=ScriptedModel((scenario.model,)),
    )
    assert report.authorised_count == 1
    assert report.blocked_count == 0


def test_scenario_loader_rejects_unknown_fields_and_references(tmp_path: Path) -> None:
    bad_field = tmp_path / "bad-field.yaml"
    bad_field.write_text(
        (ROOT / "tests" / "fixtures" / "scenarios" / "basic.yaml").read_text(encoding="utf-8") + "\nunknown: true\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="scenario_schema_error"):
        load_scenario(bad_field)

    bad_reference = tmp_path / "bad-reference.yaml"
    bad_reference.write_text(
        (ROOT / "tests" / "fixtures" / "scenarios" / "basic.yaml")
        .read_text(encoding="utf-8")
        .replace("authors: [alice]", "authors: [mallory]"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown_principal"):
        load_scenario(bad_reference)

    non_mapping = tmp_path / "non-mapping.yaml"
    non_mapping.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="root_must_be_mapping"):
        load_scenario(non_mapping)

    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("principals: [\n", encoding="utf-8")
    with pytest.raises(ValueError, match="scenario_load_failed"):
        load_scenario(malformed)

    unknown_grant = tmp_path / "unknown-grant.yaml"
    unknown_grant.write_text(
        (ROOT / "tests" / "fixtures" / "scenarios" / "basic.yaml")
        .read_text(encoding="utf-8")
        .replace("principal_id: alice", "principal_id: mallory"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown_grant_principal"):
        load_scenario(unknown_grant)


def test_scenario_loader_parses_every_declarative_action_kind(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "tests" / "fixtures" / "scenarios" / "basic.yaml").read_text(encoding="utf-8"))
    payload["model"] = {
        "schema_version": "1",
        "mode": "ordered_plan",
        "proposals": [
            {
                "id": "nested",
                "kind": "nested",
                "visibility": "internal",
                "input_ids": ["request"],
            },
            {
                "id": "message",
                "kind": "message",
                "visibility": "participants",
                "input_ids": ["request"],
                "message": "hello",
            },
            {
                "id": "delegation",
                "kind": "delegation",
                "visibility": "participants",
                "input_ids": [],
                "scope": "unsupported",
            },
            {
                "id": "stop",
                "kind": "stop",
                "visibility": "internal",
                "input_ids": [],
                "reason": "done",
            },
            {
                "id": "noop",
                "kind": "no_op",
                "visibility": "internal",
                "input_ids": [],
                "label": "nothing",
            },
        ],
    }
    path = tmp_path / "actions.yaml"
    path.write_text(json.dumps(payload), encoding="utf-8")
    actions = load_scenario(path).model.proposals
    assert isinstance(actions[0], NestedExecutionAction)
    assert isinstance(actions[1], MessageAction)
    assert isinstance(actions[2], DelegationAction)
    assert isinstance(actions[3], StopAction)
    assert isinstance(actions[4], NoOpAction)


def test_in_memory_executor_is_idempotent_and_can_fail() -> None:
    action = NoOpAction("noop")
    executor = InMemoryExecutor()
    first = executor.execute(
        action,
        certificate_id="certificate",
        action_fingerprint=action_fingerprint(action),
    )
    second = executor.execute(
        action,
        certificate_id="certificate",
        action_fingerprint=action_fingerprint(action),
    )
    assert first is second
    assert first.success
    different = NoOpAction("different")
    mismatch = executor.execute(
        different,
        certificate_id="certificate",
        action_fingerprint=action_fingerprint(different),
    )
    assert mismatch.error == "certificate_reuse_mismatch"
    failed = InMemoryExecutor(frozenset({"noop"})).execute(
        action,
        certificate_id="other",
        action_fingerprint=action_fingerprint(action),
    )
    assert failed.error == "configured_provider_failure"
    invalid = executor.execute(
        action,
        certificate_id="",
        action_fingerprint="wrong",
    )
    assert invalid.error == "certificate_action_mismatch"


def test_filesystem_executor_is_dry_run_confined_and_atomic(tmp_path: Path) -> None:
    action = _write_action("nested/output.txt")
    dry_run = ConfinedFilesystemExecutor(tmp_path)
    preview = dry_run.execute(
        action,
        certificate_id="dry",
        action_fingerprint=action_fingerprint(action),
    )
    assert preview.success
    assert not (tmp_path / "nested" / "output.txt").exists()
    assert isinstance(preview.outcome, dict) and preview.outcome["dry_run"]

    live = ConfinedFilesystemExecutor(tmp_path, dry_run=False)
    result = live.execute(
        action,
        certificate_id="live",
        action_fingerprint=action_fingerprint(action),
    )
    assert result.success
    assert (tmp_path / "nested" / "output.txt").read_text(encoding="utf-8") == "hello"
    assert not tuple((tmp_path / "nested").glob("*.tmp"))

    traversal = _write_action("../outside.txt")
    denied = live.execute(
        traversal,
        certificate_id="traversal",
        action_fingerprint=action_fingerprint(traversal),
    )
    assert denied.error == "filesystem_path_rejected"
    assert not (tmp_path.parent / "outside.txt").exists()


def test_filesystem_executor_requires_and_checks_preconditions(tmp_path: Path) -> None:
    target = tmp_path / "output.txt"
    target.write_text("existing", encoding="utf-8")
    no_precondition = _write_action("output.txt", precondition=None)
    result = ConfinedFilesystemExecutor(tmp_path, dry_run=False).execute(
        no_precondition,
        certificate_id="missing-precondition",
        action_fingerprint=action_fingerprint(no_precondition),
    )
    assert result.error == "filesystem_precondition_required"

    stale = _write_action("output.txt", precondition="wrong")
    result = ConfinedFilesystemExecutor(tmp_path, dry_run=False).execute(
        stale,
        certificate_id="stale",
        action_fingerprint=action_fingerprint(stale),
    )
    assert result.error == "filesystem_precondition_failed"
    assert target.read_text(encoding="utf-8") == "existing"

    directory = _write_action("directory", precondition="missing")
    (tmp_path / "directory").mkdir()
    result = ConfinedFilesystemExecutor(tmp_path).execute(
        directory,
        certificate_id="directory",
        action_fingerprint=action_fingerprint(directory),
    )
    assert result.error == "filesystem_target_rejected"


def test_filesystem_executor_fails_closed_for_unsupported_inputs(tmp_path: Path) -> None:
    executor = ConfinedFilesystemExecutor(tmp_path)
    noop = NoOpAction("noop")
    result = executor.execute(
        noop,
        certificate_id="noop",
        action_fingerprint=action_fingerprint(noop),
    )
    assert result.error == "unsupported_filesystem_action"

    no_resource = PrimitiveAction("write", "write", Permission("write"))
    result = executor.execute(
        no_resource,
        certificate_id="no-resource",
        action_fingerprint=action_fingerprint(no_resource),
    )
    assert result.error == "unsupported_filesystem_resource"

    no_input = PrimitiveAction(
        "write",
        "write",
        Permission("write"),
        ResourceRef("filesystem", "out.txt", "document"),
    )
    result = executor.execute(
        no_input,
        certificate_id="no-input",
        action_fingerprint=action_fingerprint(no_input),
    )
    assert result.error == "filesystem_write_missing_input"

    binary = PrimitiveAction(
        "write",
        "write",
        Permission("write"),
        ResourceRef("filesystem", "out.txt", "document"),
        (Artifact("binary", b"bytes", Provenance.unknown()),),
    )
    result = executor.execute(
        binary,
        certificate_id="binary",
        action_fingerprint=action_fingerprint(binary),
    )
    assert result.error == "filesystem_write_requires_text"


def test_filesystem_executor_replaces_matching_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "output.txt"
    target.write_text("old", encoding="utf-8")
    expected = hashlib.sha256(b"old").hexdigest()
    action = _write_action("output.txt", precondition=expected)
    result = ConfinedFilesystemExecutor(tmp_path, dry_run=False).execute(
        action,
        certificate_id="replace",
        action_fingerprint=action_fingerprint(action),
    )
    assert result.success
    assert target.read_text(encoding="utf-8") == "hello"
