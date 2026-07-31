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
    print(f"Installed CLI smoke passed: {wheels[-1].name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
