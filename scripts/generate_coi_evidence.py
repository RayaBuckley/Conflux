"""Generate or byte-check the curated COI reduction evidence bundle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from conflux.experiments import compare_coi_evidence_bundle, generate_coi_evidence_bundle

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
        generate_coi_evidence_bundle(source_commit, arguments.output)
        print(f"Generated COI reduction evidence: {arguments.output}")
        return 0
    protocol_path = arguments.output / "protocol.json"
    if not protocol_path.is_file():
        print(f"COI reduction evidence is missing: {protocol_path}", file=sys.stderr)
        return 1
    retained = json.loads(protocol_path.read_text(encoding="utf-8"))
    source_commit = str(retained["source_commit"])
    with tempfile.TemporaryDirectory(prefix="conflux-coi-") as temporary:
        regenerated = Path(temporary) / arguments.output.name
        generate_coi_evidence_bundle(source_commit, regenerated)
        changed = compare_coi_evidence_bundle(arguments.output, regenerated)
    if changed:
        print(f"COI reduction evidence is stale: {', '.join(changed)}", file=sys.stderr)
        return 1
    print("COI reduction evidence regeneration check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
