# ADR-029: Authority, influence, and a sound multi-principal policy checker

- Type: adr
- Status: proposed
- Date: 2026-10-22
- Owners: Conflux maintainers

## Context

Conflux already models a conservative Principal Context and checks every
influencing Principal against policy. The current checker is narrower than that
statement suggests. `DecisionEngine.decide` receives a session, action,
context, and environment. It does not receive the branch trace. The policy
dimensions are mostly per-action, with one local joint-argument rule. There is
no general way to express a multi-principal policy, a condition on the whole
Principal Context, or a rule over the order and history of events.

That gap matters for three reasons.

1. **Influence is broader than the model's wording.** Under the threat model,
   every model input is potentially controlling. Retrieved data can choose a
   tool, branch, recipient, loop bound, or plan step just as an instruction can.
   There is no sound general predicate that separates "instructions" from
   "data" inside model input.
2. **Authority is normative, not causal.** Influence says which Principals
   contributed to a proposal. Authority says what the organisation permits.
   Roles and model-based attribution are useful policy vocabulary and audit
   metadata, but neither is a reason to remove an influencing Principal.
3. **Some policies are joint or stateful.** A two-person rule, a separation of
   duties rule, a spending limit that depends on history, and a revocation
   deadline are not conjunctions of independent per-action decisions. A checker
   that cannot see prior events either cannot enforce them or hides state
   outside the certificate.

This record fixes the vocabulary and the minimum soundness conditions for a
future checker. It does **not** claim that the richer checker is implemented.

## Decision

### 1. Define influence and authority separately

- **Influence** is the causal contribution of a Principal's content to the
  proposed action. It includes **data influence** (the value reaches an
  argument or effect field) and **control influence** (the content affects
  which action, branch, plan step, recipient, or parameter is proposed).
- **Authority** is the normative permission of a Principal under the applicable
  policy. Authority is not inferred from influence.
- The **decision context** of an effect `e` and action `a`, written `DC(e,a)`,
  is the set of Principals whose content influenced `a`, together with any
  Principal whose authenticated approval, consent, or joint participation is
  required by policy. If influence cannot be established, `DC` is `unknown`.

The conservative baseline is:

```text
DC(e,a) = unknown
    or every Principal whose content may have influenced a
       is in DC(e,a) and is authorised for a
```

`unknown` is absorbing. It cannot be cleared by a policy allow, a model
explanation, or a role assignment.

### 2. Do not add an instruction/data security predicate

The policy language must not contain a predicate such as `is_instruction(text)`
or `is_data(text)` that can remove a Principal from `DC`. Under the threat
model, data can determine control flow. The only sound exclusion is a runtime
or out-of-band proof that the input could not influence the action, or a
separately accepted trusted-declassification mechanism. Neither exists in
current Conflux.

### 3. Roles and model attribution are advisory

- Roles are authenticated policy vocabulary and audit metadata. A role may
  select a rule or describe why a Principal participates. It must not shrink
  `DC`, substitute for an allow, or turn an unauthenticated actor into an
  authority source.
- Machine-learning attribution may **add** a suspected Principal or set `DC`
  to `unknown`. It may never remove an authenticated Principal or satisfy an
  approval/consent requirement.
- An `unknown` context denies effectful actions even if a model is confident
  about the missing attribution.

### 4. Separate authority policy from trace policy

The checker has two separable layers.

**Authority policy** decides whether `a` is within the authority available to
the Principals in `DC`. It supports:

- **conjunctive per-principal authority:** every `p` in `DC` must receive an
  authenticated allow;
- **joint multi-principal policy:** one predicate over the whole `DC`, their
  authenticated roles and relationships, and any required authenticated
  approvals. A joint rule may require an additional authenticated participant,
  but it may not drop a Principal, invent one, or let a model assert one.

**Trace policy** decides whether the event history satisfies a rule about
order, count, time, revocation, or liveness. It consumes events, not only
proposed actions. The minimum event vocabulary is:

```text
request, propose, approve, dispatch, result, timeout,
revoke, policy_update, plan_step, delegate, skill_load
```

Authority and trace policy may share a checker process, but they must expose
separable justifications. A trace rule must not be hidden inside mutable state
that the decision certificate does not bind.

### 5. Authority-soundness

A checker is **authority-sound** when every `allow` carries a justification
that:

1. names every Principal in `DC`;
2. binds each such Principal to an authenticated allow for the exact action;
3. binds each joint role, relationship, approval, or consent to authenticated
   evidence;
4. names the policy version and any trace-state fingerprint used; and
5. contains no unresolved obligation.

The checker is deny-by-default. Its outcomes are `allow`, `deny`, and
`pending`. `pending` records the missing obligation and is not an allow. A
decision is valid only if revalidation at execution time matches the action
fingerprint, decision-context fingerprint, branch identity, policy versions,
and, when trace policy is used, the trace-state fingerprint.

### 6. State is per branch and replayable

Every branch owns its policy state. Mutable policy state must not be shared
between branches. The state transition must be deterministic and replayable
from the event log. A certificate binds the state fingerprint and policy
version used at decision time. If either changes before execution, the
certificate is stale and execution denies. Revocation is an event with a
generation or epoch; an old grant cannot become valid again by replaying an old
state.

The policy language must remain analysable, decidable where practical, and
deny-by-default. It must not become Turing-complete merely to express one
workflow.

### 7. Third-party skills are untrusted Principals

A third-party skill is both code and content. Installing it is an
authority-granting event; running it is a delegation. Its instructions are
untrusted content, and its code is a separate authority domain. A skill must
declare its capabilities and provenance. The checker must not treat "the skill
is installed" as authority for every effect the skill can request, and the
model must not be able to grant a skill authority by assertion.

### 8. Refinement rule

A future implementation may shrink `DC` or clear `unknown` only when one of the
following is established outside the model:

- a runtime proof that the input could not influence the action;
- a proof that the Principal's authority is already implied by every remaining
  Principal's authority for this effect and no joint rule depends on it; or
- a separately accepted trusted-declassification mechanism with its own
  assumptions, evidence, and proof obligation.

Otherwise the conservative intersection remains mandatory.

## Consequences

- The current per-action checker remains valid for the authority it represents.
  This record does not change current runtime behaviour.
- `DecisionEngine.decide` will need a future interface for policy state and
  trace events, or a wrapper that supplies them explicitly. Hiding them in a
  mutable global would violate branch isolation and replayability.
- `DecisionCertificate` will need to bind the trace-state fingerprint and the
  authority-policy version when trace policy is enabled.
- Tests must cover: unknown absorption; no dropped influencing Principal;
  roles do not reduce `DC`; ML attribution is additive only; `pending` is not
  `allow`; joint approval binds to the exact action; stale state denies; and
  sibling branches do not share state.
- The paper may describe this as the target semantics and as an open
  implementation gap. It must not claim that multi-principal or stateful policy
  checking is already implemented.

## Non-goals

This record does not establish semantic appropriateness, implementation
conformance, side-channel resistance, TOCTOU resistance, argument harm, or
unbounded verification. It does not add LLM judgement to the confinement
decision. It does not make roles a security boundary. It does not claim that
the current code enforces the proposed checker.

## Validation

For this proposal:

- the terms `influence`, `data influence`, `control influence`, `decision
  context`, `authority-sound`, `joint policy`, and `trace policy` are defined
  in `docs/reference/GLOSSARY.md`;
- the conservative intersection and unknown rules are stated in
  `docs/reference/SEMANTICS.md`;
- the current interface gap is recorded in `docs/reference/SECURITY_MODEL.md`;
- no test or result is cited as evidence for an unimplemented checker.

A future implementation must add the tests listed under Consequences and pass
the standard validation tier before the record can move from `proposed` to
`accepted`.
