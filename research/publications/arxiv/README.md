# arXiv preprint: Preventing Privilege Escalation in LLM Agents

## Audience

The international research community. This is the self-contained +
research paper that the publications register lists as the arXiv preprint.

## Goal

One cohesive research contribution: the ITES provenance-based authority
model, the SLED worst-case evaluator, and the Conflux reference
implementation with its bounded current evidence. The paper presents the
work as a single contribution with no year-by-year framing; framing notes
live in the repository register, not in the paper.

## Rationale

This document is deliberately not structured as the fourth-year report. The
report separates work completed in the previous year from work completed
this year, because its reader is an examiner who judges progress within a
year. A research paper is judged on the contribution itself, so that same
separation reads as administrative history and weakens the claim. This paper
therefore presents the ITES/SLED theory, the Conflux implementation, and the
bounded evidence as one body of work, with no prior-year/current-year split,
and it does not address an examiner. The framing lives in the publications
register, not in the paper.

## Contents

- `main.tex` — the paper.
- `references.bib` — bibliography, merged from the workshop paper's verified
  entries.
- `generated/tables/` — six retained-result tables, each generated from
  versioned `result.json` evidence and stamped with its source digests.
- `generated/figures/` — three retained-result figures in plain TikZ, with
  `CHECKSUMS.sha256`.

## Built from

`main.tex` is a new document. Its structure follows the unified workshop
paper (`../workshop/conflux_workshop.tex`), and it adds the formal
verification material (unbounded routes, falsifiability of a holding
verdict) and the remote 14B AgentDojo results from the fourth-year
manuscript (`../manuscript/conflux_fourth_year_2026.tex`). Neither source
is modified.

## Evidence rules

Every number in the paper comes from the retained bundles under
`research/output/runs/`. The generated tables and figures are written by
`scripts/generate_fourth_year_tables.py` and
`scripts/generate_manuscript_figures.py`; add or remove an asset only by
regenerating it, never by editing a generated file. Stale workshop figures
whose inputs no longer exist are excluded.

## Build

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Bundle

`scripts/build_arxiv_bundle.py` stages the submission tree from this
directory and checks every input, bibliography, citation and named
repository path before packaging. Run it with `--check`.

## Submission metadata

The submission form needs the title and the abstract as plain ASCII under
1920 characters; `build_arxiv_bundle.py --metadata` prints both and fails
when either field cannot be submitted. The current title is 93 characters and
the abstract is 1898 characters. The bundle ships 11 files and `--check` is
clean.

Owner decisions still required for the submission form:

- **Primary category.** Suggested `cs.CR` (Cryptography and Security), with
  `cs.AI` as a possible cross-list. The paper's lead claim is system-level
  authority confinement; the owner should confirm the category.
- **License.** Use the arXiv license selected by the owner. This repository
  does not set a default.
- **Comments.** Optional. Do not state code or evidence availability unless a
  public URL exists.

Pre-submission gate: the full effect-bearing AgentDojo matrix is not yet run.
Do not submit until the owner decides that the retained breadth pilots and the
other evidence are enough for the intended claim.
