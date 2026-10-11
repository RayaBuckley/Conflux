"""Generate or byte-check the retained refusal-reasons evidence.

The script reads the retained AgentDojo run bundles, derives the refusing rule for every blocked record
that carries no reason, and writes the table to the output directory. It calls no model.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from conflux.experiments import (
    DEFAULT_RUNS_ROOT,
    compare_agentdojo_refusal_reasons_bundle,
    generate_agentdojo_refusal_reasons_bundle,
    verify_agentdojo_refusal_reasons_checksums,
)

ROOT = Path(__file__).resolve().parents[1]


def _head_commit() -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    runs_root = arguments.runs_root if arguments.runs_root.is_absolute() else ROOT / arguments.runs_root
    if not runs_root.is_dir():
        print(f"Retained run bundles are missing: {runs_root}", file=sys.stderr)
        return 1
    if not arguments.check:
        source_commit = str(arguments.source_commit or _head_commit())
        generate_agentdojo_refusal_reasons_bundle(source_commit, arguments.output, runs_root)
        payload = json.loads((arguments.output / "refusal-reasons.json").read_text(encoding="utf-8"))
        print(
            f"Generated refusal reasons: {arguments.output} "
            f"({payload['totals']['records_listed']} records, {payload['totals']['records_derived']} derived)",
        )
        return 0
    reasons_path = arguments.output / "refusal-reasons.json"
    if not reasons_path.is_file():
        print(f"Refusal-reasons evidence is missing: {reasons_path}", file=sys.stderr)
        return 1
    mismatched = verify_agentdojo_refusal_reasons_checksums(arguments.output)
    if mismatched:
        print(f"Retained checksums do not match: {', '.join(mismatched)}", file=sys.stderr)
        return 1
    source_commit = str(json.loads(reasons_path.read_text(encoding="utf-8"))["source_commit"])
    with tempfile.TemporaryDirectory(prefix="conflux-agentdojo-refusal-reasons-") as temporary:
        regenerated = Path(temporary)
        generate_agentdojo_refusal_reasons_bundle(source_commit, regenerated, runs_root)
        changed = compare_agentdojo_refusal_reasons_bundle(arguments.output, regenerated)
    if changed:
        print(f"Regenerated bundle differs: {', '.join(changed)}", file=sys.stderr)
        return 1
    print(f"Refusal reasons match the retained bundles: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
