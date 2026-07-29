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
        output = Path(temporary) / "demo"
        subprocess.run(
            (
                str(command),
                "demo",
                "--scenario",
                str(ROOT / "examples" / "basic.yaml"),
                "--output",
                str(output),
            ),
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
            env=smoke_environment,
        )
        if not (output / "result.json").is_file():
            raise RuntimeError("installed CLI did not produce result evidence")
    print(f"Installed CLI smoke passed: {wheels[-1].name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
