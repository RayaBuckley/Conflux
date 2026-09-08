# Current repository audit and semantic drift map

Audit basis: public `main` viewed 2026-09-07. The repo was at 405 commits in the web snapshot. Re-check every path against the actual local checkout before editing.

## High-priority drift already visible

### `docs/OVERVIEW.md`

Current problem wording says, in substance, that the core question is not whether the model can detect malicious instructions but whether the mechanism is safe even if the model is fully compromised.

Problem: this reads as if model-level defences are not security mechanisms. Keep the worst-case ITES property but add the complementary empirical-security layer and human analogy.

Required rewrite:

- Explain that model-level defences can materially reduce attacks, analogous to training employees to identify phishing/social engineering.
- State that the ITES guarantee deliberately does not depend on this empirical reliability.
- Explain that some workflows require semantic judgement over untrusted content and therefore cannot get the same worst-case "appropriate choice" guarantee.
- Keep the simple Principal Context explanation.

### `docs/reference/SECURITY_MODEL.md`

Strengths to preserve:

- Models/planners/classifiers cannot grant authority, assert trusted provenance, or narrow PC.
- independent policy dimensions;
- action/argument authorisation;
- authority-vs-harm distinction;
- no-laundering and external-source provenance rules.

Required corrections/extensions:

1. Replace/qualify "The LLM itself is not trusted for security" style wording. More precise: the LLM is not trusted to establish/expand authority or narrow PC; deployments may still rely on it probabilistically for semantic judgement inside the allowed envelope.
2. Add `ACS_explicit`, `D_e`, `ACS_effective(e)`, and `AuthorityEnvelope(e)` definitions.
3. Reframe "policy adequacy" to explain that real organisational policy often contains semantic predicates resolved by humans/models and not encoded in the explicit ACS.
4. Add human/AI semantic-decision boundary.
5. Keep delegation runtime-disabled status, but define intended authority semantics cleanly.
6. Remove endorsement/trusted-transformation as a current planned mechanism. Current line allowing an "explicitly trusted, separately modelled transformation" to reduce influence should either be made a generic future exception requiring a new ADR or replaced by a simple current rule that ordinary execution cannot reduce PC.
7. Add a misconception row: "No formal guarantee means no security value" -> model-level/human mitigations can reduce risk empirically, while ITES provides a different assurance class.
8. Add a misconception row: "If ITES blocks a task, the ACS must be wrong" -> some tasks depend on semantic judgement not represented in the machine-readable policy.

### `docs/research/RESEARCH_OVERVIEW.md`

Visible drift:

- says LLM is not trusted for security;
- presents utility as the main empirical axis while security invariant is ACS-derived PE prevention;
- delegation is modeled as explicit ACS state mutation;
- research lineage includes endorsement/trusted transformation as an intended direction.

Required changes:

- Distinguish "not trusted for hard authority" from "may be relied upon for probabilistic semantic security".
- Add a section on coarse machine policy vs intended organisational policy.
- Replace the simple `ACS_t -> ACS_(t+1)` delegation presentation with explicit vs execution-effective policy, unless a persistent delegation really mutates global ACS.
- State that a scoped execution delegation may be ephemeral without globally mutating the persistent ACS.
- Reframe planning research around confining/minimising already explicit delegation and unnecessary authority exposure, not manufacturing authority.
- Remove endorsement as a proposed Conflux direction.
- Keep endorsement only in literature lineage if historically useful, clearly non-normative.

### `docs/research/RELATED_WORK.md`

Current related-work text correctly distinguishes authority from harm and places Conflux in classical IFC/integrity lineage. It currently gives endorsement/trusted transformations a direct future-Conflux role.

Required:

- Retain endorsement as a classical IFC concept only if useful for scholarly completeness.
- Remove statements that make endorsement/trusted transformation a planned Conflux solution.
- Add model-level defences as complementary probabilistic security rather than merely a contrast class with no guarantees.
- Use the human phishing/security-training analogy carefully as project framing, not as a literature claim unless sourced.
- Update CaMeL comparison to emphasise the exact delegation/planning distinction: Conflux planner output is not itself an authority source; explicit principal delegation is required.

### `docs/research/RESEARCH_QUESTIONS.md`

Current secondary RQ6 asks which delegation semantics recover workflows; RQ8 asks whether planning can improve utility/minimise authority exposure.

Recommended revision:

- RQ6: explicit, scoped delegation and effective-authority semantics; can a delegated choice set recover legitimate workflows while preserving a clear confinement theorem?
- RQ8: can planning minimise/represent an authority envelope that the user has explicitly delegated, without treating plan generation itself as authority?
- Add a research-framing question or sub-question (probably not thesis-core): how should deterministic authority guarantees compose with empirically secured human/model semantic decision-making?
- Do not make SLED-V responsible for answering empirical model-security questions.

### `docs/decisions/020-maximal-permissiveness-and-synthesis.md`

Current theorem fixes ACS and separates delegation. Preserve that base theorem.

Add cross-reference to new ADR:

- maximality is relative to fixed machine authority relation + Conflux PE definition;
- after delegation, the same rule can be applied to a fixed `ACS_effective(e)` snapshot if the delegation semantics are valid;
- do not claim maximal safety for semantic organisational intent.

### `docs/decisions/015-open-ended-dynamic-planning.md`

Current spec is strong that planner output is untrusted and `ApprovalNode` manufactures no authority; `DelegationNode` is blocked.

Update only the intended future semantics:

- planner may represent/extract an explicit user delegation and an exact choice set;
- "planning says more authority is needed" is never sufficient to grant it;
- if the parser/model extracts delegation from natural language, exact scope must be authenticated/confirmed under a separately specified procedure before it affects `D_e`;
- `DelegationNode` remains runtime-disabled until activation work is separately completed;
- add ephemeral workflow execution as an application of scoped delegation, not a new ambient role.

### `docs/decisions/024-external-provenance-and-authority-bounds.md`

This ADR currently states that a trusted transformation may reduce influence and explicitly mentions runtime endorsement as unactivated.

User decision supersedes that forward-looking direction.

Do **not** erase decision history silently. Preferred approach:

- create ADR-025 that supersedes the endorsement/trusted-transformation future direction;
- add a short "Superseded in part by ADR-025" note to ADR-024 if repo ADR convention allows amendments;
- keep external provenance, no-laundering, authority-vs-harm, authentication rules intact;
- current semantics: ordinary execution never narrows PC; provenance-reduction mechanisms are outside the current design and require a new future ADR if revisited.

### `docs/evidence/CLAIMS.md`

Add/adjust claim boundaries:

- Conflux core claims authority confinement, not correctness of all choices inside authority.
- Model-level defences can provide empirical security but are outside the core formal guarantee.
- Scoped delegation is modeled/runtime-disabled; do not claim effective-ACS runtime support until activation evidence exists.
- Any claim that "model security only affects utility" must be removed.
- Add planned/evidence boundary for delegation choice-set semantics if only documented.

### `docs/evidence/STATUS.md`

Keep implementation status accurate. Add semantic migration as documentation/research framing, not implemented delegation activation.

The status should say, if accurate after edits:

- current runtime still denies delegation;
- docs now distinguish explicit ACS from intended execution-effective authority after future valid delegation;
- model-level defences are complementary empirical security controls, not in the TCB for authority establishment.

### `docs/evidence/CHANGE_CATALOG.md` and `task-registry.json`

Record this migration as a new semantic/documentation item. Do not mark runtime delegation implemented.

Suggested IDs if local conventions permit:

- `SEM-025`: authority confinement vs semantic judgement;
- `AUTH-025`: explicit vs effective ACS terminology;
- `DEL-025`: explicit delegated choice-set semantics;
- `DOC-025`: model-level security/human analogy reframing.

Use existing registry naming conventions instead if strict.

### `docs/reference/GLOSSARY.md`

Add or revise canonical terms:

- explicit ACS / `ACS_explicit`;
- effective ACS / `ACS_effective(e)`;
- authority envelope;
- semantic judgement;
- empirical model-level security / empirical semantic security;
- scoped delegation;
- delegated choice set.

Avoid introducing "true ACS". Prefer "intended organisational policy" for the richer semantic notion.

### `docs/integrations/cedar.md`

Cedar/PDP remains an implementation of the **explicit machine-readable policy source**, not the complete intended organisational policy.

Clarify that:

- a PDP answers concrete machine-policy questions;
- Conflux composes that with Principal Context;
- future valid delegation may create an execution-effective authority relation in Conflux without pretending the underlying Cedar policy globally changed;
- current runtime status remains unchanged.

### Root `README.md`

The current concise Principal Context description is largely good. Add one short boundary sentence rather than overloading the landing page:

> Conflux provides a hard authority-confinement layer; model-level defences and human/model judgement remain relevant for deciding which already-authorised action is appropriate.

Also ensure wording about "secure AI agents" does not imply complete behavioural safety.

## Publications/current research prose

Inspect and update current, editable sources that reproduce old framing, especially:

- `research/publications/manuscript/conflux_fourth_year_2026.tex`
- `research/publications/flmsec_2026/main.tex` if it remains an active editable submission source
- any current `research/reports/analysis/` synthesis document that is a current knowledge base rather than immutable archive

Do **not** edit:

- `research/reports/archive/`
- archived Part B/paper source identified by repository policy
- checksummed evidence artifacts

Publication changes must preserve historical theorem/evidence wording where required but update interpretation:

- model-level security is not "only utility";
- maximality is relative to PE + represented authority;
- semantic judgement inside authority remains empirical;
- explicit delegation changes the applicable authority relation;
- no endorsement as current Conflux direction.
