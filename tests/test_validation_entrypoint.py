"""Portable validation diagnostics."""

import sys
import time
from pathlib import Path

import pytest

from scripts import validate as validate_module
from scripts.validate import TIER_NAMES, _parse_tier, _workflow_escape

pytestmark = pytest.mark.integration


def test_workflow_diagnostics_escape_control_characters() -> None:
    assert _workflow_escape("failure 100%\r\nnext") == "failure 100%25%0D%0Anext"


def test_default_tier_is_the_whole_pipeline() -> None:
    """Continuous integration runs validate.py without arguments."""
    assert _parse_tier([]) == 3
    assert TIER_NAMES[3] == "full"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("quick", 1), ("standard", 2), ("full", 3), ("1", 1), ("2", 2), ("3", 3)],
)
def test_tier_aliases(value: str, expected: int) -> None:
    assert _parse_tier([f"--tier={value}"]) == expected
    assert _parse_tier(["--tier", value]) == expected


@pytest.mark.parametrize("arguments", [["--tier"], ["--tier", "deep"], ["--tier="]])
def test_unknown_tier_is_rejected(arguments: list[str]) -> None:
    with pytest.raises(SystemExit):
        _parse_tier(arguments)


class _RecordingCheck:
    """Record the checks ``main`` would run without executing any of them."""

    def __init__(self, fail_at: str | None = None, doctest_returncode: int = 0) -> None:
        self.fail_at = fail_at
        self.doctest_returncode = doctest_returncode
        self.invoked: list[str] = []
        self.informational: list[str] = []
        self.doctests: list[str] = []

    def run(self, *arguments: str) -> int:
        name = " ".join(arguments)
        self.invoked.append(name)
        return 1 if name == self.fail_at else 0

    def run_info(self, *arguments: str) -> int:
        self.informational.append(" ".join(arguments))
        return 0

    def run_doctests(self) -> int:
        self.doctests.append("pytest --doctest-modules src/conflux/domain -q")
        return self.doctest_returncode


class _CompletedStub:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _completed(*arguments: object, **keywords: object) -> _CompletedStub:
    return _CompletedStub()


def _drive_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *tier_arguments: str,
    fail_at: str | None = None,
    doctest_returncode: int = 0,
) -> tuple[_RecordingCheck, str, int]:
    """Run ``main`` with every subprocess replaced by a recorder."""
    validate_module.SESSION_ROOT.mkdir(parents=True, exist_ok=True)
    recorder = _RecordingCheck(fail_at, doctest_returncode)
    monkeypatch.setattr(validate_module, "run", recorder.run)
    monkeypatch.setattr(validate_module, "run_info", recorder.run_info)
    monkeypatch.setattr(validate_module, "run_doctests", recorder.run_doctests)
    monkeypatch.setattr("subprocess.run", _completed)
    monkeypatch.setattr(sys, "argv", ["scripts/validate.py", *tier_arguments])
    exit_code = validate_module.main()
    return recorder, capsys.readouterr().out, exit_code


def test_bytecode_purge_deletes_source_caches_and_spares_vendor_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stale cache must not survive the run; a vendor cache must not be touched."""
    (tmp_path / "src" / "pkg" / "__pycache__").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__pycache__" / "mod.cpython-312.pyc").write_bytes(b"stale")
    (tmp_path / "src" / "pkg" / "keep.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests" / "__pycache__").mkdir(parents=True)
    (tmp_path / ".local" / "cache" / "__pycache__").mkdir(parents=True)
    (tmp_path / ".local" / "cache" / "__pycache__" / "session.pyc").write_bytes(b"session")
    (tmp_path / ".venv" / "lib" / "__pycache__").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "__pycache__" / "dep.pyc").write_bytes(b"vendor")
    monkeypatch.setattr(validate_module, "ROOT", tmp_path)

    trees, files = validate_module.purge_bytecode_caches()

    assert (trees, files) == (2, 1)
    assert not (tmp_path / "src" / "pkg" / "__pycache__").exists()
    assert not (tmp_path / "tests" / "__pycache__").exists()
    assert (tmp_path / "src" / "pkg" / "keep.py").exists()
    assert (tmp_path / ".local" / "cache" / "__pycache__" / "session.pyc").exists()
    assert (tmp_path / ".venv" / "lib" / "__pycache__" / "dep.pyc").exists()


def test_every_tier_purges_bytecode_caches_before_its_first_step(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The purge must run in the same pass as the steps, and say what it removed."""
    calls: list[str] = []

    def fake_purge() -> tuple[int, int]:
        calls.append("purged")
        return (2, 3)

    monkeypatch.setattr(validate_module, "purge_bytecode_caches", fake_purge)
    _recorder, output, exit_code = _drive_main(monkeypatch, capsys, "--tier", "quick")
    assert exit_code == 0
    assert calls == ["purged"]
    assert "[validate] purged 3 bytecode file(s) from 2 __pycache__ tree(s)" in output
    # the purge line precedes the first recorded step, not only the summary
    assert output.index("[validate] purged") < output.index("slower check(s) skipped at this tier")
    assert _recorder.invoked[0] == "scripts/audit_repository.py"


def test_quick_tier_selects_the_fast_subset(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The quick tier must skip the slow evidence file and every deep step."""
    recorder, output, exit_code = _drive_main(monkeypatch, capsys, "--tier", "quick")
    assert exit_code == 0
    pytest_calls = [call for call in recorder.invoked if call.startswith("-m pytest")]
    assert len(pytest_calls) == 1
    assert "--ignore=tests/test_sledv_scaling_evidence.py" in pytest_calls[0]
    assert " -x " in pytest_calls[0]
    assert "--cov" not in pytest_calls[0]
    assert any("audit_repository.py" in call for call in recorder.invoked)
    assert any("validate_schemas.py" in call for call in recorder.invoked)
    assert any("-m ruff check ." in call for call in recorder.invoked)
    deep = ("-m build", "validate_wheel.py", "validate_extensions.py", "pip_audit", "-m mypy", "yamllint", "vulture")
    assert not any(step in call for call in recorder.invoked for step in deep)
    assert recorder.informational == []
    assert recorder.doctests == []
    assert not any("--check" in call for call in recorder.invoked)
    assert "slower check(s) skipped at this tier" in output
    assert "-m mypy . --no-error-summary" in output
    assert "pytest --doctest-modules src/conflux/domain -q" in output
    assert "tests/test_omitted_coverage.py" in output
    assert "python scripts/validate.py --tier standard" in output


def test_standard_tier_runs_the_whole_suite_with_the_coverage_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The standard tier must run the complete suite, not the quick subset."""
    recorder, output, exit_code = _drive_main(monkeypatch, capsys, "--tier", "standard")
    assert exit_code == 0
    pytest_calls = [call for call in recorder.invoked if call.startswith("-m pytest")]
    suite = [call for call in pytest_calls if "--cov=conflux" in call]
    assert len(suite) == 1
    assert "--cov=conflux" in suite[0]
    assert "--cov-branch" in suite[0]
    assert "--cov-fail-under=89" in suite[0]
    assert "--ignore=" not in suite[0]
    assert len(recorder.doctests) == 1
    assert any("generate_smoke_evidence.py" in call and "--check" in call for call in recorder.invoked)
    assert any("audit_repository.py" in call for call in recorder.invoked)
    assert any("validate_schemas.py" in call for call in recorder.invoked)
    assert any("tests/test_omitted_coverage.py" in call for call in pytest_calls)
    assert any("-m mypy ." in call for call in recorder.invoked)
    assert any("yamllint" in call for call in recorder.invoked)
    assert any("vulture" in call for call in recorder.invoked)
    assert not any(step in call for call in recorder.invoked for step in ("-m build", "validate_wheel.py", "validate_extensions.py"))
    assert recorder.informational == []
    assert "pip_audit" in output
    assert "python scripts/validate.py --tier full" in output


class _Clock:
    """A monotonic stand-in for time.perf_counter that the recorder advances."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class _CostlyCheck(_RecordingCheck):
    """Advance the clock so the slowest step is known without running it."""

    def __init__(self, clock: _Clock) -> None:
        super().__init__()
        self.clock = clock

    def run(self, *arguments: str) -> int:
        name = " ".join(arguments)
        self.clock.now += 104.0 if "--cov=conflux" in name else 0.5
        return super().run(*arguments)


def test_the_summary_names_the_step_that_cost_the_most(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The tier choice is about cost, so the run must report where the seconds went."""
    validate_module.SESSION_ROOT.mkdir(parents=True, exist_ok=True)
    clock = _Clock()
    recorder = _CostlyCheck(clock)
    monkeypatch.setattr(validate_module, "run", recorder.run)
    monkeypatch.setattr(validate_module, "run_info", recorder.run_info)
    monkeypatch.setattr(validate_module, "run_doctests", recorder.run_doctests)
    monkeypatch.setattr(time, "perf_counter", clock)
    monkeypatch.setattr("subprocess.run", _completed)
    monkeypatch.setattr(sys, "argv", ["scripts/validate.py", "--tier", "standard"])

    assert validate_module.main() == 0
    output = capsys.readouterr().out
    line = next(text for text in output.splitlines() if text.startswith("[validate] slowest steps:"))
    assert "--cov=conflux" in line.split(",")[0]
    assert "total" in line
    assert "104.0 s" in line


def test_the_paper_tables_are_checked_and_a_drift_fails_the_tier(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The manuscript's tables are generated from evidence; a gate must watch them.

    ``generate_flmsec_tables.py --check`` was green for weeks while nothing ran it,
    so a regeneration that moved a published number would have gone unnoticed.
    """
    recorder, _, exit_code = _drive_main(monkeypatch, capsys, "--tier", "standard")
    assert exit_code == 0
    assert "scripts/generate_flmsec_tables.py --check" in recorder.invoked

    failing, output, exit_code = _drive_main(
        monkeypatch,
        capsys,
        "--tier",
        "standard",
        fail_at="scripts/generate_flmsec_tables.py --check",
    )
    assert exit_code == 1
    assert "generate_flmsec_tables.py --check" in output
    assert "scripts/generate_flmsec_tables.py --check" in failing.invoked


def test_full_tier_runs_the_packaging_and_extension_checks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No argument means the whole pipeline, including the informational audit."""
    recorder, output, exit_code = _drive_main(monkeypatch, capsys)
    assert exit_code == 0
    assert any("-m build" in call for call in recorder.invoked)
    assert any("validate_wheel.py" in call for call in recorder.invoked)
    assert any("validate_extensions.py" in call for call in recorder.invoked)
    assert any("pip_audit" in call for call in recorder.informational)
    assert "all checks passed" in output
    assert "skipped at this tier" not in output


def test_tier_below_full_stops_at_the_first_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A lower tier fails fast and names the checks it did not reach."""
    recorder, output, exit_code = _drive_main(
        monkeypatch,
        capsys,
        "--tier",
        "standard",
        fail_at="scripts/validate_schemas.py",
    )
    assert exit_code == 1
    assert "1 check(s) failed" in output
    assert "not run after the failure" in output
    assert not any("-m mypy" in call for call in recorder.invoked)
    assert not any("vulture" in call for call in recorder.invoked)


def test_full_tier_reports_every_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The full tier keeps going so continuous integration sees all failures."""
    recorder, output, exit_code = _drive_main(
        monkeypatch,
        capsys,
        fail_at="scripts/validate_schemas.py",
    )
    assert exit_code == 1
    assert any("validate_extensions.py" in call for call in recorder.invoked)
    assert "not run after the failure" not in output


def test_standard_tier_stops_when_the_doctests_fail(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failing doctest step must be a failure that stops the lower tiers."""
    recorder, output, exit_code = _drive_main(
        monkeypatch,
        capsys,
        "--tier",
        "standard",
        doctest_returncode=1,
    )
    assert exit_code == 1
    assert len(recorder.doctests) == 1
    assert "pytest --doctest-modules src/conflux/domain -q" in output
    assert "not run after the failure" in output
    assert not any("-m mypy" in call for call in recorder.invoked)


def test_full_tier_survives_a_failing_doctest_step(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The full tier reports the doctest failure and still runs everything."""
    recorder, output, exit_code = _drive_main(monkeypatch, capsys, doctest_returncode=1)
    assert exit_code == 1
    assert len(recorder.doctests) == 1
    assert any("validate_extensions.py" in call for call in recorder.invoked)
    assert "not run after the failure" not in output


@pytest.mark.parametrize(("returncode", "expected"), [(0, 0), (5, 0), (1, 1), (2, 2)])
def test_doctest_step_maps_the_pytest_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    returncode: int,
    expected: int,
) -> None:
    """Exit code 5 (no doctests collected) is success; anything else is a failure."""
    monkeypatch.setattr("subprocess.run", lambda *arguments, **keywords: _CompletedStub(returncode))
    assert validate_module.run_doctests() == expected
    output = capsys.readouterr().out
    if returncode == 5:
        # The empty collection is the normal case today, so it must be visible.
        assert "no doctests collected" in output
    else:
        assert "no doctests collected" not in output
