"""Dependency-free structural and documentation audit."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "conflux"
DOCS = ROOT / "docs"
CANONICAL_DOCS = {
    "README.md",
    "AI_AGENT_GUIDE.md",
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
NATIVE_SLED = ROOT / "runs" / "native-sled-reproduction-v1"
COI_EVIDENCE = ROOT / "runs" / "sled-coi-reduction-v1"
CEDAR_PREFLIGHT = ROOT / "runs" / "cedar-differential-preflight-v1"
COI_EVIDENCE_ROOT_FILES = (
    "CHECKSUMS.sha256",
    "RERUN.txt",
    "manifest.json",
    "protocol.json",
    "raw-results.jsonl",
    "result.json",
    "table.md",
)
TASK_REGISTRY = DOCS / "task-registry.json"
EVIDENCE_SOURCES = DOCS / "evidence-sources.json"
REPORTS = ROOT / "reports"
REPORT_ARCHIVE = REPORTS / "archive"
REPORT_MANIFEST = REPORT_ARCHIVE / "MANIFEST.json"
REPORT_CROSSWALK = REPORTS / "analysis" / "task-crosswalk.json"
DIRECTION_TASK_IDS = {
    "DIR-PLAN-001",
    "DIR-DELEG-001",
    "DIR-ARGPOL-001",
    "DIR-VIS-001",
    "DIR-ATTR-001",
    "DIR-SLED-001",
    "DIR-BENCH-001",
    "DIR-PDP-001",
    "DIR-GOV-001",
}
APPROVED_TOP_LEVEL_DIRECTORIES = {
    ".github",
    "artifacts",
    "docs",
    "examples",
    "experiments",
    "external",
    "manuscript",
    "paper",
    "reports",
    "runs",
    "schemas",
    "scripts",
    "src",
    "tests",
}


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
    return canonical_utf8_bytes(path.read_bytes())


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


def git_blob_bytes(object_id: str) -> bytes | None:
    result = subprocess.run(
        ("git", "cat-file", "blob", object_id),
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    return result.stdout if result.returncode == 0 else None


def canonical_utf8_bytes(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


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
    current_markdown = (
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        *DOCS.rglob("*.md"),
        *MANUSCRIPT.glob("*.md"),
        REPORTS / "README.md",
        REPORT_ARCHIVE / "README.md",
        *(REPORTS / "analysis").rglob("*.md"),
    )
    for path in current_markdown:
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{path.relative_to(ROOT)} is not valid UTF-8")
            continue
        if "â" in text:
            errors.append(f"{path.relative_to(ROOT)} contains probable mojibake")
        for line, content in enumerate(text.splitlines(), 1):
            for target in link_pattern.findall(content):
                if "://" in target or target.startswith("mailto:"):
                    continue
                if not (path.parent / target).resolve().exists():
                    errors.append(f"{path.relative_to(ROOT)}:{line}: missing link {target}")

    rationale_docs = {
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        DOCS / "ARCHITECTURE.md",
        DOCS / "SECURITY_MODEL.md",
        DOCS / "RUNTIME.md",
        DOCS / "SLED.md",
        DOCS / "EVALUATION.md",
        DOCS / "CLI.md",
        DOCS / "DEVELOPMENT.md",
        DOCS / "integrations" / "models.md",
        DOCS / "integrations" / "agentdojo.md",
        REPORTS / "README.md",
        REPORT_ARCHIVE / "README.md",
    }
    for path in rationale_docs:
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?im)^#{2,3} (?:rationale\b|why\b)", text):
            errors.append(f"{path.relative_to(ROOT)} has no explicit rationale section")

    stale_paths = re.compile(r"reports/(?:New|new-v2)/")
    for path in current_markdown:
        if stale_paths.search(path.read_text(encoding="utf-8")):
            errors.append(f"{path.relative_to(ROOT)} references an obsolete report path")


def check_repository_governance(errors: list[str]) -> None:
    result = subprocess.run(
        ("git", "ls-files"), cwd=ROOT, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        errors.append("cannot inspect tracked top-level paths")
        return
    tracked_directories = {
        path.split("/", maxsplit=1)[0]
        for path in result.stdout.splitlines()
        if "/" in path
    }
    unexpected = tracked_directories - APPROVED_TOP_LEVEL_DIRECTORIES
    if unexpected:
        errors.append(
            "unapproved tracked top-level directories: " + ", ".join(sorted(unexpected))
        )
    if (REPORTS / "not_yet_processed").exists():
        errors.append("reports/not_yet_processed must be reconciled into the archive")
    template = DOCS / "templates" / "FEATURE_SPEC.md"
    if not template.is_file() or "## Expected file set and change budget" not in (
        template.read_text(encoding="utf-8")
    ):
        errors.append("feature specifications do not require an expected file set")

def check_reports(errors: list[str]) -> None:
    catalogue = (DOCS / "CHANGE_CATALOG.md").read_text(encoding="utf-8")
    for identifier in ("BUG-001", "BUG-002", "BUG-003", "BUG-004", "SLED-001", "TRACE-001"):
        if identifier not in catalogue:
            errors.append(f"change catalogue missing report identifier {identifier}")
    required = {
        ROOT / "schemas" / "attribution-record.schema.json",
        ROOT / "schemas" / "decision-certificate.schema.json",
        ROOT / "reports" / "archive" / "2026-07-27-engineering-and-sled" / "REPO_REVIEW",
        ROOT / "reports" / "archive" / "2026-07-27-engineering-and-sled" / "SLED_REVIEW",
        ROOT / "reports" / "archive" / "MANIFEST.json",
    }
    missing = sorted(path.relative_to(ROOT).as_posix() for path in required if not path.is_file())
    if missing:
        errors.append(f"missing report artifacts: {missing}")
    check_report_archive(errors)
    check_report_crosswalk(errors)
    check_task_registry(errors)
    check_evidence_sources(errors)


def supersession_has_cycle(edges: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> bool:
        if identifier in visiting:
            return True
        if identifier in visited:
            return False
        visiting.add(identifier)
        if any(visit(child) for child in edges.get(identifier, set())):
            return True
        visiting.remove(identifier)
        visited.add(identifier)
        return False

    return any(visit(identifier) for identifier in edges)


def check_report_archive(errors: list[str]) -> None:
    if not REPORT_MANIFEST.is_file():
        errors.append("missing report archive manifest")
        return
    manifest: Any = json.loads(REPORT_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1":
        errors.append("report archive manifest has an unsupported schema version")
        return
    package_records = manifest.get("packages")
    artifact_records = manifest.get("artifacts")
    if not isinstance(package_records, list) or not isinstance(artifact_records, list):
        errors.append("report archive manifest has invalid package or artifact records")
        return

    packages: dict[str, Any] = {}
    valid_statuses = {
        "superseded",
        "historical_input",
        "design_input",
        "citation_validation_required",
    }
    for record in package_records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            errors.append("report archive contains an invalid package")
            continue
        identifier = record["id"]
        if identifier in packages:
            errors.append(f"report archive duplicates package {identifier}")
        packages[identifier] = record
        if record.get("status") not in valid_statuses:
            errors.append(f"report package {identifier} has an invalid status")
        if not record.get("limitations"):
            errors.append(f"report package {identifier} has no limitations")
        for successor in record.get("canonical_successors", []):
            if not isinstance(successor, str) or not (ROOT / successor).exists():
                errors.append(f"report package {identifier} has missing successor {successor}")

    edges: dict[str, set[str]] = {}
    for identifier, record in packages.items():
        supersedes = record.get("supersedes", [])
        superseded_by = record.get("superseded_by", [])
        if not isinstance(supersedes, list) or not isinstance(superseded_by, list):
            errors.append(f"report package {identifier} has invalid supersession metadata")
            continue
        edges[identifier] = {item for item in supersedes if isinstance(item, str)}
        for older in supersedes:
            if older not in packages:
                errors.append(f"report package {identifier} supersedes unknown package {older}")
            elif identifier not in packages[older].get("superseded_by", []):
                errors.append(f"report package {identifier} has inconsistent supersession of {older}")
        for newer in superseded_by:
            if newer not in packages:
                errors.append(f"report package {identifier} is superseded by unknown package {newer}")
            elif identifier not in packages[newer].get("supersedes", []):
                errors.append(f"report package {identifier} has inconsistent successor {newer}")
    if supersession_has_cycle(edges):
        errors.append("report package supersession contains a cycle")

    archive_paths: set[str] = set()
    original_paths: set[str] = set()
    artifacts_by_path: dict[str, Any] = {}
    hashes: dict[str, list[Any]] = {}
    for index, record in enumerate(artifact_records):
        if not isinstance(record, dict):
            errors.append(f"report artifact {index} is not an object")
            continue
        archive_path = record.get("archive_path")
        original_path = record.get("original_path")
        package_id = record.get("package_id")
        expected_size = record.get("size_bytes")
        expected_hash = record.get("sha256_bytes")
        expected_blob = record.get("git_blob_oid")
        media_type = record.get("media_type")
        if (
            not isinstance(archive_path, str)
            or not isinstance(original_path, str)
            or not isinstance(package_id, str)
            or not isinstance(expected_hash, str)
            or not isinstance(expected_blob, str)
            or not isinstance(media_type, str)
        ):
            errors.append(f"report artifact {index} has incomplete identity metadata")
            continue
        if not isinstance(expected_size, int):
            errors.append(f"report artifact {archive_path} has invalid size metadata")
            continue
        if archive_path in archive_paths or original_path in original_paths:
            errors.append(f"report archive duplicates a path at {archive_path}")
        archive_paths.add(archive_path)
        original_paths.add(original_path)
        artifacts_by_path[archive_path] = record
        hashes.setdefault(expected_hash, []).append(record)
        if package_id not in packages:
            errors.append(f"report artifact {archive_path} has unknown package {package_id}")
        if not archive_path.startswith(f"reports/archive/{package_id}/"):
            errors.append(f"report artifact {archive_path} is outside its package")
        path = ROOT / archive_path
        if not path.is_file():
            errors.append(f"archived report is missing: {archive_path}")
            continue
        if index_blob_oid(path) != expected_blob:
            errors.append(f"archived report Git object changed: {archive_path}")
        blob = git_blob_bytes(expected_blob)
        if blob is None:
            errors.append(f"archived report Git object is unavailable: {archive_path}")
            continue
        if len(blob) != expected_size or hashlib.sha256(blob).hexdigest() != expected_hash:
            errors.append(f"archived report manifest does not match its Git object: {archive_path}")
        worktree = path.read_bytes()
        textual = media_type.startswith("text/") or media_type in {
            "application/json",
            "application/x-bibtex",
            "application/x-tex",
        }
        try:
            worktree_matches = (
                canonical_utf8_bytes(worktree) == canonical_utf8_bytes(blob)
                if textual
                else worktree == blob
            )
        except UnicodeDecodeError:
            worktree_matches = False
        if not worktree_matches:
            errors.append(f"archived report working copy changed: {archive_path}")

    if manifest.get("artifact_count") != len(artifact_records):
        errors.append("report archive artifact count does not match its records")
    actual_files = {
        path.relative_to(ROOT).as_posix()
        for path in REPORT_ARCHIVE.rglob("*")
        if path.is_file() and path not in {REPORT_MANIFEST, REPORT_ARCHIVE / "README.md"}
    }
    if archive_paths != actual_files:
        errors.append("report archive files and manifest entries differ")
    for digest, duplicates in hashes.items():
        if len(duplicates) < 2:
            continue
        declared = [record for record in duplicates if record.get("duplicate_of")]
        if len(declared) != len(duplicates) - 1:
            errors.append(f"report duplicate content {digest} is not explicitly declared")
    for archive_name, record in artifacts_by_path.items():
        duplicate_of = record.get("duplicate_of")
        if duplicate_of is None:
            continue
        target = artifacts_by_path.get(duplicate_of)
        if target is None or target.get("sha256_bytes") != record.get("sha256_bytes"):
            errors.append(f"report artifact {archive_name} has an invalid duplicate reference")


def check_report_crosswalk(errors: list[str]) -> None:
    if not REPORT_CROSSWALK.is_file():
        errors.append("missing report task crosswalk")
        return
    crosswalk: Any = json.loads(REPORT_CROSSWALK.read_text(encoding="utf-8"))
    sources = crosswalk.get("sources")
    entries = crosswalk.get("entries")
    if (
        crosswalk.get("schema_version") != "1"
        or not isinstance(sources, list)
        or not isinstance(entries, list)
    ):
        errors.append("report task crosswalk has an invalid schema")
        return

    expected: set[str] = set()
    raw_counts: dict[str, int] = {}
    namespaces: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            errors.append("report task crosswalk has an invalid source")
            continue
        namespace = source.get("namespace")
        source_path = source.get("path")
        lists = source.get("lists")
        items = source.get("items")
        if (
            not isinstance(namespace, str)
            or namespace in namespaces
            or not isinstance(source_path, str)
            or (not isinstance(lists, list) and not isinstance(items, list))
            or (isinstance(lists, list) and isinstance(items, list))
        ):
            errors.append(f"report task crosswalk source is invalid: {source}")
            continue
        namespaces.add(namespace)
        path = ROOT / source_path
        if not path.is_file() or not path.is_relative_to(REPORT_ARCHIVE):
            errors.append(f"report task crosswalk source is missing or not archived: {source_path}")
            continue
        identifiers: list[Any] = []
        if isinstance(items, list):
            identifiers.extend(items)
        elif isinstance(lists, list):
            data: Any = json.loads(path.read_text(encoding="utf-8"))
            for list_name in lists:
                records = data.get(list_name, []) if isinstance(list_name, str) else []
                if not isinstance(records, list):
                    errors.append(
                        f"report task source {source_path} has invalid list {list_name}"
                    )
                    continue
                identifiers.extend(
                    record.get("id") if isinstance(record, dict) else None
                    for record in records
                )
        for identifier in identifiers:
            if not isinstance(identifier, str):
                errors.append(f"report task source {source_path} has an invalid task")
                continue
            expected.add(f"{namespace}:{identifier}")
            raw_counts[identifier] = raw_counts.get(identifier, 0) + 1

    registry: Any = json.loads(TASK_REGISTRY.read_text(encoding="utf-8"))
    canonical_ids = {
        identifier
        for group in registry.get("groups", [])
        if isinstance(group, dict)
        for identifier in group.get("ids", [])
        if isinstance(identifier, str)
    }
    actual: set[str] = set()
    qualified_records: dict[str, Any] = {}
    allowed_relationships = {
        "canonical_task",
        "research_catalogue",
        "historical_recommendation",
        "superseded_by_research_v2",
    }
    for record in entries:
        if not isinstance(record, dict):
            errors.append("report task crosswalk contains a non-object entry")
            continue
        qualified = record.get("qualified_id")
        namespace = record.get("source_namespace")
        raw_id = record.get("raw_id")
        if (
            not isinstance(qualified, str)
            or not isinstance(namespace, str)
            or not isinstance(raw_id, str)
            or qualified != f"{namespace}:{raw_id}"
        ):
            errors.append(f"report task crosswalk entry has invalid identity: {record}")
            continue
        if qualified in actual:
            errors.append(f"report task crosswalk duplicates {qualified}")
        actual.add(qualified)
        qualified_records[qualified] = record
        if record.get("relationship") not in allowed_relationships:
            errors.append(f"report task {qualified} has an invalid relationship")
        canonical = record.get("canonical_task_id")
        if record.get("relationship") == "canonical_task" and canonical not in canonical_ids:
            errors.append(f"report task {qualified} has no canonical registry task")
        covered_by = record.get("covered_by")
        if (
            not isinstance(covered_by, list)
            or not covered_by
            or any(
                not isinstance(item, str) or not (ROOT / item).exists()
                for item in covered_by
            )
        ):
            errors.append(f"report task {qualified} has missing coverage evidence")
        if record.get("raw_id_collision") != (raw_counts.get(raw_id, 0) > 1):
            errors.append(f"report task {qualified} has incorrect collision metadata")

    if actual != expected or crosswalk.get("entry_count") != len(entries):
        errors.append("report task crosswalk does not cover every source task exactly once")
    expected_collisions = sorted(
        identifier for identifier, count in raw_counts.items() if count > 1
    )
    if crosswalk.get("raw_id_collisions") != expected_collisions:
        errors.append("report task crosswalk collision index is stale")
    for qualified, record in qualified_records.items():
        superseded_by = record.get("superseded_by")
        if superseded_by is not None and superseded_by not in qualified_records:
            errors.append(f"report task {qualified} has unknown successor {superseded_by}")


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
    valid_statuses = {
        "implemented",
        "evaluation_ready",
        "bounded_evidence",
        "partial",
        "externally_gated",
        "deferred",
    }
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
        if status in {"evaluation_ready", "partial", "externally_gated"} and not group.get("gap"):
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
    expected.update(("SEC-008", "SLEDMC-004"))
    expected.update(DIRECTION_TASK_IDS)
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


def check_native_sled_evidence(errors: list[str]) -> None:
    if not NATIVE_SLED.exists():
        return
    required = {
        "CHECKSUMS.sha256",
        "RERUN.txt",
        "manifest.json",
        "protocol.json",
        "raw-events.jsonl",
        "result.json",
        "table.md",
    }
    actual = {path.name for path in NATIVE_SLED.glob("*") if path.is_file()}
    if actual != required:
        errors.append("native SLED evidence files differ from the canonical bundle")
        return
    names: set[str] = set()
    lines = (NATIVE_SLED / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
    for line in lines:
        expected, separator, name = line.partition("  ")
        path = NATIVE_SLED / name
        if not separator or name in names or not path.is_file():
            errors.append(f"invalid native SLED checksum entry: {line}")
            continue
        names.add(name)
        actual_hash = hashlib.sha256(canonical_text_bytes(path)).hexdigest()
        if actual_hash != expected:
            errors.append(f"native SLED evidence checksum changed: {name}")
    if names != required - {"CHECKSUMS.sha256"}:
        errors.append("native SLED checksum index is incomplete")


def check_coi_evidence(errors: list[str]) -> None:
    if not COI_EVIDENCE.exists():
        return
    required = set(COI_EVIDENCE_ROOT_FILES)
    actual_root = {
        path.name for path in COI_EVIDENCE.glob("*") if path.is_file()
    }
    if actual_root != required:
        errors.append("COI evidence root files differ from the canonical bundle")
        return
    names: set[str] = set()
    lines = (COI_EVIDENCE / "CHECKSUMS.sha256").read_text(
        encoding="utf-8"
    ).splitlines()
    for line in lines:
        expected, separator, name = line.partition("  ")
        path = COI_EVIDENCE / name
        if not separator or name in names or not path.is_file():
            errors.append(f"invalid COI checksum entry: {line}")
            continue
        names.add(name)
        if hashlib.sha256(canonical_text_bytes(path)).hexdigest() != expected:
            errors.append(f"COI evidence checksum changed: {name}")
    actual_content = {
        path.relative_to(COI_EVIDENCE).as_posix()
        for path in COI_EVIDENCE.rglob("*")
        if path.is_file() and path.name != "CHECKSUMS.sha256"
    }
    if names != actual_content:
        errors.append("COI evidence checksum index is incomplete")
    result: Any = json.loads(
        (COI_EVIDENCE / "result.json").read_text(encoding="utf-8")
    )
    summary = result.get("summary", {}) if isinstance(result, dict) else {}
    if (
        result.get("complete") is not True
        or summary.get("fixtures") != summary.get("reference_verdict_agreements")
        or not isinstance(summary.get("fixtures_with_measurable_reduction"), int)
        or summary["fixtures_with_measurable_reduction"] < 1
    ):
        errors.append("COI evidence does not support its bounded equivalence claim")


def check_cedar_preflight_evidence(errors: list[str]) -> None:
    if not CEDAR_PREFLIGHT.exists():
        return
    required = {
        "CHECKSUMS.sha256",
        "RERUN.txt",
        "corpus.json",
        "manifest.json",
        "policy-bundle.json",
        "protocol.json",
        "result.json",
        "table.md",
    }
    actual = {path.name for path in CEDAR_PREFLIGHT.glob("*") if path.is_file()}
    if actual != required:
        errors.append("Cedar preflight files differ from the canonical bundle")
        return
    indexed: set[str] = set()
    for line in (CEDAR_PREFLIGHT / "CHECKSUMS.sha256").read_text(
        encoding="utf-8"
    ).splitlines():
        expected, separator, name = line.partition("  ")
        path = CEDAR_PREFLIGHT / name
        if not separator or name in indexed or not path.is_file():
            errors.append(f"invalid Cedar preflight checksum entry: {line}")
            continue
        indexed.add(name)
        if hashlib.sha256(canonical_text_bytes(path)).hexdigest() != expected:
            errors.append(f"Cedar preflight checksum changed: {name}")
    if indexed != required - {"CHECKSUMS.sha256"}:
        errors.append("Cedar preflight checksum index is incomplete")
    result: Any = json.loads(
        (CEDAR_PREFLIGHT / "result.json").read_text(encoding="utf-8")
    )
    cases = result.get("cases", []) if isinstance(result, dict) else []
    if (
        result.get("classification") != "evaluation_ready"
        or result.get("complete") is not False
        or result.get("cedar_status") != "unavailable"
        or len(cases) != 8
        or any(case.get("cedar_decision") is not None for case in cases)
    ):
        errors.append("Cedar preflight overstates unavailable parity evidence")


def check_schemas(errors: list[str]) -> None:
    required = {
        "cedar-policy-bundle.schema.json",
        "cedar-differential-corpus.schema.json",
        "cedar-differential-result.schema.json",
        "delegation-grant.schema.json",
        "delegation-trace.schema.json",
        "dynamic-plan-result.schema.json",
        "experiment-manifest.schema.json",
        "formal-verification-result.schema.json",
        "plan-patch.schema.json",
        "plan.schema.json",
        "planning-comparison-result.schema.json",
        "planning-observation.schema.json",
        "proposal-batch.schema.json",
        "proposal-batch-v2.schema.json",
        "result.schema.json",
        "scenario.schema.json",
        "trace-event.schema.json",
        "trace-event-v3.schema.json",
        "verification-ir.schema.json",
        "verification-result.schema.json",
        "verification-reduction.schema.json",
        "verification-reduction-result.schema.json",
        "agentdojo-comparison-result-v2.schema.json",
        "experiment-protocol-v2.schema.json",
        "experiment-run-manifest-v2.schema.json",
        "modeled-program.schema.json",
        "native-sled-result-v2.schema.json",
        "planning-comparison-result-v2.schema.json",
        "planning-diagnostic-suite.schema.json",
        "planning-laptop-smoke.schema.json",
        "planning-laptop-smoke-result.schema.json",
    }
    actual = {path.name for path in (ROOT / "schemas").glob("*.json")}
    for name in sorted(required - actual):
        errors.append(f"missing versioned schema: schemas/{name}")


def main() -> int:
    errors: list[str] = []
    check_architecture(errors)
    check_docs(errors)
    check_repository_governance(errors)
    check_reports(errors)
    check_archived_paper(errors)
    check_manuscript(errors)
    check_smoke_evidence(errors)
    check_native_sled_evidence(errors)
    check_coi_evidence(errors)
    check_cedar_preflight_evidence(errors)
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
