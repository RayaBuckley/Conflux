#!/usr/bin/env python
"""Orchestrate a complete RunPod evaluation: create pod, setup, run, retrieve, stop.

Usage:
    python scripts/runpod/run_all.py --model Qwen/Qwen2.5-7B-Instruct --gpu H100 [--yes]

Requires:
    - RUNPOD_API_KEY environment variable (for runpodctl)
    - HF_TOKEN environment variable (for gated model downloads)
    - runpodctl installed
    - SSH key (~/.runpod/ssh/runpodctl-ssh-key or ~/.ssh/id_ed25519)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from create_pod import GPU_TYPES


def _check_env() -> None:
    if not os.environ.get("RUNPOD_API_KEY"):
        print("Error: RUNPOD_API_KEY not set.", file=sys.stderr)
        sys.exit(1)


def _resolve_ssh_key() -> Path:
    runpod_key = Path.home() / ".runpod" / "ssh" / "runpodctl-ssh-key"
    ssh_key = Path.home() / ".ssh" / "id_ed25519"
    for key in (runpod_key, ssh_key):
        if key.exists():
            return key
    print("Error: No SSH key found. Run 'runpodctl config --apiKey YOUR_KEY'.", file=sys.stderr)
    sys.exit(1)


def _ssh(key: Path, ip: str, port: str, cmd: str, timeout: int = 600) -> str:
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
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True, timeout=timeout)
    except subprocess.CalledProcessError as exc:
        print(f"SSH failed (exit {exc.returncode}): {exc.stderr}", file=sys.stderr)
        raise
    return result.stdout


def _scp(key: Path, ip: str, port: str, src: str, dst: str, timeout: int = 120) -> None:
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
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.CalledProcessError as exc:
        print(f"SCP failed (exit {exc.returncode}): {exc.stderr}", file=sys.stderr)
        raise


def _start_auto_stop_timer(pod_id: str, max_minutes: int) -> threading.Timer:
    def _stop():
        print(f"\n!!! MAX RUNTIME ({max_minutes} min) REACHED — FORCE-STOPPING POD {pod_id} !!!", file=sys.stderr)
        from stop_pod import stop_pod

        stop_pod(pod_id, remove=False)
        sys.exit(1)

    timer = threading.Timer(max_minutes * 60, _stop)
    timer.daemon = True
    timer.start()
    return timer


def run_all(
    model_id: str,
    gpu: str,
    git_repo: str,
    output: Path,
    keep_pod: bool,
    max_runtime_minutes: int,
    yes: bool,
) -> None:
    _check_env()
    key = _resolve_ssh_key()

    _, price_per_hr = GPU_TYPES.get(gpu, (gpu, 0.0))
    max_cost = price_per_hr * max_runtime_minutes / 60
    print("\n=== RunPod Evaluation Plan ===")
    print(f"  Model:     {model_id}")
    print(f"  GPU:       {gpu} (${price_per_hr:.2f}/hr)")
    print(f"  Max time:  {max_runtime_minutes} min")
    print(f"  Max cost:  ${max_cost:.2f}")
    if not yes:
        resp = input("\nProceed? [y/N] ")
        if resp.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    # Phase 1: Create pod
    print("\n=== Phase 1: Creating pod ===")
    sys.path.insert(0, str(Path(__file__).parent))
    from create_pod import create_pod

    pod = create_pod(gpu=gpu, model_id=model_id, max_runtime_minutes=max_runtime_minutes)
    pod_id = pod["pod_id"]
    ip = pod.get("ssh_ip", "")
    port = pod.get("ssh_port", "22")
    start_time = time.time()

    timer = _start_auto_stop_timer(pod_id, max_runtime_minutes)

    try:
        # Phase 2: Setup
        print("\n=== Phase 2: Setting up environment ===")
        print("Waiting 10s for container to fully initialize...")
        time.sleep(10)
        setup_script = Path(__file__).parent / "setup_pod.sh"
        _scp(key, ip, port, str(setup_script), f"root@{ip}:/workspace/setup_pod.sh")
        env_prefix = f"HF_TOKEN={os.environ['HF_TOKEN']} " if os.environ.get("HF_TOKEN") else ""
        setup_cmd = f"{env_prefix}bash /workspace/setup_pod.sh {model_id} {git_repo}"
        print("Running setup (this takes ~5-10 minutes)...")
        _ssh(key, ip, port, setup_cmd, timeout=900)

        # Phase 3: Evaluate
        print("\n=== Phase 3: Running evaluations ===")
        eval_script = Path(__file__).parent / "run_evaluations.sh"
        _scp(key, ip, port, str(eval_script), f"root@{ip}:/workspace/run_evaluations.sh")
        config_path = f"research/output/runs/runpod-{model_id.replace('/', '-')}/transformers.json"
        _ssh(key, ip, port, f"bash /workspace/run_evaluations.sh research/output/runs/runpod-eval {config_path}", timeout=1800)

        # Phase 4: Retrieve
        print("\n=== Phase 4: Retrieving results ===")
        output.mkdir(parents=True, exist_ok=True)
        _scp(key, ip, port, f"root@{ip}:/workspace/conflux/research/output/runs/runpod-eval/", str(output) + "/")
        print(f"Results saved to {output}")

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
        timer.cancel()
        elapsed = time.time() - start_time
        cost = price_per_hr * elapsed / 3600
        print(f"\n=== Runtime: {elapsed / 60:.1f} min  Cost: ~${cost:.2f} ===")

        if keep_pod:
            print(f"Pod kept running: {pod_id}")
            print(f"SSH: ssh -p {port} root@{ip}")
            print(f"Stop: python scripts/runpod/stop_pod.py --pod-id {pod_id}")
        else:
            print(f"Stopping pod {pod_id}...")
            from stop_pod import stop_pod

            stop_pod(pod_id, remove=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run complete RunPod evaluation")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct", help="HuggingFace model ID")
    parser.add_argument("--gpu", default="H100", choices=list(GPU_TYPES))
    parser.add_argument("--repo", default="https://github.com/RayaBuckley/Conflux.git")
    parser.add_argument("--output", type=Path, default=Path("research/output/runs/runpod-results"))
    parser.add_argument("--keep-pod", action="store_true", help="Keep pod running after evaluation")
    parser.add_argument("--max-runtime-minutes", type=int, default=30, help="Hard stop limit (default 30)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    run_all(args.model, args.gpu, args.repo, args.output, args.keep_pod, args.max_runtime_minutes, args.yes)


if __name__ == "__main__":
    main()
