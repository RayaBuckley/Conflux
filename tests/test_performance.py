"""Performance regression tests for core CLI commands."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

from conflux.cli import main

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples" / "basic.yaml"


def test_sled_exploration_completes_under_two_seconds(tmp_path: Path) -> None:
    output = tmp_path / "sled"
    start = time.perf_counter()
    assert main(["sled", "run", "--suite", str(SCENARIO), "--output", str(output)]) == 0
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"SLED exploration took {elapsed:.3f}s"
    payload = json.loads((output / "verification.json").read_text(encoding="utf-8"))
    assert payload["verdict"] == "safe"


def test_plan_demo_completes_under_five_seconds(tmp_path: Path) -> None:
    output = tmp_path / "plan-demo"
    start = time.perf_counter()
    assert main(["plan", "demo", "--output", str(output)]) == 0
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"Planning demo took {elapsed:.3f}s"
    payload = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert payload["completed"] is True


def test_z3_unavailable_returns_unknown_under_one_second(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "z3", None)
    model = tmp_path / "model.json"
    model.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "id": "perf-model",
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
    start = time.perf_counter()
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
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"Z3 unavailable path took {elapsed:.3f}s"
    assert json.loads((output / "formal-verification.json").read_text())["verdict"] == "unknown"


def test_delegation_verification_completes_under_three_seconds(tmp_path: Path) -> None:
    output = tmp_path / "delegation"
    start = time.perf_counter()
    assert main(["sled", "delegation", "--output", str(output)]) == 0
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, f"Delegation verification took {elapsed:.3f}s"
    delegation = json.loads((output / "delegation-verification.json").read_text())
    assert delegation["canonical"]["verdict"] == "safe"
