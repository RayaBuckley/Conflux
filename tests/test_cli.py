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
