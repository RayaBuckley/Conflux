# Conflux Research Overview

> Draft reviewer-facing overview. Reconcile against the current canonical repository documentation before treating this file as normative.
>
> **Canonical owners:** The security model is normative in [SECURITY_MODEL.md](../reference/SECURITY_MODEL.md); implementation status in [STATUS.md](../evidence/STATUS.md) and [task-registry.json](../evidence/task-registry.json); claim strength in [CLAIMS.md](../evidence/CLAIMS.md); formal verification in [SLED.md](../reference/SLED.md); evaluation evidence in [EVALUATION.md](../evidence/EVALUATION.md); comparative defence analysis in [research/reports/analysis/COMPARATIVE_DEFENCE_VERIFICATION.md](../../research/reports/analysis/COMPARATIVE_DEFENCE_VERIFICATION.md); maximal-permissiveness analysis in [research/reports/analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md](../../research/reports/analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md).

## 1. Research problem

Conflux studies security for LLM agents that consume information originating from multiple principals and can perform externally visible actions.

The central threat model is deliberately stronger than ordinary prompt-injection evaluation: information supplied to an LLM may arbitrarily influence its subsequent behaviour. The security mechanism therefore should not depend on the model correctly recognising malicious instructions.

The core security question is instead:

> If a principal can influence an action, is that principal already authorised by the organisation's access-control system (ACS) to perform that action?

Prompt injection is one mechanism for creating influence. It is not itself the security property.

## 2. Principal Context and ITES

Each execution has a **Principal Context (PC)** containing the principals whose information may have influenced it.

For an action `a`, the core ITES rule is:

    Allow(a, PC) iff for every p in PC, ACS permits p to perform a.

Equivalently, effective authority is the intersection of the permissions of all influencing principals.

Additional influence can therefore preserve or reduce authority but cannot increase it.

### Trusted computing base

The guarantee assumes:

- correct provenance/influence tracking;
- a correct ACS or policy decision source;
- complete mediation of relevant effects;
- correct enforcement code.

The LLM itself is not trusted for security.

## 3. Why the rule is interesting

Under the Conflux definition of privilege escalation (PE), an executed action is insecure if at least one influencing principal lacks permission for it.

For fixed Principal Context `PC`, ITES allows every action authorised for all principals in `PC`.

If an alternative rule permits any additional action, then by definition at least one principal in `PC` lacks permission for that action. Executing it is PE.

This motivates the claim that Principal Intersection is **maximally permissive with respect to PE prevention**, under the stated threat model and ACS semantics.

Part C should distinguish:

1. the general mathematical maximality theorem;
2. formal verification of the executable transition semantics;
3. implementation-conformance evidence.

## 4. Part B foundation

The previous project introduced:

- Influence Tracking with Extrapolated Security (ITES);
- Principal/influence accumulation;
- the permission-intersection rule;
- a conservative read rule;
- authority monotonicity and PE-prevention arguments;
- SLED, which explores possible LLM/defence behaviours under worst-case model assumptions;
- bounded experiments over roughly 1.5 million traces.

The main limitation exposed by SLED was combinatorial state-space growth. The original evaluation used bounded recursive depth and therefore did not establish an unbounded implementation-level result.

## 5. Part C direction

The strongest current direction is to turn SLED into a property-parametric verification framework.

Candidate capabilities:

### Verification

Given defence `D` and property `P`:

- `SAFE`: all executions in the formal model satisfy `P`;
- `UNSAFE`: return a concrete/minimal counterexample;
- `BOUNDED_SAFE`: no violation within an explicit bound;
- `UNKNOWN`: unsupported semantics, timeout, abstraction uncertainty, etc.

### Synthesis

Given:

- the ACS;
- provenance/Principal Context;
- arbitrary schema-valid LLM proposals;
- a PE safety property;

synthesise the maximally permissive safe controller.

A particularly strong result would be that this controller is equivalent to the ITES Principal-Intersection rule.

### Comparative verification

Represent other system-level defences in the same verification semantics and ask which properties they satisfy.

The goal is not to claim that another defence is incorrect relative to its own threat model. A useful result can instead be:

    Defence D satisfies its intended property Q,
    but Q does not imply the Conflux PE property P.

SLED-V can then provide a concrete counterexample witnessing the distinction.

## 6. Richer semantics

Several extensions should remain subordinate to the core invariant.

### Delegation

Delegation should be an explicit authorised authority-changing transition, e.g.:

    ACS_t -- authorised delegation --> ACS_(t+1)

The subsequent action is checked normally under the updated authority state.

Delegation itself requires authority; permission to perform `a` should not automatically imply permission to delegate `a`.

### Consent

Consent should be separated from information provenance. Merely influencing a computation should not automatically grant a principal a veto over another principal's independently authorised action.

The derivation of the principal(s) whose agency is being exercised needs a dedicated specification.

### Visibility/confidentiality

A more permissive confidentiality rule can consider who observes an effect rather than forbidding all computation involving information not readable by every influencer.

A candidate condition is:

    Observers(effect) subset of the intersection of Readers(d)
    for all information influencing that observable effect.

This requires precise observation semantics and may eventually require relational/noninterference properties.

### Argument-level provenance

Whole-execution Principal Context is conservative. Tool arguments can have distinct causal/provenance histories.

This motivates an ablation:

    execution-level PC
    -> action-level PC
    -> argument-level PC
    -> visibility-aware argument-level PC

The security invariant should remain ACS-derived PE prevention while utility is measured empirically.

## 7. Classical security foundations

The core ITES mechanism is not without classical precedent. The
principal-sensitive authority intersection rule is structurally analogous to
low-water-mark contamination from Biba's integrity models, operationalised in
systems such as LOMAC. [ADR 012](../decisions/012-foundational-security-lineage.md)
records this positioning decision; the [foundational security literature
analysis](../../research/reports/analysis/2026-08-13-foundational-security-literature.md)
provides the detailed comparison.

### Conceptual lineage

    Reference monitors / complete mediation / least privilege
                        |
                        v
          Mandatory information-flow models
            /                            \
           v                              v
    Denning / confidentiality          Biba integrity
           |                              |
           v                              v
    noninterference                low-water-mark policies
           |                              |
           v                              v
    language-based IFC                  LOMAC
           |                              |
           +-------------+----------------+
                         v
              decentralized IFC
           declassification / endorsement
                         |
                         v
           robust attacker-influence models
                         |
                         v
     provenance / taint / whole-system IFC
                         |
                         v
     contemporary system-level LLM-agent security
                         |
                         v
            Principal Context / Conflux

This is not a single direct inheritance chain. These literatures solve
different problems. The point is to prevent the dissertation from discussing
Conflux only against work published after LLM agents appeared.

### Structural similarity to low-water-mark integrity

Biba's low-water-mark policy reduces a subject's effective integrity after it
observes less-trusted information, restricting its future high-integrity
effects. Conflux's authority-intersection rule exhibits the same monotonic
contamination pattern: adding an influencing principal to Principal Context
can preserve or reduce effective authority but cannot increase it.

Conflux enriches this pattern by:

1. retaining authenticated principal identities rather than only a generic
   trust label;
2. deriving effective authority from the organisation's existing ACS rather
   than requiring a single integrity classification;
3. supporting parameterised and argument-sensitive action authority.

These are candidate distinctions, not established novelty claims, until a
targeted prior-art search is complete.

### Revised fourth-year story

The strongest fourth-year framing is:

1. Principal Context / ITES is a principal-sensitive authority
   analogue/generalisation of low-water-mark contamination, grounded in
   existing organisational authorisation rather than a single integrity
   classification.
2. The fourth-year project develops the parts not supplied by that analogy:
   fine-grained authority semantics, explicit delegation and consent,
   visibility/controlled disclosure, planning that avoids unnecessary
   authority contamination, attribution, and substantially stronger
   verification.
3. SLED-V should distinguish ordinary safety properties from relational
   confidentiality/noninterference properties.
4. Contemporary LLM-agent systems such as CaMeL, Progent, PACT, and
   causal-provenance approaches remain the closest application-domain
   comparisons; classical security work supplies the conceptual and formal
   foundations.

The existing modern-agent landscape is retained but enriched with this
foundational stream.

## 8. Relationship to adjacent work

Conflux can borrow mechanisms without adopting another system's security objective.

Useful ideas include:

- CaMeL: plan/execution separation, mediation and capability concepts;
- PACT-like work: argument-level and cross-step provenance granularity;
- policy systems such as Progent: parameter-sensitive policy representation;
- classic IFC/Biba: monotonic labels, endorsement/declassification theory;
- capability systems: scoped delegation;
- causal provenance systems: dependency graphs and explanation;
- reference monitors: complete mediation;
- formal methods: state canonicalisation, partial-order/symmetry reduction, SMT, IC3/PDR, CEGAR and controller synthesis.

The central distinction is that Conflux asks whether influence can cause authority to exceed what the influencing principals possess in the existing ACS.

## 9. Evaluation programme

The project should produce evidence at several levels:

1. **Semantic verification** — prove/check core invariants.
2. **Negative controls** — deliberately defective mediators must yield counterexamples.
3. **Reduction experiments** — compare traces/states/runtime/memory before and after reductions.
4. **Comparative defence models** — test the same properties against faithfully modelled contemporary defences.
5. **Real-model evaluation** — AgentDojo or similar tasks for practical security/utility.
6. **Granularity ablations** — quantify utility recovered by finer provenance without weakening the PE invariant.
7. **Implementation conformance** — relate production traces/transitions to the verified semantics.

## 10. What is not yet established

Do not infer from this overview that:

- every richer Conflux extension has a completed proof;
- every external defence has been faithfully formalised;
- a current symbolic backend already proves all ITES behaviour unboundedly;
- AgentDojo results have been fully validated and committed;
- implementation conformance has been established.

Those are research/evidence tasks.

## 11. Suggested reviewer path

For a research discussion:

1. Read this overview.
2. Read the canonical security model.
3. Read the current SLED/SLED-V documentation.
4. Inspect current claims/status documents.
5. Consult the research/publications/manuscript/Part B material for the original theorem and evaluation.
6. Inspect the implementation only after the semantics and current claims are clear.
