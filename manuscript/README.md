# Current Conflux manuscript

This is the work-in-progress fourth-year paper. The canonical source is
`conflux_fourth_year_2026.tex`; the previous-year paper remains immutable under
`paper/`.

The 31 July snapshot describes the completed canonical security migration,
offline runtime and CLI, native SLED, authenticated open-ended planning,
serialisable verification subset, and pinned AgentDojo translation. Its
implementation-status table states the evidence boundary for each surface.

Numerical result placeholders must be replaced only by files generated from
versioned `runs/*/result.json` evidence. Do not copy archived trace counts into
current-result tables.

The implementation now includes bounded native and solver-facing verification,
open-ended dynamic planning, and a pinned AgentDojo translation boundary.
These are implementation statements, not empirical findings. The planning and
AgentDojo numerical placeholders remain until the gated manifests produce
retained result JSON with verified checksums.

Use the [claim ledger](../docs/CLAIMS.md) for claim strength, the
[task registry](../docs/task-registry.json) for current programme status, and
the [report analysis](../reports/analysis/PROJECT_ANALYSIS.md) for historical
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
