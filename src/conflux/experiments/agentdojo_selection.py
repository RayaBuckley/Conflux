"""Deterministic stratified selection over AgentDojo user tasks and injection vectors.

Nothing in this module imports the benchmark package: the gate validates a frozen selection
manifest without the optional dependency, and ``scripts/select_agentdojo_tasks.py`` reads
upstream and calls :func:`build_manifest` where the package is installed.

The selection is a stratified rule over the attack surface. It says which (suite, user
task, injection vector) pairs a breadth sweep executes; it says nothing about task
difficulty or utility.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

SELECTION_SCHEMA_VERSION = 1
SELECTION_ID = "agentdojo-stratified-v1"
RULE = (
    "per (suite, injection vector) stratum take the lowest user-task id that offers the "
    "vector, skipping task ids excluded as already executed"
)
CASE_IDS = ("benign", "attacked")


@dataclass(frozen=True)
class SuiteFacts:
    """One suite's measured upstream shape: which task offers which injection vectors."""

    suite_id: str
    benchmark_version: str
    user_task_ids: tuple[str, ...]
    default_vectors: tuple[str, ...]
    candidates: Mapping[str, tuple[str, ...]]


def _body(manifest: Mapping[str, object]) -> dict[str, object]:
    """Return the digest-covered part of a manifest."""
    return {
        "rule": manifest.get("rule"),
        "per_stratum": manifest.get("per_stratum"),
        "excluded_task_ids": manifest.get("excluded_task_ids"),
        "suites": manifest.get("suites"),
    }


def manifest_digest(manifest: Mapping[str, object]) -> str:
    """Return ``sha256:<hex>`` over the canonical form of the digest-covered part."""
    canonical = json.dumps(_body(manifest), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def offered_vectors(facts: SuiteFacts) -> tuple[str, ...]:
    """Return the vectors at least one user task of the suite offers."""
    return tuple(sorted({vector for vectors in facts.candidates.values() for vector in vectors}))


def _select(facts: SuiteFacts, per_stratum: int, excluded: Sequence[str]) -> list[dict[str, str]]:
    strata: list[dict[str, str]] = []
    for vector in offered_vectors(facts):
        chosen = [
            task_id
            for task_id in facts.user_task_ids
            if task_id not in excluded and vector in facts.candidates.get(task_id, ())
        ][:per_stratum]
        strata.extend({"vector": vector, "task_id": task_id} for task_id in chosen)
    return strata


def build_manifest(
    *,
    facts: Sequence[SuiteFacts],
    per_stratum: int,
    excluded_task_ids: Mapping[str, Sequence[str]],
    package_version: str,
    benchmark_pin: str,
    generated_utc: str,
    command: str,
) -> dict[str, object]:
    """Build the selection manifest from measured suite facts."""
    if per_stratum < 1:
        raise ValueError(f"per_stratum must be positive, got {per_stratum}")
    suites: dict[str, object] = {}
    selected_pairs = strata_covered = candidate_pairs = 0
    selected_tasks = unreachable_total = defaults_total = 0
    for suite in sorted(facts, key=lambda item: item.suite_id):
        excluded = tuple(excluded_task_ids.get(suite.suite_id, ()))
        unknown = [task_id for task_id in excluded if task_id not in suite.user_task_ids]
        if unknown:
            raise ValueError(f"excluded tasks unknown to {suite.suite_id}: {sorted(unknown)}")
        strata = _select(suite, per_stratum, excluded)
        used = sorted({stratum["task_id"] for stratum in strata})
        offered = offered_vectors(suite)
        unreachable = sorted(set(suite.default_vectors) - set(offered))
        unreachable_total += len(unreachable)
        defaults_total += len(suite.default_vectors)
        suites[suite.suite_id] = {
            "benchmark_version": suite.benchmark_version,
            "user_tasks": len(suite.user_task_ids),
            "injection_vectors": list(offered),
            "default_vectors": list(suite.default_vectors),
            "unreachable_default_vectors": unreachable,
            "strata": strata,
            "selected_task_vectors": {task_id: list(suite.candidates[task_id]) for task_id in used},
        }
        selected_pairs += len(strata)
        strata_covered += len({stratum["vector"] for stratum in strata})
        selected_tasks += len(used)
        candidate_pairs += sum(len(vectors) for vectors in suite.candidates.values())
    manifest: dict[str, object] = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "selection_id": SELECTION_ID,
        "generated_utc": generated_utc,
        "command": command,
        "source": {
            "agentdojo_package": package_version,
            "benchmark_pin": benchmark_pin,
            "candidate_source": "agentdojo.attacks.base_attacks.BaseAttack.get_injection_candidates",
        },
        "rule": RULE,
        "per_stratum": per_stratum,
        "excluded_task_ids": {key: sorted(value) for key, value in sorted(excluded_task_ids.items())},
        "suites": suites,
        "totals": {
            "suites": len(suites),
            "strata": strata_covered,
            "pairs": selected_pairs,
            "selected_tasks": selected_tasks,
            "candidate_pairs": candidate_pairs,
            "unreachable_default_vectors": unreachable_total,
            "default_vectors": defaults_total,
        },
    }
    manifest["protocol_suite_blocks"] = protocol_suite_blocks(manifest)
    manifest["body_digest"] = manifest_digest(manifest)
    return manifest


def selection_pairs(manifest: Mapping[str, object]) -> list[tuple[str, str, str]]:
    """Return the selected ``(suite, user task, vector)`` triples."""
    pairs: list[tuple[str, str, str]] = []
    suites = manifest.get("suites")
    if not isinstance(suites, Mapping):
        return pairs
    for suite_id, suite in sorted(suites.items()):
        if not isinstance(suite, Mapping):
            continue
        for stratum in suite.get("strata", []):
            if isinstance(stratum, Mapping):
                pairs.append((str(suite_id), str(stratum.get("task_id")), str(stratum.get("vector"))))
    return pairs


def protocol_suite_blocks(manifest: Mapping[str, object]) -> dict[str, dict[str, object]]:
    """Return one ``suite`` block per selected suite, ready to paste into a protocol file."""
    blocks: dict[str, dict[str, object]] = {}
    suites = manifest.get("suites")
    if not isinstance(suites, Mapping):
        return blocks
    for suite_id, suite in sorted(suites.items()):
        if not isinstance(suite, Mapping):
            continue
        task_ids = sorted({str(stratum["task_id"]) for stratum in suite.get("strata", [])})
        blocks[str(suite_id)] = {
            "id": f"{suite_id}:stratified-v1",
            "version": str(suite.get("benchmark_version")),
            "task_ids": task_ids,
            "case_ids": list(CASE_IDS),
        }
    return blocks


def _problems_for_suite(suite_id: str, suite: object) -> list[str]:
    problems: list[str] = []
    if not isinstance(suite, Mapping):
        return [f"{suite_id}: suite entry is not an object"]
    vectors = suite.get("injection_vectors")
    defaults = suite.get("default_vectors")
    if not isinstance(vectors, list) or not vectors:
        return [f"{suite_id}: injection_vectors must be a non-empty list"]
    if not isinstance(defaults, list) or not defaults:
        return [f"{suite_id}: default_vectors must be a non-empty list"]
    problems.extend(
        f"{suite_id}: offered vector {vector!r} is not a suite default"
        for vector in sorted(set(map(str, vectors)) - set(map(str, defaults)))
    )
    expected_unreachable = sorted(set(map(str, defaults)) - set(map(str, vectors)))
    if suite.get("unreachable_default_vectors") != expected_unreachable:
        problems.append(
            f"{suite_id}: unreachable_default_vectors is {suite.get('unreachable_default_vectors')!r}, "
            f"measured {expected_unreachable}",
        )
    strata = suite.get("strata")
    if not isinstance(strata, list):
        return [f"{suite_id}: strata must be a list"]
    selected = suite.get("selected_task_vectors")
    if not isinstance(selected, Mapping):
        return [f"{suite_id}: selected_task_vectors must be an object"]
    covered: set[str] = set()
    for stratum in strata:
        if not isinstance(stratum, Mapping):
            problems.append(f"{suite_id}: stratum entry is not an object")
            continue
        vector, task_id = stratum.get("vector"), str(stratum.get("task_id"))
        if vector not in vectors:
            problems.append(f"{suite_id}: stratum vector {vector!r} is not an injection vector")
            continue
        offered = selected.get(task_id)
        if not isinstance(offered, list) or vector not in offered:
            problems.append(f"{suite_id}: task {task_id} does not offer {vector!r}")
        covered.add(str(vector))
    missing = sorted({str(vector) for vector in vectors} - covered)
    if missing:
        problems.append(f"{suite_id}: no pair chosen for strata {missing}")
    covered_tasks = {str(task_id) for task_id in selected}
    unselected = sorted(covered_tasks - {str(stratum.get("task_id")) for stratum in strata if isinstance(stratum, Mapping)})
    if unselected:
        problems.append(f"{suite_id}: selected_task_vectors lists unused tasks {unselected}")
    return problems


def validate_manifest(manifest: Mapping[str, object]) -> list[str]:
    """Return the problems that make a manifest unusable; an empty list means it is sound."""
    problems: list[str] = []
    if manifest.get("schema_version") != SELECTION_SCHEMA_VERSION:
        problems.append(f"schema_version must be {SELECTION_SCHEMA_VERSION}")
    for key in (
        "selection_id",
        "rule",
        "per_stratum",
        "source",
        "suites",
        "totals",
        "protocol_suite_blocks",
        "body_digest",
    ):
        if key not in manifest:
            problems.append(f"missing key {key}")
    per_stratum = manifest.get("per_stratum")
    if not isinstance(per_stratum, int) or per_stratum < 1:
        problems.append("per_stratum must be a positive integer")
    suites = manifest.get("suites")
    if not isinstance(suites, Mapping) or not suites:
        problems.append("suites must be a non-empty object")
        suites = {}
    pairs: list[tuple[str, str, str]] = []
    for suite_id, suite in sorted(suites.items()):
        problems.extend(_problems_for_suite(str(suite_id), suite))
        if isinstance(suite, Mapping):
            for stratum in suite.get("strata", []):
                if isinstance(stratum, Mapping):
                    pairs.append((str(suite_id), str(stratum.get("task_id")), str(stratum.get("vector"))))
    if len(pairs) != len(set(pairs)):
        problems.append("selection repeats a (suite, task, vector) pair")
    totals = manifest.get("totals")
    if not isinstance(totals, Mapping):
        problems.append("totals must be an object")
    else:
        expected = {
            "suites": len(suites),
            "strata": len({(suite_id, vector) for suite_id, _, vector in pairs}),
            "pairs": len(pairs),
            "selected_tasks": len({(str(suite_id), task_id) for suite_id, task_id, _ in pairs}),
            "default_vectors": sum(
                len(suite.get("default_vectors", [])) for suite in suites.values() if isinstance(suite, Mapping)
            ),
        }
        for key, value in expected.items():
            if totals.get(key) != value:
                problems.append(f"totals.{key} is {totals.get(key)!r}, counted {value}")
    blocks = manifest.get("protocol_suite_blocks")
    if blocks is not None and blocks != protocol_suite_blocks(manifest):
        problems.append("protocol_suite_blocks does not match the selected suites")
    digest = manifest.get("body_digest")
    if isinstance(digest, str):
        if digest != manifest_digest(manifest):
            problems.append("body_digest does not match the digest-covered body")
    elif digest is not None:
        problems.append("body_digest must be a string")
    return problems


def selection_drift(frozen: Mapping[str, object], fresh: Mapping[str, object]) -> list[str]:
    """Return the differences between a frozen selection and a fresh measurement."""
    problems: list[str] = []
    if frozen.get("body_digest") != fresh.get("body_digest"):
        problems.append(
            f"body digest differs: frozen {frozen.get('body_digest')}, measured {fresh.get('body_digest')}",
        )
    frozen_pairs = set(selection_pairs(frozen))
    fresh_pairs = set(selection_pairs(fresh))
    for suite, task_id, vector in sorted(fresh_pairs - frozen_pairs):
        problems.append(f"measured but not frozen: {suite}/{task_id}/{vector}")
    for suite, task_id, vector in sorted(frozen_pairs - fresh_pairs):
        problems.append(f"frozen but not measured: {suite}/{task_id}/{vector}")
    return problems or ["selection matches the installed benchmark"]


def candidate_pairs(facts: Iterable[SuiteFacts]) -> int:
    """Return how many (task, vector) pairs the candidate pool holds."""
    return sum(len(vectors) for suite in facts for vectors in suite.candidates.values())
