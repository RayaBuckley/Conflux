"""Safety tests for the RunPod cost guard.

The guard must never touch a pod that is not Conflux's, and must never spend
money without an explicit confirmation and a cap check. These tests use a fake
API so that no request ever leaves the machine.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from scripts.runpod import guard

REPO_ROOT = Path(__file__).resolve().parents[1]

# Tokens that mean "this file can act on a pod by itself". Only guard.py may
# contain them: every other path must go through the guard's identity gate.
DESTRUCTIVE_TOKENS = ("pod stop", "pod delete", "pod remove", "pod terminate")


def mk_pod(
    name: str,
    pod_id: str,
    state: str = "RUNNING",
    env: Mapping[str, str] | None = None,
    rate: float = 1.79,
    gpu: str = "NVIDIA H100 PCIe",
    gpu_count: int = 1,
    started_minutes_ago: int = 30,
) -> dict[str, Any]:
    started = datetime.now(UTC) - timedelta(minutes=started_minutes_ago)
    return {
        "id": pod_id,
        "name": name,
        "desiredStatus": state,
        "gpu": {"displayName": gpu, "count": gpu_count},
        "costPerHr": rate,
        "env": dict(env or {}),
        "lastStartedAt": started.isoformat(),
    }


def conflux_pod(run_id: str = "pilot-1", pod_id: str = "pod-conflux1", **kwargs: Any) -> dict[str, Any]:
    env = {guard.MARKER_KEY: guard.MARKER_VALUE, "CONFLUX_RUN_ID": run_id, "HF_TOKEN": "hf_secret_value"}
    return mk_pod(f"{guard.NAME_PREFIX}{run_id}-20261009-120000", pod_id, env=env, **kwargs)


def foreign_pod(pod_id: str = "pod-tenant-a1", name: str = "tenant-a-h100-pcie-20261009-abc123") -> dict[str, Any]:
    return mk_pod(name, pod_id, env={"SOME_OTHER_USERS_TOKEN": "their_secret"})


class FakeResponse:
    """Minimal stand-in for the object urllib returns, for transport-level tests."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class FakeApi:
    """Records every call; refuses nothing, so tests can assert what was called."""

    def __init__(self, pods: list[dict[str, Any]] | None = None) -> None:
        self.pods = list(pods or [])
        self.calls: list[tuple[str, str]] = []

    def list_pods(self) -> list[Mapping[str, Any]]:
        return list(self.pods)

    def create_pod(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        name = str(payload.get("name") or "")
        self.calls.append(("create", name))
        pod = mk_pod(name, "pod-new1", env=dict(payload.get("env") or {}))
        self.pods.append(pod)
        return pod

    def stop_pod(self, pod_id: str) -> None:
        self.calls.append(("stop", pod_id))

    def delete_pod(self, pod_id: str) -> None:
        self.calls.append(("delete", pod_id))

    def billing_pods(self, start: datetime, end: datetime) -> list[Mapping[str, Any]]:
        return []

    def mutating_calls(self) -> list[tuple[str, str]]:
        return [call for call in self.calls if call[0] in {"create", "stop", "delete"}]


@pytest.fixture(autouse=True)
def isolated_state(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the whole guard state directory into a fresh temporary directory.

    Autouse, and a fresh directory per test rather than the shared per-test tmp_path:
    that path is reused between runs, so a ledger left behind by an earlier run made
    later runs fail the daily cap with spend the test had invented. Two real defects
    live here. First, the guard used to capture AUDIT_PATH as a function default, so a
    test that called guard.main() appended fake creates and refusals to the live log
    under .local/runpod/ and the log then described operations that never happened.
    Second, a state directory that survives across runs makes the suite unrepeatable.
    """
    state = tmp_path_factory.mktemp("guard-state")
    monkeypatch.setattr(guard, "STATE_DIR", state)
    monkeypatch.setattr(guard, "LEDGER_PATH", state / "ledger.json")
    monkeypatch.setattr(guard, "AUDIT_PATH", state / "audit.jsonl")
    monkeypatch.setattr(guard, "BUDGET_PATH", state / "budget.json")
    monkeypatch.setattr(guard, "REPORT_DIR", state / "reports")
    return state


@pytest.fixture
def state_dir(isolated_state: Path) -> Path:
    return isolated_state


@pytest.fixture
def audit_log(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    monkeypatch.setattr(guard, "audit", lambda action, target, detail, path=None: records.append(
        {"action": action, "target": target, **detail},
    ))
    return records


# --------------------------------------------------------------------------
# Identity: the safety boundary.
# --------------------------------------------------------------------------


def test_classify_accepts_marked_conflux_pod() -> None:
    ok, evidence = guard.classify(conflux_pod())
    assert ok is True
    assert "marker" in evidence


def test_classify_accepts_ledger_record_without_marker() -> None:
    pod = mk_pod("conflux-pilot-1-20261009-120000", "pod-known", env={})
    assert guard.classify(pod)[0] is False
    ok, evidence = guard.classify(pod, ["pod-known"])
    assert ok is True
    assert "ledger" in evidence


def test_classify_rejects_foreign_pod_even_with_our_marker() -> None:
    pod = mk_pod("tenant-a-h100-pcie-20261009-abc123", "pod-tenant-a1", env={guard.MARKER_KEY: guard.MARKER_VALUE})
    ok, evidence = guard.classify(pod)
    assert ok is False
    assert "naming convention" in evidence


def test_classify_rejects_conflux_name_without_evidence() -> None:
    pod = mk_pod("conflux-squatter-20261009-120000", "pod-squat", env={})
    ok, evidence = guard.classify(pod)
    assert ok is False
    assert "no marker" in evidence


def test_managed_pods_separates_the_fleet() -> None:
    pods = [conflux_pod(), foreign_pod(), mk_pod("tenant-b-h100-promptlen", "pod-tenant-b1")]
    assert [guard.pod_id(p) for p in guard.managed_pods(pods)] == ["pod-conflux1"]


def test_foreign_summary_is_aggregate_only() -> None:
    pods = [conflux_pod(), foreign_pod(), mk_pod("tenant-c-h100-pcie", "pod-tenant-c1", state="EXITED", rate=1.5)]
    summary = guard.foreign_summary(pods)
    text = json.dumps(summary)
    assert summary["pods_running"] == 1
    assert summary["pods_total"] == 2
    assert summary["by_state"] == {"EXITED": 1, "RUNNING": 1}
    for leak in ("tenant-a", "tenant-c", "pod-tenant-a1", "pod-tenant-c1", "their_secret"):
        assert leak not in text


def test_public_view_never_exposes_env_values() -> None:
    view = guard.public_view(conflux_pod(), datetime.now(UTC))
    text = json.dumps(view)
    assert "hf_secret_value" not in text
    assert view["env_keys"] == ["CONFLUX_MANAGED", "CONFLUX_RUN_ID", "HF_TOKEN"]
    assert view["gpu_count"] == 1


# --------------------------------------------------------------------------
# Target resolution: fail closed on anything foreign.
# --------------------------------------------------------------------------


def test_resolve_targets_refuses_foreign_pod_by_id() -> None:
    pods = [conflux_pod(), foreign_pod()]
    with pytest.raises(guard.GuardError) as exc:
        guard.resolve_targets(pods, "pod-tenant-a1", [])
    text = str(exc.value)
    assert "not Conflux pods" in text
    assert "never touches other users" in text
    # A refusal must not disclose another user's pod, in any spelling of its identity.
    assert "pod-tenant-a1" not in text
    assert "tenant-a-h100" not in text


def test_refusal_does_not_disclose_a_foreign_pod_to_the_user(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    audit_log: list[dict[str, object]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    squatter = mk_pod("conflux-pilot-1-20261009-120000", "pod-squat", env={"THEIR_TOKEN": "their_secret"})
    api = FakeApi([squatter])
    wire(monkeypatch, api)
    assert guard.main(["stop", "--run-id", "pilot-1", "--yes"]) == guard.EXIT_REFUSED
    captured = capsys.readouterr()
    visible = captured.out + captured.err + json.dumps(audit_log)
    for leak in ("pod-squat", "their_secret"):
        assert leak not in visible
    assert api.mutating_calls() == []


def test_resolve_targets_matches_run_id_prefix() -> None:
    pods = [conflux_pod("pilot-1"), foreign_pod()]
    targets = guard.resolve_targets(pods, "pilot-1", [])
    assert [guard.pod_id(p) for p in targets] == ["pod-conflux1"]


def test_resolve_targets_unknown_selector_raises() -> None:
    with pytest.raises(guard.GuardError):
        guard.resolve_targets([foreign_pod()], "pilot-9", [])


# --------------------------------------------------------------------------
# Caps.
# --------------------------------------------------------------------------


def request(**kwargs: Any) -> guard.PodRequest:
    base: dict[str, Any] = {
        "run_id": "pilot-1",
        "hours": 2.0,
        "gpu_type": "NVIDIA H100 PCIe",
        "assumed_rate_usd_per_hr": 1.79,
    }
    base.update(kwargs)
    return guard.PodRequest(**base)


def test_clean_request_passes() -> None:
    assert guard.refusals([], guard.Budget(), request(), datetime.now(UTC)) == []


def test_foreign_running_pods_do_not_block_our_creation() -> None:
    pods = [foreign_pod(), foreign_pod("pod-tenant-a2"), foreign_pod("pod-tenant-b1")]
    reasons = guard.refusals(pods, guard.Budget(), request(), datetime.now(UTC))
    assert reasons == []


def test_second_conflux_pod_is_refused() -> None:
    reasons = guard.refusals([conflux_pod()], guard.Budget(), request(), datetime.now(UTC))
    assert any("already running" in reason for reason in reasons)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"gpu_count": 2}, "gpu_count"),
        ({"gpu_type": "NVIDIA A100 80GB PCIe"}, "allowed H100 set"),
        ({"hours": 20.0}, "hours 20.0"),
        ({"hours": 12.0, "assumed_rate_usd_per_hr": 4.0}, "exceeds the per-pod cap"),
        ({"run_id": "Bad_ID"}, "valid Conflux pod name"),
    ],
)
def test_caps_refuse_dangerous_requests(kwargs: dict[str, Any], expected: str) -> None:
    reasons = guard.refusals([], guard.Budget(), request(**kwargs), datetime.now(UTC))
    assert any(expected in reason for reason in reasons), reasons


def test_daily_cap_is_enforced() -> None:
    reasons = guard.refusals([], guard.Budget(), request(), datetime.now(UTC), spend_today_usd=19.0)
    assert any("daily cap" in reason for reason in reasons)


def test_budget_clamps_absolute_limits(state_dir: Path) -> None:
    (state_dir / "budget.json").write_text(
        json.dumps({"max_gpu_count": 8, "max_hours_per_pod": 96, "max_usd_per_pod": 500, "bogus": 1}),
        encoding="utf-8",
    )
    budget, notes = guard.load_budget(state_dir / "budget.json")
    assert budget.max_gpu_count == guard.ABSOLUTE_MAX_GPU_COUNT
    assert budget.max_hours_per_pod == guard.ABSOLUTE_MAX_HOURS
    assert budget.max_usd_per_pod == guard.ABSOLUTE_MAX_USD_PER_POD
    assert any("unknown budget key" in note for note in notes)
    assert any("clamped" in note for note in notes)


def test_budget_honours_stricter_values_and_h100_only_allow_list(state_dir: Path) -> None:
    (state_dir / "budget.json").write_text(
        json.dumps({"max_hours_per_pod": 1.5, "allowed_gpu_types": ["NVIDIA A100 80GB PCIe"]}),
        encoding="utf-8",
    )
    budget, _ = guard.load_budget(state_dir / "budget.json")
    assert budget.max_hours_per_pod == 1.5
    assert budget.allowed_gpu_types == guard.H100_TYPES
    reasons = guard.refusals([], budget, request(hours=2.0), datetime.now(UTC))
    assert reasons


def test_assumed_rate_uses_observed_rates() -> None:
    pods = [mk_pod("conflux-a", "p1", rate=1.5), mk_pod("conflux-b", "p2", rate=2.5), mk_pod("other", "p3", rate=9.9, gpu="NVIDIA L40S")]
    assert guard.assumed_rate("NVIDIA H100 PCIe", pods) == 2.5
    assert guard.assumed_rate("NVIDIA B200", pods) is None


# --------------------------------------------------------------------------
# Ledger.
# --------------------------------------------------------------------------


def entry(
    run_id: str = "pilot-1",
    pod_id: str = "pod-conflux1",
    hours: float = 2.0,
    state: str = "created",
    created_days_ago: float = 0.0,
    expires_in_hours: float | None = None,
) -> guard.LedgerEntry:
    now = datetime.now(UTC)
    expires = hours if expires_in_hours is None else expires_in_hours
    return guard.LedgerEntry(
        run_id=run_id,
        pod_id=pod_id,
        name=f"{guard.NAME_PREFIX}{run_id}",
        created_at=(now - timedelta(days=created_days_ago)).isoformat(),
        expires_at=(now + timedelta(hours=expires)).isoformat(),
        gpu_type="NVIDIA H100 PCIe",
        assumed_rate_usd_per_hr=1.79,
        actual_rate_usd_per_hr=1.79,
        planned_hours=hours,
        planned_usd=round(1.79 * hours, 2),
        image=guard.DEFAULT_IMAGE,
        spot=False,
        state=state,
    )


def test_ledger_round_trip_and_trusted_ids(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    ledger = guard.Ledger(path)
    ledger.add(entry())
    reloaded = guard.Ledger(path)
    assert reloaded.trusted_ids() == {"pod-conflux1"}
    assert reloaded.by_run_id("pilot-1") is not None
    assert reloaded.live_run_ids() == {"pilot-1"}
    reloaded.update("pod-conflux1", state="exited", stopped_at=datetime.now(UTC).isoformat())
    assert guard.Ledger(path).entries[0].state == "exited"
    assert guard.Ledger(path).live_run_ids() == set()


def test_ledger_expiry_and_day_spend(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    now = datetime.now(UTC)
    ledger = guard.Ledger(path)
    ledger.add(entry(run_id="old", pod_id="pod-old", expires_in_hours=-1.0))
    ledger.add(entry(run_id="fresh", pod_id="pod-fresh"))
    ledger.add(entry(run_id="stale", pod_id="pod-stale", created_days_ago=2.0))
    assert [record.run_id for record in ledger.expired(now)] == ["old"]
    assert ledger.spend_on(now) == pytest.approx(7.16, abs=0.01)
    assert ledger.spend_on(now - timedelta(days=2)) == pytest.approx(3.58, abs=0.01)


def test_ledger_record_alone_makes_a_pod_manageable(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    ledger = guard.Ledger(path)
    ledger.add(entry())
    pod = mk_pod("conflux-pilot-1-20261009-120000", "pod-conflux1", env={})
    assert guard.classify(pod, ledger.trusted_ids())[0] is True


# --------------------------------------------------------------------------
# CLI: no spend, no mutation, and never a foreign pod.
# --------------------------------------------------------------------------


def wire(monkeypatch: pytest.MonkeyPatch, api: FakeApi) -> None:
    monkeypatch.setattr(guard, "api_from_env", lambda: api)


def test_cli_stop_all_stops_only_conflux_pods(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1"), foreign_pod(), foreign_pod("pod-tenant-a2"), mk_pod("tb-1", "pod-tb")])
    wire(monkeypatch, api)
    code = guard.main(["stop-all", "--yes"])
    assert code == 0
    assert api.mutating_calls() == [("stop", "pod-conflux1")]
    assert any(record["action"] == "stop-all" for record in audit_log)


def test_cli_stop_all_with_no_conflux_pods_does_nothing(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    api = FakeApi([foreign_pod(), foreign_pod("pod-tenant-a2")])
    wire(monkeypatch, api)
    assert guard.main(["stop-all", "--yes"]) == 0
    assert api.mutating_calls() == []


def test_cli_stop_refuses_a_foreign_selector(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    api = FakeApi([conflux_pod(), foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["stop", "--pod-id", "pod-tenant-a1", "--yes"]) == guard.EXIT_REFUSED
    assert api.mutating_calls() == []
    assert any(record["action"] == "stop-refused" for record in audit_log)


def test_cli_stop_requires_yes(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    api = FakeApi([conflux_pod()])
    wire(monkeypatch, api)
    assert guard.main(["stop", "--run-id", "pilot-1"]) == guard.EXIT_REFUSED
    assert api.mutating_calls() == []


def test_cli_terminate_requires_yes(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    api = FakeApi([conflux_pod()])
    wire(monkeypatch, api)
    assert guard.main(["terminate", "--run-id", "pilot-1"]) == guard.EXIT_REFUSED
    assert api.mutating_calls() == []


def test_cli_terminate_deletes_only_the_named_conflux_pod(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1"), conflux_pod("pilot-2", "pod-conflux2"), foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["terminate", "--run-id", "pilot-2", "--yes"]) == 0
    assert api.mutating_calls() == [("delete", "pod-conflux2")]


def test_cli_create_without_yes_does_not_spend(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    api = FakeApi([])
    wire(monkeypatch, api)
    code = guard.main(["create", "--run-id", "pilot-1", "--hours", "2", "--assume-rate", "1.79"])
    assert code == guard.EXIT_REFUSED
    assert api.calls == []


def test_cli_create_refuses_when_a_conflux_pod_is_running(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    api = FakeApi([conflux_pod()])
    wire(monkeypatch, api)
    code = guard.main(["create", "--run-id", "pilot-2", "--hours", "2", "--assume-rate", "1.79", "--yes"])
    assert code == guard.EXIT_REFUSED
    assert api.mutating_calls() == []
    assert any(record["action"] == "create-refused" for record in audit_log)


def test_cli_create_inside_caps_records_the_ledger(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    api = FakeApi([foreign_pod()])
    wire(monkeypatch, api)
    code = guard.main(["create", "--run-id", "pilot-1", "--hours", "2", "--assume-rate", "1.79", "--yes"])
    assert code == 0
    assert [call[0] for call in api.mutating_calls()] == ["create"]
    ledger = guard.Ledger(state_dir / "ledger.json")
    assert ledger.entries[0].run_id == "pilot-1"
    assert ledger.entries[0].planned_usd == pytest.approx(3.58, abs=0.01)
    assert [record["action"] for record in audit_log][:2] == ["create", "created"]


def test_cli_create_stops_the_pod_when_the_real_rate_exceeds_the_cap(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    class PriceyApi(FakeApi):
        def create_pod(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            self.calls.append(("create", str(payload.get("name"))))
            pod = mk_pod(str(payload.get("name")), "pod-pricey", env=dict(payload.get("env") or {}), rate=25.0)
            self.pods.append(pod)
            return pod

    api = PriceyApi([])
    wire(monkeypatch, api)
    code = guard.main(["create", "--run-id", "pilot-1", "--hours", "4", "--assume-rate", "1.0", "--yes"])
    assert code == guard.EXIT_REFUSED
    assert api.mutating_calls() == [("create", api.calls[0][1]), ("stop", "pod-pricey")]
    assert any(record["action"] == "auto-stop" for record in audit_log)


def test_cli_status_reports_foreign_usage_as_aggregate_only(monkeypatch: pytest.MonkeyPatch, state_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeApi([conflux_pod(), foreign_pod(), foreign_pod("pod-tenant-a2")])
    wire(monkeypatch, api)
    assert guard.main(["status"]) == 0
    out = capsys.readouterr().out
    assert "tenant-a-h100-pcie-20261009-abc123" not in out
    assert "their_secret" not in out
    assert "Other users on this account (untouched, aggregate only): 2 running" in out


def test_billing_query_is_urlencoded_with_rfc3339_z() -> None:
    class RecordingApi(guard.RunPodApi):
        def __init__(self) -> None:
            super().__init__("test-key")
            self.paths: list[str] = []

        def _request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> Any:
            self.paths.append(path)
            return []

    api = RecordingApi()
    start = datetime(2026, 10, 6, 11, 46, 59, tzinfo=UTC)
    end = datetime(2026, 10, 9, 11, 46, 59, tzinfo=UTC)
    api.billing_pods(start, end)
    assert api.paths == [
        "/billing/pods?bucketSize=day&startTime=2026-10-06T11%3A46%3A59Z&endTime=2026-10-09T11%3A46%3A59Z&grouping=podId",
    ]


def test_assumed_rate_prefers_our_own_recorded_pods(tmp_path: Path) -> None:
    ledger = guard.Ledger(tmp_path / "ledger.json")
    ledger.add(entry(run_id="earlier", pod_id="pod-earlier"))
    assert guard.assumed_rate("NVIDIA H100 PCIe", [], ledger) == pytest.approx(1.79)
    assert guard.assumed_rate("NVIDIA B200", [], ledger) is None


def test_preflight_refuses_without_a_rate(monkeypatch: pytest.MonkeyPatch, state_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeApi([])
    wire(monkeypatch, api)
    assert guard.main(["preflight", "--hours", "1"]) == guard.EXIT_REFUSED
    assert "no rate known" in capsys.readouterr().err


# --------------------------------------------------------------------------
# Audit round 2 (2026-10-09): every claim below was a surviving mutant or an
# uncovered path in an independent mutation audit of commit c4e5ace.
# Constants are pinned with literal numbers on purpose: comparing a cap against
# the same constant that defines it proves nothing.
# --------------------------------------------------------------------------


def test_absolute_caps_are_pinned_by_literal_numbers() -> None:
    assert guard.ABSOLUTE_MAX_GPU_COUNT == 1
    assert guard.ABSOLUTE_MAX_CONCURRENT == 1
    assert guard.ABSOLUTE_MAX_HOURS == 12.0
    assert guard.ABSOLUTE_MAX_USD_PER_POD == 50.0
    assert guard.TRUST_WINDOW_DAYS == 7


def test_ledger_trust_ignores_finished_and_stale_entries(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    ledger = guard.Ledger(path)
    ledger.add(entry(run_id="live", pod_id="pod-live"))
    ledger.add(entry(run_id="done", pod_id="pod-done", state="exited"))
    ledger.add(entry(run_id="stale", pod_id="pod-stale", created_days_ago=8.0))
    assert ledger.trusted_ids() == {"pod-live"}
    # A finished or stale entry must not turn a differently-named pod into ours.
    outsider = mk_pod("tenant-c-h100-pcie", "pod-done", env={})
    assert guard.classify(outsider, ledger.trusted_ids())[0] is False
    stale_outsider = mk_pod("tenant-c-h100-pcie", "pod-stale", env={})
    assert guard.classify(stale_outsider, ledger.trusted_ids())[0] is False


def test_ledger_trust_window_edge_is_inclusive_at_the_window_and_not_one_second_past(
    tmp_path: Path,
) -> None:
    """Pin the edge of TRUST_WINDOW_DAYS with an injected clock.

    Without an injected `now` the edge is unobservable: the entry is written a few
    microseconds before it is read, so an age of exactly seven days is always just over.
    """
    created = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    window = timedelta(days=guard.TRUST_WINDOW_DAYS)
    edge = entry(run_id="edge", pod_id="pod-edge")
    edge.created_at = created.isoformat()
    past = entry(run_id="past", pod_id="pod-past")
    past.created_at = (created - timedelta(seconds=1)).isoformat()
    ledger = guard.Ledger(tmp_path / "ledger.json")
    ledger.add(edge)
    ledger.add(past)

    at_the_edge = ledger.trusted_ids(now=created + window)
    assert "pod-edge" in at_the_edge, "an entry exactly at the window edge is still live"

    one_second_past = ledger.trusted_ids(now=created + window + timedelta(seconds=1))
    assert "pod-edge" not in one_second_past, "past the window nothing is trusted"
    assert "pod-past" not in one_second_past


def test_trusted_ledger_id_still_requires_the_name_convention() -> None:
    for bad_name in ("tenant-c-h100-pcie", "conflux-Bad_Name", "conflux-Bad-Name", "conflux-bad name"):
        pod = mk_pod(bad_name, "pod-known", env={})
        ok, evidence = guard.classify(pod, ["pod-known"])
        assert ok is False, bad_name
        assert "naming convention" in evidence
    good = mk_pod("conflux-pilot-1-20261009-120000", "pod-known", env={})
    assert guard.classify(good, ["pod-known"])[0] is True


def test_name_pattern_accepts_model_slugs_and_rejects_loose_names() -> None:
    assert guard.NAME_PATTERN.match("conflux-qwen2.5-7b-instruct-20261009-120000")
    assert guard.NAME_PATTERN.match("conflux-pilot-1")
    for bad in ("conflux-Bad_Name", "conflux-Bad-Name", "conflux-", "tenant-a-pod", "conflux-a/b"):
        assert guard.NAME_PATTERN.match(bad) is None, bad


def test_budget_caps_are_clamped_to_literal_numbers(state_dir: Path) -> None:
    (state_dir / "budget.json").write_text(
        json.dumps(
            {
                "max_hours_per_pod": 48.0,
                "max_usd_per_pod": 500.0,
                "max_usd_per_day": 300.0,
                "max_concurrent_pods": 3,
            },
        ),
        encoding="utf-8",
    )
    budget, _ = guard.load_budget(state_dir / "budget.json")
    assert budget.max_hours_per_pod == 12.0
    assert budget.max_usd_per_pod == 50.0
    assert budget.max_usd_per_day == 100.0
    assert budget.max_concurrent_pods == 1
    reasons = guard.refusals([], budget, request(hours=13.0), datetime.now(UTC))
    assert any("hours 13.0" in reason for reason in reasons), reasons
    reasons = guard.refusals([], budget, request(hours=12.0, assumed_rate_usd_per_hr=4.5), datetime.now(UTC))
    assert any("per-pod cap" in reason for reason in reasons), reasons


def test_daily_cap_counts_spend_already_recorded(state_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger = guard.Ledger(state_dir / "ledger.json")
    ledger.add(entry(run_id="earlier", pod_id="pod-earlier"))
    monkeypatch.setattr(guard, "STATE_DIR", state_dir)
    api = FakeApi([])
    wire(monkeypatch, api)
    assert guard.main(["preflight", "--hours", "12", "--assume-rate", "4.0"]) == guard.EXIT_REFUSED


def test_non_finite_budget_values_are_rejected_not_clamped(state_dir: Path) -> None:
    (state_dir / "budget.json").write_text(
        json.dumps(
            {
                "max_usd_per_pod": float("nan"),
                "max_usd_per_day": float("inf"),
                "max_hours_per_pod": float("nan"),
            },
        ),
        encoding="utf-8",
    )
    budget, notes = guard.load_budget(state_dir / "budget.json")
    assert math.isfinite(budget.max_usd_per_pod)
    assert math.isfinite(budget.max_usd_per_day)
    assert math.isfinite(budget.max_hours_per_pod)
    assert budget.max_usd_per_pod == 10.0
    assert budget.max_usd_per_day == 20.0
    assert any("not a finite number" in note for note in notes), notes
    reasons = guard.refusals([], budget, request(hours=2.0, assumed_rate_usd_per_hr=500.0), datetime.now(UTC))
    assert any("per-pod cap" in reason for reason in reasons), reasons


def test_list_pods_fails_closed_on_an_unexpected_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: Any, timeout: float = 30.0) -> FakeResponse:
        return FakeResponse(b'{"error": "nope"}')

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    with pytest.raises(guard.GuardError, match="unexpected body"):
        guard.RunPodApi("test-key").list_pods()


def test_api_requests_carry_the_explicit_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[Any] = []

    def fake_urlopen(request: Any, timeout: float = 30.0) -> FakeResponse:
        captured.append(request)
        return FakeResponse(b"[]")

    monkeypatch.setattr(guard, "urlopen", fake_urlopen)
    assert guard.RunPodApi("test-key").list_pods() == []
    headers = {key.lower(): value for key, value in captured[0].headers.items()}
    assert headers["user-agent"] == guard.USER_AGENT
    assert "conflux" in headers["user-agent"].lower()
    assert "python-urllib" not in headers["user-agent"].lower()
    assert headers["authorization"] == "Bearer test-key"


def test_cli_stop_all_without_yes_mutates_nothing(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    api = FakeApi([conflux_pod(), foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["stop-all"]) == guard.EXIT_REFUSED
    assert api.mutating_calls() == []


class RaisingApi(FakeApi):
    """Raises on the mutating call, to prove the audit record was written first."""

    def __init__(self, pods: list[dict[str, Any]] | None = None, *, fail_on: str = "stop") -> None:
        super().__init__(pods)
        self.fail_on = fail_on

    def stop_pod(self, pod_id: str) -> None:
        self.calls.append(("stop", pod_id))
        raise OSError("transport died")

    def create_pod(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(("create", str(payload.get("name"))))
        raise OSError("transport died")


def test_stop_writes_the_audit_record_before_the_api_call(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    audit_log: list[dict[str, object]],
) -> None:
    api = RaisingApi([conflux_pod()])
    wire(monkeypatch, api)
    with pytest.raises(OSError):
        guard.main(["stop", "--run-id", "pilot-1", "--yes"])
    assert [record["action"] for record in audit_log] == ["stop"]
    assert audit_log[0]["pod_id"] == "pod-conflux1"


def test_create_writes_the_audit_record_before_the_api_call(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    audit_log: list[dict[str, object]],
) -> None:
    api = RaisingApi([], fail_on="create")
    wire(monkeypatch, api)
    with pytest.raises(OSError):
        guard.main(["create", "--run-id", "pilot-1", "--hours", "2", "--assume-rate", "1.79", "--yes"])
    assert [record["action"] for record in audit_log] == ["create"]
    assert api.calls == [("create", api.calls[0][1])]
    assert not (state_dir / "ledger.json").exists() or guard.Ledger(state_dir / "ledger.json").entries == []


def test_cli_stop_happy_path_stops_exactly_one_pod(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    audit_log: list[dict[str, object]],
) -> None:
    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1"), conflux_pod("pilot-2", "pod-conflux2")])
    wire(monkeypatch, api)
    assert guard.main(["stop", "--run-id", "pilot-1", "--yes"]) == 0
    assert api.mutating_calls() == [("stop", "pod-conflux1")]
    assert [record["action"] for record in audit_log] == ["stop"]
    assert guard.Ledger(state_dir / "ledger.json").entries == []


def test_watch_stops_only_pods_that_are_still_listed_and_never_deletes(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    audit_log: list[dict[str, object]],
) -> None:
    ledger = guard.Ledger(state_dir / "ledger.json")
    ledger.add(entry(run_id="pilot-1", pod_id="pod-real", expires_in_hours=-1.0))
    ledger.add(entry(run_id="pilot-ghost", pod_id="pod-ghost", expires_in_hours=-1.0))
    api = FakeApi([conflux_pod("pilot-1", "pod-real")])
    wire(monkeypatch, api)
    assert guard.main(["watch", "--interval", "15", "--max-iterations", "1"]) == 0
    assert api.mutating_calls() == [("stop", "pod-real")]
    assert not [call for call in api.calls if call[0] == "delete"]
    assert [record["action"] for record in audit_log] == ["ttl-stop"]


def test_watch_exits_when_no_conflux_pods_remain(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    api = FakeApi([foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["watch", "--interval", "15"]) == 0
    assert "no Conflux pods left" in capsys.readouterr().out
    assert api.mutating_calls() == []


class BillingApi(FakeApi):
    """Returns billing records for our pod and for a foreign pod."""

    def billing_pods(self, start: datetime, end: datetime) -> list[Mapping[str, Any]]:
        return [
            {"podId": "pod-conflux1", "amount": 3.5, "timeBilledMs": 1_800_000},
            {"podId": "pod-tenant-a1", "amount": 42.0, "timeBilledMs": 3_600_000},
        ]


def test_report_excludes_foreign_pods_from_output_and_from_the_file(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ledger = guard.Ledger(state_dir / "ledger.json")
    ledger.add(entry(run_id="pilot-1", pod_id="pod-conflux1"))
    report_dir = tmp_path / "reports"
    monkeypatch.setattr(guard, "REPORT_DIR", report_dir)
    api = BillingApi([conflux_pod(), foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["report", "--days", "7", "--write"]) == 0
    printed = capsys.readouterr().out
    written = "".join(path.read_text(encoding="utf-8") for path in report_dir.iterdir())
    for text in (printed, written):
        assert "pod-conflux1" in text
        assert "3.50" in text
        assert "pod-tenant-a1" not in text
        assert "tenant-a-h100" not in text
        assert "42.00" not in text


class RogueApi(FakeApi):
    """Creates a pod that fails the identity check, as a compromised API could."""

    def __init__(self, *, rogue_name: str, rogue_rate: float) -> None:
        super().__init__([])
        self.rogue_name = rogue_name
        self.rogue_rate = rogue_rate

    def create_pod(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(("create", str(payload.get("name"))))
        pod = mk_pod(self.rogue_name, "pod-rogue", env={}, rate=self.rogue_rate)
        self.pods.append(pod)
        return pod


def test_post_create_identity_recheck_stops_a_rogue_pod(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
    audit_log: list[dict[str, object]],
) -> None:
    api = RogueApi(rogue_name="tenant-c-h100-pcie", rogue_rate=1.79)
    wire(monkeypatch, api)
    code = guard.main(["create", "--run-id", "pilot-1", "--hours", "2", "--assume-rate", "1.79", "--yes"])
    assert code == guard.EXIT_API_ERROR
    assert code != 0
    assert api.mutating_calls() == [("create", api.calls[0][1]), ("stop", "pod-rogue")]
    assert guard.Ledger(state_dir / "ledger.json").entries == []
    assert "auto-stop" not in [record["action"] for record in audit_log]


def test_an_unreported_real_rate_is_never_recorded_as_observed(
    monkeypatch: pytest.MonkeyPatch,
    state_dir: Path,
) -> None:
    api = RogueApi(rogue_name="conflux-pilot-1-20261009-120000", rogue_rate=0.0)
    wire(monkeypatch, api)
    assert guard.main(["create", "--run-id", "pilot-1", "--hours", "2", "--assume-rate", "1.79", "--yes"]) == 0
    ledger = guard.Ledger(state_dir / "ledger.json")
    assert ledger.entries[0].actual_rate_usd_per_hr == 0.0
    assert ledger.entries[0].assumed_rate_usd_per_hr == 1.79
    assert ledger.entries[0].planned_usd == pytest.approx(3.58, abs=0.01)
    # The assumed price must not come back as if it had been measured.
    assert guard.assumed_rate("NVIDIA H100 PCIe", [], ledger) is None


# --------------------------------------------------------------------------
# Scope: no other path may act on a pod.
# --------------------------------------------------------------------------


def test_stop_pod_shim_refuses_a_foreign_pod(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    from scripts.runpod import stop_pod as shim

    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1"), foreign_pod()])
    wire(monkeypatch, api)
    assert shim.stop_pod("pod-tenant-a1", yes=True) == guard.EXIT_REFUSED
    assert api.mutating_calls() == []


def test_stop_pod_shim_stops_a_managed_pod(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    from scripts.runpod import stop_pod as shim

    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1")])
    wire(monkeypatch, api)
    assert shim.stop_pod("pod-conflux1", yes=True) == 0
    assert api.mutating_calls() == [("stop", "pod-conflux1")]


def test_stop_pod_shim_keeps_the_confirmation_requirement(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    from scripts.runpod import stop_pod as shim

    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1")])
    wire(monkeypatch, api)
    assert shim.stop_pod("pod-conflux1") == guard.EXIT_REFUSED
    assert api.mutating_calls() == []


def test_no_other_script_can_stop_or_delete_a_pod() -> None:
    offenders: dict[str, list[str]] = {}
    for path in sorted((REPO_ROOT / "scripts").rglob("*")):
        if path.suffix not in {".py", ".sh"} or path.name == "guard.py" or not path.is_file():
            continue
        lowered = path.read_text(encoding="utf-8", errors="replace").lower()
        hits = [token for token in DESTRUCTIVE_TOKENS if token in lowered]
        if '"delete",' in lowered and "/pods/" in lowered:
            hits.append("DELETE /pods")
        if hits:
            offenders[str(path.relative_to(REPO_ROOT))] = hits
    assert offenders == {}, f"these files bypass the guard: {offenders}"


def test_run_all_routes_every_stop_through_the_guard() -> None:
    text = (REPO_ROOT / "scripts/runpod/run_all.py").read_text(encoding="utf-8")
    assert "from stop_pod import stop_pod" not in text
    assert "_guard_stop(pod_id)" in text
    assert "stop_pod.py --pod-id" not in text


def test_run_all_checks_pod_identity_before_it_touches_the_pod() -> None:
    text = (REPO_ROOT / "scripts/runpod/run_all.py").read_text(encoding="utf-8")
    check_at = text.index("_assert_conflux_pod(pod)")
    first_remote = text.index('_ssh(key, ip, port, "mkdir -p /workspace/conflux"')
    assert check_at < first_remote, "identity check must run before the first ssh"


@pytest.fixture
def run_all_module(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> Any:
    monkeypatch.setattr(guard, "LEDGER_PATH", state_dir / "ledger.json")
    helper_dir = str(REPO_ROOT / "scripts" / "runpod")
    sys.path.insert(0, helper_dir)
    try:
        return importlib.import_module("scripts.runpod.run_all")
    finally:
        sys.path.remove(helper_dir)


def test_run_all_fails_closed_when_the_created_pod_is_not_ours(
    run_all_module: Any, monkeypatch: pytest.MonkeyPatch, state_dir: Path,
) -> None:
    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1"), foreign_pod()])
    wire(monkeypatch, api)
    with pytest.raises(SystemExit):
        run_all_module._assert_conflux_pod({"pod_id": "pod-tenant-a1"})


def test_run_all_fails_closed_when_the_created_pod_is_not_visible(
    run_all_module: Any, monkeypatch: pytest.MonkeyPatch, state_dir: Path,
) -> None:
    wire(monkeypatch, FakeApi([]))
    with pytest.raises(SystemExit):
        run_all_module._assert_conflux_pod({"pod_id": "pod-gone"})


def test_run_all_accepts_a_pod_the_guard_owns(
    run_all_module: Any, monkeypatch: pytest.MonkeyPatch, state_dir: Path,
) -> None:
    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1")])
    wire(monkeypatch, api)
    run_all_module._assert_conflux_pod({"pod_id": "pod-conflux1"})


# --------------------------------------------------------------------------
# Hermeticity: the suite must never write the live state directory.
# --------------------------------------------------------------------------


def live_state_dir() -> Path:
    return REPO_ROOT / ".local" / "runpod"


def digest_live_state() -> dict[str, tuple[int, str]]:
    directory = live_state_dir()
    if not directory.exists():
        return {}
    return {
        path.name: (path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted(directory.iterdir())
        if path.is_file()
    }


def test_every_state_path_is_redirected(isolated_state: Path) -> None:
    live = live_state_dir()
    for path in (guard.STATE_DIR, guard.LEDGER_PATH, guard.AUDIT_PATH, guard.BUDGET_PATH, guard.REPORT_DIR):
        assert path == isolated_state or isolated_state in path.parents
        assert path != live
        assert live not in path.parents


def test_a_create_and_stop_cycle_leaves_the_live_state_directory_alone(
    monkeypatch: pytest.MonkeyPatch, state_dir: Path,
) -> None:
    """The real defect this covers: the suite appended fake records to the live audit log."""
    before = digest_live_state()
    api = FakeApi([foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["create", "--run-id", "hermetic", "--hours", "1", "--assume-rate", "1.79", "--yes"]) == 0
    assert guard.main(["stop", "--run-id", "hermetic", "--yes"]) == 0
    assert digest_live_state() == before


def test_audit_records_land_in_the_isolated_directory(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    api = FakeApi([foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["create", "--run-id", "hermetic-audit", "--hours", "1", "--assume-rate", "1.79", "--yes"]) == 0
    records = [json.loads(line) for line in (state_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [record["action"] for record in records][:2] == ["create", "created"]
    assert all(str(record["target"]).startswith("conflux-") for record in records)


def test_refusals_are_audited_in_the_isolated_directory_too(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1")])
    wire(monkeypatch, api)
    assert guard.main(["stop", "--pod-id", "pod-tenant-a1", "--yes"]) == guard.EXIT_REFUSED
    text = (state_dir / "audit.jsonl").read_text(encoding="utf-8")
    assert "stop-refused" in text
    assert "pod-tenant-a1" in text  # the log records the selector the user typed...
    assert "tenant-a-h100" not in text  # ...and never the foreign pod's name or env
