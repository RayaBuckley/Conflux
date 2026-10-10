"""Tests for the current manuscript's generated AgentDojo breadth tables."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts import generate_fourth_year_tables as tables


def test_generated_tables_match_the_retained_bundles() -> None:
    """Every generated table must match regeneration from the retained bundles."""
    outputs = tables.generate_all()
    assert len(outputs) == 2
    for path, content in outputs:
        assert tables._check(path, content), f"stale generated table: {path.name}"


def test_breadth_table_counts_the_retained_bundles() -> None:
    """The breadth table records one row per retained bundle plus a total row."""
    content = (tables.OUT / "agentdojo_breadth_table.tex").read_text(encoding="utf-8")
    assert "banking (\\textit{stratified}, 4 tasks) & 24 & 24 & 0 & 24 & 0 &" in content
    assert "slack (\\textit{stratified}, 5 tasks) & 30 & 24 & 0 & 24 & 6 &" in content
    assert "\\textbf{Total} & \\textbf{204} & \\textbf{198}" in content
    for directory in ("result.json", "protocol.json"):
        assert f"agentdojo-stratified-travel-v1/{directory} SHA-256: " in content


def test_fingerprints_table_records_every_bundle() -> None:
    """Each retained bundle contributes its own protocol identity to the fingerprint table."""
    content = (tables.OUT / "agentdojo_fingerprints_table.tex").read_text(encoding="utf-8")
    for _label, directory in tables.BUNDLES:
        assert directory in content
    # The four stratified bundles were retained before the sweep recorded the selection's own id, so
    # the table reports the spelling those runs actually recorded.
    assert "banking:expanded:user\\_task\\_0" in content
    assert "banking:stratified-v1" not in content


def test_a_missing_bundle_names_the_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A bundle that is not retained must fail loudly instead of producing an empty table."""
    monkeypatch.setattr(tables, "RUNS", tmp_path)
    with pytest.raises(FileNotFoundError, match="retained bundle file is missing"):
        tables.table_agentdojo_breadth()


def test_check_reports_a_changed_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The ``--check`` mode must fail when a retained table no longer matches regeneration."""
    monkeypatch.setattr(tables, "OUT", tmp_path)
    for path, content in tables.generate_all():
        tables._write(path, content)

    monkeypatch.setattr(sys, "argv", ["generate_fourth_year_tables.py", "--check"])
    assert tables.main() == 0

    changed = tmp_path / "agentdojo_breadth_table.tex"
    changed.write_text("hand-written number: 42\n", encoding="utf-8")
    assert tables.main() == 1
    assert "MISMATCH in:" in capsys.readouterr().out
