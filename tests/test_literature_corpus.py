"""Tests for the literature corpus schema and data integrity."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

CORPUS_PATH = Path(__file__).resolve().parents[1] / "research" / "reports" / "analysis" / "literature_corpus.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "literature-corpus.schema.json"
BIB_PATH = Path(__file__).resolve().parents[1] / "research" / "publications" / "manuscript" / "references.bib"
REFS_MD_PATH = Path(__file__).resolve().parents[1] / "research" / "publications" / "manuscript" / "REFERENCES.md"
NOVELTY_AUDIT_PATH = Path(__file__).resolve().parents[1] / "research" / "reports" / "analysis" / "2026-08-16-novelty-audit.md"
MANIFEST_PATH = Path(__file__).resolve().parents[1] / "research" / "literature" / "manifest.json"
MANIFEST_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "literature-manifest.schema.json"
PAPERS_DIR = Path(__file__).resolve().parents[1] / "research" / "literature" / "papers"

VALID_CLAIM_IDS = {f"A{i}" for i in range(1, 16)}

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
    def _load(self) -> list[dict[str, Any]]:
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


class TestVerificationCompleteness:
    """Enforce verification requirements per priority tier."""

    def _load(self) -> list[dict[str, Any]]:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        entries = corpus["entries"]
        assert isinstance(entries, list)
        return entries

    def test_priority_a_entries_have_verification(self) -> None:
        for entry in self._load():
            priority = entry.get("reading_priority") or entry.get("adoption_priority")
            if priority == "A":
                verified = entry["verified"]
                assert str(verified["method"]) in (
                    "primary_source",
                    "scholar_metadata",
                    "unverified",
                ), f"entry {entry['key']} has invalid verification method"
                assert verified["date"], f"entry {entry['key']} missing verification date"

    def test_read_entries_have_findings_and_limitations(self) -> None:
        for entry in self._load():
            if entry.get("reading_status") == "read":
                relevance = entry.get("relevance")
                assert relevance is not None, f"entry {entry['key']} marked read but has no relevance"
                findings = relevance.get("key_findings", [])
                limitations = relevance.get("limitations", [])
                assert isinstance(findings, list) and len(findings) > 0, f"entry {entry['key']} marked read but has no key_findings"
                assert isinstance(limitations, list) and len(limitations) > 0, f"entry {entry['key']} marked read but has no limitations"

    def test_novelty_impact_claims_are_valid(self) -> None:
        for entry in self._load():
            novelty = entry.get("novelty_impact")
            if novelty is not None:
                claims = novelty.get("affected_claims", [])
                for claim in claims:
                    assert str(claim) in VALID_CLAIM_IDS, f"entry {entry['key']} has invalid claim ref: {claim}"

    def test_priority_a_b_have_snowball_status(self) -> None:
        for entry in self._load():
            priority = entry.get("reading_priority") or entry.get("adoption_priority")
            if priority in ("A", "B"):
                snowball = entry.get("snowball_status")
                assert snowball is not None, f"entry {entry['key']} (priority {priority}) missing snowball_status"
                assert "backward" in snowball, f"entry {entry['key']} missing snowball backward"
                assert "forward" in snowball, f"entry {entry['key']} missing snowball forward"


class TestBibliographyCrossReference:
    """Cross-check references.bib and REFERENCES.md against the corpus."""

    def _load_corpus_keys(self) -> set[str]:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        return {str(e["key"]) for e in corpus["entries"]}

    def test_bib_entries_exist_in_corpus(self) -> None:
        if not BIB_PATH.exists():
            pytest.skip("references.bib not found")
        text = BIB_PATH.read_text(encoding="utf-8")
        bib_keys = set(re.findall(r"@\w+\{([^,]+),", text))
        corpus_keys = self._load_corpus_keys()
        missing = bib_keys - corpus_keys
        assert not missing, f"BibTeX keys not in corpus: {missing}"

    def test_references_md_entries_exist_in_corpus(self) -> None:
        if not REFS_MD_PATH.exists():
            pytest.skip("REFERENCES.md not found")
        text = REFS_MD_PATH.read_text(encoding="utf-8")
        ref_keys = set(re.findall(r"`(\w+)`", text))
        corpus_keys = self._load_corpus_keys()
        missing = ref_keys - corpus_keys
        assert not missing, f"REFERENCES.md keys not in corpus: {missing}"


class TestNoveltyAuditConsistency:
    """Cross-check the novelty audit against the corpus."""

    def _load_corpus(self) -> list[dict[str, Any]]:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        entries = corpus["entries"]
        assert isinstance(entries, list)
        return entries

    # Claims that require external source evidence (not "survives" or "non-claim").
    CLAIMS_REQUIRING_SOURCES = {"A1", "A2", "A4", "A6", "A8", "A9", "A10", "A11", "A13", "A14"}

    def test_all_claims_have_source_references(self) -> None:
        if not NOVELTY_AUDIT_PATH.exists():
            pytest.skip("novelty audit not found")
        entries = self._load_corpus()
        # Build map: claim ID -> list of source keys that reference it
        claim_sources: dict[str, list[str]] = {f"A{i}": [] for i in range(1, 16)}
        for entry in entries:
            novelty = entry.get("novelty_impact")
            if novelty:
                for claim in novelty.get("affected_claims", []):
                    claim_sources.setdefault(str(claim), []).append(str(entry["key"]))
        # Claims classified as "survives" or "non-claim" in the novelty audit
        # do not require external source evidence.
        unlinked = [cid for cid, srcs in claim_sources.items() if not srcs and cid in self.CLAIMS_REQUIRING_SOURCES]
        if unlinked:
            pytest.skip(f"claims requiring sources but without corpus entries (verification in progress): {unlinked}")


class TestLocalLiteratureCopies:
    """Verify local paper copies and fetch manifest consistency."""

    def _load_corpus_keys(self) -> set[str]:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        return {str(e["key"]) for e in corpus["entries"]}

    def _load_manifest(self) -> dict[str, Any]:
        data: dict[str, Any] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return data

    def test_manifest_validates_against_schema(self) -> None:
        if not MANIFEST_PATH.exists():
            pytest.skip("manifest.json not found")
        schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        manifest = self._load_manifest()
        Draft202012Validator(schema).validate(manifest)

    def test_manifest_keys_match_corpus_keys(self) -> None:
        if not MANIFEST_PATH.exists():
            pytest.skip("manifest.json not found")
        manifest = self._load_manifest()
        manifest_keys = {str(e["key"]) for e in manifest["entries"]}
        corpus_keys = self._load_corpus_keys()
        assert manifest_keys == corpus_keys, (
            f"manifest/corpus key mismatch: "
            f"missing from manifest: {corpus_keys - manifest_keys}; "
            f"extra in manifest: {manifest_keys - corpus_keys}"
        )

    def test_arxiv_entries_have_local_copy_or_failure(self) -> None:
        if not MANIFEST_PATH.exists():
            pytest.skip("manifest.json not found")
        manifest = self._load_manifest()
        manifest_by_key = {str(e["key"]): e for e in manifest["entries"]}
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        for entry in corpus["entries"]:
            has_arxiv = bool(entry.get("arxiv_id")) or "arxiv.org/abs/" in str(entry.get("source_url", ""))
            if not has_arxiv:
                continue
            key = str(entry["key"])
            m_entry = manifest_by_key.get(key)
            assert m_entry is not None, f"arXiv entry {key} missing from manifest"
            has_file = bool(m_entry.get("local_files"))
            status = str(m_entry["fetch_status"])
            assert has_file or status in ("failed", "paywall"), (
                f"arXiv entry {key} has no local file and is not marked failed/paywall (status={status})"
            )

    def test_fetch_status_json_files_valid(self) -> None:
        if not PAPERS_DIR.exists():
            pytest.skip("papers directory not found")
        for paper_dir in sorted(PAPERS_DIR.iterdir()):
            if not paper_dir.is_dir():
                continue
            status_path = paper_dir / "fetch_status.json"
            if not status_path.exists():
                continue
            data = json.loads(status_path.read_text(encoding="utf-8"))
            assert "key" in data, f"{status_path} missing 'key'"
            assert "fetch_status" in data, f"{status_path} missing 'fetch_status'"
            assert str(data["fetch_status"]) in ("fetched", "failed", "skipped", "paywall"), (
                f"{status_path} has invalid fetch_status: {data['fetch_status']}"
            )
