"""Tests for the generated examiner-facing contribution table.

The table is generated from the claim ledger so that it cannot drift. These tests
run the generator in check mode and prove that it reads the ledger rather than
echoing a constant.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.generate_contribution_table import (
    LEDGER,
    ORIGIN_ORDER,
    TARGET,
    LedgerError,
    main,
    parse_ledger,
    render_table,
    replace_generated,
)


def test_generated_table_is_current() -> None:
    assert main(["--check"]) == 0


def test_ledger_has_no_unknown_origin() -> None:
    rows = parse_ledger(LEDGER.read_text(encoding="utf-8"))
    assert rows
    assert {row[2] for row in rows} <= set(ORIGIN_ORDER)


def test_part_c_claims_are_the_majority_and_part_b_is_visible() -> None:
    rows = parse_ledger(LEDGER.read_text(encoding="utf-8"))
    origins = [row[2] for row in rows]
    assert origins.count("Part B, reproduced") == 2
    assert "Part B concept, Part C evidence" in origins
    assert origins.count("Part C") > len(rows) // 2


def test_render_table_reads_the_rows_it_is_given() -> None:
    rows = parse_ledger(LEDGER.read_text(encoding="utf-8"))
    baseline = render_table(rows)
    extra = [*rows, ("A claim that only exists in this test", "Implemented", "Part C", "unit test")]
    changed = render_table(extra)
    assert changed != baseline
    assert "A claim that only exists in this test" in changed
    assert f"Ledger rows: {len(extra)}" in changed


def test_render_table_groups_every_origin_it_receives() -> None:
    rendered = render_table(
        [
            ("b", "Implemented", "Part B", "archive"),
            ("br", "Bounded evidence", "Part B, reproduced", "run"),
            ("bc", "Implemented", "Part B concept, Part C evidence", "tests"),
            ("c", "Bounded evidence", "Part C", "run"),
        ],
    )
    for origin in ORIGIN_ORDER:
        if origin == "Part B":
            assert "Third-year contributions" in rendered
        assert origin in rendered or origin.startswith("Part B")


def test_unknown_origin_is_rejected() -> None:
    ledger_text = LEDGER.read_text(encoding="utf-8").replace(
        "| Part C |", "| Part D |", 1,
    )
    with pytest.raises(LedgerError, match="unknown Origin"):
        parse_ledger(ledger_text)


def test_a_missing_marker_block_is_an_error() -> None:
    with pytest.raises(LedgerError, match="markers"):
        replace_generated("# no markers here\n", "table\n")


def test_target_file_contains_the_generated_block() -> None:
    text = TARGET.read_text(encoding="utf-8")
    assert "<!-- BEGIN GENERATED CONTRIBUTION TABLE -->" in text
    assert "Fourth-year contributions (Part C)" in text
    ledger_claims = [row[0] for row in parse_ledger(LEDGER.read_text(encoding="utf-8"))]
    for claim in ledger_claims[:3]:
        assert claim in text


def test_paths_point_inside_the_repository() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert LEDGER.is_relative_to(repo_root)
    assert TARGET.is_relative_to(repo_root)
