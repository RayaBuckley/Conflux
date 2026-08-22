"""Paired native SLED reproduction with an independent execution oracle."""

from __future__ import annotations

import json
import sysconfig
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, cast

from jsonschema import Draft202012Validator

from conflux.adapters.scenarios import LoadedScenario, load_scenario, load_schema
from conflux.application import DecisionPipeline
from conflux.domain import Action, DataItem, EnvironmentSnapshot, Permission, PrimitiveAction, Principal, ResourceRef, Session
from conflux.evaluation import ExplicitStateChecker, ITESVerificationSystem, Transition, VerificationBounds, VerificationResult
from conflux.evaluation.defences import CanonicalITES, InitiatorOnly, LatestInputOnly, NoDefence, NoReadCheck, UnionPermissions
from conflux.experiments.protocol import ExperimentProtocol
from conflux.ites import BranchState, BranchStatus, TransitionKernel
from conflux.ites.kernel import DecisionEngine
from conflux.policy import ExplicitConsentPolicy, InMemoryAuthorisationPolicy, PolicyGrant, SessionVisibilityPolicy, SnapshotReadPolicy

_ROOT = Path(__file__).resolve().parents[3]
DEFENCE_NAMES = ("ites", "no_defence", "union_permissions", "initiator_only", "latest_input_only", "no_read_check")


@dataclass(frozen=True, slots=True)
class AbstractExecutionState:
    """Counts of proposed, authorised, blocked, and unauthorised effects in one run."""

    proposed: int
    authorised: int
    blocked: int
    modeled_executed: int
    provider_failed: int
    incomplete: int
    unauthorised_effects: int

    def to_dict(self) -> dict[str, int]:
        """Serialize this abstract execution state to a JSON-compatible dictionary."""
        return {
            "proposed": self.proposed,
            "authorised": self.authorised,
            "blocked": self.blocked,
            "modeled_executed": self.modeled_executed,
            "provider_failed": self.provider_failed,
            "incomplete": self.incomplete,
            "unauthorised_effects": self.unauthorised_effects,
        }


@dataclass(frozen=True, slots=True)
class CanonicalExecutionOracle:
    """Oracle that checks a transition against the canonical decision pipeline."""

    pipeline: DecisionPipeline
    session: Session
    environment: EnvironmentSnapshot
    name: str = "canonical_execution_oracle"

    def violation(self, transition: Transition[BranchState, Action]) -> str | None:
        """Return a violation message if an authorised transition is denied by the oracle."""
        if transition.target.status != BranchStatus.AUTHORISED:
            return None
        decision = self.pipeline.decide(
            session=self.session,
            action=transition.action,
            context=transition.source.context,
            environment=self.environment,
        )
        return None if decision.allowed else "monitor admitted an effect denied by the canonical oracle"


def run_native_reproduction(
    protocol: ExperimentProtocol,
    root: Path | None = None,
) -> dict[str, object]:
    """Run the paired native SLED reproduction and return the validated result."""
    if protocol.track != "native_sled" or protocol.model is not None:
        raise ValueError("native_sled_protocol_required")
    selected_root = root or _default_reproduction_root()
    bounds = VerificationBounds(
        max_depth=_bound(protocol, "max_depth", 4),
        max_states=_bound(protocol, "max_states", 10_000),
        max_transitions=_bound(protocol, "max_transitions", 50_000),
        max_model_calls=_bound(protocol, "max_model_calls", 4),
    )
    pairs: list[dict[str, object]] = []
    total_transitions = 0
    for index in range(1, 4):
        filename = f"env-0{index}-{_suffix(index)}"
        legacy = load_scenario(selected_root / "experiments" / "suites" / "legacy-reproduction" / filename)
        canonical = load_scenario(selected_root / "experiments" / "suites" / "canonical" / filename)
        results = []
        for suite_name, scenario in (("legacy_reproduction", legacy), ("canonical", canonical)):
            for defence_name, factory in _defences():
                row = _evaluate(scenario, suite_name, defence_name, factory(scenario.pipeline), bounds)
                total_transitions += cast(dict[str, int], row["statistics"])["transitions"]
                results.append(row)
        pairs.append(
            {
                "pair_id": f"env-{index:02d}",
                "legacy_fixture": legacy.id,
                "canonical_fixture": canonical.id,
                "results": results,
            }
        )
    controls = _negative_controls(bounds)
    baseline = json.loads((selected_root / "experiments" / "baselines" / "sled-historical-v1.json").read_text(encoding="utf-8"))
    result: dict[str, object] = {
        "schema_version": "2",
        "protocol_fingerprint": protocol.fingerprint,
        "complete": all(cast(bool, item["killed"]) and cast(bool, item["canonical_safe"]) for item in controls),
        "pairs": pairs,
        "negative_controls": controls,
        "historical_comparison": {
            "baseline_id": baseline["id"],
            "historical_trace_claim": baseline["explored_traces_approximate"],
            "current_transitions": total_transitions,
            "classification": "enumeration_change",
            "comparable": False,
        },
        "performance": {
            "runtime_ms": None,
            "peak_memory_bytes": None,
            "measurement_status": "omitted_from_deterministic_fixture",
        },
    }
    Draft202012Validator(load_schema("native-sled-result-v2.schema.json")).validate(result)
    return result


def _default_reproduction_root() -> Path:
    candidates = (
        _ROOT,
        Path(sysconfig.get_path("data")) / "share" / "conflux",
    )
    for candidate in candidates:
        if (candidate / "experiments" / "baselines" / "sled-historical-v1.json").is_file():
            return candidate
    raise ValueError("native_sled_reproduction_fixtures_unavailable")


def _suffix(index: int) -> str:
    return {1: "confidential-handoff.yaml", 2: "cross-project.yaml", 3: "nested-assistance.yaml"}[index]


def _bound(protocol: ExperimentProtocol, name: str, default: int) -> int:
    value = protocol.bounds.get(name, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"invalid_native_bound:{name}")
    return value


def _defences() -> tuple[tuple[str, Callable[[DecisionPipeline], DecisionEngine]], ...]:
    return (
        ("ites", CanonicalITES),
        ("no_defence", lambda pipeline: NoDefence()),
        ("union_permissions", UnionPermissions),
        ("initiator_only", InitiatorOnly),
        ("latest_input_only", LatestInputOnly),
        ("no_read_check", NoReadCheck),
    )


def _evaluate(
    scenario: LoadedScenario,
    suite: str,
    defence: str,
    engine: DecisionEngine,
    bounds: VerificationBounds,
) -> dict[str, object]:
    initial = BranchState.initial(scenario.environment.artifacts())
    action = scenario.model.proposals[0]
    system = ITESVerificationSystem(
        (initial,),
        (action,),
        TransitionKernel(engine),
        scenario.session,
        scenario.environment,
    )
    oracle = CanonicalExecutionOracle(scenario.pipeline, scenario.session, scenario.environment)
    result = ExplicitStateChecker().verify(system, (oracle,), bounds)
    target = system.step(initial, action)[0]
    oracle_denied = oracle.violation(Transition(initial, action, target)) is not None
    outcomes = AbstractExecutionState(
        proposed=1,
        authorised=int(target.status == BranchStatus.AUTHORISED),
        blocked=int(target.status == BranchStatus.BLOCKED),
        modeled_executed=int(target.status == BranchStatus.AUTHORISED),
        provider_failed=0,
        incomplete=int(result.truncated),
        unauthorised_effects=int(target.status == BranchStatus.AUTHORISED and oracle_denied),
    )
    return {
        "suite": suite,
        "defence": defence,
        "verdict": result.verdict.value,
        "statistics": _statistics(result),
        "outcomes": outcomes.to_dict(),
    }


def _statistics(result: VerificationResult[BranchState, Action]) -> dict[str, object]:
    return {
        "unique_states": result.unique_states,
        "transitions": result.transitions,
        "duplicate_states": result.duplicate_states,
        "truncated": result.truncated,
        "counterexample_length": None if result.counterexample is None else result.counterexample.length,
    }


def _negative_controls(bounds: VerificationBounds) -> list[dict[str, object]]:
    authority = _control_case(all_granted=False, cross_readable=True)
    read = _control_case(all_granted=True, cross_readable=False)
    rows = []
    for defence, factory, case in (
        ("no_defence", lambda pipeline: NoDefence(), authority),
        ("union_permissions", UnionPermissions, authority),
        ("initiator_only", InitiatorOnly, authority),
        ("latest_input_only", LatestInputOnly, authority),
        ("no_read_check", NoReadCheck, read),
    ):
        mutant = _verify_control(case, factory(case.pipeline), bounds)
        canonical = _verify_control(case, CanonicalITES(case.pipeline), bounds)
        rows.append(
            {
                "defence": defence,
                "killed": mutant.verdict.value == "unsafe",
                "canonical_safe": canonical.verdict.value == "safe",
                "counterexample_length": None if mutant.counterexample is None else mutant.counterexample.length,
            }
        )
    return rows


@dataclass(frozen=True, slots=True)
class _ControlCase:
    action: Action
    initial: BranchState
    environment: EnvironmentSnapshot
    session: Session
    pipeline: DecisionPipeline


def _control_case(*, all_granted: bool, cross_readable: bool) -> _ControlCase:
    alice = Principal("alice", "Alice")
    bob = Principal("bob", "Bob")
    readers = frozenset({alice, bob}) if cross_readable else frozenset({alice})
    environment = EnvironmentSnapshot(
        "negative-control",
        (
            DataItem("bob-request", "attack", frozenset({bob}), readers),
            DataItem("alice-data", "secret", frozenset({alice}), readers),
        ),
        (ResourceRef("memory", "out", "document"),),
    )
    action = PrimitiveAction("forbidden-write", "write", Permission("write"), environment.resources[0], environment.artifacts())
    grants = {PolicyGrant("alice", "write", "out")}
    if all_granted:
        grants.add(PolicyGrant("bob", "write", "out"))
    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(frozenset(grants)),
        SnapshotReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset({"forbidden-write"})),
    )
    return _ControlCase(
        action,
        BranchState.initial(environment.artifacts()),
        environment,
        Session("control", frozenset({alice, bob})),
        pipeline,
    )


def _verify_control(case: _ControlCase, engine: DecisionEngine, bounds: VerificationBounds) -> VerificationResult[BranchState, Action]:
    system = ITESVerificationSystem((case.initial,), (case.action,), TransitionKernel(engine), case.session, case.environment)
    return ExplicitStateChecker().verify(system, (CanonicalExecutionOracle(case.pipeline, case.session, case.environment),), bounds)


__all__ = ["AbstractExecutionState", "CanonicalExecutionOracle", "run_native_reproduction"]
