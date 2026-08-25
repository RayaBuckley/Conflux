"""Installed-command behavior without network access or credentials."""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import conflux.cli as cli_module
from conflux.cli import (
    EXIT_INVALID_EVIDENCE,
    EXIT_OK,
    EXIT_USAGE,
    main,
)
from conflux.experiments import ExperimentProtocol, load_protocol
from conflux.ports import LocalModelPreflight

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples" / "basic.yaml"
AGENTDOJO_FIXTURE = ROOT / "tests" / "fixtures" / "agentdojo" / "v0.1.35" / "workspace-user_task_17-injection_task_1.json"
AGENTDOJO_MANIFEST = ROOT / "research" / "experiments" / "manifests" / "agentdojo-smoke.yaml"
LAPTOP_SMOKE_PLAN = ROOT / "research/experiments/manifests/planning-laptop-smoke-v1.json"
CEDAR_BUNDLE = ROOT / "research/experiments/manifests/cedar-policy-bundle-v1.json"
CEDAR_CORPUS = ROOT / "research/experiments/suites/cedar-differential-v1.json"


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
            "model_id": (plan["generated_llama_model_id"] if is_llama else plan["source_model_id"]),
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


def test_demo_retains_manifest_and_reports_an_all_blocked_scenario(
    tmp_path: Path,
) -> None:
    blocked_scenario = tmp_path / "blocked.yaml"
    blocked_scenario.write_text(
        SCENARIO.read_text(encoding="utf-8").replace("consent: [write-output]", "consent: []"),
        encoding="utf-8",
    )
    output = tmp_path / "blocked-run"
    assert (
        main(
            [
                "demo",
                "--scenario",
                str(blocked_scenario),
                "--manifest",
                str(ROOT / "research/experiments/manifests/m3-smoke.yaml"),
                "--output",
                str(output),
            ],
        )
        == EXIT_OK
    )
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert result["diagnostics"]["blocked"] == 1
    assert result["diagnostics"]["executed"] == 0
    assert result["utility"]["completed"] is False
    assert (output / "manifest.json").is_file()


def test_visualise_writes_evidence_from_demo_result(tmp_path: Path) -> None:
    demo_output = tmp_path / "run"
    assert main(["demo", "--scenario", str(SCENARIO), "--output", str(demo_output)]) == EXIT_OK
    evidence_output = tmp_path / "evidence"
    assert (
        main(
            [
                "visualise",
                str(demo_output / "result.json"),
                "--output",
                str(evidence_output),
            ],
        )
        == EXIT_OK
    )
    assert (evidence_output / "manifest.json").is_file()
    assert (evidence_output / "index.html").is_file()


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
            ],
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
    stdout = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "Plan status: safe_stop" in stdout
    assert "Blocked: 1" in stdout
    assert "Executed: 1" in stdout


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
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "preflight",
                "--config",
                "missing.json",
                "--output",
                str(tmp_path / "missing"),
            ],
        )
        == EXIT_USAGE
    )

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
                "translate",
                "--config",
                str(AGENTDOJO_MANIFEST),
                "--upstream-log",
                str(AGENTDOJO_FIXTURE),
                "--output",
                str(output),
            ],
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
            ],
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
            ],
        )
        == EXIT_USAGE
    )


def test_verify_cli_retains_unknown_optional_backend_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "z3", None)
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
                    },
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
                    },
                ],
            },
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
            ],
        )
        == 3
    )
    assert json.loads((output / "formal-verification.json").read_text())["verdict"] == "unknown"
    summary = (output / "summary.md").read_text(encoding="utf-8")
    assert "No security conclusion" in summary
    assert "Configured bound: `1`" in summary
    assert main(["verify", "--model", str(model), "--property", "missing"]) == EXIT_USAGE


def test_verify_cli_emits_cone_reduction_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "z3", None)
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
                                        },
                                    ],
                                },
                            },
                        ],
                    },
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
                    },
                ],
            },
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
            ],
        )
        == 3
    )
    report = json.loads((output / "verification-reduction.json").read_text())
    assert report["comparison"]["equivalent"] is True
    assert report["comparison"]["reduction"]["removed_variables"] == ["noise"]
    assert report["backend"]["failure"] == "backend_unavailable_or_failed"
    assert (output / "formal-verification-original.json").is_file()
    summary = (output / "summary.md").read_text(encoding="utf-8")
    assert "Original/reduced states: `" in summary
    assert "Retained/removed variables: `1 / 1`" in summary


def test_verify_cli_explains_unavailable_nuxmv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "conflux.verification.nuxmv_backend.shutil.which",
        lambda _: None,
    )
    model = tmp_path / "model.json"
    model.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "id": "nuxmv-unavailable",
                "bound": 1,
                "assumptions": [],
                "variables": [
                    {
                        "name": "safe",
                        "sort": "boolean",
                        "initial": True,
                        "minimum": None,
                        "maximum": None,
                    },
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
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    output = tmp_path / "nuxmv"
    assert (
        main(
            [
                "verify",
                "--model",
                str(model),
                "--property",
                "safe",
                "--backend",
                "nuxmv",
                "--output",
                str(output),
            ],
        )
        == 3
    )
    summary = (output / "summary.md").read_text(encoding="utf-8")
    assert "optional binary unavailable; no conclusion" in summary
    assert "conflux verify --model" in summary


def test_live_agentdojo_gate_reports_missing_optional_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(_: str) -> str:
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(
        "conflux.adapters.benchmarks.agentdojo_v1.importlib.metadata.version",
        missing,
    )
    protocol = tmp_path / "agentdojo.json"
    output = tmp_path / "preflight"
    _write_protocol(protocol, "agentdojo", model=True)
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "preflight",
                "--config",
                str(protocol),
                "--output",
                str(output),
            ],
        )
        == EXIT_OK
    )
    preflight = json.loads((output / "preflight.json").read_text())
    assert preflight["classification"] == "partial"
    assert "agentdojo_setup_failure:not_installed" in preflight["suite_error"]


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
            ],
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
            ],
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
                "preflight",
                "--config",
                str(agentdojo),
                "--output",
                str(benchmark_output),
            ],
        )
        == EXIT_OK
    )
    benchmark_preflight = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert benchmark_preflight["execute_local"] is False
    assert len(benchmark_preflight["matrix"]) == 6
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
    delegation = json.loads((delegation_output / "delegation-verification.json").read_text())
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
            ],
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
            ],
        )
        == EXIT_OK
    )
    doctor = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert doctor["cedar"]["expected_version"] == "4.12.0"
    assert doctor["cedar"]["available"] is False
    assert doctor["cedar"]["invoked"] is False


def test_laptop_cli_retains_a_complete_fake_backed_live_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transformers = tmp_path / "transformers.json"
    llama = tmp_path / "llama.json"
    output = tmp_path / "laptop-live"
    _write_laptop_protocol(transformers, "transformers")
    _write_laptop_protocol(llama, "openai_compatible")

    class AvailableModel:
        def __init__(self, backend: str, model_id: str) -> None:
            self.backend = backend
            self.model_id = model_id

        def preflight(self) -> LocalModelPreflight:
            return LocalModelPreflight(self.backend, self.model_id, True, "loopback", None)

    def model_for(protocol: ExperimentProtocol) -> AvailableModel:
        assert protocol.model is not None
        return AvailableModel(protocol.model.backend, protocol.model.model_id)

    plan = json.loads(LAPTOP_SMOKE_PLAN.read_text(encoding="utf-8"))
    observations = [
        {
            "backend_id": backend,
            "case_id": f"{backend}:{scenario}:{mode}",
            "security_violations": 0,
        }
        for backend in plan["backends"]
        for scenario in plan["scenario_ids"]
        for mode in plan["modes"]
    ]
    monkeypatch.setattr(cli_module, "_local_model", model_for)
    monkeypatch.setattr(
        cli_module,
        "run_laptop_planning_smoke",
        lambda *_: {
            "schema_version": "1",
            "complete": True,
            "model_identities": {},
            "observations": observations,
        },
    )
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
                str(output),
                "--execute-local",
            ],
        )
        == EXIT_OK
    )
    assert (output / "CHECKSUMS.sha256").is_file()
    assert (output / "manifest.json").is_file()
    assert len((output / "raw-results.jsonl").read_text().splitlines()) == 16
    assert (output / "transformers" / "result.json").is_file()
    assert (output / "llama_cpp_q8_0" / "result.json").is_file()


def test_laptop_cli_live_gate_reports_unavailable_runtimes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transformers = tmp_path / "transformers.json"
    llama = tmp_path / "llama.json"
    _write_laptop_protocol(transformers, "transformers")
    _write_laptop_protocol(llama, "openai_compatible")

    class UnavailableModel:
        def __init__(self, backend: str, model_id: str) -> None:
            self.backend = backend
            self.model_id = model_id

        def preflight(self) -> LocalModelPreflight:
            return LocalModelPreflight(self.backend, self.model_id, False, "none", "fixture_unavailable")

    def model_for(protocol: ExperimentProtocol) -> UnavailableModel:
        assert protocol.model is not None
        return UnavailableModel(protocol.model.backend, protocol.model.model_id)

    monkeypatch.setattr(cli_module, "_local_model", model_for)
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
                "--execute-local",
            ],
        )
        == EXIT_USAGE
    )


def test_chat_cli_routes_a_turn_and_handles_end_of_input(
    monkeypatch: pytest.MonkeyPatch,
    capsys: object,
) -> None:
    class AvailableChatModel:
        api_key_env = "TEST_KEY"

        def available(self) -> bool:
            return True

    class FakeRuntime:
        def __init__(self, *_: object) -> None:
            pass

        def submit(self, text: str) -> object:
            assert text == "hello"
            report = SimpleNamespace(run_id="chat-run", blocked_count=1)
            return SimpleNamespace(report=report, executed=False, reason="blocked")

    replies = iter(("hello", "exit"))
    monkeypatch.setattr(cli_module, "OpenAICompatibleModel", lambda *_args, **_kwargs: AvailableChatModel())
    monkeypatch.setattr(cli_module, "ChatRuntime", FakeRuntime)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(replies))
    assert (
        main(
            [
                "chat",
                "--scenario",
                str(SCENARIO),
                "--endpoint",
                "http://127.0.0.1:8000/v1",
                "--model",
                "local-fixture",
            ],
        )
        == EXIT_OK
    )
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert '"run_id":"chat-run"' in output
    assert '"blocked":1' in output

    monkeypatch.setattr("builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError()))
    assert (
        main(
            [
                "chat",
                "--scenario",
                str(SCENARIO),
                "--endpoint",
                "http://127.0.0.1:8000/v1",
                "--model",
                "local-fixture",
            ],
        )
        == EXIT_OK
    )
    assert "chat_aborted_safely" in capsys.readouterr().out  # type: ignore[attr-defined]


def test_chat_cli_fails_closed_when_local_endpoint_adapter_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnavailableChatModel:
        api_key_env = "MISSING_TEST_KEY"

        def available(self) -> bool:
            return False

    monkeypatch.setattr(
        cli_module,
        "OpenAICompatibleModel",
        lambda *_args, **_kwargs: UnavailableChatModel(),
    )
    assert (
        main(
            [
                "chat",
                "--scenario",
                str(SCENARIO),
                "--endpoint",
                "http://127.0.0.1:8000/v1",
                "--model",
                "unavailable-fixture",
            ],
        )
        == EXIT_USAGE
    )


def test_model_comparison_live_paths_retain_normalized_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    planning = tmp_path / "planning.json"
    planning_output = tmp_path / "planning-live"
    _write_protocol(planning, "planning", model=True)
    monkeypatch.setattr(cli_module, "_local_model", lambda _protocol: object())
    monkeypatch.setattr(
        cli_module,
        "run_planning_comparison",
        lambda *_: {
            "schema_version": "2",
            "protocol_fingerprint": "fixture",
            "complete": True,
            "model_id": "fixture",
            "task_ids": [],
            "observations": [],
        },
    )
    assert (
        main(
            [
                "plan",
                "compare",
                "--config",
                str(planning),
                "--output",
                str(planning_output),
                "--execute-local",
            ],
        )
        == EXIT_OK
    )
    assert (planning_output / "result.json").is_file()

    agentdojo = tmp_path / "agentdojo.json"
    agentdojo_output = tmp_path / "agentdojo-live"
    _write_protocol(agentdojo, "agentdojo", model=True)
    monkeypatch.setattr(
        cli_module,
        "run_agentdojo_comparison",
        lambda *_: {
            "schema_version": "2",
            "protocol_fingerprint": "fixture",
            "complete": False,
            "model_id": "fixture",
            "cells": [],
            "failure_counts": {},
        },
    )
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "run",
                "--config",
                str(agentdojo),
                "--output",
                str(agentdojo_output),
                "--execute-local",
            ],
        )
        == 3
    )
    assert (agentdojo_output / "result.json").is_file()


def test_cedar_binary_preflight_distinguishes_missing_and_mismatched_bytes(
    tmp_path: Path,
    capsys: object,
) -> None:
    missing = tmp_path / "missing-cedar"
    assert (
        main(
            [
                "doctor",
                "--cedar-bundle",
                str(CEDAR_BUNDLE),
                "--cedar-binary",
                str(missing),
                "--json",
            ],
        )
        == EXIT_OK
    )
    assert json.loads(capsys.readouterr().out)["cedar"]["reason"] == "binary_not_found"  # type: ignore[attr-defined]

    binary = tmp_path / "cedar"
    binary.write_bytes(b"not the pinned Cedar binary")
    assert (
        main(
            [
                "doctor",
                "--cedar-bundle",
                str(CEDAR_BUNDLE),
                "--cedar-binary",
                str(binary),
                "--json",
            ],
        )
        == EXIT_OK
    )
    cedar = json.loads(capsys.readouterr().out)["cedar"]  # type: ignore[attr-defined]
    assert cedar["reason"] == "binary_checksum_mismatch"
    assert cedar["actual_sha256"] is not None
    assert cedar["invoked"] is False


def test_human_doctor_renders_local_model_and_cedar_boundaries(
    tmp_path: Path,
    capsys: object,
) -> None:
    planning = tmp_path / "planning.json"
    _write_protocol(planning, "planning", model=True)
    assert (
        main(
            [
                "doctor",
                "--local-model-config",
                str(planning),
                "--cedar-bundle",
                str(CEDAR_BUNDLE),
            ],
        )
        == EXIT_OK
    )
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "Local model:" in output
    assert "Cedar: 4.12.0 - binary_not_supplied" in output


def test_doctor_rejects_protocol_without_model(tmp_path: Path) -> None:
    protocol = tmp_path / "native.json"
    _write_protocol(protocol, "native_sled", model=False)
    assert main(["doctor", "--local-model-config", str(protocol)]) == EXIT_USAGE


def test_legacy_agentdojo_preflight_stops_after_pinned_suite_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = SimpleNamespace(to_dict=lambda: {"schema_version": "fixture"})
    monkeypatch.setattr(cli_module, "load_pinned_suite", lambda _suite_id: suite)
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "preflight",
                "--config",
                str(AGENTDOJO_MANIFEST),
                "--output",
                "ignored",
            ],
        )
        == EXIT_USAGE
    )


def test_legacy_agentdojo_execute_gate_and_model_less_protocol_fail_closed(
    tmp_path: Path,
) -> None:
    assert (
        main(
            [
                "benchmark",
                "agentdojo",
                "run",
                "--config",
                str(AGENTDOJO_MANIFEST),
                "--output",
                str(tmp_path / "legacy"),
                "--execute-local",
            ],
        )
        == EXIT_USAGE
    )
    model_less = tmp_path / "native.json"
    _write_protocol(model_less, "native_sled", model=False)
    protocol = load_protocol(model_less)
    with pytest.raises(ValueError, match="self_hosted_model_protocol_required"):
        cli_module._local_model(protocol)


def test_result_kind_routing_is_strict() -> None:
    assert cli_module._result_schema({"schema_version": "1"}) == "result.schema.json"
    assert (
        cli_module._result_schema({"schema_version": "2", "model_identities": {}, "observations": []})
        == "planning-laptop-smoke-result.schema.json"
    )
    assert cli_module._result_schema({"schema_version": "2", "cells": []}) == "agentdojo-comparison-result-v2.schema.json"
    assert cli_module._result_schema({"schema_version": "2", "observations": []}) == "planning-comparison-result-v2.schema.json"
    with pytest.raises(ValueError, match="unknown_version_two_result_kind"):
        cli_module._result_schema({"schema_version": "2"})


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
            ],
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
