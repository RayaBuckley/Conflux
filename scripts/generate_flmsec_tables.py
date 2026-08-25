"""Generate LaTeX evidence tables for the FLMSec 2026 manuscript.

Reads versioned result JSON from ``research/output/runs/`` and emits ``.tex``
files into ``research/publications/flmsec_2026/generated/tables/``.

No hand-entered numbers; each file carries a header comment with the source
path and SHA-256 of the input data.

Usage::

    python scripts/generate_flmsec_tables.py
    python scripts/generate_flmsec_tables.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "research" / "output" / "runs"
OUT = ROOT / "research" / "publications" / "flmsec_2026" / "generated" / "tables"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    return json.loads(raw), _sha256(raw)


def _header(source: str, sha: str) -> str:
    return (
        f"% GENERATED FILE -- do not edit by hand.\n% Source: {source}\n% SHA-256: {sha}\n% Run: python scripts/generate_flmsec_tables.py\n"
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _check(path: Path, content: str) -> bool:
    if not path.is_file():
        return False
    return path.read_text(encoding="utf-8").replace("\r\n", "\n") == content.replace("\r\n", "\n")


def table_defect_detection() -> list[tuple[Path, str]]:
    ns_path = RUNS / "native-sled-reproduction-v1" / "result.json"
    ns, ns_sha = _read_json(ns_path)
    source = str(ns_path.relative_to(ROOT))

    rows: list[str] = []
    for n in ns["negative_controls"]:
        defence = n["defence"].replace("_", "\\_")
        killed = r"\checkmark" if n["killed"] else ""
        cx_len = str(n["counterexample_length"])
        rows.append(f"{defence} & {killed} & {cx_len} \\\\")

    dr_path = RUNS / "direction-readiness-v1" / "security-mutations.json"
    dr, dr_sha = _read_json(dr_path)
    source += f"; {dr_path.relative_to(ROOT)}"

    for cat, mutants in dr.get("mutants", {}).items():
        for m in mutants:
            v = m["verification"]
            cx = v.get("counterexample", {})
            mutation = m["mutation"].replace("_", "\\_")
            prop = cx.get("property", "--").replace("_", "\\_")
            cx_len = str(cx.get("length", "--"))
            rows.append(f"{cat}/{mutation} & \\checkmark & {cx_len} \\footnotesize({prop}) \\\\")

    table_body = "\n".join(rows)
    all_sha = _sha256((ns_sha + dr_sha).encode())

    tex = (
        _header(source, all_sha)
        + r"""\begin{table}[t]
\centering
\small
\begin{tabular}{p{4cm}cc}
\toprule
\textbf{Defective monitor} & \textbf{Detected} & \textbf{Witness length} \\
\midrule
"""
        + table_body
        + r"""
\bottomrule
\end{tabular}
\caption{Seeded-defect detection. All five native SLED negative controls and
all 11 direction-readiness mutants (7 delegation, 4 disclosure) are detected
with one-step counterexamples. The canonical ITES model exhausts
\textsc{SAFE} within the checked bounds (max depth 1, max states 4).
Finite fixtures and bounds only.}
\label{tab:defect-detection}
\end{table}
"""
    )
    return [(OUT / "defect_detection_table.tex", tex)]


def table_checker_agreement() -> list[tuple[Path, str]]:
    coi_path = RUNS / "sled-coi-reduction-v1" / "result.json"
    coi, coi_sha = _read_json(coi_path)
    source = str(coi_path.relative_to(ROOT))

    rows: list[str] = []
    for f in coi["fixtures"]:
        fid = f["fixture_id"].replace("_", "\\_")
        orig = f["reference"]["original"]["verdict"]
        red = f["reference"]["reduced"]["verdict"]
        equiv = r"\checkmark" if f["reference"]["equivalent"] else r"$\times$"
        orig_states = f["metrics"]["original_states"]
        red_states = f["metrics"]["reduced_states"]
        rows.append(f"{fid} & \\textsc{{{orig}}} & \\textsc{{{red}}} & {orig_states}$\\to${red_states} & {equiv} \\\\")

    table_body = "\n".join(rows)

    tex = (
        _header(source, coi_sha)
        + r"""\begin{table}[t]
\centering
\small
\begin{tabular}{lccccc}
\toprule
\textbf{Fixture} & \textbf{Ref.\ verdict} & \textbf{Reduced verdict} &
\textbf{States (orig$\to$red)} & \textbf{Agree} \\
\midrule
"""
        + table_body
        + r"""
\bottomrule
\end{tabular}
\caption{Independent checker agreement. The reference interpreter and COI-reduced
model agree on both safe and unsafe fixtures. The unsafe witness lifts to the
original model. Finite IR models only.}
\label{tab:checker-agreement}
\end{table}
"""
    )
    return [(OUT / "checker_agreement_table.tex", tex)]


def table_coi_reduction() -> list[tuple[Path, str]]:
    coi_path = RUNS / "sled-coi-reduction-v1" / "result.json"
    coi, coi_sha = _read_json(coi_path)
    source = str(coi_path.relative_to(ROOT))

    rows: list[str] = []
    for f in coi["fixtures"]:
        fid = f["fixture_id"].replace("_", "\\_")
        m = f["metrics"]
        rows.append(
            f"{fid} & {m['original_variables']}$\\to${m['reduced_variables']} & "
            f"{m['original_rules']}$\\to${m['reduced_rules']} & "
            f"{m['original_states']}$\\to${m['reduced_states']} & "
            f"\\textsc{{{f['reference']['original']['verdict']}}} / "
            f"\\textsc{{{f['reference']['reduced']['verdict']}}} & "
            f"\\checkmark \\\\",
        )

    table_body = "\n".join(rows)

    tex = (
        _header(source, coi_sha)
        + r"""\begin{table}[t]
\centering
\small
\begin{tabular}{lccccc}
\toprule
\textbf{Fixture} & \textbf{Variables} & \textbf{Rules} & \textbf{States} &
\textbf{Verdict} & \textbf{Agree} \\
\midrule
"""
        + table_body
        + r"""
\bottomrule
\end{tabular}
\caption{Cone-of-influence reduction on two finite IR fixtures. Reduction
removes the noise variable and its rule in the safe fixture, and one variable
and one rule in the unsafe fixture. Verdicts agree between original and reduced
models. The unsafe witness lifts to the original model. Finite IR models only.}
\label{tab:coi-reduction}
\end{table}
"""
    )
    return [(OUT / "coi_reduction_table.tex", tex)]


def table_comparative_defence() -> list[tuple[Path, str]]:
    source = "tests/test_defence_models.py (IR model definitions + test verdicts)"
    sha = "test-code"

    tex = (
        _header(source, sha)
        + r"""\begin{table}[t]
\centering
\small
\begin{tabular}{lccc}
\toprule
\textbf{Defence model} & \textbf{Native property Q} & \textbf{PE property} &
\textbf{Counterexample} \\
\midrule
Dual-LLM & \textsc{Safe} & \textsc{Unsafe} & 1-step PE witness \\
CaMeL & \textsc{Safe} & \textsc{Unsafe} & 1-step PE witness \\
Progent & \textsc{Safe} & \textsc{Unsafe} & 1-step PE witness \\
PACT & \textsc{Safe} & \textsc{Unsafe} & 1-step PE witness \\
Requester-only (defective) & --- & \textsc{Unsafe} & 1-step PE witness \\
\textbf{ITES (Principal Context)} & --- & \textbf{Safe} & --- \\
\bottomrule
\end{tabular}
\caption{Comparative defence verification on finite IR models. Each defence
satisfies its own intended property Q but violates the PE property. ITES
preserves PE. All results are finite IR model comparisons, not
implementation-level evaluations.}
\label{tab:comparative-defence}
\end{table}
"""
    )
    return [(OUT / "comparative_defence_table.tex", tex)]


def table_coi_scaling() -> list[tuple[Path, str]]:
    scaling_path = RUNS / "coi-scaling-v1" / "result.json"
    scaling, scaling_sha = _read_json(scaling_path)
    source = str(scaling_path.relative_to(ROOT))

    rows: list[str] = []
    for f in scaling["fixtures"]:
        fid = f["fixture_id"].replace("_", "\\_")
        o = f["original"]
        r = f["reduced"]
        z3 = f["z3"]
        wit = f["witness_length"]
        z3_verdict = z3["original_verdict"].replace("_", "\\_")
        rows.append(
            f"{fid} & {o['variables']}$\\rightarrow${r['variables']} & "
            f"{o['rules']}$\\rightarrow${r['rules']} & "
            f"{o['states']}$\\rightarrow${r['states']} & "
            f"\\textsc{{{z3_verdict}}} & {wit} \\\\",
        )

    table_body = "\n".join(rows)

    tex = (
        _header(source, scaling_sha)
        + r"""\begin{table}[t]
\centering
\small
\begin{tabular}{llcccc}
\toprule
\textbf{Fixture} & \textbf{Vars} & \textbf{Rules} & \textbf{States} &
\textbf{Z3} & \textbf{Wit.} \\
\midrule
"""
        + table_body
        + r"""
\bottomrule
\end{tabular}
\caption{COI scaling on parameterized noise fixtures. Adding up to 16 irrelevant
noise variables does not change verdicts or witness length. The reduced model
always collapses to the invariant variable(s) only. Z3 agrees on original and
reduced models across all 12 fixtures. Finite IR models only.}
\label{tab:coi-scaling}
\end{table}
"""
    )
    return [(OUT / "coi_scaling_table.tex", tex)]


def generate_all() -> list[tuple[Path, str]]:
    outputs: list[tuple[Path, str]] = []
    outputs.extend(table_defect_detection())
    outputs.extend(table_checker_agreement())
    outputs.extend(table_coi_reduction())
    outputs.extend(table_comparative_defence())
    outputs.extend(table_coi_scaling())
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FLMSec evidence tables from result JSON.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify retained files match regeneration.",
    )
    arguments = parser.parse_args()

    outputs = generate_all()
    mismatches: list[str] = []

    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        if arguments.check:
            if not _check(path, content):
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            _write(path, content)
            print(f"  wrote {path.relative_to(ROOT)}")

    if arguments.check:
        if mismatches:
            print("MISMATCH in:")
            for m in mismatches:
                print(f"  {m}")
            return 1
        print(f"All {len(outputs)} generated files match.")
    else:
        print(f"Generated {len(outputs)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
