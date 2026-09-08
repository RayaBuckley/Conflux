"""Integrate the Final Corrected Literature Landscape CSV into the corpus.

Reads the CSV matrix from the literature landscape package, matches each row
to an existing corpus entry (by arXiv ID, URL, or title), updates matched
entries with corrected metadata, and creates new corpus entries, manifest
entries, and per-paper ``fetch_status.json`` files for unmatched rows.

Usage::

    python scripts/integrate_literature_landscape.py           # integrate
    python scripts/integrate_literature_landscape.py --dry-run   # preview only
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "research" / "literature" / "literature_matrix_2026-09-07.csv"
CORPUS_PATH = ROOT / "research" / "reports" / "analysis" / "literature_corpus.json"
MANIFEST_PATH = ROOT / "research" / "literature" / "manifest.json"
PAPERS_DIR = ROOT / "research" / "literature" / "papers"

INTEGRATION_DATE = "2026-09-07"

ARXIV_URL_RE = re.compile(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", re.IGNORECASE)
DOI_URL_RE = re.compile(r"doi\.org/(10\.\S+)", re.IGNORECASE)

# Package ID -> corpus key for entries that already exist in the corpus.
# These will be updated with corrected metadata from the CSV.
MATCHED: dict[str, str] = {
    "L014": "spotlighting",
    "L015": "struq",
    "L016": "fsecure",
    "L017": "camel",
    "L018": "progent",
    "L020": "designpatterns",
    "L021": "criticaleval",
    "L023": "forge",
    "L025": "pact",
    "L029": "rbac",
    "L031": "hru",
    "L032": "securityautomata",
    "L033": "hyperproperties",
    "L038": "zanzibar",
    "N007": "difc",
    "N008": "myersliskov",
    "N009": "robustdeclassification",
    "N010": "nmifc",
    "N021": "agentspec",
    "N026": "agentdojo",
    "N027": "injecagent",
    "N028": "asb",
    "N029": "clarkwilson",
    "N031": "biba1977",
    "N032": "denning1976",
    "N037": "cegar",
    "N040": "capsicum",
    "N041": "whyprovenance",
    "N042": "provsemirings",
    "N043": "goguenmeseguer",
    "N044": "saltzerschroeder",
}

# Package ID -> corpus key for new entries.
NEW_KEYS: dict[str, str] = {
    "L001": "lasco",
    "L002": "ponder",
    "L003": "policymachine",
    "L004": "policymanagespec",
    "L005": "privilegeescalation",
    "L006": "contextualintegrity",
    "L007": "ciframework",
    "L008": "sparcle",
    "L009": "policyrefinement",
    "L010": "controllednl",
    "L011": "text2policy",
    "L012": "policybyexample",
    "L013": "cedarpaper",
    "L019": "cillm",
    "L022": "agentguardian",
    "L024": "contextualmanipulation",
    "L026": "autoformpolicy",
    "L027": "pinjectiondetect",
    "L028": "policybank",
    "L030": "abacsurvey",
    "L034": "modelchecking",
    "L035": "boundedmodelchecking",
    "L036": "ic3",
    "L037": "accesscalculus",
    "L039": "xacml",
    "L040": "policyconflicts",
    "N001": "executionhistory",
    "N002": "policymaker",
    "N003": "keynote",
    "N004": "binder",
    "N005": "cassandra",
    "N006": "uconabc",
    "N011": "flam",
    "N012": "flac",
    "N013": "pbac",
    "N014": "securepbac",
    "N015": "nl2actl",
    "N016": "ace",
    "N017": "goalrefinement",
    "N018": "fret",
    "N019": "nl2spec",
    "N020": "autolllm",
    "N022": "solverpolicy",
    "N023": "symbolicguardrails",
    "N024": "agentrfc",
    "N025": "agentthread",
    "N030": "chinesewall",
    "N033": "rtframework",
    "N034": "delegationlogic",
    "N035": "stackinspection",
    "N036": "hyperltl",
    "N038": "partialorder",
    "N039": "capabilitymyths",
}

PRIORITY_MAP: dict[str, str] = {
    "Critical": "A",
    "High": "B",
    "Moderate": "C",
    "Low": "D",
}

REVIEW_STATUS_TO_METHOD: dict[str, str] = {
    "Verified primary": "primary_source",
    "Verified primary; metadata corrected": "primary_source",
    "Verified primary; version/title history needs note": "primary_source",
    "Verified standard/primary": "primary_source",
    "Verified bibliographic": "scholar_metadata",
    "Verified bibliographic/primary lineage": "scholar_metadata",
    "Verified primary/bibliographic": "scholar_metadata",
    "Verified primary PDF": "primary_source",
    "Verified NASA primary": "primary_source",
    "Verified secondary/primary-report metadata": "scholar_metadata",
    "Verified primary/author manuscript listing": "primary_source",
    "Existing Conflux reference": "primary_source",
    "Add foundational citation": "scholar_metadata",
    "Add methodology citation": "scholar_metadata",
    "Standards reference": "scholar_metadata",
    "Needs full-text review": "unverified",
    "Needs exact canonical citation verification before publication": "unverified",
    "Needs exact bibliographic verification before publication": "unverified",
    "Needs exact canonical source verification before publication": "unverified",
    "Discovery candidate - verify exact metadata": "unverified",
    "Verified primary metadata; author list to verify before publication citation": "scholar_metadata",
}


def extract_arxiv_id(url: str) -> str:
    match = ARXIV_URL_RE.search(url)
    return match.group(1) if match else ""


def extract_doi(url: str) -> str:
    match = DOI_URL_RE.search(url)
    return match.group(1) if match else ""


def classify_source(url: str) -> str:
    if "arxiv.org/abs/" in url:
        return "arxiv"
    if url.startswith("local:"):
        return "local"
    if "github.com" in url:
        return "repository"
    if "doi.org" in url:
        return "doi"
    if url.endswith(".pdf"):
        return "open_pdf"
    if url.startswith("http"):
        return "open_html"
    return "open_html"


def parse_authors(authors_str: str) -> list[str]:
    if not authors_str.strip():
        return []
    parts = [a.strip() for a in authors_str.split(";")]
    return [p for p in parts if p]


def parse_limitations(supported: str, inferred: str) -> list[str]:
    result: list[str] = []
    if supported.strip():
        result.append(supported.strip())
    if inferred.strip():
        result.append(inferred.strip())
    return result or ["Not yet assessed"]


def parse_key_findings(mechanism: str, uniqueness: str) -> list[str]:
    result: list[str] = []
    if mechanism.strip():
        result.append(mechanism.strip())
    if uniqueness.strip():
        result.append(uniqueness.strip())
    return result or ["Not yet assessed"]


def determine_source_type(row: dict[str, str]) -> str:
    work = row.get("Work", "").lower()
    stream = row.get("Research stream", "").lower()
    review_status = row.get("Review status", "").lower()
    if "standard" in review_status or "xacml" in work:
        return "standard"
    if "principles of model checking" in work:
        return "book"
    if "survey" in stream or "survey" in work:
        return "survey"
    return "primary_paper"


def build_verified(row: dict[str, str]) -> dict[str, str]:
    review_status = row.get("Review status", "")
    method = REVIEW_STATUS_TO_METHOD.get(review_status, "unverified")
    claim_safe = row.get("Claim-safe status", "")
    notes_parts: list[str] = []
    if "metadata corrected" in review_status.lower():
        notes_parts.append("Metadata corrected from literature landscape package")
    if "replaced" in review_status.lower():
        notes_parts.append("Replaced mislabelled entry from literature landscape package")
    if claim_safe and "needs citation verification" in claim_safe.lower():
        notes_parts.append("Needs citation verification before publication")
    if not notes_parts:
        notes_parts.append("Integrated from Final Corrected Literature Landscape 2026-09-07")
    return {
        "method": method,
        "depth": "metadata_only",
        "date": INTEGRATION_DATE,
        "notes": "; ".join(notes_parts),
        "checked_by": "ai_agent",
    }


def build_new_entry(row: dict[str, str], key: str) -> dict[str, Any]:
    source_url = row.get("Primary/source URL", "")
    arxiv_id = extract_arxiv_id(source_url)
    doi = extract_doi(source_url)
    priority = row.get("Priority", "")
    reading_priority = PRIORITY_MAP.get(priority, "D")

    entry: dict[str, Any] = {
        "key": key,
        "title": row.get("Work", ""),
        "authors": parse_authors(row.get("Authors", "")),
        "year": int(row.get("Year", "0") or "0"),
        "source_url": source_url,
        "verified": build_verified(row),
        "last_checked": INTEGRATION_DATE,
        "adoption_priority": reading_priority,
        "closest_relation": row.get("Agent-security relevance", ""),
        "stream": row.get("Research stream", ""),
        "mechanism": row.get("Core mechanism / contribution", ""),
        "claim_refs": [],
        "snowball_status": {
            "backward": "pending",
            "forward": "pending",
        },
        "reading_status": "not_started",
        "reading_priority": reading_priority,
        "source_type": determine_source_type(row),
    }

    if arxiv_id:
        entry["arxiv_id"] = arxiv_id
    if doi:
        entry["doi"] = doi

    relevance: dict[str, Any] = {
        "useful_parts": row.get("Recommended Conflux use", ""),
        "conflux_relation": row.get("Relationship to Conflux", ""),
        "key_findings": parse_key_findings(
            row.get("Core mechanism / contribution", ""),
            row.get("Uniqueness", ""),
        ),
        "limitations": parse_limitations(
            row.get("Source-supported limitations", ""),
            row.get("Reviewer-inferred limitations", ""),
        ),
    }
    entry["relevance"] = relevance

    return entry


def update_existing_entry(
    entry: dict[str, Any],
    row: dict[str, str],
) -> dict[str, Any]:
    updated = dict(entry)
    csv_year = int(row.get("Year", "0") or "0")
    if csv_year:
        updated["year"] = csv_year
    csv_authors = parse_authors(row.get("Authors", ""))
    if csv_authors:
        updated["authors"] = csv_authors
    csv_title = row.get("Work", "")
    if csv_title:
        updated["title"] = csv_title
    csv_url = row.get("Primary/source URL", "")
    if csv_url:
        updated["source_url"] = csv_url
    arxiv_id = extract_arxiv_id(csv_url)
    if arxiv_id:
        updated["arxiv_id"] = arxiv_id
    doi = extract_doi(csv_url)
    if doi:
        updated["doi"] = doi
    updated["stream"] = row.get("Research stream", updated.get("stream", ""))
    updated["mechanism"] = row.get(
        "Core mechanism / contribution",
        updated.get("mechanism", ""),
    )
    updated["closest_relation"] = row.get(
        "Agent-security relevance",
        updated.get("closest_relation", ""),
    )
    updated["last_checked"] = INTEGRATION_DATE

    existing_verified = updated.get("verified", {})
    verified = build_verified(row)
    if existing_verified.get("method") and existing_verified["method"] != "unverified":
        verified["method"] = existing_verified["method"]
    if existing_verified.get("depth") and existing_verified["depth"] != "metadata_only":
        verified["depth"] = existing_verified["depth"]
    updated["verified"] = verified

    relevance = updated.get("relevance", {})
    csv_relevance: dict[str, Any] = {
        "useful_parts": row.get(
            "Recommended Conflux use",
            relevance.get("useful_parts", ""),
        ),
        "conflux_relation": row.get(
            "Relationship to Conflux",
            relevance.get("conflux_relation", ""),
        ),
        "key_findings": parse_key_findings(
            row.get("Core mechanism / contribution", ""),
            row.get("Uniqueness", ""),
        ),
        "limitations": parse_limitations(
            row.get("Source-supported limitations", ""),
            row.get("Reviewer-inferred limitations", ""),
        ),
    }
    updated["relevance"] = csv_relevance

    return updated


def build_manifest_entry(
    key: str,
    source_url: str,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if existing:
        updated = dict(existing)
        updated["source_url"] = source_url
        return updated
    category = classify_source(source_url)
    return {
        "key": key,
        "source_category": category,
        "fetch_status": "skipped",
        "local_files": [],
        "content_hash": "",
        "fetched_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_url": source_url,
        "error_message": "Not yet fetched; added by literature landscape integration",
    }


def write_fetch_status(key: str, source_url: str) -> None:
    paper_dir = PAPERS_DIR / key
    paper_dir.mkdir(parents=True, exist_ok=True)
    status = {
        "key": key,
        "source_category": classify_source(source_url),
        "source_url": source_url,
        "fetch_status": "skipped",
        "local_files": [],
        "content_hash": "",
        "fetched_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "error_message": "Not yet fetched; added by literature landscape integration",
    }
    (paper_dir / "fetch_status.json").write_text(
        json.dumps(status, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Integrate the Final Corrected Literature Landscape CSV into the corpus.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files.")
    arguments = parser.parse_args()

    if not CSV_PATH.exists():
        print(f"Error: CSV not found at {CSV_PATH}", file=sys.stderr)
        return 1
    if not CORPUS_PATH.exists():
        print(f"Error: corpus not found at {CORPUS_PATH}", file=sys.stderr)
        return 1

    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_entries = corpus["entries"]
    corpus_by_key = {e["key"]: e for e in corpus_entries}

    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_by_key = {e["key"]: e for e in manifest["entries"]}
    else:
        manifest = {"schema_version": "1", "generated_date": "", "entries": []}
        manifest_by_key = {}

    updated_count = 0
    added_count = 0
    new_entries: list[dict[str, Any]] = []
    new_manifest_entries: list[dict[str, Any]] = []

    for row in rows:
        entry_id = row.get("ID", "")
        if entry_id in MATCHED:
            existing_key = MATCHED[entry_id]
            existing_entry = corpus_by_key.get(existing_key)
            if existing_entry is None:
                existing_corpus_keys = sorted(corpus_by_key.keys())
                print(
                    f"WARNING: Matched key '{existing_key}' for {entry_id} not found in corpus. "
                    f"Available keys: {existing_corpus_keys[:10]}...",
                    file=sys.stderr,
                )
                new_key = NEW_KEYS.get(entry_id, entry_id.lower())
                new_entry = build_new_entry(row, new_key)
                new_entries.append(new_entry)
                source_url = row.get("Primary/source URL", "")
                new_manifest_entries.append(
                    build_manifest_entry(new_key, source_url),
                )
                if not arguments.dry_run:
                    write_fetch_status(new_key, source_url)
                added_count += 1
                continue
            updated_entry = update_existing_entry(existing_entry, row)
            corpus_by_key[existing_key] = updated_entry
            existing_manifest = manifest_by_key.get(existing_key)
            source_url = row.get("Primary/source URL", "")
            manifest_by_key[existing_key] = build_manifest_entry(
                existing_key,
                source_url,
                existing_manifest,
            )
            updated_count += 1
        elif entry_id in NEW_KEYS:
            new_key = NEW_KEYS[entry_id]
            if new_key in corpus_by_key:
                print(
                    f"WARNING: New key '{new_key}' for {entry_id} already exists in corpus; updating.",
                    file=sys.stderr,
                )
                updated_entry = update_existing_entry(
                    corpus_by_key[new_key],
                    row,
                )
                corpus_by_key[new_key] = updated_entry
                updated_count += 1
                continue
            new_entry = build_new_entry(row, new_key)
            new_entries.append(new_entry)
            source_url = row.get("Primary/source URL", "")
            new_manifest_entries.append(
                build_manifest_entry(new_key, source_url),
            )
            if not arguments.dry_run:
                write_fetch_status(new_key, source_url)
            added_count += 1
        else:
            print(f"WARNING: {entry_id} not in MATCHED or NEW_KEYS; skipping.", file=sys.stderr)

    all_entries = list(corpus_by_key.values()) + new_entries
    all_entries.sort(key=lambda e: e["key"])

    all_manifest = list(manifest_by_key.values()) + new_manifest_entries
    all_manifest.sort(key=lambda e: e["key"])

    print(f"Updated: {updated_count}")
    print(f"Added: {added_count}")
    print(f"Total corpus entries: {len(all_entries)}")
    print(f"Total manifest entries: {len(all_manifest)}")

    corpus_keys = {e["key"] for e in all_entries}
    manifest_keys = {e["key"] for e in all_manifest}
    missing_in_manifest = corpus_keys - manifest_keys
    missing_in_corpus = manifest_keys - corpus_keys
    if missing_in_manifest:
        print(f"WARNING: keys in corpus but not manifest: {missing_in_manifest}", file=sys.stderr)
    if missing_in_corpus:
        print(f"WARNING: keys in manifest but not corpus: {missing_in_corpus}", file=sys.stderr)

    if arguments.dry_run:
        print("\n(dry run — no files written)")
        return 0

    corpus["entries"] = all_entries
    CORPUS_PATH.write_text(
        json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest["entries"] = all_manifest
    manifest["generated_date"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"\nWrote {CORPUS_PATH}")
    print(f"Wrote {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
