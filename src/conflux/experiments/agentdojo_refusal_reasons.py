"""Derive the refusing rule for retained blocked records that carry no reason.

The retained AgentDojo bundles were written before a mediation record copied the refusing rule into its
own ``reason`` field, so their blocked records read as policy refusals by outcome alone. Every one of
those records still keeps the whole ITES report, and the refusing decision sits in that report's trace.
This module reads the retained bundles, derives the rule for each blocked record that carries no reason,
and returns a table a reader can check row by row. Nothing is re-run: no model, no provider, no network.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from conflux.domain import canonical_json
from conflux.experiments.agentdojo_refusal_evidence import refusing_rule_from_retained_report

AGENTDOJO_REFUSAL_REASONS_FILES = frozenset({"CHECKSUMS.sha256", "README.md", "refusal-reasons.json"})
"""Files the retained refusal-reasons bundle holds."""

DEFAULT_RUNS_ROOT = Path("research/output/runs")
"""Directory whose ``agentdojo-*`` bundles are read, relative to the repository root."""

_COUNT_KEYS = (
    "cells",
    "records",
    "blocked",
    "blocked_named",
    "blocked_unnamed",
    "derived",
    "underivable",
)


def _read_json(path: Path) -> dict[str, Any]:
    """Return the parsed contents of a JSON file."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def derive_refusal_reason_rows(runs_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(rows, bundles)`` for every blocked record whose record carries no reason.

    Rows are ordered by bundle name, then by cell and record position, so two runs of this function
    over the same tree produce the same table.
    """
    rows: list[dict[str, Any]] = []
    bundles: list[dict[str, Any]] = []
    for directory in sorted((path for path in runs_root.glob("agentdojo-*") if path.is_dir()), key=lambda path: path.name):
        result_path = directory / "result.json"
        if not result_path.is_file():
            continue
        payload = _read_json(result_path)
        counts = dict.fromkeys(_COUNT_KEYS, 0)
        for cell_index, cell in enumerate(cast(list[dict[str, Any]], payload.get("cells", []))):
            counts["cells"] += 1
            for record_index, record in enumerate(cast(list[dict[str, Any]], cell.get("augmentation") or [])):
                counts["records"] += 1
                if record.get("outcome") != "blocked":
                    continue
                counts["blocked"] += 1
                if record.get("reason"):
                    counts["blocked_named"] += 1
                    continue
                counts["blocked_unnamed"] += 1
                report = record.get("report")
                derived = refusing_rule_from_retained_report(report) if isinstance(report, Mapping) else None
                counts["derived" if derived else "underivable"] += 1
                rows.append(
                    {
                        "bundle": directory.name,
                        "result_json": f"{runs_root.as_posix()}/{directory.name}/result.json",
                        "cell": cell_index,
                        "record": record_index,
                        "case_id": cell.get("case_id"),
                        "defence": cell.get("defence"),
                        "tool": record.get("tool"),
                        "arguments_sha256": record.get("arguments_sha256"),
                        "reason": record.get("reason"),
                        "derived_reason": (derived or {}).get("reason"),
                        "derived_policy_id": (derived or {}).get("policy_id"),
                        "derived_policy_dimension": (derived or {}).get("policy_dimension"),
                    },
                )
        bundles.append({"bundle": directory.name, "result_json": f"{runs_root.as_posix()}/{directory.name}/result.json", **counts})
    return rows, bundles


def _counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Return the counted values of one row field, in a stable order."""
    counted = Counter(str(row[key]) for row in rows if row[key] is not None)
    return {name: counted[name] for name in sorted(counted)}


def refusal_reason_totals(rows: list[dict[str, Any]], bundles: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the totals a reader checks the rows against, counted in this same pass."""
    derived = sum(1 for row in rows if row["derived_reason"])
    return {
        "bundles_read": len(bundles),
        "records_listed": len(rows),
        "records_derived": derived,
        "records_underivable": len(rows) - derived,
        "by_policy_id": _counter(rows, "derived_policy_id"),
        "by_policy_dimension": _counter(rows, "derived_policy_dimension"),
        "by_reason": _counter(rows, "derived_reason"),
        "by_tool": _counter(rows, "tool"),
    }


def refusal_reason_checks(
    rows: list[dict[str, Any]],
    bundles: list[dict[str, Any]],
    totals: Mapping[str, Any],
) -> dict[str, bool]:
    """Return the self-checks that hold for a well-formed table."""
    adapter_vocabulary = _adapter_refusal_vocabulary()
    derived_reasons = {str(row["derived_reason"]) for row in rows if row["derived_reason"]}
    listed = sum(int(bundle["blocked_unnamed"]) for bundle in bundles)
    derived = int(totals["records_derived"])
    counted = (
        sum(cast(dict[str, int], totals["by_policy_id"]).values()),
        sum(cast(dict[str, int], totals["by_policy_dimension"]).values()),
        sum(cast(dict[str, int], totals["by_reason"]).values()),
    )
    return {
        "every_unnamed_blocked_record_is_listed": int(totals["records_listed"]) == listed,
        "no_listed_record_carries_a_reason": all(not row["reason"] for row in rows),
        "each_row_is_either_fully_derived_or_not_derived_at_all": all(
            (row["derived_reason"] is None) == (row["derived_policy_id"] is None) == (row["derived_policy_dimension"] is None)
            for row in rows
        ),
        "derived_reasons_are_disjoint_from_the_adapter_vocabulary": not (derived_reasons & adapter_vocabulary),
        "totals_match_the_rows": all(count == derived for count in counted)
        and sum(cast(dict[str, int], totals["by_tool"]).values()) == int(totals["records_listed"]),
        "no_record_appears_twice": len({(row["bundle"], row["cell"], row["record"]) for row in rows}) == len(rows),
    }


def _adapter_refusal_vocabulary() -> set[str]:
    """Return the adapter's own refusal words, which a policy decision must not borrow."""
    # Imported here because the adapter imports this package, so a module-level import would cycle.
    from conflux.adapters.benchmarks.agentdojo_local import ADAPTER_REFUSAL_REASONS

    return set(ADAPTER_REFUSAL_REASONS)


def refusal_reason_payload(source_commit: str, runs_root: Path = DEFAULT_RUNS_ROOT) -> dict[str, Any]:
    """Read the retained bundles and return the refusal-reason bundle payload."""
    rows, bundles = derive_refusal_reason_rows(runs_root)
    totals = refusal_reason_totals(rows, bundles)
    return {
        "schema_version": "1",
        "classification": "adapter_evidence",
        "complete": True,
        "source_commit": source_commit,
        "runs_root": runs_root.as_posix(),
        "bundles": bundles,
        "totals": totals,
        "records": rows,
        "checks": refusal_reason_checks(rows, bundles, totals),
    }


def _readme(payload: Mapping[str, Any]) -> str:
    """Return the human-readable page that explains this bundle."""
    totals = cast(dict[str, Any], payload["totals"])
    rows = cast(list[dict[str, Any]], payload["records"])
    bundles = cast(list[dict[str, Any]], payload["bundles"])
    blocked = sum(int(bundle["blocked"]) for bundle in bundles)
    named = sum(int(bundle["blocked_named"]) for bundle in bundles)
    lines = [
        "# Refusal reasons derived from the retained bundles v1",
        "",
        "The retained AgentDojo bundles were written before a mediation record copied the refusing rule",
        "into its own `reason` field, so their blocked records carry no reason and count as policy",
        "refusals by outcome alone. Each of those records still keeps the whole ITES report, and the",
        "refusing decision sits in that report's trace. This bundle re-derives the rule for every one of",
        "them from the file. No model ran, no provider was called, and no retained bundle was rewritten:",
        "the table below is a reading of the `result.json` files under `research/output/runs/`.",
        "",
        "| Quantity | Count |",
        "|---|---|",
        f"| bundles read | {totals['bundles_read']} |",
        f"| blocked records | {blocked} |",
        f"| blocked records that already name a reason | {named} |",
        f"| blocked records with no reason, listed below | {totals['records_listed']} |",
        f"| of those, a refusing rule was derived | {totals['records_derived']} |",
        f"| of those, no denying decision could be derived | {totals['records_underivable']} |",
        "",
        "## Rules the derived rows name",
        "",
        "| policy_id | dimension | reason | records |",
        "|---|---|---|---|",
    ]
    per_rule: dict[tuple[str, str, str], int] = {}
    for row in rows:
        key = (str(row["derived_policy_id"]), str(row["derived_policy_dimension"]), str(row["derived_reason"]))
        per_rule[key] = per_rule.get(key, 0) + 1
    for (policy_id, dimension, reason), count in sorted(per_rule.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{policy_id}` | {dimension} | `{reason}` | {count} |")
    lines.append(f"| **total** | | | **{sum(per_rule.values())}** |")
    lines += [
        "",
        "## Every derived row",
        "",
        "One row per blocked record that carried no reason. `bundle`, `cell` and `record` locate it: the",
        "bundle directory, the cell's position in `result.json` and the record's position in that cell.",
        "",
        "| # | bundle | cell | record | tool | policy_id | dimension | reason |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"| {index} | `{row['bundle']}` | {row['cell']} | {row['record']} | {row['tool']} | "
            f"`{row['derived_policy_id']}` | {row['derived_policy_dimension']} | `{row['derived_reason']}` |",
        )
    checks = cast(dict[str, bool], payload["checks"])
    lines += [
        "",
        "## Checks",
        "",
        "Each check is computed while the table is built, in the same pass (refusal-reasons.json lists",
        "them under `checks`):",
        "",
    ]
    for name, value in checks.items():
        lines.append(f"* `{name}`: {str(value).lower()}")
    lines += [
        "",
        "## What this does not show",
        "",
        "* It is not an AgentDojo result, it measures no model, and it says nothing about how often a",
        "  policy refuses in a real suite. It reads the run bundles that already exist.",
        "* The historical records keep no `reason` field. This bundle derives the rule and leaves the run",
        "  bundles untouched, so a counter that reads the record still sees no reason; a reader that opens",
        "  this table, or re-runs this tool, sees the rule.",
        "* A row is only as good as the report retained beside it. A blocked record whose report held no",
        "  denying decision would be listed with empty derived columns and counted under `underivable`.",
        f"  This run derived a rule for every one of the {totals['records_listed']} rows.",
        "* The reading is limited to the bundles named above; a bundle added later changes the table, which",
        "  is why the standard validation tier byte-checks this directory against a fresh derivation.",
        "",
        "Re-run or byte-check:",
        "",
        "```console",
        "python scripts/derive_agentdojo_refusal_reasons.py research/output/runs/agentdojo-refusal-reasons-v1 --check",
        "```",
        "",
    ]
    return "\n".join(lines)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")


def generate_agentdojo_refusal_reasons_bundle(
    source_commit: str,
    output: Path,
    runs_root: Path = DEFAULT_RUNS_ROOT,
) -> None:
    """Write the refusal-reasons bundle to ``output``, reading the bundles under ``runs_root``."""
    output.mkdir(parents=True, exist_ok=True)
    payload = refusal_reason_payload(source_commit, runs_root)
    _write_json(output / "refusal-reasons.json", payload)
    (output / "README.md").write_text(_readme(payload), encoding="utf-8", newline="\n")
    checksums = sorted(
        (path for path in output.iterdir() if path.is_file() and path.name != "CHECKSUMS.sha256"),
        key=lambda path: path.name.casefold(),
    )
    (output / "CHECKSUMS.sha256").write_text(
        "".join(f"{_file_sha256(path)}  {path.name}\n" for path in checksums),
        encoding="utf-8",
        newline="\n",
    )


def compare_agentdojo_refusal_reasons_bundle(expected: Path, regenerated: Path) -> tuple[str, ...]:
    """Return file names that are missing or differ between two refusal-reasons bundles."""
    expected_files = {path.name: path for path in expected.iterdir() if path.is_file()}
    regenerated_files = {path.name: path for path in regenerated.iterdir() if path.is_file()}
    changed = set(expected_files) ^ set(regenerated_files)
    for name in set(expected_files) & set(regenerated_files):
        if _canonical_bytes(expected_files[name]) != _canonical_bytes(regenerated_files[name]):
            changed.add(name)
    return tuple(sorted(changed))


def verify_agentdojo_refusal_reasons_checksums(directory: Path) -> tuple[str, ...]:
    """Return file names whose checksums are missing or mismatched in the bundle."""
    checksum_file = directory / "CHECKSUMS.sha256"
    if not checksum_file.is_file():
        return ("CHECKSUMS.sha256",)
    errors: set[str] = set()
    indexed: set[str] = set()
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, separator, name = line.partition("  ")
        path = directory / name
        if not separator or name in indexed or not path.is_file():
            errors.add(name or line)
            continue
        indexed.add(name)
        if _file_sha256(path) != expected:
            errors.add(name)
    actual = {path.name for path in directory.iterdir() if path.is_file() and path.name != "CHECKSUMS.sha256"}
    errors.update(actual ^ indexed)
    return tuple(sorted(errors))


def _file_sha256(path: Path) -> str:
    content = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _canonical_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")


__all__ = [
    "AGENTDOJO_REFUSAL_REASONS_FILES",
    "DEFAULT_RUNS_ROOT",
    "compare_agentdojo_refusal_reasons_bundle",
    "derive_refusal_reason_rows",
    "generate_agentdojo_refusal_reasons_bundle",
    "refusal_reason_checks",
    "refusal_reason_payload",
    "refusal_reason_totals",
    "verify_agentdojo_refusal_reasons_checksums",
]
