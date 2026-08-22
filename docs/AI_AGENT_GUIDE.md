# AI Agent Guide

This file is the operating contract for AI-assisted changes, including review
checklist, commit conventions, and documentation authority rules.

## Trust and authority order

1. Code, tests, schemas, and retained generated evidence describe what is
   executable and observed.
2. Accepted specifications and ADRs describe intended behavior and rationale.
3. Current architecture, security, operation, status, and claim documents
   explain the maintained system.
4. `reports/analysis/` reconciles historical recommendations.
5. `reports/archive/` and `publications/paper/` are immutable historical evidence.

If two levels disagree, treat that as a defect. Report the discrepancy and
repair the appropriate owner; do not choose whichever source enables a task.

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

## Change procedure

1. Confirm `main`, a clean worktree, and the affected canonical owners.
2. Read the relevant specification, ADR, implementation, tests, and status.
3. Write a decision-complete specification before foundational behavior.
4. Formulate a commit strategy: when changes span multiple files or logical
   concerns, group them into atomic commits — one per distinct concern — and
   list the files for each commit. Each commit must pass validation
   independently.
5. Implement the smallest coherent change with security regression tests.
6. Run focused checks, repository audit, portable validation, and diff review.
7. Update the existing status, claim, glossary, and manuscript owners only
   where the change alters them.
8. Commit atomically. Keep generated evidence in a later commit.

### Rationale

Bounded context and one-way ownership prevent an agent from progressively
inventing new abstractions, summaries, or guarantees. The sequence forces
intent, implementation, executable evidence, and prose to converge.

## Documentation routing

| New information | Update |
|---|---|
| Normative feature behavior | specification and relevant ADR |
| Package or data-flow change | `reference/ARCHITECTURE.md` and `reference/REFERENCE.md` |
| Security rule or assumption | `reference/SECURITY_MODEL.md` and `SECURITY.md` |
| Test or validation workflow | `DEVELOPMENT.md` and `evidence/AUDIT.md` |
| Programme disposition | `task-registry.json`, summarized in `evidence/STATUS.md` |
| Claim strength or limitation | `evidence/CLAIMS.md` |
| Historical-report interpretation | `reports/analysis/` |
| Publication claim | current `publications/manuscript/`, backed by retained evidence |

Do not create a parallel roadmap, status page, glossary, task list, or claim
ledger. Link instead of copying details.

## Stop conditions

Stop and request direction if a change would broaden authority, weaken a fail-
closed default, edit archived evidence, require a secret or external side
effect not already in scope, or turn missing external evidence into a claim.
Unavailable optional tools are expected and must remain explicit.

## Review checklist

Use this checklist when reviewing a diff:

- [ ] Architecture, package guidance, and relevant ADRs inspected.
- [ ] Specification or decision record updated where needed.
- [ ] Rationale and material rejected alternatives recorded.
- [ ] Principal Context and provenance impact assessed.
- [ ] Security cases tested: allow, deny, mixed-context, failure, immutability.
- [ ] Appropriate tests added (unit, integration, adapter, reproducibility).
- [ ] `python scripts/audit_repository.py` passes.
- [ ] `python scripts/validate.py` passes.
- [ ] Existing canonical owner updated, no competing source created.
- [ ] Terminology and paper notes synchronised if architecture changed.
- [ ] Diff reviewed for hidden trust assumptions, benchmark shortcuts,
      and permission broadening.

## Commit message convention

Each commit should follow:

```text
<one-line summary>

Security impact: <brief statement or "none">

<optional rationale or detail>
```

This makes the security relevance of every change visible during diff
review without requiring a separate PR or form.

## Documentation authority

- Update an existing canonical owner before creating a new document.
- Explain why a decision exists and link to its ADR or specification.
- Put mutable task state only in `docs/evidence/task-registry.json` and claim
  strength only in `docs/evidence/CLAIMS.md`.
- Do not edit archived paper or report evidence. Add current interpretation
  outside the archive.
- Do not enter numerical claims without retained, reproducible evidence.

Use one commit per coherent change. Do not combine generated evidence with the
implementation that produces it. Review the staged diff for permission
broadening, hidden trust assumptions, benchmark shortcuts, secrets, and stale
documentation before committing.
