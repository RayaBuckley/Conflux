"""Structured OpenAI-compatible adapter for initial plans and plan patches."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, cast
from urllib.parse import urlparse

from conflux.adapters.scenarios import load_schema
from conflux.domain import canonical_json, fingerprint
from conflux.planning import (
    ContinuationRequest,
    OperationCatalogue,
    Plan,
    PlannerRecord,
    PlanningRequest,
    PlanPatch,
    parse_plan,
    parse_plan_patch,
)
from conflux.ports import ContinuationResponse, InitialPlanResponse

from .openai_compatible import (
    HTTPResponse,
    HTTPTransport,
    ModelProviderError,
    RawResponseRecord,
    _HttpxTransport,
    _redact,
)

ParsedT = TypeVar("ParsedT", Plan, PlanPatch)


@dataclass(slots=True)
class OpenAICompatiblePlanner:
    """Structured OpenAI-compatible adapter for initial plans and plan patches."""

    endpoint: str
    model: str
    catalogue: OperationCatalogue
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 30.0
    max_retries: int = 2
    max_repairs: int = 1
    backoff_seconds: float = 0.25
    transport: HTTPTransport | None = field(default=None, repr=False)
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    responses: list[RawResponseRecord] = field(default_factory=list, init=False)
    records: list[PlannerRecord] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        parsed = urlparse(self.endpoint)
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
            raise ValueError("planner endpoint must use HTTPS or loopback HTTP")
        if not self.model or not self.api_key_env:
            raise ValueError("planner model and API-key environment name are required")
        if self.timeout_seconds <= 0 or self.max_retries < 0 or self.max_repairs < 0 or self.backoff_seconds < 0:
            raise ValueError("invalid planner timeout, retry, or repair policy")

    def available(self) -> bool:
        """Return whether the API key and HTTP transport are available."""
        if not os.environ.get(self.api_key_env):
            return False
        if self.transport is not None:
            return True
        from importlib.util import find_spec

        return find_spec("httpx") is not None

    def initial_plan(self, request: PlanningRequest) -> InitialPlanResponse:
        """Request an initial plan from the model for the given planning request."""
        if request.catalogue_fingerprint != self.catalogue.fingerprint:
            return InitialPlanResponse(
                None,
                self._failure_record(
                    request.to_dict(),
                    "authenticated_catalogue_mismatch",
                ),
            )
        parsed, record = self._structured_call(
            kind="initial_plan",
            request=request.to_dict(),
            schema_name="plan.schema.json",
            parser=lambda payload: parse_plan(
                payload,
                trusted_provenance=request.provenance,
            ),
        )
        return InitialPlanResponse(parsed, record)

    def continue_plan(self, request: ContinuationRequest) -> ContinuationResponse:
        """Request a plan patch from the model for the given continuation request."""
        if request.catalogue_fingerprint != self.catalogue.fingerprint:
            return ContinuationResponse(
                None,
                self._failure_record(
                    request.to_dict(),
                    "authenticated_catalogue_mismatch",
                ),
            )
        parsed, record = self._structured_call(
            kind="plan_patch",
            request=request.to_dict(),
            schema_name="plan-patch.schema.json",
            parser=lambda payload: parse_plan_patch(
                payload,
                trusted_provenance=request.provenance,
            ),
        )
        return ContinuationResponse(parsed, record)

    def _structured_call(
        self,
        *,
        kind: str,
        request: dict[str, object],
        schema_name: str,
        parser: Callable[[object], ParsedT],
    ) -> tuple[ParsedT | None, PlannerRecord]:
        secret = os.environ.get(self.api_key_env)
        if not secret:
            return None, self._failure_record(
                request,
                f"missing_secret_environment:{self.api_key_env}",
            )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    f"Return only a Conflux {kind} JSON object matching the supplied schema. "
                    "Operation identities must come from the authenticated catalogue. "
                    "Do not execute tools and do not assert provenance or authority."
                ),
            },
            {
                "role": "user",
                "content": canonical_json(
                    {
                        "request": request,
                        "authenticated_operation_catalogue": self.catalogue.to_dict(),
                    }
                ),
            },
        ]
        schema = load_schema(schema_name)
        started = self.clock()
        last_response: object = {"error": "no_response"}
        last_error = "planner_output_missing"
        usage: tuple[int | None, int | None] = (None, None)
        for repair in range(self.max_repairs + 1):
            payload: dict[str, object] = {
                "model": self.model,
                "messages": messages,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": f"conflux_{kind}_v1",
                        "strict": True,
                        "schema": schema,
                    },
                },
            }
            try:
                response = self._post(payload, secret)
                body = response.json()
                last_response = _redact(body, secret)
                usage = _usage(body)
                content = _message_content(body)
                decoded = json.loads(content)
                parsed = parser(decoded)
            except (
                ModelProviderError,
                KeyError,
                IndexError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as error:
                last_error = f"{type(error).__name__}: {error}"
                if repair < self.max_repairs and not isinstance(error, ModelProviderError):
                    messages.extend(
                        (
                            {
                                "role": "assistant",
                                "content": (
                                    content if "content" in locals() and isinstance(content, str) else canonical_json(last_response)
                                ),
                            },
                            {
                                "role": "system",
                                "content": (
                                    f"The response was rejected. Return a complete replacement JSON object only. Error: {last_error}"
                                ),
                            },
                        )
                    )
                    continue
                record = self._record(
                    request,
                    last_response,
                    None,
                    secret,
                    started,
                    usage,
                    last_error,
                )
                return None, record
            record = self._record(
                request,
                last_response,
                parsed.to_dict(),
                secret,
                started,
                usage,
                None,
            )
            return parsed, record
        return None, self._failure_record(request, last_error)

    def _post(self, payload: dict[str, object], secret: str) -> HTTPResponse:
        transport = self.transport or _HttpxTransport()
        last_error = "provider_request_failed"
        for attempt in range(self.max_retries + 1):
            try:
                response = transport.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {secret}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.timeout_seconds,
                )
            except Exception as error:
                last_error = f"transport_error:{type(error).__name__}"
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * (attempt + 1))
                    continue
                raise ModelProviderError(last_error) from error
            self._retain(response, secret)
            if response.status_code == 200:
                return response
            last_error = f"http_status:{response.status_code}"
            retryable = response.status_code == 429 or response.status_code >= 500
            if retryable and attempt < self.max_retries:
                time.sleep(self.backoff_seconds * (attempt + 1))
                continue
            raise ModelProviderError(last_error)
        raise ModelProviderError(last_error)

    def _retain(self, response: HTTPResponse, secret: str) -> None:
        try:
            body = _redact(response.json(), secret)
        except Exception:
            body = _redact(response.text, secret)
        encoded = canonical_json(body)
        self.responses.append(
            RawResponseRecord(
                response.status_code,
                hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
                body,
            )
        )

    def _record(
        self,
        request: object,
        response: object,
        parsed: object | None,
        secret: str,
        started: float,
        usage: tuple[int | None, int | None],
        error: str | None,
    ) -> PlannerRecord:
        redacted = _redact(response, secret)
        record = PlannerRecord(
            "openai-compatible-planner",
            "1",
            fingerprint(self._configuration()),
            fingerprint(request),
            fingerprint(redacted),
            fingerprint(parsed) if parsed is not None else None,
            canonical_json(redacted),
            usage[0],
            usage[1],
            max(0, round((self.clock() - started) * 1000)),
            error,
        )
        self.records.append(record)
        return record

    def _failure_record(self, request: object, error: str) -> PlannerRecord:
        record = PlannerRecord.create(
            planner_id="openai-compatible-planner",
            planner_version="1",
            configuration=self._configuration(),
            request=request,
            response={"error": error},
            parsed=None,
            raw_response=canonical_json({"error": error}),
            error=error,
        )
        self.records.append(record)
        return record

    def _configuration(self) -> dict[str, object]:
        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "catalogue_fingerprint": self.catalogue.fingerprint,
            "api_key_env": self.api_key_env,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "max_repairs": self.max_repairs,
        }


def _message_content(body: object) -> str:
    payload = cast(dict[str, Any], body)
    content = payload["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise TypeError("planner message content must be a JSON string")
    return content


def _usage(body: object) -> tuple[int | None, int | None]:
    if not isinstance(body, dict) or not isinstance(body.get("usage"), dict):
        return (None, None)
    usage = cast(dict[str, object], body["usage"])
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    return (
        prompt if isinstance(prompt, int) and not isinstance(prompt, bool) else None,
        completion if isinstance(completion, int) and not isinstance(completion, bool) else None,
    )


__all__ = ["OpenAICompatiblePlanner"]
