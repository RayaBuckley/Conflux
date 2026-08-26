"""Reproduce the Part B 1.46M trace SLED enumeration.

Ports the exact option grammar and counter-based enumeration from the archived
original prototype (``research/reports/archive/2026-06-01-original-prototype/main.py``),
measuring canonical-state compression alongside raw trace counts.

The original code is preserved as an immutable archived artifact; this script
replicates its logic without modifying it.

Usage::

    python scripts/generate_partb_reproduction.py
    python scripts/generate_partb_reproduction.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from itertools import chain, combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "native-sled-partb-reproduction-v1"

MAX_DEPTH = 3


# --------------------------------------------------------------------------- #
# Ported domain types (verbatim from archived main.py, lines 13-72)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class User:
    """Principal with a permission set."""

    permissions: frozenset[str]
    tag: str | None = None


@dataclass(frozen=True)
class Data:
    """Data item with author and reader sets."""

    authors: frozenset[User]
    readers: frozenset[User]
    tag: str | None = None


@dataclass(frozen=True)
class PrimitiveAction:
    """Externally visible action."""

    action: str


@dataclass(frozen=True)
class LLMExecutionAction:
    """Request for another LLM execution with the given inputs."""

    inputs: frozenset[Data]


Proposal = PrimitiveAction | LLMExecutionAction


@dataclass(frozen=True)
class Environment:
    """Agent operating context."""

    data: frozenset[Data]

    @property
    def total_users(self) -> frozenset[User]:
        if not self.data:
            return frozenset()
        return frozenset().union(*(d.authors | d.readers for d in self.data))

    @property
    def total_actions(self) -> frozenset[str]:
        if not self.total_users:
            return frozenset()
        return frozenset().union(*(u.permissions for u in self.total_users))


# --------------------------------------------------------------------------- #
# Ported auth functions (verbatim from archived main.py, lines 96-121)
# --------------------------------------------------------------------------- #


def authors_for(inputs: frozenset[Data]) -> frozenset[User]:
    if not inputs:
        return frozenset()
    return frozenset().union(*(d.authors for d in inputs))


def auth(action: str, influencers: frozenset[User]) -> bool:
    """Check that all influencers are authorised.

    NOTE: Returns True for an empty influencer set (historical bug 1).
    This is emulated for faithful reproduction but documented as a bug.
    """
    return all(action in author.permissions for author in influencers)


def auth_read(data: frozenset[Data], influencers: frozenset[User]) -> bool:
    """Check that every influencer can read every input."""
    for target_input in data:
        for author in influencers:
            if author not in target_input.readers:
                return False
    return True


# --------------------------------------------------------------------------- #
# Ported defence logic (verbatim from archived main.py, lines 139-170)
# --------------------------------------------------------------------------- #


class PredefinedLogic:
    """Self-contained logic declared to the evaluator."""

    def __init__(
        self,
        initial_data: set[Data],
        llm_call: Any,
        declare: Any,
        prior_influencers: frozenset[User],
    ) -> None:
        self.initial_data = initial_data
        self.llm_call = llm_call
        self.declare = declare
        self.prior_influencers = prior_influencers

    def run(self) -> None:
        my_logic(
            self.initial_data,
            self.llm_call,
            self.declare,
            self.prior_influencers,
        )


def my_logic(
    initial_data: set[Data],
    llm_call: Any,
    declare: Any,
    prior_influencers: frozenset[User],
) -> None:
    """Core ITES defence logic (ported from MyLogic)."""
    influencers = frozenset().union(authors_for(frozenset(initial_data)), prior_influencers)
    proposals = llm_call(frozenset(initial_data))
    for proposal in proposals:
        if isinstance(proposal, PrimitiveAction) and auth(proposal.action, influencers):
            declare(proposal)
        elif isinstance(proposal, LLMExecutionAction) and auth_read(proposal.inputs, influencers):
            todo = PredefinedLogic(set(proposal.inputs), llm_call, declare, influencers)
            declare(todo)


class MyDefence:
    """ITES defence wrapper."""

    def __init__(
        self,
        environment: Environment,
        initial_data: set[Data],
        llm_call: Any,
        declare: Any,
    ) -> None:
        my_logic(initial_data, llm_call, declare, frozenset())


# --------------------------------------------------------------------------- #
# Reproduction evaluator (ported from Evaluator, lines 172-539)
# --------------------------------------------------------------------------- #


class ReproductionEvaluator:
    """Port of the original Evaluator with canonical-state tracking.

    Removes: gen_task classification, debug prints, dead debug code.
    Adds: canonical-state and transition key collection.
    Preserves: option grammar, counter logic, declare save/restore.
    """

    def __init__(
        self,
        defence: type[MyDefence],
        environment: Environment,
        initial_inputs: set[Data],
    ) -> None:
        self.defence = defence
        self.environment = environment
        self.initial_inputs = initial_inputs
        self.total = 0
        self.incomplete = 0
        self.canonical_states: set[tuple[Any, ...]] = set()
        self.canonical_transitions: set[tuple[Any, ...]] = set()
        self.union: set[User] = set()
        self._explore_all()

    # -- LLM call (ported from lines 178-211) --

    def llm_call(self, inputs: frozenset[Data]) -> frozenset[Proposal]:
        if self.decision_index >= MAX_DEPTH:
            return frozenset()

        self.union |= set(authors_for(inputs))

        choice = self.decision_path[self.decision_index]
        self.llm_inputs.append(set(inputs))
        self.decision_index += 1

        if self.decision_index < MAX_DEPTH:
            self.llm_outputs.append(set(self.options[choice]))
            return self.options[choice]
        self.llm_outputs.append(set(self.last_options[choice]))
        return self.last_options[choice]

    # -- Declare (ported from lines 213-227) --

    def declare(self, item: PrimitiveAction | PredefinedLogic) -> None:
        if isinstance(item, PrimitiveAction):
            if not auth(item.action, frozenset(self.union)):
                self.defence_actions.append((item.action, False))
                return
            self.defence_actions.append((item.action, True))
            return

        before = frozenset(self.union)
        item.run()
        self.union = set(before)

    # -- Option building (ported from explore_all, lines 402-424) --

    def _build_options(self) -> None:
        def powerset(iterable: Any) -> Any:
            items = list(iterable)
            return chain.from_iterable(combinations(items, r) for r in range(1, len(items) + 1))

        primitive = [PrimitiveAction(a) for a in sorted(self.environment.total_actions)]
        execution = [LLMExecutionAction(frozenset(s)) for s in powerset(self.environment.data)]
        atoms = primitive + execution

        self.options: list[frozenset[Proposal]] = []
        for r in range(3):
            for combo in combinations(atoms, r):
                self.options.append(frozenset(combo))
        self.num_options = len(self.options)

        self.last_options: list[frozenset[Proposal]] = []
        for r in range(4):
            for combo in combinations(primitive, r):
                self.last_options.append(frozenset(combo))
        self.num_last_options = len(self.last_options)

    # -- Canonical state key --

    def _state_key(self) -> tuple[Any, ...]:
        return (
            frozenset(u.tag for u in self.union),
            frozenset(d.tag for d in self._all_inputs()),
            self.decision_index,
        )

    def _all_inputs(self) -> set[Data]:
        result: set[Data] = set()
        for s in self.llm_inputs:
            result |= s
        return result

    # -- Enumeration (ported from explore_all, lines 428-539) --

    def _explore_all(self) -> None:
        self._build_options()
        self.decision_path: list[int] = [0] * MAX_DEPTH

        while True:
            self.decision_index = 0
            self.union = set()
            self.llm_inputs: list[set[Data]] = []
            self.defence_actions: list[tuple[str, bool]] = []
            self.llm_outputs: list[set[Proposal]] = []

            self.defence(self.environment, self.initial_inputs, self.llm_call, self.declare)
            self.total += 1

            # Incomplete: final-depth option contained nested proposals
            if self.decision_index >= MAX_DEPTH:
                last_output = self.llm_outputs[-1] if self.llm_outputs else set()
                if any(isinstance(p, LLMExecutionAction) for p in last_output):
                    self.incomplete += 1

            # Canonical state
            self.canonical_states.add(self._state_key())

            # Increment counter (mixed-radix odometer, lines 528-539)
            i = self.decision_index - 1
            while i >= 0:
                self.decision_path[i] += 1
                if self.decision_path[i] < self.num_last_options or (i < MAX_DEPTH - 1 and self.decision_path[i] < self.num_options):
                    break
                self.decision_path[i] = 0
                i -= 1
            if i < 0:
                break

    def result(self) -> dict[str, Any]:
        return {
            "total_traces": self.total,
            "incomplete_traces": self.incomplete,
            "unique_canonical_states": len(self.canonical_states),
            "num_intermediate_options": self.num_options,
            "num_final_options": self.num_last_options,
        }


# --------------------------------------------------------------------------- #
# Environment definitions (exact from archived main.py)
# --------------------------------------------------------------------------- #


def make_env1() -> tuple[Environment, set[Data]]:
    alice = User(frozenset({"read", "write"}), "alice")
    bob = User(frozenset({"read"}), "bob")
    charlie = User(frozenset({"read", "write", "database"}), "charlie")
    dafny = User(frozenset({"read"}), "dafny")

    input1 = Data(frozenset({alice}), frozenset({alice, bob}), "document request")
    input2 = Data(frozenset({bob}), frozenset({bob}), "report request")
    input3 = Data(frozenset({bob}), frozenset({alice, bob, charlie, dafny}), "user prompt")
    input4 = Data(frozenset({charlie}), frozenset({charlie}), "Sensitive data")
    input5 = Data(
        frozenset({dafny}),
        frozenset({alice, bob, charlie, dafny}),
        "Website",
    )

    env = Environment(frozenset({input1, input2, input3, input4, input5}))
    return env, {input3, input1}


def make_env2() -> tuple[Environment, set[Data]]:
    alice = User(frozenset({"read", "write to file"}), "alice")
    bob = User(frozenset({"read", "database", "write to file"}), "bob")
    charlie = User(frozenset({"read", "database"}), "charlie")
    dafny = User(frozenset(), "dafny")

    input1 = Data(frozenset({alice, bob}), frozenset({alice, bob}), "document request")
    input2 = Data(frozenset({bob, charlie}), frozenset({bob, charlie}), "report request")
    input3 = Data(
        frozenset({bob}),
        frozenset({alice, bob, charlie, dafny}),
        "user prompt",
    )
    input4 = Data(frozenset({charlie}), frozenset({charlie}), "Sensitive data")
    input5 = Data(
        frozenset({dafny}),
        frozenset({alice, bob, charlie, dafny}),
        "Website",
    )

    env = Environment(frozenset({input1, input2, input3, input4, input5}))
    return env, {input3}


def make_env3() -> tuple[Environment, set[Data]]:
    alice = User(frozenset({"read", "database", "write to file"}), "alice")
    bob = User(frozenset({"read", "write to file", "delete private file"}), "bob")

    input1 = Data(frozenset({alice}), frozenset({alice, bob}), "project report")
    input2 = Data(frozenset({bob}), frozenset({bob}), "secure file")
    input3 = Data(frozenset({bob}), frozenset({alice, bob}), "user prompt")

    env = Environment(frozenset({input1, input2, input3}))
    return env, {input3}


ENVIRONMENTS: list[tuple[str, Any, Any]] = [
    ("env-01", make_env1, {"expected_traces": 422535}),
    ("env-02", make_env2, {"expected_traces": 996451}),
    ("env-03", make_env3, {"expected_traces": 43621}),
]


# --------------------------------------------------------------------------- #
# Evidence generation
# --------------------------------------------------------------------------- #


def generate() -> dict[str, Any]:
    """Generate the full Part B reproduction evidence bundle."""
    env_results: list[dict[str, Any]] = []

    for env_id, make_fn, meta in ENVIRONMENTS:
        env, initial_inputs = make_fn()
        evaluator = ReproductionEvaluator(MyDefence, env, initial_inputs)
        result = evaluator.result()
        result["env_id"] = env_id
        result["expected_traces"] = meta["expected_traces"]
        result["trace_count_match"] = result["total_traces"] == meta["expected_traces"]
        env_results.append(result)

    total_traces = sum(r["total_traces"] for r in env_results)
    total_incomplete = sum(r["incomplete_traces"] for r in env_results)
    total_states = sum(r["unique_canonical_states"] for r in env_results)

    return {
        "schema_version": "1",
        "id": "native-sled-partb-reproduction-v1",
        "source": "research/reports/archive/2026-06-01-original-prototype/main.py",
        "max_depth": MAX_DEPTH,
        "environments": env_results,
        "totals": {
            "total_traces": total_traces,
            "incomplete_traces": total_incomplete,
            "unique_canonical_states": total_states,
            "expected_total": 1462607,
            "trace_count_match": total_traces == 1462607,
        },
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bundle(output: Path, bundle: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    data = payload.encode("utf-8")
    (output / "result.json").write_bytes(data)
    (output / "CHECKSUMS.sha256").write_text(f"{_sha256(data)}  result.json\n", encoding="utf-8", newline="\n")


def _check(output: Path) -> bool:
    result_path = output / "result.json"
    if not result_path.is_file():
        return False
    retained = result_path.read_bytes()
    regenerated = json.dumps(generate(), indent=2, sort_keys=True).encode("utf-8") + b"\n"
    return retained == regenerated


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce the Part B 1.46M trace SLED enumeration.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Part B reproduction evidence regeneration check passed")
            return 0
        print("Part B reproduction evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated Part B reproduction evidence: {OUTPUT}")
    for env in bundle["environments"]:
        match = "OK" if env["trace_count_match"] else "MISMATCH"
        print(
            f"  {env['env_id']}: {env['total_traces']} traces "
            f"(expected {env['expected_traces']}) [{match}]  "
            f"states={env['unique_canonical_states']}",
        )
    totals = bundle["totals"]
    match = "OK" if totals["trace_count_match"] else "MISMATCH"
    print(
        f"  TOTAL: {totals['total_traces']} traces [{match}]  "
        f"incomplete={totals['incomplete_traces']}  "
        f"states={totals['unique_canonical_states']}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
