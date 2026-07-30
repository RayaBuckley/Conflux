"""Strict AgentDojo 0.1.35 / benchmark v1.2.2 integration boundary.

The optional upstream package is imported only by :func:`load_pinned_suite`.
Offline result translation operates on retained, exact upstream JSON logs.
"""

from __future__ import annotations

import importlib.metadata
import json
from collections.abc import Mapping as MappingABC
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol, cast

from conflux.domain import canonical_json, fingerprint

PACKAGE_VERSION = "0.1.35"
BENCHMARK_VERSION = "v1.2.2"
INTEGRATION_SCHEMA = "conflux.agentdojo.v1"


class AgentDojoFailure(StrEnum):
    SETUP = "setup"
    MODEL = "model"
    PARSER = "parser"
    POLICY = "policy"
    SECURITY = "security"
    UTILITY = "utility"


class _ModelSchema(Protocol):
    def model_json_schema(self) -> dict[str, object]: ...


class _UpstreamFunction(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters(self) -> _ModelSchema: ...


class _UpstreamTask(Protocol):
    @property
    def ID(self) -> str: ...


class _UpstreamSuite(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def benchmark_version(self) -> tuple[int, int, int]: ...

    @property
    def tools(self) -> Sequence[_UpstreamFunction]: ...

    @property
    def user_tasks(self) -> MappingABC[str, _UpstreamTask]: ...

    @property
    def injection_tasks(self) -> MappingABC[str, _UpstreamTask]: ...


@dataclass(frozen=True, slots=True)
class AgentDojoTool:
    upstream_id: str
    description: str
    input_schema: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_schema", MappingProxyType(dict(self.input_schema)))

    def to_dict(self) -> dict[str, object]:
        return {
            "upstream_id": self.upstream_id,
            "description": self.description,
            "input_schema": dict(self.input_schema),
        }


@dataclass(frozen=True, slots=True)
class AgentDojoSuite:
    upstream_package_version: str
    benchmark_version: str
    suite_id: str
    user_task_ids: tuple[str, ...]
    injection_task_ids: tuple[str, ...]
    tools: tuple[AgentDojoTool, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": INTEGRATION_SCHEMA,
            "upstream_package_version": self.upstream_package_version,
            "benchmark_version": self.benchmark_version,
            "suite_id": self.suite_id,
            "user_task_ids": list(self.user_task_ids),
            "injection_task_ids": list(self.injection_task_ids),
            "tools": [tool.to_dict() for tool in self.tools],
        }


@dataclass(frozen=True, slots=True)
class AgentDojoResult:
    upstream_package_version: str
    benchmark_version: str
    suite_id: str
    pipeline_id: str
    user_task_id: str
    injection_task_id: str | None
    attack_id: str | None
    injections: Mapping[str, str]
    messages: tuple[Mapping[str, object], ...]
    native_utility: bool | None
    native_security: bool | None
    upstream_error: str | None
    failures: tuple[AgentDojoFailure, ...]
    raw_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "injections", MappingProxyType(dict(self.injections)))
        object.__setattr__(
            self,
            "messages",
            tuple(MappingProxyType(dict(message)) for message in self.messages),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": INTEGRATION_SCHEMA,
            "upstream_package_version": self.upstream_package_version,
            "benchmark_version": self.benchmark_version,
            "suite_id": self.suite_id,
            "pipeline_id": self.pipeline_id,
            "user_task_id": self.user_task_id,
            "injection_task_id": self.injection_task_id,
            "attack_id": self.attack_id,
            "injections": dict(self.injections),
            "messages": [dict(message) for message in self.messages],
            "native_metrics": {
                "utility": self.native_utility,
                "security": self.native_security,
            },
            "failures": [failure.value for failure in self.failures],
            "upstream_error": self.upstream_error,
            "raw_sha256": self.raw_sha256,
        }


def load_pinned_suite(suite_id: str) -> AgentDojoSuite:
    """Load upstream objects from exactly the integration's pinned package."""
    try:
        installed = importlib.metadata.version("agentdojo")
    except importlib.metadata.PackageNotFoundError as error:
        raise RuntimeError("agentdojo_setup_failure:not_installed") from error
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"agentdojo_setup_failure:unsupported_package:{installed}")
    from agentdojo.task_suite.load_suites import get_suite  # type: ignore[import-not-found]

    upstream = cast(_UpstreamSuite, get_suite(BENCHMARK_VERSION, suite_id))
    return translate_suite(upstream)


def translate_suite(upstream: _UpstreamSuite) -> AgentDojoSuite:
    expected_version = tuple(int(part) for part in BENCHMARK_VERSION.removeprefix("v").split("."))
    if upstream.benchmark_version != expected_version:
        raise ValueError(f"unsupported_agentdojo_benchmark:{upstream.benchmark_version!r}")
    tools = tuple(
        AgentDojoTool(
            upstream_id=tool.name,
            description=tool.description,
            input_schema=tool.parameters.model_json_schema(),
        )
        for tool in sorted(upstream.tools, key=lambda item: item.name)
    )
    return AgentDojoSuite(
        upstream_package_version=PACKAGE_VERSION,
        benchmark_version=BENCHMARK_VERSION,
        suite_id=upstream.name,
        user_task_ids=tuple(sorted(upstream.user_tasks)),
        injection_task_ids=tuple(sorted(upstream.injection_tasks)),
        tools=tools,
    )


def parse_upstream_log(path: Path) -> AgentDojoResult:
    """Translate the exact JSON emitted by AgentDojo 0.1.35 ``TraceLogger``."""
    raw = path.read_text(encoding="utf-8")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("agentdojo_parser_failure:invalid_json") from error
    if not isinstance(value, dict):
        raise ValueError("agentdojo_parser_failure:root_not_object")
    payload = cast(dict[str, Any], value)
    expected = {
        "suite_name",
        "pipeline_name",
        "user_task_id",
        "injection_task_id",
        "attack_type",
        "injections",
        "messages",
        "error",
        "utility",
        "security",
        "duration",
    }
    unknown = set(payload) - expected - {
        "evaluation_timestamp",
        "agentdojo_package_version",
        "benchmark_version",
    }
    if unknown:
        raise ValueError(f"agentdojo_parser_failure:unknown_fields:{','.join(sorted(unknown))}")
    for key in expected:
        if key not in payload:
            raise ValueError(f"agentdojo_parser_failure:missing_field:{key}")
    suite_id = _text(payload, "suite_name")
    pipeline_id = _text(payload, "pipeline_name")
    user_task_id = _text(payload, "user_task_id")
    injection_task_id = _optional_text(payload, "injection_task_id")
    attack_id = _optional_text(payload, "attack_type")
    injections = _string_map(payload["injections"])
    messages = _messages(payload["messages"])
    utility = _optional_bool(payload["utility"], "utility")
    security = _optional_bool(payload["security"], "security")
    upstream_error = _optional_text(payload, "error")
    failures: list[AgentDojoFailure] = []
    if upstream_error:
        failures.append(_classify_upstream_error(upstream_error))
    if utility is False:
        failures.append(AgentDojoFailure.UTILITY)
    if security is False:
        failures.append(AgentDojoFailure.SECURITY)
    return AgentDojoResult(
        upstream_package_version=str(payload.get("agentdojo_package_version", PACKAGE_VERSION)),
        benchmark_version=str(payload.get("benchmark_version", BENCHMARK_VERSION)),
        suite_id=suite_id,
        pipeline_id=pipeline_id,
        user_task_id=user_task_id,
        injection_task_id=injection_task_id,
        attack_id=attack_id,
        injections=injections,
        messages=messages,
        native_utility=utility,
        native_security=security,
        upstream_error=upstream_error,
        failures=tuple(failures),
        raw_sha256=fingerprint(json.loads(raw)),
    )


def write_translation(result: AgentDojoResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(result.to_dict()) + "\n", encoding="utf-8", newline="\n")


def classify_conflux_outcome(
    *,
    policy_blocked: bool,
    provider_failed: bool,
    native_security: bool | None,
    native_utility: bool | None,
) -> tuple[AgentDojoFailure, ...]:
    failures: list[AgentDojoFailure] = []
    if policy_blocked:
        failures.append(AgentDojoFailure.POLICY)
    if provider_failed:
        failures.append(AgentDojoFailure.SETUP)
    if native_security is False:
        failures.append(AgentDojoFailure.SECURITY)
    if native_utility is False:
        failures.append(AgentDojoFailure.UTILITY)
    return tuple(failures)


def _classify_upstream_error(error: str) -> AgentDojoFailure:
    lowered = error.lower()
    if "parse" in lowered or "invalid tool" in lowered:
        return AgentDojoFailure.PARSER
    if "model" in lowered or "context_length" in lowered or "api" in lowered:
        return AgentDojoFailure.MODEL
    return AgentDojoFailure.SETUP


def _text(payload: Mapping[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"agentdojo_parser_failure:{key}_not_text")
    return value


def _optional_text(payload: Mapping[str, object], key: str) -> str | None:
    value = payload[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"agentdojo_parser_failure:{key}_not_optional_text")
    return value


def _optional_bool(value: object, key: str) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    raise ValueError(f"agentdojo_parser_failure:{key}_not_optional_bool")


def _string_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or not isinstance(item, str)
        for key, item in value.items()
    ):
        raise ValueError("agentdojo_parser_failure:injections_not_string_map")
    return cast(dict[str, str], value)


def _messages(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError("agentdojo_parser_failure:messages_not_objects")
    messages = cast(list[dict[str, object]], value)
    for message in messages:
        if message.get("role") not in {"system", "user", "assistant", "tool"}:
            raise ValueError("agentdojo_parser_failure:unknown_message_role")
    return tuple(messages)


__all__ = [
    "AgentDojoFailure",
    "AgentDojoResult",
    "AgentDojoSuite",
    "AgentDojoTool",
    "BENCHMARK_VERSION",
    "INTEGRATION_SCHEMA",
    "PACKAGE_VERSION",
    "classify_conflux_outcome",
    "load_pinned_suite",
    "parse_upstream_log",
    "translate_suite",
    "write_translation",
]
