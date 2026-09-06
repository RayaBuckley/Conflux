#!/usr/bin/env python
"""Create a RunPod GPU pod for Conflux model evaluation.

Usage:
    python scripts/runpod/create_pod.py [--gpu H100] [--model Qwen/Qwen2.5-7B-Instruct]

Requires:
    - RUNPOD_API_KEY environment variable
    - runpodctl installed (pip install runpodctl)
    - SSH key pair (~/.ssh/id_ed25519.pub)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

GPU_TYPES = {
    "H100": "NVIDIA H100 80GB HBM3",
    "A100": "NVIDIA A100 80GB PCIe",
    "L40S": "NVIDIA L40S",
}

DEFAULT_IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def create_pod(
    gpu: str = "H100",
    model_id: str = "Qwen/Qwen2.5-7B-Instruct",
    volume_size: int = 50,
    container_disk: int = 50,
) -> dict[str, str]:
    ssh_key = Path.home() / ".ssh" / "id_ed25519.pub"
    if not ssh_key.exists():
        print(f"Error: SSH public key not found at {ssh_key}", file=sys.stderr)
        sys.exit(1)
    public_key = ssh_key.read_text().strip()
    gpu_type = GPU_TYPES.get(gpu, gpu)
    name = f"conflux-{model_id.rsplit('/', maxsplit=1)[-1].lower()}"
    cmd = [
        "runpodctl",
        "create",
        "pod",
        "--name",
        name,
        "--imageName",
        DEFAULT_IMAGE,
        "--gpuType",
        gpu_type,
        "--gpuCount",
        "1",
        "--volumeSize",
        str(volume_size),
        "--containerDiskSize",
        str(container_disk),
        "--communityCloud",
        "--ports",
        "22/tcp",
        "--env",
        f"PUBLIC_KEY={public_key}",
    ]
    print(f"Creating pod: {name} ({gpu_type})...")
    output = _run(cmd)
    pod_id = output.strip()
    if not pod_id:
        print(f"Error: Failed to create pod. Output: {output}", file=sys.stderr)
        sys.exit(1)
    print(f"Pod created: {pod_id}")
    print("Waiting for pod to start...")
    import time

    for _ in range(60):
        info = _run(["runpodctl", "get", "pod", pod_id])
        try:
            data = json.loads(info)
            if isinstance(data, dict) and data.get("desiredStatus") == "RUNNING":
                ports = data.get("runtime", {}).get("ports", [])
                ssh_port = None
                ssh_ip = None
                for port in ports:
                    if port.get("privatePort") == 22:
                        ssh_port = port.get("publicPort")
                        ssh_ip = port.get("ip")
                if ssh_port and ssh_ip:
                    result = {
                        "pod_id": pod_id,
                        "ssh_ip": ssh_ip,
                        "ssh_port": ssh_port,
                        "name": name,
                    }
                    print(json.dumps(result, indent=2))
                    return result
        except (json.JSONDecodeError, KeyError):
            pass
        time.sleep(5)
    print(f"Error: Pod {pod_id} did not reach RUNNING state in 5 minutes", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Create a RunPod GPU pod")
    parser.add_argument("--gpu", default="H100", choices=list(GPU_TYPES), help="GPU type")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct", help="Model ID for naming")
    parser.add_argument("--volume-size", type=int, default=50, help="Volume size in GB")
    parser.add_argument("--container-disk", type=int, default=50, help="Container disk size in GB")
    args = parser.parse_args()
    create_pod(
        gpu=args.gpu,
        model_id=args.model,
        volume_size=args.volume_size,
        container_disk=args.container_disk,
    )


if __name__ == "__main__":
    main()
