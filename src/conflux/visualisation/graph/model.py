"""Layout configuration for graph rendering.

Layout options are fixed (not random) to ensure deterministic output.
The renderer receives a ``LayoutOptions`` object that controls graph
direction, rank spacing, and other deterministic layout parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LayoutDirection(Enum):
    """Direction of graph layout."""

    TOP_TO_BOTTOM = "TB"
    LEFT_TO_RIGHT = "LR"
    BOTTOM_TO_TOP = "BT"
    RIGHT_TO_LEFT = "RL"


@dataclass(frozen=True)
class LayoutOptions:
    """Fixed layout options for deterministic graph rendering.

    All values are fixed (not random) to ensure reproducible output.
    """

    direction: LayoutDirection = LayoutDirection.TOP_TO_BOTTOM
    ranksep: str = "0.5"
    nodesep: str = "0.4"
    fontname: str = "Helvetica"
    fontsize: str = "10"

    def to_dict(self) -> dict[str, str]:
        """Serialise to a JSON-compatible dictionary."""
        return {
            "direction": self.direction.value,
            "ranksep": self.ranksep,
            "nodesep": self.nodesep,
            "fontname": self.fontname,
            "fontsize": self.fontsize,
        }
