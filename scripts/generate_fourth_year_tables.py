"""Generate the current manuscript's AgentDojo breadth tables from retained result JSON.

The manuscript states that no headline number is entered by hand. These tables are the empirical breadth
record: one row per retained AgentDojo bundle, counted from the bundle's own ``result.json`` and
``protocol.json``, with every source listed and hashed in the file header.

Run with ``--check`` to verify the retained files match regeneration; the standard validation tier does
that, so a bundle that is re-run or replaced without regenerating the tables fails the gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "research" / "output" / "runs"
OUT = ROOT / "research" / "publications" / "manuscript" / "generated" / "tables"

#: Column layout for the breadth table: run, cells, complete, utility, security, incomplete, failures.
_BREADTH_COLUMNS = "l" * 2 + "r" * 4 + "l"

#: (selection label, bundle directory) for every retained AgentDojo bundle in citation order.
BUNDLES: tuple[tuple[str, str], ...] = (
    ("stratified", "agentdojo-stratified-banking-v1"),
    ("stratified", "agentdojo-stratified-slack-v1"),
    ("stratified", "agentdojo-stratified-travel-v1"),
    ("stratified", "agentdojo-stratified-workspace-v1"),
    ("pilot", "agentdojo-pilot-banking-v1"),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise FileNotFoundError(f"retained bundle file is missing: {path.relative_to(ROOT)}")
    raw = path.read_bytes()
    return json.loads(raw), _sha256(raw)


def _tex_escape(value: str) -> str:
    return value.replace("_", r"\_")


def _header(sources: list[tuple[str, str]]) -> str:
    lines = [
        "% GENERATED FILE -- do not edit by hand.",
        "% Run: python scripts/generate_fourth_year_tables.py",
    ]
    lines.extend(f"% Source: {name} SHA-256: {sha}" for name, sha in sources)
    return "\n".join(lines) + "\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _check(path: Path, content: str) -> bool:
    if not path.is_file():
        return False
    return path.read_text(encoding="utf-8").replace("\r\n", "\n") == content.replace("\r\n", "\n")


def _load_bundle(
    directory: str,
) -> tuple[dict[str, Any], dict[str, Any], str, str, list[tuple[str, str]]]:
    """Return one bundle's result, protocol, and the two source names for the header."""
    result_path = RUNS / directory / "result.json"
    protocol_path = RUNS / directory / "protocol.json"
    result, result_sha = _read_json(result_path)
    protocol, protocol_sha = _read_json(protocol_path)
    sources = [
        (str(result_path.relative_to(ROOT)), result_sha),
        (str(protocol_path.relative_to(ROOT)), protocol_sha),
    ]
    return result, protocol, result_sha, protocol_sha, sources


def _counts(result: dict[str, Any]) -> tuple[int, int, int, int, int]:
    cells = result["cells"]
    complete = sum(1 for cell in cells if cell["status"] == "complete")
    utility = sum(1 for cell in cells if cell["native_utility"] is True)
    security = sum(1 for cell in cells if cell["native_security"] is True)
    return len(cells), complete, len(cells) - complete, utility, security


def _failure_summary(result: dict[str, Any]) -> str:
    counts = {str(k): int(v) for k, v in result["failure_counts"].items() if int(v)}
    if not counts:
        return "none"
    return ", ".join(f"{name} {value}" for name, value in sorted(counts.items()))


def table_agentdojo_breadth() -> list[tuple[Path, str]]:
    """Counts per retained bundle: cells, completion, utility, security, failure categories."""
    sources: list[tuple[str, str]] = []
    rows: list[str] = []
    totals = [0, 0, 0, 0]
    for label, directory in BUNDLES:
        result, protocol, _result_sha, _protocol_sha, bundle_sources = _load_bundle(directory)
        sources.extend(bundle_sources)
        suite_id = str(protocol["suite"]["id"])
        suite = suite_id.split(":", maxsplit=1)[0]
        tasks = len(protocol["suite"]["task_ids"])
        cells, complete, failed, utility, security = _counts(result)
        totals = [
            totals[0] + cells,
            totals[1] + complete,
            totals[2] + utility,
            totals[3] + security,
        ]
        failures = _tex_escape(_failure_summary(result))
        rows.append(
            f"{_tex_escape(suite)} (\\textit{{{label}}}, {tasks} tasks) & {cells} & {complete} & "
            f"{utility} & {security} & {failed} & {failures} \\\\",
        )
    rows.append(
        f"\\textbf{{Total}} & \\textbf{{{totals[0]}}} & \\textbf{{{totals[1]}}} & "
        f"\\textbf{{{totals[2]}}} & \\textbf{{{totals[3]}}} & "
        f"\\textbf{{{totals[0] - totals[1]}}} & \\\\",
    )
    body = "\n".join(rows)
    caption = (
        "Retained AgentDojo breadth evidence, counted from each bundle's own \\texttt{result.json}. "
        f"{totals[0]} cells, {totals[1]} complete, {totals[2]} with utility, {totals[3]} reporting no "
        "security violation. The model is a 0.5B floor configuration, so utility is zero and the "
        "security counts are vacuous: a model that completes no task cannot be shown to be protected. "
        "Failure counts are the categories the run recorded: each cell contributes one count per "
        "recorded failure, so one cell can carry several categories and a cell that completed can "
        "still carry a category such as \\texttt{utility}. The six incomplete "
        "slack cells were later diagnosed as capability failures of that model, not adapter gaps; a "
        "module rerun of the same suite reports them as parser failures. Section 27 of the verification "
        "record holds the diagnosis and the repeatability measurement."
    )
    tex = (
        _header(sources)
        + "\\begin{table}[t]\n\\centering\n\\small\n\\begin{tabular}{"
        + _BREADTH_COLUMNS
        + "}\n\\toprule\n"
        + "\\textbf{Run} & \\textbf{Cells} & \\textbf{Complete} & \\textbf{Utility} & "
        + "\\textbf{Security} & \\textbf{Incomplete} & \\textbf{Failure categories} \\\\\n\\midrule\n"
        + body
        + "\n\\bottomrule\n\\end{tabular}\n\\caption{"
        + caption
        + "}\n\\label{tab:agentdojo-breadth}\n\\end{table}\n"
    )
    return [(OUT / "agentdojo_breadth_table.tex", tex)]


def table_agentdojo_fingerprints() -> list[tuple[Path, str]]:
    """Protocol identity per retained bundle, so a repeat can be compared with the retained run."""
    sources: list[tuple[str, str]] = []
    rows: list[str] = []
    for label, directory in BUNDLES:
        result, protocol, _result_sha, _protocol_sha, bundle_sources = _load_bundle(directory)
        sources.extend(bundle_sources)
        suite_id = str(protocol["suite"]["id"])
        suite = _tex_escape(suite_id)
        commit = str(protocol["source_commit"])[:12]
        fingerprint = str(result["protocol_fingerprint"])[:16]
        model = _tex_escape(str(result["model_id"]))
        rows.append(
            f"{_tex_escape(directory)} & {suite} & \\texttt{{{commit}}} & \\texttt{{{fingerprint}}} & {model} \\\\",
        )
    body = "\n".join(rows)
    caption = (
        "Protocol identity of the retained bundles. A repeat that changes the suite, task set, bounds, "
        "model identity, prompts, or inputs changes the fingerprint, so a matching fingerprint is what "
        "makes a rerun comparable; a matching fingerprint also implies the recorded source commit. The "
        "fingerprints are truncated to their first 16 hexadecimal digits here and kept whole in each "
        "bundle's \\texttt{result.json}. The stratified bundles were retained before the sweep passed "
        "the selection's own suite id, so their suite ids use the earlier "
        "\\texttt{<suite>:expanded:<first task>} spelling rather than the selection manifest's "
        "\\texttt{<suite>:stratified-v1}; every id here is the one the run recorded."
    )
    tex = (
        _header(sources)
        + "\\begin{table}[t]\n\\centering\n\\small\n\\begin{tabular}{lllll}\n\\toprule\n"
        + "\\textbf{Bundle} & \\textbf{Protocol suite id} & \\textbf{Source commit} & "
        + "\\textbf{Fingerprint} & \\textbf{Model} \\\\\n\\midrule\n"
        + body
        + "\n\\bottomrule\n\\end{tabular}\n\\caption{"
        + caption
        + "}\n\\label{tab:agentdojo-fingerprints}\n\\end{table}\n"
    )
    return [(OUT / "agentdojo_fingerprints_table.tex", tex)]


def generate_all() -> list[tuple[Path, str]]:
    outputs: list[tuple[Path, str]] = []
    outputs.extend(table_agentdojo_breadth())
    outputs.extend(table_agentdojo_fingerprints())
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the retained tables match regeneration without writing",
    )
    arguments = parser.parse_args()

    outputs = generate_all()
    mismatches: list[str] = []
    for path, content in outputs:
        if arguments.check:
            if not _check(path, content):
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            _write(path, content)
            print(f"  wrote {path.relative_to(ROOT)}")

    if arguments.check:
        if mismatches:
            print("MISMATCH in:")
            for name in mismatches:
                print(f"  {name}")
            return 1
        print(f"All {len(outputs)} generated files match.")
    else:
        print(f"Generated {len(outputs)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
