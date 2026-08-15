"""Generate or byte-check the curated fourth-year direction bundle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from conflux.experiments import (
    compare_direction_evidence_bundle,
    generate_direction_evidence_bundle,
)

ROOT = Path(__file__).resolve().parents[1]


def _head_commit() -> str:
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    if not arguments.check:
        generate_direction_evidence_bundle(
            str(arguments.source_commit or _head_commit()), arguments.output,
            repo_root=ROOT,
        )
        print(f"Generated offline direction evidence: {arguments.output}")
        return 0
    manifest = arguments.output / "manifest.json"
    if not manifest.is_file():
        print(f"Direction evidence is missing: {manifest}", file=sys.stderr)
        return 1
    source_commit = str(json.loads(manifest.read_text(encoding="utf-8"))["source_commit"])
    with tempfile.TemporaryDirectory(prefix="conflux-directions-") as temporary:
        regenerated = Path(temporary) / arguments.output.name
        generate_direction_evidence_bundle(source_commit, regenerated, repo_root=ROOT)
        changed = compare_direction_evidence_bundle(arguments.output, regenerated)
    if changed:
        print(f"Direction evidence is stale: {', '.join(changed)}", file=sys.stderr)
        return 1
    print("Direction evidence regeneration check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
