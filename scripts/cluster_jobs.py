"""Materialise deterministic, resumable experiment jobs."""

from __future__ import annotations

import argparse
from pathlib import Path

from conflux.domain import canonical_json
from conflux.experiments import load_manifest, materialise_jobs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    plan = materialise_jobs(load_manifest(arguments.manifest), arguments.output)
    print(canonical_json(plan.to_dict()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
