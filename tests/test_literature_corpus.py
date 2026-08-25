"""Tests for the literature corpus schema and data integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

CORPUS_PATH = Path(__file__).resolve().parents[1] / "research" / "reports" / "analysis" / "literature_corpus.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "literature-corpus.schema.json"

pytestmark = pytest.mark.integration


class TestLiteratureCorpusSchema:
    def test_schema_is_valid(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)

    def test_corpus_validates_against_schema(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(corpus)


class TestCorpusIntegrity:
    def _load(self) -> list[dict[str, object]]:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        entries = corpus["entries"]
        assert isinstance(entries, list)
        return entries

    def test_keys_are_unique(self) -> None:
        entries = self._load()
        keys = [str(entry["key"]) for entry in entries]
        assert len(keys) == len(set(keys))

    def test_all_entries_have_last_checked(self) -> None:
        for entry in self._load():
            assert entry["last_checked"], f"entry {entry['key']} missing last_checked"

    def test_all_entries_have_verification(self) -> None:
        for entry in self._load():
            verified = entry["verified"]
            assert isinstance(verified, dict)
            assert str(verified["method"]) in ("primary_source", "scholar_metadata", "unverified")
            assert verified["date"]

    def test_no_duplicate_arxiv_ids(self) -> None:
        arxiv_ids = [str(entry["arxiv_id"]) for entry in self._load() if entry.get("arxiv_id")]
        assert len(arxiv_ids) == len(set(arxiv_ids))

    def test_no_duplicate_dois(self) -> None:
        dois = [str(entry["doi"]) for entry in self._load() if entry.get("doi")]
        assert len(dois) == len(set(dois))
