"""Run the frozen stratified AgentDojo selection against one resolved local model.

The selection manifest freezes which user tasks a breadth sweep executes and carries one
protocol `suite` block per suite. This runner calls the documented preflight and local run for
each requested suite against one already-resolved model configuration and prints one summary
line per suite. It writes nothing outside the suite run directories.

Usage:
    python scripts/run_agentdojo_sweep.py --suite all --model-config <dir>/transformers.json
    python scripts/run_agentdojo_sweep.py --suite travel --model-config <dir>/transformers.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from conflux.adapters.benchmarks.agentdojo_local import ADAPTER_REFUSAL_REASONS

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SELECTION = Path("research/experiments/manifests/agentdojo-stratified-selection-v1.json")
DEFAULT_OUTPUT_ROOT = Path("research/output/runs")
SELECTION_KEY = "protocol_suite_blocks"
Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


def selection_suites(selection: object) -> dict[str, tuple[str, ...]]:
    """Return the frozen task ids per suite from a selection manifest."""
    blocks = selection.get(SELECTION_KEY) if isinstance(selection, dict) else None
    if not isinstance(blocks, dict) or not blocks:
        raise ValueError("selection_manifest_missing_suite_blocks")
    suites: dict[str, tuple[str, ...]] = {}
    for raw_suite, block in blocks.items():
        task_ids = block.get("task_ids") if isinstance(block, dict) else None
        if not isinstance(task_ids, list) or not task_ids:
            raise ValueError(f"selection_manifest_suite_without_tasks:{raw_suite}")
        suites[str(raw_suite)] = tuple(str(task_id) for task_id in task_ids)
    return suites


def protocol_suite_ids(selection: object) -> dict[str, str]:
    """Return the frozen protocol suite id per suite key from a selection manifest.

    A run must carry the id of the selection it came from, so that a protocol can be compared with the
    manifest that produced it. The preflight spells an id of its own when it is given only a suite name,
    which is why the sweep passes this value explicitly.
    """
    blocks = selection.get(SELECTION_KEY) if isinstance(selection, dict) else None
    if not isinstance(blocks, dict) or not blocks:
        raise ValueError("selection_manifest_missing_suite_blocks")
    ids: dict[str, str] = {}
    for raw_suite, block in blocks.items():
        suite_id = block.get("id") if isinstance(block, dict) else None
        if not isinstance(suite_id, str) or not suite_id:
            raise ValueError(f"selection_manifest_suite_without_id:{raw_suite}")
        ids[str(raw_suite)] = suite_id
    return ids


def requested_suites(
    available: dict[str, tuple[str, ...]],
    requested: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    """Resolve --suite names; "all" means every suite, and unknown names are refused by name."""
    if tuple(requested) == ("all",):
        return available
    unknown = sorted(set(requested) - set(available))
    if unknown:
        raise ValueError(f"unknown_suite:{','.join(unknown)}")
    return {suite_id: available[suite_id] for suite_id in requested}


def run_directory(suite_id: str, output_root: Path) -> Path:
    """The run directory the retained bundles of this suite live in."""
    return output_root / f"agentdojo-stratified-{suite_id}-v1"


def preflight_command(
    suite_key: str,
    protocol_suite_id: str,
    task_ids: tuple[str, ...],
    model_config: Path,
    output_dir: Path,
    source_commit: str,
    conflux: Path,
) -> list[str]:
    """The documented preflight invocation for one suite.

    The bare suite key selects the matrix; the manifest's suite id is what the protocol records, so a
    run can be compared with the selection that produced it.
    """
    return [
        str(conflux),
        "benchmark",
        "agentdojo",
        "preflight",
        "--model-config",
        str(model_config),
        "--suite",
        suite_key,
        "--protocol-suite-id",
        protocol_suite_id,
        "--task-ids",
        ",".join(task_ids),
        "--source-commit",
        source_commit,
        "--output",
        str(output_dir),
    ]


def local_run_command(output_dir: Path, model_config: Path, conflux: Path) -> list[str]:
    """The documented local execute invocation for the protocol the preflight just wrote."""
    return [
        str(conflux),
        "benchmark",
        "agentdojo",
        "run",
        "--config",
        str(output_dir / "protocol.json"),
        "--model-config",
        str(model_config),
        "--output",
        str(output_dir),
        "--execute-local",
    ]


def summarise(result_path: Path) -> str:
    """One summary line for a finished suite: cells, completeness, utility and security counts."""
    result = json.loads(result_path.read_text(encoding="utf-8"))
    cells = result["cells"]
    complete = sum(1 for cell in cells if cell.get("status") == "complete")
    utility = sum(1 for cell in cells if cell.get("native_utility"))
    security = sum(1 for cell in cells if cell.get("native_security"))
    return f"cells={len(cells)} complete={complete} failed={len(cells) - complete} utility={utility} security={security}"


def _augmentation(cell: Mapping[str, object]) -> Sequence[object]:
    """Return a cell's recorded mediation records, empty when the cell carries none."""
    records = cell.get("augmentation")
    return records if isinstance(records, Sequence) else ()


def mediated_scope_note(cells: Sequence[Mapping[str, object]]) -> str | None:
    """Warn when a suite's blocked calls are out-of-scope refusals rather than policy decisions.

    A suite whose tools are not annotated cannot measure mediation: every call is refused before the
    policy sees it, the utility is zero by construction, and the folded failure count reads as policy.
    This note is what makes that visible in the sweep output instead of leaving it to the reader.
    """
    blocked = [
        record
        for cell in cells
        for record in _augmentation(cell)
        if isinstance(record, Mapping) and record.get("outcome") == "blocked"
    ]
    out_of_scope = sum(1 for record in blocked if record.get("reason") in ADAPTER_REFUSAL_REASONS)
    if not out_of_scope:
        return None
    if out_of_scope == len(blocked):
        return (
            f"WARNING: suite is outside the annotated tool scope: all {len(blocked)} blocked calls are "
            "unsupported_tool refusals, so its utility and policy counts do not measure mediation"
        )
    return f"note: {out_of_scope} of {len(blocked)} blocked calls are out-of-scope refusals"


def run_suite(
    suite_key: str,
    protocol_suite_id: str,
    task_ids: tuple[str, ...],
    model_config: Path,
    output_dir: Path,
    source_commit: str,
    conflux: Path,
    runner: Runner,
) -> bool:
    """Preflight and run one suite. Returns True when the suite produced a complete result."""
    output_dir.mkdir(parents=True, exist_ok=True)
    preflight = runner(
        preflight_command(
            suite_key,
            protocol_suite_id,
            task_ids,
            model_config,
            output_dir,
            source_commit,
            conflux,
        ),
    )
    if preflight.returncode != 0:
        print(f"{suite_key}: preflight failed ({preflight.returncode})")
        return False
    run = runner(local_run_command(output_dir, model_config, conflux))
    result_path = output_dir / "result.json"
    print(f"{suite_key}: run exit {run.returncode} | {summarise(result_path)}")
    note = mediated_scope_note(json.loads(result_path.read_text(encoding="utf-8"))["cells"])
    if note is not None:
        print(f"{suite_key}: {note}")
    return run.returncode == 0


def _git_resolve(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def resolve_commit(value: str | None, runner: Callable[[list[str]], str] | None = None) -> str:
    """Return the full commit SHA to record for *value*, defaulting to the current HEAD.

    One commit must have one spelling in a protocol record: a short SHA is ambiguous as soon as the
    repository grows, and two records of the same commit written in different spellings do not compare
    equal.
    """
    resolve = runner if runner is not None else _git_resolve
    try:
        resolved = resolve(["git", "rev-parse", "--verify", f"{value or 'HEAD'}^{{commit}}"])
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"cannot resolve --source-commit {value!r} to a full commit SHA") from error
    return resolved.strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", action="append", default=None, help='"all" or a suite id (repeatable)')
    parser.add_argument("--model-config", required=True, help="resolved local model configuration")
    parser.add_argument("--selection", default=str(DEFAULT_SELECTION))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--conflux", default=None, help="conflux entry point (defaults to this environment)")
    args = parser.parse_args(argv)

    suite_selection = Path(args.selection)
    selection = json.loads(suite_selection.read_text(encoding="utf-8"))
    available = selection_suites(selection)
    suite_ids = protocol_suite_ids(selection)
    suites = requested_suites(available, args.suite or ["all"])
    model_config = Path(args.model_config)
    conflux = Path(args.conflux) if args.conflux else Path(sys.executable).parent / "conflux"
    if not conflux.exists():
        if shutil.which("conflux") is None:
            print(f"no conflux entry point at {conflux}; pass --conflux")
            return 2
        conflux = Path(shutil.which("conflux") or "conflux")
    source_commit = resolve_commit(args.source_commit)

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)

    failures = 0
    for suite_key, task_ids in suites.items():
        if not run_suite(
            suite_key,
            suite_ids[suite_key],
            task_ids,
            model_config,
            run_directory(suite_key, Path(args.output_root)),
            source_commit,
            conflux,
            runner,
        ):
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
