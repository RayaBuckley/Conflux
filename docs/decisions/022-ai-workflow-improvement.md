# Specification 022: AI-Assisted Development Workflow Improvement

Type: specification
Status: accepted for implementation
Evidence date: 2026-08-24

## Goal and success criteria

Make the development process itself follow the same evidence-oriented
philosophy as the security research: use AI aggressively for discovery,
research, design exploration, implementation, and adversarial review; use
deterministic evidence wherever a reliable oracle exists; reserve human
judgement for research significance, normative decisions, assumptions, and
ambiguous trade-offs.

Success requires `AGENTS.md` to expose concise atomic commit guidance, the
staged workflow to be documented in `docs/AI_AGENT_GUIDE.md`, speculative
findings to be unable to silently become confirmed defects, and non-trivial
changes to carry a lightweight impact/commit plan.

## Authority distinction

**Descriptive authority** (what currently happens): retained runtime/generated
evidence; executable code, tests, and schemas; maintained descriptive
documentation.

**Normative authority** (what should happen): accepted specification/ADR/
security model; implementation and tests should conform to it.

**Scientific authority** (what may be claimed): retained reproducible evidence
plus explicit assumptions; claim ledger; manuscript prose.

A disagreement between these layers is a defect to investigate. Passing tests
do not override a normative security specification. Prose does not override
retained evidence.

## Staged workflow

```
Discover -> Falsify -> Research -> Specify -> Human gate
-> Implement -> Verify -> Adversarial review -> Human gate
-> Commit/evidence -> Claims/literature synchronisation
```

AI roles are logical stages, not a multi-agent framework. Fresh
contexts/prompts are sufficient.

- **Scout**: read-only discovery. Returns structured findings with proposed
  falsification routes. Does not implement.
- **Skeptic**: tries to make each finding disappear. Favours precision over
  recall.
- **Researcher**: activates when a finding affects novelty, threat model,
  security semantics, evaluation, formal methods, or comparison. Searches
  adversarially.
- **Implementer**: receives decision-complete specification. Implements the
  smallest coherent change. Stops if implementation exposes a contradiction.
- **Auditor**: fresh context. Receives specification, diff, tests, and
  validation output. Tries to reject the change.

## Finding classification

Each review finding is classified as one of: `confirmed_defect`,
`research_gap`, `design_hypothesis`, `documentation_drift`, `cleanup`,
`rejected`. Speculative findings cannot silently become confirmed defects.

## Human gates

Human approval is required before: accepting a new/changed security
invariant; broadening authority; weakening fail-closed behaviour; activating
delegation; changing threat-model assumptions; changing a publication novelty
claim; interpreting ambiguous literature as establishing novelty; accepting a
benchmark metric as measuring a security guarantee; or introducing a
substantial new abstraction solely from an AI review.

## Commit discipline

`AGENTS.md` receives concise high-salience commit rules visible to coding
agents without following a link. `docs/AI_AGENT_GUIDE.md` remains the
detailed owner.

Key rules:

- One commit = one coherent concern, independently revertible.
- Each implementation commit passes validation independently.
- Separate semantic implementation, refactoring, documentation, and
  generated evidence. Do not commit generated evidence with the generator.
- `Security impact: <specific or "none">` is mandatory in every commit
  message.
- Review staged diff for authority broadening, provenance loss, benchmark
  shortcuts, secrets, and stale documentation.
- Run `python scripts/validate.py` before commit; report unavailable checks.

## Change-impact manifest

For non-trivial accepted work, require a compact impact declaration before
implementation: task, research question affected, security invariants
affected, canonical source files, expected implementation files, expected
tests, expected evidence, claims potentially affected, literature potentially
affected, threat-model assumptions affected, explicit non-changes, and commit
plan.

Audit rules are added only where the relationship is objective and stable.

## Negative-control programme

Expand existing mutation testing. Each retained mutant must correspond to a
meaningful threat-model or implementation mistake, not merely increase a
mutation score. Candidate defect families include requester-only authority,
permission union, lost nested provenance, consent as authority, author set as
reader ACL, stale certificate, sibling branch leakage, expired delegation,
delegation reuse, revocation ignored, sensitive value in error, plan
executable after revocation, and benchmark oracle leak.

## Literature corpus

Replace episodic prose-only literature searches with a living, auditable
machine-readable corpus. The corpus supports deduplication, primary-source
verification, search provenance, classification, claim-to-paper
relationships, forward/backward snowballing status, and manuscript citation
checks.

Deterministic checks validate process facts (citation resolution, primary-
source records, duplicate DOI rejection, required fields, last-checked
dates). No checker asserts that a contribution is novel.

## Expected file set and change budget

- `AGENTS.md` (commit discipline section)
- `docs/AI_AGENT_GUIDE.md` (staged workflow, authority distinction, finding
  classification)
- `docs/templates/REVIEW_FINDING.md`
- `docs/templates/CHANGE_IMPACT_MANIFEST.md`
- `schemas/review-finding.schema.json`
- `schemas/change-impact-manifest.schema.json`
- `scripts/audit_repository.py` (new audit rules)
- `tests/semantics/mutants.py` (expanded negative controls)
- `schemas/literature-corpus.schema.json` (Phase 4)

No new `WORKFLOW.md`. The historical `WORKFLOW.md` was intentionally folded
into `AGENTS.md` at commit `f1e7220`. All workflow guidance lives in
`AGENTS.md` and `docs/AI_AGENT_GUIDE.md`.

## Security impact

The workflow change does not alter security semantics, authorisation,
visibility, consent, delegation, provenance, or Principal Context evaluation.
It adds process discipline and deterministic checks that prevent speculative
AI suggestions from becoming repository facts without evidence.

## Assumptions

- The existing validation pipeline (`python scripts/validate.py`) remains the
  pre-commit barrier.
- Existing canonical owners (task registry, claim ledger, status page) remain
  authoritative; no parallel trackers are created.
- The AI roles are logical stages executed in fresh contexts, not a
  multi-agent orchestration framework.
- Literature novelty conclusions remain human-reviewed.
