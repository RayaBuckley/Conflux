"""Portable repository validation entry point."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    print(f"[validate] {' '.join(arguments)}", flush=True)
    subprocess.run((sys.executable, *arguments), cwd=ROOT, check=True)


def main() -> int:
    run("scripts/audit_repository.py")
    run("scripts/validate_schemas.py")
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
    run("-c", "import conflux, conflux.domain, conflux.ites, conflux.evaluation")
    print("[validate] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
