"""Tests for the arXiv source bundle of the current manuscript."""

from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

from scripts import build_arxiv_bundle as bundle

if TYPE_CHECKING:
    import pytest


def _manuscript_copy(tmp_path: Path) -> Path:
    """Copy the manuscript directory so dependency resolution runs inside tmp_path."""
    destination = tmp_path / "manuscript"
    shutil.copytree(bundle.MANUSCRIPT.parent, destination)
    return destination / bundle.MANUSCRIPT.name


def test_manuscript_dependencies_resolve() -> None:
    """Every file the manuscript inputs must exist, with nothing missing."""
    _paths, problems = bundle.dependency_paths(bundle.MANUSCRIPT, bundle.ROOT)
    assert problems == []


def test_ship_set_covers_the_tables_and_the_bibliography() -> None:
    """The bundle carries the manuscript, every generated table and the bibliography."""
    paths, _problems = bundle.dependency_paths(bundle.MANUSCRIPT, bundle.ROOT)
    shipped = {path.name for path in paths}
    assert shipped == {
        "conflux_fourth_year_2026.tex",
        "agentdojo_breadth_table.tex",
        "agentdojo_fingerprints_table.tex",
        "semantic_conformance_table.tex",
        "native_sled_reproduction_table.tex",
        "sledv_scaling_table.tex",
        "references.bib",
    }


def test_tracked_manifest_is_current() -> None:
    """The tracked manifest must match the tree it describes."""
    assert bundle.manifest_problems() == []


def test_missing_input_is_reported(tmp_path: Path) -> None:
    """An input the tree does not carry is reported, not packaged."""
    manuscript = _manuscript_copy(tmp_path)
    manuscript.write_text(
        manuscript.read_text(encoding="utf-8") + "\n\\input{generated/tables/missing_table}\n",
        encoding="utf-8",
    )
    _paths, problems = bundle.dependency_paths(manuscript, tmp_path)
    assert problems == [f"{manuscript.name}: input target not found: generated/tables/missing_table"]


def test_stale_manifest_is_reported(tmp_path: Path) -> None:
    """A digest that no longer matches the tree is reported rather than ignored."""
    manifest = json.loads(bundle.MANIFEST.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64
    stale = tmp_path / "ARXIV_BUNDLE.json"
    stale.write_text(json.dumps(manifest), encoding="utf-8")
    problems = bundle.manifest_problems(stale)
    assert any("changed since the manifest was written" in problem for problem in problems)


def test_build_packages_exactly_the_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The archive holds the manifest's files under the archive root, and nothing else."""
    monkeypatch.setattr(bundle, "OUT", tmp_path)
    archive, problems = bundle.build(out=tmp_path)
    assert problems == []
    assert archive.parent == tmp_path
    with tarfile.open(archive, "r:gz") as tar:
        assert sorted(tar.getnames()) == sorted(
            item["path"] for item in json.loads(bundle.MANIFEST.read_text(encoding="utf-8"))["files"]
        )


def test_build_is_deterministic(tmp_path: Path) -> None:
    """Two builds of the same tree produce byte-identical archives."""
    first, _ = bundle.build(out=tmp_path / "one")
    second, _ = bundle.build(out=tmp_path / "two")
    assert first.read_bytes() == second.read_bytes()


def _fake_manuscript(tmp_path: Path, *, title: str = "A title", abstract: str = "An abstract.") -> Path:
    """Build a tiny manuscript tree so the metadata and name rules can be exercised."""
    root = tmp_path / "paper"
    tables = root / "generated" / "tables"
    tables.mkdir(parents=True)
    (tables / "table_one.tex").write_text("\\begin{table}\\end{table}\n", encoding="utf-8")
    (root / "references.bib").write_text("@book{k}\n", encoding="utf-8")
    manuscript = root / "paper.tex"
    manuscript.write_text(
        "\\documentclass{article}\n"
        f"\\title{{{title}}}\n"
        "\\begin{document}\n"
        "\\input{generated/tables/table_one}\n"
        "\\bibliography{references}\n"
        "\\begin{abstract}\n"
        f"{abstract}\n"
        "\\end{abstract}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    return manuscript


def test_file_name_characters_are_checked(tmp_path: Path) -> None:
    """A shipped name outside arXiv's character set is refused, an allowed name is not."""
    allowed = tmp_path / "ok_file-name.txt"
    rejected = tmp_path / "bad name.txt"
    allowed.write_text("x", encoding="utf-8")
    rejected.write_text("x", encoding="utf-8")
    problems = bundle.name_problems([allowed, rejected], tmp_path)
    assert len(problems) == 1
    assert "bad name.txt" in problems[0]


def test_a_bad_file_name_stops_the_manifest(tmp_path: Path) -> None:
    """A dependency with a rejected name blocks the manifest, not just the build."""
    manuscript = _fake_manuscript(tmp_path)
    spaced = manuscript.parent / "generated" / "tables" / "table two.tex"
    spaced.write_text("x", encoding="utf-8")
    manuscript.write_text(
        manuscript.read_text(encoding="utf-8") + "\\input{generated/tables/table two}\n", encoding="utf-8",
    )
    _manifest, problems = bundle.manifest_for(manuscript, tmp_path)
    assert any("rejects the file-name segment" in problem for problem in problems)


def test_reference_case_rule() -> None:
    """An added extension is fine; a name that differs in case is not."""
    assert not bundle.case_mismatch("generated/tables/table_one", "generated/tables/table_one.tex", (".tex",))
    assert bundle.case_mismatch("generated/tables/Table_One", "generated/tables/table_one.tex", (".tex",))
    assert bundle.case_mismatch("Fig", "fig.pdf", (".pdf",))
    assert not bundle.case_mismatch("fig.pdf", "fig.pdf", (".pdf",))


def test_metadata_extraction_drops_the_subtitle_line(tmp_path: Path) -> None:
    """The form's title field carries the title, not the typeset subtitle line."""
    manuscript = _fake_manuscript(tmp_path, title="Real title\\\\\\large Subtitle")
    title, abstract = bundle.metadata_strings(manuscript)
    assert title == "Real title"
    assert abstract == "An abstract."


def test_long_abstract_is_refused(tmp_path: Path) -> None:
    """arXiv refuses an abstract past 1920 characters, so the manifest does too."""
    manuscript = _fake_manuscript(tmp_path, abstract="x" * 1921)
    problems = bundle.metadata_problems(manuscript)
    assert problems and "1921" in problems[0]


def test_non_ascii_metadata_is_refused(tmp_path: Path) -> None:
    """The submission form accepts ASCII metadata only."""
    manuscript = _fake_manuscript(tmp_path, title="Caf\u00e9 study")
    problems = bundle.metadata_problems(manuscript)
    assert problems and "ASCII" in problems[0]
