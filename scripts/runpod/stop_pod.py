#!/usr/bin/env python
"""Stop or remove a Conflux pod through the cost guard.

This script used to drive the RunPod command-line tool directly, on whatever pod
id it was given. The RunPod account is shared with other students and
researchers, so that was unsafe: a typo, a stale id or a recycled id could stop
or permanently delete somebody else's pod.

Every stop now goes through ``scripts/runpod/guard.py``, which acts only on pods
that match the Conflux naming convention and carry the ``CONFLUX_MANAGED``
marker or a live ledger record, refuses everything else, and writes an audit
record before it calls the API.

Usage:
    python scripts/runpod/stop_pod.py --pod-id POD_ID --yes
    python scripts/runpod/stop_pod.py --pod-id POD_ID --remove --yes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.runpod import guard


def stop_pod(pod_id_value: str, remove: bool = False, *, yes: bool = False) -> int:
    """Stop or terminate one Conflux pod through the guard.

    Returns the guard's exit code. ``EXIT_REFUSED`` means the pod is not ours
    and was not touched.
    """
    argv = ["terminate" if remove else "stop", "--pod-id", pod_id_value]
    if yes:
        argv.append("--yes")
    return guard.main(argv)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop or remove a Conflux pod (guard-checked)")
    parser.add_argument("--pod-id", required=True, help="Pod id to stop or remove")
    parser.add_argument("--remove", action="store_true", help="Terminate the pod instead of stopping it")
    parser.add_argument("--yes", "-y", action="store_true", help="Confirm the mutation")
    args = parser.parse_args()
    return stop_pod(args.pod_id, args.remove, yes=args.yes)


if __name__ == "__main__":
    raise SystemExit(main())
