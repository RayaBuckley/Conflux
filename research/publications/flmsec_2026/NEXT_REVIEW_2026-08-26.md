# Next Review: 2026-08-26

## Manuscript status

- **Location**: `research/publications/flmsec_2026/main.tex`
- **Build**: PASSED — `latexmk -pdf main.tex` builds cleanly with MiKTeX.
- **Page count**: 8 main text pages + 1 references + 8 appendix (Part B table + NeurIPS checklist) = 17 pages total. Main text within ≤8 page limit.
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
| Architecture diagram | Figure 1 (after Section 4.5, before Section 5) | Done |
| Motivating example | Section 1, \paragraph{Motivating example.} | Done |

## Unresolved high-value issues

### Must resolve before submission

1. ~~**NeurIPS 2026 style file**~~: RESOLVED. `neurips_2026.sty` is present in the `flmsec_2026/` directory and builds correctly.
2. ~~**LaTeX build**~~: RESOLVED. Builds cleanly. Page count: 8 main text pages (within ≤8 limit).
3. **Biba primary source verification**: The Biba citation uses `@techreport{biba1977}` with MITRE Technical Report MTR-3153 — this is the correct primary source. RESOLVED.

### Should resolve if time permits

4. ~~**Z3 BMC evidence**~~: RESOLVED. Z3 evidence is present (`z3-agreement-v1/result.json`); checker_agreement_table.tex includes Z3 columns with Bounded_Safe and UNSAFE verdicts.
5. **Observational confidentiality**: Mentioned in the SLED-V section but no dedicated table. If concise, add a one-row evidence entry.
6. **Comparative defence table**: Currently hand-coded from test verdicts. Consider generating from a JSON evidence file if one is created in the future.
7. ~~**Page pressure**~~: RESOLVED. Main text is 8 pages. Figure 1 and delegation paragraph added without exceeding the limit. Part B table moved to appendix.

## Uncertain citations

8. ~~**LOMAC**~~: RESOLVED. Correctly attributed to Fraser, Timothy, USENIX ATC 2001.
9. ~~**Myers and Liskov**~~: RESOLVED. Correctly cited as `myers1997difc` (POPL 1997, "Decentralizing Information Flow Control").
10. ~~**PACT and FORGE**~~: RESOLVED. Both arXiv IDs verified: PACT=2605.11039, FORGE=2602.16708. Titles and authors confirmed against arXiv.

## Questions for tomorrow's review

1. Is the Biba distinction technically precise enough?
2. Is maximal safe authorization the best theorem to foreground?
3. Does PE need refinement for delegation/consent/authority-bearing arguments? (Partially addressed — new Discussion paragraph added.)
4. Which contemporary systems belong in main text vs. appendix?
5. Is the comparative Dual-LLM/CaMeL/Progent/PACT abstraction fair enough?
6. ~~What should be cut for the eight-page limit?~~ RESOLVED — within 8 pages.
7. Are NeurIPS checklist answers fully supported?
8. Should an anonymous evidence/code artifact be prepared?
9. What final title/abstract best matches the finished evidence?
10. ~~Is the Part B 1.5M reproduction feasible before the deadline?~~ DONE — included in Appendix B.

## Stretch goals (P1/P2, after manuscript gate)

- ~~**P1**: Reviewer pre-mortem document (`WORKSHOP_REVIEW_PREMORTEM.md`)~~ Done
- ~~**P1**: COI scaling experiment (deterministic, no LLM dependency)~~ Done
- ~~**P2**: Part B 1.5M trace reproduction~~ Done — included in Appendix B
- **P2**: Runtime/IR differential conformance testing
