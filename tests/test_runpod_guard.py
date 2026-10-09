"""Safety tests for the RunPod cost guard.

The guard must never touch a pod that is not Conflux's, and must never spend
money without an explicit confirmation and a cap check. These tests use a fake
API so that no request ever leaves the machine.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from scripts.runpod import guard


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


def foreign_pod(pod_id: str = "pod-jema1", name: str = "jema-hard200k-pcie-20261009-abc123") -> dict[str, Any]:
    return mk_pod(name, pod_id, env={"SOME_OTHER_USERS_TOKEN": "their_secret"})


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


@pytest.fixture
def state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(guard, "STATE_DIR", tmp_path)
    return tmp_path


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
    pod = mk_pod("jema-hard200k-pcie-20261009-abc123", "pod-jema1", env={guard.MARKER_KEY: guard.MARKER_VALUE})
    ok, evidence = guard.classify(pod)
    assert ok is False
    assert "naming convention" in evidence


def test_classify_rejects_conflux_name_without_evidence() -> None:
    pod = mk_pod("conflux-squatter-20261009-120000", "pod-squat", env={})
    ok, evidence = guard.classify(pod)
    assert ok is False
    assert "no marker" in evidence


def test_managed_pods_separates_the_fleet() -> None:
    pods = [conflux_pod(), foreign_pod(), mk_pod("alesia-h1-promptlen", "pod-alesia")]
    assert [guard.pod_id(p) for p in guard.managed_pods(pods)] == ["pod-conflux1"]


def test_foreign_summary_is_aggregate_only() -> None:
    pods = [conflux_pod(), foreign_pod(), mk_pod("osaze-jema-pcie", "pod-osaze", state="EXITED", rate=1.5)]
    summary = guard.foreign_summary(pods)
    text = json.dumps(summary)
    assert summary["pods_running"] == 1
    assert summary["pods_total"] == 2
    assert summary["by_state"] == {"EXITED": 1, "RUNNING": 1}
    for leak in ("jema", "osaze", "pod-jema1", "pod-osaze", "their_secret"):
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
        guard.resolve_targets(pods, "pod-jema1", [])
    assert "pod-jema1" in str(exc.value)
    assert "jema-hard200k" not in str(exc.value)
    assert "never touches other users" in str(exc.value)


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
    pods = [foreign_pod(), foreign_pod("pod-jema2"), foreign_pod("pod-alesia")]
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
    api = FakeApi([conflux_pod("pilot-1", "pod-conflux1"), foreign_pod(), foreign_pod("pod-jema2"), mk_pod("tb-1", "pod-tb")])
    wire(monkeypatch, api)
    code = guard.main(["stop-all", "--yes"])
    assert code == 0
    assert api.mutating_calls() == [("stop", "pod-conflux1")]
    assert any(record["action"] == "stop-all" for record in audit_log)


def test_cli_stop_all_with_no_conflux_pods_does_nothing(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    api = FakeApi([foreign_pod(), foreign_pod("pod-jema2")])
    wire(monkeypatch, api)
    assert guard.main(["stop-all", "--yes"]) == 0
    assert api.mutating_calls() == []


def test_cli_stop_refuses_a_foreign_selector(monkeypatch: pytest.MonkeyPatch, state_dir: Path, audit_log: list[dict[str, object]]) -> None:
    api = FakeApi([conflux_pod(), foreign_pod()])
    wire(monkeypatch, api)
    assert guard.main(["stop", "--pod-id", "pod-jema1", "--yes"]) == guard.EXIT_REFUSED
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
    api = FakeApi([conflux_pod(), foreign_pod(), foreign_pod("pod-jema2")])
    wire(monkeypatch, api)
    assert guard.main(["status"]) == 0
    out = capsys.readouterr().out
    assert "jema-hard200k-pcie-20261009-abc123" not in out
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
