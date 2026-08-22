"""Structured adapter for loopback or explicitly private model servers."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import time
from dataclasses import dataclass, field
from importlib.util import find_spec
from typing import Any, Callable, cast
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, ValidationError

from conflux.domain import canonical_json
from conflux.ports import LocalModelPreflight, LocalModelRequest, LocalModelResponse, LocalModelSpec

from .openai_compatible import HTTPTransport, _HttpxTransport


class LocalModelFailure(RuntimeError):
    """A categorized local inference boundary failure."""

    def __init__(self, category: str, detail: str) -> None:
        self.category = category
        self.detail = detail
        super().__init__(f"{category}:{detail}")


@dataclass(slots=True)
class SelfHostedOpenAIModel:
    """Adapter for a self-hosted OpenAI-compatible local model server."""

    spec: LocalModelSpec
    transport: HTTPTransport | None = field(default=None, repr=False)
    timeout_seconds: float = 60.0
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)

    def __post_init__(self) -> None:
        if self.spec.backend != "openai_compatible" or self.spec.endpoint is None:
            raise ValueError("openai_compatible_spec_required")
        _network_scope(self.spec.endpoint, self.spec.allow_private_remote)
        if self.timeout_seconds <= 0:
            raise ValueError("local_model_timeout_invalid")

    def preflight(self) -> LocalModelPreflight:
        """Return availability and network-scope metadata for this model."""
        available = self.transport is not None or find_spec("httpx") is not None
        return LocalModelPreflight(
            backend=self.spec.backend,
            model_id=self.spec.model_id,
            available=available,
            network_scope=_network_scope(cast(str, self.spec.endpoint), self.spec.allow_private_remote),
            reason=None if available else "optional_dependency_unavailable:httpx",
        )

    def generate(self, request: LocalModelRequest) -> LocalModelResponse:
        """Send a structured chat-completion request and validate the response."""
        endpoint = cast(str, self.spec.endpoint).rstrip("/") + "/chat/completions"
        body: dict[str, object] = {
            "model": self.spec.model_id,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "seed": self.spec.seed,
            "temperature": self.spec.temperature,
            "top_p": self.spec.top_p,
            "max_tokens": self.spec.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.schema_name,
                    "strict": True,
                    "schema": dict(request.schema),
                },
            },
        }
        started = self.clock()
        try:
            response = (self.transport or _HttpxTransport()).post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json=body,
                timeout=self.timeout_seconds,
            )
        except Exception as error:
            raise LocalModelFailure("endpoint", f"transport_error:{type(error).__name__}") from error
        latency = max(0, round((self.clock() - started) * 1000))
        if response.status_code != 200:
            category = "context" if response.status_code == 400 else "endpoint"
            raise LocalModelFailure(category, f"http_status:{response.status_code}")
        try:
            raw = cast(dict[str, Any], response.json())
            reported_model = raw["model"]
            if reported_model != self.spec.model_id:
                raise LocalModelFailure("identity", f"reported_model_mismatch:{reported_model}")
            content = raw["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("content_not_string")
            decoded = json.loads(content)
            if not isinstance(decoded, dict):
                raise TypeError("structured_root_not_object")
            Draft202012Validator(dict(request.schema)).validate(decoded)
            prompt_tokens, output_tokens = _usage(raw)
        except LocalModelFailure:
            raise
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as error:
            raise LocalModelFailure("malformed_output", str(error)) from error
        raw_hash = hashlib.sha256(canonical_json(raw).encode("utf-8")).hexdigest()
        return LocalModelResponse(
            request.request_id,
            self.spec.model_id,
            cast(dict[str, object], decoded),
            prompt_tokens,
            output_tokens,
            latency,
            raw_hash,
        )


def _network_scope(endpoint: str, allow_private_remote: bool) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        raise ValueError("local_model_endpoint_invalid")
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        return "loopback"
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        address = None
    if not allow_private_remote:
        raise ValueError("private_remote_requires_explicit_enablement")
    if address is not None and not address.is_private:
        raise ValueError("public_model_endpoint_forbidden")
    return "private_remote"


def _usage(body: dict[str, Any]) -> tuple[int | None, int | None]:
    usage = body.get("usage")
    if not isinstance(usage, dict):
        return None, None
    prompt = usage.get("prompt_tokens")
    output = usage.get("completion_tokens")
    return (
        prompt if isinstance(prompt, int) and not isinstance(prompt, bool) else None,
        output if isinstance(output, int) and not isinstance(output, bool) else None,
    )


__all__ = ["LocalModelFailure", "SelfHostedOpenAIModel"]
