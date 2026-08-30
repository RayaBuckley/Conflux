# Literature Verification Protocol

This document defines the canonical method for going through every source
in the Conflux literature corpus, checking each for relevant useful parts
and limitations, and verifying bibliographic metadata against primary
sources. It is the operational companion to the
[novelty audit](../../research/reports/analysis/2026-08-16-novelty-audit.md),
the [foundational security literature analysis](../../research/reports/analysis/2026-08-13-foundational-security-literature.md),
and the [claim ledger](../evidence/CLAIMS.md).

The machine-readable corpus lives at
`research/reports/analysis/literature_corpus.json` and is validated
against `schemas/literature-corpus.schema.json` (v2).

## Purpose

A novelty audit is only as strong as the primary-source verification behind
it. The repository has 109 tracked sources: 9 Priority A foundational
security works, 6 Priority B dynamic IFC systems, 5+ Priority C classical
frameworks, and ~80 modern agent-security works. Until each source has
been read and its relationship to Conflux assessed, the novelty audit's
claim classifications remain provisional.

This protocol ensures that:

1. Every source is checked against its primary publication record.
2. Useful parts and limitations are recorded in a structured, queryable
   format.
3. Novelty claims are linked to the sources that affect them.
4. The process is reproducible — another researcher can follow the same
   steps and reach the same evidence base.

## Reading order

Sources are verified in priority order. Within each priority tier, works
that affect the highest-risk novelty claims are read first.

### Tier 1: Priority A foundational works (9 sources)

These are the classical integrity and IFC works whose relationship to
Conflux is most direct. Each must achieve `primary_source` verification
with `full_text` depth.

| Key | Work | Claims affected |
|---|---|---|
| `biba1977` | Biba (1977), Integrity Considerations | A1, A2, A8 |
| `lomac` | Fraser (2000), LOMAC | A1, A8 |
| `denning1976` | Denning (1976), Lattice Model | A1 |
| `sabelfeld2003` | Sabelfeld & Myers (2003), Language-Based IFC | A8, A11 |
| `myersliskov` | Myers & Liskov (2000), Decentralized IFC | A2, A11 |
| `declassificationsurvey` | Sabelfeld & Sands (2009), Declassification | A10 |
| `robustdeclassification` | Zdancewic & Myers (2001), Robust Declassification | A10 |
| `attackercontrol` | Askarov & Myers (2007), Attacker Control | A11 |
| `nonmalleableifc` | Cecchetti et al. (2017), Nonmalleable IFC | A14 |

### Tier 2: Priority A modern works (already verified)

These 8 arXiv sources were verified against primary arXiv records on
29 July 2026. They need `reading_status: "read"` and structured
`relevance`/`novelty_impact` fields populated.

CaMeL, AgentDojo, StruQ, Spotlighting, Progent, PACT, FORGE, SecAlign.

### Tier 3: Priority B dynamic IFC systems (6 sources)

Each must achieve at least `scholar_metadata` verification with
`abstract_and_key_sections` depth.

Asbestos, HiStar, Flume, DStar, LIO, CamFlow.

### Tier 4: Priority C classical frameworks (5+ sources)

Each must achieve at least `scholar_metadata` verification with
`metadata_only` depth.

Saltzer & Schroeder, Harrison-Ruzzo-Ullman, Confused Deputy (Hardy),
capability attenuation literature, Rushby noninterference.

### Tier 5: Remaining modern agent works (~80 sources)

Verified by abstract reading. Priority is determined by
`adoption_priority` then by `closest_relation` relevance.

## Per-source checklist

For each source, complete the following steps:

1. **Verify bibliographic metadata.** Confirm that the title, author
   list, year, venue, volume, pages, and DOI match the primary
   publication record. For arXiv sources, check the current version and
   note any version changes since the last check.

2. **Read the source.** For Priority A, read the full text. For Priority
   B, read the abstract, introduction, and sections most relevant to
   Conflux (label model, authority model, downgrading). For Priority C,
   read at least the abstract and a survey summary.

3. **Extract key mechanism and formal guarantee.** Record what the
   source's core security mechanism is and what formal property it
   establishes (or does not establish).

4. **Assess relationship to Conflux.** Classify as one of:
   `mechanism` (shared mechanism), `distinction` (Conflux differs),
   `limitation` (the source reveals a Conflux limitation),
   `background` (provides vocabulary or foundation), or
   `adapter_target` (potential integration point).

5. **Identify useful parts.** What specific concepts, vocabulary,
   mechanisms, or results can Conflux borrow or cite?

6. **Identify limitations.** What does the source not establish? Where
   does it fall short? What assumptions does it make that Conflux does
   not share?

7. **Assess novelty risk.** Which Conflux claims (A1–A15 from the novelty
   audit) does this source affect? What is the risk level (high, medium,
   low, none)? What qualification does Conflux need to add or retain?

8. **Update the corpus entry.** Set `reading_status` to `"read"`,
   `verification.method` to the achieved level, `verification.depth` to
   the achieved depth, and populate `relevance` and `novelty_impact`.

9. **Update the novelty audit.** If the finding changes a claim's risk
   level, update `research/reports/analysis/2026-08-16-novelty-audit.md`.

10. **Record snowball status.** Perform backward citation search (papers
    the source cites) and forward citation search (papers citing this
    source). Record whether each is `done`, `pending`, or
    `not_applicable`.

## Source quality hierarchy

When verifying metadata, prefer sources in this order:

1. Original paper or technical report (publisher's record).
2. Author's institutional copy (personal/university website).
3. Authoritative project documentation (e.g., official GitHub, NIST).
4. Peer-reviewed survey citing the work.
5. Secondary summaries (Google Scholar, Wikipedia) — for discovery only,
   never as the basis for a citation or novelty claim.

For every novelty-critical comparison, the corpus entry must record:

- The claim being assessed.
- The supporting source and the specific section or passage.
- The interpretation (what the source says about the claim).
- The confidence level (high/medium/low).
- Any remaining ambiguity.

## Field semantics

| Field | Type | Purpose |
|---|---|---|
| `verified.method` | enum | How metadata was verified |
| `verified.depth` | enum | How deeply the source was read |
| `verified.date` | string | ISO date of last verification |
| `verified.checked_by` | string | Who performed the verification |
| `reading_status` | enum | Current reading progress |
| `reading_priority` | enum | A/B/C/D reading tier |
| `source_type` | enum | What kind of publication |
| `relevance.useful_parts` | string | What Conflux can borrow or cite |
| `relevance.conflux_relation` | string | How the source relates to Conflux |
| `relevance.key_findings` | string[] | Specific extracted findings |
| `relevance.limitations` | string[] | What the source does not establish |
| `novelty_impact.affected_claims` | string[] | Claim IDs (A1–A15) this source affects |
| `novelty_impact.risk_level` | enum | How much the source endangers Conflux novelty |
| `novelty_impact.qualification_needed` | string | What Conflux must acknowledge |

## Test enforcement

The test suite (`tests/test_literature_corpus.py`) enforces:

- **Schema validity**: the corpus validates against the v2 schema.
- **Key uniqueness**: no duplicate keys, DOIs, or arXiv IDs.
- **Verification completeness**: Priority A entries must have
  `primary_source` verification with `full_text` depth.
- **Reading completeness**: entries marked `read` must have non-empty
  `key_findings` and `limitations`.
- **Claim validity**: `novelty_impact.affected_claims` entries must
  match claim IDs from the novelty audit (A1–A15).
- **Snowball tracking**: Priority A and B entries must have
  `snowball_status` with both `backward` and `forward` fields.
- **Bibliography cross-reference**: every `references.bib` key must
  exist in the corpus; every `REFERENCES.md` key must exist in the
  corpus.

## Relationship to other documents

| Document | Role |
|---|---|
| [Novelty audit](../../research/reports/analysis/2026-08-16-novelty-audit.md) | Defines claims A1–A15 and their current risk levels |
| [Foundational literature analysis](../../research/reports/analysis/2026-08-13-foundational-security-literature.md) | Conceptual analysis that motivates the reading list |
| [Literature matrix](../../research/reports/analysis/2026-08-16-literature-matrix.md) | Structured comparison of Priority A–C works |
| [Claim ledger](../evidence/CLAIMS.md) | Canonical claim-strength tracking |
| [Related work](RELATED_WORK.md) | Manuscript-facing positioning |
| [REFERENCES.md](../../research/publications/manuscript/REFERENCES.md) | Bibliography verification status |
| [references.bib](../../research/publications/manuscript/references.bib) | BibTeX entries used by the manuscript |

## Rationale

A structured, test-enforced protocol prevents the novelty audit from
becoming stale or subjective. By recording what was read, what was found,
and how it affects each claim, the process becomes auditable by a
supervisor or examiner. The separation of corpus (data), protocol
(method), and tests (enforcement) follows the repository's existing
documentation-authority model.
