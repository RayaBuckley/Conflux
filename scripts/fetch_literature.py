"""Download local copies (HTML preferred, PDF fallback) of literature corpus papers.

Each paper's failure is isolated: a single 404 or timeout does not prevent
other papers from being fetched.  Run with ``--dry-run`` to preview
classification without downloading.

Usage::

    python scripts/fetch_literature.py                 # fetch all
    python scripts/fetch_literature.py --key agentdojo # single paper
    python scripts/fetch_literature.py --dry-run        # preview only
    python scripts/fetch_literature.py --force           # re-fetch
    python scripts/fetch_literature.py --html-only      # skip PDF fallback
    python scripts/fetch_literature.py --timeout 60     # per-request timeout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import NamedTuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "research" / "reports" / "analysis" / "literature_corpus.json"
PAPERS_DIR = ROOT / "research" / "literature" / "papers"
MANIFEST_PATH = ROOT / "research" / "literature" / "manifest.json"
MANIFEST_SCHEMA_PATH = ROOT / "schemas" / "literature-manifest.schema.json"

USER_AGENT = "Conflux-Literature-Fetcher/1.0 (research)"
ARXIV_DELAY = 3.0
MAX_REDIRECTS = 5

ARXIV_URL_RE = re.compile(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", re.IGNORECASE)
ARXIV_VERSION_RE = re.compile(r"^(.+?)(v\d+)?$")


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class FetchResult(NamedTuple):
    status: str  # "fetched" | "failed" | "skipped" | "paywall"
    local_files: list[str]
    content_hash: str
    error_message: str


class FetchError(Exception):
    """Raised when a network fetch fails."""


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------


def load_corpus() -> list[dict[str, object]]:
    """Load the literature corpus and return the entries list."""
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    entries = corpus["entries"]
    assert isinstance(entries, list)
    return entries


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify_entry(entry: dict[str, object]) -> str:
    """Classify a corpus entry by how it should be fetched."""
    source_url = str(entry.get("source_url", ""))
    if entry.get("arxiv_id") or "arxiv.org/abs/" in source_url:
        return "arxiv"
    if source_url.startswith("local:"):
        return "local"
    if "github.com" in source_url:
        return "repository"
    if source_url.startswith(("https://doi.org/", "http://doi.org/")):
        return "doi"
    if source_url.endswith(".pdf"):
        return "open_pdf"
    if source_url.startswith("http"):
        return "open_html"
    return "open_html"


def extract_arxiv_id(entry: dict[str, object]) -> str:
    """Return the arXiv ID from the ``arxiv_id`` field or the ``source_url``."""
    arxiv_id = str(entry.get("arxiv_id", ""))
    if arxiv_id:
        return arxiv_id
    source_url = str(entry.get("source_url", ""))
    match = ARXIV_URL_RE.search(source_url)
    if match:
        return match.group(1)
    raise FetchError(f"could not extract arXiv ID from {source_url}")


def strip_arxiv_version(arxiv_id: str) -> str:
    """Remove the version suffix from an arXiv ID (``2406.13352v3`` → ``2406.13352``)."""
    match = ARXIV_VERSION_RE.match(arxiv_id)
    if match and match.group(1):
        return match.group(1)
    return arxiv_id


# ---------------------------------------------------------------------------
# HTTP utilities
# ---------------------------------------------------------------------------


def fetch_url(url: str, timeout: int) -> tuple[bytes, str]:
    """Fetch *url* and return ``(content, content_type)``.

    Raises :class:`FetchError` on any failure.
    """
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            content: bytes = response.read()
            content_type = response.headers.get("Content-Type", "")
            return content, content_type
    except HTTPError as error:
        raise FetchError(f"HTTP {error.code} {error.reason}") from error
    except URLError as error:
        raise FetchError(f"URL error: {error.reason}") from error
    except TimeoutError:
        raise FetchError("timeout") from None


def validate_html(content: bytes) -> bool:
    """Check whether *content* looks like an HTML document."""
    head = content[:512].lstrip().lower()
    return b"<html" in head or b"<!doctype" in head


def validate_pdf(content: bytes) -> bool:
    """Check whether *content* starts with the PDF magic bytes."""
    return content[:5] == b"%PDF-"


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------------
# Per-category fetchers
# ---------------------------------------------------------------------------


def _existing_file(paper_dir: Path, filename: str, force: bool) -> bool:
    """Return True if the file already exists and *force* is False."""
    if force:
        return False
    return (paper_dir / filename).exists()


def fetch_arxiv(
    entry: dict[str, object],
    timeout: int,
    force: bool,
    html_only: bool,
) -> FetchResult:
    """Fetch an arXiv paper: HTML preferred, PDF fallback."""
    arxiv_id = extract_arxiv_id(entry)
    bare_id = strip_arxiv_version(arxiv_id)
    key = str(entry["key"])
    paper_dir = PAPERS_DIR / key
    paper_dir.mkdir(parents=True, exist_ok=True)

    local_files: list[str] = []
    content_hash = ""
    errors: list[str] = []

    # Attempt HTML
    html_path = paper_dir / "paper.html"
    if not _existing_file(paper_dir, "paper.html", force):
        html_url = f"https://arxiv.org/html/{bare_id}"
        try:
            content, _ = fetch_url(html_url, timeout)
            if validate_html(content):
                html_path.write_bytes(content)
                local_files.append("paper.html")
                content_hash = sha256_hex(content)
            else:
                errors.append("HTML validation failed")
        except FetchError as error:
            errors.append(f"HTML: {error}")
        time.sleep(ARXIV_DELAY)
    else:
        local_files.append("paper.html")
        content_hash = sha256_hex(html_path.read_bytes())

    # Attempt PDF (unless html-only)
    if not html_only:
        pdf_path = paper_dir / "paper.pdf"
        if not _existing_file(paper_dir, "paper.pdf", force):
            pdf_url = f"https://arxiv.org/pdf/{bare_id}"
            try:
                content, _ = fetch_url(pdf_url, timeout)
                if validate_pdf(content):
                    pdf_path.write_bytes(content)
                    local_files.append("paper.pdf")
                    if not content_hash:
                        content_hash = sha256_hex(content)
                else:
                    errors.append("PDF validation failed")
            except FetchError as error:
                errors.append(f"PDF: {error}")
            time.sleep(ARXIV_DELAY)
        else:
            local_files.append("paper.pdf")
            if not content_hash:
                content_hash = sha256_hex(pdf_path.read_bytes())

    if local_files:
        return FetchResult("fetched", local_files, content_hash, "")
    return FetchResult("failed", [], "", "; ".join(errors))


def fetch_open_pdf(
    entry: dict[str, object],
    timeout: int,
    force: bool,
) -> FetchResult:
    """Fetch a non-arXiv open-access PDF; also try an HTML variant."""
    source_url = str(entry.get("source_url", ""))
    key = str(entry["key"])
    paper_dir = PAPERS_DIR / key
    paper_dir.mkdir(parents=True, exist_ok=True)

    local_files: list[str] = []
    content_hash = ""
    errors: list[str] = []

    # Try HTML variant (replace .pdf with .html)
    html_url = source_url[:-4] + ".html" if source_url.endswith(".pdf") else ""
    if html_url:
        html_path = paper_dir / "paper.html"
        if not _existing_file(paper_dir, "paper.html", force):
            try:
                content, _ = fetch_url(html_url, timeout)
                if validate_html(content):
                    html_path.write_bytes(content)
                    local_files.append("paper.html")
                    content_hash = sha256_hex(content)
            except FetchError:
                pass  # HTML variant is best-effort

    # Fetch PDF
    pdf_path = paper_dir / "paper.pdf"
    if not _existing_file(paper_dir, "paper.pdf", force):
        try:
            content, _ = fetch_url(source_url, timeout)
            if validate_pdf(content):
                pdf_path.write_bytes(content)
                local_files.append("paper.pdf")
                if not content_hash:
                    content_hash = sha256_hex(content)
            elif validate_html(content):
                # Server returned HTML instead of PDF
                html_path = paper_dir / "paper.html"
                html_path.write_bytes(content)
                local_files.append("paper.html")
                if not content_hash:
                    content_hash = sha256_hex(content)
            else:
                errors.append("content validation failed")
        except FetchError as error:
            errors.append(str(error))
    else:
        local_files.append("paper.pdf")
        if not content_hash:
            content_hash = sha256_hex(pdf_path.read_bytes())

    if local_files:
        return FetchResult("fetched", local_files, content_hash, "")
    return FetchResult("failed", [], "", "; ".join(errors))


def fetch_open_html(
    entry: dict[str, object],
    timeout: int,
    force: bool,
) -> FetchResult:
    """Fetch an open-access HTML page (documentation site, project page)."""
    source_url = str(entry.get("source_url", ""))
    key = str(entry["key"])
    paper_dir = PAPERS_DIR / key
    paper_dir.mkdir(parents=True, exist_ok=True)

    html_path = paper_dir / "paper.html"
    if _existing_file(paper_dir, "paper.html", force):
        return FetchResult("fetched", ["paper.html"], sha256_hex(html_path.read_bytes()), "")

    try:
        content, _ = fetch_url(source_url, timeout)
        if validate_html(content) or len(content) > 100:
            html_path.write_bytes(content)
            return FetchResult("fetched", ["paper.html"], sha256_hex(content), "")
        return FetchResult("failed", [], "", "content too short or not HTML")
    except FetchError as error:
        return FetchResult("failed", [], "", str(error))


def fetch_doi(
    entry: dict[str, object],
    timeout: int,
    force: bool,
) -> FetchResult:
    """Resolve a DOI URL; fetch HTML if open-access, otherwise mark as paywall."""
    source_url = str(entry.get("source_url", ""))
    key = str(entry["key"])
    paper_dir = PAPERS_DIR / key
    paper_dir.mkdir(parents=True, exist_ok=True)

    html_path = paper_dir / "paper.html"
    if _existing_file(paper_dir, "paper.html", force):
        return FetchResult("fetched", ["paper.html"], sha256_hex(html_path.read_bytes()), "")

    try:
        content, content_type = fetch_url(source_url, timeout)
        if validate_pdf(content):
            pdf_path = paper_dir / "paper.pdf"
            pdf_path.write_bytes(content)
            return FetchResult("fetched", ["paper.pdf"], sha256_hex(content), "")
        if validate_html(content):
            html_path.write_bytes(content)
            return FetchResult("fetched", ["paper.html"], sha256_hex(content), "")
        # Could not identify content — likely a paywall landing page
        return FetchResult(
            "paywall",
            [],
            "",
            f"DOI resolved to non-open-access content (Content-Type: {content_type})",
        )
    except FetchError as error:
        return FetchResult("paywall", [], "", str(error))


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def fetch_entry(
    entry: dict[str, object],
    category: str,
    timeout: int,
    force: bool,
    html_only: bool,
) -> FetchResult:
    """Dispatch to the appropriate fetcher based on *category*."""
    if category == "local":
        return FetchResult("skipped", [], "", "local file — already in repository")
    if category == "repository":
        return FetchResult("skipped", [], "", "GitHub repository — no separate download")
    if category == "arxiv":
        return fetch_arxiv(entry, timeout, force, html_only)
    if category == "open_pdf":
        return fetch_open_pdf(entry, timeout, force)
    if category == "open_html":
        return fetch_open_html(entry, timeout, force)
    if category == "doi":
        return fetch_doi(entry, timeout, force)
    return FetchResult("skipped", [], "", f"unknown category: {category}")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_fetch_status(key: str, category: str, source_url: str, result: FetchResult) -> None:
    """Write per-paper ``fetch_status.json``."""
    paper_dir = PAPERS_DIR / key
    paper_dir.mkdir(parents=True, exist_ok=True)
    status = {
        "key": key,
        "source_category": category,
        "source_url": source_url,
        "fetch_status": result.status,
        "local_files": result.local_files,
        "content_hash": result.content_hash,
        "fetched_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "error_message": result.error_message,
    }
    (paper_dir / "fetch_status.json").write_text(
        json.dumps(status, indent=2) + "\n",
        encoding="utf-8",
    )


def update_manifest(results: list[dict[str, object]]) -> None:
    """Write the aggregate manifest."""
    manifest = {
        "schema_version": "1",
        "generated_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": results,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024}KB"
    return f"{size_bytes // (1024 * 1024)}MB"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download local copies of literature corpus papers.",
    )
    parser.add_argument("--key", help="Fetch only the paper with this corpus key.")
    parser.add_argument("--dry-run", action="store_true", help="Classify and print without downloading.")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if a local copy exists.")
    parser.add_argument("--html-only", action="store_true", help="Skip PDF fallback for arXiv papers.")
    parser.add_argument("--timeout", type=int, default=30, help="Per-request timeout in seconds (default: 30).")
    arguments = parser.parse_args()

    try:
        entries = load_corpus()
    except (OSError, json.JSONDecodeError) as error:
        print(f"Error loading corpus: {error}", file=sys.stderr)
        return 1

    if arguments.key:
        entries = [e for e in entries if str(e["key"]) == arguments.key]
        if not entries:
            print(f"No corpus entry with key '{arguments.key}'", file=sys.stderr)
            return 1

    # Classify all entries
    classified = [(entry, classify_entry(entry)) for entry in entries]

    if arguments.dry_run:
        print(f"{'Key':<30} {'Category':<12} {'Source URL'}")
        print("-" * 90)
        for entry, category in classified:
            source_url = str(entry.get("source_url", ""))[:50]
            print(f"{entry['key']!s:<30} {category:<12} {source_url}")
        print(f"\nTotal: {len(classified)} entries")
        counts: dict[str, int] = {}
        for _, category in classified:
            counts[category] = counts.get(category, 0) + 1
        for cat in sorted(counts):
            print(f"  {cat}: {counts[cat]}")
        return 0

    # Fetch
    manifest_entries: list[dict[str, object]] = []
    fetched_count = 0
    failed_count = 0
    skipped_count = 0
    paywall_count = 0

    for entry, category in classified:
        key = str(entry["key"])
        source_url = str(entry.get("source_url", ""))
        try:
            result = fetch_entry(entry, category, arguments.timeout, arguments.force, arguments.html_only)
        except Exception as error:  # isolate per-paper failures
            result = FetchResult("failed", [], "", f"unexpected error: {error}")

        write_fetch_status(key, category, source_url, result)

        # Build manifest entry
        manifest_entries.append(
            {
                "key": key,
                "source_category": category,
                "fetch_status": result.status,
                "local_files": result.local_files,
                "content_hash": result.content_hash,
                "fetched_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source_url": source_url,
                "error_message": result.error_message,
            },
        )

        # Print result line
        if result.status == "fetched":
            file_info = ""
            if result.local_files:
                first_file = PAPERS_DIR / key / result.local_files[0]
                if first_file.exists():
                    file_info = f" files={result.local_files[0]} ({_format_size(first_file.stat().st_size)})"
                else:
                    file_info = f" files={','.join(result.local_files)}"
            hash_info = f" hash={result.content_hash[:12]}..." if result.content_hash else ""
            print(f"[fetch] key={key} category={category} status=fetched{file_info}{hash_info}")
            fetched_count += 1
        elif result.status == "failed":
            print(f"[fetch] key={key} category={category} status=failed error={result.error_message}", file=sys.stderr)
            failed_count += 1
        elif result.status == "paywall":
            print(f"[fetch] key={key} category={category} status=paywall error={result.error_message}")
            paywall_count += 1
        else:
            print(f"[fetch] key={key} category={category} status=skipped")
            skipped_count += 1

    update_manifest(manifest_entries)

    print(f"\nSummary: {fetched_count} fetched, {failed_count} failed, {paywall_count} paywall, {skipped_count} skipped")

    if fetched_count > 0:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
