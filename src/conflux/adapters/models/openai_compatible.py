"""Vendor-neutral OpenAI-compatible structured proposal adapter."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, cast
from urllib.parse import urlparse

from conflux.adapters.scenarios import load_schema, parse_proposal_batch
from conflux.domain import Artifact, PrimitiveAction, ProposalBatch, canonical_json


class ModelOutputError(ValueError):
    """The provider returned output that cannot be a canonical proposal."""


class ModelProviderError(RuntimeError):
    """The provider request failed or returned an HTTP failure."""


class HTTPResponse(Protocol):
    """Minimal protocol for an HTTP response."""

    @property
    def status_code(self) -> int:
        """Return the HTTP status code."""
        ...

    @property
    def text(self) -> str:
        """Return the raw response body as text."""
        ...

    def json(self) -> object:
        """Parse and return the response body as JSON."""
        ...


class HTTPTransport(Protocol):
    """Protocol for an HTTP transport that can POST JSON."""

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, object],
        timeout: float,
    ) -> HTTPResponse:
        """POST JSON to the given URL and return the response."""
        ...


@dataclass(frozen=True, slots=True)
class RawResponseRecord:
    """An immutable record of a raw HTTP response from a model provider."""

    status_code: int
    body_sha256: str
    body: object

    def to_dict(self) -> dict[str, object]:
        """Serialize this response record to a canonical dictionary."""
        return {
            "status_code": self.status_code,
            "body_sha256": self.body_sha256,
            "body": self.body,
        }


@dataclass(slots=True)
class OpenAICompatibleModel:
    """Vendor-neutral adapter for an OpenAI-compatible proposal model."""

    endpoint: str
    model: str
    allowed_resources: frozenset[tuple[str, str, str]]
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 30.0
    max_retries: int = 2
    backoff_seconds: float = 0.25
    transport: HTTPTransport | None = field(default=None, repr=False)
    responses: list[RawResponseRecord] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        parsed = urlparse(self.endpoint)
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
            raise ValueError("model endpoint must use HTTPS or loopback HTTP")
        if not self.model or not self.api_key_env:
            raise ValueError("model and API-key environment name must be non-empty")
        if self.timeout_seconds <= 0 or self.max_retries < 0 or self.backoff_seconds < 0:
            raise ValueError("invalid timeout or retry policy")
        self.allowed_resources = frozenset(self.allowed_resources)

    def available(self) -> bool:
        """Return whether the API key and HTTP transport are available."""
        if not os.environ.get(self.api_key_env):
            return False
        if self.transport is not None:
            return True
        from importlib.util import find_spec

        return find_spec("httpx") is not None

    def propose(self, inputs: tuple[Artifact[Any], ...]) -> ProposalBatch:
        """Request a structured proposal batch from the model for the given artifacts."""
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise ModelProviderError(f"missing_secret_environment:{self.api_key_env}")
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only a JSON proposal batch matching the supplied schema. Never claim authority or execute an action."
                    ),
                },
                {
                    "role": "user",
                    "content": canonical_json(
                        {
                            "artifacts": [
                                {
                                    "id": item.id,
                                    "value": item.value,
                                    "provenance": item.provenance.to_dict(),
                                }
                                for item in inputs
                            ]
                        }
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "conflux_proposal_batch_v1",
                    "strict": True,
                    "schema": load_schema("proposal-batch.schema.json"),
                },
            },
        }
        transport = self.transport or _HttpxTransport()
        last_error = "provider_request_failed"
        for attempt in range(self.max_retries + 1):
            try:
                response = transport.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
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
            self._retain(response, api_key)
            if response.status_code == 200:
                return self._parse(response, inputs)
            last_error = f"http_status:{response.status_code}"
            retryable = response.status_code == 429 or response.status_code >= 500
            if retryable and attempt < self.max_retries:
                time.sleep(self.backoff_seconds * (attempt + 1))
                continue
            raise ModelProviderError(last_error)
        raise ModelProviderError(last_error)

    def _retain(self, response: HTTPResponse, api_key: str) -> None:
        try:
            body = _redact(response.json(), api_key)
        except Exception:
            body = _redact(response.text, api_key)
        canonical = canonical_json(body)
        self.responses.append(
            RawResponseRecord(
                response.status_code,
                hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                body,
            )
        )

    def _parse(
        self,
        response: HTTPResponse,
        inputs: tuple[Artifact[Any], ...],
    ) -> ProposalBatch:
        try:
            body = cast(dict[str, Any], response.json())
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("message content must be a JSON string")
            proposal = json.loads(content)
            if not isinstance(proposal, dict):
                raise TypeError("proposal root must be an object")
            batch = parse_proposal_batch(cast(dict[str, Any], proposal), inputs)
            for action in batch.proposals:
                if (
                    isinstance(action, PrimitiveAction)
                    and action.resource is not None
                    and action.resource.key not in self.allowed_resources
                ):
                    raise ValueError(f"unknown_resource:{action.resource.key}")
            return batch
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as error:
            raise ModelOutputError(f"malformed_structured_output:{error}") from error


class _HttpxTransport:
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, object],
        timeout: float,
    ) -> HTTPResponse:
        """POST JSON using httpx and return the response."""
        try:
            import httpx
        except ImportError as error:
            raise ModelProviderError("optional_dependency_unavailable:httpx") from error
        return cast(
            HTTPResponse,
            httpx.post(
                url,
                headers=headers,
                json=json,
                timeout=timeout,
            ),
        )


def _redact(value: object, secret: str) -> object:
    if isinstance(value, dict):
        return {
            str(key): (
                "[REDACTED]"
                if any(token in str(key).lower() for token in ("authorization", "api_key", "secret", "token"))
                else _redact(item, secret)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item, secret) for item in value]
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]")
    return value


__all__ = [
    "HTTPResponse",
    "HTTPTransport",
    "ModelOutputError",
    "ModelProviderError",
    "OpenAICompatibleModel",
    "RawResponseRecord",
]
