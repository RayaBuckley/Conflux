"""Generate a deterministic native SLED state-exploration comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from conflux.domain import canonical_json
from conflux.experiments.sled_comparison import comparison


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    payload = comparison(arguments.depth)
    arguments.output.mkdir(parents=True, exist_ok=True)
    (arguments.output / "result.json").write_text(
        canonical_json(payload) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    trace = payload["trace_enumeration"]
    state = payload["state_exploration"]
    assert isinstance(trace, dict) and isinstance(state, dict)
    table = (
        "| Method | States | Transitions |\n"
        "|---|---:|---:|\n"
        f"| Trace enumeration | {trace['state_visits']} | {trace['transitions']} |\n"
        f"| State exploration | {state['unique_states']} | {state['transitions']} |\n"
    )
    (arguments.output / "table.md").write_text(table, encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(arguments.output), "depth": arguments.depth}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
