"""Portable validation diagnostics."""

from scripts.validate import _workflow_escape


def test_workflow_diagnostics_escape_control_characters() -> None:
    assert _workflow_escape("failure 100%\r\nnext") == "failure 100%25%0D%0Anext"
