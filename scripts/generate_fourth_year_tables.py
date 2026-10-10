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

#: Column layout for the reproduction table: environment, two counts, match, canonical states.
_REPRODUCTION_COLUMNS = "l" + "r" * 3 + "l"

#: Column layout for the scaling table: family, fixtures, two sizes, reduction factor.
_SCALING_COLUMNS = "l" + "r" * 4

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


THREE_WAY = RUNS / "three-way-agreement-v1" / "result.json"
NATIVE_SLED_A = RUNS / "native-sled-reproduction-v1" / "result.json"
NATIVE_SLED_B = RUNS / "native-sled-partb-reproduction-v1" / "result.json"
SLEDV = RUNS / "sledv-scaling-v1" / "result.json"


def _count(value: int) -> str:
    """Format a count for a LaTeX table: thousands separated without a stray space."""
    return f"{int(value):,}".replace(",", "{,}")


def _sources(*paths: Path) -> list[tuple[str, str]]:
    """Header source list: relative path and SHA-256, in the order a table cites them."""
    entries: list[tuple[str, str]] = []
    for path in paths:
        _payload, digest = _read_json(path)
        entries.append((str(path.relative_to(ROOT)), digest))
    return entries


def table_semantic_conformance() -> list[tuple[Path, str]]:
    """Reference interpreter, Z3 and nuXmv decisions over the same bounded IR variants."""
    result, _digest = _read_json(THREE_WAY)
    summary: dict[str, Any] = result["summary"]
    control = "holds" if summary["control_ok"] else "fails"
    rows = [
        ("IR variants checked", _count(summary["total_variants"])),
        ("Decided by Z3", _count(summary["z3_measured"])),
        ("Decided by nuXmv", _count(summary["nuxmv_measured"])),
        ("Refuted by the reference interpreter", _count(summary["refuted_variants"])),
        ("Reference and Z3 agree", _count(summary["agree_reference_z3"])),
        ("Reference and nuXmv agree", _count(summary["agree_reference_nuxmv"])),
        ("All three agree", _count(summary["agree_all_three"])),
        ("Negative control", control),
    ]
    body = "\n".join(f"{label} & {value} \\\\" for label, value in rows)
    caption = (
        "Semantic conformance over the same bounded IR variants: the reference interpreter, the "
        "optional Z3 backend and the optional nuXmv backend decide the same variants and agree on "
        "every decision, refuted variants included, and the negative control confirms the harness "
        "can still fail. Counts are read from the bundle's own \\texttt{result.json}, so the "
        "table cannot drift from the evidence it cites."
    )
    tex = (
        _header(_sources(THREE_WAY))
        + "\\begin{table}[t]\n\\centering\n\\small\n\\begin{tabular}{lr}\n\\toprule\n"
        + "\\textbf{Quantity} & \\textbf{Count} \\\\\n\\midrule\n"
        + body
        + "\n\\bottomrule\n\\end{tabular}\n\\caption{"
        + caption
        + "}\n\\label{tab:semantic-conformance}\n\\end{table}\n"
    )
    return [(OUT / "semantic_conformance_table.tex", tex)]


def table_native_sled_reproduction() -> list[tuple[Path, str]]:
    """Reproduced historical trace counts and the canonical-versus-archived comparison."""
    part_b, _digest_b = _read_json(NATIVE_SLED_B)
    part_a, _digest_a = _read_json(NATIVE_SLED_A)
    rows: list[str] = []
    for environment in part_b["environments"]:
        match = "yes" if environment["trace_count_match"] else "no"
        rows.append(
            f"{_tex_escape(str(environment['env_id']))} & {_count(environment['expected_traces'])} & "
            f"{_count(environment['total_traces'])} & {match} & "
            f"{_count(environment['unique_canonical_states'])} \\\\",
        )
    totals: dict[str, Any] = part_b["totals"]
    total_match = "yes" if totals["trace_count_match"] else "no"
    rows.append("\\midrule")
    rows.append(
        f"\\textbf{{Total}} & {_count(totals['expected_total'])} & {_count(totals['total_traces'])} & "
        f"{total_match} & {_count(totals['unique_canonical_states'])} \\\\",
    )
    historical: dict[str, Any] = part_a["historical_comparison"]
    comparable = "yes" if historical["comparable"] else "no"
    controls = part_a["negative_controls"]
    killed = sum(1 for control in controls if control["killed"])
    rows.append("\\midrule")
    rows.append(
        "\\multicolumn{5}{l}{\\emph{Canonical fixtures against the archived prototype}} \\\\",
    )
    rows.append(
        f"\\multicolumn{{5}}{{l}}{{Pairs compared: {len(part_a['pairs'])}; "
        f"negative controls killed: {killed} of {len(controls)}}} \\\\",
    )
    rows.append(
        f"\\multicolumn{{5}}{{l}}{{Directly comparable with the archived trace claim: {comparable} "
        f"({_tex_escape(str(historical['classification']))})}} \\\\",
    )
    rows.append(
        f"\\multicolumn{{5}}{{l}}{{Reproduced under depth bound {part_b['max_depth']}; "
        "runtime is omitted from the deterministic fixture}} \\\\",
    )
    body = "\n".join(rows)
    caption = (
        "Native SLED reproduction. The historical environments reproduce their exact trace counts "
        "under the recorded depth bound, and the canonical-state compression collapses the raw "
        "traces to a handful of states. The archived prototype enumerated transitions differently, "
        "so its headline trace count is not directly comparable; this is reproduction and "
        "conformance, not an unbounded security proof. Counts are read from each bundle's own "
        "\\texttt{result.json}."
    )
    tex = (
        _header(_sources(NATIVE_SLED_B, NATIVE_SLED_A))
        + "\\begin{table}[t]\n\\centering\n\\small\n\\begin{tabular}{"
        + _REPRODUCTION_COLUMNS
        + "}\n\\toprule\n"
        + "\\textbf{Environment} & \\textbf{Expected traces} & \\textbf{Reproduced} & "
        + "\\textbf{Match} & \\textbf{Canonical states} \\\\\n\\midrule\n"
        + body
        + "\n\\bottomrule\n\\end{tabular}\n\\caption{"
        + caption
        + "}\n\\label{tab:native-sled-reproduction}\n\\end{table}\n"
    )
    return [(OUT / "native_sled_reproduction_table.tex", tex)]


def table_sledv_scaling() -> list[tuple[Path, str]]:
    """Per-family SLED-V reduction sizes, and the verdict checks over every fixture."""
    result, _digest = _read_json(SLEDV)
    families: dict[str, Any] = result["by_family"]
    rows: list[str] = []
    for family in result["scaling_families"]:
        data = families[family]
        rows.append(
            f"{_tex_escape(str(family).replace('_', ' '))} & {_count(data['total_fixtures'])} & "
            f"{_count(data['max_original_states'])} & {_count(data['max_reduced_states'])} & "
            f"{float(data['state_reduction_ratio']):.1f}$\\times$ \\\\",
        )
    summary: dict[str, Any] = result["summary"]
    fixtures = result["fixtures"]
    equivalent = sum(1 for fixture in fixtures if fixture["coi_equivalent"])
    downgrade = "none" if summary["no_coi_downgrade"] else "present"
    agree = "yes" if summary["ref_z3_agree"] else "no"
    rows.append("\\midrule")
    rows.append(
        f"\\multicolumn{{5}}{{l}}{{Total fixtures: {_count(summary['total_fixtures'])}; "
        f"COI-equivalent fixtures: {_count(equivalent)}}} \\\\",
    )
    rows.append(f"\\multicolumn{{5}}{{l}}{{Verdict downgrades after reduction: {downgrade}}} \\\\")
    rows.append(f"\\multicolumn{{5}}{{l}}{{Reference and Z3 agree: {agree}}} \\\\")
    body = "\n".join(rows)
    caption = (
        "SLED-V reduction over three scaling families. The reduction collapses the finite models by "
        "up to the factor shown, no verdict is downgraded after reduction, and the reference and Z3 "
        "decisions agree. Sizes and checks are read from the bundle's own \\texttt{result.json}. "
        "This is bounded evidence on the tested finite models; it is not a proof of security for "
        "arbitrary or unbounded deployments."
    )
    tex = (
        _header(_sources(SLEDV))
        + "\\begin{table}[t]\n\\centering\n\\small\n\\begin{tabular}{"
        + _SCALING_COLUMNS
        + "}\n\\toprule\n"
        + "\\textbf{Family} & \\textbf{Fixtures} & \\textbf{Largest model} & "
        + "\\textbf{After reduction} & \\textbf{Reduction} \\\\\n\\midrule\n"
        + body
        + "\n\\bottomrule\n\\end{tabular}\n\\caption{"
        + caption
        + "}\n\\label{tab:sledv-scaling}\n\\end{table}\n"
    )
    return [(OUT / "sledv_scaling_table.tex", tex)]


def generate_all() -> list[tuple[Path, str]]:
    outputs: list[tuple[Path, str]] = []
    outputs.extend(table_agentdojo_breadth())
    outputs.extend(table_agentdojo_fingerprints())
    outputs.extend(table_semantic_conformance())
    outputs.extend(table_native_sled_reproduction())
    outputs.extend(table_sledv_scaling())
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
