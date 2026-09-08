# Conflux semantic reframing — coder package

**Date:** 2026-09-07  
**Target repository:** `https://github.com/RayaBuckley/Conflux`  
**Target branch:** current `main` at implementation time  
**Purpose:** perform a large-scale, internally consistent documentation/semantics correction. This is primarily a semantics and documentation migration, not a request to activate new runtime authority.

## Executive instruction

The repository currently presents Conflux/ITES mainly as a system-level alternative to model-level prompt-injection defence. That framing must be revised.

The new canonical story is:

> Conflux separates **authority confinement** from **semantic judgement**. Principal Context plus the applicable machine-enforceable authority policy gives a deterministic boundary on what an execution may do. This does not guarantee that every choice inside that boundary is appropriate. Humans already make semantic security decisions over untrusted inputs in real organisations, and AI agents can also be used as semantic decision-makers. Model-level defences therefore provide genuine security value, but with empirical/probabilistic assurance rather than the hard guarantee provided by Conflux's authority-confinement layer. Where possible, organisations should encode restrictions structurally; where semantic judgement is genuinely required, the residual risk must be accepted, mitigated by humans/model-level defences, or the workflow must be disallowed.

Delegation is the explicit mechanism for changing the authority available to a particular execution. It must be **explicitly authorised by a principal**, scoped, and machine-enforceable. Planning may represent/extract an explicit delegation and constrain it to a precise choice set, but planning does not itself create authority merely because more authority would help the task.

The project must distinguish:

- `ACS_explicit`: the organisation's persistent machine-readable access-control relation / PDP state;
- `D_e`: explicit valid delegation(s) applicable to execution `e`;
- `ACS_effective(e)`: the authority relation actually used by ITES for execution `e`, combining `ACS_explicit` with applicable explicit delegation;
- `PC(e)`: conservative Principal Context;
- semantic judgement: a human/model decision about whether an action inside an available authority envelope is appropriate.

The hard ITES condition after delegation is conceptually:

```text
Execute_e(a) => PC(e) != empty
                and forall p in PC(e): ACS_effective(e, p, a)
```

with argument/resource/time constraints included by the real operation schema and policy ports.

## User-confirmed decisions that are NOT optional

1. Model-level defences are genuine security mechanisms, not merely utility mechanisms. Their assurance is empirical/probabilistic rather than a worst-case system-level guarantee.
2. Humans and AI agents may both serve as semantic decision-makers. Human judgement is not a formal guarantee either; phishing/security training is a useful analogy.
3. Real organisational policy is often richer than the explicit machine-readable ACS. Humans routinely resolve semantic predicates the ACS does not encode.
4. Keep the formal ITES theorem relative to its stated machine-enforceable policy/ACS assumptions. Do not silently redefine the theorem around an unknowable "true policy".
5. Model/classifier judgements must **not** remove provenance, narrow Principal Context, or bypass the hard authority boundary.
6. `ACS_explicit` and `ACS_effective(e)` are distinct. The latter includes valid explicit scoped delegation for that execution.
7. Delegation is explicit authority transfer. Planning does not grant authority merely because a plan needs it.
8. Planning may parse/represent explicit user delegation and derive a precise delegated choice set; if extraction cannot be trusted, require explicit human verification/confirmation of that scope.
9. The useful delegation primitive is a constrained action/effect choice set, not broad role transfer where avoidable.
10. Ephemeral agents are an application/advantage of scoped delegation, not the central formal novelty.
11. When strict authority confinement makes a task impossible, the organisation's remaining choices are to use explicit delegation where actually intended, rely on a trusted semantic decision-maker (human and/or defended AI) for the residual semantic risk, or disallow the workflow. Do not invent endorsement as another mechanism.
12. **Remove endorsement from Conflux's intended mechanism set.** Classical literature may still mention endorsement as prior-art terminology when needed, but the repo must not present endorsement/trusted endorsement as a planned Conflux solution.
13. Conflux guarantees confinement to the represented authority envelope; it does not guarantee correctness/appropriateness of choices inside that envelope.
14. SLED/SLED-V remains focused on system-level properties. Do not turn it into a model-level PI benchmark. Existing empirical agent/model benchmarks are the appropriate place to measure model-level resistance and semantic decision quality.
15. Current archived reports and archived Part B/paper materials are historical evidence and must not be rewritten.

## Work order

Read these package files in order:

1. `01_CANONICAL_SEMANTICS.md`
2. `02_CURRENT_REPO_AUDIT.md`
3. `03_FILE_BY_FILE_MIGRATION.md`
4. `04_DELEGATION_AND_PLANNING.md`
5. `05_MODEL_SECURITY_AND_HUMAN_ANALOGY.md`
6. `06_EVALUATION_CLAIMS_AND_PUBLICATIONS.md`
7. `07_SEARCH_AND_DRIFT_AUDIT.md`
8. `08_ACCEPTANCE_CHECKLIST.md`
9. `coder_task_manifest.json`
10. `drafts/025-authority-confinement-semantic-judgement-delegation.md`

## Non-goals

- Do **not** activate runtime delegation in this documentation task.
- Do **not** make model-level classifiers part of the trusted authority boundary.
- Do **not** remove conservative provenance because a model says an input is benign.
- Do **not** add endorsement/trusted transformation as a newly recommended solution.
- Do **not** claim the explicit ACS perfectly captures organisational intent.
- Do **not** weaken or broaden the maximal-permissiveness theorem beyond its stated PE definition and authority model.
- Do **not** edit immutable historical report archives or archived Part B/paper sources.
- Do **not** turn SLED-V into an empirical model-security evaluator.

## Repository re-audit requirement

This package was prepared from the public `main` snapshot visible on 2026-09-07. Before editing, re-run the search programme in `07_SEARCH_AND_DRIFT_AUDIT.md` against the actual checkout. The repository changes frequently; the local checkout is authoritative for exact file names and current wording.
