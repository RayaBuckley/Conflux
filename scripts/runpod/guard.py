#!/usr/bin/env python
"""Cost guard and identity gate for Conflux RunPod operations.

Usage:
    python scripts/runpod/guard.py status
    python scripts/runpod/guard.py report --days 7
    python scripts/runpod/guard.py preflight --hours 4
    python scripts/runpod/guard.py create --run-id pilot-1 --hours 2 --image IMG --yes
    python scripts/runpod/guard.py stop --run-id pilot-1 --yes
    python scripts/runpod/guard.py terminate --run-id pilot-1 --yes
    python scripts/runpod/guard.py stop-all --yes
    python scripts/runpod/guard.py watch --interval 60

Safety model (fail closed):
  * A Conflux pod has a name matching ``^conflux-...`` AND either the env marker
    ``CONFLUX_MANAGED=1`` or a pod id in a live, recent ledger entry (state created
    or running, recorded within ``TRUST_WINDOW_DAYS``). Both conditions require the
    name, so a foreign pod can never qualify.
  * Foreign pods belong to other users of the shared RunPod account. This tool never
    names, lists, stops, starts or terminates them, and it does not repeat a foreign
    pod id, name or environment value anywhere - not on stdout, not on stderr and not
    in the audit log, including in a refusal. They appear only as aggregate counts and
    hourly cost. A vendor error body is summarised - status code, body size and JSON
    key names - and never quoted, because it can carry another tenant's pod identity.
  * Caps enforced before any API mutation: one GPU, H100 family only, one Conflux pod
    at a time, per-pod hour and spend caps, per-day spend cap. Configuration may lower
    these; the absolute limits in this module can never be raised, and a non-finite
    budget value is rejected instead of clamped.
  * ``create``, ``stop``, ``terminate`` and ``stop-all`` require ``--yes`` and write
    the audit record before the API call. Three stops happen without ``--yes`` on
    purpose, because each can only stop our own pods and only reduces spend:
    ``watch`` (the expiry watchdog), the compensating stop of a pod that fails the
    identity recheck after creation, and the compensating stop of a pod whose real
    rate exceeds the per-pod cap. None of the three ever creates, terminates or
    deletes anything, and every one is written to the audit log.

Requires RUNPOD_API_KEY in the environment (see ~/.config/conflux/credentials.env).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as HttpRequest
from urllib.request import urlopen

API_BASE = "https://rest.runpod.io/v1"
USER_AGENT = "Conflux-Guard/1.0 (local ops tool)"
REPO_ROOT = Path(__file__).resolve().parents[2]
# State lives in one gitignored directory. Every path below is read at call time,
# never captured as a function default, so a caller or a test can redirect the whole
# state directory with one monkeypatch. A captured default would send a test's audit
# records into the live audit log and make the trail lie about what ran.
STATE_DIR = REPO_ROOT / ".local" / "runpod"
LEDGER_PATH = STATE_DIR / "ledger.json"
AUDIT_PATH = STATE_DIR / "audit.jsonl"
BUDGET_PATH = STATE_DIR / "budget.json"
REPORT_DIR = STATE_DIR / "reports"

LIVE_STATES = frozenset({"created", "running"})
# A ledger entry older than this, or already finished, must not authorise a stop:
# pod ids can be recycled, and the ledger is a local file.
TRUST_WINDOW_DAYS = 7
# Two uptime readings below this difference are treated as the same figure. The vendor's
# start stamp resets on a container restart and can be missing, so ours is preferred
# (RC-2026-10-15-10) and a real disagreement is printed rather than hidden.
VENDOR_STAMP_DISAGREEMENT_HOURS = 0.1
NAME_PREFIX = "conflux-"
# Lower-case letters, digits, dots and hyphens only: model slugs such as
# `qwen2.5-7b-instruct` are allowed, while `conflux-Bad_Name` and anything with
# uppercase, underscore or whitespace stays foreign. The name alone never qualifies
# a pod; the marker or a live ledger entry must also match.
NAME_PATTERN = re.compile(r"^conflux-[a-z0-9][a-z0-9.-]{1,60}$")
MARKER_KEY = "CONFLUX_MANAGED"
MARKER_VALUE = "1"

# Verified against the vendor's live enum (GET /v1/openapi.json, 2026-10-09).
H100_TYPES: tuple[str, ...] = (
    "NVIDIA H100 80GB HBM3",
    "NVIDIA H100 NVL",
    "NVIDIA H100 PCIe",
)

# Absolute limits. Configuration may lower these but never raise them.
ABSOLUTE_MAX_GPU_COUNT = 1
ABSOLUTE_MAX_HOURS = 12.0
ABSOLUTE_MAX_USD_PER_POD = 50.0
INT_BUDGET_KEYS = frozenset({"max_gpu_count", "max_concurrent_pods", "container_disk_gb", "volume_gb"})
FLOAT_BUDGET_KEYS = frozenset({"max_hours_per_pod", "max_usd_per_pod", "max_usd_per_day"})
ABSOLUTE_MAX_CONCURRENT = 1
DEFAULT_IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
EXIT_REFUSED = 2
EXIT_API_ERROR = 3


class GuardError(RuntimeError):
    """A refusal or operational failure that must stop the command."""


# --------------------------------------------------------------------------
# Pod identity. This is the safety boundary: everything mutating goes through
# classify() plus resolve_targets().
# --------------------------------------------------------------------------


def pod_id(pod: Mapping[str, Any]) -> str:
    return str(pod.get("id") or "")


def pod_name(pod: Mapping[str, Any]) -> str:
    return str(pod.get("name") or "")


def pod_state(pod: Mapping[str, Any]) -> str:
    return str(pod.get("desiredStatus") or "UNKNOWN").upper()


def pod_env_keys(pod: Mapping[str, Any]) -> tuple[str, ...]:
    env = pod.get("env")
    if isinstance(env, Mapping):
        return tuple(sorted(str(k) for k in env))
    return ()


def verify_created_pod(
    expected_name: str,
    expected_image: str,
    refreshed: Mapping[str, Any],
) -> tuple[bool, str]:
    """Confirm a freshly created pod is the pod we asked for.

    ``classify`` cannot carry this check. The id of a pod we just created is in
    our hands, so passing it to ``classify`` as a trusted id makes the ledger
    clause true whatever the API returned; only the naming convention would
    remain. This check compares the values we sent instead:

    * the name must equal the name we asked for, exactly;
    * the image must equal the requested image, when the listing reports one;
    * if the listing carries our environment namespace at all, the management
      marker must be present, because a Conflux-named pod without it is not
      ours to spend on.

    A listing that omits ``env`` entirely is accepted, and the returned evidence
    says so, because the vendor listing does not always echo the environment.
    """
    name = pod_name(refreshed)
    if name != expected_name:
        return False, f"the API returned name {name!r} instead of {expected_name!r}"
    image = str(refreshed.get("imageName") or "")
    if image and expected_image and image != expected_image:
        return False, f"the API returned image {image!r} instead of {expected_image!r}"
    env = refreshed.get("env")
    if isinstance(env, Mapping):
        namespace = f"{MARKER_KEY.split('_', maxsplit=1)[0]}_"
        carries_ours = any(str(key).startswith(namespace) for key in env)
        if carries_ours and str(env.get(MARKER_KEY, "")).strip() != MARKER_VALUE:
            return False, "an environment block came back without the management marker"
        if carries_ours:
            return True, "exact name, requested image, management marker"
        return True, "exact name, requested image (no Conflux environment keys reported)"
    return True, "exact name, requested image (no environment block reported)"


def classify(pod: Mapping[str, Any], trusted_ids: Iterable[str] = ()) -> tuple[bool, str]:
    """Return (is_conflux_pod, evidence). Fails closed: name is mandatory."""
    name = pod_name(pod).strip()
    if not NAME_PATTERN.match(name):
        return False, "name does not match the Conflux naming convention"
    env = pod.get("env")
    marked = isinstance(env, Mapping) and str(env.get(MARKER_KEY, "")).strip() == MARKER_VALUE
    known = pod_id(pod) in set(trusted_ids)
    if marked and known:
        return True, "name + CONFLUX_MANAGED marker + ledger record"
    if marked:
        return True, "name + CONFLUX_MANAGED marker"
    if known:
        return True, "name + ledger record"
    return False, "name matches but no marker and no ledger record"


def managed_pods(pods: Sequence[Mapping[str, Any]], trusted_ids: Iterable[str] = ()) -> list[Mapping[str, Any]]:
    return [pod for pod in pods if classify(pod, trusted_ids)[0]]


def foreign_summary(pods: Sequence[Mapping[str, Any]], trusted_ids: Iterable[str] = ()) -> dict[str, object]:
    """Aggregate-only view of pods we do not own. Never an id, name or env."""
    foreign = [pod for pod in pods if not classify(pod, trusted_ids)[0]]
    by_state: dict[str, int] = {}
    for pod in foreign:
        state = pod_state(pod)
        by_state[state] = by_state.get(state, 0) + 1
    running = [pod for pod in foreign if pod_state(pod) == "RUNNING"]
    return {
        "pods_total": len(foreign),
        "pods_running": len(running),
        "hourly_usd_running": round(sum(hourly_rate(pod) for pod in running), 2),
        "by_state": dict(sorted(by_state.items())),
    }


def hourly_rate(pod: Mapping[str, Any]) -> float:
    for key in ("adjustedCostPerHr", "costPerHr"):
        value = pod.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    machine = pod.get("machine")
    if isinstance(machine, Mapping):
        for key, count_key in (("costPerHr", None), ("currentPricePerGpu", "minPodGpuCount")):
            value = machine.get(key)
            if isinstance(value, (int, float)):
                count = pod_gpu_count(pod) if count_key else 1
                return float(value) * max(count, 1)
    gpu = pod.get("gpu")
    if isinstance(gpu, Mapping):
        count = pod_gpu_count(pod)
        for key in ("securePrice", "communityPrice"):
            value = gpu.get(key)
            if isinstance(value, (int, float)):
                return float(value) * max(count, 1)
    return 0.0


def pod_gpu_count(pod: Mapping[str, Any]) -> int:
    for source in (pod, pod.get("gpu"), pod.get("machine")):
        if isinstance(source, Mapping):
            value = source.get("count", source.get("gpuCount"))
            if isinstance(value, (int, float)):
                return int(value)
    return 0


def pod_gpu_type(pod: Mapping[str, Any]) -> str:
    gpu = pod.get("gpu")
    if isinstance(gpu, Mapping):
        for key in ("displayName", "id"):
            value = gpu.get(key)
            if value:
                return str(value)
    machine = pod.get("machine")
    if isinstance(machine, Mapping):
        for key in ("gpuDisplayName", "gpuTypeId"):
            value = machine.get(key)
            if value:
                return str(value)
    return "unknown"


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def started_at(pod: Mapping[str, Any]) -> datetime | None:
    return parse_time(pod.get("lastStartedAt")) or parse_time(pod.get("createdAt"))


def uptime_hours(pod: Mapping[str, Any], now: datetime) -> float:
    start = started_at(pod)
    if start is None:
        return 0.0
    return max(0.0, (now - start).total_seconds() / 3600.0)


def spend_estimate(pod: Mapping[str, Any], now: datetime) -> float:
    if pod_state(pod) != "RUNNING":
        return 0.0
    return round(hourly_rate(pod) * uptime_hours(pod, now), 4)


def public_view(pod: Mapping[str, Any], now: datetime) -> dict[str, object]:
    """Conflux-pod detail with secrets removed: env values are never returned."""
    return {
        "id": pod_id(pod),
        "name": pod_name(pod),
        "state": pod_state(pod),
        "gpu": pod_gpu_type(pod),
        "gpu_count": pod_gpu_count(pod),
        "usd_per_hr": round(hourly_rate(pod), 4),
        "started_at": str(started_at(pod) or ""),
        "uptime_hours": round(uptime_hours(pod, now), 3),
        "est_spend_usd": spend_estimate(pod, now),
        "spot": bool(pod.get("interruptible")),
        "locked": bool(pod.get("locked")),
        "env_keys": list(pod_env_keys(pod)),
    }


# --------------------------------------------------------------------------
# Budget, preflight decisions, ledger and audit trail.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Budget:
    """Cost and concurrency caps. Configuration may lower, never raise."""

    max_gpu_count: int = 1
    allowed_gpu_types: tuple[str, ...] = H100_TYPES
    max_concurrent_pods: int = 1
    max_hours_per_pod: float = 4.0
    max_usd_per_pod: float = 10.0
    max_usd_per_day: float = 20.0
    default_image: str = DEFAULT_IMAGE
    container_disk_gb: int = 50
    volume_gb: int = 20
    volume_mount: str = "/workspace"
    ports: tuple[str, ...] = ("22/tcp",)
    cloud_type: str = "SECURE"


def _finite_number(value: object, default: float, key: str, notes: list[str]) -> float:
    """Coerce a budget value to a finite float. NaN and infinity are rejected, not clamped.

    ``min(nan, cap)`` returns nan in Python, so a NaN in the budget file would silently
    defeat every money cap. A bad value falls back to the default and is reported.
    """
    try:
        number = float(str(value)) if isinstance(value, str) else float(cast("float", value))
    except (TypeError, ValueError):
        notes.append(f"ignored {key}: not a number")
        return default
    if not math.isfinite(number):
        notes.append(f"ignored {key}: not a finite number")
        return default
    return number


def _positive_int(value: object, default: int, key: str, notes: list[str]) -> int:
    """Coerce a budget value to an int of at least 1, rejecting NaN, infinity and junk."""
    return max(int(_finite_number(value, float(default), key, notes)), 1)


def load_budget(path: Path | None = None) -> tuple[Budget, list[str]]:
    """Load the local budget file, clamping every value to the absolute limits."""
    path = BUDGET_PATH if path is None else path
    budget = Budget()
    notes: list[str] = []
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GuardError(f"budget file {path} is not readable JSON: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise GuardError(f"budget file {path} must contain a JSON object")
        known = {f for f in Budget.__dataclass_fields__ if hasattr(budget, f)}
        updates: dict[str, object] = {}
        for key, value in raw.items():
            if key not in known:
                notes.append(f"ignored unknown budget key {key!r}")
                continue
            if key == "allowed_gpu_types":
                if isinstance(value, list) and value:
                    updates[key] = tuple(str(v) for v in value)
                else:
                    notes.append("ignored allowed_gpu_types: must be a non-empty list")
                continue
            if key in INT_BUDGET_KEYS:
                updates[key] = _positive_int(value, cast("int", getattr(budget, key)), key, notes)
                continue
            if key in FLOAT_BUDGET_KEYS:
                updates[key] = _finite_number(value, cast("float", getattr(budget, key)), key, notes)
                continue
            updates[key] = value
        budget = replace(budget, **updates)  # type: ignore[arg-type]
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(budget), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        notes.append(f"wrote default budget to {path}")

    # Values are re-sanitised here as well as on load, because a Budget can also be
    # constructed directly (by code or by a future caller) with a NaN field.
    clamped = Budget(
        max_gpu_count=min(_positive_int(budget.max_gpu_count, 1, "max_gpu_count", notes), ABSOLUTE_MAX_GPU_COUNT),
        allowed_gpu_types=tuple(t for t in budget.allowed_gpu_types if t in H100_TYPES) or H100_TYPES,
        max_concurrent_pods=min(
            _positive_int(budget.max_concurrent_pods, 1, "max_concurrent_pods", notes),
            ABSOLUTE_MAX_CONCURRENT,
        ),
        max_hours_per_pod=min(
            _finite_number(budget.max_hours_per_pod, 1.0, "max_hours_per_pod", notes),
            ABSOLUTE_MAX_HOURS,
        ),
        max_usd_per_pod=min(
            _finite_number(budget.max_usd_per_pod, 1.0, "max_usd_per_pod", notes),
            ABSOLUTE_MAX_USD_PER_POD,
        ),
        max_usd_per_day=min(
            _finite_number(budget.max_usd_per_day, 1.0, "max_usd_per_day", notes),
            ABSOLUTE_MAX_USD_PER_POD * 2,
        ),
        default_image=budget.default_image,
        container_disk_gb=max(_positive_int(budget.container_disk_gb, 10, "container_disk_gb", notes), 10),
        volume_gb=max(_positive_int(budget.volume_gb, 10, "volume_gb", notes), 10),
        volume_mount=budget.volume_mount,
        ports=tuple(budget.ports) or ("22/tcp",),
        cloud_type=budget.cloud_type if budget.cloud_type in {"SECURE", "COMMUNITY"} else "SECURE",
    )
    if clamped != budget:
        notes.append("some budget values were clamped to the absolute limits")
    return clamped, notes


@dataclass(frozen=True)
class PodRequest:
    """A proposed pod creation."""

    run_id: str
    hours: float
    gpu_type: str
    assumed_rate_usd_per_hr: float
    gpu_count: int = 1
    spot: bool = False

    @property
    def name_prefix(self) -> str:
        return f"{NAME_PREFIX}{self.run_id}-"

    @property
    def projected_usd(self) -> float:
        return round(self.assumed_rate_usd_per_hr * self.hours, 2)


def rfc3339(moment: datetime) -> str:
    """Format for the vendor API, which rejects '+00:00' and microseconds."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def assumed_rate(gpu_type: str, pods: Sequence[Mapping[str, Any]], ledger: Ledger | None = None) -> float | None:
    """Best evidence for this GPU type's hourly rate, or None if nothing is known.

    The list endpoint does not report a GPU type, so the reliable source is this
    machine's own ledger of pods it created. Falling back to the advertised rate
    of a matching pod only works when the API does return the type.
    """
    if ledger is not None:
        recorded = sorted(
            entry.actual_rate_usd_per_hr
            for entry in ledger.entries
            if entry.gpu_type == gpu_type and entry.actual_rate_usd_per_hr > 0
        )
        if recorded:
            return recorded[len(recorded) // 2]
    rates = sorted(
        hourly_rate(pod) for pod in pods if pod_gpu_type(pod) == gpu_type and hourly_rate(pod) > 0
    )
    return rates[len(rates) // 2] if rates else None


def refusals(
    pods: Sequence[Mapping[str, Any]],
    budget: Budget,
    request: PodRequest,
    now: datetime,
    trusted_ids: Iterable[str] = (),
    spend_today_usd: float = 0.0,
) -> list[str]:
    """Every reason this request must not proceed. Empty list means it may."""
    reasons: list[str] = []
    if not NAME_PATTERN.match(request.name_prefix + "x"):
        reasons.append(f"run id {request.run_id!r} does not form a valid Conflux pod name")
    if request.gpu_count != 1:
        reasons.append(f"gpu_count must be 1, not {request.gpu_count}")
    if request.gpu_count > min(budget.max_gpu_count, ABSOLUTE_MAX_GPU_COUNT):
        reasons.append(f"gpu_count {request.gpu_count} exceeds the configured maximum {budget.max_gpu_count}")
    if request.gpu_type not in H100_TYPES:
        reasons.append(f"gpu type {request.gpu_type!r} is not in the allowed H100 set {list(H100_TYPES)}")
    if request.gpu_type not in budget.allowed_gpu_types:
        reasons.append(f"gpu type {request.gpu_type!r} is not in the configured allow list")
    if not 0 < request.hours <= min(budget.max_hours_per_pod, ABSOLUTE_MAX_HOURS):
        reasons.append(f"hours {request.hours} must be > 0 and <= {budget.max_hours_per_pod}")
    if request.projected_usd > min(budget.max_usd_per_pod, ABSOLUTE_MAX_USD_PER_POD):
        reasons.append(
            f"projected spend ${request.projected_usd:.2f} exceeds the per-pod cap ${budget.max_usd_per_pod:.2f}",
        )
    if spend_today_usd + request.projected_usd > budget.max_usd_per_day:
        reasons.append(
            f"today's spend ${spend_today_usd:.2f} plus ${request.projected_usd:.2f} exceeds the daily cap "
            f"${budget.max_usd_per_day:.2f}",
        )
    live = [pod for pod in managed_pods(pods, trusted_ids) if pod_state(pod) == "RUNNING"]
    if len(live) >= min(budget.max_concurrent_pods, ABSOLUTE_MAX_CONCURRENT):
        names = ", ".join(pod_name(pod) for pod in live)
        reasons.append(f"a Conflux pod is already running ({names}); stop it first - one pod at a time")
    return reasons


@dataclass
class LedgerEntry:
    run_id: str
    pod_id: str
    name: str
    created_at: str
    expires_at: str
    gpu_type: str
    assumed_rate_usd_per_hr: float
    actual_rate_usd_per_hr: float
    planned_hours: float
    planned_usd: float
    image: str
    spot: bool
    state: str = "created"
    stopped_at: str = ""
    note: str = ""

    def wall_clock_hours(self, now: datetime) -> float:
        """Hours this pod existed, from the stamps this machine wrote itself.

        The vendor's start stamp resets when a container restarts and can be missing
        entirely, so it understates a pod's age (RC-2026-10-15-10). ``created_at`` and
        ``stopped_at`` are written locally at create and stop time, so they are the wall
        clock; a live entry is measured up to ``now``.
        """
        started = parse_time(self.created_at)
        if started is None:
            return 0.0
        ended = parse_time(self.stopped_at) or now
        return max(0.0, (ended - started).total_seconds() / 3600.0)

    def wall_clock_usd(self, now: datetime) -> float:
        """Cost of the pod's measured life at the rate this machine recorded."""
        rate = self.actual_rate_usd_per_hr or self.assumed_rate_usd_per_hr
        return round(rate * self.wall_clock_hours(now), 4)


class Ledger:
    """Local record of every pod this machine created. Gitignored under .local/."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = LEDGER_PATH if path is None else path
        self.entries: list[LedgerEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        records = raw.get("entries") if isinstance(raw, Mapping) else None
        if not isinstance(records, list):
            return
        for record in records:
            if isinstance(record, Mapping):
                fields = {k: v for k, v in record.items() if k in LedgerEntry.__dataclass_fields__}
                try:
                    self.entries.append(LedgerEntry(**fields))
                except TypeError:
                    continue

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "entries": [asdict(entry) for entry in self.entries]}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def add(self, entry: LedgerEntry) -> None:
        self.entries.append(entry)
        self.save()

    def update(self, pod_id_value: str, **changes: Any) -> LedgerEntry | None:
        for index, entry in enumerate(self.entries):
            if entry.pod_id == pod_id_value:
                updated = replace(entry, **changes)
                self.entries[index] = updated
                self.save()
                return updated
        return None

    def by_run_id(self, run_id: str) -> LedgerEntry | None:
        for entry in self.entries:
            if entry.run_id == run_id:
                return entry
        return None

    def trusted_ids(self, now: datetime | None = None) -> frozenset[str]:
        """Ids this machine may act on: live, recent entries only.

        A finished or stale entry must not authorise anything, because pod ids can be
        recycled on a shared account. Entries within the window in a live state remain
        trusted even if the vendor omits the marker.
        """
        moment = now or datetime.now(UTC)
        window = timedelta(days=TRUST_WINDOW_DAYS)
        trusted: set[str] = set()
        for entry in self.entries:
            if not entry.pod_id or entry.state not in LIVE_STATES:
                continue
            created = parse_time(entry.created_at)
            if created is None:
                continue
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if moment - created > window:
                continue
            trusted.add(entry.pod_id)
        return frozenset(trusted)

    def live_run_ids(self) -> set[str]:
        return {entry.run_id for entry in self.entries if entry.state in LIVE_STATES}

    def spend_on(self, day: datetime) -> float:
        """Planned cost recorded for one day. The caps are checked against this figure.

        It stays plan-based on purpose: switching the caps to the wall-clock figure below
        changes when a create is refused, which is the owner's call (RC-2026-10-15-10).
        The undercount it can carry is reported, not silently enforced.
        """
        total = 0.0
        for entry in self.entries:
            created = parse_time(entry.created_at)
            if created is None or created.date() != day.date():
                continue
            if entry.state == "exited":
                total += entry.actual_rate_usd_per_hr * entry.planned_hours
            else:
                total += entry.planned_usd
        return round(total, 2)

    def wall_clock_spend(self, now: datetime) -> float:
        """Cost of every recorded pod's measured life (RC-2026-10-15-10)."""
        return round(sum(entry.wall_clock_usd(now) for entry in self.entries), 2)

    def expired(self, now: datetime) -> list[LedgerEntry]:
        return [
            entry
            for entry in self.entries
            if entry.state in {"created", "running"} and (expiry := parse_time(entry.expires_at)) is not None and expiry <= now
        ]


def pod_cost_note(pod: Mapping[str, Any], now: datetime, ledger: Ledger) -> str:
    """Uptime and cost text for one pod line, preferring this machine's own stamps.

    The vendor's start stamp resets on a container restart and can be absent, so it can
    understate a pod's age by hours (RC-2026-10-15-10). When the ledger knows the pod,
    the wall clock is printed and any real disagreement with the vendor stamp is shown
    beside it; a pod the ledger does not know is labelled with the weaker source.
    """
    vendor_hours = uptime_hours(pod, now)
    entry = next((item for item in ledger.entries if item.pod_id == pod_id(pod)), None)
    if entry is None:
        return f"uptime={vendor_hours:.2f}h est=${spend_estimate(pod, now):.2f} (vendor stamp)"
    wall_hours = entry.wall_clock_hours(now)
    rate = entry.actual_rate_usd_per_hr or entry.assumed_rate_usd_per_hr
    cost = f"est=${entry.wall_clock_usd(now):.2f}" if rate > 0 else "est=unknown (no rate recorded)"
    note = f"uptime={wall_hours:.2f}h {cost} (wall clock)"
    if abs(wall_hours - vendor_hours) >= VENDOR_STAMP_DISAGREEMENT_HOURS:
        note += f" [vendor stamp: {vendor_hours:.2f}h]"
    return note


def audit(action: str, target: str, detail: Mapping[str, object], path: Path | None = None) -> None:
    """Append one action record. Never contains env values or credentials."""
    path = AUDIT_PATH if path is None else path
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": datetime.now(UTC).isoformat(), "action": action, "target": target, **detail}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def describe_error_body(body: bytes) -> str:
    """Summarise a vendor error body without repeating what it contains.

    The message a refusal carries reaches stderr and ``audit.jsonl``, and the account
    is shared, so a raw error body is never quoted: it can name or identify another
    tenant's pod. The status code and the shape of the body are what an operator needs
    to tell a stale key from a missing permission; the text itself stays out of our
    logs.
    """
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return ": empty response body"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return f": non-JSON response body of {len(text)} characters"
    if isinstance(parsed, Mapping):
        keys = ", ".join(sorted(str(key) for key in parsed))
        return f": JSON response body with key(s) {keys}"
    return f": JSON {type(parsed).__name__} response body"


class RunPodApi:
    """Minimal REST client. Only ever called with Conflux pod ids."""

    def __init__(self, api_key: str, base: str = API_BASE, timeout: float = 30.0) -> None:
        if not api_key:
            raise GuardError("RUNPOD_API_KEY is not set; load ~/.config/conflux/credentials.env")
        self._api_key = api_key
        self._base = base.rstrip("/")
        self._timeout = timeout

    def _request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Authorization": f"Bearer {self._api_key}", "User-Agent": USER_AGENT, "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = HttpRequest(f"{self._base}{path}", data=body, method=method, headers=headers)
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise GuardError(f"{method} {path} failed with HTTP {exc.code}{describe_error_body(exc.read())}") from exc
        except URLError as exc:
            raise GuardError(f"{method} {path} failed: {exc.reason}") from exc
        return json.loads(raw) if raw.strip() else None

    def list_pods(self) -> list[Mapping[str, Any]]:
        """Return the account's pods.

        An unexpected body is an error, never an empty list: silently reading "no pods"
        would hide a running pod from the caps and from every identity check.
        """
        data = self._request("GET", "/pods")
        if not isinstance(data, list):
            raise GuardError("pods list returned an unexpected body; refusing to continue")
        return [cast("Mapping[str, Any]", item) for item in data]

    def create_pod(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        data = self._request("POST", "/pods", payload)
        if not isinstance(data, Mapping):
            raise GuardError("create returned an unexpected body")
        return cast("Mapping[str, Any]", data)

    def stop_pod(self, pod_id_value: str) -> None:
        self._request("POST", f"/pods/{pod_id_value}/stop")

    def delete_pod(self, pod_id_value: str) -> None:
        self._request("DELETE", f"/pods/{pod_id_value}")

    def billing_pods(self, start: datetime, end: datetime) -> list[Mapping[str, Any]]:
        query = urlencode(
            {
                "bucketSize": "day",
                "startTime": rfc3339(start),
                "endTime": rfc3339(end),
                "grouping": "podId",
            },
        )
        data = self._request("GET", f"/billing/pods?{query}")
        return [cast("Mapping[str, Any]", item) for item in data] if isinstance(data, list) else []


def resolve_targets(
    pods: Sequence[Mapping[str, Any]],
    selector: str,
    trusted_ids: Iterable[str],
) -> list[Mapping[str, Any]]:
    """Map a run id or pod id to Conflux pods only, refusing anything foreign."""
    trusted = set(trusted_ids)
    matches: list[Mapping[str, Any]] = []
    for pod in pods:
        if pod_id(pod) == selector or pod_name(pod) == selector or pod_name(pod).startswith(f"{NAME_PREFIX}{selector}-"):
            matches.append(pod)
    if not matches:
        raise GuardError(f"no pod matches {selector!r} on this account")
    foreign = [pod for pod in matches if not classify(pod, trusted)[0]]
    if foreign:
        # Deliberately no ids, names or environment values here: a refusal must not
        # disclose another user's pod, and this text reaches stderr and the audit log.
        raise GuardError(
            f"refusing to act on {len(foreign)} of {len(matches)} matched pod(s) that are not Conflux pods; "
            "this tool never touches other users' pods",
        )
    return matches


# --------------------------------------------------------------------------
# Commands.
# --------------------------------------------------------------------------


def api_from_env() -> RunPodApi:
    return RunPodApi(os.environ.get("RUNPOD_API_KEY", ""))


def hf_token() -> str:
    token = os.environ.get("HF_TOKEN", "")
    if token:
        return token
    for candidate in (Path.home() / ".cache" / "huggingface" / "token",):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()
    return ""


def cmd_status(_args: argparse.Namespace) -> int:
    now = datetime.now(UTC)
    ledger = Ledger()
    pods = api_from_env().list_pods()
    budget, notes = load_budget()
    trusted = ledger.trusted_ids()
    mine = managed_pods(pods, trusted)
    print(f"Conflux pods: {len(mine)}")
    running_cost = 0.0
    for pod in mine:
        view = public_view(pod, now)
        print(
            f"  - {view['name']} [{view['id']}] state={view['state']} gpu={view['gpu']} x{view['gpu_count']} "
            f"${view['usd_per_hr']}/hr {pod_cost_note(pod, now, ledger)}",
        )
        if view["state"] == "RUNNING":
            running_cost += float(cast("float", view["usd_per_hr"]))
    print(f"Conflux burn rate: ${running_cost:.2f}/hr")
    for entry in ledger.expired(now):
        print(f"  ! expired TTL: run {entry.run_id} ({entry.pod_id}) passed {entry.expires_at} - run stop")
    print(
        f"Budget: max {budget.max_concurrent_pods} pod(s), {budget.max_hours_per_pod}h, "
        f"${budget.max_usd_per_pod}/pod, ${budget.max_usd_per_day}/day, gpus={list(budget.allowed_gpu_types)}",
    )
    summary = foreign_summary(pods, trusted)
    print(
        f"Other users on this account (untouched, aggregate only): {summary['pods_running']} running of "
        f"{summary['pods_total']} total, ${summary['hourly_usd_running']}/hr, states={summary['by_state']}",
    )
    for note in notes:
        print(f"  note: {note}")
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    now = datetime.now(UTC)
    ledger = Ledger()
    pods = api_from_env().list_pods()
    budget, _ = load_budget()
    trusted = ledger.trusted_ids()
    gpu_type = args.gpu_type or budget.allowed_gpu_types[0]
    rate = float(args.assume_rate) if args.assume_rate else assumed_rate(gpu_type, pods, ledger)
    if rate is None:
        print(f"REFUSED: no rate known for {gpu_type}; pass --assume-rate USD", file=sys.stderr)
        return EXIT_REFUSED
    request = PodRequest(run_id=args.run_id, hours=float(args.hours), gpu_type=gpu_type, assumed_rate_usd_per_hr=rate)
    reasons = refusals(pods, budget, request, now, trusted, ledger.spend_on(now))
    print(f"Request: {request.run_id} {request.gpu_type} x{request.gpu_count} for {request.hours}h "
          f"at ${rate:.2f}/hr = ${request.projected_usd:.2f}")
    if reasons:
        for reason in reasons:
            print(f"REFUSED: {reason}")
        return EXIT_REFUSED
    print("PASS: within budget, no Conflux pod running")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    now = datetime.now(UTC)
    ledger = Ledger()
    budget, _ = load_budget()
    gpu_type = args.gpu_type or budget.allowed_gpu_types[0]
    api = api_from_env()
    pods = api.list_pods()
    trusted = ledger.trusted_ids()
    rate = float(args.assume_rate) if args.assume_rate else assumed_rate(gpu_type, pods, ledger)
    if rate is None:
        print(f"REFUSED: no rate known for {gpu_type}; pass --assume-rate USD", file=sys.stderr)
        return EXIT_REFUSED
    request = PodRequest(
        run_id=args.run_id,
        hours=float(args.hours),
        gpu_type=gpu_type,
        assumed_rate_usd_per_hr=rate,
        spot=bool(args.spot),
    )
    reasons = refusals(pods, budget, request, now, trusted, ledger.spend_on(now))
    plan = (
        f"create {request.name_prefix}<stamp> gpu={gpu_type} x1 hours={request.hours} "
        f"rate=${rate:.2f}/hr projected=${request.projected_usd:.2f} image={args.image}"
    )
    if reasons:
        for reason in reasons:
            print(f"REFUSED: {reason}")
        audit("create-refused", request.run_id, {"reasons": reasons})
        return EXIT_REFUSED
    if not args.yes:
        print(f"PLAN: {plan}")
        print("add --yes to execute; refusing to spend money without it")
        return EXIT_REFUSED
    stamp = now.strftime("%Y%m%d-%H%M%S")
    name = f"{request.name_prefix}{stamp}"
    env: dict[str, str] = {
        MARKER_KEY: MARKER_VALUE,
        "CONFLUX_RUN_ID": request.run_id,
        "CONFLUX_OWNER": os.environ.get("CONFLUX_OWNER", Path.home().name),
    }
    if args.with_hf_token:
        token = hf_token()
        if not token:
            print("REFUSED: --with-hf-token but no HF_TOKEN found", file=sys.stderr)
            return EXIT_REFUSED
        env["HF_TOKEN"] = token
    for item in args.env or []:
        key, _, value = item.partition("=")
        if not key or not _:
            print(f"REFUSED: --env expects KEY=VALUE, got {item!r}", file=sys.stderr)
            return EXIT_REFUSED
        env[key] = value
    payload: dict[str, Any] = {
        "name": name,
        "imageName": args.image,
        "gpuTypeIds": [gpu_type],
        "gpuCount": 1,
        "cloudType": budget.cloud_type,
        "containerDiskInGb": budget.container_disk_gb,
        "volumeInGb": budget.volume_gb,
        "volumeMountPath": budget.volume_mount,
        "ports": list(budget.ports),
        "env": env,
        "interruptible": request.spot,
    }
    if args.cmd:
        payload["dockerStartCmd"] = list(args.cmd)
    audit("create", name, {"run_id": request.run_id, "gpu": gpu_type, "hours": request.hours,
                           "projected_usd": request.projected_usd, "env_keys": sorted(env)})
    created = api.create_pod(payload)
    created_id = pod_id(created)
    if not created_id:
        # No raw vendor body: it can echo other account data into our logs.
        raise GuardError(f"create returned no pod id (response keys: {sorted(str(k) for k in created)})")
    # Re-read the pod: confirm identity, take the real rate, and enforce the cap.
    # The recheck compares the fields we sent. Handing our own new id to classify()
    # would have satisfied its ledger clause by construction and left the naming
    # convention as the only real check.
    listed = next((pod for pod in api.list_pods() if pod_id(pod) == created_id), None)
    refreshed = listed if listed is not None else created
    ok, evidence = verify_created_pod(name, args.image, refreshed)
    if ok and listed is None:
        evidence = f"{evidence}; id was not visible in a fresh listing yet"
    if not ok:
        api.stop_pod(created_id)
        raise GuardError(f"created pod {created_id} failed the identity check ({evidence}); stopped it")
    observed_rate = hourly_rate(refreshed)
    # Never record an assumed price as an observed one: an unknown rate stays 0.0 so it
    # cannot seed later assumed_rate() calls with a number nobody measured.
    actual_rate = observed_rate if observed_rate > 0 else 0.0
    billed_rate = observed_rate or rate
    projected = round(billed_rate * request.hours, 2)
    entry = LedgerEntry(
        run_id=request.run_id,
        pod_id=created_id,
        name=name,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(hours=request.hours)).isoformat(),
        gpu_type=gpu_type,
        assumed_rate_usd_per_hr=rate,
        actual_rate_usd_per_hr=actual_rate,
        planned_hours=request.hours,
        planned_usd=projected,
        image=args.image,
        spot=request.spot,
        state="created",
        note=evidence,
    )
    ledger.add(entry)
    audit(
        "created",
        name,
        {
            "pod_id": created_id,
            "observed_usd_per_hr": observed_rate,
            "billed_usd_per_hr": billed_rate,
            "planned_usd": projected,
        },
    )
    over_cap = projected > min(budget.max_usd_per_pod, ABSOLUTE_MAX_USD_PER_POD)
    print(f"created {name} [{created_id}] at ${billed_rate:.2f}/hr, planned ${projected:.2f}, "
          f"expires {entry.expires_at}")
    print(f"stop it with: python scripts/runpod/guard.py stop --run-id {request.run_id} --yes")
    if over_cap:
        print("actual rate exceeds the per-pod cap; stopping the pod now")
        api.stop_pod(created_id)
        ledger.update(created_id, state="exited", stopped_at=datetime.now(UTC).isoformat(), note="auto-stopped: over cap")
        audit("auto-stop", name, {"pod_id": created_id, "reason": "actual rate over per-pod cap"})
        return EXIT_REFUSED
    return 0


def _stop_targets(args: argparse.Namespace, *, terminate: bool) -> int:
    now = datetime.now(UTC)
    ledger = Ledger()
    api = api_from_env()
    pods = api.list_pods()
    selector = args.run_id or args.pod_id
    if not selector:
        print("need --run-id or --pod-id", file=sys.stderr)
        return EXIT_REFUSED
    try:
        targets = resolve_targets(pods, selector, ledger.trusted_ids())
    except GuardError as exc:
        audit("stop-refused", selector, {"reason": str(exc), "terminate": terminate})
        print(f"REFUSED: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    action = "terminate" if terminate else "stop"
    for pod in targets:
        print(f"{action}: {pod_name(pod)} [{pod_id(pod)}] state={pod_state(pod)} {pod_cost_note(pod, now, ledger)}")
    if not args.yes:
        print(f"add --yes to {action}")
        return EXIT_REFUSED
    for pod in targets:
        audit(action, pod_name(pod), {"pod_id": pod_id(pod), "state": pod_state(pod)})
        if terminate:
            api.delete_pod(pod_id(pod))
            ledger.update(pod_id(pod), state="terminated", stopped_at=datetime.now(UTC).isoformat())
        else:
            api.stop_pod(pod_id(pod))
            ledger.update(pod_id(pod), state="exited", stopped_at=datetime.now(UTC).isoformat())
    print(f"{action}d {len(targets)} Conflux pod(s); no other pod was touched")
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    return _stop_targets(args, terminate=False)


def cmd_terminate(args: argparse.Namespace) -> int:
    return _stop_targets(args, terminate=True)


def cmd_stop_all(args: argparse.Namespace) -> int:
    now = datetime.now(UTC)
    ledger = Ledger()
    api = api_from_env()
    pods = api.list_pods()
    mine = [pod for pod in managed_pods(pods, ledger.trusted_ids()) if pod_state(pod) in {"RUNNING", "EXITED"}]
    running = [pod for pod in mine if pod_state(pod) == "RUNNING"]
    if not mine:
        print("no Conflux pods to stop")
        return 0
    for pod in mine:
        print(f"stop: {pod_name(pod)} [{pod_id(pod)}] state={pod_state(pod)} {pod_cost_note(pod, now, ledger)}")
    print(f"{len(running)} running, {len(mine)} total - only Conflux pods appear above")
    if not args.yes:
        print("add --yes to stop them")
        return EXIT_REFUSED
    for pod in mine:
        audit("stop-all", pod_name(pod), {"pod_id": pod_id(pod), "state": pod_state(pod)})
        api.stop_pod(pod_id(pod))
        ledger.update(pod_id(pod), state="exited", stopped_at=datetime.now(UTC).isoformat())
    print(f"stopped {len(mine)} Conflux pod(s)")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    """Enforce per-pod TTLs: stop Conflux pods whose expiry has passed."""
    interval = max(float(args.interval), 15.0)
    api = api_from_env()
    ledger = Ledger()
    iterations = 0
    while True:
        iterations += 1
        now = datetime.now(UTC)
        pods = {pod_id(pod): pod for pod in managed_pods(api.list_pods(), ledger.trusted_ids())}
        due = [entry for entry in ledger.expired(now) if entry.pod_id in pods]
        for entry in due:
            pod = pods[entry.pod_id]
            print(f"TTL passed for {entry.run_id} ({entry.pod_id}); stopping")
            audit("ttl-stop", pod_name(pod), {"pod_id": entry.pod_id, "expires_at": entry.expires_at})
            api.stop_pod(entry.pod_id)
            ledger.update(entry.pod_id, state="exited", stopped_at=datetime.now(UTC).isoformat(), note="ttl")
        if due or args.verbose:
            print(f"[{now.isoformat()}] managed={len(pods)} stopped={len(due)}")
        if not pods and iterations >= 1:
            print("no Conflux pods left; watch exiting")
            return 0
        if args.max_iterations and iterations >= args.max_iterations:
            return 0
        time.sleep(interval)


def cmd_report(args: argparse.Namespace) -> int:
    now = datetime.now(UTC)
    ledger = Ledger()
    api = api_from_env()
    start = now - timedelta(days=int(args.days))
    records = api.billing_pods(start, now)
    ours = {entry.pod_id: entry for entry in ledger.entries}
    rows: list[tuple[str, str, float, float]] = []
    total = 0.0
    for record in records:
        pod = str(record.get("podId") or "")
        if pod not in ours:
            continue
        amount = float(record.get("amount") or 0.0)
        hours = float(record.get("timeBilledMs") or 0) / 3_600_000
        rows.append((ours[pod].run_id, pod, hours, amount))
        total += amount
    print(f"Conflux RunPod spend, last {args.days} day(s): ${total:.2f} across {len(rows)} record(s)")
    for run_id, pod, hours, amount in sorted(rows, key=lambda row: -row[3]):
        print(f"  {run_id:<28} {pod:<16} {hours:6.2f}h  ${amount:7.2f}")
    if not rows:
        print("  (no billing records for Conflux pods in this window)")
    estimated = sum(entry.planned_usd for entry in ledger.entries)
    print(f"Ledger planned spend (all time, local estimate): ${estimated:.2f}")
    wall = ledger.wall_clock_spend(now)
    print(f"Wall-clock spend from our own create/stop stamps (authoritative): ${wall:.2f}")
    summary = foreign_summary(api.list_pods(), ledger.trusted_ids())
    print(f"Other users' pods excluded from these figures: {summary['pods_running']} running, "
          f"${summary['hourly_usd_running']}/hr (aggregate only)")
    if args.write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORT_DIR / f"cost-{now.strftime('%Y%m%d-%H%M%S')}.md"
        lines = [
            f"# Conflux RunPod cost report ({now.date().isoformat()})",
            "",
            f"- Window: {start.date().isoformat()} to {now.date().isoformat()}",
            f"- Billed to Conflux pods: ${total:.2f}",
            f"- Local estimate from ledger: ${estimated:.2f}",
            f"- Wall-clock estimate from our own create/stop stamps: ${wall:.2f}",
            "",
            "| run | pod | billed hours | billed usd |",
            "| --- | --- | ---: | ---: |",
        ]
        lines += [f"| {run_id} | {pod} | {hours:.2f} | {amount:.2f} |" for run_id, pod, hours, amount in rows]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {path} ({path.stat().st_size} bytes)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cost guard and identity gate for Conflux RunPod operations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show Conflux pods, budget and account aggregates").set_defaults(func=cmd_status)
    rep = sub.add_parser("report", help="cost report for Conflux pods")
    rep.add_argument("--days", type=int, default=7)
    rep.add_argument("--write", action="store_true", help="write a markdown copy under .local/runpod/reports/")
    rep.set_defaults(func=cmd_report)
    pre = sub.add_parser("preflight", help="check every cap without creating anything")
    pre.add_argument("--run-id", default="preflight")
    pre.add_argument("--hours", type=float, default=1.0)
    pre.add_argument("--gpu-type", default="")
    pre.add_argument("--assume-rate", type=float, default=0.0)
    pre.set_defaults(func=cmd_preflight)
    cre = sub.add_parser("create", help="create exactly one Conflux pod inside the caps")
    cre.add_argument("--run-id", required=True)
    cre.add_argument("--hours", type=float, required=True)
    cre.add_argument("--gpu-type", default="")
    cre.add_argument("--image", default="")
    cre.add_argument("--assume-rate", type=float, default=0.0)
    cre.add_argument("--spot", action="store_true")
    cre.add_argument("--cmd", nargs="*", default=[])
    cre.add_argument("--env", action="append", default=[])
    cre.add_argument("--with-hf-token", action="store_true")
    cre.add_argument("--yes", action="store_true")
    cre.set_defaults(func=cmd_create)
    for name, func in (("stop", cmd_stop), ("terminate", cmd_terminate)):
        sp = sub.add_parser(name, help=f"{name} Conflux pods only")
        sp.add_argument("--run-id", default="")
        sp.add_argument("--pod-id", default="")
        sp.add_argument("--yes", action="store_true")
        sp.set_defaults(func=func)
    sa = sub.add_parser("stop-all", help="stop every Conflux pod (panic switch)")
    sa.add_argument("--yes", action="store_true")
    sa.set_defaults(func=cmd_stop_all)
    wa = sub.add_parser("watch", help="stop Conflux pods whose TTL has passed")
    wa.add_argument("--interval", type=float, default=60.0)
    wa.add_argument("--max-iterations", type=int, default=0)
    wa.add_argument("--verbose", action="store_true")
    wa.set_defaults(func=cmd_watch)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "create" and not args.image:
        args.image = load_budget()[0].default_image
    try:
        return int(cast("int", args.func(args)))
    except GuardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_API_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
