# CaMeL and ITES: Corrected Technical Position

## 1. Purpose

This document corrects an overly broad statement in earlier guidance: it is too strong to say that CaMeL "cannot encode PE as a policy". The defensible claim is narrower and more useful.

## 2. What CaMeL actually provides

The CaMeL paper and released implementation define security policies as Python callables over the tool name and `CaMeLValue` arguments. The policy engine can inspect value capabilities/dependencies and return `Allowed` or `Denied`.

The implementation also carries provenance/source and reader information in capabilities. Its dependency analysis distinguishes normal and strict metadata propagation, and the architecture explicitly protects the trusted query/control flow from untrusted data.

Primary sources:
- https://arxiv.org/abs/2503.18813
- https://github.com/google-research/camel-prompt-injection/blob/main/src/camel/security_policy.py
- https://github.com/google-research/camel-prompt-injection/blob/main/src/camel/interpreter/interpreter.py

## 3. What follows from this

Because the policy interface is programmable, one can imagine extending CaMeL with a policy roughly of the form:

    influencers = principal_mapping(relevant_capability_sources)
    allow iff every influencer is authorised in the organisation ACS
                        for the proposed parameterised action

That observation is logically valid but should NOT be presented as evidence that CaMeL natively enforces ITES PE.

To make such a policy soundly implement ITES, the surrounding system must supply the semantics that ITES depends on:

1. authenticated mapping from external/tool sources to organisational principals;
2. sufficiently fine-grained provenance attached to the relevant objects/values;
3. the definition of which information and control influences are included in Principal Context;
4. conservative propagation through nested executions;
5. propagation through scheduling and persistent derived objects;
6. preservation of influence across assistant calls/sessions where applicable;
7. a trusted interface to the organisation's ACS for the concrete parameterised action;
8. a policy composition rule deciding how the set of influencing principals is interpreted;
9. complete mediation of every effectful action;
10. explicit semantics for cases where the available CaMeL dependency set is not the same as the ITES execution-level influence set.

Adding these semantics would be an extension of CaMeL rather than a demonstration that its native security objective already implies PE.

## 4. The right comparison

Do not use:

> "CaMeL cannot express privilege escalation as a policy."

Do not use:

> "CaMeL enforces ITES PE because its policies are Python."

Use a formulation such as:

> CaMeL provides programmable, capability- and dependency-aware policies that can express a wide range of application-specific security conditions. An ITES-style PE predicate could be implemented on top of this interface only after supplying the principal attribution, influence-propagation, persistence, and ACS semantics required by ITES. We therefore compare the systems using their native/expected security semantics, rather than treating hypothetical extensions to CaMeL as equivalent to ITES.

## 5. Influence semantics are the key distinction

The most useful comparison is what each system considers relevant influence.

ITES adopts a conservative execution-level Principal Context. If authenticated information from principal p genuinely contributes to an execution, then p remains in the execution's influence context unless a separately trusted semantic operation removes or transforms that influence. This explicitly covers implicit/control influence and cross-execution propagation.

CaMeL is built around a protected planning/control-flow architecture and capability/dependency tracking for data flows. Its implementation has a STRICT dependency mode, so the paper must not falsely claim that CaMeL simply ignores control dependence. The comparison must instead ask whether CaMeL's native dependency set and policy checks imply the ITES definition of principal influence for the particular witness.

## 6. How Table 9 should be framed

The table should not say that CaMeL, Progent, or PACT "violates PE" in the broad sense.

Instead, frame it as:

> **Influence semantics enforced by representative system-level defences**

Useful columns:

- security objective;
- policy mechanism;
- provenance granularity;
- explicit value/data dependence;
- control dependence treatment;
- cross-execution/persistent influence;
- principal attribution;
- ACS integration;
- whether the native guarantee implies the ITES PE predicate;
- counterexample witness if it does not.

The witness should demonstrate a difference in the definitions, not that another system is defective for failing to satisfy a property it does not claim.

## 7. Provenance authentication and the utility argument

There are two distinct issues.

### Provenance uncertainty

If provenance is unauthenticated or too coarse, a conservative system may need to attribute a datum to many possible authors. That can unnecessarily enlarge Principal Context and reduce utility.

Authenticated, appropriately chunked/object-level provenance reduces this unnecessary loss by identifying the real source of each input component.

### Genuine low-authority influence

Once an external sender/source is accurately identified, authentication does not grant that source organisational authority. If the external principal lacks permission for the proposed action, core ITES should still block the action.

This is not provenance failure. It is the intended zero-trust authority floor.

Thus:

> Authentication makes the security decision accurate; it does not make the decision permissive.

## 8. Utility recovery

There are at least three distinct mechanisms:

1. **Fine-grained authenticated provenance:** avoid unnecessary contamination from unrelated authors.
2. **Planning optimisation:** order and isolate subtasks so that sensitive/low-authority inputs are only observed by executions that actually require them; avoid pulling unnecessary sources into a shared Principal Context.
3. **Explicit authority-changing mechanisms:** delegation/approval/declassification when the organisation intentionally wants a low-authority principal to trigger a higher-authority operation.

A fourth mechanism is model-side planning protection, exemplified by CaMeL's architecture: protecting the plan/control flow from untrusted data can improve empirical utility under attack by reducing the probability that the model selects an attacker-intended branch. This is complementary to, not a replacement for, ITES's authority enforcement.

The paper should clearly separate:

- security-preserving task decomposition and observation ordering;
- empirical robustness improvements from protected planning;
- genuine authority expansion through trusted delegation.

## 9. Worked example required by the paper

Use an authenticated external email/calendar example:

Alice asks the assistant to read an incoming supplier email and create the requested meeting.

- The email sender is authenticated as `Supplier`.
- The relevant email content influences the calendar action.
- Principal Context becomes `{Alice, Supplier}`.
- If Supplier lacks the ACS permission for the concrete calendar operation, ITES blocks it.
- If Supplier and Alice share that permission, the action remains allowed.
- Better provenance cannot manufacture authority; explicit delegation or an organisational policy change is required to intentionally expand the allowed action set.
- If the original message contained unrelated content from other sources, fine-grained chunk provenance can prevent those unrelated sources from unnecessarily contaminating the action context.

This example should be presented as the cost of the zero-trust floor, not as a bug.

## 10. Persistent provenance and the laundering hole

For ordinary derived objects:

    PC(derived_object) superset PC(execution_that_derived_it)

For scheduled future executions:

    PC(scheduled_execution) includes PC(context_that_created_or_controlled_schedule)

unless a separately trusted, explicitly modelled operation changes the context.

This prevents an attacker from using a tainted execution to schedule a "fresh" clean execution and thereby laundering influence.

The implementation and tests must cover:

- persistent storage;
- summaries and derived objects;
- delayed retrieval;
- scheduled executions;
- new assistant calls/sessions;
- cross-component hand-off.

## 11. Residual harm

ITES guarantees authority safety, not correctness of authorised intent.

An adversarial model operating under a clean context may still choose a harmful action that the ACS already authorises. Similarly, if the ACS grants excessive authority, ITES preserves that authority.

The paper should distinguish:

- authority safety;
- intent/safety within authority;
- adequacy of the underlying ACS.

That distinction is a strength, not a weakness: it defines exactly what ITES guarantees.
