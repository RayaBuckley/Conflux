"""Dependency-free structural and documentation audit."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
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
    "MVP_RESULTS.md",
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
SMOKE = ROOT / "runs" / "smoke"
TASK_REGISTRY = DOCS / "task-registry.json"
EVIDENCE_SOURCES = DOCS / "evidence-sources.json"


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
        elif isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
    return result


def canonical_text_bytes(path: Path) -> bytes:
    text = path.read_bytes().decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def archive_digest(path: Path, mode: str) -> str:
    if mode == "canonical_utf8_lf":
        payload = canonical_text_bytes(path)
    elif mode == "raw_bytes":
        payload = path.read_bytes()
    else:
        raise ValueError(f"unsupported archive checksum mode {mode}")
    return hashlib.sha256(payload).hexdigest()


def index_blob_oid(path: Path) -> str | None:
    relative = path.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ("git", "ls-files", "--stage", "--", relative),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    fields = result.stdout.split(maxsplit=3)
    return fields[1] if len(fields) == 4 else None


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
            if path.is_relative_to(SOURCE / "planning") and imported.startswith(
                "conflux.adapters"
            ):
                errors.append(f"{path.relative_to(ROOT)}: planning imports adapter {imported}")
    benchmark_exports = (SOURCE / "adapters" / "benchmarks" / "__init__.py").read_text(
        encoding="utf-8"
    )
    if "agentdojo" in benchmark_exports.lower():
        errors.append("experimental AgentDojo integration is publicly re-exported")


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
    required = {
        ROOT / "reports" / "archive" / "2026-07-27-engineering-and-sled" / "REPO_REVIEW",
        ROOT / "reports" / "archive" / "2026-07-27-engineering-and-sled" / "SLED_REVIEW",
        ROOT / "reports" / "archive" / "MANIFEST.json",
    }
    missing = sorted(path.relative_to(ROOT).as_posix() for path in required if not path.is_file())
    if missing:
        errors.append(f"missing report artifacts: {missing}")
    check_task_registry(errors)
    check_evidence_sources(errors)


def check_task_registry(errors: list[str]) -> None:
    if not TASK_REGISTRY.is_file():
        errors.append("missing machine-readable task registry")
        return
    registry = json.loads(TASK_REGISTRY.read_text(encoding="utf-8"))
    groups = registry.get("groups")
    if not isinstance(groups, list):
        errors.append("task registry has no groups")
        return
    registered: set[str] = set()
    valid_statuses = {"implemented", "partial", "externally_gated", "deferred"}
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            errors.append(f"task registry group {index} is not an object")
            continue
        identifiers = group.get("ids")
        status = group.get("status")
        evidence = group.get("evidence")
        if not isinstance(identifiers, list) or not identifiers:
            errors.append(f"task registry group {index} has no IDs")
            continue
        if status not in valid_statuses:
            errors.append(f"task registry group {index} has invalid status {status}")
        if status in {"partial", "externally_gated"} and not group.get("gap"):
            errors.append(f"task registry group {index} has no explicit evidence gap")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"task registry group {index} has no evidence")
            continue
        for item in evidence:
            if not isinstance(item, str) or not (ROOT / item).exists():
                errors.append(f"task registry group {index} has missing evidence {item}")
        for identifier in identifiers:
            if not isinstance(identifier, str):
                errors.append(f"task registry group {index} has non-string ID")
            elif identifier in registered:
                errors.append(f"task registry duplicates {identifier}")
            else:
                registered.add(identifier)

    backlog = json.loads(
        (
            ROOT
            / "reports"
            / "archive"
            / "2026-07-29-implementation-programme"
            / "Conflux_Codex_Implementation_Backlog.json"
        ).read_text(encoding="utf-8")
    )
    dynamic = json.loads(
        (
            ROOT
            / "reports"
            / "archive"
            / "2026-07-30-dynamic-planning-programme"
            / "Conflux_Codex_Progress_and_Dynamic_Planning_Plan_2026-07-30.json"
        ).read_text(encoding="utf-8")
    )
    expected = {task["id"] for task in backlog["tasks"]}
    expected.update(task["id"] for task in dynamic["recommended_planning_tasks"])
    expected.add("SEC-008")
    for identifier in sorted(expected - registered):
        errors.append(f"task registry missing report task {identifier}")
    for identifier in sorted(registered - expected):
        errors.append(f"task registry contains unknown task {identifier}")


def check_evidence_sources(errors: list[str]) -> None:
    if not EVIDENCE_SOURCES.is_file():
        errors.append("missing immutable evidence source manifest")
        return
    manifest = json.loads(EVIDENCE_SOURCES.read_text(encoding="utf-8"))
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        errors.append("evidence source manifest has no source list")
        return
    for source in sources:
        if not isinstance(source, dict):
            errors.append("evidence source entry is not an object")
            continue
        path = ROOT / str(source.get("path"))
        expected = source.get("canonical_text_sha256")
        if not path.is_file() or not isinstance(expected, str):
            errors.append(f"invalid evidence source entry: {source}")
            continue
        actual = hashlib.sha256(canonical_text_bytes(path)).hexdigest()
        if actual != expected:
            errors.append(f"immutable evidence source changed: {path.relative_to(ROOT)}")


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
    if manifest.get("schema_version") != "2":
        errors.append("paper archive manifest has an unsupported schema version")
        return
    for name, record in files.items():
        path = PAPER / str(name)
        if not path.is_file():
            errors.append(f"archived paper file is missing: paper/{name}")
            continue
        if not isinstance(record, dict):
            errors.append(f"paper archive record is invalid: paper/{name}")
            continue
        mode = record.get("mode")
        expected = record.get("sha256")
        expected_blob = record.get("git_blob_oid")
        if (
            not isinstance(mode, str)
            or not isinstance(expected, str)
            or not isinstance(expected_blob, str)
        ):
            errors.append(f"paper archive record is incomplete: paper/{name}")
            continue
        try:
            actual = archive_digest(path, mode)
        except (UnicodeDecodeError, ValueError) as error:
            errors.append(f"paper/{name}: {error}")
            continue
        if actual != expected:
            errors.append(f"archived paper file changed: paper/{name}")
        if index_blob_oid(path) != expected_blob:
            errors.append(f"archived paper Git object changed: paper/{name}")


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


def check_smoke_evidence(errors: list[str]) -> None:
    required = {
        "RERUN.txt",
        "checksums.sha256",
        "counterexample.json",
        "manifest.json",
        "raw.jsonl",
        "result.json",
        "table.md",
    }
    missing = required - {path.name for path in SMOKE.glob("*")}
    if missing:
        errors.append(f"smoke evidence is incomplete: {sorted(missing)}")
        return
    for line in (SMOKE / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        expected, separator, name = line.partition("  ")
        path = SMOKE / name
        if not separator or not path.is_file():
            errors.append(f"invalid smoke checksum entry: {line}")
            continue
        actual = hashlib.sha256(canonical_text_bytes(path)).hexdigest()
        if actual != expected:
            errors.append(f"smoke evidence checksum changed: runs/smoke/{name}")


def check_schemas(errors: list[str]) -> None:
    required = {
        "dynamic-plan-result.schema.json",
        "experiment-manifest.schema.json",
        "formal-verification-result.schema.json",
        "plan-patch.schema.json",
        "plan.schema.json",
        "planning-comparison-result.schema.json",
        "planning-observation.schema.json",
        "proposal-batch.schema.json",
        "result.schema.json",
        "scenario.schema.json",
        "trace-event.schema.json",
        "verification-ir.schema.json",
        "verification-result.schema.json",
    }
    actual = {path.name for path in (ROOT / "schemas").glob("*.json")}
    for name in sorted(required - actual):
        errors.append(f"missing versioned schema: schemas/{name}")


def main() -> int:
    errors: list[str] = []
    check_architecture(errors)
    check_docs(errors)
    check_reports(errors)
    check_archived_paper(errors)
    check_manuscript(errors)
    check_smoke_evidence(errors)
    check_schemas(errors)
    if not (ROOT / "SECURITY.md").is_file():
        errors.append("missing repository security policy: SECURITY.md")
    if errors:
        print("Repository audit failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Repository audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
