# Next Review: 2026-08-26

## Manuscript status

- **Location**: `research/publications/flmsec_2026/main.tex`
- **Build**: Not yet verified (LaTeX not available in this environment). Needs `latexmk -pdf main.tex` with NeurIPS 2026 style file.
- **Page count**: Not yet checked. Needs verification after build.
- **Anonymity audit**: PASSED (no author names, institutions, emails, or identifying URLs)
- **Placeholder audit**: PASSED (no TODO, TBD, FIXME, "generated result pending")

## Completed deliverables

| Deliverable | Location | Status |
| --- | --- | --- |
| Dedicated FLMSec source | `research/publications/flmsec_2026/main.tex` | Done |
| Anonymous default build | `main.tex` (anonymous author block) | Done |
| `SUBMISSION_CHECKLIST.md` | `research/publications/flmsec_2026/SUBMISSION_CHECKLIST.md` | Done |
| Claim/evidence map | `research/publications/flmsec_2026/CLAIM_EVIDENCE_MAP.md` | Done |
| Evidence table generator | `scripts/generate_flmsec_tables.py` | Done |
| Generated tables (4) | `research/publications/flmsec_2026/generated/tables/*.tex` | Done |
| `references.bib` with classical IFC | `research/publications/flmsec_2026/references.bib` | Done |
| NeurIPS checklist | Appendix A of `main.tex` | Done |
| Biba/low-water-mark lineage | Section 3, paragraph after Theorem 2 | Done |
| TCB box | Section 2.3 | Done |
| Research questions | Section 5 intro (RQ1-RQ4) | Done |
| Comparison table | Section 6, Table 2 | Done |
| Architecture diagram | Section 5.5, Figure 1 | Done |
| Motivating example | Section 5.4 | Done |

## Unresolved high-value issues

### Must resolve before submission

1. **NeurIPS 2026 style file**: `neurips_2026.sty` is referenced but not yet present in the `flmsec_2026/` directory. Need to obtain the official NeurIPS 2026 style file and place it there. Alternatively, if FLMSec uses a different template, update `\documentclass` and `\usepackage` accordingly.
2. **LaTeX build**: The manuscript has not been compiled. Must verify it builds cleanly and check page count (≤8 main text pages excluding references/appendix).
3. **Biba primary source verification**: The Biba framing says "structurally analogous to Biba's low-water-mark integrity policy." Verify this against the actual Biba 1977 paper before final submission. The citation currently uses `@inproceedings{biba1977}` with MITRE Technical Report as the booktitle — confirm this is the correct citation format.

### Should resolve if time permits

4. **Z3 BMC evidence**: The checker-agreement table (Table 2) currently reports COI fixture agreement but not Z3 BMC results directly. The Z3 verification evidence exists in the claim ledger but the run directories (`verify-coi-*`) are not present in `research/output/runs/`. This may be because Z3 was unavailable in the generation environment. If Z3 evidence can be regenerated, add a Z3 column to Table 2.
5. **Observational confidentiality**: Mentioned in the SLED-V section but no dedicated table. If concise, add a one-row evidence entry.
6. **Comparative defence table**: Currently hand-coded from test verdicts. Consider generating from a JSON evidence file if one is created in the future.
7. **Page pressure**: If the paper exceeds 8 pages, candidates for cutting: the motivating example subsection (5.4), the architecture diagram (5.5), or moving the NeurIPS checklist to a separate file.

## Uncertain citations

8. **LOMAC**: Cited as `@inproceedings{lomac2001}` with "LOMAC: Low Water-Mark Integrity Protection for Linux" by Maxwell Krohn. Verify the author and venue.
9. **Myers and Liskov**: Cited as `@inproceedings{myers2000}` but the entry references "Protecting Mobile Agents from External Attacks" which may be the wrong paper. The decentralized IFC work is "Decentralizing Information Flow Control" (POPL 1997). Fix or remove if uncertain.
10. **PACT and FORGE**: These are recent (2026) preprints. Verify exact titles, author lists, and arXiv IDs against the actual papers before submission.

## Questions for tomorrow's review

1. Is the Biba distinction technically precise enough?
2. Is maximal safe authorization the best theorem to foreground?
3. Does PE need refinement for delegation/consent/authority-bearing arguments?
4. Which contemporary systems belong in main text vs. appendix?
5. Is the comparative Dual-LLM/CaMeL/Progent/PACT abstraction fair enough?
6. What should be cut for the eight-page limit?
7. Are NeurIPS checklist answers fully supported?
8. Should an anonymous evidence/code artifact be prepared?
9. What final title/abstract best matches the finished evidence?
10. Is the Part B 1.5M reproduction feasible before the deadline?

## Stretch goals (P1/P2, after manuscript gate)

- **P1**: Reviewer pre-mortem document (`WORKSHOP_REVIEW_PREMORTEM.md`)
- **P1**: COI scaling experiment (deterministic, no LLM dependency)
- **P2**: Part B 1.5M trace reproduction
- **P2**: Runtime/IR differential conformance testing
