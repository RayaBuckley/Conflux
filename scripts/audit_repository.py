"""Static repository checks for AI-assisted changes.

The audit is deliberately dependency-free.  It checks the repository's
documentation graph, Python module ownership, and canonical terminology so a
reviewer gets a useful failure before running the full test suite.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE = ROOT / "src" / "conflux"
CANONICAL_DOCS = {
    "docs/README.md",
    "docs/ARCHITECTURE.md",
    "docs/REFERENCE.md",
    "docs/DEVELOPMENT.md",
    "docs/EVALUATION.md",
    "docs/STATUS.md",
    "docs/AUDIT.md",
    "docs/GLOSSARY.md",
}


def markdown_links(path: Path) -> list[tuple[int, str]]:
    pattern = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")
    return [(line_no, target) for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) for target in pattern.findall(line)]


def check_documentation_links(errors: list[str]) -> None:
    for relative in CANONICAL_DOCS:
        if not (ROOT / relative).exists():
            errors.append(f"missing canonical document {relative}")
    for path in [ROOT / "README.md", *DOCS.rglob("*.md")]:
        for line_no, target in markdown_links(path):
            if "://" in target or target.startswith("mailto:"):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}:{line_no}: missing link target {target}")


def check_module_docstrings(errors: list[str]) -> None:
    for path in SOURCE.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        if not re.match(r"\s*(?:from __future__ import annotations\s*)?(?:\"\"\"|''')", text):
            errors.append(f"{path.relative_to(ROOT)}: missing module docstring")


def check_audit_coverage(errors: list[str]) -> None:
    ledger = (DOCS / "AUDIT.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"`([^`]+)`", ledger))
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith((
            ".venv/",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            "src/conflux.egg-info/",
        )) or relative in {".coverage"}:
            continue
        if relative not in documented and relative not in {"docs/AUDIT.md"}:
            errors.append(f"{relative}: missing docs/AUDIT.md ledger entry")


def check_terminology(errors: list[str]) -> None:
    forbidden = re.compile(r"\buser(?:s)?\b", re.IGNORECASE)
    for path in [ROOT / "README.md", *DOCS.rglob("*.md")]:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "human user" in line.lower() or "human users" in line.lower():
                continue
            if forbidden.search(line) and "Principal" not in line:
                errors.append(f"{path.relative_to(ROOT)}:{line_no}: prefer Principal terminology")


def main() -> int:
    errors: list[str] = []
    check_documentation_links(errors)
    check_module_docstrings(errors)
    check_audit_coverage(errors)
    check_terminology(errors)
    if errors:
        print("Repository audit failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Repository audit passed: documentation, module ownership, and terminology checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
