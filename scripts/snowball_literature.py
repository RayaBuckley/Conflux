"""Snowball the Conflux literature corpus through key-free bibliographic APIs.

Backward snowballing walks a seed's reference list; forward snowballing walks
the works that cite it.  OpenAlex (CC0) is the primary provider; Semantic
Scholar (key-free, unauthenticated) is the fallback citation graph; Crossref
supplies publisher-DOI metadata and its ``reference`` array, and the arXiv Atom
API covers arXiv-only seeds.  A provider that is rate-limited, blocked or empty
hands the direction to the next provider in ``--graph-provider`` order.  Every
raw response is cached under ``.local/snowball-cache/`` so a restart never
refetches a URL, and per-seed progress is checkpointed in
``.local/snowball-state.json`` so ``--resume`` continues where the run stopped.

The run writes three artefacts into ``research/reports/analysis/`` (the date
prefix follows ``--date``):

* ``<date>-snowball-candidates.json`` - one record per candidate with its
  provenance (seed and direction), the dedupe verdict against the corpus, a
  stream guess, and the score with its rubric.
* ``<date>-snowball-candidates.md`` - human triage: seeds snowballed per
  direction, counts, a ranked top-30 table, and the unresolved seeds.
* ``<date>-snowball-proposed-entries.json`` - schema-conformant corpus entries
  for the strongest new candidates.  This is a *proposal*: the corpus and its
  manifest are not modified (admission is a separate reviewed step).

Usage::

    python scripts/snowball_literature.py --dry-run
    python scripts/snowball_literature.py --direction both --seed-limit 5
    python scripts/snowball_literature.py --resume --direction backward
    python scripts/snowball_literature.py --keys controllednl,text2policy --direction backward
    python scripts/snowball_literature.py --date 2026-10-09 --propose-limit 30
    python scripts/snowball_literature.py --resume --render-only

``--render-only`` rebuilds the artefacts from the checkpoint without any
network call, which is how a render fix is re-applied to an existing sweep.

A seed is resolved to a work by its corpus DOI or arXiv id, by a DOI or arXiv
id found in its ``source_url``, or by a title search (OpenAlex, then the
Semantic Scholar match endpoint, then a Crossref bibliographic search).  A
title hit is accepted only when the title is near-exact and a year or an author
surname confirms the record; a seed whose corpus title differs from the
published title stays ``needs_manual_mapping`` on purpose.

The script uses no API keys.  Providers receive a polite ``mailto`` parameter
where the API supports one, and each provider is paced separately
(``--min-interval`` for OpenAlex, default 1.2; ``--s2-interval`` for Semantic
Scholar, default 1.5; Crossref and arXiv have fixed intervals).  A 429 or 5xx
response is retried with exponential backoff capped by ``--max-backoff``.  Any
429 raises that provider's pacing to ``--blocked-interval``; a 429 that asks
for more than ``--hard-block-seconds`` (default 300) is treated as a spent
budget, so the provider is paused for the rest of the run and the fallback
provider answers instead.  Raise ``--min-interval`` (five seconds worked from
this host) when the IP is behind a busy NAT.  Only metadata is stored; no paper
text is downloaded.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "research" / "reports" / "analysis" / "literature_corpus.json"
OUT_DIR = ROOT / "research" / "reports" / "analysis"
CACHE_DIR = ROOT / ".local" / "snowball-cache"
STATE_PATH = ROOT / ".local" / "snowball-state.json"
SCHEMA_PATH = ROOT / "schemas" / "literature-corpus.schema.json"

PROVIDER_OPENALEX = "openalex"  # single-work lookups: still served when the list quota is spent
PROVIDER_OPENALEX_LIST = "openalex-list"  # filter/search/pagination endpoints: metered separately
PROVIDER_CROSSREF = "crossref"
PROVIDER_ARXIV = "arxiv"
CROSSREF_TITLE_SELECT = "DOI,title,issued,type,container-title,is-referenced-by-count,author,score"

PROVIDER_S2 = "semanticscholar"

OPENALEX_API = "https://api.openalex.org"
CROSSREF_API = "https://api.crossref.org"
ARXIV_API = "http://export.arxiv.org/api/query"
S2_API = "https://api.semanticscholar.org/graph/v1"

USER_AGENT = "Conflux-Snowball/1.0 (+https://github.com/conflux; research; mailto:{mailto})"
DEFAULT_MAILTO = "conflux-snowball@users.noreply.github.com"

WORK_SELECT = ",".join(
    [
        "id",
        "doi",
        "ids",
        "title",
        "display_name",
        "publication_year",
        "publication_date",
        "cited_by_count",
        "authorships",
        "primary_location",
        "locations",
        "referenced_works",
        "type",
        "primary_topic",
    ],
)

# Scoring rubric, written down so the ranking is reproducible and auditable.
RUBRIC = (
    "score = 3 * min(distinct_seeds, 5)               # cross-seed corroboration (max 15)\n"
    "      + 2 * (both directions seen)                # reachable backwards and forwards (max 2)\n"
    "      + min(citation_count, 4000) // 400          # influence proxy (max 10)\n"
    "      + 2 * min(topical_hits, 4)                  # keyword match against Conflux lanes (max 8)\n"
    "      + year_term (3 if year >= 2024, 1 if year >= 2020, else 0)\n"
    "      - 100 if the candidate is already in the corpus (kept for audit, sinks rank)"
)


class CacheMissError(RuntimeError):
    """Raised in ``--dry-run`` mode when a URL is not already cached."""


class ProviderBlockedError(RuntimeError):
    """Raised when a provider is paused for the rest of the run after 429s."""


@dataclass
class HttpOutcome:
    """One HTTP interaction with a bibliographic API (cached on disk)."""

    url: str
    provider: str
    status: str  # "ok" | "http_error" | "network_error"
    http_status: int | None
    body: Any
    error: str
    fetched_at: str

    def to_cache(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "provider": self.provider,
            "status": self.status,
            "http_status": self.http_status,
            "error": self.error,
            "fetched_at": self.fetched_at,
            "body": self.body,
        }

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 seconds precision."""
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def cache_key(url: str) -> str:
    """Return the deterministic cache-file stem for *url*."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


class CachedHttp:
    """GET JSON documents with an on-disk cache, pacing and 429 backoff.

    The cache is the resumability contract: a URL that has been fetched once is
    never fetched again unless ``--refresh`` is passed, so a killed run loses at
    most the in-flight request.
    """

    def __init__(
        self,
        cache_dir: Path,
        *,
        timeout: int,
        refresh: bool,
        dry_run: bool,
        min_intervals: dict[str, float],
        blocked_interval: float,
        max_backoff: float,
        hard_block_seconds: float,
        retries: int,
        mailto: str,
    ) -> None:
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.refresh = refresh
        self.dry_run = dry_run
        self.min_intervals = min_intervals
        self.blocked_interval = blocked_interval
        self.max_backoff = max_backoff
        self.hard_block_seconds = hard_block_seconds
        self.retries = retries
        self.mailto = mailto
        self.user_agent = USER_AGENT.format(mailto=mailto)
        self._last_call: dict[str, float] = {}
        self._failures: dict[str, int] = {}
        self._paused: dict[str, str] = {}
        self.stats: dict[str, int] = {
            "cache_hits": 0,
            "requests": 0,
            "ok": 0,
            "http_errors": 0,
            "network_errors": 0,
            "rate_limited": 0,
            "pacing_escalations": 0,
            "endpoints_paused": 0,
        }
        if not dry_run:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- cache ---------------------------------------------------------------

    def cache_path(self, url: str) -> Path:
        """Return the cache file for *url*."""
        return self.cache_dir / f"{cache_key(url)}.json"

    def read_cache(self, url: str) -> HttpOutcome | None:
        """Return the cached outcome for *url*, or None when absent/corrupt."""
        path = self.cache_path(url)
        if not path.is_file():
            return None
        try:
            data: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or data.get("url") != url:
            return None
        return HttpOutcome(
            url=str(data.get("url")),
            provider=str(data.get("provider", "")),
            status=str(data.get("status", "network_error")),
            http_status=data.get("http_status"),
            body=data.get("body"),
            error=str(data.get("error", "")),
            fetched_at=str(data.get("fetched_at", "")),
        )

    def write_cache(self, outcome: HttpOutcome) -> None:
        """Persist *outcome* (atomically) so a later run reuses it."""
        path = self.cache_path(outcome.url)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(outcome.to_cache(), indent=1, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    # -- network -------------------------------------------------------------

    def _pace(self, provider: str) -> None:
        interval = self.min_intervals.get(provider, 1.0)
        previous = self._last_call.get(provider)
        now = time.monotonic()
        if previous is not None and now - previous < interval:
            time.sleep(interval - (now - previous))
        self._last_call[provider] = time.monotonic()

    def _hard_block(self, provider: str, outcome: HttpOutcome) -> bool:
        """Pause *provider* for the run when it reports a long rate-limit window.

        A 429 that asks for hours of silence means the IP budget is spent, not
        that the next second will be busy; retrying it wastes the run, so the
        endpoint is parked and the caller falls back to another provider.
        """
        if outcome.status != "http_error" or outcome.http_status != 429:
            return False
        retry_after = self._retry_after_seconds(outcome)
        if retry_after is None or retry_after <= self.hard_block_seconds:
            return False
        self._paused[provider] = f"HTTP 429 with Retry-After {retry_after:.0f}s"
        self.stats["endpoints_paused"] += 1
        print(
            f"[snowball] {provider} paused for this run: rate-limited with Retry-After {retry_after:.0f}s",
            flush=True,
        )
        return True

    def _escalate(self, provider: str) -> None:
        """Raise the provider's pacing to ``blocked_interval`` after a 429.

        A shared IP budget answers a burst with 429s; long-lived runs recover by
        asking for less per second instead of hammering the API.
        """
        if self.min_intervals.get(provider, 0.0) >= self.blocked_interval:
            return
        self.min_intervals[provider] = self.blocked_interval
        self.stats["pacing_escalations"] += 1
        print(
            f"[snowball] {provider} pacing raised to {self.blocked_interval:.1f}s after a rate-limit response",
            flush=True,
        )

    def _backoff(self, provider: str, outcome: HttpOutcome, attempt: int) -> float:
        retry_after = None
        if outcome.http_status == 429:
            self.stats["rate_limited"] += 1
            self._escalate(provider)
            retry_after = self._retry_after_seconds(outcome)
        if retry_after is not None:
            return min(float(retry_after), self.max_backoff)
        return min(float(5 * (2**attempt)), self.max_backoff)

    @staticmethod
    def _retry_after_seconds(outcome: HttpOutcome) -> float | None:
        raw = str((outcome.body or {}).get("__retry_after__", "")) if isinstance(outcome.body, dict) else ""
        if not raw:
            return None
        try:
            return max(float(raw), 0.0)
        except ValueError:
            return None

    def _raw_get(self, url: str, provider: str) -> HttpOutcome:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
        )
        self.stats["requests"] += 1
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
                return HttpOutcome(url, provider, "ok", response.status, body, "", utc_now())
        except urllib.error.HTTPError as error:
            detail = ""
            retry_after = error.headers.get("Retry-After") if error.headers else None
            try:
                payload = json.loads(error.read().decode("utf-8"))
                if isinstance(payload, dict):
                    detail = str(payload.get("error", ""))[:300]
            except Exception:
                detail = ""
            retry_body: Any = {"__retry_after__": str(retry_after)} if retry_after else None
            return HttpOutcome(url, provider, "http_error", error.code, retry_body, detail or str(error.reason), utc_now())
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            return HttpOutcome(url, provider, "network_error", None, None, repr(error)[:300], utc_now())

    def get_json(self, url: str, provider: str) -> HttpOutcome:
        """Return the outcome for *url*, using the cache unless refreshing.

        Raises :class:`CacheMissError` in dry-run mode when *url* is not cached
        and :class:`ProviderBlockedError` when *provider* is paused for the run.
        """
        cached = self.read_cache(url)
        if cached is not None and not self.refresh:
            self.stats["cache_hits"] += 1
            return cached
        if self.dry_run:
            raise CacheMissError(url)
        pause = self._paused.get(provider)
        if pause is not None:
            raise ProviderBlockedError(f"{provider} paused for this run: {pause}")
        outcome = self._raw_get(url, provider)
        blocked = self._hard_block(provider, outcome)
        for attempt in range(0 if blocked else self.retries):
            if outcome.ok:
                break
            if outcome.status != "http_error" or outcome.http_status not in (429, 500, 502, 503, 504):
                break
            wait = self._backoff(provider, outcome, attempt)
            print(
                f"[snowball] {provider} HTTP {outcome.http_status} on {url.split('?', maxsplit=1)[0]}; "
                f"backing off {wait:.0f}s (attempt {attempt + 1}/{self.retries})",
                flush=True,
            )
            time.sleep(wait)
            self._pace(provider)
            outcome = self._raw_get(url, provider)
        if outcome.status == "http_error":
            self.stats["http_errors"] += 1
            if outcome.http_status == 429:
                self._failures[provider] = self._failures.get(provider, 0) + 1
                if self._failures[provider] >= 3:
                    self._paused[provider] = (
                        f"{self._failures[provider]} consecutive 429 responses; re-run with --resume later"
                    )
                    print(f"[snowball] {provider} paused for the rest of the run: {self._paused[provider]}", flush=True)
        elif outcome.status == "network_error":
            self.stats["network_errors"] += 1
        else:
            self.stats["ok"] += 1
            self._failures[provider] = 0
        self.write_cache(outcome)
        return outcome

    @property
    def paused_providers(self) -> dict[str, str]:
        """Return the paused providers with their reason."""
        return dict(self._paused)


def api_url(path: str, params: dict[str, str] | None = None, *, mailto: str = "") -> str:
    """Build an API URL with deterministic parameter order."""
    query = dict(params or {})
    if mailto:
        query["mailto"] = mailto
    if not query:
        return path
    return f"{path}?{urllib.parse.urlencode(sorted(query.items()))}"


def strip_openalex_id(value: Any) -> str:
    """Return the bare OpenAlex identifier (``https://openalex.org/W1`` -> ``W1``)."""
    return str(value or "").rsplit("/", 1)[-1]


def normalise_doi(value: Any) -> str:
    """Return a lower-case bare DOI, or an empty string."""
    doi = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        doi = doi.removeprefix(prefix)
    return doi


def normalise_arxiv(value: Any) -> str:
    """Return a bare arXiv identifier (version suffix stripped)."""
    arxiv = str(value or "").strip().lower()
    arxiv = re.sub(r"^https?://arxiv\.org/(abs|pdf)/", "", arxiv)
    arxiv = re.sub(r"\.pdf$", "", arxiv)
    return re.sub(r"v\d+$", "", arxiv)


def normalise_title(value: Any) -> str:
    """Return a comparison key for a title (lower-case, alphanumeric words)."""
    text = re.sub(r"[^0-9a-z]+", " ", str(value or "").lower())
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Corpus, seeds and dedupe
# ---------------------------------------------------------------------------


@dataclass
class Seed:
    """One corpus entry chosen for snowballing."""

    key: str
    title: str
    year: int | None
    doi: str
    arxiv_id: str
    source_url: str
    stream: str
    priority: str
    verified_method: str
    snowball_backward: str
    snowball_forward: str
    authors: tuple[str, ...] = ()


PRIORITY_RANK = {"A": 0, "B": 1, "C": 2, "D": 3, "": 4}
UNVERIFIED_METHOD = "unverified"


def load_corpus() -> dict[str, Any]:
    """Load the literature corpus document."""
    corpus: dict[str, Any] = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    return corpus


def build_seed(entry: dict[str, Any]) -> Seed:
    """Convert a corpus entry into a :class:`Seed`."""
    verified = entry.get("verified") or {}
    snowball = entry.get("snowball_status") or {}
    source_url = str(entry.get("source_url", ""))
    return Seed(
        key=str(entry.get("key", "")),
        title=str(entry.get("title", "")),
        year=entry.get("year") if isinstance(entry.get("year"), int) else None,
        doi=normalise_doi(entry.get("doi")) or extract_doi(source_url),
        arxiv_id=normalise_arxiv(entry.get("arxiv_id")) or extract_arxiv(source_url),
        source_url=source_url,
        stream=str(entry.get("stream", "")),
        priority=str(entry.get("adoption_priority", "")),
        verified_method=str(verified.get("method", "")),
        snowball_backward=str(snowball.get("backward", "")),
        snowball_forward=str(snowball.get("forward", "")),
        authors=tuple(str(author) for author in (entry.get("authors") or []) if str(author).strip()),
    )


def select_seeds(
    entries: list[dict[str, Any]],
    *,
    only_keys: set[str] | None = None,
    seed_limit: int | None = None,
) -> list[Seed]:
    """Return the seed queue in deterministic order.

    A seed is included when it is an adoption-priority A/B entry whose backward
    snowball is still ``pending``, or when its ``verified.method`` is
    ``unverified`` (the corpus' own "next papers to research" signal).  Order is
    priority tier then key, so ``--seed-limit`` always cuts the same queue.
    """
    selected: list[Seed] = []
    for entry in entries:
        seed = build_seed(entry)
        pending_ab = seed.priority in ("A", "B") and seed.snowball_backward == "pending"
        unverified = seed.verified_method == UNVERIFIED_METHOD
        if not (pending_ab or unverified):
            continue
        if only_keys is not None and seed.key not in only_keys:
            continue
        selected.append(seed)
    selected.sort(key=lambda item: (PRIORITY_RANK.get(item.priority, 4), item.key))
    if seed_limit is not None:
        selected = selected[:seed_limit]
    return selected


class CorpusIndex:
    """DOI / arXiv / title index over the existing corpus entries."""

    def __init__(self, entries: list[dict[str, Any]]) -> None:
        self.dois: dict[str, str] = {}
        self.arxivs: dict[str, str] = {}
        self.titles: dict[str, str] = {}
        self.title_keys: list[tuple[str, str]] = []
        for entry in entries:
            key = str(entry.get("key", ""))
            doi = normalise_doi(entry.get("doi"))
            if doi:
                self.dois.setdefault(doi, key)
            arxiv = normalise_arxiv(entry.get("arxiv_id"))
            if not arxiv:
                match = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+)", str(entry.get("source_url", "")))
                if match:
                    arxiv = normalise_arxiv(match.group(1))
            if arxiv:
                self.arxivs.setdefault(arxiv, key)
            title = normalise_title(entry.get("title"))
            if title:
                self.titles.setdefault(title, key)
                self.title_keys.append((title, key))

    def match(self, *, doi: str, arxiv_id: str, title: str) -> tuple[str, str, str]:
        """Return ``(verdict, matched_key, match_type)`` for a candidate identity."""
        if doi and doi in self.dois:
            return "existing", self.dois[doi], "doi"
        if arxiv_id and arxiv_id in self.arxivs:
            return "existing", self.arxivs[arxiv_id], "arxiv"
        normalised = normalise_title(title)
        if normalised and normalised in self.titles:
            return "existing", self.titles[normalised], "title"
        if normalised:
            best_key = ""
            best_ratio = 0.0
            for corpus_title, key in self.title_keys:
                if abs(len(corpus_title) - len(normalised)) > 30:
                    continue
                ratio = difflib.SequenceMatcher(None, normalised, corpus_title).ratio()
                if ratio > best_ratio:
                    best_ratio, best_key = ratio, key
            if best_ratio >= 0.93:
                return "possible_duplicate", best_key, "title_similarity"
        return "new", "", ""


# ---------------------------------------------------------------------------
# Candidate records
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    """One snowballed work, merged across the seeds and directions that found it."""

    id: str
    openalex_id: str = ""
    doi: str = ""
    arxiv_id: str = ""
    title: str = ""
    year: int | None = None
    venue: str = ""
    authors: list[str] = field(default_factory=list)
    citation_count: int | None = None
    source: str = ""
    primary_topic: str = ""
    type: str = ""
    surfaced_by: list[dict[str, str]] = field(default_factory=list)
    dedupe_verdict: str = "new"
    dedupe_key: str = ""
    dedupe_match: str = ""
    stream_guess: str = ""
    stream_hits: list[str] = field(default_factory=list)
    score: int = 0
    score_components: dict[str, int] = field(default_factory=dict)

    def identity(self) -> str:
        """Return the stable identity string for this candidate."""
        if self.doi:
            return f"doi:{self.doi}"
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id}"
        if self.openalex_id:
            return f"openalex:{self.openalex_id}"
        return f"title:{normalise_title(self.title)}"

    def to_json(self) -> dict[str, Any]:
        """Return the serialisable candidate record."""
        return {
            "id": self.id,
            "openalex_id": self.openalex_id,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "year": self.year,
            "venue": self.venue,
            "authors": self.authors,
            "citation_count": self.citation_count,
            "source": self.source,
            "primary_topic": self.primary_topic,
            "surfaced_by": self.surfaced_by,
            "dedupe": {
                "verdict": self.dedupe_verdict,
                "matched_key": self.dedupe_key,
                "match_type": self.dedupe_match,
            },
            "stream_guess": self.stream_guess,
            "stream_hits": self.stream_hits,
            "score": self.score,
            "score_components": self.score_components,
        }


def _authorship_names(work: dict[str, Any], limit: int = 12) -> list[str]:
    names: list[str] = []
    for authorship in work.get("authorships") or []:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author") or {}
        name = str(author.get("display_name", "")).strip()
        if name:
            names.append(name)
        if len(names) >= limit:
            break
    return names


def _primary_venue(work: dict[str, Any]) -> str:
    location = work.get("primary_location") or {}
    source = (location.get("source") or {}) if isinstance(location, dict) else {}
    return str(source.get("display_name", "") or "").strip()


def _arxiv_from_locations(work: dict[str, Any]) -> str:
    for location in work.get("locations") or []:
        if not isinstance(location, dict):
            continue
        landing = str(location.get("landing_page_url", ""))
        match = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+)", landing)
        if match:
            return normalise_arxiv(match.group(1))
    doi = normalise_doi(work.get("doi"))
    if doi.startswith("10.48550/arxiv."):
        return normalise_arxiv(doi.removeprefix("10.48550/arxiv."))
    return ""


def candidate_from_openalex(work: dict[str, Any], *, source: str = PROVIDER_OPENALEX) -> Candidate | None:
    """Build a :class:`Candidate` from an OpenAlex work object."""
    if not isinstance(work, dict):
        return None
    title = str(work.get("display_name") or work.get("title") or "").strip()
    if not title:
        return None
    doi = normalise_doi(work.get("doi"))
    arxiv = _arxiv_from_locations(work)
    openalex_id = strip_openalex_id(work.get("id"))
    topic = ""
    primary_topic = work.get("primary_topic")
    if isinstance(primary_topic, dict):
        topic = str(primary_topic.get("display_name", ""))
    citation_count = work.get("cited_by_count")
    year = work.get("publication_year")
    candidate = Candidate(
        id="",
        openalex_id=openalex_id,
        doi=doi,
        arxiv_id=arxiv,
        title=title,
        year=year if isinstance(year, int) else None,
        venue=_primary_venue(work),
        authors=_authorship_names(work),
        citation_count=citation_count if isinstance(citation_count, int) else None,
        source=source,
        primary_topic=topic,
        type=str(work.get("type", "")),
    )
    candidate.id = candidate.identity()
    return candidate


def candidate_from_crossref(item: dict[str, Any]) -> Candidate | None:
    """Build a :class:`Candidate` from a Crossref ``message`` object."""
    if not isinstance(item, dict):
        return None
    titles = item.get("title") or []
    title = str(titles[0]).strip() if isinstance(titles, list) and titles else ""
    if not title:
        return None
    year: int | None = None
    issued = (item.get("issued") or {}).get("date-parts") or []
    if issued and isinstance(issued[0], list) and issued[0]:
        first = issued[0][0]
        year = first if isinstance(first, int) else None
    container = item.get("container-title") or []
    venue = str(container[0]) if isinstance(container, list) and container else ""
    authors = []
    for authorship in item.get("author") or []:
        given = str(authorship.get("given", "")).strip()
        family = str(authorship.get("family", "")).strip()
        name = " ".join(part for part in (given, family) if part)
        if name:
            authors.append(name)
    doi = normalise_doi(item.get("DOI"))
    citation_count = item.get("is-referenced-by-count")
    candidate = Candidate(
        id="",
        doi=doi,
        title=title,
        year=year,
        venue=venue,
        authors=authors[:12],
        citation_count=citation_count if isinstance(citation_count, int) else None,
        source=PROVIDER_CROSSREF,
    )
    candidate.id = candidate.identity()
    return candidate


# ---------------------------------------------------------------------------
# Stream guess and scoring
# ---------------------------------------------------------------------------

STREAM_KEYWORDS: dict[str, tuple[str, ...]] = {
    "LLM agent security": (
        "llm",
        "language model",
        "agent",
        "prompt injection",
        "tool use",
        "tool call",
        "guardrail",
        "jailbreak",
        "instruction",
    ),
    "Information flow control": (
        "information flow",
        "noninterference",
        "non-interference",
        "taint",
        "declassification",
        "confidentiality",
        "ifc",
        "flow-limited",
        "label",
    ),
    "Integrity models": ("integrity", "biba", "low-water-mark", "endorsement", "trustworthiness"),
    "Access control": (
        "access control",
        "rbac",
        "abac",
        "capability",
        "permission",
        "authorization",
        "authorisation",
        "usage control",
        "privilege",
    ),
    "Delegation and authority": ("delegation", "authority", "trust management", "certificate", "credential"),
    "Provenance and attribution": ("provenance", "causal", "attribution", "lineage", "history", "audit"),
    "Verification and synthesis": (
        "model checking",
        "verification",
        "symbolic",
        "abstract interpretation",
        "synthesis",
        "solver",
        "satisfiability",
        "sat",
        "smt",
        "hyperproperty",
        "temporal logic",
    ),
    "Runtime enforcement": ("monitor", "enforcement", "runtime", "policy engine", "interpreter", "sandbox"),
    "Multi-agent systems": ("multi-agent", "multiagent", "coalition", "protocol", "interoperability"),
    "Policy languages and analysis": (
        "policy language",
        "policy specification",
        "conflict",
        "policy analysis",
        "refinement",
        "natural language",
        "requirements",
    ),
    "Systems security": ("kernel", "operating system", "memory", "file system", "microkernel", "process", "cloud"),
}

STREAM_SEARCH_TEXT_FIELDS = ("title", "primary_topic", "venue")


def guess_stream(candidate: Candidate, seed_streams: list[str]) -> tuple[str, list[str]]:
    """Return ``(lane, matched_keywords)`` for a candidate.

    The keyword lanes win first; when nothing matches, the lane most common
    among the surfacing seeds is inherited, then the candidate's OpenAlex topic.
    """
    text = " ".join(
        [candidate.title, candidate.primary_topic, candidate.venue, candidate.type],
    ).lower()
    best_lane = ""
    best_hits: list[str] = []
    for lane, keywords in STREAM_KEYWORDS.items():
        hits = [keyword for keyword in keywords if keyword in text]
        if len(hits) > len(best_hits) or (len(hits) == len(best_hits) and hits and lane < best_lane):
            best_lane, best_hits = lane, hits
    if best_hits:
        return best_lane, sorted(best_hits)
    seed_lanes = [stream for stream in seed_streams if stream]
    if seed_lanes:
        most_common = sorted({(seed_lanes.count(stream), stream) for stream in seed_lanes})[-1][1]
        return most_common, []
    return candidate.primary_topic, []


def score_candidate(candidate: Candidate, *, distinct_seeds: int, directions: set[str]) -> None:
    """Fill ``score`` and ``score_components`` using the documented rubric."""
    corroboration = 3 * min(distinct_seeds, 5)
    both_directions = 2 if {"backward", "forward"} <= directions else 0
    influence = min(candidate.citation_count or 0, 4000) // 400
    topical = 2 * min(len(candidate.stream_hits), 4)
    if candidate.year is not None and candidate.year >= 2024:
        year_term = 3
    elif candidate.year is not None and candidate.year >= 2020:
        year_term = 1
    else:
        year_term = 0
    penalty = -100 if candidate.dedupe_verdict == "existing" else 0
    candidate.score_components = {
        "corroboration": corroboration,
        "both_directions": both_directions,
        "influence": influence,
        "topical": topical,
        "year": year_term,
        "already_in_corpus": penalty,
    }
    candidate.score = sum(candidate.score_components.values())


# ---------------------------------------------------------------------------
# Seed resolution
# ---------------------------------------------------------------------------

DOI_URL_RE = re.compile(r'''10\.\d{4,9}/[^\s"'<>]+''')
ARXIV_URL_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+)")


def extract_doi(text: str) -> str:
    """Return the first DOI-looking token in *text* (empty string when absent)."""
    match = DOI_URL_RE.search(urllib.parse.unquote(text))
    return normalise_doi(match.group(0)) if match else ""


def extract_arxiv(text: str) -> str:
    """Return the first arXiv identifier in *text* (empty string when absent)."""
    match = ARXIV_URL_RE.search(text)
    return normalise_arxiv(match.group(1)) if match else ""


@dataclass
class Resolution:
    """How a seed was mapped onto an API identity."""

    status: str  # "resolved" | "metadata_only" | "needs_manual_mapping"
    identity: str
    method: str
    openalex_id: str = ""
    doi: str = ""
    work: dict[str, Any] | None = None
    work_provider: str = ""
    s2_ids: list[str] = field(default_factory=list)
    title: str = ""
    year: int | None = None
    notes: str = ""


def openalex_work_by_doi_url(doi: str, mailto: str) -> str:
    """Return the OpenAlex single-work URL for a DOI."""
    return api_url(f"{OPENALEX_API}/works/doi:{urllib.parse.quote(doi, safe='/')}", {"select": WORK_SELECT}, mailto=mailto)


def openalex_title_search_url(title: str, mailto: str, per_page: int = 5) -> str:
    """Return the OpenAlex title-search URL for *title*."""
    return api_url(
        f"{OPENALEX_API}/works",
        {"filter": f"title.search:{title}", "per-page": str(per_page), "select": WORK_SELECT},
        mailto=mailto,
    )


def openalex_batch_url(work_ids: list[str], mailto: str) -> str:
    """Return the OpenAlex batch URL for up to 50 work identifiers."""
    return api_url(
        f"{OPENALEX_API}/works",
        {
            "filter": "openalex_id:" + "|".join(strip_openalex_id(work_id) for work_id in work_ids),
            "per-page": "50",
            "select": WORK_SELECT,
        },
        mailto=mailto,
    )


def openalex_citing_url(work_id: str, cursor: str, mailto: str, per_page: int = 50) -> str:
    """Return the OpenAlex forward-citation URL for *work_id*."""
    return api_url(
        f"{OPENALEX_API}/works",
        {"filter": f"cites:{strip_openalex_id(work_id)}", "per-page": str(per_page), "cursor": cursor, "select": WORK_SELECT},
        mailto=mailto,
    )


def crossref_work_url(doi: str) -> str:
    """Return the Crossref single-work URL for a DOI."""
    return f"{CROSSREF_API}/works/{urllib.parse.quote(doi, safe='/')}"


def arxiv_metadata_url(arxiv_id: str) -> str:
    """Return the arXiv Atom metadata URL for an identifier list."""
    return api_url(ARXIV_API, {"id_list": arxiv_id})


def title_ratio(seed_title: str, candidate_title: str, seed_year: int | None, candidate_year: Any) -> float:
    """Return a title-similarity score, down-weighted on a year mismatch."""
    target = normalise_title(seed_title)
    other = normalise_title(candidate_title)
    if not target or not other:
        return 0.0
    ratio = 1.0 if target == other else difflib.SequenceMatcher(None, target, other).ratio()
    if seed_year is not None and isinstance(candidate_year, int) and abs(candidate_year - seed_year) > 2:
        ratio -= 0.2
    return ratio


def title_search_matches(
    seed_title: str,
    seed_year: int | None,
    results: list[dict[str, Any]],
    *,
    threshold: float = 0.93,
) -> tuple[dict[str, Any] | None, str]:
    """Pick the best title-search hit, or return None with the rejection reason."""
    best: dict[str, Any] | None = None
    best_ratio = 0.0
    for work in results:
        ratio = title_ratio(seed_title, str(work.get("display_name") or work.get("title") or ""), seed_year, work.get("publication_year"))
        if ratio > best_ratio:
            best_ratio, best = ratio, work
    if best is None or best_ratio < threshold:
        return None, f"no title-search hit above {threshold:.2f} (best {best_ratio:.2f})"
    return best, ""


def openalex_resolution(
    work: dict[str, Any],
    *,
    identity: str,
    method: str,
    notes: str,
    title_hint: str,
    year: int | None,
    doi: str = "",
) -> Resolution:
    """Return a resolved seed backed by an OpenAlex work object."""
    work_year = work.get("publication_year")
    return Resolution(
        status="resolved",
        identity=identity,
        method=method,
        openalex_id=strip_openalex_id(work.get("id")),
        doi=doi or normalise_doi(work.get("doi")),
        work=work,
        work_provider=PROVIDER_OPENALEX,
        s2_ids=s2_identifiers_from_openalex(work, doi or normalise_doi(work.get("doi"))),
        title=str(work.get("display_name") or title_hint),
        year=work_year if isinstance(work_year, int) else year,
        notes=notes,
    )


def openalex_title_resolution(
    client: CachedHttp,
    title: str,
    year: int | None,
    mailto: str,
) -> tuple[Resolution | None, str]:
    """Resolve *title* through the OpenAlex title search, returning a reason on failure."""
    try:
        outcome = client.get_json(openalex_title_search_url(title, mailto), PROVIDER_OPENALEX_LIST)
    except (ProviderBlockedError, CacheMissError) as error:
        return None, f"OpenAlex title search unavailable ({error})"
    if not outcome.ok or not isinstance(outcome.body, dict):
        return None, f"OpenAlex title search {outcome.status} {outcome.http_status}"
    results = [item for item in outcome.body.get("results") or [] if isinstance(item, dict)]
    hit, reason = title_search_matches(title, year, results)
    if hit is None:
        return None, reason
    work_id = strip_openalex_id(hit.get("id"))
    is_doi_less = "doi:" not in title
    return (
        Resolution(
            status="resolved",
            identity=f"openalex:{work_id}" if is_doi_less else f"doi:{normalise_doi(hit.get('doi'))}",
            method="openalex-title",
            openalex_id=work_id,
            work=hit,
            work_provider=PROVIDER_OPENALEX,
            s2_ids=s2_identifiers_from_openalex(hit, normalise_doi(hit.get("doi"))),
            title=str(hit.get("display_name") or title),
            year=hit.get("publication_year") if isinstance(hit.get("publication_year"), int) else year,
            notes="OpenAlex title search",
        ),
        "",
    )


def s2_resolution(
    paper: dict[str, Any],
    *,
    identity: str,
    method: str,
    notes: str,
    title_hint: str,
    year: int | None,
) -> Resolution:
    """Return a resolved seed backed by a Semantic Scholar paper object."""
    external = paper.get("externalIds") or {}
    paper_year = paper.get("year")
    identifiers = s2_identifiers_from_paper(paper)
    return Resolution(
        status="resolved",
        identity=identity,
        method=method,
        openalex_id=strip_openalex_id(external.get("OpenAlex")),
        doi=normalise_doi(external.get("DOI")),
        work=paper,
        work_provider=PROVIDER_S2,
        s2_ids=identifiers,
        title=str(paper.get("title") or title_hint),
        year=paper_year if isinstance(paper_year, int) else year,
        notes=notes,
    )


def s2_resolution_by_identifier(
    client: CachedHttp,
    identifier: str,
    *,
    identity: str,
    method: str,
    title_hint: str,
    year: int | None,
    notes: str,
) -> Resolution | None:
    """Resolve a seed through a Semantic Scholar identifier, or return None."""
    try:
        outcome = client.get_json(s2_paper_url(identifier), PROVIDER_S2)
    except (ProviderBlockedError, CacheMissError):
        return None
    if not outcome.ok or not isinstance(outcome.body, dict):
        return None
    return s2_resolution(outcome.body, identity=identity, method=method, notes=notes, title_hint=title_hint, year=year)


def s2_resolution_by_title(client: CachedHttp, title: str, year: int | None) -> tuple[Resolution | None, str]:
    """Resolve a seed through the Semantic Scholar title-match endpoint.

    Returns the resolution, or ``(None, reason)`` so the caller can record why
    the fallback did not fire.
    """
    try:
        outcome = client.get_json(s2_match_url(title), PROVIDER_S2)
    except (ProviderBlockedError, CacheMissError) as error:
        return None, f"Semantic Scholar match unavailable ({error})"
    if not outcome.ok or not isinstance(outcome.body, dict):
        return None, f"Semantic Scholar match {outcome.status} {outcome.http_status}"
    rows = [item for item in outcome.body.get("data") or [] if isinstance(item, dict)]
    if not rows:
        return None, "no Semantic Scholar title-match hit"
    paper = rows[0]
    ratio = title_ratio(title, str(paper.get("title") or ""), year, paper.get("year"))
    if ratio < 0.93:
        return None, f"Semantic Scholar title match below 0.93 (best {ratio:.2f})"
    external = paper.get("externalIds") or {}
    doi = normalise_doi(external.get("DOI"))
    arxiv = normalise_arxiv(external.get("ArXiv"))
    if doi:
        identity = f"doi:{doi}"
    elif arxiv:
        identity = f"arxiv:{arxiv}"
    elif paper.get("paperId"):
        identity = f"openalex:{paper['paperId']}"
    else:
        identity = ""
    return (
        s2_resolution(
            paper,
            identity=identity,
            method="s2-title-match",
            notes=f"Semantic Scholar title match (similarity {ratio:.2f})",
            title_hint=title,
            year=year,
        ),
        "",
    )


def crossref_title_resolution(
    client: CachedHttp,
    title: str,
    year: int | None,
    *,
    authors: Iterable[str] = (),
    threshold: float = 0.85,
) -> tuple[Resolution | None, str]:
    """Resolve an identifier-less seed through the Crossref bibliographic search.

    Crossref has no rate-limit wall on this host, so it is the last-resort title
    lookup when the OpenAlex title search is blocked and the Semantic Scholar
    match misses.  A hit is accepted only when its title reaches ``threshold``
    and the record is confirmed either by an agreeing year or by an overlapping
    author surname, because Crossref sometimes omits ``issued``.  The similarity
    and the confirmation are recorded so a reviewer can check the mapping.
    """
    best: dict[str, Any] | None = None
    best_ratio = 0.0
    best_confirm = ""
    unconfirmed_ratio = 0.0
    seed_surnames = author_surnames(authors)
    for variant in title_variants(title):
        try:
            outcome = client.get_json(crossref_title_search_url(variant), PROVIDER_CROSSREF)
        except (ProviderBlockedError, CacheMissError) as error:
            return None, f"Crossref title search unavailable ({error})"
        if not outcome.ok or not isinstance(outcome.body, dict):
            return None, f"Crossref title search {outcome.status} {outcome.http_status}"
        message = outcome.body.get("message") or {}
        items = [item for item in message.get("items") or [] if isinstance(item, dict)]
        if not items:
            continue
        for item in items:
            if item.get("type") == "component" or not item.get("DOI"):
                continue
            titles = item.get("title") or [""]
            item_year = crossref_item_year(item)
            ratio = title_ratio(variant, str(titles[0]), year, item_year)
            if ratio < threshold:
                continue
            confirmed = ""
            if year is not None and item_year is not None and abs(item_year - year) <= 2:
                confirmed = f"year agreement ({item_year})"
            else:
                overlap = seed_surnames & crossref_item_surnames(item)
                if overlap:
                    confirmed = f"author overlap ({', '.join(sorted(overlap))})"
            if not confirmed:
                unconfirmed_ratio = max(unconfirmed_ratio, ratio)
                continue
            if ratio > best_ratio:
                best_ratio, best, best_confirm = ratio, item, confirmed
        if best is not None:
            break
    if best is None:
        if unconfirmed_ratio:
            return None, (
                f"Crossref title-search hit at {unconfirmed_ratio:.2f} is unconfirmed "
                "(no year agreement and no author overlap)"
            )
        return None, f"no Crossref title-search hit above {threshold:.2f}"
    doi = normalise_doi(best.get("DOI"))
    titles = best.get("title") or [""]
    return (
        Resolution(
            status="resolved",
            identity=f"doi:{doi}",
            method="crossref-title-search",
            doi=doi,
            work=None,
            work_provider=PROVIDER_CROSSREF,
            s2_ids=[f"DOI:{doi}"],
            title=str(titles[0] or title),
            year=crossref_item_year(best) or year,
            notes=(
                "no DOI/arXiv in the corpus entry; resolved by a Crossref bibliographic search "
                f"(title similarity {best_ratio:.2f}, {best_confirm})"
            ),
        ),
        "",
    )


def resolve_seed(client: CachedHttp, seed: Seed, mailto: str, *, providers: list[str] | None = None) -> Resolution:
    """Map a corpus seed onto a work record from the first provider that answers.

    Identity order: corpus DOI, then arXiv id, then a DOI/arXiv extracted from
    ``source_url``, then a title search.  Each identity is offered to the
    providers in ``providers`` order, so an exhausted OpenAlex list quota hands
    the work to Semantic Scholar instead of dropping the seed.
    """
    plan = providers if providers is not None else [PROVIDER_OPENALEX, PROVIDER_S2]
    doi = seed.doi or extract_doi(seed.source_url)
    arxiv = seed.arxiv_id or extract_arxiv(seed.source_url)
    title_hint = seed.title
    attempts: list[str] = []
    use_openalex = PROVIDER_OPENALEX in plan
    use_s2 = PROVIDER_S2 in plan

    if doi:
        if use_openalex:
            outcome = client.get_json(openalex_work_by_doi_url(doi, mailto), PROVIDER_OPENALEX)
            if outcome.ok and isinstance(outcome.body, dict):
                return openalex_resolution(
                    outcome.body, identity=f"doi:{doi}", method="openalex-doi",
                    notes="OpenAlex DOI lookup", title_hint=title_hint, year=seed.year, doi=doi,
                )
            attempts.append(f"openalex-doi {outcome.status} {outcome.http_status}".strip())
        if use_s2:
            s2 = s2_resolution_by_identifier(
                client, f"DOI:{doi}", identity=f"doi:{doi}", method="s2-doi",
                title_hint=title_hint, year=seed.year,
                notes="Semantic Scholar DOI lookup (OpenAlex DOI lookup unavailable)",
            )
            if s2 is not None:
                return s2
            attempts.append("s2-doi miss")
        crossref = client.get_json(crossref_work_url(doi), PROVIDER_CROSSREF)
        crossref_message = (crossref.body or {}).get("message") if crossref.ok and isinstance(crossref.body, dict) else None
        if isinstance(crossref_message, dict):
            crossref_title = ""
            titles = crossref_message.get("title") or []
            if isinstance(titles, list) and titles:
                crossref_title = str(titles[0])
            search_title = crossref_title or title_hint
            if use_openalex:
                hit, reason = openalex_title_resolution(client, search_title, seed.year, mailto)
                if hit is not None and seed.doi:
                    hit.identity = f"doi:{doi}"
                    hit.method = "openalex-title-via-crossref"
                    hit.notes = "OpenAlex DOI lookup failed; resolved through the Crossref title"
                    return hit
                if hit is not None:
                    return hit
                attempts.append(f"openalex-title {reason}")
            if use_s2:
                match, match_reason = s2_resolution_by_title(client, search_title, seed.year)
                if match is not None:
                    match.identity = f"doi:{doi}"
                    match.method = "s2-title-via-crossref"
                    match.notes = "OpenAlex DOI lookup failed; resolved through the Crossref title and a Semantic Scholar match"
                    return match
                attempts.append(match_reason)
            return Resolution(
                status="metadata_only",
                identity=f"doi:{doi}",
                method="crossref",
                doi=doi,
                title=crossref_title or title_hint,
                year=crossref_item_year(crossref_message) or seed.year,
                notes=f"Crossref metadata only; citation graph unavailable ({'; '.join(attempts) or 'no provider'})",
            )
        # A DOI that no provider knows still deserves a title search before the
        # seed is declared unmappable, but only a near-exact title hit is taken.
        mapped, mapped_reason = crossref_title_resolution(client, title_hint, seed.year, authors=seed.authors)
        if mapped is not None:
            mapped.notes = f"corpus DOI {doi} is unresolved; {mapped.notes}"
            return mapped
        attempts.append(mapped_reason)
        return Resolution(
            status="needs_manual_mapping",
            identity=f"doi:{doi}",
            method="",
            doi=doi,
            title=title_hint,
            year=seed.year,
            notes=(
                f"DOI {doi} unresolved ({'; '.join(attempts) or 'no provider tried'}); "
                f"Crossref says {crossref.status} {crossref.http_status}"
            ),
        )

    if arxiv:
        if use_openalex:
            outcome = client.get_json(openalex_work_by_doi_url(f"10.48550/arxiv.{arxiv}", mailto), PROVIDER_OPENALEX)
            if outcome.ok and isinstance(outcome.body, dict):
                return openalex_resolution(
                    outcome.body, identity=f"arxiv:{arxiv}", method="openalex-arxiv-doi",
                    notes="OpenAlex arXiv-DOI lookup", title_hint=title_hint, year=seed.year,
                )
            attempts.append(f"openalex-arxiv-doi {outcome.status} {outcome.http_status}".strip())
        if use_s2:
            s2 = s2_resolution_by_identifier(
                client, f"ARXIV:{arxiv}", identity=f"arxiv:{arxiv}", method="s2-arxiv",
                title_hint=title_hint, year=seed.year,
                notes="Semantic Scholar arXiv lookup (OpenAlex arXiv-DOI lookup unavailable)",
            )
            if s2 is not None:
                return s2
            attempts.append("s2-arxiv miss")
        if use_openalex:
            hit, reason = openalex_title_resolution(client, title_hint, seed.year, mailto)
            if hit is not None:
                hit.identity = f"arxiv:{arxiv}"
                hit.method = "openalex-title"
                hit.notes = "OpenAlex arXiv-DOI lookup failed; resolved by title search"
                return hit
            attempts.append(f"openalex-title {reason}")
        if use_s2:
            match, match_reason = s2_resolution_by_title(client, title_hint, seed.year)
            if match is not None:
                match.identity = f"arxiv:{arxiv}"
                match.method = "s2-title-match"
                return match
            attempts.append(match_reason)
        atom = client.get_json(arxiv_metadata_url(arxiv), PROVIDER_ARXIV)
        if atom.ok:
            return Resolution(
                status="metadata_only",
                identity=f"arxiv:{arxiv}",
                method="arxiv-atom",
                doi="",
                title=title_hint,
                year=seed.year,
                notes=f"arXiv Atom metadata only; no citation graph ({'; '.join(attempts) or 'no provider'})",
            )
        return Resolution(
            status="needs_manual_mapping",
            identity=f"arxiv:{arxiv}",
            method="",
            title=title_hint,
            year=seed.year,
            notes=f"arXiv id {arxiv} unresolved ({'; '.join(attempts) or 'no provider tried'}); arXiv says {atom.status}",
        )

    if use_openalex:
        hit, reason = openalex_title_resolution(client, title_hint, seed.year, mailto)
        if hit is not None:
            hit.notes = "No DOI or arXiv id in the corpus entry; resolved by OpenAlex title search"
            return hit
        attempts.append(f"openalex-title {reason}")
    if use_s2:
        match, match_reason = s2_resolution_by_title(client, title_hint, seed.year)
        if match is not None:
            match.notes = "No DOI or arXiv id in the corpus entry; resolved by a Semantic Scholar title match"
            return match
        attempts.append(match_reason)
    crossref_match, crossref_reason = crossref_title_resolution(client, title_hint, seed.year, authors=seed.authors)
    if crossref_match is not None:
        return crossref_match
    attempts.append(crossref_reason)
    return Resolution(
        status="needs_manual_mapping",
        identity="",
        method="",
        title=title_hint,
        year=seed.year,
        notes=f"no DOI/arXiv identity and no title match ({'; '.join(attempts) or 'no provider tried'})",
    )


# ---------------------------------------------------------------------------
# Semantic Scholar (key-free citation-graph fallback)
# ---------------------------------------------------------------------------

S2_PAPER_FIELDS = ",".join(
    [
        "title",
        "year",
        "citationCount",
        "referenceCount",
        "externalIds",
        "venue",
        "authors",
        "publicationTypes",
        "fieldsOfStudy",
    ],
)

# S2 page size for reference/citation lists; the API caps a page at 1000.
S2_PAGE_SIZE = 100

# Title prefixes that mark a reference entry as a venue or container, not a paper.
CONTAINER_TITLE_PREFIXES = (
    "proc.",
    "proceedings",
    "in proc",
    "conference on",
    "symposium on",
    "workshop on",
    "journal of",
    "extended abstracts",
    "lecture notes",
    "vol.",
    "pages",
)

# Semantic Scholar publication types mapped onto OpenAlex type vocabulary.
S2_TYPE_MAP = {
    "journalarticle": "article",
    "conference": "article",
    "review": "review",
    "journalreview": "review",
    "book": "book",
    "booksection": "book-chapter",
    "dataset": "report",
    "clinicaltrial": "article",
    "editorial": "article",
    "lettersandcomments": "article",
    "news": "article",
    "study": "article",
    "metaanalysis": "review",
}


def s2_paper_url(identifier: str) -> str:
    """Return the Semantic Scholar single-paper URL for *identifier*."""
    return f"{S2_API}/paper/{urllib.parse.quote(identifier, safe=':/')}?fields={S2_PAPER_FIELDS}"


def s2_references_url(identifier: str, offset: int, limit: int) -> str:
    """Return the Semantic Scholar reference-list URL for *identifier*."""
    quoted = urllib.parse.quote(identifier, safe=":/")
    return f"{S2_API}/paper/{quoted}/references?fields={S2_PAPER_FIELDS}&limit={limit}&offset={offset}"


def s2_citations_url(identifier: str, offset: int, limit: int) -> str:
    """Return the Semantic Scholar citing-paper URL for *identifier*."""
    quoted = urllib.parse.quote(identifier, safe=":/")
    return f"{S2_API}/paper/{quoted}/citations?fields={S2_PAPER_FIELDS}&limit={limit}&offset={offset}"


def s2_match_url(title: str) -> str:
    """Return the Semantic Scholar title-match URL for *title*."""
    return api_url(f"{S2_API}/paper/search/match", {"query": title, "fields": S2_PAPER_FIELDS})


def s2_identifiers_from_openalex(work: dict[str, Any], doi: str) -> list[str]:
    """Return Semantic Scholar look-up identifiers derived from an OpenAlex work."""
    identifiers: list[str] = []
    if doi:
        identifiers.append(f"DOI:{doi}")
    raw_ids = work.get("ids") or {}
    mag = str(raw_ids.get("mag") or "").rsplit("/", 1)[-1]
    if mag:
        identifiers.append(f"MAG:{mag}")
    return identifiers


def s2_identifiers_from_paper(paper: dict[str, Any]) -> list[str]:
    """Return Semantic Scholar look-up identifiers derived from an S2 paper object."""
    external = paper.get("externalIds") or {}
    identifiers: list[str] = []
    if external.get("DOI"):
        identifiers.append(f"DOI:{normalise_doi(external['DOI'])}")
    if external.get("ArXiv"):
        identifiers.append(f"ARXIV:{normalise_arxiv(external['ArXiv'])}")
    if external.get("MAG"):
        identifiers.append(f"MAG:{external['MAG']}")
    if external.get("CorpusId"):
        identifiers.append(f"CorpusId:{external['CorpusId']}")
    return identifiers


def candidate_from_s2(paper: dict[str, Any]) -> Candidate | None:
    """Build a :class:`Candidate` from a Semantic Scholar paper object."""
    if not isinstance(paper, dict):
        return None
    title = str(paper.get("title") or "").strip()
    if not title:
        return None
    external = paper.get("externalIds") or {}
    types = [str(item) for item in paper.get("publicationTypes") or []]
    fields_of_study = [str(item) for item in paper.get("fieldsOfStudy") or []]
    authors = [
        str(author.get("name", "")).strip()
        for author in paper.get("authors") or []
        if isinstance(author, dict) and str(author.get("name", "")).strip()
    ]
    citation_count = paper.get("citationCount")
    year = paper.get("year")
    candidate = Candidate(
        id="",
        openalex_id=strip_openalex_id(external.get("OpenAlex")),
        doi=normalise_doi(external.get("DOI")),
        arxiv_id=normalise_arxiv(external.get("ArXiv")),
        title=title,
        year=year if isinstance(year, int) else None,
        venue=str(paper.get("venue") or ""),
        authors=authors[:12],
        citation_count=citation_count if isinstance(citation_count, int) else None,
        source=PROVIDER_S2,
        primary_topic=fields_of_study[0] if fields_of_study else "",
        type=S2_TYPE_MAP.get(types[0].lower(), "") if types else "",
    )
    candidate.id = candidate.identity()
    return candidate


def fetch_backward_s2(client: CachedHttp, resolution: Resolution, *, cap: int) -> DirectionResult:
    """Fetch the seed's reference list through the Semantic Scholar reference list.

    The list is empty for many pre-2010 paywalled papers, so an empty result is
    reported as a coverage gap rather than an error.
    """
    result = DirectionResult(direction="backward", provider=PROVIDER_S2)
    identifiers = resolution.s2_ids or s2_identifiers_from_openalex(resolution.work or {}, resolution.doi)
    if not identifiers:
        result.error = "no Semantic Scholar identifier for backward traversal"
        return result
    try:
        for identifier in identifiers[:3]:
            offset = 0
            while len(result.candidates) < cap:
                limit = min(S2_PAGE_SIZE, cap - len(result.candidates))
                outcome = client.get_json(s2_references_url(identifier, offset, limit), PROVIDER_S2)
                if not outcome.ok or not isinstance(outcome.body, dict):
                    result.error = f"references request failed ({outcome.status} {outcome.http_status})"
                    break
                rows = [row for row in outcome.body.get("data") or [] if isinstance(row, dict)]
                for row in rows:
                    candidate = candidate_from_s2(row.get("citedPaper") or {})
                    if candidate is not None:
                        result.candidates.append(candidate)
                offset += len(rows)
                if not rows:
                    break
            if result.error or result.candidates:
                break
    except (ProviderBlockedError, CacheMissError) as error:
        result.error = str(error)
    result.available = max(result.available, len(result.candidates))
    result.capped = len(result.candidates) > cap
    result.candidates = result.candidates[:cap]
    result.fetched = len(result.candidates)
    if not result.candidates and not result.error:
        result.notes = "Semantic Scholar returned an empty reference list (a coverage gap for many pre-2010 papers)"
    return result


def fetch_forward_s2(client: CachedHttp, resolution: Resolution, *, cap: int) -> DirectionResult:
    """Fetch citing works through the Semantic Scholar citation list."""
    result = DirectionResult(direction="forward", provider=PROVIDER_S2)
    identifiers = resolution.s2_ids or s2_identifiers_from_openalex(resolution.work or {}, resolution.doi)
    if not identifiers:
        result.error = "no Semantic Scholar identifier for forward traversal"
        return result
    try:
        for identifier in identifiers[:3]:
            offset = 0
            while len(result.candidates) < cap:
                limit = min(S2_PAGE_SIZE, cap - len(result.candidates))
                outcome = client.get_json(s2_citations_url(identifier, offset, limit), PROVIDER_S2)
                if not outcome.ok or not isinstance(outcome.body, dict):
                    result.error = f"citations request failed ({outcome.status} {outcome.http_status})"
                    break
                rows = [row for row in outcome.body.get("data") or [] if isinstance(row, dict)]
                for row in rows:
                    candidate = candidate_from_s2(row.get("citingPaper") or {})
                    if candidate is not None:
                        result.candidates.append(candidate)
                offset += len(rows)
                result.available = max(result.available, offset)
                if not rows:
                    break
            if result.error or result.candidates:
                break
    except (ProviderBlockedError, CacheMissError) as error:
        result.error = str(error)
    result.capped = len(result.candidates) >= cap
    result.candidates = result.candidates[:cap]
    result.fetched = len(result.candidates)
    if result.capped:
        result.notes = f"citation list reached the {cap}-candidate cap (more citing works may exist)"
    return result


# ---------------------------------------------------------------------------
# Crossref reference lists (backward fallback for publisher DOIs)
# ---------------------------------------------------------------------------


def crossref_item_year(item: dict[str, Any]) -> int | None:
    """Return the publication year of a Crossref item, when it is known."""
    parts = ((item.get("issued") or {}).get("date-parts") or [[]])[0]
    if parts and isinstance(parts[0], int):
        return int(parts[0])
    return None


# A five-row window is not enough: Crossref ranks supplementary-material records
# (".../mm1") of unrelated articles above the real paper, so the window is wide
# and those component records are dropped before scoring.
CROSSREF_TITLE_ROWS = 20


def crossref_title_search_url(title: str, *, rows: int = CROSSREF_TITLE_ROWS) -> str:
    """Return the Crossref bibliographic-search URL for *title*."""
    return api_url(
        f"{CROSSREF_API}/works",
        {"query.bibliographic": title, "rows": str(rows), "select": CROSSREF_TITLE_SELECT},
    )


def title_variants(title: str) -> list[str]:
    """Return search strings for an annotated corpus title, longest first.

    Corpus titles often carry a parenthetical acronym ("... (ACRONYM)"), and the
    variant without it matches the published title, so the fallback search
    keeps a usable query for seeds that carry no identifier.
    """
    variants = [title.strip()]
    stripped = re.sub(r"\s*[(\[][^)\]]*[)\]]", " ", title).strip()
    stripped = re.sub(r"\s{2,}", " ", stripped)
    if stripped and stripped not in variants and len(stripped.split()) >= 3:
        variants.append(stripped)
    return variants


def normalise_name_token(text: str) -> str:
    """Return a comparable ASCII lower-case form of a personal name token."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_only = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z]", "", ascii_only.lower())


def author_surnames(names: Iterable[str]) -> set[str]:
    """Return the surname set of author strings such as "Blaze, M." or "Matt Blaze"."""
    surnames: set[str] = set()
    for raw in names:
        cleaned = re.sub(r"\bet\s+al\.?", " ", str(raw), flags=re.IGNORECASE).strip()
        if not cleaned:
            continue
        candidate = cleaned.split(",")[0] if "," in cleaned else cleaned.split()[-1]
        token = normalise_name_token(candidate)
        if len(token) >= 3:
            surnames.add(token)
    return surnames


def crossref_item_surnames(item: dict[str, Any]) -> set[str]:
    """Return the surname set of a Crossref item's author list."""
    return author_surnames(str(author.get("family") or "") for author in (item.get("author") or []) if isinstance(author, dict))


def candidate_is_citable(candidate: Candidate) -> tuple[bool, str]:
    """Return whether a candidate can be cited, with the reason when it cannot.

    A candidate needs a year or an identifier to be admissible, and a reference
    entry that only names a venue ("Proc. 16th USENIX Security") is not a paper.
    """
    has_identity = bool(candidate.doi or candidate.arxiv_id or candidate.openalex_id)
    if not has_identity and candidate.year is None:
        return False, "no year and no DOI/arXiv/OpenAlex identity"
    if not has_identity and candidate.source.endswith("-reference") and candidate.title.lower().strip().startswith(CONTAINER_TITLE_PREFIXES):
        return False, "reference entry names a venue or container, not a paper"
    return True, ""


def crossref_reference_candidates(message: dict[str, Any], *, cap: int) -> list[Candidate]:
    """Build candidates from a Crossref ``reference`` array.

    Crossref deposits carry a title, year, venue and often a DOI per reference,
    but never a citation count; missing values stay empty rather than guessed.
    """
    candidates: list[Candidate] = []
    for reference in message.get("reference") or []:
        if not isinstance(reference, dict):
            continue
        title = str(
            reference.get("article-title")
            or reference.get("volume-title")
            or reference.get("unstructured")
            or "",
        ).strip()
        # Publisher deposits often prefix a reference with the number of the one before its year.
        title = re.sub(r"^\d{4}[.,]?\s+", "", title).strip()
        if not title:
            continue
        year_raw = str(reference.get("year") or "").strip()
        year = int(year_raw) if year_raw.isdigit() else None
        doi = normalise_doi(reference.get("DOI") or reference.get("doi"))
        candidate = Candidate(
            id="",
            doi=doi,
            title=title,
            year=year,
            venue=str(reference.get("journal-title") or "").strip(),
            authors=[str(reference.get("author")).strip()] if reference.get("author") else [],
            source=f"{PROVIDER_CROSSREF}-reference",
        )
        candidate.id = candidate.identity()
        candidates.append(candidate)
        if len(candidates) >= cap:
            break
    return candidates


def fetch_backward_crossref(client: CachedHttp, resolution: Resolution, *, cap: int) -> DirectionResult:
    """Fetch the seed's reference list from the Crossref work record."""
    result = DirectionResult(direction="backward", provider=PROVIDER_CROSSREF)
    doi = resolution.doi or resolution.identity.removeprefix("doi:")
    if not doi:
        result.error = "no DOI for a Crossref reference lookup"
        return result
    try:
        outcome = client.get_json(crossref_work_url(doi), PROVIDER_CROSSREF)
    except (ProviderBlockedError, CacheMissError) as error:
        result.error = str(error)
        return result
    if not outcome.ok or not isinstance(outcome.body, dict):
        result.error = f"Crossref work lookup failed ({outcome.status} {outcome.http_status})"
        return result
    message = outcome.body.get("message")
    if not isinstance(message, dict):
        result.error = "Crossref response has no message object"
        return result
    result.available = int(message.get("reference-count") or 0)
    result.candidates = crossref_reference_candidates(message, cap=cap)
    result.capped = len(result.candidates) >= cap
    result.fetched = len(result.candidates)
    dropped = len(message.get("reference") or []) - result.fetched
    if dropped > 0:
        result.notes = f"Crossref deposits {len(message.get('reference') or [])} reference entries; {dropped} carry no title or DOI to cite"
    return result


# ---------------------------------------------------------------------------
# Snowballing
# ---------------------------------------------------------------------------


@dataclass
class DirectionResult:
    """Outcome of one snowball direction for one seed."""

    direction: str
    provider: str = ""
    attempts: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    available: int = 0
    fetched: int = 0
    capped: bool = False
    notes: str = ""
    error: str = ""


def fetch_backward(
    client: CachedHttp,
    resolution: Resolution,
    *,
    cap: int,
    mailto: str,
    provider: str = PROVIDER_OPENALEX,
) -> DirectionResult:
    """Fetch the seed's reference list from *provider*."""
    if provider == PROVIDER_S2:
        return fetch_backward_s2(client, resolution, cap=cap)
    if provider == PROVIDER_CROSSREF:
        return fetch_backward_crossref(client, resolution, cap=cap)
    return fetch_backward_openalex(client, resolution, cap=cap, mailto=mailto)


def fetch_backward_openalex(client: CachedHttp, resolution: Resolution, *, cap: int, mailto: str) -> DirectionResult:
    """Fetch the seed's reference list through the OpenAlex batch endpoint."""
    result = DirectionResult(direction="backward", provider=PROVIDER_OPENALEX)
    if resolution.work_provider and resolution.work_provider != PROVIDER_OPENALEX:
        result.error = f"seed resolved through {resolution.work_provider}; no OpenAlex work object"
        return result
    work = resolution.work or {}
    references = [strip_openalex_id(item) for item in (work.get("referenced_works") or [])]
    references = [item for item in references if item]
    result.available = len(references)
    if not references:
        result.error = "seed has no referenced_works in OpenAlex"
        return result
    selected = references[:cap]
    result.capped = len(references) > cap
    try:
        for start in range(0, len(selected), 50):
            chunk = selected[start : start + 50]
            outcome = client.get_json(openalex_batch_url(chunk, mailto), PROVIDER_OPENALEX_LIST)
            if not outcome.ok or not isinstance(outcome.body, dict):
                result.error = f"batch request failed ({outcome.status} {outcome.http_status})"
                break
            for item in outcome.body.get("results") or []:
                candidate = candidate_from_openalex(item)
                if candidate is not None:
                    result.candidates.append(candidate)
    except (ProviderBlockedError, CacheMissError) as error:
        result.error = str(error)
    result.fetched = len(result.candidates)
    missing = len(selected) - result.fetched
    if missing > 0 and not result.error:
        result.notes = f"the batch endpoint returned {result.fetched} of {len(selected)} referenced works"
    return result


def fetch_forward(
    client: CachedHttp,
    resolution: Resolution,
    *,
    cap: int,
    mailto: str,
    provider: str = PROVIDER_OPENALEX,
) -> DirectionResult:
    """Fetch works citing the seed from *provider*."""
    if provider == PROVIDER_S2:
        return fetch_forward_s2(client, resolution, cap=cap)
    if provider != PROVIDER_OPENALEX:
        return DirectionResult(direction="forward", error=f"{provider} has no citation-graph endpoint")
    return fetch_forward_openalex(client, resolution, cap=cap, mailto=mailto)


def fetch_forward_openalex(client: CachedHttp, resolution: Resolution, *, cap: int, mailto: str) -> DirectionResult:
    """Fetch works citing the seed through the OpenAlex cursor API."""
    result = DirectionResult(direction="forward", provider=PROVIDER_OPENALEX)
    work_id = resolution.openalex_id or strip_openalex_id((resolution.work or {}).get("id"))
    if not work_id:
        result.error = "no OpenAlex work id for forward traversal"
        return result
    cursor = "*"
    try:
        while len(result.candidates) < cap:
            outcome = client.get_json(openalex_citing_url(work_id, cursor, mailto), PROVIDER_OPENALEX_LIST)
            if not outcome.ok or not isinstance(outcome.body, dict):
                result.error = f"cites request failed ({outcome.status} {outcome.http_status})"
                break
            page = outcome.body.get("results") or []
            for item in page:
                candidate = candidate_from_openalex(item)
                if candidate is not None:
                    result.candidates.append(candidate)
            meta = outcome.body.get("meta") or {}
            result.available = int(meta.get("count") or len(result.candidates))
            cursor = str(meta.get("next_cursor") or "")
            if not cursor or not page:
                break
        if len(result.candidates) >= cap:
            result.candidates = result.candidates[:cap]
            result.capped = result.available > cap
    except (ProviderBlockedError, CacheMissError) as error:
        result.error = str(error)
    result.fetched = len(result.candidates)
    return result


def merge_candidate(store: dict[str, Candidate], candidate: Candidate, seed_key: str, direction: str) -> None:
    """Insert or merge *candidate*, recording seed/direction provenance."""
    identity = candidate.identity()
    existing = store.get(identity)
    if existing is None:
        candidate.surfaced_by = [{"seed": seed_key, "direction": direction}]
        store[identity] = candidate
        return
    provenance = {"seed": seed_key, "direction": direction}
    if provenance not in existing.surfaced_by:
        existing.surfaced_by.append(provenance)
    for attribute in ("openalex_id", "doi", "arxiv_id", "venue", "primary_topic", "type"):
        if not getattr(existing, attribute) and getattr(candidate, attribute):
            setattr(existing, attribute, getattr(candidate, attribute))
    if existing.citation_count is None and candidate.citation_count is not None:
        existing.citation_count = candidate.citation_count
    if existing.year is None and candidate.year is not None:
        existing.year = candidate.year
    if not existing.title and candidate.title:
        existing.title = candidate.title
    if not existing.authors and candidate.authors:
        existing.authors = candidate.authors
    existing.id = existing.identity()


# ---------------------------------------------------------------------------
# State and artefacts
# ---------------------------------------------------------------------------

RELEVANCE_TEMPLATES: dict[str, str] = {
    "LLM agent security": "agent-security threat or defence result that bounds what Conflux can assume about model behaviour",
    "Information flow control": "IFC label/declassification mechanism comparable to Conflux provenance labels",
    "Integrity models": "integrity model that constrains how Conflux may treat untrusted inputs as authority",
    "Access control": "authorisation mechanism or policy model that Conflux must position against",
    "Delegation and authority": "delegation or trust-management construction relevant to Conflux authority transfer",
    "Provenance and attribution": "provenance/attribution technique usable as Conflux prior work or baseline",
    "Verification and synthesis": "verification or synthesis technique applicable to Conflux policy checking",
    "Runtime enforcement": "runtime enforcement or monitoring approach comparable to Conflux reference monitoring",
    "Multi-agent systems": "multi-agent composition result relevant to Conflux agent-protocol analysis",
    "Policy languages and analysis": "policy language or policy-analysis result relevant to Conflux policy formalisation",
    "Systems security": "systems-security mechanism supplying the OS/cloud substrate assumptions Conflux inherits",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "based",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "toward",
    "towards",
    "using",
    "with",
}

SOURCE_TYPE_BY_OPENALEX_TYPE = {
    "article": "primary_paper",
    "review": "survey",
    "book": "book",
    "book-chapter": "book",
    "report": "technical_report",
    "standard": "standard",
    "dissertation": "technical_report",
    "preprint": "primary_paper",
}


def slugify_title(title: str, *, max_words: int = 3, max_length: int = 28) -> str:
    """Return a candidate corpus key derived from the title."""
    words = [word for word in normalise_title(title).split() if word not in STOPWORDS]
    slug = "".join(words[:max_words])[:max_length]
    return slug or "untitled"


def propose_key(title: str, used: set[str]) -> str:
    """Return a unique corpus key for a proposed entry."""
    base = slugify_title(title)
    if base not in used:
        used.add(base)
        return base
    for index in range(2, 100):
        candidate = f"{base}{index}"
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise RuntimeError(f"could not derive a unique key for {title!r}")


def candidate_from_state(data: dict[str, Any]) -> Candidate:
    """Rebuild a :class:`Candidate` from its state/JSON form."""
    dedupe = data.get("dedupe") or {}
    candidate = Candidate(
        id=str(data.get("id", "")),
        openalex_id=str(data.get("openalex_id", "")),
        doi=str(data.get("doi", "")),
        arxiv_id=str(data.get("arxiv_id", "")),
        title=str(data.get("title", "")),
        year=data.get("year") if isinstance(data.get("year"), int) else None,
        venue=str(data.get("venue", "")),
        authors=[str(author) for author in data.get("authors") or []],
        citation_count=data.get("citation_count") if isinstance(data.get("citation_count"), int) else None,
        source=str(data.get("source", "")),
        primary_topic=str(data.get("primary_topic", "")),
        type=str(data.get("type", "")),
        surfaced_by=[dict(item) for item in data.get("surfaced_by") or []],
        dedupe_verdict=str(dedupe.get("verdict", "new")),
        dedupe_key=str(dedupe.get("matched_key", "")),
        dedupe_match=str(dedupe.get("match_type", "")),
        stream_guess=str(data.get("stream_guess", "")),
        stream_hits=[str(hit) for hit in data.get("stream_hits") or []],
    )
    candidate.id = candidate.id or candidate.identity()
    return candidate


def source_url_for(candidate: Candidate) -> str:
    """Return the best primary URL for a candidate."""
    if candidate.doi:
        return f"https://doi.org/{candidate.doi}"
    if candidate.arxiv_id:
        return f"https://arxiv.org/abs/{candidate.arxiv_id}"
    if candidate.openalex_id:
        return f"https://openalex.org/{candidate.openalex_id}"
    return ""


def build_proposed_entry(candidate: Candidate, *, key: str, date: str, priority: str) -> dict[str, Any]:
    """Return a schema-conformant corpus entry proposal for *candidate*."""
    provenance = ", ".join(
        f"{item.get('seed')} ({item.get('direction')})" for item in sorted_provenance(candidate.surfaced_by)
    )
    entry: dict[str, Any] = {
        "key": key,
        "title": candidate.title,
        "year": candidate.year,
        "verified": {
            "method": "unverified",
            "depth": "unverified",
            "date": date,
            "notes": (
                f"Snowball candidate from seed(s) {provenance}; "
                f"{candidate.source} identity {candidate.identity()}. Metadata only - primary-source "
                "verification and a landscape pass are still required before admission."
            ),
            "checked_by": "ai_agent",
        },
        "last_checked": date,
        "adoption_priority": priority,
        "snowball_status": {"backward": "pending", "forward": "pending"},
        "reading_status": "not_started",
        "reading_priority": priority,
        "stream": candidate.stream_guess,
        "source_type": SOURCE_TYPE_BY_OPENALEX_TYPE.get(candidate.type, "primary_paper"),
    }
    if candidate.authors:
        entry["authors"] = candidate.authors
    if candidate.venue:
        entry["venue"] = candidate.venue
    if candidate.doi:
        entry["doi"] = candidate.doi
    if candidate.arxiv_id:
        entry["arxiv_id"] = candidate.arxiv_id
    url = source_url_for(candidate)
    if url:
        entry["source_url"] = url
    return entry


def sorted_provenance(surfaced_by: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return provenance entries in deterministic order."""
    return sorted(surfaced_by, key=lambda item: (str(item.get("seed", "")), str(item.get("direction", ""))))


def entry_is_schema_conformant(entry: dict[str, Any]) -> list[str]:
    """Return schema errors for one proposed entry (empty list when conformant)."""
    schema: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    item_schema = schema["properties"]["entries"]["items"]
    errors = sorted(Draft202012Validator(item_schema).iter_errors(entry), key=lambda error: list(error.path))
    return [f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}" for error in errors]


def display_path(path: Path) -> str:
    """Return *path* relative to the repository root when it lives inside it."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:  # --out-dir outside the repository
        return str(path)


def ensure_parent(path: Path) -> None:
    """Create the parent directory of *path* when it does not exist yet."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> int:
    """Write *payload* as deterministic JSON and return the byte size."""
    ensure_parent(path)
    text = json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    size = path.stat().st_size
    print(f"[snowball] wrote {display_path(path)} ({size} bytes)", flush=True)
    return size


def write_markdown(path: Path, text: str) -> int:
    """Write *text* to *path* and return the byte size."""
    ensure_parent(path)
    path.write_text(text, encoding="utf-8")
    size = path.stat().st_size
    print(f"[snowball] wrote {display_path(path)} ({size} bytes)", flush=True)
    return size


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def candidate_sort_key(candidate: Candidate) -> tuple[int, int, str]:
    """Rank candidates by score, then citations, then title."""
    return (-candidate.score, -(candidate.citation_count or 0), normalise_title(candidate.title))


def relevance_line(candidate: Candidate) -> str:
    """Return the one-line relevance statement for a candidate."""
    template = RELEVANCE_TEMPLATES.get(candidate.stream_guess, "candidate for manual triage")
    provenance = ", ".join(
        f"{item.get('seed')} ({item.get('direction')})" for item in sorted_provenance(candidate.surfaced_by)
    )
    return f"{template}; surfaced from {provenance}"


def compact_seed_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a seed record without the raw provider payload.

    The resolved work is reduced to the fields a reviewer needs in order to check
    the mapping (title, year, DOI, type).  The raw JSON responses stay in the
    response cache keyed by URL, so third-party payload fields (author
    affiliations, for example) are not copied into the report.
    """
    compact = {key: value for key, value in record.items() if key != "work"}
    work = record.get("work")
    if isinstance(work, dict):
        compact["work_summary"] = {
            "title": work.get("display_name") or work.get("title") or "",
            "year": work.get("publication_year"),
            "doi": normalise_doi(work.get("doi")) or "",
            "openalex_type": work.get("type") or "",
        }
    return compact


def render_candidates_document(
    *,
    date: str,
    generator: str,
    corpus_sha256: str,
    corpus_entries: int,
    seeds: list[dict[str, Any]],
    candidates: list[Candidate],
    counts: dict[str, int],
    client_stats: dict[str, int],
    paused_providers: dict[str, str],
    provider_plans: dict[str, list[str]],
    provider_mix: dict[str, dict[str, int]],
) -> dict[str, Any]:
    """Return the machine-readable candidate document."""
    return {
        "schema_version": "1",
        "generated_date": date,
        "generator": generator,
        "corpus": {
            "path": "research/reports/analysis/literature_corpus.json",
            "entries": corpus_entries,
            "sha256": corpus_sha256,
        },
        "sources": [
            {"provider": PROVIDER_OPENALEX, "endpoint": OPENALEX_API, "role": "primary identity, backward and forward graph"},
            {
                "provider": PROVIDER_S2,
                "endpoint": S2_API,
                "role": "fallback identity and citation graph (key-free; reference lists empty for many pre-2010 papers)",
            },
            {
                "provider": PROVIDER_CROSSREF,
                "endpoint": CROSSREF_API,
                "role": "publisher-DOI metadata and reference lists (no citation counts)",
            },
            {"provider": PROVIDER_ARXIV, "endpoint": ARXIV_API, "role": "metadata for arXiv-only seeds"},
        ],
        "provider_plans": provider_plans,
        "provider_mix": provider_mix,
        "paused_providers": paused_providers,
        "http_stats": client_stats,
        "rubric": RUBRIC,
        "counts": counts,
        "seeds": seeds,
        "candidates": [candidate.to_json() for candidate in candidates],
    }


def _mix_line(counts: dict[str, Any]) -> str:
    """Render provider counts (or provider reasons) as ``name n, name n``."""
    items: list[str] = []
    for key, value in sorted(counts.items(), key=lambda item: str(item[0])):
        if isinstance(value, bool) or not value:
            continue
        items.append(f"{key} {value}" if isinstance(value, int) else f"{key} ({value})")
    return ", ".join(items) or "none"


def _seed_row(seed_record: dict[str, Any]) -> str:
    backward = seed_record.get("backward") or {}
    forward = seed_record.get("forward") or {}
    detail = []
    if seed_record.get("status") == "needs_manual_mapping":
        detail.append(str(seed_record.get("notes", "")))
    if backward.get("error"):
        detail.append(f"backward: {backward['error']}")
    if forward.get("error"):
        detail.append(f"forward: {forward['error']}")
    return " | ".join(detail) or str(seed_record.get("notes", ""))


def render_triage_markdown(
    *,
    date: str,
    generator: str,
    corpus_sha256: str,
    corpus_entries: int,
    seeds: list[dict[str, Any]],
    candidates: list[Candidate],
    counts: dict[str, int],
    client_stats: dict[str, int],
    proposed_count: int,
    top_titles: dict[str, str],
    provider_mix: dict[str, dict[str, int]],
    paused_providers: dict[str, str],
    uncitable: dict[str, int],
) -> str:
    """Return the human triage report."""
    ranked = sorted(candidates, key=candidate_sort_key)
    lines: list[str] = []
    lines.append(f"# Snowball candidates: {date}")
    lines.append("")
    lines.append(
        f"Generated by `{generator}` against the literature corpus "
        f"(`research/reports/analysis/literature_corpus.json`, {corpus_entries} entries, "
        f"sha256 `{corpus_sha256[:12]}`). Key-free sources only: OpenAlex (primary), Semantic Scholar "
        "(fallback citation graph), Crossref (publisher-DOI metadata and reference lists) and the arXiv "
        "Atom API (arXiv-only seeds). Raw responses are cached under `.local/snowball-cache/`; the corpus "
        "and its manifest were not modified.",
    )
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Seeds selected | {counts['seeds_total']} |")
    lines.append(f"| Seeds resolved to a work record (any provider) | {counts['seeds_resolved']} |")
    lines.append(f"| Seeds snowballed backward (>=1 reference fetched) | {counts['backward_seeds_with_results']} |")
    lines.append(f"| Seeds snowballed forward (>=1 citing work fetched) | {counts['forward_seeds_with_results']} |")
    lines.append(f"| Seeds whose backward traversal hit the cap | {counts.get('backward_seeds_capped', 0)} |")
    lines.append(f"| Seeds whose forward traversal hit the cap | {counts.get('forward_seeds_capped', 0)} |")
    lines.append(f"| Seeds with per-direction coverage notes | {counts.get('seeds_with_coverage_notes', 0)} |")
    lines.append(f"| Raw graph hits dropped as uncitable | {counts.get('candidates_uncitable', 0)} |")
    lines.append(f"| Seeds with metadata only (no key-free citation graph) | {counts['seeds_metadata_only']} |")
    lines.append(f"| Seeds needing manual mapping | {counts['seeds_unresolved']} |")
    lines.append(f"| Candidate sightings (seed x direction) | {counts['sightings']} |")
    lines.append(f"| Distinct candidates | {counts['candidates_total']} |")
    lines.append(f"| New after dedupe | {counts['candidates_new']} |")
    lines.append(f"| Possible duplicates (fuzzy title) | {counts['candidates_possible_duplicate']} |")
    lines.append(f"| Already in the corpus | {counts['candidates_existing']} |")
    lines.append(f"| Proposed entries | {proposed_count} |")
    lines.append(f"| API requests issued / cache hits (sweep total) | {client_stats.get('requests', 0)} / {client_stats.get('cache_hits', 0)} |")
    lines.append(f"| Seed resolution providers | {_mix_line(provider_mix.get('resolution', {}))} |")
    lines.append(f"| Backward answers by provider | {_mix_line(provider_mix.get('backward', {}))} |")
    lines.append(f"| Forward answers by provider | {_mix_line(provider_mix.get('forward', {}))} |")
    lines.append(f"| Paused providers (429 budget wall) | {_mix_line(paused_providers) or 'none'} |")
    lines.append("")
    lines.append("## Score rubric")
    lines.append("")
    lines.append("```text")
    lines.extend(RUBRIC.splitlines())
    lines.append("```")
    lines.append("")
    lines.append(f"## Ranked candidates (top {min(30, len(ranked))} of {len(ranked)})")
    lines.append("")
    lines.append("| # | Candidate | Year | Score | Surfaced by | Why it matters |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for position, candidate in enumerate(ranked[:30], start=1):
        label = top_titles.get(candidate.id, candidate.title)
        provenance = ", ".join(
            f"{item.get('seed')}:{str(item.get('direction', ''))[:1]}" for item in sorted_provenance(candidate.surfaced_by)
        )
        verdict = "" if candidate.dedupe_verdict == "new" else f" [{candidate.dedupe_verdict}: {candidate.dedupe_key}]"
        lines.append(
            f"| {position} | {label}{verdict} | {candidate.year or ''} | {candidate.score} | {provenance} | "
            f"{relevance_line(candidate)} |",
        )
    lines.append("")
    lines.append("## Unresolved and failed seeds")
    lines.append("")
    lines.append("| Seed | Status | Identity | Detail |")
    lines.append("| --- | --- | --- | --- |")
    unresolved_rows = 0
    for seed_record in seeds:
        if seed_record.get("status") in ("resolved", "snowballed"):
            backward = seed_record.get("backward") or {}
            forward = seed_record.get("forward") or {}
            if not backward.get("error") and not forward.get("error"):
                continue
        lines.append(
            f"| {seed_record.get('key', '')} | {seed_record.get('status', '')} | "
            f"{seed_record.get('identity', '') or '-'} | {_seed_row(seed_record) or '-'} |",
        )
        unresolved_rows += 1
    if unresolved_rows == 0:
        lines.append("| _(none)_ | | | Every selected seed resolved and snowballed without a recorded error. |")
    lines.append("")
    lines.append("## Method and limitations")
    lines.append("")
    lines.append("- Backward = the seed's reference list; forward = works citing the seed. Provider order is OpenAlex, then Semantic Scholar, then (for DOI seeds, backward only) the Crossref `reference` array.")
    lines.append("- A provider that is rate-limited, blocked or empty hands over to the next provider in the plan, so one exhausted quota does not drop a seed.")
    lines.append(
        "- Identity resolution order: corpus DOI or arXiv id, then a DOI/arXiv extracted from `source_url`, "
        "then a title search (OpenAlex, then the Semantic Scholar match endpoint, then a Crossref bibliographic search). "
        "A title hit is accepted only when the title is near-exact and the record is confirmed by an agreeing year or an "
        "overlapping author surname; a corpus title that differs from the published title stays unresolved on purpose.",
    )
    lines.append("- Dedupe checks DOI, arXiv id and normalised title against the 176 corpus keys; `possible_duplicate` means a title-similarity score of at least 0.93 with no identifier match.")
    lines.append(
        "- The resolved work is reduced to a summary (title, year, DOI, OpenAlex type); the raw provider "
        "responses stay in the response cache keyed by URL and are not copied into the artefact.",
    )
    lines.append("- Citation counts and venue strings come from OpenAlex or Semantic Scholar and are metadata, not verified bibliography.")
    lines.append("- Semantic Scholar is key-free and unauthenticated, so it is rate-limited hard: page fetches back off, and an empty reference list means a coverage gap, not an error.")
    lines.append("- Crossref reference entries often carry no DOI and never carry a citation count, so those candidates rank lower and are excluded from the proposed entries.")
    lines.append("- Forward traversal is capped per seed. `capped` in the machine-readable record means the cap stopped the traversal; `notes` records provider coverage gaps (for example a Crossref reference entry without a title, or an empty Semantic Scholar reference list).")
    lines.append(f"- Raw graph hits that cannot be cited are dropped from the ranked list: {_mix_line(uncitable)}.")
    lines.append("- Proposed entries are unverified proposals: admission to the corpus, the fetch manifest and `fetch_status.json` is a separate reviewed step.")
    lines.append("")
    return "\n".join(lines)


def render_proposed_entries(
    *,
    date: str,
    generator: str,
    candidates: list[Candidate],
    limit: int,
    used_keys: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Return the proposed-entries document and its schema-validation errors."""
    eligible = [
        candidate
        for candidate in sorted(candidates, key=candidate_sort_key)
        if candidate.dedupe_verdict == "new"
        and candidate.year is not None
        and (candidate.doi or candidate.arxiv_id or candidate.openalex_id)
    ]
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    for candidate in eligible[:limit]:
        priority = "B" if candidate.score >= 25 else "C"
        entry = build_proposed_entry(candidate, key=propose_key(candidate.title, used_keys), date=date, priority=priority)
        entry_errors = entry_is_schema_conformant(entry)
        if entry_errors:
            errors.append(f"{candidate.identity()}: {'; '.join(entry_errors)}")
            continue
        entries.append(entry)
    document: dict[str, Any] = {
        "schema_version": "2",
        "generated_date": date,
        "generator": generator,
        "status": "proposal",
        "note": (
            "Proposed corpus entries from the snowball pass. The corpus, its manifest and "
            "fetch_status.json are unchanged; admission is a separate reviewed step."
        ),
        "selection_rule": (
            f"top {limit} candidates with dedupe verdict 'new', a non-null year, a DOI/arXiv/OpenAlex identity, "
            "ranked by the snowball score; adoption_priority B when score >= 25 else C"
        ),
        "admission_checklist": [
            "add the entry to research/reports/analysis/literature_corpus.json",
            "add the matching manifests entry to research/literature/manifest.json (key parity is enforced by tests)",
            "write research/literature/papers/<key>/fetch_status.json when a local copy is fetched",
            "run python scripts/validate.py --tier quick after the edit and --tier standard before committing",
            "promote verified.method only after primary-source verification",
        ],
        "entries": entries,
    }
    return document, errors


# ---------------------------------------------------------------------------
# Run driver
# ---------------------------------------------------------------------------


def load_state(path: Path) -> dict[str, Any]:
    """Load a checkpoint, returning an empty skeleton when absent or invalid."""
    if not path.is_file():
        return {"seeds": {}, "candidates": []}
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"seeds": {}, "candidates": []}
    if not isinstance(data, dict):
        return {"seeds": {}, "candidates": []}
    seeds = data.get("seeds") if isinstance(data.get("seeds"), dict) else {}
    candidates = data.get("candidates") if isinstance(data.get("candidates"), list) else []
    stats = data.get("stats") if isinstance(data.get("stats"), dict) else {}
    paused = data.get("paused_providers") if isinstance(data.get("paused_providers"), dict) else {}
    return {"seeds": seeds, "candidates": candidates, "stats": stats, "paused_providers": paused}


def save_state(path: Path, state: dict[str, Any]) -> None:
    """Persist the checkpoint after each seed."""
    payload = {
        "updated_utc": utc_now(),
        "seeds": state.get("seeds", {}),
        "candidates": [candidate.to_json() for candidate in state.get("candidates", [])],
        "stats": state.get("stats", {}),
        "paused_providers": state.get("paused_providers", {}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def attempt_direction(
    client: CachedHttp,
    resolution: Resolution,
    direction: str,
    *,
    cap: int,
    mailto: str,
    providers: list[str],
) -> DirectionResult:
    """Run one direction over the provider plan, keeping the best result.

    Providers are tried in plan order until one returns candidates.  A provider
    that is rate-limited, blocked or empty hands over to the next one; errors
    are reported only when no provider produced candidates, so a fallback that
    works does not hide a usable answer behind a stale failure.
    """
    attempts: list[str] = []
    fallback: DirectionResult | None = None
    for provider in providers:
        try:
            if direction == "backward":
                result = fetch_backward(client, resolution, cap=cap, mailto=mailto, provider=provider)
            else:
                result = fetch_forward(client, resolution, cap=cap, mailto=mailto, provider=provider)
        except (ProviderBlockedError, CacheMissError) as error:
            attempts.append(f"{provider}: {error}")
            continue
        if result.candidates:
            attempts.append(f"{provider}: {len(result.candidates)} candidates")
            result.attempts = attempts
            return result
        detail = result.error or "no candidates"
        attempts.append(f"{provider}: {detail}")
        if not result.error and fallback is None:
            fallback = result
    if fallback is not None:
        fallback.attempts = attempts
        return fallback
    return DirectionResult(
        direction=direction,
        attempts=attempts,
        error="; ".join(attempts) or f"no provider returned {direction} data",
    )


def process_seed(
    client: CachedHttp,
    seed: Seed,
    *,
    directions: list[str],
    backward_cap: int,
    forward_cap: int,
    mailto: str,
    providers: dict[str, list[str]],
    retry_errors: bool,
    state: dict[str, Any],
) -> None:
    """Resolve *seed* and snowball the missing directions, updating *state*."""
    seeds_state: dict[str, Any] = state["seeds"]
    record: dict[str, Any] = seeds_state.setdefault(
        seed.key,
        {
            "key": seed.key,
            "title": seed.title,
            "priority": seed.priority,
            "verified_method": seed.verified_method,
            "stream": seed.stream,
            "identity": "",
            "resolution": "",
            "status": "pending",
            "notes": "",
        },
    )
    if record["status"] in ("needs_manual_mapping", "metadata_only", "provider_unavailable") and not isinstance(
        record.get("work"), dict,
    ):
        return
    if not record.get("identity") or not isinstance(record.get("work"), dict):
        try:
            resolution = resolve_seed(client, seed, mailto, providers=providers.get("backward", []))
        except (ProviderBlockedError, CacheMissError) as error:
            record.update({"status": "provider_unavailable", "notes": str(error)})
            return
        except (urllib.error.URLError, TimeoutError, ValueError) as error:  # pragma: no cover - network guard
            record.update({"status": "needs_manual_mapping", "notes": f"resolution failed: {error!r}"})
            return
        record.update(
            {
                "identity": resolution.identity,
                "resolution": resolution.method,
                "status": resolution.status,
                "notes": resolution.notes,
                "openalex_id": resolution.openalex_id,
                "doi": resolution.doi,
                "work_provider": resolution.work_provider,
                "s2_ids": resolution.s2_ids,
                "work": resolution.work if resolution.status == "resolved" else None,
            },
        )
        if resolution.status != "resolved":
            return
    else:
        # A resumed run reuses the checkpointed work object; the 176-entry corpus
        # and the response cache make the remaining directions the only work left.
        checkpointed = record["work"]
        work_provider = str(record.get("work_provider") or PROVIDER_OPENALEX)
        recorded_ids = [str(item) for item in record.get("s2_ids") or []]
        if not recorded_ids and work_provider == PROVIDER_OPENALEX:
            recorded_ids = s2_identifiers_from_openalex(checkpointed, str(record.get("identity", "")).removeprefix("doi:"))
        resolution = Resolution(
            status="resolved",
            identity=str(record.get("identity", "")),
            method=str(record.get("resolution", "")),
            openalex_id=str(record.get("openalex_id", "")),
            doi=str(record.get("doi") or str(record.get("identity", "")).removeprefix("doi:")),
            work=checkpointed,
            work_provider=work_provider,
            s2_ids=recorded_ids,
        )

    for direction in directions:
        recorded = record.get(direction)
        if recorded is not None and not (retry_errors and recorded.get("error")):
            continue
        cap = backward_cap if direction == "backward" else forward_cap
        result = attempt_direction(
            client,
            resolution,
            direction,
            cap=cap,
            mailto=mailto,
            providers=providers.get(direction, providers.get("backward", [])),
        )
        for candidate in result.candidates:
            merge_candidate(state["candidate_store"], candidate, seed.key, direction)
        record[direction] = {
            "provider": result.provider,
            "available": result.available,
            "fetched": result.fetched,
            "capped": result.capped,
            "notes": result.notes,
            "attempts": result.attempts,
            "error": result.error,
        }
    errors = [record.get(direction, {}).get("error", "") for direction in directions]
    results = [record.get(direction, {}).get("fetched", 0) for direction in directions]
    if any(error for error in errors):
        record["status"] = "partial"
    elif not any(results):
        record["status"] = "no_citation_data"
    else:
        record["status"] = "snowballed"


def refresh_candidates(
    candidates: list[Candidate],
    corpus_index: CorpusIndex,
    seed_streams: dict[str, str],
) -> tuple[list[Candidate], dict[str, int]]:
    """Recompute dedupe verdicts, stream guesses and scores for every candidate.

    Returns the citable candidates and the count of dropped ones keyed by
    reason, so the artefacts can state how much raw graph output was filtered
    out and why.
    """
    kept: list[Candidate] = []
    dropped: dict[str, int] = {}
    for candidate in candidates:
        candidate.dedupe_verdict, candidate.dedupe_key, candidate.dedupe_match = corpus_index.match(
            doi=candidate.doi, arxiv_id=candidate.arxiv_id, title=candidate.title,
        )
        seed_streams_for_candidate = [
            seed_streams.get(str(item.get("seed", "")), "") for item in candidate.surfaced_by
        ]
        candidate.stream_guess, candidate.stream_hits = guess_stream(candidate, seed_streams_for_candidate)
        directions = {str(item.get("direction", "")) for item in candidate.surfaced_by}
        distinct_seeds = {str(item.get("seed", "")) for item in candidate.surfaced_by}
        score_candidate(candidate, distinct_seeds=len(distinct_seeds), directions=directions)
        candidate.surfaced_by = sorted_provenance(candidate.surfaced_by)
        citable, reason = candidate_is_citable(candidate)
        if citable:
            kept.append(candidate)
        else:
            dropped[reason] = dropped.get(reason, 0) + 1
    return kept, dropped


def compute_counts(seed_records: dict[str, Any], candidates: list[Candidate], seeds_total: int) -> dict[str, int]:
    """Return the coverage counters used by both artefacts."""
    seeds_resolved = 0
    metadata_only = 0
    unresolved = 0
    backward_results = 0
    forward_results = 0
    backward_capped = 0
    forward_capped = 0
    noted = 0
    for record in seed_records.values():
        status = str(record.get("status", ""))
        if status in ("resolved", "snowballed", "partial", "no_citation_data"):
            seeds_resolved += 1
        if status == "metadata_only":
            metadata_only += 1
        if status == "needs_manual_mapping":
            unresolved += 1
        backward = record.get("backward") or {}
        forward = record.get("forward") or {}
        if backward.get("fetched", 0) > 0:
            backward_results += 1
        if forward.get("fetched", 0) > 0:
            forward_results += 1
        if backward.get("capped"):
            backward_capped += 1
        if forward.get("capped"):
            forward_capped += 1
        if backward.get("notes") or forward.get("notes"):
            noted += 1
    return {
        "seeds_total": seeds_total,
        "seeds_attempted": len(seed_records),
        "seeds_resolved": seeds_resolved,
        "seeds_metadata_only": metadata_only,
        "seeds_unresolved": unresolved,
        "backward_seeds_with_results": backward_results,
        "forward_seeds_with_results": forward_results,
        "backward_seeds_capped": backward_capped,
        "forward_seeds_capped": forward_capped,
        "seeds_with_coverage_notes": noted,
        "sightings": sum(len(candidate.surfaced_by) for candidate in candidates),
        "candidates_total": len(candidates),
        "candidates_new": sum(1 for candidate in candidates if candidate.dedupe_verdict == "new"),
        "candidates_possible_duplicate": sum(
            1 for candidate in candidates if candidate.dedupe_verdict == "possible_duplicate"
        ),
        "candidates_existing": sum(1 for candidate in candidates if candidate.dedupe_verdict == "existing"),
    }


def short_title(title: str, limit: int = 64) -> str:
    """Return a table-safe short title."""
    cleaned = title.replace("|", "\\|").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "\u2026"


def top_title_labels(candidates: list[Candidate]) -> dict[str, str]:
    """Return markdown link labels for the ranked table."""
    labels: dict[str, str] = {}
    for candidate in candidates:
        url = source_url_for(candidate)
        label = short_title(candidate.title)
        labels[candidate.id] = f"[{label}]({url})" if url else label
    return labels


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


@dataclass
class ArtefactPaths:
    """The three artefacts written by a run."""

    candidates_json: Path
    triage_md: Path
    proposed_json: Path


def artefact_paths(date: str, out_dir: Path | None = None) -> ArtefactPaths:
    """Return the artefact paths for *date*."""
    directory = out_dir if out_dir is not None else OUT_DIR
    return ArtefactPaths(
        candidates_json=directory / f"{date}-snowball-candidates.json",
        triage_md=directory / f"{date}-snowball-candidates.md",
        proposed_json=directory / f"{date}-snowball-proposed-entries.json",
    )


def resolve_direction(value: str) -> list[str]:
    """Return the list of snowball directions for the CLI value."""
    if value == "both":
        return ["backward", "forward"]
    return [value]


def provider_plan(name: str, direction: str) -> list[str]:
    """Return the provider order for *direction* under the CLI provider selection.

    ``auto`` keeps OpenAlex first and falls back to Semantic Scholar; Crossref
    is only useful for backward traversal of a DOI-registered seed, because it
    has no citing-works endpoint.
    """
    if name == "openalex":
        return [PROVIDER_OPENALEX]
    if name == "s2":
        return [PROVIDER_S2]
    if direction == "backward":
        return [PROVIDER_OPENALEX, PROVIDER_S2, PROVIDER_CROSSREF]
    return [PROVIDER_OPENALEX, PROVIDER_S2]


def provider_mix(seeds: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Count the provider that answered each seed resolution and direction."""
    mix: dict[str, dict[str, int]] = {"resolution": {}, "backward": {}, "forward": {}}
    for record in seeds:
        resolution = str(record.get("resolution", ""))
        key = resolution.split("-", maxsplit=1)[0] if resolution else "unresolved"
        mix["resolution"][key] = mix["resolution"].get(key, 0) + 1
        for direction in ("backward", "forward"):
            detail = record.get(direction)
            if not isinstance(detail, dict):
                continue
            provider = str(detail.get("provider") or "none")
            mix[direction][provider] = mix[direction].get(provider, 0) + 1
    return mix


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Snowball the Conflux literature corpus with key-free bibliographic APIs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--direction",
        choices=["backward", "forward", "both"],
        default="both",
        help="which citation direction to traverse (default: both)",
    )
    parser.add_argument("--seed-limit", type=int, default=None, help="process only the first N seeds of the queue")
    parser.add_argument("--keys", default="", help="comma-separated seed keys to restrict the run to")
    parser.add_argument(
        "--graph-provider",
        choices=("auto", "openalex", "s2"),
        default="auto",
        help=(
            "citation-graph provider order: auto = OpenAlex then Semantic Scholar "
            "(plus Crossref references for DOI seeds), openalex = OpenAlex only, s2 = Semantic Scholar only"
        ),
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="on --resume, retry directions whose checkpointed attempt recorded an error",
    )
    parser.add_argument(
        "--s2-interval",
        type=float,
        default=1.5,
        help="seconds between Semantic Scholar calls (default: 1.5)",
    )
    parser.add_argument("--resume", action="store_true", help="continue the checkpointed run in .local/snowball-state.json")
    parser.add_argument("--refresh", action="store_true", help="ignore the response cache and refetch every URL")
    parser.add_argument("--dry-run", action="store_true", help="print the seed plan without any network call or write")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="with --resume: skip traversal and rebuild the artefacts from the checkpointed state",
    )
    parser.add_argument("--date", default="", help="artefact date prefix (default: today, UTC)")
    parser.add_argument("--propose-limit", type=int, default=25, help="maximum proposed corpus entries (default: 25)")
    parser.add_argument("--backward-cap", type=int, default=150, help="maximum references fetched per seed (default: 150)")
    parser.add_argument("--forward-cap", type=int, default=100, help="maximum citing works fetched per seed (default: 100)")
    parser.add_argument("--min-interval", type=float, default=1.2, help="seconds between OpenAlex calls (default: 1.2)")
    parser.add_argument("--max-backoff", type=float, default=45.0, help="cap for 429/5xx backoff in seconds (default: 45)")
    parser.add_argument(
        "--blocked-interval",
        type=float,
        default=10.0,
        help="per-provider pacing after a 429 response (default: 10)",
    )
    parser.add_argument(
        "--hard-block-seconds",
        type=float,
        default=300.0,
        help="pause an endpoint for the run when a 429 asks for a longer wait (default: 300)",
    )
    parser.add_argument("--retries", type=int, default=2, help="retries per rate-limited request (default: 2)")
    parser.add_argument("--timeout", type=int, default=30, help="per-request timeout in seconds (default: 30)")
    parser.add_argument("--mailto", default=DEFAULT_MAILTO, help="contact address sent to OpenAlex/Crossref")
    parser.add_argument("--cache-dir", default="", help="override the response cache directory")
    parser.add_argument(
        "--out-dir",
        default="",
        help="override the artefact directory (default: research/reports/analysis)",
    )
    return parser


def corpus_digest() -> str:
    """Return the SHA-256 of the corpus file."""
    return hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest()


def seed_stream_map(seeds: list[Seed]) -> dict[str, str]:
    """Return the lane label per seed key."""
    return {seed.key: seed.stream for seed in seeds}


def run(args: argparse.Namespace) -> int:
    """Execute one snowball pass and write the artefacts."""
    date = args.date or dt.datetime.now(dt.UTC).date().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        print(f"[snowball] invalid --date {date!r}: expected YYYY-MM-DD", file=sys.stderr)
        return 1
    corpus = load_corpus()
    entries = [entry for entry in corpus.get("entries", []) if isinstance(entry, dict)]
    corpus_index = CorpusIndex(entries)
    only_keys = {key.strip() for key in args.keys.split(",") if key.strip()} or None
    seeds = select_seeds(entries, only_keys=only_keys, seed_limit=args.seed_limit)
    if not seeds:
        print("[snowball] no seeds matched the selection", file=sys.stderr)
        return 1
    directions = resolve_direction(args.direction)
    provider_plans = {direction: provider_plan(args.graph_provider, direction) for direction in ("backward", "forward")}
    paths = artefact_paths(date, Path(args.out_dir) if args.out_dir else None)
    streams = seed_stream_map(seeds)

    if args.render_only and not args.resume:
        print("[snowball] --render-only needs --resume: refusing to overwrite artefacts from an empty state", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[snowball] dry run: {len(seeds)} seeds, directions={directions}, no network calls, no writes")
        for seed in seeds:
            identity = (seed.doi and f"doi:{seed.doi}") or (seed.arxiv_id and f"arxiv:{seed.arxiv_id}") or (
                "title:" + normalise_title(seed.title)[:40]
            )
            print(f"[snowball]   {seed.key:24s} priority={seed.priority or '-':1s} verified={seed.verified_method:14s} identity={identity}")
        print(f"[snowball] provider plan: {provider_plans}")
        print(f"[snowball] dry run complete: would write {paths.candidates_json.name}, {paths.triage_md.name}, {paths.proposed_json.name}")
        return 0

    client = CachedHttp(
        Path(args.cache_dir) if args.cache_dir else CACHE_DIR,
        timeout=args.timeout,
        refresh=args.refresh,
        dry_run=False,
        min_intervals={
            PROVIDER_OPENALEX: args.min_interval,
            PROVIDER_OPENALEX_LIST: args.min_interval,
            PROVIDER_S2: args.s2_interval,
            PROVIDER_CROSSREF: 1.2,
            PROVIDER_ARXIV: 3.1,
        },
        blocked_interval=args.blocked_interval,
        max_backoff=args.max_backoff,
        hard_block_seconds=args.hard_block_seconds,
        retries=args.retries,
        mailto=args.mailto,
    )

    state: dict[str, Any] = {"seeds": {}, "candidate_store": {}, "stats": {}, "paused_providers": {}}
    if args.resume:
        loaded = load_state(STATE_PATH)
        state["seeds"] = loaded["seeds"]
        state["stats"] = loaded["stats"]
        state["paused_providers"] = loaded["paused_providers"]
        for item in loaded["candidates"]:
            candidate = candidate_from_state(item)
            state["candidate_store"][candidate.identity()] = candidate
        print(f"[snowball] resumed: {len(state['seeds'])} seeds, {len(state['candidate_store'])} candidates", flush=True)
    else:
        print(f"[snowball] fresh run: {len(seeds)} seeds, directions={directions}", flush=True)
    print(f"[snowball] provider plan: {provider_plans}", flush=True)

    used_keys = set(corpus_index.titles.values()) | set(corpus_index.dois.values()) | set(corpus_index.arxivs.values())
    used_keys |= {str(entry.get("key", "")) for entry in entries}

    render_kwargs: dict[str, Any] = {
        "date": date,
        "paths": paths,
        "state": state,
        "seeds": seeds,
        "corpus_index": corpus_index,
        "streams": streams,
        "entries": entries,
        "used_keys": used_keys,
        "client": client,
        "provider_plans": provider_plans,
        "propose_limit": args.propose_limit,
    }

    if args.render_only:
        if not state["seeds"]:
            print("[snowball] --render-only found no checkpointed seeds", file=sys.stderr)
            return 1
        print("[snowball] render-only: artefacts rebuilt from the checkpointed state", flush=True)
    else:
        for position, seed in enumerate(seeds, start=1):
            process_seed(
                client,
                seed,
                directions=directions,
                backward_cap=args.backward_cap,
                forward_cap=args.forward_cap,
                mailto=args.mailto,
                providers=provider_plans,
                retry_errors=args.retry_errors,
                state=state,
            )
            counts, _uncitable, _errors = write_run_artefacts(**render_kwargs)
            record = state["seeds"][seed.key]
            print(
                f"[snowball] {position}/{len(seeds)} seed={seed.key} status={record.get('status')} "
                f"backward={(record.get('backward') or {}).get('fetched', 0)} "
                f"forward={(record.get('forward') or {}).get('fetched', 0)} "
                f"candidates={counts['candidates_total']} new={counts['candidates_new']} "
                f"requests={client.stats['requests']} cache_hits={client.stats['cache_hits']}",
                flush=True,
            )

    # Always render once more after the traversal: this keeps the artefacts
    # current for --render-only, and it re-validates the proposal in-process.
    counts, _uncitable, schema_errors = write_run_artefacts(**render_kwargs)
    print(f"[snowball] done: {json.dumps(counts, sort_keys=True)}")
    print(f"[snowball] http: {json.dumps(client.stats, sort_keys=True)}")
    if client.paused_providers:
        print(f"[snowball] providers paused mid-run: {client.paused_providers}", file=sys.stderr)
    if schema_errors:
        print("[snowball] proposed entries failed schema validation:", file=sys.stderr)
        for error in schema_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    return 0


def write_run_artefacts(
    *,
    date: str,
    paths: ArtefactPaths,
    state: dict[str, Any],
    seeds: list[Seed],
    corpus_index: CorpusIndex,
    streams: dict[str, str],
    entries: list[dict[str, Any]],
    used_keys: set[str],
    client: CachedHttp,
    provider_plans: dict[str, list[str]],
    propose_limit: int,
) -> tuple[dict[str, int], dict[str, int], list[str]]:
    """Recompute the ranking and write the three artefacts.

    Returns the coverage counters, the uncitable-candidate reasons, and the
    schema errors of the proposed entries (empty when the proposal validates).
    """
    storable = list(state["candidate_store"].values())
    candidates, uncitable = refresh_candidates(storable, corpus_index, streams)
    counts = compute_counts(state["seeds"], candidates, len(seeds))
    counts["candidates_uncitable"] = sum(uncitable.values())
    seed_records = [compact_seed_record(state["seeds"][seed.key]) for seed in seeds if seed.key in state["seeds"]]
    digest = corpus_digest()
    # The API footprint of a resumed sweep spans processes, so the checkpoint
    # carries the running totals and this process adds its own on top.  A
    # --render-only pass therefore reports the traversal, not zero.
    stats = dict(state.get("stats") or {})
    for key, value in client.stats.items():
        stats[key] = stats.get(key, 0) + int(value)
    paused = {**(state.get("paused_providers") or {}), **client.paused_providers}
    state["stats"] = stats
    state["paused_providers"] = paused
    candidates_doc = render_candidates_document(
        date=date,
        generator="scripts/snowball_literature.py",
        corpus_sha256=digest,
        corpus_entries=len(entries),
        seeds=seed_records,
        candidates=candidates,
        counts=counts,
        client_stats=stats,
        paused_providers=paused,
        provider_plans=provider_plans,
        provider_mix=provider_mix(seed_records),
    )
    triage = render_triage_markdown(
        date=date,
        generator="scripts/snowball_literature.py",
        corpus_sha256=digest,
        corpus_entries=len(entries),
        seeds=seed_records,
        candidates=candidates,
        counts=counts,
        client_stats=stats,
        proposed_count=min(propose_limit, counts["candidates_new"]),
        top_titles=top_title_labels(candidates),
        provider_mix=provider_mix(seed_records),
        paused_providers=paused,
        uncitable=uncitable,
    )
    proposed, schema_errors = render_proposed_entries(
        date=date,
        generator="scripts/snowball_literature.py",
        candidates=candidates,
        limit=propose_limit,
        used_keys=set(used_keys),
    )
    write_json(paths.candidates_json, candidates_doc)
    write_markdown(paths.triage_md, triage)
    write_json(paths.proposed_json, proposed)
    save_state(
        STATE_PATH,
        {"seeds": state["seeds"], "candidates": storable, "stats": stats, "paused_providers": paused},
    )
    return counts, uncitable, schema_errors


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run."""
    args = build_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
