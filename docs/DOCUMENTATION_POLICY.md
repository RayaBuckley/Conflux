# Documentation policy

> **Status:** canonical · **Owner:** project owner · **Last reviewed:** 2026-10-22
> **Canonical for:** document classes, permanence labels, and writing rules.

This repository has several kinds of documentation. They answer different
questions and have different lifetimes. This page defines the labels used at the
top of maintained documents, the rules for changing each kind, and the writing
habits that keep the repository readable.

## Permanence labels

Use one of these labels in the first block of every maintained document.

| Label | What it means | Change rule |
|---|---|---|
| `canonical` | The current source of truth for a contract, rule, or interface. | Change only with review. Update every document that links here. |
| `living` | A current snapshot that is expected to change. | Update at each milestone. Keep it short; move dated history to git or a history file. |
| `proposal` | A design that is not implemented or accepted. | Mark every claim as proposed. Change or reject it without treating it as current behaviour. |
| `historical` | A frozen record of what was done or believed at a point in time. | Do not edit except to add a supersession note. Do not use it for current claims. |
| `generated` | A file produced by a script from retained inputs. | Do not hand-edit. Regenerate it and record the source and checksum. |
| `working` | Notes, scratch work, or investigation material. | Not canonical. Do not link to it as if it were shipped documentation. |

The label is about intended lifetime, not importance. A short historical note can
be more important than a long living page.

## Metadata block

Put a visible metadata block at the top of a maintained document:

```markdown
> **Status:** living · **Owner:** project owner · **Last reviewed:** 2026-10-22
> **Canonical for:** current implementation status
```

Rules:

- `Status` is one of the labels above.
- `Owner` is a role, not a person. Use `project owner` unless a narrower role is
  real and maintained.
- `Last reviewed` is the date a human last checked the document against its
  source. It is not the date of the last typo fix.
- `Canonical for` names the fact or contract this document owns. Omit it when the
  document owns no fact.
- Do not add metadata to generated files or archived files that must remain
  byte-identical. Add a separate `README.md` beside them instead.

## Document classes

The four Diátaxis classes are useful for reader intent. Conflux adds evidence,
decisions, and generated records because research work needs them.

| Class | Reader question | Typical documents |
|---|---|---|
| Tutorial or quick start | How do I get one successful result? | `README.md` quick start, `docs/DEVELOPMENT.md` setup |
| How-to guide | How do I perform a task? | `docs/reference/CLI.md`, `docs/integrations/` |
| Reference | What are the exact rules, names, and interfaces? | `docs/reference/SECURITY_MODEL.md`, `SEMANTICS.md`, `GLOSSARY.md` |
| Explanation | Why does this exist, and how do the parts fit? | `docs/OVERVIEW.md`, `docs/reference/ARCHITECTURE.md`, `docs/research/` |
| Decision record | Why was this choice made, and is it still current? | `docs/decisions/` |
| Evidence | What was measured, under what limits, and what may be claimed? | `docs/evidence/`, retained run bundles |
| Generated record | What did the script produce from retained inputs? | `research/output/`, generated tables and figures |

Do not mix these jobs in one page when a link will do. A tutorial should not
carry a claim ledger. A reference page should not tell a story. An evidence page
should not present a proposal as a result.

## Ownership

Every fact has one canonical owner. Other documents link to the owner instead of
restating the fact.

| Fact | Canonical owner |
|---|---|
| Executable behaviour | code, tests, and schemas |
| Intended security behaviour | accepted ADRs and `docs/reference/SECURITY_MODEL.md` |
| Formal invariants | `docs/reference/SEMANTICS.md` |
| Current implementation status | `docs/evidence/STATUS.md` and `docs/evidence/task-registry.json` |
| What may be claimed from evidence | `docs/evidence/CLAIMS.md` and the retained bundle |
| Historical recommendations | `research/reports/analysis/` |
| Publication scope | `research/publications/README.md` and each publication's `README.md` |

When two owners disagree, that is a defect. Record the disagreement and repair
the owner. Do not pick the version that makes the current task easier.

## Writing rules

These rules target the most common failure mode in a long research repository:
text that sounds complete but does not help a reader decide or act.

1. **Lead with the reader's job.** In the first two sentences, say who the
   document is for and what they can do after reading it.
2. **Use concrete nouns and verbs.** Prefer "the executor receives the action
   and a certificate id" to "the system provides robust enforcement".
3. **State the evidence boundary.** Say whether a statement is implemented,
   measured, proposed, or historical.
4. **Keep one fact in one place.** Link to the canonical owner. Repeated
   summaries drift.
5. **Use dates and versions.** "Current" is not a date. "Recent" is not a
   version.
6. **Cut empty framing.** Remove "This document aims to", "It is important to
   note", and "In summary" when the next sentence already does the work.
7. **Do not use a three-part list as a substitute for an argument.** Use a list
   only when the items are parallel and each item matters.
8. **Do not claim breadth from a narrow run.** Name the tasks, models, bounds,
   and denominators.
9. **Mark proposals in the present tense of the design, not the system.** Write
   "the proposed checker returns..." not "the checker returns..." until it is
   implemented and tested.
10. **Delete or archive documents with no reader.** A stale page is worse than
    no page because it competes with the canonical owner.

### AI-slop checklist

Before committing a prose change, check for these patterns:

- repeated summaries at the top and bottom of the same page;
- long lists of abstract nouns with no actor or action;
- "comprehensive", "robust", "seamless", "critical", and "essential" used
  without a measurable referent;
- "not X but Y" used as a rhythm rather than a real distinction;
- a heading for every paragraph;
- a rationale section that restates the decision;
- claims with no link to code, a test, a bundle, or an ADR;
- the same claim stated in the README, overview, status page, and paper;
- a "Recent changes" section that duplicates git history.

The fix is usually deletion, not rewording.

## Review and change rules

- `canonical`: review when the contract changes, and at each release.
- `living`: review at each milestone; add the review date.
- `proposal`: review when the proposal is accepted, rejected, or implemented.
- `historical`: never edit the body. Add a supersession link in a separate index.
- `generated`: regenerate from the recorded script and inputs; never patch by
  hand.

Use `docs/templates/` for new documents. A new ADR starts from
`docs/decisions/000-template.md` and must have a `Status:` line. A new evidence
record must name its bundle, script, and retention boundary.

## Document map

| Need | Start here |
|---|---|
| Understand the project | `README.md`, then `docs/OVERVIEW.md` |
| Run the offline path | `README.md` quick start, then `docs/DEVELOPMENT.md` |
| Check current status | `docs/evidence/STATUS.md` |
| Check what may be claimed | `docs/evidence/CLAIMS.md` |
| Read the security contract | `docs/reference/SECURITY_MODEL.md` |
| Read the formal invariants | `docs/reference/SEMANTICS.md` |
| Find a term | `docs/reference/GLOSSARY.md` |
| Understand a design choice | `docs/decisions/README.md` |
| Work on the repository with an AI agent | `AGENTS.md`, then `docs/AI_AGENT_GUIDE.md` |
| Read a paper or report | `research/publications/README.md` |

## External guidance used

- Diátaxis, a four-part documentation framework:
  <https://diataxis.fr/>
- GitLab handbook front matter, including document status and review metadata:
  <https://handbook.gitlab.com/docs/frontmatter/>
- GitHub Docs YAML front matter:
  <https://docs.github.com/en/contributing/writing-for-github-docs/using-yaml-frontmatter>
- "The Field Guide to AI Slop", for the repetition and vagueness patterns above:
  <https://www.ignorance.ai/p/the-field-guide-to-ai-slop>
