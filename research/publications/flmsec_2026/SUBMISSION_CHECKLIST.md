# FLMSec 2026 Submission Checklist

## Venue

NeurIPS 2026 Workshop on Foundations of Language Model Security (FLMSec)
Deadline: 27 August 2026, 23:59 AoE

## Format requirements

- [x] NeurIPS 2026 template used
- [x] Main text ≤8 pages excluding references/appendix (needs re-verification after restructuring)
- [x] Double-blind (anonymous author block)
- [x] No acknowledgements
- [x] No identifying repository links
- [x] No author/institution names
- [x] Anonymized self-citations (none present; preprint was not published)
- [x] No identifying emails
- [x] PDF metadata to be checked before upload

## Content requirements

- [x] No "generated result pending" or placeholder text
- [x] All citations resolve in references.bib
- [x] Claims evidence-backed (see CLAIM_EVIDENCE_MAP.md)
- [x] Limitations section exists (Section 7, Future Work)
- [x] Theorem assumptions and proofs stated (Section 4)
- [x] Finite/bounded scope stated for all relevant claims
- [x] NeurIPS checklist present (Appendix B)
- [x] SLED/SLED-V distinction accurate
- [x] Biba/low-water-mark lineage explicit

## Build

- [ ] Clean LaTeX build: `latexmk -pdf -interaction=nonstopmode main.tex` (needs re-verification)
- [ ] Page count verified (needs re-verification after restructuring)
- [x] Tables generated from retained evidence: `python scripts/generate_flmsec_tables.py`

## Anonymity audit

Run: `python -c "import pathlib; t=pathlib.Path('research/publications/flmsec_2026/main.tex').read_text(); [print(f) for f in ['Raya','Buckley','Oxford','Keble','ox.ac.uk','github.com/RayaBuckley'] if f in t]"`

Expected output: none (empty).

## Placeholder audit

Run: `python -c "import pathlib; t=pathlib.Path('research/publications/flmsec_2026/main.tex').read_text(); [print(f) for f in ['TODO','TBD','FIXME','generated result pending','citation needed','???'] if f in t]"`

Expected output: none (empty).

## OpenReview

- [ ] Create OpenReview profile
- [ ] Fill in submission metadata
- [ ] Declare conflicts of interest
- [ ] Upload PDF
- [ ] Verify PDF metadata (exiftool or pdfinfo)
