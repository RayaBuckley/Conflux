"""Portable repository validation entry point."""

from __future__ import annotations

import subprocess
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _workflow_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def run(*arguments: str) -> None:
    print(f"[validate] {' '.join(arguments)}", flush=True)
    process = subprocess.Popen(
        (sys.executable, *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
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
            f"::error title=Conflux validation failed ({_workflow_escape(command)})::"
            f"{_workflow_escape(detail)}",
            flush=True,
        )
        raise subprocess.CalledProcessError(return_code, (sys.executable, *arguments))


def main() -> int:
    run("scripts/audit_repository.py")
    run("scripts/validate_schemas.py")
    run(
        "scripts/generate_smoke_evidence.py",
        "experiments/manifests/m3-smoke.yaml",
        "runs/smoke",
        "--check",
    )
    run(
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "--cov=src/conflux",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
    )
    run("-m", "ruff", "check", "src", "tests", "scripts")
    run("-m", "mypy", "src", "tests", "scripts", "--no-error-summary")
    run("-m", "build", "--wheel", "--no-isolation", "--outdir", "dist")
    run("scripts/validate_wheel.py")
    print("[validate] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
