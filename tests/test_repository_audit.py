"""Regression tests for platform-neutral repository evidence checks."""

from __future__ import annotations

import hashlib
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import audit_repository as audit_module
from scripts.audit_repository import (
    ROOT,
    archive_digest,
    check_archived_paper,
    check_docstrings,
    check_evidence_registry,
    check_report_archive,
    check_report_crosswalk,
    check_repository_governance,
    supersession_has_cycle,
)

pytestmark = pytest.mark.integration


def test_development_install_contains_nonisolated_build_requirements() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    build_requirements = {requirement.split(">=")[0] for requirement in project["build-system"]["requires"]}
    development_requirements = {requirement.split(">=")[0] for requirement in project["project"]["optional-dependencies"]["dev"]}
    assert build_requirements <= development_requirements


def test_canonical_archive_digest_ignores_checkout_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "evidence.md"
    path.write_bytes(b"first\r\nsecond\r\n")
    windows_digest = archive_digest(path, "canonical_utf8_lf")
    path.write_bytes(b"first\nsecond\n")
    assert archive_digest(path, "canonical_utf8_lf") == windows_digest


def test_canonical_archive_digest_rejects_semantic_change(tmp_path: Path) -> None:
    path = tmp_path / "evidence.md"
    path.write_text("first\nsecond\n", encoding="utf-8")
    original = archive_digest(path, "canonical_utf8_lf")
    path.write_text("first\nchanged\n", encoding="utf-8")
    assert archive_digest(path, "canonical_utf8_lf") != original


def test_raw_archive_digest_remains_byte_exact(tmp_path: Path) -> None:
    path = tmp_path / "evidence.bin"
    path.write_bytes(b"first\r\nsecond\r\n")
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert archive_digest(path, "raw_bytes") == expected
    path.write_bytes(b"first\nsecond\n")
    assert archive_digest(path, "raw_bytes") != expected


def test_unknown_archive_mode_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "evidence"
    path.write_bytes(b"content")
    with pytest.raises(ValueError, match="unsupported archive checksum mode"):
        archive_digest(path, "platform_default")


REPOSITORY_CHECKS: dict[str, Callable[[list[str]], None]] = {
    "archived_paper_manifest": check_archived_paper,
    "report_archive_manifest": check_report_archive,
    "report_crosswalk": check_report_crosswalk,
    "repository_governance": check_repository_governance,
    "docstrings": check_docstrings,
    "evidence_registry": check_evidence_registry,
}


@pytest.mark.parametrize("check", list(REPOSITORY_CHECKS.values()), ids=list(REPOSITORY_CHECKS))
def test_repository_check_reports_no_errors(check: Callable[[list[str]], None]) -> None:
    """Every repository check must leave its error list empty on this checkout."""
    errors: list[str] = []
    check(errors)
    assert errors == []


def test_unregistered_evidence_file_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A file in docs/evidence that nobody registered must be named, not ignored."""
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "registered.md").write_text("registered\n", encoding="utf-8")
    (evidence / "orphan.md").write_text("orphan\n", encoding="utf-8")
    monkeypatch.setattr(audit_module, "DOCS", tmp_path)
    monkeypatch.setattr(audit_module, "CANONICAL_DOCS", {"evidence/registered.md"})

    errors: list[str] = []
    audit_module.check_evidence_registry(errors)

    assert errors == ["unregistered evidence file docs/evidence/orphan.md: add it to CANONICAL_DOCS"]


def test_supersession_cycle_detection() -> None:
    assert not supersession_has_cycle({"new": {"old"}, "old": set()})
    assert supersession_has_cycle({"first": {"second"}, "second": {"first"}})
