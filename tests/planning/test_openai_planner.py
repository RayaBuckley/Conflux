"""Offline structured-planner adapter tests."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest

from conflux.adapters.models import OpenAICompatiblePlanner
from conflux.adapters.models.openai_compatible import HTTPResponse
from conflux.domain import Principal, Provenance
from conflux.planning import (
    ContinuationRequest,
    OperationCatalogue,
    PatchKind,
    PatchOperation,
    Plan,
    PlanBudgets,
    PlanningRequest,
    PlanPatch,
    TerminalNode,
    TerminalOutcome,
)


@dataclass
class Response:
    status_code: int
    payload: object

    @property
    def text(self) -> str:
        return json.dumps(self.payload)

    def json(self) -> object:
        return self.payload


@dataclass
class Transport:
    responses: list[Response]
    calls: list[dict[str, object]] = field(default_factory=list)

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, object],
        timeout: float,
    ) -> HTTPResponse:
        self.calls.append(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        return self.responses.pop(0)


def provenance(principal: Principal, source: str) -> Provenance:
    return Provenance.from_principal(principal, source=source)


def response(content: object, *, secret: str | None = None) -> Response:
    body: dict[str, object] = {
        "choices": [{"message": {"content": json.dumps(content)}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 7},
    }
    if secret is not None:
        body["debug_token"] = secret
    return Response(200, body)


def terminal_plan(principal: Principal) -> Plan:
    source = provenance(principal, "model-asserted")
    return Plan(
        "planner-plan",
        "repair",
        (
            TerminalNode(
                "done",
                TerminalOutcome.SUCCEEDED,
                "done",
                source,
            ),
        ),
        source,
    )


def test_initial_plan_uses_authenticated_catalogue_and_trusted_provenance(
    monkeypatch: pytest.MonkeyPatch,
    alice: Principal,
    bob: Principal,
) -> None:
    secret = "planner-secret"
    monkeypatch.setenv("PLANNER_KEY", secret)
    catalogue = OperationCatalogue((), identity="empty")
    transport = Transport([response(terminal_plan(bob).to_dict(), secret=secret)])
    ticks = iter((1.0, 1.125))
    planner = OpenAICompatiblePlanner(
        "https://planner.example/v1/chat/completions",
        "planner-model",
        catalogue,
        api_key_env="PLANNER_KEY",
        transport=transport,
        clock=lambda: next(ticks),
    )
    request = PlanningRequest(
        "initial",
        "repair",
        (),
        catalogue.fingerprint,
        PlanBudgets(),
        provenance(alice, "trusted-request"),
    )
    result = planner.initial_plan(request)
    assert result.plan is not None
    assert result.plan.invocation_provenance.principals == frozenset({alice})
    assert result.plan.node("done").control_provenance.principals == frozenset({alice})
    call = transport.calls[0]
    assert call["headers"] == {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
    }
    request_body = call["json"]
    assert isinstance(request_body, dict)
    schema = request_body["response_format"]
    assert isinstance(schema, dict)
    assert schema["json_schema"]["name"] == "conflux_initial_plan_v1"
    assert result.record.input_tokens == 12
    assert result.record.output_tokens == 7
    assert result.record.latency_ms == 125
    assert secret not in result.record.raw_response
    assert "[REDACTED]" in result.record.raw_response


def test_continuation_repairs_once_and_never_returns_unparsed_text(
    monkeypatch: pytest.MonkeyPatch,
    alice: Principal,
) -> None:
    monkeypatch.setenv("PLANNER_KEY", "key")
    catalogue = OperationCatalogue((), identity="empty")
    plan = terminal_plan(alice)
    patch = PlanPatch(
        "patch",
        plan.id,
        (
            PatchOperation(
                "stop",
                PatchKind.TERMINATE,
                terminal_outcome=TerminalOutcome.SAFE_STOP,
                terminal_reason="safe stop",
            ),
        ),
    )
    transport = Transport(
        [
            response({"unparsed": "not a patch"}),
            response(patch.to_dict()),
        ]
    )
    planner = OpenAICompatiblePlanner(
        "http://127.0.0.1:8000/v1/chat/completions",
        "local",
        catalogue,
        api_key_env="PLANNER_KEY",
        max_repairs=1,
        transport=transport,
    )
    request = ContinuationRequest(
        "continue",
        plan,
        (),
        (),
        catalogue.fingerprint,
        PlanBudgets(),
        "manual",
        provenance(alice, "continuation"),
    )
    result = planner.continue_plan(request)
    assert result.patch is not None
    assert result.patch.fingerprint == patch.fingerprint
    assert len(transport.calls) == 2
    second = transport.calls[1]["json"]
    assert isinstance(second, dict)
    messages = second["messages"]
    assert isinstance(messages, list)
    assert "response was rejected" in messages[-1]["content"]


def test_malformed_output_after_repair_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    alice: Principal,
) -> None:
    monkeypatch.setenv("PLANNER_KEY", "key")
    catalogue = OperationCatalogue((), identity="empty")
    transport = Transport([response({"bad": True}), response({"still": "bad"})])
    planner = OpenAICompatiblePlanner(
        "https://planner.example/v1",
        "planner",
        catalogue,
        api_key_env="PLANNER_KEY",
        max_repairs=1,
        transport=transport,
    )
    request = PlanningRequest(
        "initial",
        "repair",
        (),
        catalogue.fingerprint,
        PlanBudgets(),
        provenance(alice, "request"),
    )
    result = planner.initial_plan(request)
    assert result.plan is None
    assert result.record.error is not None
    assert result.record.parsed_hash is None


def test_secret_catalogue_and_endpoint_failures_are_explicit(
    monkeypatch: pytest.MonkeyPatch,
    alice: Principal,
) -> None:
    catalogue = OperationCatalogue((), identity="empty")
    planner = OpenAICompatiblePlanner(
        "https://planner.example/v1",
        "planner",
        catalogue,
        api_key_env="MISSING_PLANNER_KEY",
        transport=Transport([]),
    )
    request = PlanningRequest(
        "initial",
        "repair",
        (),
        catalogue.fingerprint,
        PlanBudgets(),
        provenance(alice, "request"),
    )
    assert not planner.available()
    missing = planner.initial_plan(request)
    assert missing.plan is None
    assert "missing_secret_environment" in (missing.record.error or "")

    monkeypatch.setenv("MISSING_PLANNER_KEY", "key")
    mismatched = PlanningRequest(
        "initial",
        "repair",
        (),
        "wrong-catalogue",
        PlanBudgets(),
        provenance(alice, "request"),
    )
    rejected = planner.initial_plan(mismatched)
    assert rejected.plan is None
    assert rejected.record.error == "authenticated_catalogue_mismatch"

    with pytest.raises(ValueError, match="HTTPS"):
        OpenAICompatiblePlanner("http://remote.example/v1", "planner", catalogue)
    with pytest.raises(ValueError, match="policy"):
        OpenAICompatiblePlanner(
            "https://planner.example/v1",
            "planner",
            catalogue,
            max_repairs=-1,
        )
