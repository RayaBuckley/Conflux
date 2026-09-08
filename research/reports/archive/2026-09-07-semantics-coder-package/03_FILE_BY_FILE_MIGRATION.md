# File-by-file migration specification

The exact checkout may contain additional files. Use the search audit to discover all transitive references.

## Phase 0 — create the canonical decision first

Create `docs/decisions/025-authority-confinement-semantic-judgement-delegation.md` from the supplied draft.

Update `docs/decisions/README.md` to list ADR-025.

This ADR must become the canonical owner for:

- authority confinement vs semantic judgement;
- model-level defences as empirical security;
- human/AI semantic decision-makers;
- explicit vs effective ACS;
- scoped explicit delegation;
- planner is not an authority source;
- endorsement is not a current Conflux mechanism.

Do not duplicate all rationale verbatim in every document; link back to ADR-025.

## Phase 1 — normative semantic documents

### `docs/reference/SECURITY_MODEL.md`

Add sections in approximately this order:

1. "Security assurance layers"
2. "Explicit and effective authority policy"
3. "Authority envelope"
4. existing decision pipeline/normative rules
5. "Semantic judgement within authority"
6. "Humans, models, and model-level defences"
7. existing external provenance/authentication
8. existing authority versus harm, revised

Mandatory normative statements:

```text
Models/planners/classifiers are not trusted to grant authority or narrow PC.
A model may still be relied upon probabilistically to choose within already available authority.
Model-level security can reduce security risk even though it does not establish the ITES worst-case guarantee.
The machine-readable ACS is not asserted to encode every semantic condition in organisational intent.
Valid delegation changes ACS_effective for its scoped execution; it does not erase provenance.
Planning cannot manufacture delegation merely from task necessity.
```

Reconcile PC reduction wording with the decision to drop endorsement. Current recommendation: "Current Conflux execution does not reduce Principal Context. Any future exception requires a separately accepted semantics and proof obligation." This is simpler and avoids leaving an undefined trusted-transformation backdoor.

### `docs/reference/GLOSSARY.md`

Canonical definitions must be brief and non-circular. Suggested entries:

**Explicit ACS (`ACS_explicit`)** — the organisation's persistent machine-readable authority relation/PDP state before execution-scoped delegation.

**Effective ACS (`ACS_effective(e)`)** — the authority relation used for a particular execution after applying all valid scoped delegations to the explicit ACS.

**Authority envelope** — the set of effects an execution can be machine-authorised to perform under its Principal Context and effective ACS (plus pointwise authority-bearing argument restrictions as appropriate).

**Semantic judgement** — deciding whether an effect within available authority is appropriate given task meaning/context; may be performed by humans or models and generally carries empirical rather than worst-case assurance.

**Delegated choice set** — the exact finite or predicate-defined effects/parameters an authorised principal explicitly makes available to a beneficiary/execution.

**Model-level defence** — a control that changes model behaviour to reduce the chance of malicious/inappropriate decisions; security-relevant but empirically evidenced and not trusted to grant Conflux authority.

Remove or demote any glossary term that implies Conflux endorsement is an intended mechanism.

## Phase 2 — reader-facing narrative

### `docs/OVERVIEW.md`

Rewrite the opening problem section. Suggested structure:

1. Prompt injection/social engineering can manipulate both humans and AI decision-makers.
2. Model-level mitigations can reduce that risk and are security-relevant.
3. They do not provide a worst-case authority guarantee.
4. Conflux adds a complementary hard authority boundary.
5. If a workflow genuinely needs semantic judgement over untrusted content, Conflux cannot prove that the decision is appropriate; it can bound the authority exposed to that judgement.

Add one human analogy and one scoped-delegation example.

### Root `README.md`

Make only minimal high-level changes. Avoid making the README a second security-model owner.

### `docs/README.md`

Ensure navigation points users to ADR-025 / security model if a new semantic concepts section is added.

## Phase 3 — research framing

### `docs/research/RESEARCH_OVERVIEW.md`

Mandatory conceptual rewrite:

- "arbitrary model behaviour" remains the threat model for the hard authority theorem, not a claim that model robustness has no security value;
- explicitly separate formal authority safety from probabilistic semantic security;
- explain machine-readable policy vs intended organisational policy;
- delegation operates through `ACS_effective(e)`;
- planning may minimise or encode explicitly delegated authority but cannot grant it;
- ephemeral workflows/agents are an application of scoped delegation;
- remove endorsement/trusted transformations from the project's intended extension list;
- keep classical endorsement only in the historical literature tree if useful, with a sentence that it is not currently planned Conflux semantics.

### `docs/research/RESEARCH_QUESTIONS.md`

Recommended updated RQ6:

> Which explicit, scoped delegation semantics allow an authorised principal to delegate a precisely bounded choice set to an execution while preserving a clear confinement theorem over the resulting `ACS_effective`?

Recommended updated RQ8:

> Can planning represent and minimise an explicitly authorised delegated choice set and unnecessary observations without treating planner output or task necessity as an authority source?

Do not make model-level PI evaluation a SLED research question. It can appear as complementary empirical evidence in the evaluation programme.

### `docs/research/RELATED_WORK.md`

Add a short "Defence in depth: model behaviour and authority confinement" section.

Key points:

- model-level PI defences reduce attack success probabilistically;
- system-level Conflux bounds authority independently of those defences;
- neither subsumes the other for all security questions;
- human semantic decision-making is a useful systems analogy, but not itself a guarantee;
- Conflux can be combined with model-level defences.

CaMeL comparison must not claim the distinction is simply "Conflux has planning/delegation". The precise distinction for this project is that planner output is not an authority source; explicit principal delegation is required for `D_e`.

Retain scholarly descriptions of endorsement only as literature; remove it from the planned Conflux mechanism list.

## Phase 4 — planning and delegation decisions

### `docs/decisions/015-open-ended-dynamic-planning.md`

Append a superseding/future-delegation clarification linked to ADR-025. Do not alter current runtime fact that `DelegationNode` is blocked.

Specify:

- if natural-language user input explicitly delegates a bounded decision, planning may parse it into a proposed delegation object;
- this parse is untrusted until the repo's future activation protocol authenticates the exact scope/issuer and, where required, obtains explicit confirmation;
- no automatic "permission request because task failed" is equivalent to delegation;
- `RequiredAuthority(plan)` is diagnostic/planning metadata, not authority;
- when active in future, execution is still mediated under `ACS_effective(e)` and exact certificate/argument constraints.

### `docs/decisions/020-maximal-permissiveness-and-synthesis.md`

Add scope note:

- theorem applies to fixed authority relation;
- base proof can use `ACS_explicit` when no delegation applies;
- an extension can instantiate the same theorem at a fixed valid `ACS_effective(e)` snapshot;
- theorem does not solve semantic appropriateness or claim maximal organisational automation utility.

### `docs/decisions/024-external-provenance-and-authority-bounds.md`

Mark future endorsement/trusted-transformation portion superseded by ADR-025. Keep no-laundering and authority-vs-harm intact.

## Phase 5 — integrations, evaluation, evidence

### `docs/integrations/cedar.md`

Clarify Cedar is a PDP for `ACS_explicit` decisions. If/when Conflux scoped delegation is activated, Conflux may compose explicit policy with delegation to construct `ACS_effective(e)`; do not claim Cedar policy was globally rewritten unless the integration actually does so.

### `docs/evidence/CLAIMS.md`

Add semantic claim rows only if the claim ledger convention supports conceptual/documentation claims. Do not mark delegation activation implemented.

Suggested boundaries:

```text
Authority-confinement semantics distinguish model-level empirical security | documented/accepted semantics
Effective ACS includes only explicit valid delegation | specified, runtime delegation still disabled
Model-level defence cannot narrow PC or grant authority | implemented boundary if supported by code/tests
Semantic appropriateness inside envelope | not guaranteed by ITES
```

### `docs/evidence/STATUS.md`

Record the new accepted semantics and keep implementation status honest.

### `docs/evidence/CHANGE_CATALOG.md`

Record the migration and note that it is primarily semantic/documentation work.

### `docs/evidence/task-registry.json`

Add/update tasks under existing schema. Validate schema and deterministic formatting.

### `docs/evidence/EVALUATION.md` and `docs/reference/SLED.md` (or actual SLED path)

Add an evidence taxonomy:

- system-level formal/bounded evidence;
- empirical model-security evidence;
- empirical task utility.

State that SLED/SLED-V verifies the first category. AgentDojo/model experiments measure the second/third where configured.

Do not combine "no PE under arbitrary model behaviour" with "model resists attack" into one metric.

## Phase 6 — publication/current manuscript sweep

Search current editable publications for old framing.

Must rewrite phrases equivalent to:

- model-level defences only improve utility;
- model behaviour is irrelevant to security (without qualifying "authority confinement");
- correct ACS perfectly captures intended tasks;
- every blocked legitimate-looking task implies ACS should be modified;
- delegation as generic ACS mutation where execution-scoped effective authority is more accurate;
- endorsement/trusted transformation as planned current extension.

Do not rewrite historical results or archive blobs.

For current papers, the clean formulation is:

> ITES gives a worst-case authority-confinement result relative to the represented authority relation. Model-level defences remain complementary security controls for semantic correctness within that authority, much as organisations rely on trained human judgement for policy conditions not fully encoded in machine access control.

## Phase 7 — repository-wide consistency pass

Run all search patterns in `07_SEARCH_AND_DRIFT_AUDIT.md`, inspect every hit manually, and classify:

- normative/current — must agree with ADR-025;
- historical archive — do not edit;
- literature quotation/description — retain if accurate, but prevent it from being mistaken for current Conflux semantics;
- code/test comment — update only if it misstates current semantics; do not change behavior silently.
