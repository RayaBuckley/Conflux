# Repository Context Brief for External AI Sessions

> **Non-authoritative export.** This document is a compressed summary of
> canonical repository sources for pasting into external AI tools (ChatGPT,
> Claude, etc.) at the start of a research or planning session. It must not be
> treated as normative. Always verify against the canonical owners linked below.
>
> **Last verified:** 2026-09-03

## Project summary

Conflux researches principal-aware security for AI agents. An agent may be
influenced by multiple Principals; permissions are derived from the current
Principal Context and provenance, not static prompt trust labels. The security
boundary (ITES) sits between the model and the tools: every proposed action is
checked against every influencing Principal's organisational permissions before
it may execute.

**Core equation:**

    Allow(a, PC) iff for every p in PC, ACS permits p to perform a

Effective authority is the intersection of all influencing Principals'
permissions. Additional influence can only reduce authority, never increase it.
The LLM itself is not trusted for security.

**Canonical:** [OVERVIEW.md](../OVERVIEW.md),
[RESEARCH_OVERVIEW.md](../research/RESEARCH_OVERVIEW.md)

## Threat model

Information supplied to an LLM may arbitrarily influence its subsequent
behaviour. The security mechanism must not depend on the model correctly
recognising malicious instructions. Prompt injection is one mechanism for
creating influence; it is not itself the security property.

ITES prevents authority amplification relative to the ACS. It does not
guarantee that authorised actions are safe, intended, or optimally
parameterised (authority guarantee, not complete safety guarantee).

**Trusted computing base:** correct provenance/influence tracking, correct ACS,
complete mediation of relevant effects, correct enforcement code.

## Non-negotiable invariants

- Preserve provenance and derive Principal Context from trusted influence.
- Evaluate Principal Context and every policy dimension at action time.
- Keep authorisation, read access, visibility, and consent independent.
- Consent and model output never manufacture authority.
- Deny unsupported delegation, unknown schemas, missing consent, policy
  errors, stale certificates, and unavailable effect boundaries.
- Keep alternative branches isolated and exploration side effect free.
- Keep benchmark behavior out of the domain and ITES kernel.
- Separate implemented behavior, bounded evidence, empirical results, and
  hypotheses in every claim.

**Canonical:** [AGENTS.md](../../AGENTS.md),
[AI_AGENT_GUIDE.md](../AI_AGENT_GUIDE.md)

## Repository map

| Path | Purpose |
|---|---|
| `src/conflux/domain` | Immutable security-domain values and action taxonomy |
| `src/conflux/execution` | Provenance-preserving transformations |
| `src/conflux/policy`, `application` | Policy decisions and composition |
| `src/conflux/ites` | Canonical security boundary and mediation |
| `src/conflux/adapters` | External policy, provider, and benchmark adapters |
| `src/conflux/evaluation` | SLED bounded verification and evaluation services |
| `src/conflux/planning` | Authenticated dynamic plans and bounded execution |
| `src/conflux/verification` | Serialisable formal subset and optional backends |
| `tests` | Offline unit, security, integration, and reproducibility tests |
| `docs` | Architecture, contracts, decisions, status, and workflows |
| `research/publications/manuscript` | Current LaTeX paper |
| `research/reports/analysis` | Current synthesis of immutable historical reports |
| `research/reports/archive` | Immutable historical evidence |

## Trust and authority order

1. Code, tests, schemas, and retained generated evidence (descriptive)
2. Accepted specifications and ADRs (normative)
3. Current architecture, security, status, and claim documents (maintained)
4. `research/reports/analysis/` (reconciled historical)
5. `research/reports/archive/` and `research/publications/paper/` (immutable)

If two levels disagree, that is a defect. Report and repair; do not choose
whichever source enables a task.

**Authority distinction:** descriptive (what happens) vs normative (what
should happen) vs scientific (what may be claimed). Passing tests do not
override a normative security specification. Prose does not override retained
evidence.

## Current implementation status (compressed)

- Offline security kernel mediates every agent effect through PC authority
  checks.
- Native SLED explores deterministic finite states and returns counterexamples.
- Verification IR with optional Z3 BMC and nuXmv adapter (returns UNKNOWN when
  unsupported).
- COI reduction, self-composition for observational confidentiality.
- Authenticated dynamic plans with certificate-bound execution.
- Scoped delegation modelled but runtime-disabled pending activation evidence.
- AgentDojo integration (pinned 0.1.35), Cedar adapter (4.12.0, preflight
  ready, live invocation blocked by schema compatibility).
- Comparative defence models: CaMeL, Progent, PACT, Dual-LLM (finite IR
  abstractions, not implementation conformance).
- 1210 tests, ruff + mypy + markdownlint + cspell clean.

**Canonical:** [STATUS.md](../evidence/STATUS.md),
[task-registry.json](../evidence/task-registry.json)

## Claim strength boundaries

**Implemented (code + tests):** empty context denial, external provenance
non-escalation, no-laundering closure, branch isolation, provenance is not read
ACL, argument authority, disclosure/visibility, attribution, delegation model
(runtime disabled), re-authorisation at execution time.

**Bounded evidence (finite retained run):** native SLED reproduction (5/5
seeded defects), COI reduction (2 fixtures), Z3 agreement (scaling to 16 noise
variables), self-composition (safe + unsafe fixtures), defence models (4
abstractions: each satisfies own property Q but native Q does not imply PE),
ITES PE property (bounded safe), Part B 1.46M trace reproduction.

**Not yet evidenced:** Cedar differential parity (binary not invoked),
unbounded safety (not claimed), self-hosted model cross-hardware
reproducibility (not claimed), cloud policy provider parity (not claimed).

**Canonical:** [CLAIMS.md](../evidence/CLAIMS.md)

## Current research questions

1. **RQ1 — Maximal permissiveness:** Is Principal Intersection the maximally
   permissive rule that prevents PE?
2. **RQ2 — Unbounded verification:** Can SLED-V prove the core PE invariant
   without the recursive depth bound?
3. **RQ3 — Comparative security objectives:** Which defences satisfy the Conflux
   PE property under a common formal semantics?
4. **RQ4 — State-space reductions:** Which reductions preserve properties and
   improve scalability?
5. **RQ5 — Provenance granularity and utility:** How much utility is recovered by
   finer provenance?

**Suggested thesis core:** RQ1, RQ2, RQ3 or RQ4, empirical support from
RQ5/AgentDojo.

**Canonical:** [RESEARCH_QUESTIONS.md](../research/RESEARCH_QUESTIONS.md)

## Validation pipeline

`python scripts/validate.py` runs: ruff (lint), mypy (strict types), pytest
(branch coverage, threshold 89%), yamllint, vulture, pip-audit, markdownlint,
cspell, schema validation (41 schemas), repository audit, wheel build + smoke.

**Quick commands:**

    python -m ruff check .          # lint
    python -m mypy . --no-error-summary  # type check
    python -m pytest tests -x -q    # run tests
    python scripts/audit_repository.py  # governance audit

## Commit discipline

- One commit per coherent concern; each commit must pass its own checks.
- Separate implementation, refactoring, documentation, and generated evidence.
- Always state `Security impact: <specific impact or "none">`.
- Run `python scripts/validate.py` before committing.
- For security-semantics changes, generate or update human-reviewable evidence.
