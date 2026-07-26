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


def markdown_links(path: Path) -> list[tuple[int, str]]:
    pattern = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")
    return [(line_no, target) for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) for target in pattern.findall(line)]


def check_documentation_links(errors: list[str]) -> None:
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
    check_terminology(errors)
    if errors:
        print("Repository audit failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Repository audit passed: documentation, module ownership, and terminology checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
