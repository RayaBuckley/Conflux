# Next Review: 2026-08-27

## Manuscript status

- **Location**: `research/publications/flmsec_2026/main.tex`
- **Build**: Needs re-verification after restructuring.
- **Page count**: Needs verification after restructuring.
- **Anonymity audit**: PASSED (no author names, institutions, emails, or identifying URLs)
- **Placeholder audit**: PASSED (no TODO, TBD, FIXME, "generated result pending")

## Structure (restructured to follow preprint)

| Section | Title | Notes |
| --- | --- | --- |
| 1 | Introduction | ITES prominent, 4 contributions (PE, ITES, SLED, SLED-V), preprint tone |
| 2 | Related Work | Moved before Threat Model; Model-Level, System-Level, Classical IFC/Biba, Evaluation, Summary |
| 3 | Threat Model and Security Objective | ACS tuple, definitions, TCB box |
| 4 | Influence Tracking with Extrapolated Security | Expanded to preprint detail; Biba paragraph; architecture figure |
| 5 | SLED: A System-Level Evaluator for Defences | Preprint subsections + brief SLED-V subsection |
| 6 | Results | 1.5M trace tables (main eval) + SLED-V preliminary results subsection |
| 7 | Future Work | Preprint structure + delegation/consent expansion |
| 8 | Conclusion | Preprint tone, ITES name |
| App A | Trace-Level Reproduction | Part B table |
| App B | NeurIPS checklist | checklist.tex |

## Completed deliverables

| Deliverable | Location | Status |
| --- | --- | --- |
| Dedicated FLMSec source | `research/publications/flmsec_2026/main.tex` | Done |
| Restructured to follow preprint | `main.tex` | Done — ITES prominent, preprint section order, 1.5M traces as main eval |
| Anonymous default build | `main.tex` (anonymous author block) | Done |
| `SUBMISSION_CHECKLIST.md` | `research/publications/flmsec_2026/SUBMISSION_CHECKLIST.md` | Done |
| Claim/evidence map | `research/publications/flmsec_2026/CLAIM_EVIDENCE_MAP.md` | Done |
| Evidence table generator | `scripts/generate_flmsec_tables.py` | Done |
| Generated tables (6) | `research/publications/flmsec_2026/generated/tables/*.tex` | Done |
| `references.bib` with classical IFC + preprint citations | `research/publications/flmsec_2026/references.bib` | Done — added davi2010privilege, model-level defence citations |
| NeurIPS checklist | `checklist.tex` (\input in appendix) | Done |
| Biba/low-water-mark lineage | Section 4, paragraph after Theorem 2 | Done |
| TCB box | Section 3.3 | Done |
| Comparison table | Section 2, Table 1 | Done — includes PACT and FORGE |
| Architecture diagram | Figure 1 (in Section 4, ITES) | Done |
| Motivating example | Section 6.1 (Results, Security) | Done — moved from intro to Results per preprint |
| SLED-V preliminary results | Section 6.4 | Done — condensed RQ1-RQ4 into one subsection |

## Unresolved high-value issues

### Must resolve before submission

1. ~~**NeurIPS 2026 style file**~~: RESOLVED.
2. ~~**LaTeX build**~~: Needs re-verification after restructuring.
3. ~~**Biba primary source verification**~~: RESOLVED.

### Should resolve if time permits

4. ~~**Z3 BMC evidence**~~: RESOLVED.
5. **Observational confidentiality**: Mentioned in SLED-V subsection but no dedicated table.
6. **Comparative defence table**: Generated from JSON evidence.
7. ~~**Page pressure**~~: Needs re-verification after restructuring.

## Uncertain citations

8. ~~**LOMAC**~~: RESOLVED.
9. ~~**Myers and Liskov**~~: RESOLVED.
10. ~~**PACT and FORGE**~~: RESOLVED.

## Questions for next review

1. Is the Biba distinction technically precise enough?
2. Is maximal safe authorization the best theorem to foreground?
3. Does PE need refinement for delegation/consent/authority-bearing arguments? (Partially addressed — Future Work paragraph.)
4. Which contemporary systems belong in main text vs. appendix?
5. Is the comparative Dual-LLM/CaMeL/Progent/PACT abstraction fair enough?
6. Are NeurIPS checklist answers fully supported?
7. Should an anonymous evidence/code artifact be prepared?
8. Does the restructured paper fit within 8 pages?

## Stretch goals (P1/P2, after manuscript gate)

- ~~**P1**: Reviewer pre-mortem document (`WORKSHOP_REVIEW_PREMORTEM.md`)~~ Done
- ~~**P1**: COI scaling experiment (deterministic, no LLM dependency)~~ Done
- ~~**P2**: Part B 1.5M trace reproduction~~ Done — included in Appendix A
- **P2**: Runtime/IR differential conformance testing
