from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from conflux.adapters.benchmarks.agentdojo_v1 import (
    BENCHMARK_VERSION,
    AgentDojoFailure,
    classify_conflux_outcome,
    parse_upstream_log,
    translate_suite,
    write_translation,
)

pytestmark = pytest.mark.adapter

FIXTURE = Path(__file__).parent / "fixtures" / "agentdojo" / "v0.1.35" / "workspace-user_task_17-injection_task_1.json"


def test_real_upstream_log_translation_preserves_ids_and_metrics(tmp_path: Path) -> None:
    result = parse_upstream_log(FIXTURE)
    assert result.benchmark_version == BENCHMARK_VERSION
    assert result.suite_id == "workspace"
    assert result.user_task_id == "user_task_17"
    assert result.injection_task_id == "injection_task_1"
    assert result.attack_id == "important_instructions"
    assert result.native_utility is True
    assert result.native_security is False
    assert result.failures == (AgentDojoFailure.SECURITY,)
    output = tmp_path / "translated.json"
    write_translation(result, output)
    translated = json.loads(output.read_text(encoding="utf-8"))
    assert translated["native_metrics"] == {"security": False, "utility": True}
    assert translated["raw_sha256"] == result.raw_sha256


@dataclass
class _Schema:
    value: dict[str, object]

    def model_json_schema(self) -> dict[str, object]:
        return self.value


@dataclass
class _Tool:
    name: str
    description: str
    parameters: _Schema


@dataclass
class _Task:
    ID: str


@dataclass
class _Suite:
    name: str
    benchmark_version: tuple[int, int, int]
    tools: list[_Tool]
    user_tasks: dict[str, _Task]
    injection_tasks: dict[str, _Task]


def test_suite_translation_is_explicit_stable_and_versioned() -> None:
    suite = _Suite(
        "workspace",
        (1, 2, 2),
        [_Tool("z_tool", "Z", _Schema({"type": "object"})), _Tool("a_tool", "A", _Schema({}))],
        {"user_task_2": _Task("user_task_2"), "user_task_1": _Task("user_task_1")},
        {"injection_task_1": _Task("injection_task_1")},
    )
    translated = translate_suite(suite)
    assert translated.user_task_ids == ("user_task_1", "user_task_2")
    assert [tool.upstream_id for tool in translated.tools] == ["a_tool", "z_tool"]
    with pytest.raises(ValueError, match="unsupported_agentdojo_benchmark"):
        translate_suite(_Suite("workspace", (1, 0, 0), [], {}, {}))


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"unexpected": 1}, "unknown_fields"),
        ({"duration": ...}, "missing_field:duration"),
        ({"utility": "yes"}, "utility_not_optional_bool"),
        ({"injections": []}, "injections_not_string_map"),
        ({"messages": ["bad"]}, "messages_not_objects"),
        ({"messages": [{"role": "developer"}]}, "unknown_message_role"),
    ],
)
def test_upstream_log_parser_fails_closed(tmp_path: Path, mutation: dict[str, object], message: str) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for key, value in mutation.items():
        if value is ...:
            del payload[key]
        else:
            payload[key] = value
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        parse_upstream_log(path)


def test_failure_taxonomy_keeps_policy_security_and_utility_separate() -> None:
    assert classify_conflux_outcome(
        policy_blocked=True,
        provider_failed=False,
        native_security=False,
        native_utility=False,
    ) == (
        AgentDojoFailure.POLICY,
        AgentDojoFailure.SECURITY,
        AgentDojoFailure.UTILITY,
    )
    assert classify_conflux_outcome(
        policy_blocked=False,
        provider_failed=True,
        native_security=True,
        native_utility=True,
    ) == (AgentDojoFailure.TOOL,)
