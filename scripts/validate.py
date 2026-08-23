"""Portable repository validation entry point."""

from __future__ import annotations

import os
import subprocess
import sys
from collections import deque
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SESSION_ROOT = ROOT / ".local" / "validation" / uuid4().hex


def _validation_environment() -> dict[str, str]:
    environment = dict(os.environ)
    temporary = SESSION_ROOT / "temp"
    hugging_face = SESSION_ROOT / "huggingface"
    temporary.mkdir(parents=True, exist_ok=True)
    hugging_face.mkdir(parents=True, exist_ok=True)
    environment.update(
        {
            "TEMP": str(temporary),
            "TMP": str(temporary),
            "TMPDIR": str(temporary),
            "HF_HOME": str(hugging_face),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        },
    )
    return environment


VALIDATION_ENV = _validation_environment()


def _workflow_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def run(*arguments: str) -> int:
    print(f"[validate] {' '.join(arguments)}", flush=True)
    process = subprocess.Popen(
        (sys.executable, *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=VALIDATION_ENV,
    )
    assert process.stdout is not None
    tail: deque[str] = deque(maxlen=30)
    for line in process.stdout:
        print(line, end="", flush=True)
        tail.append(line.rstrip())
    return_code = process.wait()
    if return_code:
        command = " ".join(arguments)
        detail = "\n".join(tail)
        print(
            f"::error title=Conflux validation failed ({_workflow_escape(command)})::{_workflow_escape(detail)}",
            flush=True,
        )
    return return_code


def run_info(*arguments: str) -> int:
    """Run a check but never add it to the failure list (informational only)."""
    print(f"[validate] {' '.join(arguments)}", flush=True)
    process = subprocess.Popen(
        (sys.executable, *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=VALIDATION_ENV,
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
    return process.wait()


def main() -> int:
    failures: list[str] = []

    def _run(*arguments: str) -> None:
        if run(*arguments):
            failures.append(" ".join(arguments))

    _run("scripts/audit_repository.py")
    _run("scripts/validate_schemas.py")
    _run(
        "scripts/generate_smoke_evidence.py",
        "experiments/manifests/m3-smoke.yaml",
        "output/runs/smoke",
        "--check",
    )
    if (ROOT / "output" / "runs" / "native-sled-reproduction-v1").is_dir():
        _run(
            "scripts/generate_native_sled_evidence.py",
            "output/runs/native-sled-reproduction-v1",
            "--check",
        )
    if (ROOT / "output" / "runs" / "sled-coi-reduction-v1").is_dir():
        _run(
            "scripts/generate_coi_evidence.py",
            "output/runs/sled-coi-reduction-v1",
            "--check",
        )
    if (ROOT / "output" / "runs" / "cedar-differential-preflight-v1").is_dir():
        _run(
            "scripts/generate_cedar_preflight.py",
            "output/runs/cedar-differential-preflight-v1",
            "--check",
        )
    if (ROOT / "output" / "runs" / "direction-readiness-v1").is_dir():
        _run(
            "scripts/generate_direction_evidence.py",
            "output/runs/direction-readiness-v1",
            "--check",
        )
    _run(
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "--cov=conflux",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-fail-under=89",
        f"--basetemp={SESSION_ROOT / 'pytest'}",
    )
    doctest_process = subprocess.run(
        (sys.executable, "-m", "pytest", "--doctest-modules", "src/conflux/domain", "-q"),
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=VALIDATION_ENV,
    )
    if doctest_process.returncode and doctest_process.returncode != 5:
        print("[validate] -m pytest --doctest-modules src/conflux/domain -q")
        print(doctest_process.stdout, end="")
        print(doctest_process.stderr, end="", file=sys.stderr)
        failures.append("pytest --doctest-modules src/conflux/domain")
    _run(
        "-m",
        "pytest",
        "tests/test_omitted_coverage.py",
        "-q",
        f"--basetemp={SESSION_ROOT / 'omitted'}",
    )
    _run("-m", "ruff", "check", ".")
    _run("-m", "mypy", ".", "--no-error-summary")
    _run("-m", "yamllint", "-c", ".yamllint.yml", ".")
    _run("-m", "vulture", "src/conflux", "vulture-whitelist.py", "--min-confidence", "60")
    run_info("-m", "pip_audit", "--skip-editable", "-f", "json")
    _run("-m", "build", "--wheel", "--no-isolation", "--outdir", "dist")
    _run("scripts/validate_wheel.py")
    _run("scripts/validate_extensions.py")
    if failures:
        print(f"[validate] {len(failures)} check(s) failed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    rmtree(SESSION_ROOT)
    print("[validate] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
