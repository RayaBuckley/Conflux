# ADR 012: Foundational security lineage

- Status: accepted
- Date: 2026-08-16
- Source: `reports/analysis/2026-08-13-foundational-security-literature.md`

## Decision

Position ITES's core mechanism as a **principal-sensitive authority
analogue/generalisation of low-water-mark contamination**, grounded in
existing organisational authorisation rather than a single integrity
classification.

Adopt classical information-flow-control vocabulary (declassification,
endorsement, noninterference, contamination) for existing and proposed
Conflux concepts, without changing implementation semantics.

## Consequences

- The authority-intersection rule `Allow(a, PC) iff forall p in PC,
  ACS(p, a)` is structurally analogous to Biba's low-water-mark
  integrity: consuming information from an additional principal can
  preserve or reduce effective authority but cannot increase it.

- Delegation is not endorsement. Delegation changes authority;
  endorsement changes the integrity status of information. They must
  not be conflated in documentation or code.

- Visibility confinement is not declassification. Confinement keeps
  effects visible only to already-authorised observers; declassification
  explicitly permits selected release beyond confinement. They are
  separate mechanisms.

- Novelty claims involving monotonic authority reduction,
  provenance-based restriction, or source-sensitive context must be
  qualified against the classical IFC and integrity literature before
  assertion. See the [foundational security literature
  analysis](../../reports/analysis/2026-08-13-foundational-security-literature.md)
  and the [claim ledger](../evidence/CLAIMS.md).

- SLED-V properties should distinguish access safety from
  observational confidentiality and relational noninterference
  properties. The property hierarchy in the source analysis provides
  the reference structure.

- Candidate distinctions that may survive prior-art search include:
  retaining authenticated principal identities rather than only a
  generic trust label; deriving effective authority from the
  organisation's current ACS; parameterised argument-sensitive action
  authority; and verifying the security layer under arbitrary model
  proposals. These remain hypotheses until a targeted novelty search
  is complete.
