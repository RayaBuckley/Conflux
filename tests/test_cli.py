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
