"""Generate Part B historical-classification evidence from the archived prototype.

The archived 2026-06-01 prototype
(``research/reports/archive/2026-06-01-original-prototype/main.py``) is the only
retained implementation of the classification counters behind the manuscript's
per-environment table (traces, secure actions, blocked privilege escalation,
secure tasks, blocked privilege-escalation tasks).  ``generate_partb_reproduction.py``
covers the trace totals and the canonical-state compression; this generator
covers the classification counters themselves.

The archived classifier walks ``frozenset`` containers of strings, so its
counters depend on Python's per-process string-hash order: two runs of the same
environment can disagree.  This generator therefore runs the prototype in a
subprocess with ``PYTHONHASHSEED`` pinned, so every retained tuple is
reproducible, and sweeps a few additional seeds to record the order dependence,
the per-environment invariant, and whether the historical table tuple is an
observed ordering sample.

The archived file is never modified: the environment region is substituted in
memory and the substituted source is handed to the subprocess.  Each substituted
source is retained in the bundle for review.

Usage::

    python scripts/generate_partb_classification_evidence.py
    python scripts/generate_partb_classification_evidence.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "native-sled-partb-classification-v1"
ARCHIVED = ROOT / "research" / "reports" / "archive" / "2026-06-01-original-prototype" / "main.py"

# 0-based half-open line ranges inside the archived file.
REGION = (552, 590)
BLOCKS: dict[str, tuple[int, int]] = {
    "envA": (553, 567),
    "envB": (569, 580),
    "envC": (582, 589),
}

PRIMARY_SEED = 0
SWEEP_SEEDS: dict[str, tuple[int, ...]] = {
    "envA": (0, 1, 2, 3, 13),
    "envB": (0, 1, 2),
    "envC": (0, 1, 2, 3, 166, 299),
}
RUN_TIMEOUT_SECONDS = 300

COUNTER_MAP: dict[str, Any] = {
    "definitions": "research/reports/archive/2026-06-01-original-prototype/main.py lines 231-245",
    "columns": {
        "secure_actions": {"index": 0, "name": "PU", "meaning": "goal and declared and secure"},
        "blocked_pe": {"index": 5, "name": "BPI", "meaning": "not goal and not declared"},
        "secure_tasks": {"index": 6, "name": "PTU", "meaning": "genuine task, executed, secure"},
        "blocked_pe_tasks": {"index": 11, "name": "BTPI", "meaning": "not a genuine task and not executed"},
    },
    "depth_bound_counter": {
        "index": 12,
        "name": "LLM execution proposals",
        "note": "index 12 is internal to gen_task and drives the printed incomplete count",
    },
    "invariant": "6 * incomplete + counts[6]",
}

ENVIRONMENTS: tuple[tuple[str, str, str], ...] = (
    ("env1", "envA", "4 principals, 5 data items, initial inputs {user prompt, document request}"),
    ("env2", "envB", "4 principals, 5 data items, initial input {user prompt}"),
    ("env3", "envC", "2 principals, 3 data items, initial input {user prompt}"),
)

# Historical tuples: research/publications/flmsec_2026/main.tex lines 651-655, cross-checked
# against the archived preprint research/publications/paper/iclr2026_conference.tex lines 517-521.
HISTORICAL: dict[str, dict[str, int]] = {
    "env1": {
        "traces": 422535,
        "incomplete": 40040,
        "secure_actions": 176352,
        "blocked_pe": 352704,
        "secure_tasks": 2118454,
        "blocked_pe_tasks": 75648,
    },
    "env2": {
        "traces": 996451,
        "incomplete": 159112,
        "secure_actions": 381328,
        "blocked_pe": 878096,
        "secure_tasks": 4756190,
        "blocked_pe_tasks": 107136,
    },
    "env3": {
        "traces": 43621,
        "incomplete": 19755,
        "secure_actions": 45488,
        "blocked_pe": 28852,
        "secure_tasks": 141342,
        "blocked_pe_tasks": 0,
    },
}

DRIVER = (
    "import sys\n"
    "source = sys.stdin.read()\n"
    "namespace = {'__name__': '__main__', '__file__': sys.argv[1]}\n"
    "exec(compile(source, sys.argv[1], 'exec'), namespace)\n"
)

COUNTS_PATTERN = re.compile(r"^\[([\d,\s]+)\]\s*\[([\d,\s]+)\]$")
TOTALS_PATTERN = re.compile(r"^(\d+) (\d+)$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archived_lines() -> list[str]:
    return ARCHIVED.read_text(encoding="utf-8").splitlines()


def build_source(chosen: str, lines: list[str]) -> str:
    """Return the archived source with only the chosen environment block enabled."""
    rebuilt: list[str] = []
    for name, (start, end) in BLOCKS.items():
        enabled = name == chosen
        rebuilt.append(f"# ---- {name} ({'ENABLED' if enabled else 'commented out'}) ----")
        for line in lines[start:end]:
            rebuilt.append(line if enabled or not line.strip() else f"# {line}")
    return "\n".join(lines[: REGION[0]] + rebuilt + lines[REGION[1]:]) + "\n"


def run_environment(block: str, seed: int, source: str, timeout: float = RUN_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Run the substituted archived prototype once and return its counters."""
    environment = dict(os.environ)
    environment["PYTHONHASHSEED"] = str(seed)
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-c", DRIVER, str(ARCHIVED)],
        input=source,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=environment,
    )
    elapsed = round(time.perf_counter() - started, 3)
    totals: tuple[int, int] | None = None
    counts: list[int] | None = None
    irregularities: list[int] | None = None
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        totals_match = TOTALS_PATTERN.match(stripped)
        if totals_match:
            totals = (int(totals_match.group(1)), int(totals_match.group(2)))
        counts_match = COUNTS_PATTERN.match(stripped)
        if counts_match:
            counts = [int(value) for value in counts_match.group(1).replace(" ", "").split(",") if value]
            irregularities = [int(value) for value in counts_match.group(2).replace(" ", "").split(",") if value]
    complete = completed.returncode == 0 and totals is not None and counts is not None
    return {
        "seed": seed,
        "status": "COMPLETE" if complete else "ERROR",
        "returncode": completed.returncode,
        "total": totals[0] if totals else None,
        "incomplete": totals[1] if totals else None,
        "counts": counts,
        "irr_counts": irregularities,
        "wall_seconds": elapsed,
        "stderr_tail": completed.stderr.splitlines()[-3:],
    }


def _row_tuple(run: dict[str, Any]) -> tuple[int, int, int, int, int] | None:
    counts: list[int] | None = run["counts"]
    if counts is None or run["total"] is None or len(counts) < 12:
        return None
    return (int(run["total"]), int(counts[0]), int(counts[5]), int(counts[6]), int(counts[11]))


def _invariant(run: dict[str, Any]) -> int | None:
    counts: list[int] | None = run["counts"]
    if counts is None or run["incomplete"] is None or len(counts) < 12:
        return None
    return 6 * int(run["incomplete"]) + int(counts[6])


def _historical_invariant(env_id: str) -> int:
    row = HISTORICAL[env_id]
    return 6 * row["incomplete"] + row["secure_tasks"]


def _environment_evidence(env_id: str, block: str, description: str, lines: list[str]) -> tuple[dict[str, Any], str]:
    source = build_source(block, lines)
    runs = [run_environment(block, seed, source) for seed in SWEEP_SEEDS[block]]
    for run in runs:
        print(
            f"  {env_id} seed={run['seed']}: traces={run['total']} incomplete={run['incomplete']} "
            f"counts={run['counts']} [{run['status']}, {run['wall_seconds']}s]",
        )
    primary = next(run for run in runs if run["seed"] == PRIMARY_SEED)
    signatures = {_row_tuple(run) for run in runs}
    invariants = {_invariant(run) for run in runs}
    historical = HISTORICAL[env_id]
    expected = (
        historical["traces"],
        historical["secure_actions"],
        historical["blocked_pe"],
        historical["secure_tasks"],
        historical["blocked_pe_tasks"],
    )
    exact_seeds = sorted(run["seed"] for run in runs if _row_tuple(run) == expected)
    counts = [run["counts"] for run in runs if run["counts"] is not None]
    return {
        "env_id": env_id,
        "block": block,
        "description": description,
        "block_file_lines": [BLOCKS[block][0] + 1, BLOCKS[block][1]],
        "source_file": f"sources/{block}.py",
        "source_sha256": _sha256(source.encode("utf-8")),
        "primary_seed": PRIMARY_SEED,
        "primary_run": primary,
        "runs": runs,
        "seed_sensitivity": {
            "distinct_signatures": len(signatures),
            "counts_0_range": [min(row[0] for row in counts), max(row[0] for row in counts)],
            "incomplete_range": [min(int(run["incomplete"]) for run in runs), max(int(run["incomplete"]) for run in runs)],
        },
        "invariant": {
            "expression": COUNTER_MAP["invariant"],
            "values": sorted(value for value in invariants if value is not None),
            "constant_across_seeds": len(invariants) == 1,
        },
        "historical_row": {
            "expected": historical,
            "traces_match": all(run["total"] == historical["traces"] for run in runs),
            "blocked_pe_tasks_match": all(run["counts"][11] == historical["blocked_pe_tasks"] for run in runs if run["counts"]),
            "exact_tuple_seeds": exact_seeds,
            "exact_tuple_observed": bool(exact_seeds),
            "historical_incomplete_observed": any(run["incomplete"] == historical["incomplete"] for run in runs),
            "invariant": _historical_invariant(env_id),
            "invariant_in_observed_set": _historical_invariant(env_id) in invariants,
        },
    }, source


def generate() -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Run the pinned-seed sweep and return the bundle, the protocol and the sources."""
    lines = archived_lines()
    environments: list[dict[str, Any]] = []
    sources: dict[str, str] = {}
    for env_id, block, description in ENVIRONMENTS:
        evidence, source = _environment_evidence(env_id, block, description, lines)
        environments.append(evidence)
        sources[f"{block}.py"] = source
    total_traces = sum(int(env["primary_run"]["total"]) for env in environments)
    historical_total = sum(row["traces"] for row in HISTORICAL.values())
    bundle = {
        "schema_version": "1",
        "id": OUTPUT.name,
        "source": str(ARCHIVED.relative_to(ROOT)),
        "source_sha256": _sha256(ARCHIVED.read_bytes()),
        "method": {
            "hash_seed": (
                "PYTHONHASHSEED is pinned per run; the archived classifier walks frozensets, so its counters depend on "
                "string-hash order"
            ),
            "region_substitution": "the environment region is rebuilt in memory; the archived file is never written",
            "run_timeout_seconds": RUN_TIMEOUT_SECONDS,
        },
        "counter_map": COUNTER_MAP,
        "environments": environments,
        "totals": {
            "primary_seed": PRIMARY_SEED,
            "total_traces": total_traces,
            "historical_total_traces": historical_total,
            "historical_incomplete": sum(row["incomplete"] for row in HISTORICAL.values()),
            "traces_match": total_traces == historical_total,
        },
    }
    return bundle, protocol(), sources


def protocol() -> dict[str, Any]:
    """Return the run protocol for the bundle."""
    return {
        "schema_version": "1",
        "id": OUTPUT.name,
        "generator": "scripts/generate_partb_classification_evidence.py",
        "archived_source": str(ARCHIVED.relative_to(ROOT)),
        "archived_source_sha256": _sha256(ARCHIVED.read_bytes()),
        "primary_seed": PRIMARY_SEED,
        "sweep_seeds": {block: list(seeds) for block, seeds in SWEEP_SEEDS.items()},
        "environments": {env_id: block for env_id, block, _ in ENVIRONMENTS},
        "counter_map": COUNTER_MAP,
        "historical_source": (
            "research/publications/flmsec_2026/main.tex lines 651-655, cross-checked against "
            "research/publications/paper/iclr2026_conference.tex lines 517-521"
        ),
        "determinism": (
            "Repeating a run with the same PYTHONHASHSEED returns an identical tuple; varying the seed changes the frozenset "
            "iteration order and therefore the counters. The counters are a function of (environment, hash order), not of the "
            "environment alone."
        ),
        "check_semantics": (
            "--check recomputes result.json, protocol.json and the sources/ copies and compares them byte for byte. Run timings "
            "are printed to stdout only and are never retained, so the check is timing-independent. Source hashes depend on the "
            "archived file, not on the repository revision."
        ),
        "negated_claims": [
            "A counter tuple is not a trace-level witness; it counts enumerated paths per environment.",
            "These counters do not prove any security property; they classify enumerated behaviour in the prototype's model.",
        ],
        "limitations": [
            "The archived prototype's incomplete-trace criterion differs from the canonical-state reproduction; index 12 drives it.",
            "A historical tuple that is not observed in the retained seed sweep is still an admissible ordering sample when it "
            "satisfies the environment's invariant, which is constant across every observed seed.",
        ],
    }


VOLATILE_KEYS = ("wall_seconds",)


def _without_timings(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return the bundle with volatile fields removed, so --check is timing independent."""
    stripped: dict[str, Any] = json.loads(json.dumps(bundle))
    for environment in stripped["environments"]:
        for run in [environment["primary_run"], *environment["runs"]]:
            for key in VOLATILE_KEYS:
                run.pop(key, None)
            if run.get("status") == "COMPLETE":
                run.pop("stderr_tail", None)
    return stripped


def _write_bundle(output: Path, bundle: dict[str, Any], proto: dict[str, Any], sources: dict[str, str]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    bundle = _without_timings(bundle)
    (output / "sources").mkdir(parents=True, exist_ok=True)
    files = ["result.json", "protocol.json"]
    (output / "result.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output / "protocol.json").write_text(json.dumps(proto, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    for name, source in sorted(sources.items()):
        (output / "sources" / name).write_text(source, encoding="utf-8", newline="\n")
        files.append(f"sources/{name}")
    checksums = "".join(f"{_sha256((output / name).read_bytes())}  {name}\n" for name in files)
    (output / "CHECKSUMS.sha256").write_text(checksums, encoding="utf-8", newline="\n")


def _check(output: Path) -> bool:
    result_path = output / "result.json"
    protocol_path = output / "protocol.json"
    if not result_path.is_file() or not protocol_path.is_file():
        return False
    bundle, proto, sources = generate()
    if result_path.read_text(encoding="utf-8") != json.dumps(_without_timings(bundle), indent=2, sort_keys=True) + "\n":
        return False
    if protocol_path.read_text(encoding="utf-8") != json.dumps(proto, indent=2, sort_keys=True) + "\n":
        return False
    return all(
        (output / "sources" / name).is_file() and (output / "sources" / name).read_text(encoding="utf-8") == source
        for name, source in sources.items()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Part B classification evidence from the archived prototype.")
    parser.add_argument("--check", action="store_true", help="Verify the retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Part B classification evidence regeneration check passed")
            return 0
        print("Part B classification evidence is stale or missing", file=sys.stderr)
        return 1

    bundle, proto, sources = generate()
    _write_bundle(OUTPUT, bundle, proto, sources)
    print(f"Generated Part B classification evidence: {OUTPUT}")
    for env in bundle["environments"]:
        primary = env["primary_run"]
        historical = env["historical_row"]
        print(
            f"  {env['env_id']} ({env['block']}): primary seed {primary['seed']} traces={primary['total']} "
            f"incomplete={primary['incomplete']} counts={primary['counts']} | traces_match={historical['traces_match']} "
            f"exact_tuple_seeds={historical['exact_tuple_seeds']} invariant={historical['invariant']} "
            f"invariant_observed={historical['invariant_in_observed_set']}",
        )
    totals = bundle["totals"]
    print(
        f"  TOTAL: {totals['total_traces']} traces, historical {totals['historical_total_traces']} "
        f"[{'OK' if totals['traces_match'] else 'MISMATCH'}] historical incomplete {totals['historical_incomplete']}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
