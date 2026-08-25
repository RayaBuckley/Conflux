# AI Agent Guide

This file is the operating contract for AI-assisted changes, including review
checklist, commit conventions, and documentation authority rules.

## Trust and authority order

1. Code, tests, schemas, and retained generated evidence describe what is
   executable and observed.
2. Accepted specifications and ADRs describe intended behavior and rationale.
3. Current architecture, security, operation, status, and claim documents
   explain the maintained system.
4. `research/reports/analysis/` reconciles historical recommendations.
5. `research/reports/archive/` and `research/publications/paper/` are immutable historical evidence.

If two levels disagree, treat that as a defect. Report the discrepancy and
repair the appropriate owner; do not choose whichever source enables a task.

## Authority distinction

Distinguish three kinds of authority when making decisions:

- **Descriptive authority** (what currently happens): retained runtime and
  generated evidence; executable code, tests, and schemas; maintained
  descriptive documentation.
- **Normative authority** (what should happen): accepted specifications,
  ADRs, and the security model. Implementation and tests should conform to
  it.
- **Scientific authority** (what may be claimed): retained reproducible
  evidence plus explicit assumptions; the claim ledger; manuscript prose.

A disagreement between these layers is a defect to investigate. Passing tests
do not override a normative security specification. Prose does not override
retained evidence.

## Finding classification

Each review finding should be classified as one of:

- `confirmed_defect`: reproducible evidence demonstrates a discrepancy.
- `research_gap`: a justified missing experiment, comparison, proof, or
  literature area.
- `design_hypothesis`: plausible improvement without sufficient evidence yet.
- `documentation_drift`: canonical sources disagree.
- `cleanup`: non-semantic maintainability improvement.
- `rejected`: falsification or review indicates no change is justified.

Speculative findings cannot silently become confirmed defects. A finding
that cannot be deterministically falsified may still proceed as a research or
design hypothesis, but must be labelled accordingly.

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

The development process follows a staged, evidence-oriented workflow:

```
Discover -> Falsify -> Research -> Specify -> Human gate
-> Implement -> Verify -> Adversarial review -> Human gate
-> Commit/evidence -> Claims/literature synchronisation
```

1. **Discover** (Scout): read-only inspection of the repository, evidence,
   documentation, and external literature. Return structured findings with
   proposed falsification routes. Do not implement.
2. **Falsify** (Skeptic): try to make each finding disappear. Inspect
   authoritative sources, look for existing tests/specs that resolve it,
   construct minimal reproducers, distinguish actual semantic failure from
   documentation ambiguity. Downgrade unsupported findings.
3. **Research** (Researcher): activate when a finding affects novelty,
   threat model, security semantics, evaluation methodology, formal methods,
   or comparison. Search adversarially — assume the contribution is not
   novel and look for the strongest prior work.
4. **Specify**: write a decision-complete specification before foundational
   behavior. Confirm `main`, a clean worktree, and the affected canonical
   owners.
5. **Human gate**: human approval is required before accepting a new or
   changed security invariant, broadening authority, weakening fail-closed
   behaviour, activating delegation, changing threat-model assumptions,
   changing a publication novelty claim, or introducing a substantial new
   abstraction solely from an AI review.
6. **Implement**: implement the smallest coherent change with security
   regression tests. Stop and return to specification if implementation
   exposes a contradiction with the spec.
7. **Verify**: run focused checks, repository audit, portable validation, and
   diff review.
8. **Adversarial review** (Auditor): use a fresh context. Receive the
   specification, final diff, tests, and validation output. Try to reject
   the change. Check for authority broadening, provenance loss, fail-closed
   weakening, benchmark leakage, stronger undocumented assumptions, and
   stale documentation or claims.
9. **Human gate**: review the auditor's findings before proceeding.
10. **Commit/evidence**: commit atomically. Keep generated evidence in a
    later commit after the generator implementation exists.
11. **Claims/literature synchronisation**: update existing status, claim,
    glossary, and manuscript owners only where the change alters them.

### Rationale

Bounded context and one-way ownership prevent an agent from progressively
inventing new abstractions, summaries, or guarantees. The sequence forces
intent, implementation, executable evidence, and prose to converge.

## Documentation routing

| New information | Update |
|---|---|
| Normative feature behavior | specification and relevant ADR |
| Package or data-flow change | `reference/ARCHITECTURE.md` and `reference/REFERENCE.md` |
| Security rule or assumption | `reference/SECURITY_MODEL.md` |
| Test or validation workflow | `DEVELOPMENT.md` and `evidence/AUDIT.md` |
| Programme disposition | `task-registry.json`, summarized in `evidence/STATUS.md` |
| Claim strength or limitation | `evidence/CLAIMS.md` |
| Historical-report interpretation | `research/reports/analysis/` |
| Publication claim | current `research/publications/manuscript/`, backed by retained evidence |

Do not create a parallel roadmap, status page, glossary, task list, or claim
ledger. Link instead of copying details.

## Examiner mode

The examiner workflow helps a human or AI reviewer understand an
unfamiliar part of the codebase before making changes.  It is a
learning procedure, not a code-change step.

### Learning packet

To build a learning packet for a target area:

1. Identify the canonical specification, ADR, or security-model
   section that governs the area.
2. Identify the implementation entry point and key data structures.
3. Identify the tests that exercise the security-relevant behaviour.
4. Identify the evidence (SLED traces, verification results, audit
   output) that demonstrates the behaviour.
5. Summarise: what invariant does this area enforce, how is it
   tested, and what evidence exists for it?

### Examiner prompt template

```
You are examining the <area> subsystem of Conflux.

Read these files in order:
1. <specification or ADR>
2. <implementation entry point>
3. <key test file>
4. <evidence or audit output>

Answer:
- What invariant does this area enforce?
- How is the invariant tested?
- What evidence exists for it?
- What assumptions does it depend on?
- What would break if the invariant were violated?
```

### Examiner constraints

- Do not implement changes during examination.
- Do not modify evidence or tests during examination.
- Report findings as structured findings (see Finding classification).
- If a finding affects a security invariant, mark it
  `confirmed_defect` or `design_hypothesis` as appropriate.

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
