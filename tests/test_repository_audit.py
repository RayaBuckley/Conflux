"""Regression tests for platform-neutral repository evidence checks."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.audit_repository import (
    archive_digest,
    check_archived_paper,
    check_report_archive,
    check_report_crosswalk,
    supersession_has_cycle,
)


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


def test_current_paper_manifest_matches_content_and_index() -> None:
    errors: list[str] = []
    check_archived_paper(errors)
    assert errors == []


def test_current_report_archive_matches_manifest_and_index() -> None:
    errors: list[str] = []
    check_report_archive(errors)
    assert errors == []


def test_report_crosswalk_covers_every_source_task() -> None:
    errors: list[str] = []
    check_report_crosswalk(errors)
    assert errors == []


def test_supersession_cycle_detection() -> None:
    assert not supersession_has_cycle({"new": {"old"}, "old": set()})
    assert supersession_has_cycle({"first": {"second"}, "second": {"first"}})
