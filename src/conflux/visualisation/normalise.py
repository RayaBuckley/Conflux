"""Canonical ordering helpers for deterministic visualisation output.

These helpers ensure that Principals, artifacts, and other multi-element
collections are always displayed in the same order regardless of
insertion order, making visual output reproducible.
"""

from __future__ import annotations

from collections.abc import Iterable


def sorted_principals(principals: Iterable[str]) -> list[str]:
    """Return principals in canonical (alphabetical) order."""
    return sorted(set(principals))


def sorted_artifacts(artifacts: Iterable[str]) -> list[str]:
    """Return artifact keys in canonical (alphabetical) order."""
    return sorted(set(artifacts))


def sorted_node_ids(ids: Iterable[str]) -> list[str]:
    """Return node IDs in canonical (alphabetical) order."""
    return sorted(set(ids))


def truncate_label(text: str, max_length: int = 60) -> str:
    """Truncate a label to ``max_length`` characters with an ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def safe_label(text: str) -> str:
    """Return a label safe for SVG/HTML rendering.

    This does not perform full HTML escaping (the renderer does that).
    It replaces newlines and control characters that would break layout.
    """
    return text.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()
