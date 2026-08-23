"""CLI command examples from README.md and docs/reference/CLI.md."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conflux.cli import EXIT_OK, main

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples" / "basic.yaml"


def test_doctor_json_emits_schema_version(capsys: object) -> None:
    _ = capsys
    assert main(["doctor", "--json"]) == EXIT_OK
    doctor = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert "schema_version" in doctor


def test_demo_writes_trace_result_and_report(tmp_path: Path) -> None:
    output = tmp_path / "demo"
    assert main(["demo", "--scenario", str(SCENARIO), "--output", str(output)]) == EXIT_OK
    assert (output / "result.json").is_file()
    assert (output / "trace.jsonl").is_file()
    assert (output / "report.md").is_file()


def test_sled_run_writes_safe_verdict(tmp_path: Path) -> None:
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


def test_report_renders_markdown(tmp_path: Path, capsys: object) -> None:
    _ = capsys
    demo_output = tmp_path / "demo"
    assert main(["demo", "--scenario", str(SCENARIO), "--output", str(demo_output)]) == EXIT_OK
    assert main(["report", str(demo_output / "result.json")]) == EXIT_OK
    assert "# Conflux run" in capsys.readouterr().out  # type: ignore[attr-defined]


def test_plan_demo_writes_completed_result(tmp_path: Path) -> None:
    output = tmp_path / "plan-demo"
    assert main(["plan", "demo", "--output", str(output)]) == EXIT_OK
    payload = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert payload["completed"] is True
