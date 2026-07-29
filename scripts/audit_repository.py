"""Dependency-free structural and documentation audit."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "conflux"
DOCS = ROOT / "docs"
CANONICAL_DOCS = {
    "README.md",
    "ARCHITECTURE.md",
    "SECURITY_MODEL.md",
    "REFERENCE.md",
    "SLED.md",
    "EVALUATION.md",
    "RUNTIME.md",
    "CLI.md",
    "NEGATIVE_CONTROLS.md",
    "CHANGE_CATALOG.md",
    "CLAIMS.md",
    "RELATED_WORK.md",
    "DEVELOPMENT.md",
    "STATUS.md",
    "AUDIT.md",
    "GLOSSARY.md",
}
LEGACY = {"core", "auth", "research", "compatibility"}
FORBIDDEN_IMPORTS = tuple(f"conflux.{name}" for name in LEGACY)
PAPER = ROOT / "paper"
MANUSCRIPT = ROOT / "manuscript"


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
        elif isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
    return result


def check_architecture(errors: list[str]) -> None:
    for name in LEGACY:
        if list((SOURCE / name).glob("*.py")):
            errors.append(f"legacy package still contains Python modules: conflux.{name}")
    for path in SOURCE.rglob("*.py"):
        for imported in imports(path):
            if imported.startswith(FORBIDDEN_IMPORTS):
                errors.append(f"{path.relative_to(ROOT)} imports legacy {imported}")
            if path.is_relative_to(SOURCE / "domain") and imported.startswith("conflux."):
                errors.append(f"{path.relative_to(ROOT)}: domain imports outward {imported}")
            if path.is_relative_to(SOURCE / "ports") and imported.startswith("conflux.adapters"):
                errors.append(f"{path.relative_to(ROOT)}: port imports adapter {imported}")


def check_docs(errors: list[str]) -> None:
    for name in CANONICAL_DOCS:
        if not (DOCS / name).exists():
            errors.append(f"missing canonical document docs/{name}")
    link_pattern = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")
    for path in (ROOT / "README.md", *DOCS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "â" in text:
            errors.append(f"{path.relative_to(ROOT)} contains probable mojibake")
        for line, content in enumerate(text.splitlines(), 1):
            for target in link_pattern.findall(content):
                if "://" in target or target.startswith("mailto:"):
                    continue
                if not (path.parent / target).resolve().exists():
                    errors.append(f"{path.relative_to(ROOT)}:{line}: missing link {target}")


def check_reports(errors: list[str]) -> None:
    catalogue = (DOCS / "CHANGE_CATALOG.md").read_text(encoding="utf-8")
    for identifier in ("BUG-001", "BUG-002", "BUG-003", "BUG-004", "SLED-001", "TRACE-001"):
        if identifier not in catalogue:
            errors.append(f"change catalogue missing report identifier {identifier}")
    expected = {
        "REPO_REVIEW",
        "SLED_REVIEW",
        "Conflux_Codex_Action_Manifest.json",
        "Conflux_Codex_Research_Backlog.json",
    }
    missing = expected - {path.name for path in (ROOT / "reports").iterdir()}
    if missing:
        errors.append(f"missing report artifacts: {sorted(missing)}")


def check_archived_paper(errors: list[str]) -> None:
    manifest_path = PAPER / "ARCHIVE_MANIFEST.json"
    marker_path = PAPER / "ARCHIVED.md"
    if not manifest_path.exists() or not marker_path.exists():
        errors.append("archived paper marker or checksum manifest is missing")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("paper archive manifest has no file map")
        return
    for name, expected in files.items():
        path = PAPER / str(name)
        if not path.is_file():
            errors.append(f"archived paper file is missing: paper/{name}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"archived paper file changed: paper/{name}")


def check_manuscript(errors: list[str]) -> None:
    required = {
        "README.md",
        "REFERENCES.md",
        "conflux_fourth_year_2026.tex",
        "references.bib",
        "generated/tables/README.md",
        "generated/figures/README.md",
    }
    for name in required:
        if not (MANUSCRIPT / name).is_file():
            errors.append(f"current manuscript file is missing: manuscript/{name}")
    if (MANUSCRIPT / "conflux_fourth_year_2026.pdf").exists():
        errors.append("generated current-manuscript PDF must be a CI artefact")


def main() -> int:
    errors: list[str] = []
    check_architecture(errors)
    check_docs(errors)
    check_reports(errors)
    check_archived_paper(errors)
    check_manuscript(errors)
    if errors:
        print("Repository audit failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Repository audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
