"""Query the task registry and claim ledger for prioritised gaps.

Read-only script that produces a Markdown gap report for pasting into external
AI planning sessions. Reports:

- Claims with status "Not yet evidenced" or "Not claimed"
- Tasks with status "partial", "deferred", "externally_gated", or
  "evaluation_ready"
- Recent git commits for session context

Usage::

    python scripts/query_tasks.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_REGISTRY = ROOT / "docs" / "evidence" / "task-registry.json"
CLAIMS = ROOT / "docs" / "evidence" / "CLAIMS.md"

PRIORITY_STATUSES = {
    "partial",
    "deferred",
    "externally_gated",
    "evaluation_ready",
}

CLAIM_GAP_STATUSES = {
    "Not yet evidenced",
    "Not claimed",
}


def _load_task_registry() -> dict[str, object]:
    with TASK_REGISTRY.open(encoding="utf-8") as fh:
        data: object = json.load(fh)
    assert isinstance(data, dict)
    return data


def _parse_claims() -> list[dict[str, str]]:
    """Parse the CLAIMS.md markdown table into structured rows."""
    rows: list[dict[str, str]] = []
    in_table = False
    for line in CLAIMS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("| Claim") and "---" not in stripped:
            in_table = True
            continue
        if in_table and stripped.startswith("|---"):
            continue
        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) >= 3:
                rows.append(
                    {"claim": cells[0], "status": cells[1], "evidence": cells[2]},
                )
        elif in_table and not stripped.startswith("|"):
            in_table = False
    return rows


def _recent_commits(count: int = 5) -> list[str]:
    """Return the last ``count`` commit subjects."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--format=%h %s"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=True,
            timeout=10,
        )
        return result.stdout.strip().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ["(git log unavailable)"]


def _format_report(
    registry: dict[str, object],
    claims: list[dict[str, str]],
    commits: list[str],
) -> str:
    lines: list[str] = []

    lines.append("# Task Gap Report")
    lines.append("")
    lines.append(f"Generated from `{TASK_REGISTRY.relative_to(ROOT)}`")
    lines.append(f"and `{CLAIMS.relative_to(ROOT)}`.")
    lines.append("")

    # Recent commits
    lines.append("## Recent commits")
    lines.append("")
    for c in commits:
        lines.append(f"- {c}")
    lines.append("")

    # Task registry gaps
    lines.append("## Task registry gaps")
    lines.append("")
    groups = registry.get("groups", [])
    assert isinstance(groups, list)
    gap_groups: list[tuple[str, list[str], str | None]] = []
    for group in groups:
        assert isinstance(group, dict)
        status = group.get("status", "")
        assert isinstance(status, str)
        if status in PRIORITY_STATUSES:
            ids = group.get("ids", [])
            assert isinstance(ids, list)
            gap = group.get("gap")
            assert gap is None or isinstance(gap, str)
            gap_groups.append((status, [str(i) for i in ids], gap))

    if gap_groups:
        for status, ids, gap in gap_groups:
            lines.append(f"### {status}")
            lines.append("")
            lines.append(f"Tasks: {', '.join(ids)}")
            if gap:
                lines.append(f"Gap: {gap}")
            lines.append("")
    else:
        lines.append("_No gaps found in task registry._")
        lines.append("")

    # Deferred research
    deferred = registry.get("deferred_research", [])
    assert isinstance(deferred, list)
    if deferred:
        lines.append("## Deferred research directions")
        lines.append("")
        for item in deferred:
            assert isinstance(item, str)
            lines.append(f"- {item}")
        lines.append("")

    # Claim gaps
    lines.append("## Claim gaps")
    lines.append("")
    gap_claims = [cl for cl in claims if cl["status"] in CLAIM_GAP_STATUSES]
    if gap_claims:
        for cl in gap_claims:
            lines.append(f"- **{cl['claim']}** — {cl['status']}")
            if cl["evidence"]:
                lines.append(f"  Evidence: {cl['evidence']}")
        lines.append("")
    else:
        lines.append("_No claims with gap status found._")
        lines.append("")

    # Bounded evidence (informational)
    bounded_claims = [cl for cl in claims if "Bounded" in cl["status"] or "bounded" in cl["status"]]
    if bounded_claims:
        lines.append("## Bounded evidence (review for upgrade opportunities)")
        lines.append("")
        for cl in bounded_claims:
            lines.append(f"- **{cl['claim']}** — {cl['status']}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    if not TASK_REGISTRY.exists():
        print(f"error: {TASK_REGISTRY} not found", file=sys.stderr)
        return 1
    if not CLAIMS.exists():
        print(f"error: {CLAIMS} not found", file=sys.stderr)
        return 1

    registry = _load_task_registry()
    claims = _parse_claims()
    commits = _recent_commits()
    report = _format_report(registry, claims, commits)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
