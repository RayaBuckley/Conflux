# Conflux — Supervisor Feedback Revision Plan for AI Coder

**Date:** 2 September 2026  
**Purpose:** Implement the paper/repository revisions arising from supervisor feedback, Fable 5.1's second review, and a targeted verification of CaMeL's policy/planning semantics.

## 0. Executive instruction

Revise the repository and current manuscript so that the paper presents ITES as a **precise zero-trust authority floor** rather than as a complete solution to agent safety or utility.

Do not broaden the project merely to answer every criticism with a new mechanism. The paper already has enough contributions. The immediate objective is to make the existing contribution technically exact, explicitly acknowledge its costs and residual risks, and use planning/delegation/verification as clearly delimited extensions.

The central paper story should become:

> **ITES prevents privilege escalation by deriving an execution's authority from the authenticated principals whose information influences it and intersecting their permissions in the existing ACS. This is maximally permissive for the stated PE property, but it is intentionally conservative: genuine untrusted influence can reduce utility. Fine-grained authenticated provenance can reduce unnecessary authority loss; planning can recover utility by avoiding unnecessary contamination and by constraining which branches the model can select; explicit delegation is required when an organisation intentionally wants authority to cross an influence boundary.**

The repository should make all of these distinctions executable and testable.

---

## 1. What the new feedback establishes

The second Fable response resolves several earlier disagreements and should be treated as a writing/positioning guide rather than a demand for large new functionality.

### 1.1 LOMAC/Biba relationship

The classical relationship should be acknowledged directly. Conflux has a low-water-mark style monotone contamination pattern: additional influence cannot increase effective authority. However, Conflux should not claim that this is simply an LOMAC implementation.

The useful distinction is:

- classical low-water-mark integrity uses integrity labels/levels;
- ITES retains a set of authenticated principal identities as influence;
- effective authority is obtained from the organisation's existing ACS rather than from a newly assigned integrity lattice;
- parameterised/action-argument permissions can be evaluated using the same organisational authorisation machinery.

The paper should therefore say that ITES is **structurally analogous to low-water-mark contamination while replacing a single integrity label with principal-sensitive provenance interpreted through an existing ACS**.

Avoid claiming that no labels, metadata, or deployment work are required. Provenance authentication, source identity, object/chunk provenance, and ACS configuration remain necessary.

### 1.2 Provenance authentication and utility loss are two different issues

Clarify the distinction that arose in the email exchange.

**Problem A: provenance uncertainty/coarseness.**
Before an input is authenticated and appropriately decomposed/chunked, the system may need to attribute it conservatively to every principal that could have authored it. This can unnecessarily enlarge the Principal Context and reduce utility.

**Solution to A:** authenticated provenance plus sufficiently fine-grained object/chunk attribution.

**Problem B: genuine low-authority influence.**
After authenticated provenance establishes that an external principal actually authored the relevant content, that principal's low permissions legitimately constrain the execution. Better authentication does not remove this restriction.

**Solution to B:** do not silently remove the influence. Use explicit delegation/authority change, or accept that the action is outside the ACS authority envelope.

Use wording similar to:

> Authentication does not grant an external principal organisational authority. It makes the provenance used by ITES accurate. This matters because, before authentication and fine-grained attribution, conservative provenance may unnecessarily collapse the execution's authority. Once provenance is accurate, ITES intentionally refuses actions not jointly authorised by all influencers.

This distinction should appear in the paper, security model, and worked example.

### 1.3 The external-email task is a required worked example

Add one concrete example where external content genuinely determines an internal action.

Example:

1. Alice asks the assistant to read an incoming email from `supplier.example`.
2. The email says to schedule a delivery meeting.
3. The sender is authenticated as an external principal.
4. The assistant must read the email because Alice asked it to.
5. The email content influences the decision to create the calendar event.
6. If the external principal lacks permission to create that event, core ITES blocks the effect.
7. This is intentional: the ACS has not granted the external principal that authority.
8. If the organisation wants the workflow, it needs an explicit authority/delegation rule that grants only the required calendar authority.
9. If provenance had instead conservatively included a much larger set of possible authors, the same workflow could be blocked even when the real source is authorised; authenticated/fine-grained provenance avoids that unnecessary loss.

The purpose is not to present this as a defect. It is the key trade-off of the zero-trust floor.

### 1.4 “Maximal utility” must be narrowed

Replace broad or empirical-sounding language such as:

- “maximal utility was preserved”
- “ITES provides maximal utility”
- “all useful tasks remain available”

with precise language such as:

> For a fixed Principal Context and ACS, the Principal-Intersection rule is maximally permissive among action-level policies that preserve the stated PE property.

This is a mathematical maximality result, not a claim about the fraction of real-world tasks that remain useful.

The paper should then separately report utility loss/recovery empirically.

### 1.5 ITES is an authority guarantee, not a complete safety guarantee

State explicitly that ITES does **not** prevent an adversarial model from choosing the worst action that is already authorised by every influencer.

Three separate questions should be distinguished:

1. **Authority safety:** can influence cause execution outside the influencers' authority? ITES addresses this.
2. **Intent/safety within authority:** can the model choose a harmful action that is already authorised? Core ITES does not address this.
3. **Policy adequacy:** did the ACS itself grant excessive authority? This is outside the core ITES guarantee.

This is the “strategic” residual highlighted by the supervisor and should be stated as an explicit limitation and motivation for the next-stage research.

---

## 2. CaMeL research verification — policy expressiveness and what it actually means

### 2.1 Finding: PE can be represented as a CaMeL policy in a restricted/value-level sense

This should be incorporated into the repository and paper comparison.

CaMeL's published design states that security policies are Python functions taking the **tool name and arguments** and returning Allowed/Denied. The paper explicitly describes these policies as arbitrary Python logic and shows a calendar-event policy that inspects argument values and their capabilities/readers. citeturn674493view0turn780202view1

The published CaMeL implementation has the following relevant structure:

```text
SecurityPolicy(tool_name, kwargs) -> Allowed | Denied
SecurityPolicyEngine.check_policy(...)
```

and capabilities attached to individual values include provenance/source information and readers. The paper states that provenance can come from the user, CaMeL transformations, or specific tools; tools can also identify an inner source, such as the sender of an email, and cloud storage tools can label document provenance with editors. citeturn780202view1

Therefore, **if a source-to-organisational-principal mapping is supplied to the policy and the relevant principal provenance is present on the CaMeL values/dependencies, one can write a CaMeL policy that rejects a tool call whenever an identified influencing source lacks permission for the proposed tool/arguments.**

For example, conceptually:

```text
CaMeLPolicy(tool, args, dependencies):
    influencers = principals_from_capabilities(dependencies)
    return Allowed iff
        every influencer is authorised in ACS for (tool, args)
```

This means the previous wording “CaMeL cannot encode PE as a policy” is too strong and must be removed.

### 2.2 Important qualification: this does NOT mean CaMeL natively enforces ITES PE

The distinction is semantic and must be the focus of the comparison.

CaMeL policies operate when tool calls are reached and can inspect value capabilities/dependencies. CaMeL also explicitly models control-flow and data-flow separately. The paper states that the trusted query is converted to code, and that the P-LLM's generated plan is protected from untrusted data by the architecture. citeturn780202view0turn674493view1

CaMeL's dependency graph does have a STRICT mode in which a conditional test or loop iterable becomes a dependency of assignments in the block. The paper therefore already recognises that control-flow influence matters for some attacks. citeturn674493view3

The clean comparison is:

- **ITES:** conservative execution-level Principal Context; influence can persist through control dependence, nested executions, scheduling, and persisted artefacts.
- **CaMeL:** capability/dependency-based data/control-flow tracking inside a generated restricted program, with policies checked at tool calls.
- **Therefore:** an ITES-style PE policy is expressible in principle over CaMeL's policy interface **if** the policy has the necessary source-to-principal mapping and relevant dependencies are present; however, that does not establish that CaMeL's native architecture enforces the same whole-execution PE property.

### 2.3 The correct Table 9 / comparative-claims framing

Do not write:

> “CaMeL violates PE.”

Write:

> “CaMeL's native guarantees and ITES's PE property are different. A faithfully constructed model can satisfy CaMeL's intended property while admitting an execution that violates the Conflux PE property, demonstrating that the two properties are non-equivalent.”

The same approach should be used for Progent and PACT.

The comparison table should be reframed around **definitions of influence and enforced properties**, for example:

| Dimension | ITES | CaMeL | Progent | PACT |
|---|---|---|---|---|
| Primary security objective | PE prevention | Prompt-injection/data-flow security + policy enforcement | Tool/policy confinement | Provenance/argument security |
| Principal-level provenance | Yes | Source/capability-level | Policy/domain-specific | Fine-grained provenance |
| Explicit value/data dependencies | Yes | Yes | Yes, policy inputs | Yes |
| Control-flow influence | Conservatively retained in PC | Modelled via restricted program/dependency semantics; verify mode | Depends on model | Depends on model |
| Persistent cross-call influence | Yes | Interpreter state/capabilities persist across runs | Model dependent | Model dependent |
| Existing ACS as authority source | Core design | Not native | Not native | Not native |
| PE implication | Native property | Must be separately encoded/tested | Must be separately encoded/tested | Must be separately encoded/tested |

Do not claim any comparative result until the corresponding finite models are validated.

---

## 3. CaMeL planning restrictions and utility: incorporate this explicitly

### 3.1 What the primary paper actually supports

CaMeL explicitly separates a privileged planning LLM from the quarantined data-processing LLM. The P-LLM receives the user query and generates a restricted program/plan; it does not receive tool-returned values or Q-LLM outputs directly. Untrusted data is processed through the Q-LLM and capability-tracked interpreter. citeturn780202view0

CaMeL also reports empirical utility under attack and states that it “preserves utility better when under attack” than native tool calling in its AgentDojo experiments. citeturn667962view0

The paper's explanation is not “planning restrictions mathematically guarantee higher utility.” Instead, the architecture makes the trusted query's control flow explicit and prevents arbitrary untrusted data from changing the original plan. This can prevent attack-induced diversion of the main control flow.

The paper also documents that CaMeL has a utility cost/limitation where the required action itself depends on data that the P-LLM cannot observe. Its “Data requires action” failure occurs precisely for tasks of the form “do the actions specified in this email”. citeturn780202view2

### 3.2 How Conflux should formulate the planning idea

The planning contribution should not claim:

> “Planning improves utility.”

Instead distinguish two mechanisms.

**Planning optimisation for the ITES authority floor:**
Choose the ordering and decomposition of subtasks so that unnecessary low-authority information does not enter a shared execution context. Isolate independent subtasks into separate executions where possible. This can reduce unnecessary Principal Context growth and therefore recover utility without weakening the PE invariant.

**CaMeL-style control-flow restriction under attack:**
A trusted or separately protected planner can restrict the set/order of actions that the model can select. Under attack, this can increase the probability that the execution follows the intended task path rather than an attacker-selected branch. This is a utility/security-scaffolding effect, not an ITES authority proof.

These mechanisms are complementary.

### 3.3 A concrete utility-recovery formulation

Given a task decomposition:

```text
T = {t1, t2, ..., tn}
```

with data dependencies, define the authority cost of a schedule as a function such as:

```text
PC-size cost = sum over execution steps of |PC_t|
```

or a more meaningful weighted form:

```text
AuthorityExposure(schedule) =
    sum_t risk_weight(PC_t, t)
```

Then compare:

1. naive monolithic execution;
2. dependency-respecting execution order;
3. isolated subtasks;
4. authority-minimising planner;
5. planner + CaMeL-style trusted control-flow restriction.

The hard security constraint remains:

```text
Executed(action) -> every p in PC(action) is authorised by ACS
```

Only the strategy for obtaining a secure goal changes.

### 3.4 Strong experiment to add to SLED-V/planning evaluation

Use identical environments, task goals, attack distributions, and model.

Compare at least:

- unrestricted native tool-calling loop;
- ITES with naive task order;
- ITES with dependency-aware ordering;
- ITES with subtask isolation;
- ITES with authority-minimising planning;
- a CaMeL-style planner restriction;
- combined authority-minimising + restricted planner.

Measure:

- secure task completion;
- blocked actions;
- Principal Context size over time;
- number of distinct principals introduced;
- sensitive reads;
- model proposals selecting the intended branch;
- attack-induced branch divergence;
- action/plan retries;
- latency and model calls.

The key hypotheses are:

**H1:** ordering/isolation recovers tasks that core ITES blocks only because unrelated influence contaminated a shared execution.

**H2:** CaMeL-style control-flow restriction can improve utility under attack by preventing attacker-controlled data from changing the allowed/intended plan path.

**H3:** the combination provides greater practical utility than either mechanism alone without weakening the PE invariant.

H2 should be presented as an empirical hypothesis to test, not as a theorem.

---

## 4. Required changes to the security model

### 4.1 Provenance and authentication

Add explicit definitions for:

- authenticated source identity;
- provenance granularity;
- conservative provenance when exact authorship cannot be established;
- chunk/object derivation;
- external-source identity;
- source-to-principal mapping where external entities interact with organisational ACS.

State that authentication is part of the TCB and is required for the PE guarantee.

### 4.2 External tool outputs

Correct the old ambiguous rule.

Required rule:

> An externally fetched object retains the authenticated provenance of its actual source(s). It does not inherit the requesting user's organisational authority merely because the request was made on the user's behalf.

For objects genuinely produced/derived by an execution, the resulting object, scheduled execution, and persistent artefact must inherit the execution's Principal Context unless an explicitly trusted provenance transformation is modelled.

### 4.3 Cross-call laundering

Make the pc-taint/laundering closure explicit.

A sequence like:

```text
external input -> tainted execution -> schedule new execution -> privileged action
```

must remain tainted.

Likewise:

```text
external input -> write persistent object -> new assistant call reads object -> privileged action
```

must retain the original influence.

Tests must cover both.

### 4.4 Delegation

Treat delegation as a first-class authority-changing transition rather than as a weakening of the intersection rule.

Required structure:

```text
ACS_t + authorised delegation action
        -> ACS_(t+1)
        -> subsequent ordinary ITES checks use ACS_(t+1)
```

Permission to perform `a` must not automatically imply permission to delegate `a`.

Delegation must specify scope, principal, actions/resources, expiry, revocation, use count, and redelegation policy.

The current repository correctly keeps operational delegation denied pending activation evidence; do not weaken this merely to make the email example work. citeturn365619view1turn894081view1

---

## 5. Required changes to the formal claims

### 5.1 Reframe Theorem 1

Present this as a simple mathematical maximality/design result:

> For fixed Principal Context and fixed ACS semantics, Principal Intersection permits exactly the actions that do not constitute PE under the paper's definition. Any strict superset admits PE.

Do not present it as a deep theoretical contribution.

### 5.2 Reframe monotonicity

Retain monotonicity, because it is useful and directly supports the design:

```text
PC1 subseteq PC2
=> EffectiveAuthority(PC2) subseteq EffectiveAuthority(PC1)
```

Use this to motivate why influence cannot be laundered away.

### 5.3 Separate proof layers

The manuscript should clearly distinguish:

1. mathematical property of the abstract Principal-Intersection predicate;
2. SLED-V checking of the executable formal transition model;
3. implementation-conformance evidence;
4. finite empirical model results;
5. real-model benchmark results.

Do not conflate these.

---

## 6. Required changes to SLED/SLED-V presentation

### 6.1 Original SLED paper positioning

The paper's SLED contribution should primarily be:

> a system-level evaluator that treats model behaviour as adversarial/nondeterministic and can evaluate arbitrary black-box defences under a common system model.

The ITES experiment is a validation/sanity-check case, not the entire justification for SLED.

### 6.2 Bounded evidence

Do not use the old “1.5 million traces” language as though it were an unqualified formal result.

Use the current repository's distinction between:

- bounded historical reproduction;
- finite state-space verification;
- `BOUNDED_SAFE`;
- `SAFE` when a finite reachable state space is actually exhausted;
- `UNKNOWN` when semantics/backend/adapter support is incomplete.

The current repository already implements these distinctions. citeturn654172view3

### 6.3 Negative controls

Retain and explain defective monitors such as:

- requester-only authority;
- permission union/ANY-authorised;
- dropped provenance after nesting;
- empty-context-as-privileged;
- stale ACS;
- sibling-context leakage.

Their purpose is to demonstrate that SLED-V can detect violations, not to prove the correctness of ITES alone.

The repository already reports seeded-defect detection in the retained baseline evidence. citeturn894081view1

### 6.4 Comparative defence verification

For each external defence:

1. validate its own intended property;
2. build a faithful finite model;
3. test the Conflux PE property separately;
4. return a minimal counterexample only where warranted;
5. state that the result demonstrates property non-implication, not that the defence is “insecure”.

The current comparative-design document already uses this interpretation and should become canonical for the manuscript. citeturn654172view2

---

## 7. Required paper changes

### Abstract

Replace broad claims with a formulation along these lines:

> We introduce ITES, a provenance-based authority mechanism in which an execution inherits a Principal Context from authenticated input provenance and may perform only actions authorised for every principal in that context under an existing organisational access-control system. This is maximally permissive with respect to privilege-escalation prevention, but deliberately conservative: genuine untrusted influence can reduce the authority available to an execution. We show how fine-grained provenance, explicit delegation, and planning can address distinct sources of utility loss without weakening the core invariant. We additionally introduce SLED, a defence-independent evaluator that treats model behaviour as adversarial and exhaustively checks finite system models.

Do not reuse this text verbatim if the actual implementation/experiments differ; use it as the intended claim boundary.

### Related work

Add:

- Biba;
- LOMAC;
- Denning/noninterference;
- declassification/endorsement;
- HiStar;
- Flume;
- Asbestos;
- Clark-Wilson;
- Wu, Cecchetti and Xiao;
- CaMeL with the corrected value/control-flow distinction;
- Progent;
- PACT.

The classical foundation is essential because the contribution is not that monotone contamination is new.

### Threat model

Explicitly define:

- authenticated provenance as a TCB assumption;
- external principals;
- source-to-principal mapping;
- persistent object inheritance;
- scheduling inheritance;
- current ACS semantics;
- authority-changing delegation transitions.

### Security section

Include the three-way distinction:

```text
Authority security     -> ITES
Intent within authority -> not guaranteed
ACS correctness         -> assumption
```

### Utility section

Add the external-email/calendar worked example.

Then add the planning paragraph:

> Utility loss has two distinct causes. First, unnecessary influence can reduce effective authority; better provenance, ordering, and subtask isolation can reduce this contamination without changing the security invariant. Second, under attack, a model can choose an unintended branch even when the intended action remains authorised; CaMeL-style protected planning can reduce this failure mode by constraining the model's control-flow choices. These are utility mechanisms, not relaxations of the ITES PE rule.

The empirical CaMeL results support mentioning this as a motivated comparison: the CaMeL paper reports that it preserves utility better under attack in its AgentDojo evaluation, while also documenting task classes whose actions depend on untrusted data and therefore suffer utility limitations. citeturn667962view0turn780202view2

### Comparison table

Change the comparison from “which systems violate PE?” to “which influence semantics and native properties are enforced?”

### Evaluation

Split into:

1. SLED generic capability demonstration;
2. ITES sanity/conformance check;
3. negative-control detection;
4. comparative finite models;
5. planning utility experiments;
6. real-model evaluation where available.

### Limitations

State prominently:

- authenticated provenance is assumed;
- accurate ACS is assumed;
- genuine external influence can reduce utility;
- core ITES does not prevent misuse of already-authorised authority;
- core PE maximality does not imply confidentiality/noninterference;
- planning is not security-trusted unless its outputs pass the same mediation/verification boundary;
- richer delegation/visibility/consent extensions have separate proof obligations.

---

## 8. Repository changes

### 8.1 Canonical documents

Update these first:

- `docs/reference/SECURITY_MODEL.md`
- `docs/research/RESEARCH_OVERVIEW.md`
- `docs/reference/SLED.md`
- `research/reports/analysis/COMPARATIVE_DEFENCE_VERIFICATION.md`
- `research/reports/analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md`
- `docs/evidence/CLAIMS.md`
- manuscript related-work / methodology / discussion sections.

The current repository already identifies these as canonical owners. citeturn365619view3

### 8.2 Provenance tests

Add deterministic tests for:

1. authenticated external source retains external principal identity;
2. requesting user does not become the author of a web result merely by requesting it;
3. coarse/unknown provenance conservatively reduces utility;
4. authenticated fine-grained provenance recovers the expected utility case;
5. persistent artefacts inherit source influence;
6. scheduled executions inherit source influence;
7. new assistant calls cannot reset context;
8. chunk A and chunk B can have different provenance;
9. mixing chunks joins provenance exactly as specified.

### 8.3 Utility tests for ordering/isolation

Construct paired examples where:

- a monolithic execution reads both a low-authority item and a privileged-authority item before acting, and is blocked;
- the same overall task can be decomposed into independent subtasks whose contexts remain separate;
- the final action is still authorised in the isolated branch.

The test should demonstrate **utility recovery without security weakening**.

### 8.4 Planning tests

Add planner fixtures where:

- the task has two subtasks A and B with asymmetric provenance;
- A's result does not need to enter B's context;
- a naive plan contaminates B;
- an isolated/order-aware plan avoids that contamination;
- both satisfy exactly the same PE checks.

Add adversarial planner cases where:

- unrestricted planning selects an attacker-specified branch;
- protected planning exposes only the intended action/control-flow envelope;
- security remains enforced by ITES even when the planner is wrong.

### 8.5 Comparative CaMeL model

Do not delete the existing finite CaMeL model.

Update its specification so that it distinguishes:

- source/value dependency;
- control dependency;
- policy predicate on tool and arguments;
- planner-generated control flow;
- STRICT versus NORMAL dependency semantics where relevant.

Add two explicit experiments:

**Experiment A:** a PE policy is supplied to the CaMeL-style model. Verify that it can enforce PE when the policy has access to the needed source-to-principal information.

**Experiment B:** remove/relax the PE policy but retain native CaMeL-style policies. Demonstrate the resulting property set and any PE counterexample only if the formal model supports it.

This directly answers the supervisor's correction without unfairly characterising CaMeL.

### 8.6 Manuscript wording checks

Add an automated terminology/claim audit checking that the current manuscript does not contain:

- “CaMeL violates PE”
- “CaMeL cannot encode PE”
- “maximal utility” without the necessary qualifier
- “1.5 million traces” without “bounded historical evaluation” context
- “proof” for an empirical finite check
- “guarantees safety” where only PE is established.

Use the current claims ledger as the allowed-claim source. citeturn365619view4

---

## 9. Planning research specification

### 9.1 Formal planning state

A planning state should expose at least:

```text
environment state
principal context(s)
known/provenance-tagged artefact handles
available operations
ACS/policy state
pending subtasks
current plan position
failure/outcome state
call/resource budget
```

### 9.2 Planning objective

Use security as a hard constraint and utility as an optimisation criterion.

Candidate objective:

```text
subject to:
    NoPrivilegeEscalation
    ProvenancePreserved
    ReadPolicySatisfied
    VisibilityPolicySatisfied
    DelegationOnlyWhenExplicitlyAuthorised

optimise:
    task completion
    - authority exposure
    - unnecessary data observations
    - number of contaminated executions
    - model calls / latency
```

### 9.3 What “correct order” means

A planning optimisation counts as valid only if the precedence relation is justified by explicit task dependencies.

Example:

```text
fetch public metadata -> identify record -> inspect confidential record -> mutate record
```

should not be reordered arbitrarily.

The planner may reorder **independent** subtasks to keep contexts disjoint, but may not reorder operations in a way that changes task semantics.

### 9.4 Subtask isolation

Where two subtasks do not share data dependencies, execute them under separate child contexts.

The result should carry only the provenance needed by the parent. Do not claim that summarisation removes influence automatically.

### 9.5 CaMeL-style control-flow restriction

Represent the planner's output as an explicit finite control-flow envelope.

The LLM may propose content inside the envelope, but untrusted data must not silently enlarge the set of executable control-flow transitions.

This is a utility/robustness layer. ITES remains the final authority check.

---

## 10. Evaluation matrix to implement

| Experiment | Security question | Utility question | Status target |
|---|---|---|---|
| Authenticated vs coarse provenance | Does fine provenance preserve PE? | How much utility is recovered? | deterministic + real-model |
| Naive vs ordered plan | Does reordering preserve PE? | Does authority contamination fall? | deterministic |
| Monolithic vs isolated subtasks | Does isolation preserve PE? | How much utility returns? | deterministic |
| Unrestricted vs protected planning under attack | Does ITES still enforce PE? | Does intended-task completion improve? | real-model |
| ITES vs CaMeL-style policy | Can policy encode PE? | Which tasks differ because influence definitions differ? | finite model |
| CaMeL native property vs PE | Does native Q imply PE? | Which counterexample distinguishes them? | finite model |
| Delegation | Can authority legitimately change? | Which previously blocked tasks become possible? | bounded formal model |
| Persistent artefact laundering | Can taint be reset? | What utility cost does persistence impose? | formal model |

---

## 11. Acceptance criteria for the AI coder

Do not mark this task complete until all relevant items below are satisfied.

### Security semantics

- [ ] External source authorship/provenance is explicitly separate from requesting user identity.
- [ ] Authenticated provenance is documented as a TCB assumption.
- [ ] Persistent artefacts and scheduled executions preserve influence.
- [ ] Provenance can be fine-grained/chunked without changing the PE predicate.
- [ ] Empty/unknown context behaviour remains fail-closed.
- [ ] Delegation remains an explicit authority-changing transition.

### Paper claims

- [ ] LOMAC/Biba lineage is acknowledged.
- [ ] “maximality” is qualified as PE-relative mathematical maximal permissiveness.
- [ ] Broad “maximal utility” language is removed or qualified.
- [ ] SLED's general black-box role is foregrounded.
- [ ] ITES evaluation is described as a sanity/conformance demonstration where appropriate.
- [ ] Comparative claims use “property non-equivalence” / “different influence semantics” rather than “violates PE”.
- [ ] Residual authorised-harm limitation is explicit.
- [ ] External-email/calendar example is included.

### CaMeL comparison

- [ ] Primary CaMeL policy semantics are cited.
- [ ] Paper/code evidence that policies are Python functions over tool + args is cited.
- [ ] Capability source/provenance semantics are acknowledged.
- [ ] The statement “CaMeL cannot express PE” is removed.
- [ ] A finite experiment demonstrates the exact conditions under which an ITES-style PE policy can be represented.
- [ ] Control-flow/influence differences are explained separately from policy expressiveness.

### Planning

- [ ] Utility recovery by dependency-aware ordering is implemented or modelled.
- [ ] Utility recovery by independent subtask isolation is implemented or modelled.
- [ ] CaMeL-style protected planning is represented as a distinct utility/control-flow mechanism.
- [ ] A real-model or controlled empirical experiment tests whether protected planning improves task completion under attack.
- [ ] Planning never bypasses the ITES mediation kernel.

### Verification/evidence

- [ ] Current SLED-V verdict semantics are preserved.
- [ ] Negative-control mutants still produce counterexamples.
- [ ] New planning/provenance tests have deterministic retained evidence.
- [ ] Claims ledger and manuscript are updated consistently.
- [ ] Validation, tests, type checks, and repository audit pass.
- [ ] No unsupported empirical result is described as completed.

---

## 12. Recommended implementation order

### Phase 1 — paper/semantic repair

1. Update `SECURITY_MODEL.md` with the authenticated-provenance, external-source, persistent-influence, and residual-authorised-harm rules.
2. Update the research overview and claims ledger.
3. Add the external-email/calendar worked example.
4. Add the LOMAC/Biba/HiStar/Flume/Asbestos/Clark-Wilson/Wu lineage.
5. Rewrite the comparison language around influence semantics.

### Phase 2 — provenance and laundering tests

6. Add the source-authentication and requester-identity tests.
7. Add persistence/scheduling inheritance tests.
8. Add fine-grained/chunked provenance fixtures.
9. Retain deterministic evidence outputs.

### Phase 3 — CaMeL correction

10. Audit the current CaMeL finite model against the primary paper and implementation.
11. Add the explicit PE-policy experiment.
12. Add control-flow/value-flow comparative counterexamples only where faithfully modelled.
13. Update Table 9 and associated text.

### Phase 4 — planning utility

14. Add dependency-aware ordering.
15. Add independent-subtask isolation.
16. Add authority-exposure metrics.
17. Add CaMeL-style planner/control-flow restriction baseline.
18. Run controlled under-attack utility experiments.

### Phase 5 — manuscript/evidence closure

19. Replace all overstated claims.
20. Regenerate figures/tables from retained evidence.
21. Run the full validation/audit suite.
22. Run a final claim-to-evidence audit before publication.

Do not start new production policy/provider work during these phases unless required to support one of the experiments above.

---

## 13. Final intended contribution hierarchy

The final manuscript should have the following hierarchy.

### Core contribution

**Principal Context / ITES:** a principal-sensitive, ACS-grounded authority rule for zero-trust agent execution with a precise PE guarantee.

### Supporting contribution

**SLED:** defence-independent worst-case evaluation of system-level security properties, demonstrated with ITES and defective controls.

### Fourth-year extensions / empirical contributions

- fine-grained authenticated provenance and its utility/security trade-off;
- explicit delegation;
- visibility/confidentiality extensions;
- planning/order/isolation for utility recovery;
- protected control-flow planning for robustness under attack;
- stronger verification/conformance through SLED-V.

These extensions should be evaluated separately. Do not quietly fold them into the core PE theorem.

---

## 14. Research interpretation to preserve

The paper is strongest when it admits the following:

> ITES is a deliberately conservative zero-trust floor. If untrusted information genuinely influences a computation, the resulting execution inherits the authority constraints of that influence. This can make useful workflows impossible unless provenance is sufficiently precise or the organisation explicitly grants the required authority. That cost is not a failure of the PE guarantee; it is the price of refusing to trust the model to decide when untrusted influence should be ignored. Planning, isolation, and explicit delegation therefore belong above the core authority invariant, while SLED-V asks whether those extensions preserve it.

This is the cleanest way to incorporate the supervisor's feedback without turning the workshop paper into an attempt to solve every aspect of agent security.

---

## Sources checked for the revised CaMeL assessment

- Debenedetti et al., *Defeating Prompt Injections by Design*, arXiv:2503.18813v2. The paper defines CaMeL's P-LLM/Q-LLM architecture, security policies, capabilities, control/data-flow handling, and empirical utility/security evaluation. citeturn751810view0turn780202view0turn780202view1
- CaMeL official research artifact, `google-research/camel-prompt-injection`. Its current security-policy interface confirms that policies are functions over the tool name and `CaMeLValue` arguments and that policy decisions can inspect capabilities. citeturn186399search0
- Current Conflux repository: the README identifies the current system as a pre-1.0 research framework with a fail-closed ITES kernel, planning, bounded SLED verification, and authenticated dynamic plans. citeturn365619view0
- Current Conflux security model: authenticated provenance is in the TCB; the kernel, policy ports, action schemas, and executor define the trusted boundary; provenance is explicitly distinct from read policy; model/planner components cannot grant authority or narrow Principal Context. citeturn365619view1
- Current Conflux status: the repository records the current finite verification/evidence boundaries, existing CaMeL/Progent/PACT finite models, and the outstanding planning/AgentDojo/delegation research tasks. citeturn894081view1
