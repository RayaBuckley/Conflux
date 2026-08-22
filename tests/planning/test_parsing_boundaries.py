"""Complete strict-parser coverage for untrusted planning responses."""

from __future__ import annotations

from copy import deepcopy

import pytest

from conflux.domain import Principal, Provenance
from conflux.planning import parse_node, parse_plan, parse_plan_patch

pytestmark = pytest.mark.security


def _provenance() -> Provenance:
    return Provenance.from_principal(Principal("alice", "Alice"), source="trusted")


def _binding(kind: str = "literal") -> dict[str, object]:
    if kind == "literal":
        return {"kind": "literal", "value": True, "provenance": {"ignored": True}}
    if kind == "artifact":
        return {"kind": "artifact", "artifact_id": "artifact"}
    return {"kind": "node_output", "node_id": "model", "output_name": "text"}


def _common(node_id: str, kind: str) -> dict[str, object]:
    return {
        "id": node_id,
        "kind": kind,
        "dependencies": [],
        "control_provenance": {"ignored": True},
    }


def _nodes() -> list[dict[str, object]]:
    model = {
        **_common("model", "model_call"),
        "prompt": _binding("artifact"),
        "output_name": "text",
    }
    action = {
        **_common("action", "action_template"),
        "template": {
            "id": "action",
            "operation_id": "filesystem.write",
            "operation_version": "1",
            "arguments": [
                {"name": "path", "binding": _binding("node_output")},
                {"name": "content", "binding": _binding()},
            ],
            "visibility": "participants",
        },
        "on_block": None,
        "on_failure": None,
        "output_name": "result",
    }
    branch = {
        **_common("branch", "branch"),
        "condition": _binding(),
        "when_true": "terminal",
        "when_false": "terminal",
    }
    loop = {
        **_common("loop", "loop"),
        "condition": _binding(),
        "body_node_id": "terminal",
        "exit_node_id": "terminal",
        "max_iterations": 2,
    }
    continuation = {
        **_common("continue", "continue_planning"),
        "observation_bindings": [_binding("artifact")],
        "trigger": "blocked",
    }
    approval = {**_common("approval", "approval"), "request": "confirm"}
    delegation = {**_common("delegation", "delegation"), "scope": "unsupported"}
    subplan = {**_common("subplan", "subplan"), "child_plan_id": "child"}
    terminal = {
        **_common("terminal", "terminal"),
        "outcome": "safe_stop",
        "reason": "done",
    }
    return [model, action, branch, loop, continuation, approval, delegation, subplan, terminal]


def test_every_node_and_binding_variant_parses_with_trusted_provenance() -> None:
    trusted = _provenance()
    parsed = [parse_node(node, trusted_provenance=trusted) for node in _nodes()]
    assert [node.id for node in parsed] == [
        "model",
        "action",
        "branch",
        "loop",
        "continue",
        "approval",
        "delegation",
        "subplan",
        "terminal",
    ]
    assert all(node.control_provenance == trusted for node in parsed)


def test_nested_plan_and_every_patch_operation_parse() -> None:
    trusted = _provenance()
    child = {
        "schema_version": "1",
        "id": "child",
        "goal": "child",
        "invocation_provenance": {"ignored": True},
        "nodes": [
            {
                **_common("child-done", "terminal"),
                "outcome": "succeeded",
                "reason": "done",
            }
        ],
        "subplans": [],
    }
    parent = {
        "schema_version": "1",
        "id": "parent",
        "goal": "parent",
        "invocation_provenance": {"ignored": True},
        "nodes": [
            {
                **_common("spawn", "subplan"),
                "child_plan_id": "child",
            }
        ],
        "subplans": [child],
    }
    assert parse_plan(parent, trusted_provenance=trusted).subplans[0].id == "child"
    terminal_node = {
        **_common("new-done", "terminal"),
        "outcome": "succeeded",
        "reason": "done",
    }
    operation = {
        "id": "operation",
        "kind": "terminate",
        "nodes": [],
        "target_node_ids": [],
        "subplans": [],
        "terminal_outcome": "safe_stop",
        "terminal_reason": "stop",
    }
    patch = {
        "schema_version": "1",
        "id": "patch",
        "plan_id": "parent",
        "operations": [
            {
                **operation,
                "id": "append",
                "kind": "append",
                "nodes": [terminal_node],
                "terminal_outcome": None,
                "terminal_reason": "",
            },
            {
                **operation,
                "id": "replace",
                "kind": "replace",
                "nodes": [terminal_node],
                "target_node_ids": ["spawn"],
                "terminal_outcome": None,
                "terminal_reason": "",
            },
            {**operation, "id": "spawn", "kind": "spawn_subplan", "subplans": [child]},
            operation,
        ],
    }
    parsed = parse_plan_patch(patch, trusted_provenance=trusted)
    assert len(parsed.operations) == 4
    assert parsed.operations[-1].terminal_outcome is not None


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"kind": "unknown"}, "unsupported plan node kind"),
        ({"kind": "terminal", "outcome": "unknown"}, "unsupported terminal outcome"),
        ({"kind": "action_template", "template.visibility": "private"}, "unsupported template visibility"),
        ({"kind": "model_call", "prompt.kind": "unknown"}, "unsupported binding kind"),
        ({"kind": "loop", "max_iterations": True}, "max_iterations must be an integer"),
    ],
)
def test_node_parser_rejects_unknown_enums_and_types(
    mutation: dict[str, object],
    message: str,
) -> None:
    by_kind = {node["kind"]: node for node in _nodes()}
    node = deepcopy(by_kind.get(str(mutation["kind"]), _nodes()[0]))
    if mutation["kind"] == "unknown":
        node["kind"] = "unknown"
    elif "outcome" in mutation:
        node["outcome"] = mutation["outcome"]
    elif "template.visibility" in mutation:
        node["template"]["visibility"] = mutation["template.visibility"]  # type: ignore[index]
    elif "prompt.kind" in mutation:
        node["prompt"]["kind"] = mutation["prompt.kind"]  # type: ignore[index]
    else:
        node["max_iterations"] = mutation["max_iterations"]
    with pytest.raises(ValueError, match=message):
        parse_node(node, trusted_provenance=_provenance())


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (None, "plan must be an object"),
        ({"schema_version": "1"}, "fields do not match schema"),
        (
            {
                "schema_version": "2",
                "id": "p",
                "goal": "g",
                "invocation_provenance": {},
                "nodes": [],
                "subplans": [],
            },
            "unsupported plan schema version",
        ),
    ],
)
def test_plan_parser_rejects_malformed_roots(
    payload: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_plan(payload, trusted_provenance=_provenance())


def test_patch_parser_rejects_unknown_version_and_operation() -> None:
    base: dict[str, object] = {
        "schema_version": "2",
        "id": "patch",
        "plan_id": "plan",
        "operations": [],
    }
    with pytest.raises(ValueError, match="unsupported patch schema version"):
        parse_plan_patch(base, trusted_provenance=_provenance())
    base["schema_version"] = "1"
    base["operations"] = [
        {
            "id": "bad",
            "kind": "invent",
            "nodes": [],
            "target_node_ids": [],
            "subplans": [],
            "terminal_outcome": None,
            "terminal_reason": "",
        }
    ]
    with pytest.raises(ValueError, match="unsupported patch operation"):
        parse_plan_patch(base, trusted_provenance=_provenance())
