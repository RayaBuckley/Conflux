# Conflux workshop paper

This is the unified workshop paper covering both the original ITES/SLED work
and the Conflux fourth-year extensions. It targets a NeurIPS 2026 workshop
submission.

## Target workshops

| Workshop | Location | Deadline | Pages | Status |
|---|---|---|---|---|
| FLMSec — Foundations of Language Model Security | Paris | Aug 27, 2026 AoE | 8 | Primary |
| Agents in the Wild — Safety, Security, and Beyond | Sydney | Aug 29, 2026 AoE | 9 (or 4 short) | Fallback |
| Who Verifies the Agents? | Sydney | Aug 29, 2026 AoE | 4–9 | Secondary |

The paper is structured for 8 pages to stay portable across all three.
Adjust `\workshoptitle{}` in `conflux_workshop.tex` for the target workshop.

## Build

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error conflux_workshop.tex
```

LaTeX intermediates are ignored; the PDF is a CI artefact until a reviewed
release.

## Provenance

The archived previous-year paper under `../paper/` is integrity-protected
by `ARCHIVE_MANIFEST.json` and must not be modified. The current
fourth-year manuscript under `../manuscript/` is separate. This workshop
paper draws content from both but is a new, independent document.

## Evidence rules

Paper claims must match tested implementation behaviour. Use the
[claim ledger](../../../docs/evidence/CLAIMS.md) for claim strength and the
[task registry](../../../docs/evidence/task-registry.json) for current
programme status. Numerical tables and figures must be generated from
versioned `output/runs/*/result.json` evidence. Do not infer current claims
from archived sources.

Three evidence tiers are distinguished in the paper:

- **Archived**: prior prototype results (e.g., 1.5M trace SLED evaluation)
- **Bounded current**: canonical kernel, finite models (e.g., native SLED
  mutation testing, COI reduction)
- **Pending**: gated on retained result artefacts (e.g., real-model
  comparison, Cedar parity)

## Anonymisation

The paper uses `\usepackage[dblblindworkshop]{neurips_2026}` for
double-blind review. The style file automatically hides author information
and adds line numbers. Self-citations to the archived paper must be in
third person (e.g., "In prior work [Anonymous et al., 2025]...").
Acknowledgements are removed via the `ack` environment.

## Bibliography

`references.bib` is merged from:

- `../manuscript/references.bib` (8 verified entries)
- `../paper/iclr2026_conference.bib` (unique prompt-injection and AC entries)
- Classical security literature verified against `../manuscript/REFERENCES.md`

Bibliography metadata was checked against primary arXiv records on 29 July
2026. Reconcile the final bibliography with the project Zotero library
before submission.

## Template

The NeurIPS 2026 style file (`neurips_2026.sty`) and checklist
(`checklist.tex`) are from the official NeurIPS 2026 template package.
Workshop mode is selected via `\usepackage[dblblindworkshop]{neurips_2026}`
with `\workshoptitle{...}` set to the target workshop name.

## Rationale

A separate workshop directory keeps the unified paper distinct from both the
integrity-protected archived paper and the in-progress fourth-year manuscript.
The archived paper is immutable evidence; the manuscript tracks current
fourth-year work. The workshop paper synthesises both into a self-contained
submission without modifying either source.
