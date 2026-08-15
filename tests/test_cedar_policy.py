"""Pinned local Cedar translation, failure isolation, and policy parity."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Iterator

import pytest
from jsonschema import Draft202012Validator

from conflux.adapters.policy import (
    CEDAR_COMMIT,
    CEDAR_VERSION,
    CedarArgumentAuthorisationPolicy,
    CedarAuthorisationPolicy,
    CedarBinaryIdentity,
    CedarCliRunner,
    CedarDecision,
    CedarPolicyBundle,
    CedarRequest,
    CedarRunnerResult,
)
from conflux.application import DecisionPipeline
from conflux.domain import (
    ActionArgument,
    ArgumentRole,
    EnvironmentSnapshot,
    Permission,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    Provenance,
    ResourceRef,
    Session,
)

ROOT = Path(__file__).resolve().parents[1]
ZERO_SHA = "0" * 64


def _bundle(*, binary_sha256: str = ZERO_SHA) -> CedarPolicyBundle:
    return CedarPolicyBundle(
        "test-policy",
        json.dumps({"Conflux": {}}),
        "permit(principal, action, resource);",
        json.dumps([]),
        CedarBinaryIdentity(CEDAR_VERSION, CEDAR_COMMIT, binary_sha256),
    )


def _result(decision: CedarDecision, label: str = "fixture") -> CedarRunnerResult:
    return CedarRunnerResult(
        True,
        decision,
        "cedar_allow" if decision is CedarDecision.ALLOW else "cedar_deny",
        sha256(label.encode()).hexdigest(),
    )


class RecordingRunner:
    def __init__(self, decisions: Iterator[CedarRunnerResult] | None = None) -> None:
        self.requests: list[CedarRequest] = []
        self.decisions = decisions

    def evaluate(self, bundle: CedarPolicyBundle, request: CedarRequest) -> CedarRunnerResult:
        _ = bundle
        self.requests.append(request)
        return next(self.decisions) if self.decisions is not None else _result(CedarDecision.ALLOW)


def _action(
    principal: Principal,
    *,
    destination: str = "archive",
    include_argument: bool = True,
) -> PrimitiveAction:
    arguments = (
        (
            ActionArgument.bind(
                name="destination",
                role=ArgumentRole.DESTINATION,
                value=destination,
                provenance=Provenance.from_principal(principal),
            ),
        )
        if include_argument
        else ()
    )
    return PrimitiveAction(
        "write",
        "write",
        Permission("write"),
        ResourceRef("test", "out", "document"),
        arguments=arguments,
    )


def test_bundle_is_pinned_hashed_immutable_and_schema_valid() -> None:
    bundle = _bundle()
    assert bundle.fingerprint == _bundle().fingerprint
    assert bundle.binary.version == "4.12.0"
    schema = json.loads((ROOT / "schemas" / "cedar-policy-bundle.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(bundle.to_dict())
    with pytest.raises(ValueError, match="unsupported Cedar binary"):
        CedarBinaryIdentity("4.10.0", CEDAR_COMMIT, ZERO_SHA)
    with pytest.raises(ValueError, match="unsupported Cedar features"):
        replace(bundle, supported_features=frozenset({"parc", "templates"}))
    with pytest.raises(ValueError, match="malformed Cedar JSON"):
        replace(bundle, schema_json="not-json")


def test_translation_maps_parc_roles_agent_and_delegation_context(
    environment: EnvironmentSnapshot,
    alice: Principal,
) -> None:
    runner = RecordingRunner()
    adapter = CedarAuthorisationPolicy(
        _bundle(),
        runner,
        {"write": "2"},
        {"agent_id": "conflux-test"},
    )
    action = _action(alice)
    decision = adapter.decide(alice, action, environment)
    assert decision.allowed
    request = runner.requests[0]
    assert request.principal == 'Principal::"alice"'
    assert request.action == 'Action::"write"'
    assert request.resource == 'Resource::"test:document:out"'
    context = json.loads(request.context_json)
    assert context["operation_version"] == "2"
    assert set(context["arguments"]) == {"destination"}
    assert context["arguments"]["destination"][0]["name"] == "destination"
    assert context["arguments"]["destination"][0]["value_fingerprint"] == action.arguments[0].value_fingerprint
    assert context["agent"] == {"agent_id": "conflux-test"}
    assert context["delegation"] is None
    assert _bundle().fingerprint in decision.evidence
    assert runner.requests[0].fingerprint in decision.evidence


def test_argument_request_identifies_exact_trusted_role(
    environment: EnvironmentSnapshot,
    alice: Principal,
) -> None:
    runner = RecordingRunner()
    adapter = CedarAuthorisationPolicy(_bundle(), runner, {"write": "1"})
    action = _action(alice)
    decision = CedarArgumentAuthorisationPolicy(adapter).decide(
        alice,
        action,
        action.arguments[0],
        environment,
    )
    assert decision.allowed
    assert json.loads(runner.requests[0].context_json)["argument_under_decision"] == "destination"


@pytest.mark.parametrize(
    ("action", "versions", "reason"),
    [
        (PrimitiveAction("x", "write", Permission("write")), {"write": "1"}, "missing_resource_entity"),
        (None, {}, "unsupported_operation_version"),
    ],
)
def test_missing_entities_and_unknown_operation_versions_deny(
    action: PrimitiveAction | None,
    versions: dict[str, str],
    reason: str,
    environment: EnvironmentSnapshot,
    alice: Principal,
) -> None:
    adapter = CedarAuthorisationPolicy(_bundle(), RecordingRunner(), versions)
    decision = adapter.decide(alice, action or _action(alice), environment)
    assert not decision.allowed
    assert decision.reason == reason


@pytest.mark.parametrize(
    "result",
    [
        CedarRunnerResult(False, None, "malformed_output", sha256(b"bad").hexdigest()),
        CedarRunnerResult(False, None, "timeout", sha256(b"timeout").hexdigest()),
        CedarRunnerResult(False, None, "validation_error", sha256(b"schema").hexdigest()),
        CedarRunnerResult(False, None, "unsupported_extension", sha256(b"extension").hexdigest()),
    ],
)
def test_runner_failures_are_explicit_denials(
    result: CedarRunnerResult,
    environment: EnvironmentSnapshot,
    alice: Principal,
) -> None:
    adapter = CedarAuthorisationPolicy(_bundle(), RecordingRunner(iter((result,))), {"write": "1"})
    decision = adapter.decide(alice, _action(alice), environment)
    assert not decision.allowed
    assert decision.reason == result.reason
    assert result.response_sha256 in decision.evidence


def test_mixed_principal_context_denies_pointwise(
    pipeline: DecisionPipeline,
    environment: EnvironmentSnapshot,
    session: Session,
    alice: Principal,
    bob: Principal,
) -> None:
    runner = RecordingRunner(iter((_result(CedarDecision.ALLOW, "alice"), _result(CedarDecision.DENY, "bob"))))
    adapter = CedarAuthorisationPolicy(_bundle(), runner, {"write": "1"})
    cedar_pipeline = replace(pipeline, authorisation=adapter)
    decision = cedar_pipeline.decide(
        session=session,
        action=_action(alice, include_argument=False),
        context=PrincipalContext(frozenset({alice, bob})),
        environment=environment,
    )
    assert not decision.allowed
    assert decision.authorisation.reason == "principal_denied"
    assert len(runner.requests) == 2


def test_explicit_forbid_response_overrides_expected_allow(
    environment: EnvironmentSnapshot,
    alice: Principal,
) -> None:
    adapter = CedarAuthorisationPolicy(
        _bundle(),
        RecordingRunner(iter((_result(CedarDecision.DENY, "explicit-forbid"),))),
        {"write": "1"},
    )
    decision = adapter.decide(alice, _action(alice), environment)
    assert not decision.allowed
    assert decision.reason == "cedar_deny"


def test_cli_runner_uses_no_shell_and_exact_binary_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary = tmp_path / "cedar"
    binary.write_bytes(b"pinned cedar fixture")
    bundle = _bundle(binary_sha256=sha256(binary.read_bytes()).hexdigest())
    calls: list[tuple[tuple[str, ...], bool]] = []
    responses = iter(
        (
            subprocess.CompletedProcess([], 0, "cedar 4.12.0\n", ""),
            subprocess.CompletedProcess([], 0, "validation passed\n", ""),
            subprocess.CompletedProcess([], 0, "ALLOW\n", ""),
        )
    )

    def fake_run(command: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, bool(kwargs["shell"])))
        return next(responses)

    monkeypatch.setattr("conflux.adapters.policy.cedar.subprocess.run", fake_run)
    request = CedarRequest('Principal::"alice"', 'Action::"write"', 'Resource::"out"', "{}")
    result = CedarCliRunner(binary).evaluate(bundle, request)
    assert result.decision is CedarDecision.ALLOW
    assert all(not shell for _, shell in calls)
    assert calls[1][0][1] == "validate"
    assert calls[2][0][1] == "authorize"
    assert "--context" in calls[2][0]


def test_cli_runner_rejects_hash_mismatch_before_invocation(tmp_path: Path) -> None:
    binary = tmp_path / "cedar"
    binary.write_bytes(b"not the declared binary")
    result = CedarCliRunner(binary).evaluate(
        _bundle(),
        CedarRequest('Principal::"alice"', 'Action::"write"', 'Resource::"out"', "{}"),
    )
    assert not result.available
    assert result.reason == "binary_identity_mismatch"


@pytest.mark.parametrize(
    ("responses", "expected"),
    [
        ((subprocess.CompletedProcess([], 0, "cedar 4.10.0\n", ""),), "binary_identity_mismatch"),
        (
            (
                subprocess.CompletedProcess([], 0, "cedar 4.12.0\n", ""),
                subprocess.CompletedProcess([], 1, "", "invalid schema"),
            ),
            "validation_error",
        ),
        (
            (
                subprocess.CompletedProcess([], 0, "cedar 4.12.0\n", ""),
                subprocess.CompletedProcess([], 0, "validation passed\n", ""),
                subprocess.CompletedProcess([], 0, "allow-ish\n", ""),
            ),
            "malformed_output",
        ),
        (
            (
                subprocess.CompletedProcess([], 0, "cedar 4.12.0\n", ""),
                subprocess.CompletedProcess([], 0, "validation passed\n", ""),
                subprocess.CompletedProcess([], 1, "", "evaluation failed"),
            ),
            "cedar_error",
        ),
    ],
)
def test_cli_runner_fails_closed_on_version_validation_and_output(
    responses: tuple[subprocess.CompletedProcess[str], ...],
    expected: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary = tmp_path / "cedar"
    binary.write_bytes(b"pinned cedar fixture")
    bundle = _bundle(binary_sha256=sha256(binary.read_bytes()).hexdigest())
    queued = iter(responses)

    def fake_run(command: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[str]:
        _ = command, kwargs
        return next(queued)

    monkeypatch.setattr("conflux.adapters.policy.cedar.subprocess.run", fake_run)
    result = CedarCliRunner(binary).evaluate(
        bundle,
        CedarRequest('Principal::"alice"', 'Action::"write"', 'Resource::"out"', "{}"),
    )
    assert not result.available
    assert result.reason == expected


def test_cli_runner_timeout_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary = tmp_path / "cedar"
    binary.write_bytes(b"pinned cedar fixture")
    bundle = _bundle(binary_sha256=sha256(binary.read_bytes()).hexdigest())

    def timeout(command: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[str]:
        _ = kwargs
        raise subprocess.TimeoutExpired(command, 1)

    monkeypatch.setattr("conflux.adapters.policy.cedar.subprocess.run", timeout)
    result = CedarCliRunner(binary).evaluate(
        bundle,
        CedarRequest('Principal::"alice"', 'Action::"write"', 'Resource::"out"', "{}"),
    )
    assert not result.available
    assert result.reason == "timeout"
