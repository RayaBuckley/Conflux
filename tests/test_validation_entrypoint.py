"""Portable validation diagnostics."""

import sys

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

    def __init__(self, fail_at: str | None = None) -> None:
        self.fail_at = fail_at
        self.invoked: list[str] = []
        self.informational: list[str] = []

    def run(self, *arguments: str) -> int:
        name = " ".join(arguments)
        self.invoked.append(name)
        return 1 if name == self.fail_at else 0

    def run_info(self, *arguments: str) -> int:
        self.informational.append(" ".join(arguments))
        return 0


class _CompletedStub:
    returncode = 0


def _completed(*arguments: object, **keywords: object) -> _CompletedStub:
    return _CompletedStub()


def _drive_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *tier_arguments: str,
    fail_at: str | None = None,
) -> tuple[_RecordingCheck, str, int]:
    """Run ``main`` with every subprocess replaced by a recorder."""
    validate_module.SESSION_ROOT.mkdir(parents=True, exist_ok=True)
    recorder = _RecordingCheck(fail_at)
    monkeypatch.setattr(validate_module, "run", recorder.run)
    monkeypatch.setattr(validate_module, "run_info", recorder.run_info)
    monkeypatch.setattr("subprocess.run", _completed)
    monkeypatch.setattr(sys, "argv", ["scripts/validate.py", *tier_arguments])
    exit_code = validate_module.main()
    return recorder, capsys.readouterr().out, exit_code


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
    assert not any("--check" in call for call in recorder.invoked)
    assert "slower check(s) skipped at this tier" in output
    assert "-m mypy . --no-error-summary" in output
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
