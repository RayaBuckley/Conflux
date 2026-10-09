# ADR-026: Continuation of the Part B project and contribution provenance

- Type: adr
- Status: accepted
- Date: 2026-10-09
- Owners: Conflux maintainers

## Context

The fourth-year project (Part C) continues the third-year project (Part B) on
the same research line: ITES as a reference monitor that prevents authority
amplification, Principal Context as the unit of authority, and SLED as bounded
exploration of the resulting state space. Part B produced a prototype, a report
and a preprint, and archived evidence of about 1.46 million explored traces.

Two facts make an explicit provenance record necessary:

1. The examiner of the fourth-year report must be able to tell which parts of
   the submitted work are third-year contributions and which are fourth-year
   contributions. Presenting Part B results as new Part C work would be a
   misrepresentation; omitting the continuation would understate the Part C
   contribution.
2. Paper submissions are different: a journal or workshop submission may present
   the whole line of work as one submission, because the venue judges the
   contribution, not the year in which it was produced.

The FLMSec 2026 workshop submission was a Part B result packaged and revised
during Part C; it was rejected. The rejection does not change the project scope,
and its review reasons (writing quality, limited empirical evidence) are now
addressed as Part C workstreams rather than by resubmitting the same text.

## Decision

1. **Continuation is stated, not implied.** The dissertation states in its
   introduction that it continues the Part B project, names what Part B
   established, and names the open problems Part B left.

2. **Every claim carries an origin.** `docs/evidence/CLAIMS.md` gains an `Origin`
   column with exactly three values:

   | Value | Meaning |
   | --- | --- |
   | `Part B` | Established in the third-year project and not re-derived here; cited as prior work, never presented as a Part C result. |
   | `Part B, reproduced` | A Part B result re-executed during Part C, with the archive path and the reproduction artefact recorded. |
   | `Part B concept, Part C evidence` | The idea is a third-year contribution; the implementation, tests or proof cited in the row were produced in Part C. The contribution claim belongs to Part B, the evidence to Part C. |
   | `Part C` | New contribution of the fourth-year project. |

3. **Part B evidence stays in the archive.** Part B artefacts under
   `research/reports/archive/2026-06-01-original-prototype/` and
   `research/publications/paper/` are immutable references. Part C results that
   reuse Part B fixtures name the archived source and the Part C artefact.

4. **The examiner-facing table is mandatory.** The dissertation contains one
   table with a row per contribution, its origin, and the artefact that supports
   it. This table is generated from the claim ledger rather than written by hand,
   so it cannot drift from the evidence.

5. **Submissions may present the whole line of work.** A paper submission may
   include Part B and Part C results as one contribution. Any such submission
   still states which results were previously published or submitted, so the
   venue is not misled about novelty.

6. **A rejected submission is disclosed in the report.** The dissertation notes
   that a Part B result was submitted to FLMSec 2026 and rejected, with the
   review reasons and the Part C changes that address them. Disclosure protects
   the resubmission path: a later venue may ask for prior submission history.

## Consequences

- The fourth-year contribution is defined by exclusion: it is everything the
  ledger marks `Part C`. On the current ledger this is the formal verification
  line (SLED-V, IR-encoded verification, solver agreement), canonical-state
  exploration and counterexample minimality, the planning and re-authorisation
  runtime, finer-grained authority semantics (ADRs 024, 025), the comparative
  defence analysis, the evidence and claim infrastructure, the measured
  operational tooling (`scripts/runpod/guard.py` and its audit), and the
  planned agent-security empirical programme.
- Part B contributes the problem statement, ITES and Principal Context, the SLED
  idea, the bounded trace experiments, and the 12-category task taxonomy.
- The generated table keeps the boundary visible during writing, so a Part B
  result cannot drift into the Part C contribution narrative by accident.

## Related

- `docs/evidence/CLAIMS.md` - the ledger this ADR extends.
- `docs/evidence/EVALUATION.md` - Part B versus Part C comparison.
- `docs/reference/GLOSSARY.md` - Part B and Part C definitions.
- `.conflux-investigation/PLAN-partC-programme.md` - the Part C programme.
