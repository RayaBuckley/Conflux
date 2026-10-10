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
    """The bundle carries the manuscript, both generated tables and the bibliography."""
    paths, _problems = bundle.dependency_paths(bundle.MANUSCRIPT, bundle.ROOT)
    shipped = {path.name for path in paths}
    assert shipped == {
        "conflux_fourth_year_2026.tex",
        "agentdojo_breadth_table.tex",
        "agentdojo_fingerprints_table.tex",
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
