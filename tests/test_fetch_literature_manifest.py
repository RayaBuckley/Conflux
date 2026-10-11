"""The literature fetcher must merge its manifest, never replace the store's index.

A ``--key`` run once rewrote ``research/literature/manifest.json`` from the one entry it
had just fetched, which deleted the rows for every other key.  ``tests/test_literature_corpus.py``
compares the manifest keys with the corpus keys, so the loss is loud, but the file damage
survives until someone re-fetches the whole corpus.  These tests pin the merge.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.reproducibility

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research" / "literature" / "manifest.json"


def _load_fetcher() -> Any:
    """Load the fetcher module without importing the scripts directory as a package."""
    path = ROOT / "scripts" / "fetch_literature.py"
    spec = importlib.util.spec_from_file_location("fetch_literature", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _row(key: str, status: str = "fetched") -> dict[str, object]:
    return {
        "key": key,
        "source_category": "arxiv",
        "fetch_status": status,
        "local_files": [f"{key}/paper.txt"],
        "content_hash": "0" * 64,
        "fetched_date": "2026-10-11T03:00:00Z",
        "source_url": f"https://arxiv.org/abs/{key}",
        "error_message": "",
    }


def _write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps({"schema_version": "1", "generated_date": "2026-01-01T00:00:00Z", "entries": rows}, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_rows(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["entries"]
    assert isinstance(rows, list)
    return rows


def test_a_single_key_run_keeps_every_other_manifest_row(tmp_path: Path) -> None:
    fetcher = _load_fetcher()
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_row("alpha"), _row("beta", "skipped"), _row("gamma")])

    fetcher.update_manifest([_row("beta")], path=manifest)

    rows = _read_rows(manifest)
    assert [str(row["key"]) for row in rows] == ["alpha", "beta", "gamma"]
    assert rows[1]["fetch_status"] == "fetched"
    assert rows[0]["content_hash"] == "0" * 64
    assert rows[2]["local_files"] == ["gamma/paper.txt"]


def test_a_key_new_to_the_manifest_is_appended(tmp_path: Path) -> None:
    fetcher = _load_fetcher()
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_row("alpha")])

    fetcher.update_manifest([_row("delta")], path=manifest)

    assert [str(row["key"]) for row in _read_rows(manifest)] == ["alpha", "delta"]


def test_a_missing_manifest_starts_from_the_fetched_rows(tmp_path: Path) -> None:
    fetcher = _load_fetcher()
    manifest = tmp_path / "not-yet-written.json"

    fetcher.update_manifest([_row("alpha"), _row("beta")], path=manifest)

    assert [str(row["key"]) for row in _read_rows(manifest)] == ["alpha", "beta"]


def test_an_unreadable_manifest_does_not_stop_a_run(tmp_path: Path) -> None:
    fetcher = _load_fetcher()
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{ this is not json", encoding="utf-8")

    fetcher.update_manifest([_row("alpha")], path=manifest)

    assert [str(row["key"]) for row in _read_rows(manifest)] == ["alpha"]


def test_non_row_entries_are_dropped_rather_than_rewritten(tmp_path: Path) -> None:
    fetcher = _load_fetcher()
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_row("alpha"), {"no_key": True}, "a string"])  # type: ignore[list-item]

    fetcher.update_manifest([_row("beta")], path=manifest)

    assert [str(row["key"]) for row in _read_rows(manifest)] == ["alpha", "beta"]


def test_the_shipped_manifest_keeps_its_rows_when_one_key_is_updated(tmp_path: Path) -> None:
    if not MANIFEST_PATH.exists():
        pytest.skip("manifest.json not found")
    fetcher = _load_fetcher()
    copy = tmp_path / "manifest.json"
    copy.write_text(MANIFEST_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    before = _read_rows(copy)
    assert len(before) > 1

    fetcher.update_manifest([dict(before[0])], path=copy)

    after = _read_rows(copy)
    assert len(after) == len(before)
    assert [str(row["key"]) for row in after] == [str(row["key"]) for row in before]
