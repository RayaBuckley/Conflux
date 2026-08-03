"""Install the built wheel into a clean temporary environment and smoke it."""

from __future__ import annotations

import json
import os
import site
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write_protocol(path: Path, track: str, output: Path) -> None:
    model: dict[str, object] | None = None
    if track != "native_sled":
        model = {
            "backend": "transformers",
            "model_id": "wheel-smoke-local-model",
            "revision": "wheel-smoke-revision",
            "weight_manifest_sha256": "0" * 64,
            "tokenizer_id": "wheel-smoke-tokenizer",
            "tokenizer_revision": "wheel-smoke-revision",
            "prompt_template_version": "wheel-smoke-v1",
            "seed": 0,
            "temperature": 0,
            "top_p": 1,
            "max_output_tokens": 64,
            "context_limit": 1024,
            "device": "cpu",
            "dtype": "float32",
            "runtime_version": "wheel-smoke",
            "endpoint": None,
            "allow_private_remote": False,
        }
    payload = {
        "schema_version": "2",
        "id": f"wheel-{track}",
        "track": track,
        "suite": {"id": f"wheel-{track}", "version": "1"},
        "source_commit": "abcdef0",
        "inputs": {},
        "model": model,
        "prompts": {},
        "seeds": [0],
        "repetitions": 1,
        "bounds": {
            "max_model_calls": 2,
            "max_steps": 4,
            "max_depth": 4,
            "max_states": 1000,
            "max_transitions": 5000,
        },
        "environment": {"class": "wheel-smoke"},
        "output_directory": str(output),
        "rerun_command": ["conflux", track],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def main() -> int:
    wheels = sorted((ROOT / "dist").glob("conflux-*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        print("Wheel validation failed: no wheel found", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="conflux-wheel-") as temporary:
        environment = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        command = environment / ("Scripts/conflux.exe" if sys.platform == "win32" else "bin/conflux")
        subprocess.run(
            (
                str(python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                str(wheels[-1]),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
        )
        smoke_environment = os.environ.copy()
        dependency_path = next(
            path for path in site.getsitepackages() if path.endswith("site-packages")
        )
        smoke_environment["PYTHONPATH"] = dependency_path
        doctor = subprocess.run(
            (str(command), "doctor", "--json"),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if json.loads(doctor.stdout)["schema_version"] != "1":
            raise RuntimeError("installed doctor returned an unknown schema")
        demo_output = Path(temporary) / "demo"
        subprocess.run(
            (
                str(command),
                "demo",
                "--scenario",
                str(ROOT / "examples" / "basic.yaml"),
                "--output",
                str(demo_output),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if not (demo_output / "result.json").is_file():
            raise RuntimeError("installed CLI did not produce result evidence")
        report = subprocess.run(
            (str(command), "report", str(demo_output / "result.json"), "--json"),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if json.loads(report.stdout)["schema_version"] != "1":
            raise RuntimeError("installed report returned an unknown schema")
        plan_output = Path(temporary) / "plan"
        subprocess.run(
            (str(command), "plan", "demo", "--output", str(plan_output)),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if not (plan_output / "result.json").is_file():
            raise RuntimeError("installed planning CLI did not produce result evidence")
        sled_output = Path(temporary) / "sled"
        subprocess.run(
            (
                str(command),
                "sled",
                "run",
                "--suite",
                str(ROOT / "examples" / "basic.yaml"),
                "--output",
                str(sled_output),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        verification = json.loads(
            (sled_output / "verification.json").read_text(encoding="utf-8")
        )
        if verification["verdict"] != "safe":
            raise RuntimeError("installed SLED smoke did not exhaust the finite fixture")

        delegation_output = Path(temporary) / "delegation"
        subprocess.run(
            (str(command), "sled", "delegation", "--output", str(delegation_output)),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        delegation = json.loads(
            (delegation_output / "delegation-verification.json").read_text(
                encoding="utf-8"
            )
        )
        if delegation["runtime_enabled"] or not all(
            item["killed"] for item in delegation["mutants"]
        ):
            raise RuntimeError("installed delegation verification gates are incomplete")

        native_protocol = Path(temporary) / "native-protocol.json"
        native_output = Path(temporary) / "native-reproduction"
        _write_protocol(native_protocol, "native_sled", native_output)
        subprocess.run(
            (
                str(command),
                "sled",
                "reproduce",
                "--protocol",
                str(native_protocol),
                "--output",
                str(native_output),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        native = json.loads((native_output / "result.json").read_text(encoding="utf-8"))
        if not native["complete"]:
            raise RuntimeError("installed native reproduction was incomplete")

        planning_protocol = Path(temporary) / "planning-protocol.json"
        _write_protocol(planning_protocol, "planning", Path(temporary) / "planning-comparison")
        planning_preflight_output = Path(temporary) / "planning-preflight"
        planning = subprocess.run(
            (
                str(command),
                "plan",
                "compare",
                "--config",
                str(planning_protocol),
                "--output",
                str(planning_preflight_output),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if len(json.loads(planning.stdout)["matrix"]) != 32:
            raise RuntimeError("installed planning preflight matrix is incomplete")
        if not (planning_preflight_output / "preflight.json").is_file():
            raise RuntimeError("installed planning preflight was not retained")

        agentdojo_protocol = Path(temporary) / "agentdojo-protocol.json"
        agentdojo_output = Path(temporary) / "agentdojo"
        _write_protocol(agentdojo_protocol, "agentdojo", agentdojo_output)
        agentdojo = subprocess.run(
            (
                str(command),
                "benchmark",
                "agentdojo",
                "--config",
                str(agentdojo_protocol),
                "--output",
                str(agentdojo_output),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if len(json.loads(agentdojo.stdout)["matrix"]) != 4:
            raise RuntimeError("installed AgentDojo preflight matrix is incomplete")
        if not (agentdojo_output / "preflight.json").is_file():
            raise RuntimeError("installed AgentDojo preflight was not retained")

        cedar_output = Path(temporary) / "cedar-preflight"
        cedar = subprocess.run(
            (
                str(command),
                "policy",
                "cedar",
                "preflight",
                "--bundle",
                str(ROOT / "experiments/manifests/cedar-policy-bundle-v1.json"),
                "--corpus",
                str(ROOT / "experiments/suites/cedar-differential-v1.json"),
                "--output",
                str(cedar_output),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if json.loads(cedar.stdout)["classification"] != "evaluation_ready":
            raise RuntimeError("installed Cedar preflight overstated unavailable evidence")

        local_doctor = subprocess.run(
            (str(command), "doctor", "--local-model-config", str(planning_protocol), "--json"),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if json.loads(local_doctor.stdout)["local_model"]["network_scope"] != "none":
            raise RuntimeError("installed local-model preflight reported the wrong scope")
    print(f"Installed CLI smoke passed: {wheels[-1].name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
