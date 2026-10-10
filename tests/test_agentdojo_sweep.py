"""Tests for the stratified sweep runner (pure helpers, no benchmark package)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import run_agentdojo_sweep as sweep

SELECTION = Path("research/experiments/manifests/agentdojo-stratified-selection-v1.json")


def _selection() -> object:
    return json.loads(SELECTION.read_text(encoding="utf-8"))


def _completed(returncode: int) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["conflux"], returncode=returncode, stdout="", stderr="")


def test_frozen_selection_exposes_every_suite_with_tasks() -> None:
    suites = sweep.selection_suites(_selection())
    assert sorted(suites) == ["banking", "slack", "travel", "workspace"]
    assert len(suites["banking"]) == 4
    assert suites["banking"][0] == "user_task_0"
    for task_id in ("user_task_14", "user_task_16", "user_task_17", "user_task_22", "user_task_39"):
        assert task_id not in suites["workspace"]


def test_selection_without_suite_blocks_is_refused() -> None:
    with pytest.raises(ValueError, match="selection_manifest_missing_suite_blocks"):
        sweep.selection_suites({})
    with pytest.raises(ValueError, match="selection_manifest_missing_suite_blocks"):
        sweep.selection_suites({"protocol_suite_blocks": {}})
    with pytest.raises(ValueError, match="selection_manifest_suite_without_tasks:banking"):
        sweep.selection_suites({"protocol_suite_blocks": {"banking": {"task_ids": []}}})


def test_protocol_suite_ids_read_the_manifest_ids() -> None:
    """The sweep records the selection's own suite id, not the preflight's derived spelling."""
    selection = {
        "protocol_suite_blocks": {
            "banking": {"id": "banking:stratified-v1", "task_ids": ["user_task_0"]},
            "slack": {"id": "slack:stratified-v1", "task_ids": ["user_task_0"]},
        },
    }
    assert sweep.protocol_suite_ids(selection) == {
        "banking": "banking:stratified-v1",
        "slack": "slack:stratified-v1",
    }


def test_protocol_suite_ids_refuse_a_block_without_an_id() -> None:
    with pytest.raises(ValueError, match="selection_manifest_missing_suite_blocks"):
        sweep.protocol_suite_ids({})
    with pytest.raises(ValueError, match="selection_manifest_suite_without_id:banking"):
        sweep.protocol_suite_ids({"protocol_suite_blocks": {"banking": {"task_ids": ["user_task_0"]}}})


def test_requested_suites_accepts_all_and_refuses_unknown_names() -> None:
    available: dict[str, tuple[str, ...]] = {"banking": ("user_task_0",), "travel": ("user_task_5",)}
    assert sweep.requested_suites(available, ["all"]) == available
    assert sweep.requested_suites(available, ["travel"]) == {"travel": ("user_task_5",)}
    with pytest.raises(ValueError, match="unknown_suite:policy"):
        sweep.requested_suites(available, ["policy"])


def test_run_directory_names_the_retained_bundle() -> None:
    assert sweep.run_directory("slack", Path("runs")) == Path("runs/agentdojo-stratified-slack-v1")


def test_commands_match_the_documented_invocations() -> None:
    conflux = Path("/venv/bin/conflux")
    preflight = sweep.preflight_command(
        "banking",
        "banking:stratified-v1",
        ("user_task_0", "user_task_1"),
        Path("cfg/transformers.json"),
        Path("runs/banking"),
        "a" * 40,
        conflux,
    )
    assert preflight[:4] == [str(conflux), "benchmark", "agentdojo", "preflight"]
    assert preflight[preflight.index("--suite") + 1] == "banking"
    assert preflight[preflight.index("--protocol-suite-id") + 1] == "banking:stratified-v1"
    assert preflight[preflight.index("--task-ids") + 1] == "user_task_0,user_task_1"
    assert preflight[preflight.index("--source-commit") + 1] == "a" * 40
    run = sweep.local_run_command(Path("runs/banking"), Path("cfg/transformers.json"), conflux)
    assert run[-1] == "--execute-local"
    assert run[run.index("--config") + 1] == "runs/banking/protocol.json"


def test_summarise_counts_cells_utility_and_security(tmp_path: Path) -> None:
    result = tmp_path / "result.json"
    result.write_text(
        json.dumps(
            {
                "cells": [
                    {"status": "complete", "native_utility": True, "native_security": True},
                    {"status": "complete", "native_utility": False, "native_security": True},
                    {"status": "model_failed", "native_utility": None, "native_security": None},
                ],
            },
        ),
        encoding="utf-8",
    )
    assert sweep.summarise(result) == "cells=3 complete=2 failed=1 utility=1 security=2"


def test_run_suite_stops_after_a_failed_preflight(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return _completed(2)

    ok = sweep.run_suite(
        "banking",
        "banking:stratified-v1",
        ("user_task_0",),
        Path("cfg.json"),
        tmp_path / "run",
        "a" * 40,
        Path("/venv/bin/conflux"),
        runner,
    )
    assert ok is False
    assert len(calls) == 1
    assert "preflight" in calls[0]


def test_run_suite_summarises_a_finished_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "run"

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        if "preflight" in command:
            return _completed(0)
        output.joinpath("result.json").write_text(
            json.dumps({"cells": [{"status": "complete", "native_utility": False, "native_security": True}]}),
            encoding="utf-8",
        )
        return _completed(0)

    ok = sweep.run_suite(
        "travel",
        "travel:stratified-v1",
        ("user_task_5",),
        Path("cfg.json"),
        output,
        "a" * 40,
        Path("/venv/bin/conflux"),
        runner,
    )
    assert ok is True
    assert "travel: run exit 0 | cells=1 complete=1 failed=0 utility=0 security=1" in capsys.readouterr().out


def test_run_suite_reports_a_failed_run(tmp_path: Path) -> None:
    output = tmp_path / "run"

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        if "preflight" in command:
            return _completed(0)
        output.joinpath("result.json").write_text(
            json.dumps({"cells": [{"status": "model_failed"}]}),
            encoding="utf-8",
        )
        return _completed(3)

    ok = sweep.run_suite(
        "slack",
        "slack:stratified-v1",
        ("user_task_0",),
        Path("cfg.json"),
        output,
        "a" * 40,
        Path("/venv/bin/conflux"),
        runner,
    )
    assert ok is False


def test_main_runs_every_suite_when_asked_for_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, str]] = []

    def fake_run_suite(*args: object, **kwargs: object) -> bool:
        seen.append((str(args[0]), str(args[1])))
        return True

    monkeypatch.setattr(sweep, "run_suite", fake_run_suite)
    monkeypatch.setattr(sweep, "resolve_commit", lambda value, runner=None: "a" * 40)
    config = tmp_path / "transformers.json"
    config.write_text("{}", encoding="utf-8")
    assert sweep.main(["--model-config", str(config), "--conflux", "/bin/true"]) == 0
    assert seen == [
        ("banking", "banking:stratified-v1"),
        ("slack", "slack:stratified-v1"),
        ("travel", "travel:stratified-v1"),
        ("workspace", "workspace:stratified-v1"),
    ]


def test_main_refuses_an_unknown_suite(tmp_path: Path) -> None:
    config = tmp_path / "transformers.json"
    config.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown_suite:policy"):
        sweep.main(["--model-config", str(config), "--suite", "policy", "--conflux", "/bin/true"])


def test_source_commit_is_resolved_to_a_full_sha() -> None:
    """A short commit in a protocol record is ambiguous, so the sweep resolves it first."""
    seen: list[list[str]] = []

    def runner(command: list[str]) -> str:
        seen.append(command)
        return "1127281372dc7ce938b835be8c7d2184ccfa0a0a\n"

    resolved = sweep.resolve_commit("1127281", runner)
    assert resolved == "1127281372dc7ce938b835be8c7d2184ccfa0a0a"
    assert seen == [["git", "rev-parse", "--verify", "1127281^{commit}"]]
    sweep.resolve_commit(None, runner)
    assert seen[1] == ["git", "rev-parse", "--verify", "HEAD^{commit}"]


def test_source_commit_that_does_not_resolve_is_refused() -> None:
    """An unresolvable commit stops the sweep instead of recording a spelling nobody can resolve."""

    def runner(command: list[str]) -> str:
        raise subprocess.CalledProcessError(1, command)

    with pytest.raises(SystemExit):
        sweep.resolve_commit("not-a-commit", runner)
