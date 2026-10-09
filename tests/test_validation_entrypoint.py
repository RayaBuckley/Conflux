"""Portable validation diagnostics."""

import pytest

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
