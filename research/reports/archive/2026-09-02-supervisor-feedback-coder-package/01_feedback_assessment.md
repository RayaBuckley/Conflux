# Conflux: Supervisor Feedback Assessment and AI-Coder Improvement Plan

Assessment date: 2026-09-02

Repository reviewed: https://github.com/RayaBuckley/Conflux, `main`

Primary historical source reviewed: `research/publications/flmsec_2026/main.tex` and archived Part B paper/report.

Purpose: determine which points in the supervisor's Claude feedback are technically correct, which are incomplete or based on the older manuscript, and translate the findings into concrete repository work for the AI coder.

## 1. Executive conclusion

The supervisor's feedback is substantially useful, but it mixes three different things:

1. valid criticism of the old FLMSec manuscript;
2. valid classical-security positioning that should be incorporated into the paper;
3. a few claims that are too strong or depend on a particular interpretation of external principals and action parameters.

The current repository has already addressed several of the criticisms that were made against the older implementation. In particular, the current security model explicitly requires non-empty/known Principal Context for effectful actions, separates provenance from read policy, treats rejected proposals as diagnostics rather than violations, uses one canonical ITES transition kernel, and makes external models/planners unable to narrow Principal Context. The current repository also explicitly acknowledges the Biba/LOMAC lineage and warns that novelty claims about provenance, monotonic restriction, or source-sensitive context require classical prior-art qualification.

However, the underlying conceptual challenge identified by the supervisor remains important: **accurate provenance does not by itself solve the utility problem created by untrusted external input**. Authentication makes provenance sound; it does not make an external principal privileged. If a webpage is correctly attributed to an `internet`/external principal with no relevant permissions, the ITES meet may indeed be empty and effectful work must be blocked. The current repository correctly treats this as a consequence of the conservative security model, not as something authentication alone fixes.

The most important improvements are therefore:

- repair the old paper's external-tool provenance wording;
- explicitly characterise ITES as a conservative, principal-sensitive authority analogue of low-water-mark integrity rather than claiming novelty for contamination/monotonicity itself;
- move the main contribution away from the elementary intersection theorem and toward the richer fourth-year semantics and verification work;
- make the FLMSec comparison claims about CaMeL/Progent/PACT faithful to their own objectives;
- correct the interpretation of the 1.46M/1.5M trace result;
- explicitly distinguish **authority bounds** from **harm bounds** and distinguish coarse action permissions from argument/effect-level security;
- add the missing classical systems literature: Biba, LOMAC, HiStar, Flume, Asbestos, Clark-Wilson, plus a much stronger treatment of Wu, Cecchetti and Xiao;
- add a small, explicit external-provenance model and tests demonstrating both the security guarantee and the utility cost;
- keep the current repository claim ledger as the source of truth and prevent manuscript text from outrunning retained evidence.

## 2. Repository state relevant to this feedback

The current repository is materially ahead of the manuscript that motivated the supervisor's review.

### 2.1 Current security contract

`docs/reference/SECURITY_MODEL.md` now says that authentication/provenance adapters attach complete origins and label uncertainty as unknown; the ITES kernel preserves context, isolates branches and composes decisions; models and planners cannot grant authority, assert decision provenance or narrow Principal Context; and only exact decision certificates can cross into execution.

The current normative rules include:

- empty or unknown Principal Context denies observable, nested, delegation and effectful actions;
- every Principal in context must be allowed;
- trusted operation schemas, rather than model output, assign argument roles;
- provenance describes influence while read policy decides observation;
- rejected proposals are diagnostics rather than executed security violations;
- Principal Context is monotone and sibling alternatives remain isolated.

See: `docs/reference/SECURITY_MODEL.md`.

### 2.2 Current ITES kernel

`src/conflux/ites/kernel.py` is explicitly documented as the sole pure ITES transition kernel. It implements complete mediation, the authority-intersection rule, alternatives with parent-state isolation, ordered sequential plans, and exact certificate binding.

In alternatives mode proposals are sorted deterministically and each branch starts from the same parent state. In ordered-plan mode state propagates sequentially and the next step is re-authorised before execution.

This directly addresses the older concern that the richer mediator might implement weaker branch semantics than the normative prototype.

### 2.3 Current research/evidence boundary

`docs/evidence/STATUS.md`, `docs/evidence/CLAIMS.md`, `docs/evidence/EVALUATION.md`, and `docs/reference/SLED.md` now distinguish:

- implementation status;
- bounded evidence;
- evaluation-ready infrastructure;
- historical Part B reproduction;
- unbounded claims;
- unavailable optional backends;
- live-model results.

The claim ledger explicitly records the 1.46M Part B reproduction as historical evidence, notes the collapse from 1,462,607 raw traces to 31 canonical states, and says the incomplete-count criterion differs from the old preprint. This is already better than the original manuscript's wording.

### 2.4 Current external benchmark position

The current repository records AgentDojo translation as implemented but does not treat translation as efficacy evidence. It also records a completed small Qwen 1.5B run as bounded evidence while explicitly explaining that the model is too small for useful task completion and that larger-model runs remain pending.

This evidence discipline should be preserved in the FLMSec paper rather than replacing it with stronger retrospective claims.

## 3. Point-by-point assessment of the supervisor's feedback

## 3.1 "This is LOMAC for principals"

### Verdict: substantively correct as a classical analogy, but incomplete as a characterisation of the contribution.

The current repository now correctly acknowledges the relation. `docs/reference/SECURITY_MODEL.md` explicitly calls the authority-intersection rule a structural analogue of Biba low-water-mark contamination, and `docs/research/RELATED_WORK.md` says the same mechanism is analogous to LOMAC.

The supervisor is therefore right that the paper should not present monotone contamination itself as unprecedented.

However, "LOMAC for principals" is a useful mnemonic rather than a full equivalence.

LOMAC/Biba uses an integrity ordering or label system. Conflux instead maintains a set of authenticated principals and derives effective action authority from the intersection of the permissions those principals receive from an existing organisational access-control relation. In the current repository this is extended with parameter-sensitive action arguments, provenance, visibility, consent, certificates, and current-policy re-checking.

The defensible statement is therefore:

> ITES instantiates the low-water-mark idea over a principal-sensitive authority domain: influence adds principals to a context, while the effective action authority is the meet/intersection of the permissions currently assigned to those principals by the organisation's ACS.

Do not claim that the intersection/monotonicity construction itself is novel without a much stronger prior-art search.

### Action for coder

Add an explicit "Classical lineage and distinction" subsection to the FLMSec paper. Explain:

- Biba low-water-mark contamination;
- LOMAC as an operating-system implementation of the low-water-mark idea;
- what differs in Conflux: identity/provenance sets rather than scalar labels, existing organisation-specific action permissions rather than a single integrity lattice, and later argument-sensitive authority.

Do not overstate the distinction. The repository's current research overview already uses appropriately cautious language and should be treated as the source for the wording.

## 3.2 "Reading external content makes the intersection empty"

### Verdict: conditionally correct; the underlying utility problem is real, but the supervisor overstates the universality.

The current ITES rule is:

`Allow(a, PC) iff PC is non-empty and every p in PC is authorised for a.`

Therefore, if external content is authenticated to an external principal with no relevant permissions, then adding that principal can indeed reduce the effective authority to the empty action set.

This is not a bug in the implementation. It is the cost of the conservative policy.

But "read anything external => empty" is only true if the external principal has no relevant permissions. If an organisation intentionally grants the external principal some permissions, those shared permissions remain available. The current model therefore allows organisations to decide how much authority an external principal has.

More importantly, authentication is not the solution to the utility problem in the sense suggested in the user's response. Authentication solves a different problem:

- it establishes that provenance labels correspond to the actual source;
- it does not make that source authorised for privileged actions;
- it does not tell ITES whether the content is malicious;
- it does not remove the source from Principal Context.

A correctly authenticated malicious webpage should still be treated as external influence.

The strongest interpretation is:

> **Authentication is a prerequisite for sound provenance, not a mechanism for recovering authority after untrusted influence is admitted.**

Utility recovery requires a separately justified mechanism such as more permissive visibility semantics, information bottlenecks, trusted transformations/endorsement, restricted delegation, or planning that delays unnecessary observation.

The current repository's visibility and disclosure work is already moving in this direction.

### Action for coder

Add a canonical example to the security-model tests and documentation:

1. `Alice` is the initiating principal.
2. `Internet` is an authenticated external principal with no `send_email` permission.
3. A webpage authored by `Internet` is read.
4. The Principal Context becomes `{Alice, Internet}`.
5. `send_email` is blocked because `Internet` does not permit it.
6. An action permitted to both principals remains allowed if one exists.
7. A user-visible reply is allowed only according to the repository's visibility policy and current empty/unknown-context rules.

This example should explicitly state the utility cost rather than trying to hide it.

## 3.3 "Label creep / laundering / endorsement: choose a regime"

### Verdict: strong conceptual criticism of the old paper; current repository now has a much clearer answer.

The old paper blurred together three possibilities:

- conservative contamination;
- removing contamination by starting a fresh execution;
- trusted removal/relaxation of influence.

The current repository has an explicit rule that models and planners cannot narrow Principal Context and that provenance/context accumulates monotonically through nesting. It also separates runtime delegation from future trusted authority-changing transitions.

This puts the current implementation squarely in the conservative regime for its core guarantee:

> **There is no untrusted laundering and no untrusted endorsement. Influence is only reduced by explicitly trusted semantics that are outside the ordinary model-proposal path.**

This should be made explicit in the paper.

The old user's proposed statement that "persistent objects inherit permissions of the LLM execution" should be refined. Objects should inherit the execution's **provenance/Principal Context**, not a frozen set of historical permissions. Later authorisation must be evaluated against the current ACS.

### Action for coder

Add a formal "No laundering" rule:

`PC(output) superseteq PC(execution inputs)`

for ordinary derived objects, unless a named trusted transformation is invoked.

Define a trusted transformation/endorsement operation separately if the project intends to study it. Do not let ordinary model-generated plans or object creation perform this operation.

Add tests for:

- new model call over an object produced by an untrusted execution;
- persistent storage followed by a new user session;
- summary object followed by privileged action;
- object copied between stores;
- explicit trusted transformation, if enabled in the model.

## 3.4 "The theorems are definitions restated"

### Verdict: essentially correct, and should be conceded.

The old Theorem 1 is mathematically immediate from the chosen security objective. The theorem does not demonstrate a surprising consequence; it characterises the maximal controller under the PE definition.

The authority monotonicity theorem is similarly a direct consequence of set intersection.

These results are still useful, but they should be labelled correctly:

- **design principle / optimality characterisation**, not a difficult theorem;
- **security consequence**, not a novel mathematical result.

The research value comes from showing how the principle behaves in the LLM-agent setting, where influence enters through arbitrary model behaviour, provenance, tools, recursive executions, and later policy changes, and from the verification/evaluation framework built around it.

### Action for coder

In the FLMSec paper:

- replace "we prove" language where it suggests deep theoretical novelty;
- call the maximality result an optimality characterisation of the policy;
- shorten the proof substantially;
- move the full elementary proof to an appendix if space requires;
- spend the saved text on the actual distinction from existing systems and on the threat-model semantics.

Do not delete the result entirely: it establishes why the intersection is not merely arbitrary conservative policy.

## 3.5 "1.5 million traces really means 31 canonical states and depth three"

### Verdict: correct and already mostly repaired in the current repository.

The current claim ledger explicitly records the exact Part B reproduction and says:

- 1,462,607 raw traces were reproduced;
- the canonical state representation collapses those into 31 unique canonical states;
- the reproduction is historical evidence;
- the current checker is not directly comparable because it explores canonical states rather than the old trace enumeration;
- the old incomplete-count criterion differs from the preprint.

The old paper's framing should therefore not be reused as if it describes the present SLED implementation.

The supervisor is also correct that the experiment is fundamentally bounded. Depth three is not a proof of arbitrary-depth behaviour.

### Action for coder

For the FLMSec paper, use wording equivalent to:

> We reproduce the three original environments under the original finite exploration regime, obtaining 1,462,607 prototype traces. The current state-based reproduction maps these executions to 31 canonical states under depth-three bounds. This is a reproduction/conformance exercise, not an evaluation of an independent implementation against unseen environments.

If the paper keeps the 1.5M number at all, explicitly label it historical/Part-B reproduction and give the bound immediately next to it.

## 3.6 "SLED is checking ITES against its own predicate"

### Verdict: partly correct; it depends on how the experiment is described.

If a test feeds ITES into SLED and the only property checked is ITES's own authorisation predicate, then the result is indeed primarily a conformance check.

But the original SLED design is broader than that: the intended contribution was a defence-independent evaluator in which the LLM is treated as adversarial and the evaluator checks externally defined system-level properties. The current repository has strengthened this idea substantially with an independent canonical safety oracle, defective monitors, negative controls, a verification IR, and explicit SAFE/UNSAFE/BOUNDED_SAFE/UNKNOWN outcomes.

The important distinction is between:

1. **SLED reproduces the ITES semantics**;
2. **SLED evaluates any defence against an independently specified property**;
3. **SLED verifies the implementation of that defence conforms to the formal model**.

These should not be conflated.

### Action for coder

Add one explicit independent-oracle experiment to the FLMSec evidence:

- construct a deliberately defective defence;
- make it violate the PE property;
- let SLED find the witness;
- show that the evaluator's property oracle is not implemented by the defence itself.

Then describe the existing ITES run as **semantic conformance** and the negative-control run as **evaluator sensitivity**.

## 3.7 "CaMeL, Progent and PACT do not violate PE because they never claimed it"

### Verdict: correct as a criticism of the old wording; current repository has already adopted the right qualification.

The current `CLAIMS.md` explicitly says the comparative models satisfy their own native properties while failing the Conflux PE property in the finite abstractions. The current `RESEARCH_OVERVIEW.md` says the correct interpretation is:

`D satisfies intended property Q, but Q does not imply Conflux PE property P.`

That is the correct experimental statement.

A counterexample to PE demonstrates a **threat-model/objective gap**, not a defect in the other system.

This is especially important for CaMeL because its capabilities and policies pursue different security goals. A faithful comparison therefore needs to model CaMeL's intended property and then ask whether that property is sufficient for PE under Conflux's threat model.

The same applies to Progent and PACT.

### Action for coder

Revise every comparative sentence in the FLMSec manuscript so that it uses one of:

- "does not guarantee PE";
- "PE is outside the modelled security objective";
- "its stated property does not imply PE";
- "our finite abstraction admits a PE counterexample under the Conflux property".

Do not write "CaMeL is insecure", "Progent fails", or "PACT violates its own guarantee".

Add a table with columns:

`System | Native objective | Trusted components | Provenance granularity | Conflux PE implication | Status of comparison`

The final column should explicitly say whether the entry is a faithful implementation, a finite abstraction, or a purely conceptual comparison.

## 3.8 "Tool outputs authored by the invoking user collapse the scheme"

### Verdict: definitely correct; this is the most important concrete modelling defect in the old paper.

The old manuscript states that outsourced/untrusted tool outputs may be associated with the principal on whose behalf the tool was invoked. This is unsafe if interpreted as assigning the user's authority to the resulting content.

The source of an output and the principal on whose behalf a tool executes are different concepts.

Example:

`Alice -> browser -> malicious webpage`

The browser may be acting on Alice's behalf, but the returned webpage was authored by the external site, not by Alice. Assigning Alice as its author would incorrectly transfer Alice's authority to attacker-controlled content.

The current repository's security model has the correct abstraction: authenticated provenance adapters attach complete origins, while models and planners cannot narrow Principal Context. This should be reflected in the paper.

### Required semantic distinction

Every object should distinguish at least:

- **producer/author principal(s):** who controlled the object's contents;
- **execution/agency principal(s):** on whose behalf the operation was requested;
- **transport/tool identity:** which system retrieved or produced it;
- **provenance:** the principals whose information can conservatively influence downstream computation.

The second must not silently become the first.

For a web page the default provenance should normally be the authenticated external source or an explicit `Internet` principal, not the user who requested the fetch.

### Action for coder

Add a decision record and test corpus named something like `external_provenance_non_escalation`.

It must test:

- web fetch result;
- inbound email;
- API response;
- tool-generated object;
- database result returned through a user's session;
- LLM-generated persistent object.

For each, record who authored the data and who invoked the tool separately.

Also update the paper wording from "associated with the principal on whose behalf the tool was invoked" to a precise statement that provenance reflects the authenticated source of the resulting object.

## 3.9 "Need HiStar, Flume, Asbestos"

### Verdict: correct and important.

These are not optional background references if the paper discusses provenance, information flow, dynamic labels, reference monitors, or the utility costs of contamination.

HiStar is a strict information-flow OS with explicit labels and a small trusted kernel. Flume applies decentralized IFC at process/OS abstraction level and uses a reference monitor/interposition architecture. Asbestos provides kernel-enforced labels and event-process isolation for systems acting on behalf of multiple users.

These systems are particularly relevant because they demonstrate that:

- dynamic contamination is old;
- trusted reference-monitor boundaries are old;
- acting on behalf of multiple principals is a classical problem;
- utility/security tension and label management are longstanding problems;
- declassification/endorsement boundaries are necessary when conservative contamination is too restrictive.

### Action for coder

Add the following references and discuss them in a dedicated classical systems/IFC subsection:

- Biba, *Integrity Considerations for Secure Computer Systems* (1977).
- Fraser, *LOMAC: Low Water-Mark Integrity Protection for COTS Environments*.
- Zeldovich et al., *Making Information Flow Explicit in HiStar* (OSDI 2006).
- Krohn et al. / Efstathopoulos et al., *Asbestos* work.
- Krohn et al./related Flume paper, *Information Flow Control for Standard OS Abstractions* (SOSP 2007).

The paper should explain exactly which phenomenon from each system is inherited and what Conflux changes.

## 3.10 "Need Clark-Wilson"

### Verdict: correct, especially for endorsement/delegation discussion.

Clark-Wilson is useful because it is not merely another information-flow model. It provides a model of integrity through well-formed/certified transformations and separation of duties.

This maps cleanly onto a future Conflux question:

> Under what trusted transformation may conservative influence be reduced or authority be changed without letting arbitrary untrusted input choose the transformation?

That is precisely the conceptual problem behind endorsement/declassification and controlled delegation.

### Action for coder

Add Clark-Wilson to related work and use it to frame trusted transformations/approval workflows. Do not claim that ITES implements Clark-Wilson; use it as a classical point of comparison for future trusted transformation and delegation semantics.

## 3.11 "Need a real differentiation from Wu, Cecchetti and Xiao"

### Verdict: definitely correct.

Wu, Cecchetti and Xiao's 2024 work already positions indirect prompt injection as an information-flow-control problem, provides formal models, a context-aware pipeline and a security monitor, and evaluates the resulting system.

This paper is particularly close to Conflux's threat model because it treats malicious information as able to influence subsequent planning and puts a system-level reference monitor around the model.

The differentiation must therefore not be:

- "we are system-level";
- "we use information flow";
- "we use a security monitor";
- "we are independent of model robustness".

Those are not sufficient.

A potentially defensible distinction is:

> Wu et al. prevent certain untrusted inputs from reaching the privileged planning component through a structured information-flow pipeline. Conflux instead treats all model-visible information as potentially influential, computes a conservative set of influencing principals, and derives the permitted externally visible authority by evaluating every influencer against the organisation's existing ACS. The security objective is therefore principal-sensitive privilege escalation rather than the integrity of a privileged planning channel.

That distinction needs to be demonstrated in a side-by-side formal example, not asserted rhetorically.

### Action for coder

Add a concrete comparative model of Wu et al.'s native property and a PE property. Show:

- a behaviour satisfying their security property but violating Conflux PE;
- an ITES behaviour satisfying PE;
- exactly which assumptions differ.

Do not use this to claim Wu et al. is insecure. The result should be phrased as **non-implication between security objectives**.

## 3.12 "ITES bounds authority, not harm"

### Verdict: conceptually correct, but the supervisor's example is too coarse if actions are parameterised.

The key distinction is:

> **Authority confinement is not the same as consequence/harm confinement.**

Suppose `PC = {user, external}`. ITES permits the intersection of their permissions, not all user permissions. If `external` has no `send_money` permission, then `send_money` is blocked.

However, if both principals can perform an operation such as:

`send_email(recipient, amount, attachment)`

and the ACS only models permission for the coarse `send_email` operation, then an attacker-controlled input may still influence which recipient, amount or attachment is selected. That is harm within already-authorised coarse authority.

The current repository has correctly identified this issue and now has trusted operation schemas and pointwise authority-bearing argument checks. It explicitly says richer operation-specific effect semantics remain future work.

Therefore the correct paper statement is:

> ITES prevents authority amplification relative to the granularity of the ACS. It does not by itself guarantee that authorised actions are safe, intended, or optimally parameterised. Finer argument/effect policies are needed where organisations treat those parameters as independently security-relevant.

This should not be dismissed as a mistake. It is a valuable limitation and an important motivation for the fourth-year extension.

### Action for coder

Add an explicit "authority versus harm" example to the paper and tests.

Test at least:

- coarse action permission only;
- recipient-specific permission;
- resource-specific permission;
- amount/limit constraint;
- credential/destination constraint.

Measure what ITES prevents at each granularity.

## 4. Additional issue not fully captured in the supervisor email: provenance versus read access

The current repository has already repaired an earlier semantic error where provenance was accidentally treated as a read ACL. The canonical domain model stores authors and readers separately, and current documentation states that provenance describes influence while read policy decides observation.

This separation is important to the external-input discussion:

- authentication/provenance answers *who originated the information*;
- read policy answers *who may observe it*;
- action policy answers *who may perform the operation*;
- visibility answers *who can observe the effect*.

These must remain distinct throughout the FLMSec paper.

The coder should search the manuscript and documentation for any sentence using author, reader, actor, consentor, invoking principal, and decision principal interchangeably.

## 5. Additional manuscript risk: empty context and universal quantification

The old prototype's mathematical rule was written as a universal quantification. In ordinary mathematics this makes the empty context vacuously satisfy an "all principals are authorised" test.

The current repository correctly adds an explicit non-empty/known-context condition. The paper should include it in the formal rule, not merely explain it in prose:

`Allow(a, PC) iff PC != empty and forall p in PC: P(p,a)`.

This is important because a formally careful reviewer can otherwise construct the obvious empty-context counterexample.

## 6. Recommended paper-level reframe

The supervisor's most useful suggestion is not simply "add references". It is to change what the paper claims to contribute.

The old story was approximately:

> ITES introduces provenance-based influence tracking, proves privilege escalation impossible, and SLED evaluates it exhaustively.

The stronger and more defensible story is:

> The paper identifies a principal-sensitive authority interpretation of low-water-mark contamination for LLM agents and shows how that principle interacts with existing organisational access control, worst-case model behaviour, and recursive execution. The main engineering contribution is a system-level enforcement/evaluation framework with explicit provenance, authority, visibility, and policy boundaries. The paper carefully separates elementary policy optimality from implementation conformance and bounded experimental evidence.

For the fourth-year project, the main new work should then be:

- fine-grained action/argument authority;
- safe delegation;
- visibility and confidentiality;
- attribution;
- planning under authority constraints;
- SLED-V formal verification;
- implementation conformance.

The current repository's research overview already supports this hierarchy.

## 7. Concrete AI-coder work plan

### P0 — semantic and documentation repair

1. Add an `external_provenance_non_escalation` specification/ADR.
2. Update tool-output provenance wording so that source identity and invoking/agency principal are distinct.
3. Add external/web/email/API provenance fixtures.
4. Add a test showing that authentication does not itself recover external authority.
5. Add the explicit non-empty Principal Context condition to every normative formulation.
6. Audit all docs for provenance/read/consent/decision-principal terminology.
7. Add the authority-versus-harm distinction to `SECURITY_MODEL.md` and the paper.
8. Ensure every persistent derived object inherits provenance/context, not historical permissions.

### P0 — FLMSec claim repair

1. Replace deep-theorem language around maximality and monotonicity with design/optimality language.
2. Reword the 1.5M result as bounded historical reproduction/conformance.
3. State depth three next to the relevant results.
4. Explain that the state-based current implementation has 31 canonical states for the reproduced environments.
5. Reword all comparative-defence results as non-implication between objectives, not defects in other systems.
6. Make clear which results are finite abstractions and which are implementation evidence.
7. Remove any sentence implying that passing SLED for ITES independently proves the ITES predicate unless the test uses an independent oracle.

### P1 — related work repair

Add and integrate:

- Biba;
- LOMAC;
- HiStar;
- Flume;
- Asbestos;
- Clark-Wilson;
- Wu, Cecchetti and Xiao.

For each, give a two- or three-sentence comparison focused on mechanism, threat model/property and the exact difference from Conflux.

### P1 — comparative verification

Create one finite canonical comparison harness with:

- ITES;
- a Wu-style IFC monitor;
- a Dual-LLM monitor;
- a CaMeL abstraction;
- Progent abstraction;
- PACT abstraction;
- an intentionally defective requester-only monitor.

Every model must have:

- its native property;
- the Conflux PE property;
- finite bounds;
- explicit assumptions;
- counterexample replay data;
- a status describing whether the model is faithful to a real implementation.

The comparison report must use the language:

`native property holds; Conflux PE does/does not follow`.

### P1 — utility-cost experiment

Construct a small family of external-principal scenarios:

- external principal with zero permissions;
- external principal with one safe permission;
- external principal sharing some user permissions;
- external principal with read-only permissions;
- external principal with parameter-restricted permissions.

Measure:

- number of actions remaining authorised;
- task completion under the deterministic model;
- Principal Context size;
- number of blocked actions;
- authority loss after observation.

This turns the "label creep" concern into measured research rather than a rhetorical objection.

### P1 — action-parameter experiment

Use a single action with increasingly fine ACS semantics:

`send_email` -> `send_email:recipient` -> `send_email:resource` -> `send_email:recipient+resource`.

Measure which attacker choices remain possible under each model.

This directly demonstrates the supervisor's "authority is not harm" point while also showing the value of Conflux's newer pointwise argument model.

### P2 — trusted transformation/endorsement model

Do not activate runtime endorsement yet.

Instead model a trusted transformation as an explicit state transition with:

- trusted transformer identity;
- input provenance;
- output provenance;
- policy justification;
- transformation certificate;
- no model authority to invoke or redefine the trust boundary.

Use SLED-V to ask which transformations preserve PE and/or confidentiality.

### P2 — paper/repository synchronization

Build a machine-readable paper-claim manifest or at least a repository audit that checks the manuscript for:

- every numerical claim has a retained evidence source;
- every comparative claim has an explicit objective/property qualifier;
- every novelty statement has a classical-prior-art qualifier where required;
- archived historical results are labelled as archived/historical;
- current implementation claims match `CLAIMS.md`.

## 8. Acceptance tests for the AI coder

The task should not be considered complete until all of the following are true.

### Security semantics

- An external web result is attributed to the external source, not the invoking user.
- A tool invocation principal cannot automatically become the author of its output.
- Empty/unknown context cannot authorise an effectful action.
- A derived object retains source provenance across sessions.
- A model cannot delete, narrow, or relabel Principal Context.
- Reads use reader policy rather than authorship provenance.
- Coarse action permission cannot be presented as a guarantee of safe parameter values.

### Evidence

- At least one independently judged defective monitor produces a minimal PE witness.
- At least one secure monitor completes with no PE witness.
- Historical Part B reproduction is clearly separated from current canonical evaluation.
- Comparative models record native properties separately from Conflux PE.
- All current numerical manuscript claims resolve to retained result JSON.

### Literature

- All seven missing classical/adjacent references are present in the bibliography.
- Wu, Cecchetti and Xiao have an explicit comparison subsection.
- Biba/LOMAC language is analogy-aware rather than novelty-claiming.

### Tooling

- repository audit checks the above conditions where practical;
- all tests pass;
- strict mypy and Ruff pass;
- manuscript builds in CI;
- the changed evidence bundle regenerates deterministically.

## 9. Suggested exact replacement language for key manuscript claims

### On LOMAC

> ITES follows the low-water-mark pattern of classical integrity systems such as Biba and LOMAC: consuming information from an additional source can preserve or reduce the effective authority of a computation but cannot increase it. Unlike scalar integrity labels, ITES retains authenticated principal identities and derives action authority from the organisation's existing access-control relation.

### On external input

> External information is not assigned the authority of the principal requesting it. Its authenticated source contributes to provenance and therefore to the execution's Principal Context. If the resulting context has no common authority for the requested action, the action is blocked. This conservatism is a security guarantee and an explicit utility cost, not something authentication removes.

### On maximality

> For a fixed Principal Context and the stated PE objective, principal intersection is the maximal safe authorisation rule: any strict superset permits an action for which at least one influencing principal lacks ACS authority. The result is an optimality characterisation of the policy rather than a technically difficult theorem.

### On SLED results

> The historical SLED experiment exhaustively enumerated the original finite prototype model to depth three. The current repository separately reproduces those environments using canonical states, yielding 31 unique states for the 1,462,607 prototype traces. These results establish reproduction/conformance under the stated bounds; they are not an unbounded security proof.

### On competing defences

> Our comparative models ask whether a defence's native security property implies the Conflux privilege-escalation property. A counterexample demonstrates non-implication between objectives; it does not show that the original defence violates its own stated guarantee.

### On authority versus harm

> ITES confines an action to authority shared by all influencing principals, but this guarantee is relative to the granularity of the ACS and action model. It does not by itself guarantee that every authorised parameter choice is safe or aligned with user intent. Fine-grained argument policies can therefore reduce harm within authorised action classes without weakening the privilege-escalation invariant.

## 10. Priority judgement

The supervisor has identified a genuine paper-positioning problem, not a fatal flaw in the core idea.

The old paper's strongest weakness is not that the intersection mechanism is logically wrong. It is that the paper did not clearly distinguish:

- an old and well-known contamination pattern from the new application;
- provenance correctness from utility recovery;
- authority confinement from harm prevention;
- conformance testing from independent evaluation;
- another system's native objective from the Conflux PE objective.

The current repository has already moved significantly in the correct direction. The next AI-coder pass should therefore be a **semantic/documentation consolidation and FLMSec repair**, not a large new feature sprint.

The immediate target should be one coherent narrative:

`authenticated source -> Principal Context -> existing ACS -> conservative authority bound -> explicit cost of external influence -> optional richer mechanisms -> independent verification/evaluation`.

The fourth-year contribution should then be built on the pieces the current repository already identifies as extensions: fine-grained arguments/effects, controlled authority changes, visibility/confidentiality, planning, attribution, and stronger verification.

## 11. Sources and repository locations

Repository:
https://github.com/RayaBuckley/Conflux

Current security contract:
`docs/reference/SECURITY_MODEL.md`

Current SLED semantics:
`docs/reference/SLED.md`

Current evidence status:
`docs/evidence/STATUS.md`

Current claim ledger:
`docs/evidence/CLAIMS.md`

Current evidence methodology:
`docs/evidence/EVALUATION.md`

Current research positioning:
`docs/research/RELATED_WORK.md`
`docs/research/RESEARCH_OVERVIEW.md`

Current ITES kernel:
`src/conflux/ites/kernel.py`

Current paper:
`research/publications/manuscript/conflux_fourth_year_2026.tex`

FLMSec paper:
`research/publications/flmsec_2026/main.tex`

Historical Part B paper/report: supplied in the project materials and archived in the repository.

Primary external literature verified for this assessment includes Biba (1977), LOMAC, HiStar, Flume, Asbestos, Clark-Wilson-related integrity work, and Wu, Cecchetti and Xiao (2024).
