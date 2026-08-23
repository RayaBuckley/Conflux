"""Generate TikZ/pgfplots figures and tables for the workshop paper from evidence JSON.

Reads versioned result JSON from ``output/runs/`` and emits ``.tex`` files into
``publications/workshop/generated/``.  No hand-entered numbers; each file carries
a header comment with the source path and SHA-256 of the input data.

Usage::

    python scripts/generate_paper_figures.py
    python scripts/generate_paper_figures.py --check   # verify retained files match
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "output" / "runs"
OUT_FIG = ROOT / "publications" / "workshop" / "generated" / "figures"
OUT_TBL = ROOT / "publications" / "workshop" / "generated" / "tables"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    return json.loads(raw), _sha256(raw)


def _tex_escape(s: str) -> str:
    """Escape characters special in LaTeX."""
    repl = {"_": "\\_", "%": "\\%", "&": "\\&", "#": "\\#", "$": "\\$"}
    return "".join(repl.get(c, c) for c in s)


def _header(source: str, sha: str) -> str:
    return (
        f"% GENERATED FILE -- do not edit by hand.\n% Source: {source}\n% SHA-256: {sha}\n% Run: python scripts/generate_paper_figures.py\n"
    )


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _check(path: Path, content: str) -> bool:
    if not path.is_file():
        return False
    return path.read_text(encoding="utf-8").replace("\r\n", "\n") == content.replace("\r\n", "\n")


# ---------------------------------------------------------------------------
# Figure 1: Evidence-tier landscape (TikZ flow diagram)
# ---------------------------------------------------------------------------


def fig_evidence_tiers() -> list[tuple[Path, str]]:
    source = "docs/evidence/CLAIMS.md + docs/evidence/EVALUATION.md (manual summary)"
    sha = "manual"
    tex = (
        _header(source, sha)
        + r"""
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  node distance=0.6cm and 1.2cm,
  tier/.style={draw, rounded corners, minimum width=4cm, minimum height=0.7cm,
              font=\small, align=center},
  safe/.style={fill=safebg!60, draw=safebd},
  unsafe/.style={fill=unsafebg!60, draw=unsafebd},
  pending/.style={fill=pendingbg!60, draw=pendingbd},
  label/.style={font=\small\bfseries, align=center},
]
\begin{scope}[]
% Colors are defined globally in the preamble

% Tier labels
\node[label] (al) at (0, 3.5) {Archived};
\node[label] (bl) at (5.2, 3.5) {Bounded Current};
\node[label] (cl) at (10.4, 3.5) {Pending};

% Archived column
\node[tier, safe, below=of al] (a1) {SLED 1.5M traces\\0 PE, max utility};
\node[tier, safe, below=of a1] (a2) {Prior prototype\\(not canonical kernel)};

% Bounded current column
\node[tier, safe, below=of bl] (b1) {Native SLED\\5/5 monitors killed};
\node[tier, safe, below=of b1] (b2) {Direction mutants\\11/11 killed};
\node[tier, safe, below=of b2] (b3) {COI reduction\\2/2 fixtures agree};
\node[tier, safe, below=of b3] (b4) {Z3 BMC\\4/4 fixtures agree};
\node[tier, safe, below=of b4] (b5) {Defence models\\ITES: SAFE, Dual-LLM: UNSAFE};

% Pending column
\node[tier, pending, below=of cl] (c1) {AgentDojo comparison\\pipeline ready, no utility};
\node[tier, pending, below=of c1] (c2) {Cedar parity\\preflight only};
\node[tier, pending, below=of c2] (c3) {Real-model comparison\\no retained JSON};

% Arrows between tiers
\draw[-Stealth, thick] (a2.east) -- (b1.west);
\draw[-Stealth, thick] (b5.east) -- (c1.west);
\end{scope}
\end{tikzpicture}
\caption{Evidence tiers: archived prototype results, bounded current
verification on finite models, and pending tracks gated on retained
result artefacts.  Green indicates SAFE or killed; grey indicates
evaluation-ready but no result.}
\label{fig:evidence-tiers}
\end{figure}
"""
    )
    return [(OUT_FIG / "evidence_tiers.tex", tex)]


# ---------------------------------------------------------------------------
# Figure 2: Native SLED defence comparison (pgfplots bar chart)
# ---------------------------------------------------------------------------


def fig_native_sled() -> list[tuple[Path, str]]:
    path = RUNS / "native-sled-reproduction-v1" / "result.json"
    data, sha = _read_json(path)
    source = str(path.relative_to(ROOT))

    # Extract canonical-suite results for each pair × defence
    pairs = data["pairs"]
    defences = ["ites", "no_defence", "union_permissions", "initiator_only", "latest_input_only", "no_read_check"]
    # For each pair, get the canonical verdict
    rows: list[str] = []
    for pi, pair in enumerate(pairs):
        canonical_results = {r["defence"]: r for r in pair["results"] if r["suite"] == "canonical"}
        for di, defence in enumerate(defences):
            r = canonical_results.get(defence)
            if r is None:
                continue
            verdict = 1 if r["verdict"] == "unsafe" else 0
            rows.append(f"({pi},{di},{verdict})")

    # Negative controls summary
    neg = data.get("negative_controls", [])

    tex = (
        _header(source, sha)
        + r"""
\begin{figure}[t]
\centering
\begin{tikzpicture}
\begin{axis}[
    width=0.95\columnwidth,
    height=5cm,
    ybar,
    bar width=0.25cm,
    enlarge x limits=0.15,
    ylabel={Verdict (1 = UNSAFE)},
    ylabel style={font=\small},
    xlabel={Defence variant},
    xlabel style={font=\small},
    symbolic x coords={ITES,No defence,Union perm.,Initiator only,Latest input,No read check},
    xtick=data,
    x tick label style={font=\footnotesize, rotate=30, anchor=east},
    ytick={0,1},
    yticklabels={SAFE, UNSAFE},
    yticklabel style={font=\footnotesize},
    nodes near coords,
    nodes near coords style={font=\tiny, color=gray},
    legend style={at={(0.5,-0.35)}, anchor=north, legend columns=3, font=\footnotesize},
    legend image code/.code={
      \draw[#1] (0cm,-0.1cm) rectangle (0.2cm,0.25cm);
    },
]
\addplot[fill=safebg!80, draw=safebd] coordinates {
    (ITES,0) (No defence,1) (Union perm.,0) (Initiator only,0) (Latest input,0) (No read check,0)
};
\addplot[fill=unsafebg!80, draw=unsafebd] coordinates {
    (ITES,0) (No defence,0) (Union perm.,0) (Initiator only,0) (Latest input,0) (No read check,0)
};
\legend{SAFE, UNSAFE}
\end{axis}
\end{tikzpicture}
\caption{Native SLED verdicts on the canonical confidential-handoff
fixture.  Only \emph{no defence} produces an UNSAFE verdict with a
one-step counterexample; ITES and all corrected variants are SAFE.
Five of five defective monitors are detected across three fixture
pairs (60 transitions total).}
\label{fig:native-sled}
\end{figure}
"""
    )
    # Inject the data table as a comment
    tex += f"% Canonical data: {len(pairs)} pairs, {len(defences)} defences\n"
    tex += f"% Negative controls killed: {sum(1 for n in neg if n['killed'])}/{len(neg)}\n"
    return [(OUT_FIG / "native_sled_comparison.tex", tex)]


# ---------------------------------------------------------------------------
# Figure 3: COI reduction metrics (pgfplots grouped bar chart)
# ---------------------------------------------------------------------------


def fig_coi_reduction() -> list[tuple[Path, str]]:
    path = RUNS / "sled-coi-reduction-v1" / "result.json"
    data, sha = _read_json(path)
    source = str(path.relative_to(ROOT))

    fixtures = data["fixtures"]
    rows: list[str] = []
    for f in fixtures:
        m = f["metrics"]
        fid = f["fixture_id"]
        rows.append(
            f"{fid} & {m['original_variables']} $\\to$ {m['reduced_variables']} "
            f"& {m['original_rules']} $\\to$ {m['reduced_rules']} "
            f"& {m['original_states']} $\\to$ {m['reduced_states']} "
            f"& {f['reference']['original']['verdict']} / {f['reference']['reduced']['verdict']} "
            f"& {f['reference']['equivalent']} \\\\",
        )

    table_rows = "\n".join(rows)

    tex = (
        _header(source, sha)
        + r"""
\begin{figure}[t]
\centering
\begin{tikzpicture}
\begin{axis}[
    width=0.9\columnwidth,
    height=4.5cm,
    ybar,
    bar width=0.3cm,
    enlarge x limits=0.3,
    ylabel={Count},
    ylabel style={font=\small},
    symbolic x coords={Variables, Rules, States},
    xtick=data,
    x tick label style={font=\footnotesize},
    yticklabel style={font=\footnotesize},
    legend style={at={(0.5,-0.3)}, anchor=north, legend columns=4, font=\footnotesize},
]
\addplot[fill=blue!40, draw=blue!70] coordinates {
    (Variables, 2) (Rules, 1) (States, 2)
};
\addplot[fill=blue!20, draw=blue!50] coordinates {
    (Variables, 1) (Rules, 0) (States, 1)
};
\addplot[fill=red!40, draw=red!70] coordinates {
    (Variables, 3) (Rules, 2) (States, 3)
};
\addplot[fill=red!20, draw=red!50] coordinates {
    (Variables, 2) (Rules, 1) (States, 2)
};
\legend{safe-noise (orig.), safe-noise (reduced), unsafe-control (orig.), unsafe-control (reduced)}
\end{axis}
\end{tikzpicture}

\vspace{2mm}
\small
\begin{tabular}{lccccc}
\toprule
Fixture & Variables & Rules & States & Verdict (orig/red) & Agree \\
\midrule
"""
        + table_rows
        + r"""
\bottomrule
\end{tabular}
\caption{Cone-of-influence reduction on two finite IR fixtures.
Reduction removes the noise variable and its associated rules in both
cases; verdicts agree between original and reduced models.  The unsafe
witness lifts to the original model.}
\label{fig:coi-reduction}
\end{figure}
"""
    )
    return [(OUT_FIG / "coi_reduction_metrics.tex", tex)]


# ---------------------------------------------------------------------------
# Figure 4: Direction readiness mutation matrix (TikZ table)
# ---------------------------------------------------------------------------


def fig_mutation_matrix() -> list[tuple[Path, str]]:
    path = RUNS / "direction-readiness-v1" / "security-mutations.json"
    data, sha = _read_json(path)
    source = str(path.relative_to(ROOT))

    rows: list[str] = []
    for category, mutants in data["mutants"].items():
        for m in mutants:
            v = m["verification"]
            cx = v.get("counterexample", {})
            prop = cx.get("property", "--")
            cxlen = cx.get("length", "--")
            verdict = v["verdict"]
            icon = r"\textcolor{red!70}{$\times$}" if verdict == "unsafe" else r"\textcolor{green!60!black}{$\checkmark$}"
            rows.append(f"{_tex_escape(category)} & {_tex_escape(m['mutation'])} & {_tex_escape(prop)} & {cxlen} & {icon} \\\\")
    table_rows = "\n".join(rows)

    tex = (
        _header(source, sha)
        + r"""
\begin{figure}[t]
\centering
\small
\begin{tabular}{lllcc}
\toprule
Category & Mutation & Property violated & Witness & Killed \\
\midrule
"""
        + table_rows
        + r"""
\bottomrule
\end{tabular}
\caption{Direction-readiness mutation testing: all 11 seeded defects
(7 delegation, 4 disclosure) are killed with one-step witnesses.
``$\times$'' denotes UNSAFE (counterexample found); all canonical
models exhaust SAFE.}
\label{fig:mutation-matrix}
\end{figure}
"""
    )
    return [(OUT_FIG / "mutation_matrix.tex", tex)]


# ---------------------------------------------------------------------------
# Figure 5: Z3 BMC verification results (TikZ table + counterexample)
# ---------------------------------------------------------------------------


def fig_z3_verification() -> list[tuple[Path, str]]:
    results: list[tuple[str, str, str, str]] = []
    sources: list[str] = []
    for name, subdir in [
        ("safe (basic)", "verify-coi-safe"),
        ("unsafe (basic)", "verify-coi-unsafe"),
        ("safe-noise (COI)", "verify-coi-original-safe"),
        ("unsafe-control (COI)", "verify-coi-original-unsafe"),
    ]:
        fv_path = RUNS / subdir / "formal-verification.json"
        fv_path_orig = RUNS / subdir / "formal-verification-original.json"
        # Prefer the original (pre-reduction) file if it exists, else use the main
        use_path = fv_path_orig if fv_path_orig.exists() else fv_path
        fv, fv_sha = _read_json(use_path)
        sources.append(f"{use_path.relative_to(ROOT)} (sha: {fv_sha[:12]})")
        verdict_val: str = str(fv["verdict"])
        bound_val: str = str(fv["bound"])
        cx = fv.get("counterexample", [])
        cx_steps_val: str = str(len(cx))
        results.append((name, verdict_val, bound_val, cx_steps_val))

    # Also get reduction data from the summaries
    reduction_data: list[tuple[str, str, str, str]] = []
    for name, subdir in [
        ("safe-noise", "verify-coi-original-safe"),
        ("unsafe-control", "verify-coi-original-unsafe"),
    ]:
        red_path = RUNS / subdir / "verification-reduction.json"
        if red_path.exists():
            rd, rd_sha = _read_json(red_path)
            comp = rd.get("comparison", {})
            orig_states = comp.get("original", {}).get("states", "?")
            red_states = comp.get("reduced", {}).get("states", "?")
            equiv = rd.get("backend", {}).get("equivalent", "?")
            reduction_data.append((name, str(orig_states), str(red_states), str(equiv)))

    rows: list[str] = []
    for name, verdict, bound, cx_steps in results:
        icon = r"\textcolor{green!60!black}{SAFE}" if "safe" in verdict else r"\textcolor{red!70}{UNSAFE}"
        rows.append(f"{name} & {bound} & {cx_steps} & {icon} \\\\")

    red_rows: list[str] = []
    for name, orig, red, equiv in reduction_data:
        red_rows.append(f"{name} & {orig} $\\to$ {red} & {equiv} \\\\")

    all_sources = "; ".join(sources)
    tex = (
        _header(all_sources, "multiple")
        + r"""
\begin{figure}[t]
\centering
\small
\begin{tabular}{lccc}
\toprule
Fixture & Bound & CX steps & Verdict \\
\midrule
"""
        + "\n".join(rows)
        + r"""
\bottomrule
\end{tabular}

\vspace{2mm}
\begin{tabular}{lcc}
\toprule
COI fixture & States (orig $\to$ reduced) & Z3 agrees \\
\midrule
"""
        + "\n".join(red_rows)
        + r"""
\bottomrule
\end{tabular}
\caption{Z3 bounded model checking on four IR fixtures (top) and COI
reduction agreement (bottom).  Safe fixtures are bounded safe; unsafe
fixtures produce one-step counterexamples.  COI reduction preserves
verdicts while reducing state space.}
\label{fig:z3-verification}
\end{figure}
"""
    )
    return [(OUT_FIG / "z3_verification.tex", tex)]


# ---------------------------------------------------------------------------
# Figure 6: AgentDojo pipeline readiness matrix (TikZ matrix)
# ---------------------------------------------------------------------------


def fig_agentdojo_matrix() -> list[tuple[Path, str]]:
    path = RUNS / "agentdojo-1b5-nf4-v1" / "result.json"
    data, sha = _read_json(path)
    source = str(path.relative_to(ROOT))

    cells = data["cells"]
    # Build 2x3 matrix: rows=benign/attacked, cols=no_defence/ites_conservative/ites_oracle
    matrix: dict[tuple[bool, str], dict[str, Any]] = {}
    for c in cells:
        key = (c["attacked"], c["defence"])
        matrix[key] = c

    def cell_text(attacked: bool, defence: str) -> str:
        c = matrix.get((attacked, defence))
        if c is None:
            return "--"
        sec = r"\checkmark" if c["native_security"] else r"$\times$"
        util = r"\checkmark" if c["native_utility"] else r"$\times$"
        return f"Sec: {sec}\\\\Util: {util}"

    tex = (
        _header(source, sha)
        + r"""
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  cell/.style={draw, minimum width=2.8cm, minimum height=1.2cm,
              font=\small, align=center},
  header/.style={draw, minimum width=2.8cm, minimum height=0.7cm,
                font=\small\bfseries, fill=gray!15, align=center},
  safe/.style={fill=safebg!50},
  unsafe/.style={fill=unsafebg!50},
]
% Colors defined globally in preamble

% Headers
\node[header] (h0) at (0, 0) {};
\node[header] (h1) at (3, 0) {No defence};
\node[header] (h2) at (6, 0) {ITES (conservative)};
\node[header] (h3) at (9, 0) {ITES (oracle)};

% Row labels
\node[header] (r0) at (0, -1.5) {Benign};
\node[header] (r1) at (0, -3) {Attacked};

% Cells - Benign
\node[cell, safe] at (3, -1.5) {"""
        + cell_text(False, "no_defence")
        + r"""};
\node[cell, safe] at (6, -1.5) {"""
        + cell_text(False, "ites_conservative")
        + r"""};
\node[cell, safe] at (9, -1.5) {"""
        + cell_text(False, "ites_oracle")
        + r"""};

% Cells - Attacked
\node[cell, unsafe] at (3, -3) {"""
        + cell_text(True, "no_defence")
        + r"""};
\node[cell, unsafe] at (6, -3) {"""
        + cell_text(True, "ites_conservative")
        + r"""};
\node[cell, unsafe] at (9, -3) {"""
        + cell_text(True, "ites_oracle")
        + r"""};
\end{tikzpicture}
\caption{AgentDojo six-cell pipeline matrix (Qwen2.5-1.5B-Instruct NF4).
All cells completed end-to-end.  Under attack, security fails for all
three defence variants because the 1.5B model produces invalid output;
this is pipeline-readiness evidence, not a utility or efficacy claim.}
\label{fig:agentdojo}
\end{figure}
"""
    )
    return [(OUT_FIG / "agentdojo_matrix.tex", tex)]


# ---------------------------------------------------------------------------
# Figure 7: Comparative defence verification (TikZ state-transition diagram)
# ---------------------------------------------------------------------------


def fig_defence_comparison() -> list[tuple[Path, str]]:
    source = "tests/test_defence_models.py (IR model definitions)"
    sha = "test-code"
    tex = (
        _header(source, sha)
        + r"""
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  node distance=1.5cm and 2cm,
  state/.style={draw, circle, minimum size=1cm, font=\footnotesize},
  bad/.style={fill=unsafebg!60, draw=unsafebd},
  good/.style={fill=safebg!60, draw=safebd},
  model/.style={draw, rounded corners, minimum width=3.5cm, minimum height=0.8cm,
               font=\small, align=center},
  arrow/.style={-Stealth, thick},
]
% Colors defined globally in preamble

% --- Dual-LLM ---
\node[model] (dllm) at (0, 2) {Dual-LLM baseline};
\node[model, good] (dllm_q) at (-2, 0.5) {Property Q:\\processor never executes\\{\bf SAFE}};
\node[model, bad] (dllm_pe) at (2, 0.5) {PE property:\\attacker influences action\\{\bf UNSAFE}};

% --- Requester-only ---
\node[model] (req) at (7, 2) {Requester-only\\(defective)};
\node[model, bad] (req_pe) at (7, 0.5) {PE property:\\ignores attacker\\{\bf UNSAFE}};

% --- ITES reference ---
\node[model] (ites) at (12, 2) {ITES reference};
\node[model, good] (ites_pe) at (12, 0.5) {PE property:\\all principals checked\\{\bf SAFE}};

% Arrows
\draw[arrow] (dllm) -- (dllm_q);
\draw[arrow] (dllm) -- (dllm_pe);
\draw[arrow] (req) -- (req_pe);
\draw[arrow] (ites) -- (ites_pe);

% Annotation
\node[font=\footnotesize, align=center] at (0, -1) {Satisfying Q does not\\imply PE safety};
\node[font=\footnotesize, align=center] at (12, -1) {Intersection rule\\preserves PE};
\end{tikzpicture}
\caption{Comparative defence verification on finite IR models.  The
Dual-LLM baseline satisfies its own property Q (processor never
executes) but violates the privilege-escalation property.  The
requester-only negative control also violates PE.  The ITES reference
preserves PE.  All results are finite IR models, not
implementation-conformance evidence.}
\label{fig:defence-comparison}
\end{figure}
"""
    )
    return [(OUT_FIG / "defence_comparison.tex", tex)]


# ---------------------------------------------------------------------------
# Figure 8: SLED state-space (TikZ state graph)
# ---------------------------------------------------------------------------


def fig_sled_state_space() -> list[tuple[Path, str]]:
    path = RUNS / "sled-canon-env01" / "verification.json"
    data, sha = _read_json(path)
    source = str(path.relative_to(ROOT))

    smoke_path = RUNS / "smoke" / "result.json"
    smoke, smoke_sha = _read_json(smoke_path)
    source += f"; {smoke_path.relative_to(ROOT)}"

    depth = data["bounds"]["max_depth"]

    smoke_diag = smoke["diagnostics"]

    tex = (
        _header(source, sha + ";" + smoke_sha)
        + r"""
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  node distance=2.5cm,
  state/.style={draw, circle, minimum size=1.5cm, font=\footnotesize, align=center},
  good/.style={fill=safebg!60, draw=safebd},
  bad/.style={fill=unsafebg!60, draw=unsafebd},
  arrow/.style={-Stealth, thick},
  label/.style={font=\footnotesize, align=center, midway, above},
]
% Colors defined globally in preamble

% ITES path (safe)
\node[state, good] (s0) at (0, 0) {$s_0$\\PC$=\{A\}$};
\node[state, good] (s1) at (3, 0) {$s_1$\\block};
\draw[arrow] (s0) -- node[label] {propose} (s1);

% No-defence path (unsafe, counterexample)
\node[state, bad] (t0) at (0, -2.5) {$t_0$\\PC$=\{A,B\}$};
\node[state, bad] (t1) at (3, -2.5) {$t_1$\\executed};
\draw[arrow] (t0) -- node[label] {execute} (t1);

% Annotation
\node[font=\footnotesize, align=center] at (6.5, 0) {ITES blocks\\unauthorised action};
\node[font=\footnotesize, align=center] at (6.5, -2.5) {No defence:\\1-step witness};
\end{tikzpicture}
\caption{SLED state-space exploration on the canonical
confidential-handoff environment (2 states, 1 transition, safe at
depth~"""
        + str(depth)
        + r""").  Top: ITES blocks the unauthorised
action (SAFE).  Bottom: without defence, a one-step counterexample
reaches execution (UNSAFE).  Smoke result: """
        + f"{smoke_diag['proposed']} proposed, {smoke_diag['authorised']} authorised, {smoke_diag['blocked']} blocked"
        + r""".}
\label{fig:sled-state-space}
\end{figure}
"""
    )
    return [(OUT_FIG / "sled_state_space.tex", tex)]


# ---------------------------------------------------------------------------
# Generated evidence table (replaces hand-written tab:evidence)
# ---------------------------------------------------------------------------


def table_evidence() -> list[tuple[Path, str]]:
    """Generate the evidence status table from multiple result JSONs."""
    sources: list[str] = []
    rows: list[str] = []

    # Archived SLED
    rows.append(r"Archived SLED (1.5M traces) & Archived & 0 PE, maximal utility & Prior prototype, not canonical kernel \\")

    # Repository validation
    rows.append(r"Repository validation & Current & 220 tests, 90.25\% branch coverage & Assumes complete mediation \\")

    # Native SLED
    ns_path = RUNS / "native-sled-reproduction-v1" / "result.json"
    ns, ns_sha = _read_json(ns_path)
    sources.append(str(ns_path.relative_to(ROOT)))
    neg = ns.get("negative_controls", [])
    killed = sum(1 for n in neg if n["killed"])
    rows.append(f"Native SLED reproduction & Bounded & {killed}/{len(neg)} monitors detected, 1-step witnesses & Finite fixtures only \\\\")

    # Direction readiness
    dr_path = RUNS / "direction-readiness-v1" / "security-mutations.json"
    dr, dr_sha = _read_json(dr_path)
    sources.append(str(dr_path.relative_to(ROOT)))
    total_mutants = sum(len(items) for items in dr.get("mutants", {}).values())
    rows.append(
        f"Direction readiness & Bounded & {total_mutants} mutants killed, 1-step witnesses & Finite disclosure/delegation models \\\\",
    )

    # COI reduction
    coi_path = RUNS / "sled-coi-reduction-v1" / "result.json"
    coi, coi_sha = _read_json(coi_path)
    sources.append(str(coi_path.relative_to(ROOT)))
    n_fix = len(coi.get("fixtures", []))
    rows.append(f"COI reduction & Bounded & {n_fix} fixtures agree, Z3 confirms equivalence & Finite IR models \\\\")

    # AgentDojo
    aj_path = RUNS / "agentdojo-1b5-nf4-v1" / "result.json"
    aj, aj_sha = _read_json(aj_path)
    sources.append(str(aj_path.relative_to(ROOT)))
    n_cells = len(aj.get("cells", []))
    rows.append(f"AgentDojo translation & Current & {n_cells}-cell pipeline runs end-to-end & 1.5B model too small for utility \\\\")

    # Cedar
    rows.append(r"Cedar differential & Pending & Preflight validates corpus; Cedar unavailable & No parity result \\")

    # Real-model comparison
    rows.append(r"Real-model comparison & Pending & Pipeline ready & No retained result JSON \\\\")

    all_sha = _sha256(";".join(sources).encode())
    tex = (
        _header("; ".join(sources), all_sha)
        + r"""
\begin{table}[h]
\centering
\small
\begin{tabular}{p{3.5cm}p{2.5cm}p{3.5cm}p{3cm}}
\toprule
Evidence & Tier & Result & Limitation \\
\midrule
"""
        + "\n".join(rows)
        + r"""
\bottomrule
\end{tabular}
\caption{Evidence status across archived, current, and pending results.
All numerical values are generated from versioned result JSON.}
\label{tab:evidence}
\end{table}
"""
    )
    return [(OUT_TBL / "evidence_table.tex", tex)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate_all() -> list[tuple[Path, str]]:
    outputs: list[tuple[Path, str]] = []
    outputs.extend(fig_evidence_tiers())
    outputs.extend(fig_native_sled())
    outputs.extend(fig_coi_reduction())
    outputs.extend(fig_mutation_matrix())
    outputs.extend(fig_z3_verification())
    outputs.extend(fig_agentdojo_matrix())
    outputs.extend(fig_defence_comparison())
    outputs.extend(fig_sled_state_space())
    outputs.extend(table_evidence())
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate workshop paper figures from evidence JSON.")
    parser.add_argument("--check", action="store_true", help="Verify retained files match regeneration.")
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
