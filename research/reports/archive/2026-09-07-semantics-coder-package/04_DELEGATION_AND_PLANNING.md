# Delegation, planning, and ephemeral-agent semantics

## 1. Why general delegation is too coarse

A broad grant such as "the agent may issue refunds" exposes much more authority than many tasks need. Conflux should prefer task-scoped, parameter-constrained delegation.

A delegation can be represented as a finite choice set:

```text
D = {
  Refund(order_17, amount <= 42),
  Resend(order_17, address = existing_address),
  Escalate(order_17)
}
```

or a typed predicate over action/resource/arguments.

The security value is attenuation: compromise or bad semantic judgement can choose a bad member of `D`, but cannot escape into unrelated authority if mediation is correct.

## 2. Delegation is an authority transition, not a provenance transition

Never write that delegation "cleans" low-privilege influence.

Before valid delegation:

```text
ACS_explicit(low_user, refund(order_17)) = deny
```

After an authorised scoped grant applies to execution `e`:

```text
DelegatedAllow(D_e, low_user, refund(order_17, <= 42)) = allow
ACS_effective(e, low_user, refund(order_17, <= 42)) = allow
```

`PC(e)` still includes the low user and any other influencing principals. The action is no longer a PE relative to the *effective* authority relation because the authority transfer was explicit and authorised.

## 3. Issuer authority

A grant must itself be authorised.

Do not assume:

```text
CanPerform(issuer, a) => CanDelegate(issuer, a)
```

A production policy may require a separate `delegate` permission, role, purpose, approval chain, resource restriction, or organisational rule.

## 4. Planning must not manufacture authority

This is critical.

The planner can calculate:

```text
RequiredAuthority(plan)
```

but that set has no authorising force.

A failed task does not create delegation. A planner saying "I need admin access" does not create delegation. A model inventing an approval does not create delegation.

Authority exists only if an authorised principal explicitly delegates it under the accepted delegation protocol.

## 5. What "delegation as part of planning" should mean

The user's intent is narrower than a generic permission-request planner.

When a principal explicitly says something semantically equivalent to:

> choose which of these three approved actions to take for this task

planning can:

1. identify the bounded actions/resources/argument domains that were explicitly delegated;
2. construct a proposed `DelegationGrant` / delegated choice set;
3. show/record the exact scope;
4. require whatever authentication/confirmation the final activation design specifies;
5. execute the plan under that exact scope only.

If the user did **not** explicitly delegate additional authority, the planner must not convert task necessity into an authority request and then treat approval of "continue" as delegation.

The repo can still support a UI that informs the user why the task is blocked, but that is not semantically equivalent to an explicit delegation statement unless the user subsequently makes one.

## 6. Comparison with CaMeL-style planning

Avoid caricatures. The intended Conflux distinction is not that CaMeL has planning and Conflux does not.

The useful distinction for current Conflux semantics is:

```text
Planner output is untrusted structured data.
Planner output does not establish authority.
Explicit authorised delegation establishes D_e.
ITES then mediates every effect under PC(e) and ACS_effective(e).
```

A plan can be malicious and still fail to expand authority unless a principal explicitly grants the relevant scope.

When writing related work, use non-implication/architectural distinction language rather than "CaMeL planning is insecure".

## 7. Authority-minimising planning

This remains useful, but frame it correctly.

If the user has explicitly delegated a class of choices, the planner can prefer the smallest sufficient subset or the plan with the least authority exposure.

Possible objective:

```text
minimise Risk(DelegatedChoiceSet(plan))
subject to task feasibility and user-stated delegation constraints
```

This is a planning/utility/security-hardening objective. It does not create authority.

## 8. Ephemeral agents

A temporary execution can be given a one-task `D_e` and destroyed afterwards.

Example properties:

- exact sponsor/issuer;
- exact beneficiary/execution ID;
- exact operations/resources;
- argument bounds;
- short expiry;
- one use or bounded use count;
- no redelegation unless explicitly allowed;
- revocation;
- certificate-bound execution;
- no ambient sponsor credentials exposed to the low-privilege caller.

This is a strong practical advantage to highlight:

> A low-privilege user can initiate a prescribed privileged workflow without receiving the privileged principal's ambient role or credentials.

But call it an application of scoped delegation/capability attenuation, not an independent formal novelty unless future research establishes otherwise.

## 9. Failure/fallback semantics

If a task is blocked under current hard authority semantics, there is no universal automatic recovery.

The organisation can choose among:

- perform a structurally authorised plan that needs no extra authority;
- use explicit delegation if the principal genuinely intends to delegate a bounded choice;
- rely on a human semantic decision-maker;
- rely on an AI semantic decision-maker with appropriate model-level defences;
- combine AI recommendation and human decision;
- refuse/disallow the task.

Do not impose a universal hierarchy between human and AI semantic judgement. That is an organisational risk decision.
