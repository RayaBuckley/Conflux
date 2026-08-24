"""Tests for canonical ordering and label helpers."""

from __future__ import annotations

from conflux.visualisation.normalise import (
    safe_label,
    sorted_artifacts,
    sorted_principals,
    truncate_label,
)


class TestSortedPrincipals:
    def test_sorts_alphabetically(self) -> None:
        assert sorted_principals(["Bob", "Alice"]) == ["Alice", "Bob"]

    def test_deduplicates(self) -> None:
        assert sorted_principals(["Alice", "Alice", "Bob"]) == ["Alice", "Bob"]

    def test_empty(self) -> None:
        assert sorted_principals([]) == []


class TestSortedArtifacts:
    def test_sorts_alphabetically(self) -> None:
        assert sorted_artifacts(["doc_b", "doc_a"]) == ["doc_a", "doc_b"]


class TestTruncateLabel:
    def test_short_label_unchanged(self) -> None:
        assert truncate_label("short", max_length=60) == "short"

    def test_long_label_truncated(self) -> None:
        text = "x" * 70
        result = truncate_label(text, max_length=60)
        assert len(result) == 60
        assert result.endswith("...")

    def test_exact_length(self) -> None:
        text = "x" * 60
        assert truncate_label(text, max_length=60) == text


class TestSafeLabel:
    def test_replaces_newlines(self) -> None:
        assert safe_label("line1\nline2") == "line1 line2"

    def test_replaces_tabs(self) -> None:
        assert safe_label("col1\tcol2") == "col1 col2"

    def test_strips_whitespace(self) -> None:
        assert safe_label("  text  ") == "text"
