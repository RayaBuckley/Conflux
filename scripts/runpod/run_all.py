#!/usr/bin/env python
"""Orchestrate a complete RunPod evaluation: create pod, setup, run, retrieve, stop.

Usage:
    python scripts/runpod/run_all.py --model Qwen/Qwen2.5-7B-Instruct --gpu H100

Requires:
    - RUNPOD_API_KEY environment variable (for runpodctl)
    - HF_TOKEN environment variable (for gated model downloads)
    - runpodctl installed
    - SSH key pair (~/.ssh/id_ed25519)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _check_env() -> None:
    missing = []
    if not os.environ.get("RUNPOD_API_KEY"):
        missing.append("RUNPOD_API_KEY")
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Set them before running this script:", file=sys.stderr)
        print("  export RUNPOD_API_KEY=your_key", file=sys.stderr)
        print("  export HF_TOKEN=your_hf_token  # optional for public models", file=sys.stderr)
        sys.exit(1)


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _ssh(ip: str, port: str, key: Path, cmd: str, timeout: int = 600) -> str:
    ssh_cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-i",
        str(key),
        "-p",
        port,
        f"root@{ip}",
        cmd,
    ]
    result = _run(ssh_cmd)
    return result.stdout


def _scp(ip: str, port: str, key: Path, src: str, dst: str) -> None:
    cmd = [
        "scp",
        "-r",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-i",
        str(key),
        "-P",
        port,
        src,
        dst,
    ]
    _run(cmd)


def run_all(
    model_id: str,
    gpu: str,
    git_repo: str,
    output: Path,
    keep_pod: bool,
) -> None:
    _check_env()
    key = Path.home() / ".ssh" / "id_ed25519"
    if not key.exists():
        print(f"Error: SSH key not found at {key}", file=sys.stderr)
        sys.exit(1)

    # Phase 1: Create pod
    print("\n=== Phase 1: Creating pod ===")
    from create_pod import create_pod

    pod = create_pod(gpu=gpu, model_id=model_id)
    pod_id = pod["pod_id"]
    ip = pod["ssh_ip"]
    port = pod["ssh_port"]

    try:
        # Phase 2: Setup environment on pod
        print("\n=== Phase 2: Setting up environment ===")
        setup_script = Path(__file__).parent / "setup_pod.sh"
        _scp(ip, port, key, str(setup_script), f"root@{ip}:/workspace/setup_pod.sh")
        env_vars = ""
        if os.environ.get("HF_TOKEN"):
            env_vars = f"HF_TOKEN={os.environ['HF_TOKEN']}"
        setup_cmd = f"bash /workspace/setup_pod.sh {model_id} {git_repo}"
        if env_vars:
            setup_cmd = f"{env_vars} {setup_cmd}"
        print("Running setup (this takes ~5-10 minutes)...")
        _ssh(ip, port, key, setup_cmd, timeout=900)

        # Phase 3: Run evaluations
        print("\n=== Phase 3: Running evaluations ===")
        eval_script = Path(__file__).parent / "run_evaluations.sh"
        _scp(ip, port, key, str(eval_script), f"root@{ip}:/workspace/run_evaluations.sh")
        config_path = f"research/output/runs/runpod-{model_id.replace('/', '-')}/transformers.json"
        _ssh(ip, port, key, f"bash /workspace/run_evaluations.sh research/output/runs/runpod-eval {config_path}", timeout=1800)

        # Phase 4: Retrieve results
        print("\n=== Phase 4: Retrieving results ===")
        output.mkdir(parents=True, exist_ok=True)
        _scp(ip, port, key, f"root@{ip}:/workspace/conflux/research/output/runs/runpod-eval/", str(output) + "/")
        print(f"Results saved to {output}")

        # Print summary
        result_file = output / "runpod-eval" / "result.json"
        if result_file.exists():
            d = json.loads(result_file.read_text())
            print("\n=== AgentDojo Summary ===")
            print(f"Complete: {d.get('complete')}")
            for cell in d.get("cells", []):
                print(f"  {cell['case_id']}: utility={cell.get('native_utility')} security={cell.get('native_security')}")

        planning_file = output / "runpod-eval" / "planning" / "result.json"
        if planning_file.exists():
            d = json.loads(planning_file.read_text())
            passed = sum(1 for o in d.get("observations", []) if o.get("utility_completed"))
            total = len(d.get("observations", []))
            print("\n=== Planning Summary ===")
            print(f"Complete: {d.get('complete')}  ({passed}/{total} passed)")

    finally:
        # Phase 5: Cleanup
        if keep_pod:
            print(f"\n=== Pod kept running: {pod_id} ===")
            print(f"SSH: ssh -p {port} root@{ip}")
            print(f"Stop with: python scripts/runpod/stop_pod.py --pod-id {pod_id}")
        else:
            print(f"\n=== Phase 5: Stopping pod {pod_id} ===")
            from stop_pod import stop_pod

            stop_pod(pod_id, remove=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run complete RunPod evaluation")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct", help="HuggingFace model ID")
    parser.add_argument("--gpu", default="H100", choices=["H100", "A100", "L40S"])
    parser.add_argument("--repo", default="https://github.com/Conflux-Research/Conflux.git")
    parser.add_argument("--output", type=Path, default=Path("research/output/runs/runpod-results"))
    parser.add_argument("--keep-pod", action="store_true", help="Keep pod running after evaluation")
    args = parser.parse_args()
    run_all(args.model, args.gpu, args.repo, args.output, args.keep_pod)


if __name__ == "__main__":
    main()
