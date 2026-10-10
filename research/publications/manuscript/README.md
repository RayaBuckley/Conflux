# Current Conflux manuscript

This is the work-in-progress fourth-year paper. The canonical source is
`conflux_fourth_year_2026.tex`; the previous-year paper remains immutable under
`../paper/`.

The 31 July snapshot describes the completed canonical security migration,
offline runtime and CLI, native SLED, authenticated open-ended planning,
serialisable verification subset, and pinned AgentDojo translation. Its
implementation-status table states the evidence boundary for each surface.

The repository-validation result is sourced from the retained
`output/validation/6fe6b584500e/` record. Research-result placeholders must
be replaced only by files generated from versioned `output/runs/*/result.json`
evidence. Do not copy archived trace counts into current-result tables.

The implementation now includes bounded native and solver-facing verification,
property-scoped cone-of-influence reduction, argument-aware policy, audience
disclosure, structured attribution, open-ended dynamic planning, a pinned
AgentDojo translation boundary, an optional pinned Cedar adapter, and a scoped
delegation model that is disabled at runtime. These are implementation or
bounded-model statements, not live integration findings. Planning, AgentDojo,
Cedar-parity, and delegation-activation claims remain pending until their
gated protocols produce completed retained result JSON with verified checksums.

## arXiv submission bundle

`scripts/build_arxiv_bundle.py` stages the source an arXiv submission needs and
packages it as a deterministic `.tar.gz` below `.local/arxiv-bundle/`. It
resolves every `\input`, `\bibliography` and `\includegraphics` target from the
manuscript, refuses to package a tree with a missing dependency, and compares
the tracked `ARXIV_BUNDLE.json` manifest with the files it ships, so a changed
source or a stale manifest stops the build. The archive root is this directory,
because arXiv compiles from the root of the submission directory. The standard
validation tier runs the script with `--check`.

Those rules were read from <https://info.arxiv.org/help/submit_tex.html> on
2026-10-10: a source collection is packaged in a `.tar` or `.zip` archive;
compilation always runs from the submission root; `.bib` or `.bbl` files must
ship when BibTeX is used, and arXiv runs `bibtex`; auxiliary and output files
are removed automatically; and no on-the-fly figure conversion or embedded
JavaScript is permitted. Two limits of this host: it has no TeX distribution,
so the bundle is checked for completeness rather than compiled, and no `.bbl`
is pre-generated here, because arXiv runs `bibtex` on the shipped
`references.bib`.

[ARXIV_SUBMISSION.md](ARXIV_SUBMISSION.md) lists the submission rules, what the
script enforces, and the steps only the owner can take.

Use the [claim ledger](../../../docs/evidence/CLAIMS.md) for claim strength, the
[task registry](../../../docs/evidence/task-registry.json) for current programme status, and
the [report analysis](../../../research/reports/analysis/PROJECT_ANALYSIS.md) for historical
reconciliation. Do not infer current claims from archived manuscript sources.

## Build

The pinned Linux CI job installs TeX Live and runs:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error conflux_fourth_year_2026.tex
```

Local compilation is optional. LaTeX intermediates are ignored; the current
PDF is retained as a CI artefact until a reviewed manuscript release.

Reference metadata was checked against primary arXiv records on 29 July 2026.
`REFERENCES.md` records the verification state. Reconcile the final bibliography
with the project Zotero library before submission.
