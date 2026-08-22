"""Run optional VS Code extension checks (markdownlint, cspell, ltex) when available.

This script is advisory: it exits 0 when all available tools pass or when no
tools are installed. It exits 1 only when an available tool reports failures.
Install the Node.js tools with ``npm install`` (see ``package.json``).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
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


def _run_ltex() -> int:
    """Run the LTeX CLI if bundled with the VS Code extension."""
    home = os.path.expanduser("~")
    vscode_exts = os.path.join(home, ".vscode", "extensions")
    if not os.path.isdir(vscode_exts):
        print("[extensions] VS Code extensions directory not found — skipping ltex")
        return 0
    cli: str | None = None
    for entry in sorted(os.listdir(vscode_exts)):
        if entry.startswith("ltex-plus.vscode-ltex-plus-"):
            candidate = os.path.join(vscode_exts, entry, "lib")
            if os.path.isdir(candidate):
                for sub in sorted(os.listdir(candidate)):
                    if sub.startswith("ltex-ls-plus-"):
                        bat = os.path.join(candidate, sub, "bin", "ltex-cli-plus.bat")
                        if os.path.isfile(bat):
                            cli = bat
                            break
            if cli:
                break
    if cli is None:
        print("[extensions] ltex-cli-plus not found — skipping ltex")
        return 0
    config = ROOT / ".ltexrc.json"
    cmd = [cli]
    if config.exists():
        cmd.append(f"--client-configuration={config}")
    md_files = _find_markdown_files()
    if not md_files:
        print("[extensions] no markdown files — skipping ltex")
        return 0
    cmd.extend(md_files[:20])
    print(f"[extensions] ltex-cli-plus (checking {min(20, len(md_files))} files)...")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        print(f"[extensions] ltex reported failures (exit {result.returncode})")
    else:
        output = result.stdout.strip()
        if output:
            print(output)
    return result.returncode


def main() -> int:
    failures: list[str] = []

    md_files = _find_markdown_files()
    if md_files:
        rc = _run_npx_tool("markdownlint-cli2", ["**/*.md"])
        if rc:
            failures.append("markdownlint-cli2")

        rc = _run_npx_tool("cspell", ["--no-progress", "**/*.md", "**/*.py", "**/*.yaml", "**/*.yml"])
        if rc:
            failures.append("cspell")
    else:
        print("[extensions] no markdown files found")

    rc = _run_ltex()
    if rc:
        failures.append("ltex")

    if failures:
        print(f"[extensions] {len(failures)} tool(s) failed: {', '.join(failures)}")
        return 1
    print("[extensions] all available extension checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
