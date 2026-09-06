"""Comparative tests for multi-format model output parsing.

Tests that the harness correctly handles different output formats that small
models produce: JSON objects, Python dict literals, bare arrays, bare strings,
and markdown-fenced variants.  Each format is tested against the schemas used
by the AgentDojo and planning pipelines.
"""

from __future__ import annotations

from typing import Any

import pytest
from jsonschema import Draft202012Validator

from conflux.adapters.models import LocalModelFailure, TransformersLocalModel
from conflux.adapters.models.local_openai import (
    _extract_bare_array,
    _extract_bare_string,
    _extract_first_json,
    _extract_python_dict,
    _extract_structured,
)
from conflux.adapters.models.local_transformers import LocalTextGeneration
from conflux.experiments import LocalModelSpec
from conflux.ports import LocalModelRequest

pytestmark = pytest.mark.adapter


# ---------------------------------------------------------------------------
# Schemas mirroring the production pipelines
# ---------------------------------------------------------------------------

AGENTDOJO_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["final", "tool_call"],
    "properties": {
        "final": {"type": ["string", "null"]},
        "tool_call": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "arguments"],
                    "properties": {
                        "name": {"type": "string"},
                        "arguments": {"type": "object"},
                    },
                },
            ],
        },
    },
}

ACTION_LIST_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["action_ids"],
    "properties": {"action_ids": {"type": "array", "items": {"type": "string"}}},
}

ANSWER_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer"],
    "properties": {"answer": {"type": "string"}},
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _spec() -> LocalModelSpec:
    return LocalModelSpec(
        backend="transformers",
        model_id="test/model",
        revision="rev",
        weight_manifest_sha256="a" * 64,
        tokenizer_id="test/model",
        tokenizer_revision="rev",
        prompt_template_version="1",
        seed=0,
        temperature=0.0,
        top_p=1.0,
        max_output_tokens=32,
        context_limit=1024,
        device="cpu",
        dtype="float32",
        runtime_version="test",
    )


def _make_request(schema: dict[str, object], schema_name: str = "test") -> LocalModelRequest:
    return LocalModelRequest("req-1", "system", "user", schema_name, schema)


# ---------------------------------------------------------------------------
# JSON object parsing
# ---------------------------------------------------------------------------


class TestJsonParsing:
    def test_plain_json_object(self) -> None:
        result = _extract_first_json('{"answer":"ok"}')
        assert result == {"answer": "ok"}

    def test_json_with_surrounding_text(self) -> None:
        result = _extract_first_json('Here is the answer:\n{"answer":"ok"}\nDone.')
        assert result == {"answer": "ok"}

    def test_markdown_fenced_json(self) -> None:
        result = _extract_first_json('```json\n{"answer":"fenced"}\n```')
        assert result == {"answer": "fenced"}

    def test_no_brace_raises(self) -> None:
        with pytest.raises(ValueError, match="no_json_object_found"):
            _extract_first_json("no braces here")


# ---------------------------------------------------------------------------
# Python dict literal parsing
# ---------------------------------------------------------------------------


class TestPythonDictParsing:
    def test_python_dict_with_single_quotes(self) -> None:
        result = _extract_python_dict("{'answer': 'ok'}")
        assert result == {"answer": "ok"}

    def test_python_dict_with_trailing_comma(self) -> None:
        result = _extract_python_dict('{"answer": "ok",}')
        assert result == {"answer": "ok"}

    def test_python_dict_with_nested_list(self) -> None:
        result = _extract_python_dict("{'action_ids': ['write', 'read']}")
        assert result == {"action_ids": ["write", "read"]}

    def test_python_dict_no_brace_raises(self) -> None:
        with pytest.raises(ValueError, match="no_python_dict_found"):
            _extract_python_dict("no dict here")


# ---------------------------------------------------------------------------
# Bare array parsing (wraps based on schema)
# ---------------------------------------------------------------------------


class TestBareArrayParsing:
    def test_bare_array_wraps_action_ids(self) -> None:
        result = _extract_bare_array('["write","read"]', ACTION_LIST_SCHEMA)
        assert result == {"action_ids": ["write", "read"]}

    def test_bare_array_wraps_effects(self) -> None:
        schema: dict[str, object] = {
            "type": "object",
            "required": ["effects"],
            "properties": {"effects": {"type": "array"}},
        }
        result = _extract_bare_array('[{"id":"e1"}]', schema)
        assert result == {"effects": [{"id": "e1"}]}

    def test_bare_array_no_matching_field_raises(self) -> None:
        with pytest.raises(ValueError, match="bare_array_no_matching_schema_field"):
            _extract_bare_array('["write"]', ANSWER_SCHEMA)

    def test_bare_array_no_bracket_raises(self) -> None:
        with pytest.raises(ValueError, match="no_bare_array_found"):
            _extract_bare_array("no array here", ACTION_LIST_SCHEMA)


# ---------------------------------------------------------------------------
# Bare string parsing (wraps based on schema)
# ---------------------------------------------------------------------------


class TestBareStringParsing:
    def test_bare_string_wraps_final(self) -> None:
        result = _extract_bare_string("08:00", AGENTDOJO_SCHEMA)
        assert result == {"final": "08:00", "tool_call": None}

    def test_bare_string_wraps_answer(self) -> None:
        result = _extract_bare_string("ok", ANSWER_SCHEMA)
        assert result == {"answer": "ok"}

    def test_bare_string_strips_markdown_fence(self) -> None:
        result = _extract_bare_string("```\n08:00\n```", AGENTDOJO_SCHEMA)
        assert result == {"final": "08:00", "tool_call": None}

    def test_bare_string_starts_with_brace_raises(self) -> None:
        with pytest.raises(ValueError, match="no_bare_string_found"):
            _extract_bare_string('{"key":"val"}', AGENTDOJO_SCHEMA)

    def test_bare_string_no_matching_field_raises(self) -> None:
        schema: dict[str, object] = {"type": "object", "required": ["effects"]}
        with pytest.raises(ValueError, match="bare_string_no_matching_schema_field"):
            _extract_bare_string("some text", schema)


# ---------------------------------------------------------------------------
# Structured dispatcher (tries all parsers in sequence)
# ---------------------------------------------------------------------------


class TestExtractStructured:
    def test_json_takes_priority(self) -> None:
        result = _extract_structured('{"answer":"ok"}', ANSWER_SCHEMA)
        assert result == {"answer": "ok"}

    def test_python_dict_fallback(self) -> None:
        result = _extract_structured("{'answer': 'ok'}", ANSWER_SCHEMA)
        assert result == {"answer": "ok"}

    def test_bare_array_fallback(self) -> None:
        result = _extract_structured('["write"]', ACTION_LIST_SCHEMA)
        assert result == {"action_ids": ["write"]}

    def test_bare_string_fallback(self) -> None:
        result = _extract_structured("08:00", AGENTDOJO_SCHEMA)
        assert result == {"final": "08:00", "tool_call": None}

    def test_malformed_json_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            _extract_structured("{broken", ANSWER_SCHEMA)


# ---------------------------------------------------------------------------
# Integration: TransformersLocalModel with multi-format outputs
# ---------------------------------------------------------------------------


def _generator(content: str) -> Any:
    def gen(
        system_prompt: str,
        user_prompt: str,
        *,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        seed: int,
    ) -> LocalTextGeneration:
        return LocalTextGeneration(content, 10, 5)

    return gen


class TestTransformersMultiFormat:
    def test_json_output_validates(self) -> None:
        model = TransformersLocalModel(_spec(), generator=_generator('{"answer":"ok"}'), clock=lambda: 1.0)
        response = model.generate(_make_request(ANSWER_SCHEMA))
        assert response.payload == {"answer": "ok"}

    def test_python_dict_output_validates(self) -> None:
        model = TransformersLocalModel(_spec(), generator=_generator("{'answer': 'ok'}"), clock=lambda: 1.0)
        response = model.generate(_make_request(ANSWER_SCHEMA))
        assert response.payload == {"answer": "ok"}

    def test_bare_array_wraps_for_action_ids(self) -> None:
        model = TransformersLocalModel(_spec(), generator=_generator('["write"]'), clock=lambda: 1.0)
        response = model.generate(_make_request(ACTION_LIST_SCHEMA))
        assert response.payload == {"action_ids": ["write"]}

    def test_bare_string_wraps_for_agentdojo(self) -> None:
        model = TransformersLocalModel(_spec(), generator=_generator("08:00"), clock=lambda: 1.0)
        response = model.generate(_make_request(AGENTDOJO_SCHEMA))
        assert response.payload == {"final": "08:00", "tool_call": None}

    def test_malformed_json_still_fails(self) -> None:
        model = TransformersLocalModel(_spec(), generator=_generator("{broken"), clock=lambda: 1.0)
        with pytest.raises(LocalModelFailure, match="malformed_output"):
            model.generate(_make_request(ANSWER_SCHEMA))

    def test_markdown_fenced_json_still_works(self) -> None:
        model = TransformersLocalModel(_spec(), generator=_generator('```json\n{"answer":"fenced"}\n```'), clock=lambda: 1.0)
        response = model.generate(_make_request(ANSWER_SCHEMA))
        assert response.payload == {"answer": "fenced"}


# ---------------------------------------------------------------------------
# Parametrised: simulating different model output styles
# ---------------------------------------------------------------------------


_MODEL_OUTPUTS = [
    pytest.param('{"action_ids":["write"]}', "json_object", id="qwen-json"),
    pytest.param("{'action_ids': ['write']}", "python_dict", id="python-single-quote"),
    pytest.param('["write"]', "bare_array", id="qwen-1.5b-bare-array"),
    pytest.param('```json\n{"action_ids":["write"]}\n```', "fenced_json", id="qwen-3b-fenced"),
]


@pytest.mark.parametrize("output,expected_type", _MODEL_OUTPUTS)
def test_planning_action_ids_parses_all_formats(output: str, expected_type: str) -> None:
    result = _extract_structured(output, ACTION_LIST_SCHEMA)
    Draft202012Validator(ACTION_LIST_SCHEMA).validate(result)
    assert result["action_ids"] == ["write"]


_AGENTDOJO_OUTPUTS = [
    pytest.param('{"final":"08:00","tool_call":null}', "json_object", id="qwen-json"),
    pytest.param("08:00", "bare_string", id="qwen-3b-bare-string"),
    pytest.param("```\n08:00\n```", "fenced_string", id="fenced-bare-string"),
    pytest.param("{'final': '08:00', 'tool_call': None}", "python_dict", id="python-dict"),
]


@pytest.mark.parametrize("output,expected_type", _AGENTDOJO_OUTPUTS)
def test_agentdojo_final_parses_all_formats(output: str, expected_type: str) -> None:
    result = _extract_structured(output, AGENTDOJO_SCHEMA)
    Draft202012Validator(AGENTDOJO_SCHEMA).validate(result)
    assert result["final"] == "08:00"
    assert result["tool_call"] is None
