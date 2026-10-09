"""Generate the examiner-facing contribution table from the claim ledger.

The fourth-year report must state which parts of the work are third-year
(Part B) contributions and which are fourth-year (Part C) contributions; see
docs/decisions/026-continuation-and-contribution-provenance.md. The table is
generated from docs/evidence/CLAIMS.md so it cannot drift from the evidence.

Usage:
    python scripts/generate_contribution_table.py            # rewrite the table
    python scripts/generate_contribution_table.py --check     # fail if stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER = REPO_ROOT / "docs" / "evidence" / "CLAIMS.md"
TARGET = REPO_ROOT / "docs" / "evidence" / "CONTRIBUTION_PROVENANCE.md"

BEGIN = "<!-- BEGIN GENERATED CONTRIBUTION TABLE -->"
END = "<!-- END GENERATED CONTRIBUTION TABLE -->"

# Report order: prior work first, then work that mixes both phases, then the
# new fourth-year contribution.
ORIGIN_ORDER = (
    "Part B",
    "Part B, reproduced",
    "Part B concept, Part C evidence",
    "Part C",
)
ORIGIN_HEADING = {
    "Part B": "Third-year contributions (Part B)",
    "Part B, reproduced": "Third-year results reproduced here",
    "Part B concept, Part C evidence": "Third-year mechanisms with fourth-year evidence",
    "Part C": "Fourth-year contributions (Part C)",
}
LEDGER_HEADER = "| Claim | Status | Origin | Evidence and limits |"
LEDGER_SEPARATOR = "| --- | --- | --- | --- |"


class LedgerError(RuntimeError):
    """Raised when the claim ledger cannot be parsed."""


def parse_ledger(text: str) -> list[tuple[str, str, str, str]]:
    """Return (claim, status, origin, evidence) rows in ledger order."""
    rows: list[tuple[str, str, str, str]] = []
    header_seen = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == LEDGER_HEADER:
            header_seen = True
            continue
        if not header_seen or not stripped.startswith("|"):
            continue
        if stripped in (LEDGER_SEPARATOR, LEDGER_HEADER):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 4:
            raise LedgerError(f"expected 4 columns, found {len(cells)}: {stripped[:80]}")
        rows.append((cells[0], cells[1], cells[2], cells[3]))
    if not rows:
        raise LedgerError("no claim rows found in the ledger")
    unknown = sorted({origin for _, _, origin, _ in rows} - set(ORIGIN_ORDER))
    if unknown:
        raise LedgerError(f"unknown Origin value(s): {unknown}")
    return rows


def render_table(rows: list[tuple[str, str, str, str]]) -> str:
    """Render one markdown table per origin group."""
    blocks: list[str] = []
    for origin in ORIGIN_ORDER:
        group = [row for row in rows if row[2] == origin]
        if not group:
            continue
        label = "claim" if len(group) == 1 else "claims"
        blocks.append(f"### {ORIGIN_HEADING[origin]} ({len(group)} {label})")
        blocks.append("")
        blocks.append("| Claim | Status | Evidence and limits |")
        blocks.append("| --- | --- | --- |")
        blocks.extend(f"| {claim} | {status} | {evidence} |" for claim, status, _, evidence in group)
        blocks.append("")
    totals = ", ".join(
        f"{origin}: {sum(1 for row in rows if row[2] == origin)}" for origin in ORIGIN_ORDER
    )
    blocks.append(f"Ledger rows: {len(rows)} ({totals}).")
    return "\n".join(blocks).rstrip() + "\n"


def replace_generated(text: str, table: str) -> str:
    """Return text with the generated block replaced by table."""
    start = text.find(BEGIN)
    end = text.find(END)
    if start == -1 or end == -1 or end < start:
        raise LedgerError(f"markers {BEGIN} / {END} not found in the target file")
    head, tail = text[: start + len(BEGIN)], text[end:]
    return f"{head}\n\n{table}\n{tail}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 if the table is stale")
    args = parser.parse_args(argv)

    rows = parse_ledger(LEDGER.read_text(encoding="utf-8"))
    rendered = render_table(rows)
    current = TARGET.read_text(encoding="utf-8")
    updated = replace_generated(current, rendered)

    if args.check:
        if updated != current:
            print("contribution table is stale; run scripts/generate_contribution_table.py", file=sys.stderr)
            return 1
        print(f"contribution table is current ({len(rows)} ledger rows)")
        return 0

    TARGET.write_text(updated, encoding="utf-8")
    print(f"wrote {TARGET.relative_to(REPO_ROOT)} from {len(rows)} ledger rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
