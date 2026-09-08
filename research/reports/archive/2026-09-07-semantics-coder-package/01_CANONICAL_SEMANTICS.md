# Canonical semantics to establish across Conflux

This document is the semantic source for the migration. The coder should create a repository ADR/specification from it before broad edits so that later prose links to one canonical decision rather than rephrasing the concepts independently.

## 1. Three different things currently conflated by "security"

Conflux should distinguish at least three questions.

### 1.1 Authority confinement

Can an execution exercise machine-enforceable authority outside the authority envelope explicitly available to every influencing principal?

This is the property ITES is intended to enforce independently of model behaviour.

For an execution `e`, operation/effect `a`, conservative Principal Context `PC(e)`, and effective machine policy `ACS_effective(e)`:

```text
ITESAllow(e, a) iff
    PC(e) is known and non-empty
    and forall p in PC(e): ACS_effective(e, p, a)
    and all independent argument/read/visibility/consent/certificate checks pass.
```

The exact production relation is parameterised by action, resource, arguments, current policy state, time/context, etc.; the notation above is intentionally compact.

### 1.2 Semantic decision security

Given authority to choose among several permitted effects, does the decision-maker choose an appropriate effect for the real task and context?

Examples:

- Is this customer request legitimate?
- Is this email social engineering?
- Does this complaint justify an exceptional refund?
- Which of several already-delegated actions is appropriate?

These predicates can depend on natural language, incomplete evidence, context, judgement and organisational norms. They may not be fully captured by the explicit machine-readable ACS.

Humans already perform this role. AI agents may perform the same role. Security training helps humans; model-level PI defences, instruction hierarchy, fine-tuning, classifiers, and similar techniques can improve AI decisions. These are real security controls, but they do not provide the same worst-case guarantee as ITES authority confinement.

### 1.3 Policy adequacy / organisational intent

Does the machine-readable authority policy represent all of the organisation's actual intended restrictions?

Usually not perfectly. The organisation's real decision rule may be conceptually closer to:

```text
AllowIntended(p, a, state, input_semantics, purpose, context, ...)
```

while the explicit ACS/PDP captures only the machine-enforceable subset.

Do not call human/model semantic judgement a literal mutation of the persistent ACS unless it actually changes policy state. It is more precise to say that the decision-maker resolves semantic conditions not represented in the explicit ACS.

## 2. Explicit versus effective ACS

Adopt canonical vocabulary.

### `ACS_explicit`

The persistent machine-readable authorisation state supplied by the organisation/PDP. Examples may include RBAC/ABAC/ReBAC/IAM/Cedar-style decisions. It is an external trust assumption/input to the core theorem.

### `D_e`

The set of valid, explicit, scoped delegation grants applicable to execution `e`.

A grant must be independently authorised. Being allowed to perform `a` does not automatically imply permission to delegate `a`; the policy for creating the delegation is itself an authority decision.

### `ACS_effective(e)`

The authority relation evaluated by ITES for execution `e` after applying the explicit policy plus valid execution-scoped delegation.

A compact definition is:

```text
ACS_effective(e, p, a) =
    ACS_explicit(p, a)
    OR DelegatedAllow(D_e, p, a)
```

where `DelegatedAllow` includes resource, argument, beneficiary, issuer, lifetime, use-count, revocation and other scope checks.

Do not imply that delegation overwrites the explicit ACS globally. It creates a scoped effective authority relation for the applicable execution/workflow.

## 3. Authority envelope

Define the authority envelope of an execution as the machine-enforceable set of effects that pass the current ITES authority rule under `ACS_effective(e)` (before additional restrictive dimensions such as consent/visibility if the repo prefers to reserve "authority" for the authorisation dimension).

A precise conceptual form is:

```text
AuthorityEnvelope(e) = {
    a | PC(e) known/non-empty
        and forall p in PC(e): ACS_effective(e, p, a)
        and action/argument authority checks pass
}
```

If the repository already has a more precise operation/resource/argument formalism, use it rather than introducing a parallel implementation type.

Core promise:

> Conflux constrains the maximum machine-enforceable authority available to a decision-maker. It does not guarantee that the decision-maker chooses the best or intended element from that set.

## 4. Model-level defences

Canonical position:

> Model-level defences provide meaningful security by reducing the probability that untrusted inputs cause inappropriate decisions. Their evidence is empirical/probabilistic and can degrade under distribution shift or adaptive attacks. Conflux provides a complementary system-level authority-confinement layer whose core property is defined under arbitrary model proposals.

Consequences:

- Delete/rewrite claims that model-level defences are "only utility".
- Do not say they have "no security value" because they lack guarantees.
- Do not imply Conflux makes them unnecessary in workflows where harmful choices remain inside the authority envelope.
- Keep models/classifiers untrusted for *granting authority* or *narrowing Principal Context*.
- A model may nevertheless be deliberately relied upon for semantic judgement inside an already available authority envelope.

Recommended phrase:

> A model can be untrusted for authority establishment while still being relied upon, probabilistically, for semantic judgement within already granted authority.

## 5. Human analogy

Use this explanatory example consistently:

A privileged employee may read arbitrary external email and then exercise privileged actions. The machine ACS often grants the employee broad action authority and relies on the employee to determine whether a particular email/request legitimately warrants using it. Phishing training improves security but does not prove that every decision is correct.

Replacing the human with an AI agent does not make the semantic decision problem disappear. If the task genuinely requires arbitrary untrusted content to determine a privileged choice, a purely provenance-based layer cannot simultaneously assume worst-case model behaviour and prove that the choice is appropriate. The organisation must either:

- structurally constrain the choice so a hard guarantee is possible;
- explicitly delegate a bounded choice it really intends to delegate;
- rely on human/model semantic judgement with residual risk; or
- disallow the workflow.

Do not present humans as inherently secure. They are another semantic decision mechanism whose reliability is empirical/organisational.

## 6. Delegation semantics

Delegation is not provenance removal. It changes the applicable authority relation explicitly.

Preferred delegation unit: a constrained choice set / predicate over effects, not ambient role transfer.

Examples:

```text
D = {
  refund(order_17, amount <= 42),
  resend(order_17, existing_address),
  escalate(order_17)
}
```

or a typed predicate `phi(a, resource, args)`.

The agent can choose inside `D`; Conflux guarantees that it cannot escape `D` (subject to the rest of the TCB/mediation assumptions). Model-level security then affects whether the agent chooses the appropriate member of `D`.

This gives a clean two-layer statement:

```text
Conflux guarantee: ExecutedAction is inside the explicitly available authority envelope.
Semantic-security goal: the decision-maker selects the appropriate action inside that envelope.
```

## 7. Planning semantics

Planning is not an authority source.

The planner may:

- structure a task;
- compute/represent the actions a workflow may need;
- minimise authority exposure;
- extract a delegation already explicit in the user's request;
- present the exact parsed delegation scope for user verification/confirmation;
- plan execution inside an already authorised delegated choice set.

The planner must not:

- manufacture authority because a task would otherwise fail;
- treat `RequiredAuthority(plan)` as automatically granted;
- silently turn "this plan needs X" into delegation of X;
- drop Principal Context after a trusted-looking plan is created.

If the intended user request itself explicitly delegates a bounded decision, the plan can encode that delegation. If extraction is not sufficiently trustworthy, a human must verify/approve the extracted exact scope before it becomes `D_e`.

This is the important contrast with planning systems where trusted planning/control flow itself is the security boundary: in Conflux the plan is not authoritative merely because it was produced by a planner.

## 8. Ephemeral agents

Treat as an application/property of scoped delegation, not as the core theorem.

A high-authority principal can explicitly delegate a narrow workflow choice set to a temporary execution. The execution can be short-lived, one-use, bounded to exact resources/arguments, and destroyed after completion. The caller does not receive the sponsor's ambient credentials or general role.

Good product/research example, but avoid implying that "ephemeral agent" itself is a new security primitive if it is just a consequence of scoped delegation + mediation.

## 9. Endorsement/trusted-transformation decision

User decision: **remove endorsement as a proposed Conflux mechanism.**

Required handling:

- Delete planned Conflux endorsement/trusted-endorsement mechanisms from normative/research direction prose.
- Do not add an endorsement task or API.
- Classical related-work sections may still explain that IFC literature contains endorsement, provided it is clearly described as adjacent literature rather than an intended current Conflux extension.
- ADR-024 currently contains a "trusted transformation model" and says runtime endorsement is unactivated. Reconcile this: preserve historical rationale if ADR immutability conventions require it, but add a superseding ADR stating that endorsement/trusted transformation is not part of the current planned semantics. If accepted ADRs are editable by repository convention, mark that section superseded rather than silently deleting decision history.
- Current hard semantics should simply retain conservative provenance; any future provenance-reduction exception requires a separate explicit design decision.

## 10. Maximal permissiveness theorem

Do not weaken the existing theorem. Narrow its wording.

Correct claim:

> For fixed `ACS_effective` (or fixed explicit ACS in the base theorem), fixed conservative Principal Context, and the stated Conflux PE definition, Principal Intersection is the maximally permissive controller that prevents PE.

Incorrect overclaim:

> ITES is the maximally permissive safe way to automate every organisational task.

Human/model semantic trust and explicit delegation can make additional workflows acceptable to an organisation; that does not contradict the theorem because the authority relation/security objective has changed or the claim being evaluated is different.

## 11. SLED/SLED-V boundary

SLED-V verifies system-level properties such as:

- authority confinement;
- provenance preservation;
- delegation confinement;
- read/visibility properties supported by the formal model;
- certificate/mediation properties;
- finite or solver-supported invariants.

It should not become the benchmark for whether a model spots prompt injection or correctly decides semantic legitimacy. Use AgentDojo/other empirical benchmark tracks for that.

The repo may report both evidence classes, but must label them separately:

```text
formal/bounded system-level evidence
vs
empirical model/agent security evidence
```
