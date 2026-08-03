"""Installed-command behavior without network access or credentials."""

from __future__ import annotations

import json
from pathlib import Path

from conflux.cli import (
    EXIT_INVALID_EVIDENCE,
    EXIT_OK,
    EXIT_USAGE,
    main,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples" / "basic.yaml"
AGENTDOJO_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "agentdojo"
    / "v0.1.35"
    / "workspace-user_task_17-injection_task_1.json"
)
AGENTDOJO_MANIFEST = ROOT / "experiments" / "manifests" / "agentdojo-smoke.yaml"
LAPTOP_SMOKE_PLAN = ROOT / "experiments/manifests/planning-laptop-smoke-v1.json"
CEDAR_BUNDLE = ROOT / "experiments/manifests/cedar-policy-bundle-v1.json"
CEDAR_CORPUS = ROOT / "experiments/suites/cedar-differential-v1.json"


def _write_protocol(path: Path, track: str, *, model: bool) -> None:
    payload: dict[str, object] = {
        "schema_version": "2",
        "id": f"cli-{track}",
        "track": track,
        "suite": {"id": f"{track}-test", "version": "1"},
        "source_commit": "abcdef0",
        "inputs": {},
        "model": None,
        "prompts": {},
        "seeds": [7],
        "repetitions": 1,
        "bounds": {"max_model_calls": 2, "max_steps": 4, "max_depth": 3},
        "environment": {"class": "test"},
        "output_directory": str(path.parent / "default-output"),
        "rerun_command": ["conflux", track],
    }
    if model:
        payload["model"] = {
            "backend": "transformers",
            "model_id": "locally-cached-test-model",
            "revision": "immutable-test-revision",
            "weight_manifest_sha256": "0" * 64,
            "tokenizer_id": "locally-cached-test-tokenizer",
            "tokenizer_revision": "immutable-test-revision",
            "prompt_template_version": "test-v1",
            "seed": 7,
            "temperature": 0,
            "top_p": 1,
            "max_output_tokens": 128,
            "context_limit": 2048,
            "device": "cpu",
            "dtype": "float32",
            "runtime_version": "test",
            "endpoint": None,
            "allow_private_remote": False,
        }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_laptop_protocol(path: Path, backend: str) -> None:
    plan = json.loads(LAPTOP_SMOKE_PLAN.read_text(encoding="utf-8"))
    is_llama = backend == "openai_compatible"
    payload = {
        "schema_version": "2",
        "id": f"laptop-{'llama' if is_llama else 'transformers'}",
        "track": "planning",
        "suite": {
            "id": "planning-diagnostic-v1",
            "version": "1",
            "case_ids": plan["scenario_ids"],
        },
        "source_commit": "abcdef0",
        "inputs": {},
        "model": {
            "backend": backend,
            "model_id": (
                plan["generated_llama_model_id"]
                if is_llama
                else plan["source_model_id"]
            ),
            "revision": plan["source_revision"],
            "weight_manifest_sha256": ("b" if is_llama else "a") * 64,
            "tokenizer_id": plan["tokenizer_id"],
            "tokenizer_revision": plan["tokenizer_revision"],
            "prompt_template_version": plan["prompt_template_version"],
            "seed": plan["seed"],
            "temperature": 0,
            "top_p": 1,
            "max_output_tokens": 128,
            "context_limit": 2048,
            "device": "cpu",
            "dtype": "Q8_0" if is_llama else "float32",
            "runtime_version": "llama.cpp-b9637-test" if is_llama else "test",
            "endpoint": "http://127.0.0.1:8080/v1" if is_llama else None,
            "allow_private_remote": False,
        },
        "prompts": {"planner": plan["prompt_template_version"]},
        "seeds": [plan["seed"]],
        "repetitions": 1,
        "bounds": plan["bounds"],
        "environment": {"class": "operator-configured"},
        "output_directory": str(path.parent / "laptop-output"),
        "rerun_command": ["conflux", "plan", "laptop-smoke", "--execute-local"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_demo_writes_linked_trace_result_and_report(
    tmp_path: Path,
    capsys: object,
) -> None:
    _ = capsys
    output = tmp_path / "run"
    assert main(["demo", "--scenario", str(SCENARIO), "--output", str(output)]) == EXIT_OK
    payload = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert payload["diagnostics"]["executed"] == 1
    assert payload["utility"]["completed"]
    assert (output / "trace.jsonl").is_file()
    assert (output / "report.md").is_file()


def test_native_sled_command_writes_verification_result(tmp_path: Path) -> None:
    output = tmp_path / "sled"
    assert (
        main(
            [
                "sled",
                "run",
                "--suite",
                str(SCENARIO),
                "--output",
                str(output),
            ]
        )
        == EXIT_OK
    )
    payload = json.loads((output / "verification.json").read_text(encoding="utf-8"))
    assert payload["verdict"] == "safe"


def test_dynamic_plan_demo_writes_replayable_evidence(
    tmp_path: Path,
    capsys: object,
) -> None:
    output = tmp_path / "plan-demo"
    assert main(["plan", "demo", "--output", str(output)]) == EXIT_OK
    payload = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert payload["completed"] is True
    assert payload["state"]["status"] == "safe_stop"
    assert (output / "trace.jsonl").is_file()
    summary = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert summary["blocked"] == 1
    assert summary["executed"] == 1


def test_report_and_doctor_have_machine_readable_modes(
    tmp_path: Path,
    capsys: object,
) -> None:
    _ = capsys
    output = tmp_path / "run"
    assert main(["demo", "--scenario", str(SCENARIO), "--output", str(output)]) == EXIT_OK
    assert main(["report", str(output / "result.json"), "--json"]) == EXIT_OK
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert json.loads(captured.out.splitlines()[-1])["schema_version"] == "1"

    assert main(["doctor", "--json"]) == EXIT_OK
    doctor = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert doctor["schema_version"] == "1"
    assert "agentdojo" in doctor["optional_backends"]


def test_unavailable_backends_and_invalid_evidence_fail_closed(
    tmp_path: Path,
) -> None:
    assert main(["verify"]) == EXIT_USAGE
    assert main(["benchmark", "agentdojo", "--config", "missing.yaml"]) == EXIT_USAGE

    invalid = tmp_path / "result.json"
    invalid.write_text('{"schema_version":"1"}', encoding="utf-8")
    assert main(["report", str(invalid)]) == EXIT_INVALID_EVIDENCE


def test_agentdojo_command_translates_retained_upstream_log(
    tmp_path: Path,
    capsys: object,
) -> None:
    output = tmp_path / "translated.json"
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "--config",
                str(AGENTDOJO_MANIFEST),
                "--upstream-log",
                str(AGENTDOJO_FIXTURE),
                "--output",
                str(output),
            ]
        )
        == EXIT_OK
    )
    assert json.loads(output.read_text())["user_task_id"] == "user_task_17"
    summary = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert summary["native_security"] is False


def test_text_modes_selection_and_optional_failures_are_explicit(
    tmp_path: Path,
    capsys: object,
) -> None:
    output = tmp_path / "run"
    assert main(["demo", "--scenario", str(SCENARIO), "--output", str(output)]) == EXIT_OK
    assert main(["report", str(output / "result.json")]) == EXIT_OK
    assert "# Conflux run" in capsys.readouterr().out  # type: ignore[attr-defined]
    assert main(["doctor"]) == EXIT_OK
    assert "Conflux doctor:" in capsys.readouterr().out  # type: ignore[attr-defined]
    assert (
        main(
            [
                "demo",
                "--scenario",
                str(SCENARIO),
                "--output",
                str(tmp_path / "invalid"),
                "--select-branch",
                "missing",
            ]
        )
        == EXIT_USAGE
    )
    assert (
        main(
            [
                "chat",
                "--scenario",
                str(SCENARIO),
                "--endpoint",
                "http://127.0.0.1:1/v1/chat/completions",
                "--model",
                "unavailable",
                "--principal",
                "missing",
            ]
        )
        == EXIT_USAGE
    )


def test_verify_cli_retains_unknown_optional_backend_result(
    tmp_path: Path,
) -> None:
    model = tmp_path / "model.json"
    model.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "id": "cli-model",
                "bound": 1,
                "assumptions": [],
                "variables": [
                    {
                        "name": "safe",
                        "sort": "boolean",
                        "initial": True,
                        "minimum": None,
                        "maximum": None,
                    }
                ],
                "transitions": [],
                "invariants": [
                    {
                        "id": "safe",
                        "expression": {
                            "kind": "variable",
                            "value": "safe",
                            "arguments": [],
                        },
                        "description": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "verify"
    assert (
        main(
            [
                "verify",
                "--model",
                str(model),
                "--property",
                "safe",
                "--backend",
                "z3",
                "--output",
                str(output),
            ]
        )
        == 3
    )
    assert json.loads((output / "formal-verification.json").read_text())["verdict"] == "unknown"
    assert (
        main(["verify", "--model", str(model), "--property", "missing"])
        == EXIT_USAGE
    )


def test_verify_cli_emits_cone_reduction_comparison(tmp_path: Path) -> None:
    model = tmp_path / "reducible.json"
    model.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "id": "reducible",
                "bound": 2,
                "assumptions": [],
                "variables": [
                    {
                        "name": name,
                        "sort": "boolean",
                        "initial": name == "safe",
                        "minimum": None,
                        "maximum": None,
                    }
                    for name in ("safe", "noise")
                ],
                "transitions": [
                    {
                        "id": "noise-only",
                        "guard": {
                            "kind": "constant",
                            "value": True,
                            "arguments": [],
                        },
                        "assignments": [
                            {
                                "variable": "noise",
                                "expression": {
                                    "kind": "not",
                                    "value": None,
                                    "arguments": [
                                        {
                                            "kind": "variable",
                                            "value": "noise",
                                            "arguments": [],
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ],
                "invariants": [
                    {
                        "id": "safe",
                        "expression": {
                            "kind": "variable",
                            "value": "safe",
                            "arguments": [],
                        },
                        "description": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "reduced"
    assert (
        main(
            [
                "verify",
                "--model",
                str(model),
                "--property",
                "safe",
                "--reduce",
                "cone_of_influence",
                "--output",
                str(output),
            ]
        )
        == 3
    )
    report = json.loads((output / "verification-reduction.json").read_text())
    assert report["comparison"]["equivalent"] is True
    assert report["comparison"]["reduction"]["removed_variables"] == ["noise"]
    assert report["backend"]["failure"] == "backend_unavailable_or_failed"
    assert (output / "formal-verification-original.json").is_file()


def test_live_agentdojo_gate_reports_missing_optional_package() -> None:
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "--config",
                str(AGENTDOJO_MANIFEST),
            ]
        )
        == 3
    )


def test_model_dependent_commands_preflight_without_model_invocation(
    tmp_path: Path,
    capsys: object,
) -> None:
    planning = tmp_path / "planning.json"
    _write_protocol(planning, "planning", model=True)
    planning_output = tmp_path / "planning-output"
    assert (
        main(
            [
                "plan",
                "compare",
                "--config",
                str(planning),
                "--output",
                str(planning_output),
            ]
        )
        == EXIT_OK
    )
    plan_preflight = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert plan_preflight["execute_local"] is False
    assert len(plan_preflight["matrix"]) == 32
    assert json.loads((planning_output / "preflight.json").read_text())["complete"] is False

    transformers = tmp_path / "laptop-transformers.json"
    llama = tmp_path / "laptop-llama.json"
    _write_laptop_protocol(transformers, "transformers")
    _write_laptop_protocol(llama, "openai_compatible")
    assert (
        main(
            [
                "plan",
                "laptop-smoke",
                "--plan",
                str(LAPTOP_SMOKE_PLAN),
                "--transformers-config",
                str(transformers),
                "--llama-config",
                str(llama),
                "--output",
                str(tmp_path / "laptop-output"),
            ]
        )
        == EXIT_OK
    )
    laptop_preflight = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert laptop_preflight["execute_local"] is False
    assert laptop_preflight["stop_after_bundle"] is True
    assert len(laptop_preflight["matrix"]) == 16
    assert (tmp_path / "laptop-output" / "preflight.json").is_file()

    agentdojo = tmp_path / "agentdojo.json"
    _write_protocol(agentdojo, "agentdojo", model=True)
    benchmark_output = tmp_path / "agentdojo-output"
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "--config",
                str(agentdojo),
                "--output",
                str(benchmark_output),
            ]
        )
        == EXIT_OK
    )
    benchmark_preflight = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert benchmark_preflight["execute_local"] is False
    assert len(benchmark_preflight["matrix"]) == 4
    assert (benchmark_output / "preflight.json").is_file()

    assert main(["doctor", "--local-model-config", str(planning), "--json"]) == EXIT_OK
    doctor = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert doctor["local_model"]["network_scope"] == "none"


def test_direction_security_preflight_commands_are_offline(
    tmp_path: Path,
    capsys: object,
) -> None:
    delegation_output = tmp_path / "delegation"
    assert main(["sled", "delegation", "--output", str(delegation_output)]) == EXIT_OK
    delegation = json.loads(
        (delegation_output / "delegation-verification.json").read_text()
    )
    assert delegation["runtime_enabled"] is False
    assert delegation["canonical"]["verdict"] == "safe"
    assert len(delegation["mutants"]) == 7
    assert all(item["killed"] for item in delegation["mutants"])
    capsys.readouterr()  # type: ignore[attr-defined]

    cedar_output = tmp_path / "cedar"
    assert (
        main(
            [
                "policy",
                "cedar",
                "preflight",
                "--bundle",
                str(CEDAR_BUNDLE),
                "--corpus",
                str(CEDAR_CORPUS),
                "--output",
                str(cedar_output),
            ]
        )
        == EXIT_OK
    )
    cedar = json.loads((cedar_output / "preflight.json").read_text())
    assert cedar["classification"] == "evaluation_ready"
    assert cedar["complete"] is False
    assert cedar["binary_preflight"]["invoked"] is False
    assert cedar["binary_preflight"]["reason"] == "binary_not_supplied"
    capsys.readouterr()  # type: ignore[attr-defined]

    assert (
        main(
            [
                "doctor",
                "--cedar-bundle",
                str(CEDAR_BUNDLE),
                "--json",
            ]
        )
        == EXIT_OK
    )
    doctor = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert doctor["cedar"]["expected_version"] == "4.11.0"
    assert doctor["cedar"]["available"] is False
    assert doctor["cedar"]["invoked"] is False


def test_native_reproduction_cli_and_version_two_report(
    tmp_path: Path,
    capsys: object,
) -> None:
    protocol = tmp_path / "native.json"
    output = tmp_path / "native-output"
    _write_protocol(protocol, "native_sled", model=False)
    assert (
        main(
            [
                "sled",
                "reproduce",
                "--protocol",
                str(protocol),
                "--output",
                str(output),
            ]
        )
        == EXIT_OK
    )
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert result["complete"] is True
    assert len(result["negative_controls"]) == 5
    assert all(control["killed"] for control in result["negative_controls"])
    capsys.readouterr()  # type: ignore[attr-defined]
    assert main(["report", str(output / "result.json")]) == EXIT_OK
    assert "# Conflux native SLED result" in capsys.readouterr().out  # type: ignore[attr-defined]
