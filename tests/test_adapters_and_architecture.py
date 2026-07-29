"""Adapter failure behavior and clean import architecture."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from conflux.adapters.benchmarks.experimental import parse_external_record
from conflux.adapters.policy.aws import evaluate_statement
from conflux.adapters.providers import (
    FilesystemSnapshotProvider,
    RecordingExecutor,
    StaticEnvironmentProvider,
    UnsupportedDockerExecutor,
)
from conflux.domain import Artifact, NoOpAction, Principal, Provenance, action_fingerprint
from conflux.execution import Operation
from conflux.policy import OwnerAuthorisationPolicy

ROOT = Path(__file__).resolve().parents[1]


def test_external_benchmark_unknown_schema_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        parse_external_record(
            {"schema": "2", "task_id": "x", "secure": True, "useful": True},
            supported_schema="1",
        )


def test_external_benchmark_keeps_security_and_utility_separate() -> None:
    result = parse_external_record(
        {"schema": "1", "task_id": "x", "secure": True, "useful": False},
        supported_schema="1",
    )
    assert result.secure and not result.useful


def test_external_benchmark_rejects_incomplete_or_mistyped_records() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        parse_external_record({"schema": "1"}, supported_schema="1")
    with pytest.raises(TypeError, match="Boolean"):
        parse_external_record(
            {"schema": "1", "task_id": "x", "secure": "yes", "useful": True},
            supported_schema="1",
        )


def test_aws_subset_rejects_unsupported_fields() -> None:
    decision = evaluate_statement(
        {"Effect": "Allow", "Action": "read", "Resource": "x", "Condition": {}},
        action="read",
        resource="x",
    )
    assert not decision.allowed
    assert decision.reason.startswith("unsupported_fields")


def test_aws_explicit_deny_wins() -> None:
    decision = evaluate_statement(
        {"Effect": "Deny", "Action": "read", "Resource": "x"},
        action="read",
        resource="x",
    )
    assert not decision.allowed
    assert decision.reason == "explicit_deny"


def test_aws_subset_allows_exact_match_and_denies_bad_effect() -> None:
    assert evaluate_statement(
        {"Effect": "Allow", "Action": ["read"], "Resource": ["x"]},
        action="read",
        resource="x",
    ).allowed
    assert not evaluate_statement(
        {"Effect": "Maybe", "Action": "read", "Resource": "x"},
        action="read",
        resource="x",
    ).allowed


def test_docker_executor_is_fail_closed() -> None:
    result = UnsupportedDockerExecutor().execute(
        NoOpAction("noop"),
        certificate_id="certificate",
        action_fingerprint="fingerprint",
    )
    assert not result.success


def test_recording_executor_binds_fingerprint() -> None:
    action = NoOpAction("noop")
    executor = RecordingExecutor()
    assert executor.execute(
        action,
        certificate_id="certificate",
        action_fingerprint=action_fingerprint(action),
    ).success
    assert executor.executed == ["noop"]
    assert not executor.execute(
        action,
        certificate_id="",
        action_fingerprint="wrong",
    ).success


def test_static_and_filesystem_providers(tmp_path: Path) -> None:
    principal = Principal("p", "Principal")
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    snapshot = FilesystemSnapshotProvider(
        tmp_path,
        principal,
        frozenset({principal}),
    ).snapshot()
    assert snapshot.data[0].value == "hello"
    assert StaticEnvironmentProvider(snapshot).snapshot() is snapshot


def test_filesystem_provider_rejects_non_directory(tmp_path: Path) -> None:
    principal = Principal("p", "Principal")
    file_path = tmp_path / "file"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="directory"):
        FilesystemSnapshotProvider(file_path, principal, frozenset()).snapshot()


def test_operation_preserves_provenance() -> None:
    principal = Principal("p", "Principal")
    source = Artifact("x", "hello", Provenance.from_principal(principal))
    result = Operation[str, str]("upper", str.upper).run(source, output_id="y")
    assert result.value == "HELLO"
    assert principal in result.provenance.principals


def test_owner_policy_is_normal_policy_oracle() -> None:
    from conflux.domain import EnvironmentSnapshot, Permission, PrimitiveAction, ResourceRef

    principal = Principal("owner", "Owner")
    action = PrimitiveAction(
        "write",
        "write",
        Permission("write"),
        ResourceRef("x", "r", "doc", {"owner_id": "owner"}),
    )
    assert OwnerAuthorisationPolicy().decide(
        principal,
        action,
        EnvironmentSnapshot("e"),
    ).allowed


def test_no_legacy_packages_or_imports() -> None:
    forbidden = {"conflux.core", "conflux.auth", "conflux.research", "conflux.compatibility"}
    source = ROOT / "src" / "conflux"
    assert not any(
        list((source / name).glob("*.py"))
        for name in ("core", "auth", "research", "compatibility")
    )
    for path in source.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert not any(any(name == item or name.startswith(f"{item}.") for item in forbidden) for name in imports)


def test_domain_has_no_outward_conflux_dependencies() -> None:
    for path in (ROOT / "src" / "conflux" / "domain").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("conflux.")
