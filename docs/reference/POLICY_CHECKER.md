# Authority and Influence Policy Checker

- Status: proposed, not implemented
- Date: 2026-10-22
- Related: [ADR-029](../decisions/029-authority-influence-and-policy-checker.md),
  [formal semantics](SEMANTICS.md), [security model](SECURITY_MODEL.md)

This document fixes the interface and fact vocabulary for the checker proposed
in ADR-029. It is a design contract, not a description of current runtime
behaviour. The current checker is pointwise over the represented Principal
Context, with one local joint-argument rule. It does not receive a branch trace
and does not expose a general multi-principal or stateful policy interface.

The purpose of the contract is to make a future implementation reviewable. A
checker that cannot produce the justification described here is not the checker
this design specifies.

## Design boundary

The checker has three inputs that must not be conflated:

1. **Influence evidence** says which Principals contributed to a proposal. It is
   causal. It may be incomplete, in which case the decision context is
   `unknown`.
2. **Authority policy** says what those Principals are permitted to do. It is
   normative. It is derived from authenticated grants, delegations, roles,
   approvals, consents, and the current access-control state.
3. **Trace policy** says whether the event history satisfies an order, count,
   deadline, revocation, or liveness condition. It is stateful and
   event-sourced.

Influence never grants authority. Authority never proves non-influence. A role
is policy vocabulary, not a causal claim and not a security boundary.

## Interface

The checker is a deterministic function of a request, a policy view, and a
trace state. It must not read ambient mutable state.

```text
check(request: CheckRequest, policy: PolicyView) -> CheckResult
```

### CheckRequest

| Field | Meaning |
|---|---|
| `effect_id` | Stable identifier for the proposed effect |
| `branch_id` | ITES branch that owns the proposal and its state |
| `action` | Operation, permission, resource, argument values, and authority-bearing fields |
| `action_fingerprint` | Hash of the exact action, including material arguments |
| `decision_context` | Known Principal set plus influence edges, or `unknown` with a reason |
| `context_fingerprint` | Hash of the decision context and its edges |
| `trace_state` | Opaque per-branch state supplied by the caller |
| `new_events` | Ordered events to apply before deciding, if any |
| `policy_versions` | Versions of the authority and trace policies used |
| `now` | Checker time from a trusted clock, used only for time-bounded rules |

The request must bind the action fingerprint and context fingerprint to the
certificate that execution will check. A request that omits either is invalid.

### CheckResult

| Field | Meaning |
|---|---|
| `verdict` | `allow`, `deny`, or `pending` |
| `justification` | Evidence for the verdict, or the reason for a denial |
| `obligations` | Missing facts for `pending`; empty for `allow` and final `deny` |
| `trace_state` | Updated state after `new_events` |
| `trace_state_fingerprint` | Hash of the updated state and the event sequence |
| `policy_versions` | Versions actually used |

`pending` is not an allow. It records a missing obligation that an authorised
actor or event could still supply. `unknown` influence is a final `deny`, not
`pending`, because a model cannot supply the missing attribution.

## Fact schema

The trusted policy view exposes facts. The names below are a contract, not a
requirement that the implementation use this exact surface syntax.

| Fact | Meaning | Authentication |
|---|---|---|
| `principal(p, kind, status)` | `p` is a known Principal | Directory or session authentication |
| `role(p, role, scope)` | `p` holds `role` in `scope` | Authenticated directory evidence |
| `grant(g, issuer, beneficiary, permission, resource, constraints, epoch, expiry)` | `beneficiary` may exercise `permission` on `resource` | Issuer is authenticated and authorised to grant |
| `delegated(g, parent, issuer, beneficiary, permission, resource, expiry)` | `g` is a scoped delegation of `parent` | Both the delegation and the parent grant are authenticated |
| `influenced_by(effect, p, kind)` | `p` influenced `effect` through `data` or `control` | Provenance or control-dependence evidence |
| `unknown_influence(effect, reason)` | Influence is incomplete | Fail-closed marker |
| `approved(effect, p, approval_id, action_fingerprint)` | `p` approved this exact action | Authenticated approval channel |
| `consented(effect, p, consent_id, action_fingerprint)` | `p` consented to this exact action | Authenticated consent channel |
| `relationship(p, q, kind, scope)` | `p` and `q` have an authenticated relationship | Directory or organisational evidence |
| `revoked(g, epoch)` | `g` is invalid from `epoch` onward | Authenticated revocation event |
| `expired(g, at)` | `g` is invalid at `at` | Clock plus grant expiry |
| `consumed(g, effect)` | A one-use `g` was spent on `effect` | Dispatch event |
| `event(id, branch, seq, kind, actor, subject, at, digest)` | One event in the branch log | Event source and digest |
| `policy_version(dimension, version)` | Policy version in force | Configuration record |
| `trace_state(branch, seq, fingerprint)` | State position and hash | Deterministic replay |

The fact vocabulary deliberately has no `is_instruction(text)` or
`is_data(text)` predicate. Such a predicate would let a policy remove an
influencing Principal by labelling content. The only sound way to remove
influence is an out-of-band proof that the input could not influence the action,
or an accepted trusted-declassification mechanism with its own assumptions.

## Influence and decision context

For an effect `e` and action `a`, the decision context is:

```text
DC(e, a) = { p | influenced_by(e, p, data) or influenced_by(e, p, control) }
```

If any relevant influence is unknown, the context is `unknown`. The
conservative baseline is:

```text
DC(e, a) = unknown
    or every p whose content may have influenced a is in DC(e, a)
       and is authorised for a
```

If isolation is not proven, the whole model input is a control influence on the
whole proposal. A checker that tracks only argument provenance can miss a
data-dependent tool choice, branch choice, recipient selection, or plan step.

Roles and machine-learning attribution are additive only:

- a role may select a rule or describe a Principal, but cannot shrink `DC`;
- an ML attribution may add a suspected Principal or set `unknown`, but cannot
  remove an authenticated Principal or satisfy an approval.

## Verdict semantics

The checker is deny-by-default. It returns `allow` only when all of the
following hold:

1. `DC(e, a)` is known and non-empty.
2. For every `p` in `DC(e, a)`, there is a derivation of an authenticated allow
   for this exact action and resource.
3. Every joint condition required by the policy has authenticated evidence.
4. No negative condition holds: no revoked or expired grant, no consumed
   one-use grant, no failed separation-of-duties condition, no stale policy
   version.
5. The trace policy, if any, accepts the event history and the resulting state
   fingerprint is bound to this action.
6. There is no unresolved obligation.

A missing approval, consent, role fact, or relationship fact normally yields
`pending` when an authorised actor could still supply it. A missing or unknown
influence fact, a failed separation condition, a revoked grant, or an
unverifiable trace state yields `deny`.

## Authority policy

### Conjunctive per-principal authority

The baseline rule is the intersection over the decision context:

```text
allow_action(a) :- forall p in DC(e, a): allow(p, a)
```

Because `DC` is finite, the implementation may compile this into one
conjunction of per-Principal obligations. It must not replace the conjunction
with a single "representative" Principal or with a role-level allow.

### Joint multi-principal policy

A joint rule is one predicate over the whole context, authenticated roles and
relationships, and authenticated approvals or consents:

```text
allow_joint(a) :-
    require_two_person(a),
    role(approver, "approver", resource_scope(a)),
    approved(a, approver, _, action_fingerprint(a)),
    requester(a, requester),
    approver != requester
```

A joint rule may require an additional authenticated participant. That is not
authority amplification if the participant's authority is genuinely part of the
decision. It must not:

- drop a Principal from `DC`;
- let the model or an untrusted skill supply a Principal;
- accept an asserted role without authenticated evidence;
- use an "any Principal" pattern that lets an unrelated actor satisfy the rule;
- use negation to make an unrelated Principal's permission decisive.

The justification must name every joint fact used and every Principal whose
participation was required.

### Policy language shape

The trusted core should be a restricted, deny-by-default language:

- facts and Horn-style rules;
- stratified negation, or no negation in the trusted core;
- finite domains and bounded aggregates;
- no Turing-complete features;
- deterministic evaluation and replay;
- explicit `pending` obligations for missing facts.

A more expressive language is acceptable only if the checker remains
analysable, deterministic, replayable, and authority-sound.

## Trace policy

Trace policy consumes events, not only proposed actions. The minimum event
vocabulary is:

```text
request, propose, approve, dispatch, result, timeout,
revoke, policy_update, plan_step, delegate, skill_load
```

The state transition is:

```text
S(i+1) = step(S(i), event(i))
trace_state_fingerprint = H(branch_id, seq, S(i+1), policy_versions)
```

Rules may constrain order, count, time, revocation, liveness, or one-use
consumption. The state is owned by one branch. Sibling branches must not share
mutable policy state. The certificate binds the state fingerprint and policy
versions used at decision time. If either changes before execution, the
certificate is stale and execution denies.

Revocation is an event with an epoch. A one-use grant is consumed on dispatch
and bound to the effect. Replaying an old event log cannot make a revoked grant
valid again, because the certificate's state fingerprint and policy versions
must match the current state.

## Justification

An `allow` must carry a replayable justification. A `pending` result carries the
same structure plus the missing obligations. A `deny` result carries the failed
condition or the unknown influence reason.

The justification must expose:

- the decision context and every influence edge;
- every per-Principal grant or delegation used;
- every joint role, relationship, approval, or consent used;
- the policy versions and trace-state fingerprint;
- any negative facts that were checked;
- any remaining obligations for `pending`.

Example shape:

```json
{
  "verdict": "pending",
  "action_fingerprint": "sha256:...",
  "context_fingerprint": "sha256:...",
  "principals": ["user:alice", "external:doc-7"],
  "influence_edges": [
    {"principal": "user:alice", "kind": "control"},
    {"principal": "external:doc-7", "kind": "data"}
  ],
  "per_principal": [
    {"principal": "user:alice", "grant": "g-1"},
    {"principal": "external:doc-7", "grant": "g-2"}
  ],
  "joint": [],
  "policy_versions": {"authority": "3", "trace": "1"},
  "trace_state_fingerprint": "sha256:...",
  "obligations": [
    {
      "kind": "approval",
      "required_role": "approver",
      "action_fingerprint": "sha256:..."
    }
  ]
}
```

The example is illustrative. The implementation must not treat a model-generated
explanation as a substitute for any field.

## Worked cases

### Conservative read

A user asks the agent to summarise an email. The email body contains an
instruction to send a file. The decision context for the send action contains
the user and the email author. Both must be authorised for the send. If the
email author lacks that authority, the action is denied. This is the intended
conservative behaviour, even when the user's own authority would allow the send.

### Two-person approval

A transfer requires the requester and an approver. The requester's grant and the
approver's authenticated approval are both in the justification. The approval is
bound to the exact action fingerprint. If the approval is missing, the result is
`pending`, not `allow`. If the approver is the requester, the separation
condition denies.

### Spending limit

A trace rule sums prior dispatches in the branch. If the current amount would
exceed the limit, the action is denied. If the state is missing or does not
replay, the action is denied rather than treated as zero. A manager approval may
raise the limit only through an authenticated policy fact bound to the action.

### Revocation

A grant is revoked at epoch 5. A certificate issued at epoch 4 is stale. The
executor's revalidation compares the certificate's policy version and state
fingerprint with the current values and denies.

### Third-party skill

A skill package declares `read:email`. The user installs it, which is an
authority-granting event. Running the skill is a delegation. An effect that
sends email is outside the declared capability, so it is denied even though the
skill is installed. Skill instructions are untrusted content; skill code is a
separate authority domain. The model cannot grant the skill authority by
assertion.

## Current implementation gap

The current runtime does not implement this checker:

- `DecisionEngine.decide` receives the session, action, context, and
  environment, but not the branch trace;
- the policy dimensions are mostly per-action, with one local joint-argument
  rule;
- `DecisionCertificate` does not bind a trace-state fingerprint or an
  authority-policy version;
- control influence is not separately represented from value provenance.

The current policy remains valid for the decisions it represents. It must not be
described as enforcing the proposed multi-principal, joint, or stateful
semantics until the checker is implemented and tested.

## Required tests for an implementation

An implementation of this contract must cover at least:

- `unknown` influence denies and cannot be cleared by a policy allow or a role;
- adding an influencing Principal cannot increase authority;
- a role or ML attribution cannot remove an influencing Principal;
- every `allow` contains a derivation for every Principal in `DC`;
- a joint approval binds to the exact action fingerprint;
- an approval by the requester fails separation of duties;
- `pending` never executes;
- `deny` is the default for missing or stale policy state;
- sibling branches do not share trace state;
- replaying an old event log cannot revive a revoked or consumed grant;
- a stale certificate denies at execution time;
- a third-party skill cannot exceed its declared capabilities.

## Non-goals

This contract does not establish semantic appropriateness, implementation
conformance, side-channel resistance, TOCTOU resistance, argument harm, or
unbounded verification. It does not add model judgement to the confinement
decision. It does not make roles a security boundary. It does not claim that the
current code enforces these semantics.
