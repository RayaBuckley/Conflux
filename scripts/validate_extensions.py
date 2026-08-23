"""Run markdownlint and cspell checks when available.

This script exits 0 when all available tools pass or when no tools are
installed. It exits 1 only when an available tool reports failures.
Install the Node.js tools with ``npm install`` (see ``package.json``).

LTeX (grammar and style checking) is configured via ``.ltexrc.json`` for
use within the VS Code editor only; it is not run in CI because the
LTeX CLI depends on a VS Code extension that is not available in the
CI environment.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_IGNORE_DIRS = {
    "reports/archive",
    "publications/paper",
    "node_modules",
    ".local",
    ".git",
    "dist",
    "build",
    ".venv",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}


def _find_markdown_files() -> list[str]:
    """Return tracked markdown globs, excluding immutable archives."""
    markdown_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        if any(rel.startswith(ig) or rel == ig for ig in _IGNORE_DIRS):
            continue
        for filename in filenames:
            if filename.endswith(".md"):
                markdown_files.append(os.path.relpath(os.path.join(dirpath, filename), ROOT))
    return markdown_files


def _run_npx_tool(tool: str, args: list[str]) -> int:
    """Run an npm-based tool via npx, installing if needed."""
    npx = shutil.which("npx")
    if npx is None:
        print(f"[extensions] npx not found — skipping {tool}")
        return 0
    cmd = [npx, "--yes", tool, *args]
    print(f"[extensions] {' '.join(cmd[:3])}...")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"[extensions] {tool} reported failures (exit {result.returncode})")
    return result.returncode


def main() -> int:
    failures: list[str] = []

    md_files = _find_markdown_files()
    if md_files:
        rc = _run_npx_tool("markdownlint-cli2", ["**/*.md"])
        if rc:
            failures.append("markdownlint-cli2")

        rc = _run_npx_tool("cspell", ["--no-progress", "**/*.md", "**/*.py", "**/*.yaml", "**/*.yml", "**/*.tex", "**/*.bib"])
        if rc:
            failures.append("cspell")
    else:
        print("[extensions] no markdown files found")

    if failures:
        print(f"[extensions] {len(failures)} tool(s) failed: {', '.join(failures)}")
        return 1
    print("[extensions] all available extension checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
