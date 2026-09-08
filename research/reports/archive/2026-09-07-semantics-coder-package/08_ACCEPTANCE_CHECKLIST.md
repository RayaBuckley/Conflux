# Acceptance checklist

The migration is complete only when every item below is satisfied.

## Semantic correctness

- [ ] ADR-025 (or next available number) exists and is accepted/canonical.
- [ ] `ACS_explicit` is clearly defined as persistent machine-readable authority.
- [ ] `ACS_effective(e)` is clearly defined as explicit authority plus valid scoped delegation applicable to execution `e`.
- [ ] `PC(e)` remains conservative and is not narrowed by model/classifier judgement.
- [ ] Delegation is explicit, independently authorised, scoped, and never described as provenance removal.
- [ ] Planning is not an authority source.
- [ ] Planning may represent/extract an explicit user delegation but may not infer a grant merely because a task needs it.
- [ ] Authority envelope is defined and the core guarantee is confinement to it.
- [ ] Semantic appropriateness inside the envelope is explicitly outside the hard ITES guarantee.
- [ ] Model-level defences are explicitly recognised as genuine empirical/probabilistic security controls.
- [ ] Human judgement is used as an analogy for semantic policy resolution without claiming humans are guaranteed secure.
- [ ] Machine-readable ACS is not described as necessarily encoding the whole intended organisational policy.
- [ ] Endorsement/trusted endorsement is not a planned Conflux mechanism.
- [ ] Classical endorsement references, if retained, are clearly literature-only.

## Claim discipline

- [ ] Maximal-permissiveness theorem remains scoped to the Conflux PE definition and fixed represented authority relation.
- [ ] No text implies ITES guarantees all authorised actions are harmless or intended.
- [ ] No text implies "no formal guarantee" means "no security benefit".
- [ ] No text says a fully compromised model yields complete security without specifying authority-confinement property.
- [ ] No runtime delegation claim has been promoted accidentally.
- [ ] Existing bounded/unbounded SLED claim distinctions remain intact.

## Evaluation discipline

- [ ] SLED/SLED-V remains a system-level verifier/evaluator.
- [ ] Model PI resistance/semantic correctness is labelled empirical and assigned to real-model/agent benchmarks.
- [ ] Utility remains separate from both authority confinement and model-level security.

## Repository consistency

- [ ] `README.md`, `docs/OVERVIEW.md`, `SECURITY_MODEL.md`, `GLOSSARY.md`, research overview, related work, research questions, planning specs, status and claims all agree.
- [ ] Current manuscript has been searched for stale framing.
- [ ] Active FLMSec source has been searched if editable/current.
- [ ] Historical archives were not modified.
- [ ] ADR-024's endorsement/trusted-transformation direction is explicitly superseded/reconciled rather than silently erased.
- [ ] Documentation navigation/ADR index links to the new decision.
- [ ] Task registry/change catalogue records the migration without claiming new runtime functionality.

## Mechanical validation

- [ ] `git diff --check` passes.
- [ ] repository validation command passes.
- [ ] markdown/link/audit checks pass.
- [ ] JSON/task registry/schema checks pass if touched.
- [ ] repository-wide post-edit grep completed and all risky hits classified.
- [ ] no unrelated evidence/output regeneration was committed.

## Final coder report

The coder must finish with a short report containing:

1. files changed;
2. canonical semantic decisions implemented;
3. stale statements intentionally left untouched because they are historical/literature sources;
4. any implementation behavior discovered that conflicts with the new docs;
5. validation commands and outcomes;
6. remaining semantic ambiguities — do not guess them.
