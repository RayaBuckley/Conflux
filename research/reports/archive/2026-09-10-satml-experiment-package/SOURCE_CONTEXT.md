# Source Context and Research Rationale

This package is grounded in two bodies of evidence: the historical Conflux paper/report supplied by the project owner and the current public repository state inspected on 2026-09-10.

## Historical project evidence

The earlier preprint framed ITES as provenance-based authority confinement and SLED as bounded worst-case state-space exploration. It reported approximately 1.46 million explored execution traces across three environments, with depth-three bounds and incomplete traces excluded. The earlier Part B report explains the combinatorial limitations directly: depth four exceeded tens of millions of traces and the evaluation therefore used depth three.

Those historical materials establish why the new experiment should not merely run a larger trace count. The stronger research question is how the current state-based and solver-backed SLED-V architecture changes scalability, diagnostic quality, and verification confidence.

## Current repository evidence inspected 2026-09-10

Current public repository documentation states that:

- Conflux now has one fail-closed ITES mediation kernel and canonical Principal Context semantics.
- Native SLED explores deterministic finite states and emits shortest counterexamples.
- The verification package includes a serialisable IR, reference interpreter, optional Z3 bounded checking, nuXmv adapter, and COI reduction.
- Historical Part B trace counts have been reproduced exactly: 422,535 + 996,451 + 43,621 = 1,462,607.
- That reproduction compresses to 31 unique canonical states.
- Current retained security mutation evidence includes five historical monitor defects plus seven delegation mutants.
- Z3/reference/COI verdict agreement exists on retained finite fixtures and COI scaling through 16 irrelevant variables.
- AgentDojo 0.1.35 / benchmark v1.2.2 integration runs end-to-end, but existing small-model evidence is diagnostic rather than an efficacy result.
- Planning comparisons run end-to-end; Qwen2.5-7B has encouraging but small pilot evidence.
- Cedar 4.12.0 differential evaluation is preflight-ready but has not yet established live parity.
- Observational confidentiality has finite self-composition/Z3 evidence but is not claimed as a general noninterference proof.

Canonical repository sources to re-read before implementation:

- `AGENTS.md`
- `docs/evidence/CLAIMS.md`
- `docs/evidence/STATUS.md`
- `docs/reference/SECURITY_MODEL.md`
- `docs/reference/SLED.md`
- `research/experiments/README.md`

## Why the package prioritises these experiments

The fastest high-value evidence comes from deterministic infrastructure that already exists:

1. Scaling can extend the current historical reproduction, COI scaling, and Z3-agreement machinery.
2. Mutation testing can extend existing bounded security mutants without requiring external models.
3. Provenance precision can use canonical ITES and deterministic ACS fixtures.
4. AgentDojo can then use the already-pinned integration once a competent model/task subset is selected.
5. Planning, Cedar, and confidentiality are useful secondary experiments but should not delay the first four.

## Scientific discipline

The package deliberately preserves current repository claim boundaries. Bounded model checking and finite exhaustive exploration do not establish unbounded deployment security. Authenticated provenance remains part of the trusted computing base. Real-model benchmarks measure empirical behaviour under selected tasks/models/attacks rather than universal security. Candidate formal abstractions of competing defences are not treated as faithful implementations unless separately validated.
