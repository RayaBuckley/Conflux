#!/usr/bin/env python
"""Create a RunPod GPU pod for Conflux model evaluation.

Usage:
    python scripts/runpod/create_pod.py [--gpu H100] [--model Qwen/Qwen2.5-7B-Instruct]

Requires:
    - RUNPOD_API_KEY environment variable
    - runpodctl installed
    - SSH key pair (~/.ssh/id_ed25519.pub)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

GPU_TYPES = {
    "H100": ("NVIDIA H100 80GB HBM3", 3.49),
    "A100": ("NVIDIA A100 80GB PCIe", 1.59),
    "L40S": ("NVIDIA L40S", 1.09),
}

DEFAULT_IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"


def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"runpodctl failed (exit {exc.returncode})", file=sys.stderr)
        print(f"stderr: {exc.stderr}", file=sys.stderr)
        print(f"stdout: {exc.stdout}", file=sys.stderr)
        raise
    return result.stdout.strip()


def create_pod(
    gpu: str = "H100",
    model_id: str = "Qwen/Qwen2.5-7B-Instruct",
    volume_size: int = 50,
    container_disk: int = 50,
    max_runtime_minutes: int = 30,
) -> dict[str, str]:
    gpu_type, price_per_hr = GPU_TYPES.get(gpu, (gpu, 0.0))
    max_cost = price_per_hr * max_runtime_minutes / 60
    name = f"conflux-{model_id.rsplit('/', maxsplit=1)[-1].lower()}"
    print(f"Pod: {name} ({gpu_type})")
    print(f"Rate: ${price_per_hr:.2f}/hr  Max runtime: {max_runtime_minutes} min  Max cost: ${max_cost:.2f}")
    runpod_key = Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key.pub"
    ssh_key = Path.home() / ".ssh" / "id_ed25519.pub"
    key_path = runpod_key if runpod_key.exists() else ssh_key
    if not key_path.exists():
        print(f"Error: SSH public key not found at {key_path}", file=sys.stderr)
        print("Run 'runpodctl config --apiKey YOUR_KEY' to generate one.", file=sys.stderr)
        sys.exit(1)
    public_key = key_path.read_text().strip()
    cmd = [
        "runpodctl",
        "pod",
        "create",
        "--name",
        name,
        "--image",
        DEFAULT_IMAGE,
        "--gpu-id",
        gpu_type,
        "--gpu-count",
        "1",
        "--volume-in-gb",
        str(volume_size),
        "--container-disk-in-gb",
        str(container_disk),
        "--cloud-type",
        "SECURE",
        "--ports",
        "22/tcp",
        "--env",
        json.dumps({"PUBLIC_KEY": public_key}),
        "--wait",
        "--wait-timeout",
        "10m",
    ]
    print(f"Creating pod: {name} ({gpu_type})...")
    output = _run(cmd)
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        print(f"Error: Unexpected output from runpodctl: {output}", file=sys.stderr)
        sys.exit(1)
    pod_id = data.get("id", "")
    if not pod_id:
        print(f"Error: No pod ID in response: {output}", file=sys.stderr)
        sys.exit(1)
    print(f"Pod created and SSH-ready: {pod_id}")
    ssh_info = data.get("ssh", {}) or {}
    ssh_command = ssh_info.get("ssh_command", "")
    result: dict[str, str] = {
        "pod_id": pod_id,
        "ssh_command": ssh_command,
        "name": name,
    }
    if ssh_command:
        parts = ssh_command.split()
        result["ssh_ip"] = ""
        result["ssh_port"] = "22"
        for i, part in enumerate(parts):
            if part.startswith("root@"):
                result["ssh_ip"] = part[5:]
            if part == "-p" and i + 1 < len(parts):
                result["ssh_port"] = parts[i + 1]
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Create a RunPod GPU pod")
    parser.add_argument("--gpu", default="H100", choices=list(GPU_TYPES), help="GPU type")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct", help="Model ID for naming")
    parser.add_argument("--volume-size", type=int, default=50, help="Volume size in GB")
    parser.add_argument("--container-disk", type=int, default=50, help="Container disk size in GB")
    parser.add_argument("--max-runtime-minutes", type=int, default=30, help="Hard stop limit")
    args = parser.parse_args()
    create_pod(
        gpu=args.gpu,
        model_id=args.model,
        volume_size=args.volume_size,
        container_disk=args.container_disk,
        max_runtime_minutes=args.max_runtime_minutes,
    )


if __name__ == "__main__":
    main()
