# AI Agent Guide

This file is the compact operating contract for AI-assisted changes. Human
contributors should start with [CONTRIBUTING.md](../CONTRIBUTING.md).

## Trust and authority order

1. Code, tests, schemas, and retained generated evidence describe what is
   executable and observed.
2. Accepted specifications and ADRs describe intended behavior and rationale.
3. Current architecture, security, operation, status, and claim documents
   explain the maintained system.
4. `reports/analysis/` reconciles historical recommendations.
5. `reports/archive/` and `paper/` are immutable historical evidence.

If two levels disagree, treat that as a defect. Report the discrepancy and
repair the appropriate owner; do not choose whichever source enables a task.

## Non-negotiable invariants

- Preserve provenance and derive Principal Context from trusted influence.
- Evaluate Principal Context and every policy dimension at action time.
- Keep authorisation, read access, visibility, and consent independent.
- Consent and model output never manufacture authority.
- Deny unsupported delegation, unknown schemas, missing consent, policy
  errors, stale certificates, and unavailable effect boundaries.
- Keep alternative branches isolated and exploration side-effect free.
- Keep benchmark behavior out of the domain and ITES kernel.
- Separate implemented behavior, bounded evidence, empirical results, and
  hypotheses in every claim.

## Change procedure

1. Confirm `main`, a clean worktree, and the affected canonical owners.
2. Read the relevant specification, ADR, implementation, tests, and status.
3. Write a decision-complete specification before foundational behavior.
4. Implement the smallest coherent change with security regression tests.
5. Run focused checks, repository audit, portable validation, and diff review.
6. Update the existing status, claim, glossary, and manuscript owners only
   where the change alters them.
7. Commit atomically. Keep generated evidence in a later commit.

### Rationale

Bounded context and one-way ownership prevent an agent from progressively
inventing new abstractions, summaries, or guarantees. The sequence forces
intent, implementation, executable evidence, and prose to converge.

## Documentation routing

| New information | Update |
|---|---|
| Normative feature behavior | specification and relevant ADR |
| Package or data-flow change | `ARCHITECTURE.md` and `REFERENCE.md` |
| Security rule or assumption | `SECURITY_MODEL.md` and `SECURITY.md` |
| Test or validation workflow | `DEVELOPMENT.md` and `AUDIT.md` |
| Programme disposition | `task-registry.json`, summarized in `STATUS.md` |
| Claim strength or limitation | `CLAIMS.md` |
| Historical-report interpretation | `reports/analysis/` |
| Publication claim | current `manuscript/`, backed by retained evidence |

Do not create a parallel roadmap, status page, glossary, task list, or claim
ledger. Link instead of copying details.

## Stop conditions

Stop and request direction if a change would broaden authority, weaken a fail-
closed default, edit archived evidence, require a secret or external side
effect not already in scope, or turn missing external evidence into a claim.
Unavailable optional tools are expected and must remain explicit.
