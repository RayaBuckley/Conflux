"""Portable validation diagnostics."""

import pytest

from scripts.validate import _workflow_escape

pytestmark = pytest.mark.integration


def test_workflow_diagnostics_escape_control_characters() -> None:
    assert _workflow_escape("failure 100%\r\nnext") == "failure 100%25%0D%0Anext"
