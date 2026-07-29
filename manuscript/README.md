# Current Conflux manuscript

This is the work-in-progress fourth-year paper. The canonical source is
`conflux_fourth_year_2026.tex`; the previous-year paper remains immutable under
`paper/`.

Numerical result placeholders must be replaced only by files generated from
versioned `runs/*/result.json` evidence. Do not copy archived trace counts into
current-result tables.

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
