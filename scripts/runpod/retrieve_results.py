#!/usr/bin/env python
"""Retrieve evaluation results from a RunPod instance via SCP.

Usage:
    python scripts/runpod/retrieve_results.py --pod-ip IP --pod-port PORT --output research/output/runs/runpod-results

Requires:
    - SSH key (~/.ssh/id_ed25519)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def retrieve_results(pod_ip: str, pod_port: str, output: Path, ssh_key: Path | None = None) -> None:
    key = ssh_key or Path.home() / ".ssh" / "id_ed25519"
    if not key.exists():
        print(f"Error: SSH key not found at {key}", file=sys.stderr)
        sys.exit(1)
    output.mkdir(parents=True, exist_ok=True)
    remote = f"root@{pod_ip}:/workspace/conflux/research/output/runs/"
    cmd = [
        "scp",
        "-r",
        "-P",
        pod_port,
        "-i",
        str(key),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        remote,
        str(output),
    ]
    print(f"Retrieving results from {pod_ip}:{pod_port}...")
    subprocess.run(cmd, check=True)
    print(f"Results saved to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve results from RunPod")
    parser.add_argument("--pod-ip", required=True, help="Pod TCP IP address")
    parser.add_argument("--pod-port", required=True, help="Pod TCP port")
    parser.add_argument("--output", type=Path, default=Path("research/output/runs/runpod-results"))
    parser.add_argument("--ssh-key", type=Path, default=None)
    args = parser.parse_args()
    retrieve_results(args.pod_ip, args.pod_port, args.output, args.ssh_key)


if __name__ == "__main__":
    main()
