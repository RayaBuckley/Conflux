"""Generate or byte-check the retained harness demo run."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from conflux.experiments.harness_demo import (
    compare_harness_demo_bundle,
    generate_harness_demo_bundle,
    verify_harness_demo_checksums,
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
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    if not arguments.check:
        source_commit = str(arguments.source_commit or _head_commit())
        generate_harness_demo_bundle(source_commit, arguments.output)
        print(f"Generated harness demo: {arguments.output}")
        return 0
    result_path = arguments.output / "result.json"
    if not result_path.is_file():
        print(f"Harness demo is missing: {result_path}", file=sys.stderr)
        return 1
    mismatched = verify_harness_demo_checksums(arguments.output)
    if mismatched:
        print(f"Retained checksums do not match: {', '.join(mismatched)}", file=sys.stderr)
        return 1
    source_commit = str(json.loads(result_path.read_text(encoding="utf-8"))["source_commit"])
    with tempfile.TemporaryDirectory(prefix="conflux-harness-demo-") as temporary:
        regenerated = Path(temporary)
        generate_harness_demo_bundle(source_commit, regenerated)
        changed = compare_harness_demo_bundle(arguments.output, regenerated)
    if changed:
        print(f"Regenerated bundle differs: {', '.join(changed)}", file=sys.stderr)
        return 1
    print(f"Harness demo matches: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
