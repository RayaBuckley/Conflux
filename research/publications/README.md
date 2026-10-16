# Publications

Every document in this directory has a different reader. This register records
the audience and the goal of each publication, so a document is never framed
for the wrong reader.

Framing lives here, not in the papers. A manuscript speaks to its own audience
without explaining who that audience is.

## Rationale

The same body of work is reported in three ways, and each way has a different
reader. An annual report is judged on progress within a year, so it must
separate work already done from work done since the last review. A research
paper is judged on the contribution itself, so that same separation reads as a
record of administrative history and weakens the claim. Stating the audience
here keeps one framing from being copied into the other.

## Register

| Document | Audience | Goal |
| --- | --- | --- |
| [paper/](paper/ARCHIVED.md) | Reviewers of the previous year | Frozen record of the previous prototype |
| [manuscript/](manuscript/README.md) | The fourth-year reviewer | Progress report, year by year |
| [workshop/](workshop/README.md) | NeurIPS 2026 workshop reviewers | One unified eight-page contribution |
| [flmsec_2026/](flmsec_2026/SUBMISSION_CHECKLIST.md) | FLMSec 2026 reviewers | Influence-tracking submission package |
| arXiv preprint | The international research community | One cohesive research contribution |

## paper/ - archived previous-year paper

- **Audience**: the reviewers of the venue the previous year's paper was sent to.
- **Goal**: an immutable record of the previous prototype and its bounded results. Every file is pinned by `paper/ARCHIVE_MANIFEST.json`, and repository validation fails if one of them changes.
- **Not**: evidence for the current architecture. Recorded in `paper/ARCHIVED.md`.

## manuscript/ - fourth-year report

- **Audience**: the fourth-year reviewer.
- **Goal**: report progress and state the evidence boundary of each claim.
- **Framing**: it separates work completed in the previous year from work completed this year. That is correct for this reader, and it is not a model for any other document.
- **Open issue**: `scripts/build_arxiv_bundle.py` points `MANUSCRIPT` at this file, so the arXiv bundle currently ships the fourth-year report rather than a research paper.

## workshop/ - unified workshop paper

- **Audience**: NeurIPS 2026 workshop reviewers. FLMSec is the primary target, and the paper is held to eight pages so it stays portable.
- **Goal**: one self-contained contribution covering both the ITES/SLED work and the fourth-year extensions. `conflux_workshop.tex` is a new document, not a version of `paper/`.
- **Title**: Preventing Privilege Escalation in LLM Agents: Provenance-Based Authority from Theory to Canonical Implementation.

## flmsec_2026/ - earlier FLMSec submission package

- **Audience**: FLMSec 2026 reviewers, deadline 27 August 2026.
- **Goal**: the influence-tracking framing of the work, with its own checklist and claim-to-evidence map.
- **Relation to workshop/**: same venue, different framing and a different document. `workshop/` covers the wider body of work.

## arXiv preprint

- **Audience**: the international research community.
- **Goal**: one cohesive research contribution. Every part of the work appears as a single body of research.
- **Framing rule**: the preprint must not be structured as a progress report, must not separate the work by year, and must not read as a document written for examiners.
- **Status**: no dedicated source file yet. The bundle step builds from the fourth-year report until one exists.
