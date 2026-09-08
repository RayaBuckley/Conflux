# Evaluation, claims, and publication migration

## 1. Evidence classes must be separated

The repo should consistently distinguish:

| Question | Mechanism | Evidence class |
|---|---|---|
| Can an execution exceed its authority envelope? | ITES / SLED-V | theorem, model checking, bounded/unbounded formal evidence |
| Can delegation escape its scope? | delegation monitor / SLED-V | formal/bounded verification + negative controls |
| Can PC/provenance be laundered/reset? | provenance kernel / SLED-V | formal/bounded verification + tests |
| Does a model resist prompt injection? | model-level defence | empirical attack benchmark |
| Does a model/human choose an appropriate authorised action? | semantic decision-maker | empirical evaluation / organisational assurance |
| Does a task complete? | planner/model/runtime | empirical utility/effect evidence |

SLED/SLED-V should remain focused on the system-level columns. AgentDojo and real-model experiments can supply empirical model-security/utility evidence, but should not be described as the proof source for authority confinement.

## 2. `docs/evidence/CLAIMS.md`

Recommended new/updated claim boundaries:

### Authority confinement

> Conflux's hard guarantee concerns authority amplification relative to the represented effective machine authority relation. It does not guarantee semantic appropriateness of every authorised effect.

### Model-level security

> Model-level defences may reduce security risk empirically, but are not trusted by the Conflux kernel to grant authority or narrow Principal Context.

This is a conceptual/architecture statement; only label "implemented" if the code path/tests genuinely enforce that boundary.

### Delegation

Until runtime activation:

> Scoped delegation model exists, but `ACS_effective` delegation semantics are documentation/specification-level and runtime authority transfer remains denied.

Do not accidentally convert the new semantics into an implementation claim.

## 3. `docs/evidence/STATUS.md`

Add a "semantic framing" bullet to recent changes:

- clarified authority confinement vs semantic judgement;
- model-level defences recognised as complementary empirical security;
- distinguished explicit vs effective ACS;
- scoped delegation defined as explicit authority transfer, planner not authority source;
- endorsement removed from current planned mechanism set.

Then separately preserve implementation status: runtime delegation remains disabled.

## 4. SLED docs

Add a short scope paragraph:

> SLED-V asks whether a system-level transition model satisfies formal authority/provenance/visibility properties under arbitrary well-typed model proposals. It does not estimate whether a particular model resists prompt injection or correctly evaluates semantic legitimacy; those questions require empirical model/agent evaluation.

When reporting real-model experiments, label them complementary evidence rather than part of the hard SLED proof.

## 5. AgentDojo/model integration docs

Where relevant, clarify that an empirical attack result can establish evidence about model/system efficacy on those cases. It does not upgrade a bounded/formal Conflux claim, and the formal guarantee does not make empirical model robustness irrelevant inside the allowed authority envelope.

## 6. Current fourth-year manuscript

Search all sections, especially:

- abstract/introduction;
- threat model;
- security objective;
- related work/model-level defences;
- ITES theorem wording;
- planning/delegation future work;
- limitations/discussion;
- evaluation methodology.

Required framing:

1. Prompt injection has both a model-behaviour dimension and an authority dimension.
2. ITES deliberately gives a worst-case authority guarantee rather than attempting semantic detection.
3. This does not imply model-level defences are only utility improvements.
4. Human employees already mediate semantic conditions not fully encoded in access control; AI agents can occupy that role, with empirical risk.
5. ITES maximality is relative to the Conflux PE definition and represented authority relation.
6. Explicit delegation can intentionally enlarge the execution-effective authority relation.
7. Planning does not itself grant authority.
8. No endorsement direction.

## 7. FLMSec/current workshop source

If still active/editable, update the same conceptual boundary but preserve submission length constraints. Prefer one concise paragraph in discussion/limitations rather than expanding the paper substantially.

Suggested short wording:

> The worst-case model assumption isolates the authority-confinement guarantee; it does not imply that model-level defences have no security value. Organisations already rely on human judgement to resolve semantic conditions not encoded in access control, and defended models may serve a similar role. Such controls are empirical rather than part of the ITES guarantee, which instead bounds the authority available to either a correct or incorrect semantic decision.

## 8. Historical material

Do not edit:

- original Part B report/preprint archive;
- immutable report packages;
- checksummed evidence outputs.

Current docs can explicitly say that older material used an earlier framing where model-level security was treated mostly as utility and that the current semantics supersede that interpretation without altering historical artifacts.
