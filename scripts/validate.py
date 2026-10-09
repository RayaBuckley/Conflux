"""Portable repository validation entry point.

Checks are grouped into three tiers so a laptop does not pay for the whole
pipeline on every edit:

1. ``quick`` - static checks (repository audit, schemas, ruff) plus the fast
   test subset; measured 2026-10-08 at 10 s.  Use while iterating.
2. ``standard`` - adds the full test suite with the coverage threshold, the
   evidence reproductions, doctests, mypy, yamllint and vulture; measured at
   1.8 min, of which the branch-coverage run is 104 s (a plain suite run of
   the same 1331 tests takes 33 s).  Use before committing.
3. ``full`` - adds the wheel build with the installed-CLI smoke test, the
   markdownlint and cspell extension checks, and the informational pip-audit;
   measured at 2 min, only 13 s more than ``standard`` because packaging and
   linting the extensions are cheap next to the coverage run.  This is the CI
   path.

Tiers 1 and 2 stop at the first failing step; tier 3 runs every step and
reports all failures, which is what CI needs.  Select a tier with
``--tier quick|standard|full`` (or ``--tier 1|2|3``); the default is ``full``
so the continuous-integration entry point is unchanged.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections import deque
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SESSION_ROOT = ROOT / ".local" / "validation" / uuid4().hex


def _validation_environment() -> dict[str, str]:
    environment = dict(os.environ)
    temporary = SESSION_ROOT / "temp"
    hugging_face = SESSION_ROOT / "huggingface"
    temporary.mkdir(parents=True, exist_ok=True)
    hugging_face.mkdir(parents=True, exist_ok=True)
    environment.update(
        {
            "TEMP": str(temporary),
            "TMP": str(temporary),
            "TMPDIR": str(temporary),
            "HF_HOME": str(hugging_face),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        },
    )
    return environment


VALIDATION_ENV = _validation_environment()


TIER_NAMES = {1: "quick", 2: "standard", 3: "full"}
TIER_ALIASES = {
    "1": 1,
    "2": 2,
    "3": 3,
    "quick": 1,
    "standard": 2,
    "full": 3,
}


# A generated evidence bundle dominates the suite: until 2026-10-08 every test in
# tests/test_sledv_scaling_evidence.py regenerated it (296 s of the 342 s suite).
# The tests now share one generation, but the tier-1 subset still skips the file;
# re-derive this list with `python -m pytest --durations=30`.
SLOW_TEST_PATHS: tuple[str, ...] = ("tests/test_sledv_scaling_evidence.py",)


def _parse_tier(arguments: list[str]) -> int:
    """Read the requested tier from the command line (default: full)."""
    tier = 3
    for index, argument in enumerate(arguments):
        value: str | None = None
        if argument == "--tier":
            if index + 1 >= len(arguments):
                raise SystemExit("--tier requires a value: quick, standard or full")
            value = arguments[index + 1]
        elif argument.startswith("--tier="):
            value = argument.split("=", 1)[1]
        if value is None:
            continue
        if value not in TIER_ALIASES:
            raise SystemExit(f"unknown tier {value!r}: use quick, standard or full")
        tier = TIER_ALIASES[value]
    return tier



def _workflow_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def run(*arguments: str) -> int:
    print(f"[validate] {' '.join(arguments)}", flush=True)
    process = subprocess.Popen(
        (sys.executable, *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=VALIDATION_ENV,
    )
    assert process.stdout is not None
    tail: deque[str] = deque(maxlen=30)
    for line in process.stdout:
        print(line, end="", flush=True)
        tail.append(line.rstrip())
    return_code = process.wait()
    if return_code:
        command = " ".join(arguments)
        detail = "\n".join(tail)
        print(
            f"::error title=Conflux validation failed ({_workflow_escape(command)})::{_workflow_escape(detail)}",
            flush=True,
        )
    return return_code


DOCTEST_TARGET = "src/conflux/domain"
DOCTEST_CHECK = f"pytest --doctest-modules {DOCTEST_TARGET} -q"


def run_doctests() -> int:
    """Run the domain doctests; pytest exit code 5 (no tests collected) is success.

    This step needs the captured stdout to print only when it fails, so it does
    not go through :func:`run`; keeping it in its own function lets the wiring
    tests replace it the same way they replace ``run`` and ``run_info``.
    """
    process = subprocess.run(
        (sys.executable, "-m", "pytest", "--doctest-modules", DOCTEST_TARGET, "-q"),
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=VALIDATION_ENV,
    )
    if process.returncode and process.returncode != 5:
        print(f"[validate] {DOCTEST_CHECK}")
        print(process.stdout, end="")
        print(process.stderr, end="", file=sys.stderr)
        return process.returncode
    return 0


def run_info(*arguments: str) -> int:
    """Run a check but never add it to the failure list (informational only)."""
    print(f"[validate] {' '.join(arguments)}", flush=True)
    process = subprocess.Popen(
        (sys.executable, *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=VALIDATION_ENV,
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
    return process.wait()


def main() -> int:
    tier = _parse_tier(sys.argv[1:])
    failures: list[str] = []
    not_run: list[str] = []
    after_failure: list[str] = []
    stopped = False

    def _run(step_tier: int, *arguments: str) -> None:
        nonlocal stopped
        name = " ".join(arguments)
        if stopped:
            after_failure.append(name)
            return
        if step_tier > tier:
            not_run.append(name)
            return
        if run(*arguments):
            failures.append(name)
            if tier < 3:
                stopped = True

    print(
        f"[validate] tier {tier} ({TIER_NAMES[tier]}); "
        "use --tier quick|standard|full to change the depth",
        flush=True,
    )

    _run(1, "scripts/audit_repository.py")
    _run(1, "scripts/validate_schemas.py")
    _run(
        2,
        "scripts/generate_smoke_evidence.py",
        "research/experiments/manifests/m3-smoke.yaml",
        "research/output/runs/smoke",
        "--check",
    )
    if (ROOT / "research" / "output" / "runs" / "native-sled-reproduction-v1").is_dir():
        _run(
            2,
            "scripts/generate_native_sled_evidence.py",
            "research/output/runs/native-sled-reproduction-v1",
            "--check",
        )
    if (ROOT / "research" / "output" / "runs" / "sled-coi-reduction-v1").is_dir():
        _run(
            2,
            "scripts/generate_coi_evidence.py",
            "research/output/runs/sled-coi-reduction-v1",
            "--check",
        )
    if (ROOT / "research" / "output" / "runs" / "cedar-differential-preflight-v1").is_dir():
        _run(
            2,
            "scripts/generate_cedar_preflight.py",
            "research/output/runs/cedar-differential-preflight-v1",
            "--check",
        )
    if (ROOT / "research" / "output" / "runs" / "direction-readiness-v1").is_dir():
        _run(
            2,
            "scripts/generate_direction_evidence.py",
            "research/output/runs/direction-readiness-v1",
            "--check",
        )
    if tier == 1:
        _run(
            1,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-x",
            "-q",
            *(f"--ignore={path}" for path in SLOW_TEST_PATHS),
            f"--basetemp={SESSION_ROOT / 'pytest'}",
        )
    else:
        _run(
            2,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--cov=conflux",
            "--cov-branch",
            "--cov-report=term-missing",
            "--cov-fail-under=89",
            f"--basetemp={SESSION_ROOT / 'pytest'}",
        )
    if stopped:
        after_failure.append(DOCTEST_CHECK)
    elif tier < 2:
        not_run.append(DOCTEST_CHECK)
    elif run_doctests():
        failures.append(DOCTEST_CHECK)
        if tier < 3:
            stopped = True
    _run(
        2,
        "-m",
        "pytest",
        "tests/test_omitted_coverage.py",
        "-q",
        f"--basetemp={SESSION_ROOT / 'omitted'}",
    )
    _run(1, "-m", "ruff", "check", ".")
    _run(2, "-m", "mypy", ".", "--no-error-summary")
    _run(2, "-m", "yamllint", "-c", ".yamllint.yml", ".")
    _run(2, "-m", "vulture", "src/conflux", "scripts/vulture_whitelist.py", "--min-confidence", "60")
    if stopped:
        after_failure.append("pip_audit")
    elif tier < 3:
        not_run.append("pip_audit")
    else:
        run_info("-m", "pip_audit", "--skip-editable", "-f", "json")
    _run(3, "-m", "build", "--wheel", "--no-isolation", "--outdir", "dist")
    _run(3, "scripts/validate_wheel.py")
    _run(3, "scripts/validate_extensions.py")
    if failures:
        print(f"[validate] tier {tier} ({TIER_NAMES[tier]}): {len(failures)} check(s) failed:")
        for name in failures:
            print(f"  - {name}")
        if after_failure:
            print(f"[validate] {len(after_failure)} check(s) not run after the failure:")
            for name in after_failure:
                print(f"  - {name}")
        return 1
    rmtree(SESSION_ROOT)
    print(f"[validate] tier {tier} ({TIER_NAMES[tier]}): all checks passed")
    if not_run:
        print(f"[validate] {len(not_run)} slower check(s) skipped at this tier:")
        for name in not_run:
            print(f"  - {name}")
        if tier < 3:
            print(
                "[validate] run the next tier before committing: "
                f"python scripts/validate.py --tier {TIER_NAMES[tier + 1]}",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
