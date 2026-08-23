# Current Research Questions

> Draft prioritisation document. These questions should be reconciled with the current repository status and claims ledger.
>
> **Canonical owners:** Implementation status is in [task-registry.json](../evidence/task-registry.json); claim strength in [CLAIMS.md](../evidence/CLAIMS.md); change catalogue in [CHANGE_CATALOG.md](../evidence/CHANGE_CATALOG.md).

## Primary questions

### RQ1 — Maximal permissiveness

Is Principal Intersection the maximally permissive action-authorisation/controller rule that prevents privilege escalation under the stated ACS, provenance and arbitrary-LLM threat model?

Desired evidence:

- a general theorem;
- a formal transition-system statement;
- controller synthesis on finite instances that reconstructs the ITES rule.

### RQ2 — Unbounded verification

Can SLED-V prove the core ITES PE invariant without the recursive depth bound used by the original SLED experiments?

Desired evidence:

- explicit assumptions and supported fragment;
- unbounded `SAFE` result where possible;
- inductive invariant/proof artefact;
- negative controls producing counterexamples.

### RQ3 — Comparative security objectives

Which contemporary system-level defences satisfy the Conflux PE property when faithfully represented under a common formal semantics?

Desired evidence:

- defence-specific semantic adapters/models;
- verification of each defence's own intended property where feasible;
- shortest PE counterexamples where the Conflux property does not hold;
- careful distinction between "violates Conflux PE" and "breaks the defence's published guarantee".

### RQ4 — State-space reductions

Which reductions preserve the relevant Conflux properties and materially improve verification scalability?

Candidates:

- canonical-state memoisation;
- cone-of-influence;
- policy-equivalent principal/resource symmetry;
- partial-order reduction;
- authority-aware subsumption/antichains.

Each optimisation needs a preservation argument and an ablation.

### RQ5 — Provenance granularity and utility

How much utility is recovered by finer provenance while retaining the same ACS-derived PE invariant?

Compare:

- execution-level Principal Context;
- action-level Principal Context;
- argument-level Principal Context;
- visibility-aware argument-level provenance.

## Secondary questions

### RQ6 — Delegation

Which explicit delegation semantics preserve a clear security theorem while recovering legitimate workflows?

### RQ7 — Confidentiality

Can Conflux verify observational confidentiality/noninterference in addition to authorised-read safety?

### RQ8 — Planning

Can secure controller synthesis or verified planning complete more tasks while minimising authority exposure and unnecessary observations?

### RQ9 — Implementation conformance

How can executable Conflux and external-defence implementations be shown to refine or conform to their verified models?

## Scope discipline

A strong Part C need not answer all questions.

Suggested thesis core:

- RQ1;
- RQ2;
- RQ3 or RQ4;
- empirical support from RQ5/AgentDojo.

Delegation, consent, planning and production integration should remain supporting directions unless results justify promoting them.
