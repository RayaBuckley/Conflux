# Conflux Research Overview

> Draft reviewer-facing overview. Reconcile against the current canonical repository documentation before treating this file as normative.
>
> **Canonical owners:** The security model is normative in [SECURITY_MODEL.md](SECURITY_MODEL.md); implementation status in [STATUS.md](STATUS.md) and [task-registry.json](task-registry.json); claim strength in [CLAIMS.md](CLAIMS.md); formal verification in [SLED.md](SLED.md); evaluation evidence in [EVALUATION.md](EVALUATION.md); comparative defence analysis in [reports/analysis/COMPARATIVE_DEFENCE_VERIFICATION.md](../reports/analysis/COMPARATIVE_DEFENCE_VERIFICATION.md); maximal-permissiveness analysis in [reports/analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md](../reports/analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md).

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

## 7. Relationship to adjacent work

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

## 8. Evaluation programme

The project should produce evidence at several levels:

1. **Semantic verification** — prove/check core invariants.
2. **Negative controls** — deliberately defective mediators must yield counterexamples.
3. **Reduction experiments** — compare traces/states/runtime/memory before and after reductions.
4. **Comparative defence models** — test the same properties against faithfully modelled contemporary defences.
5. **Real-model evaluation** — AgentDojo or similar tasks for practical security/utility.
6. **Granularity ablations** — quantify utility recovered by finer provenance without weakening the PE invariant.
7. **Implementation conformance** — relate production traces/transitions to the verified semantics.

## 9. What is not yet established

Do not infer from this overview that:
- every richer Conflux extension has a completed proof;
- every external defence has been faithfully formalised;
- a current symbolic backend already proves all ITES behaviour unboundedly;
- AgentDojo results have been fully validated and committed;
- implementation conformance has been established.

Those are research/evidence tasks.

## 10. Suggested reviewer path

For a research discussion:
1. Read this overview.
2. Read the canonical security model.
3. Read the current SLED/SLED-V documentation.
4. Inspect current claims/status documents.
5. Consult the manuscript/Part B material for the original theorem and evaluation.
6. Inspect the implementation only after the semantics and current claims are clear.
