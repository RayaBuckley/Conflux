#!/usr/bin/env python
"""Stop or remove a RunPod instance.

Usage:
    python scripts/runpod/stop_pod.py --pod-id POD_ID [--remove]
"""

from __future__ import annotations

import argparse
import subprocess


def stop_pod(pod_id: str, remove: bool = False) -> None:
    if remove:
        cmd = ["runpodctl", "pod", "delete", pod_id]
        print(f"Removing pod {pod_id}...")
    else:
        cmd = ["runpodctl", "pod", "stop", pod_id]
        print(f"Stopping pod {pod_id}...")
    subprocess.run(cmd, check=True)
    print(f"Pod {pod_id} {'removed' if remove else 'stopped'}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stop or remove a RunPod instance")
    parser.add_argument("--pod-id", required=True, help="Pod ID to stop/remove")
    parser.add_argument("--remove", action="store_true", help="Permanently remove the pod")
    args = parser.parse_args()
    stop_pod(args.pod_id, args.remove)


if __name__ == "__main__":
    main()
