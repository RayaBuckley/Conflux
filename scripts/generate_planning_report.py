"""Generate a four-mode planning comparison from retained observations."""

from __future__ import annotations

import argparse
from pathlib import Path

from conflux.domain import canonical_json
from conflux.experiments import generate_planning_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_directory", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    print(canonical_json(generate_planning_report(arguments.input_directory, arguments.output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
