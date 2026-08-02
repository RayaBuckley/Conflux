# Delegation and Consent

## What this direction is

Delegation is an explicit transfer of authority from one principal to another, usually for a scoped set of actions and resources. Consent is a separate mechanism: it records whether the relevant principal approves a proposed effect at the time it is about to happen.

These are related but not the same. Delegation changes what the system may do. Consent changes whether a specific action should proceed now.

## Why it matters

The current security intuition is conservative by design: every influencing principal must already be authorised for the action. That prevents privilege escalation, but it also blocks legitimate workflows where a low-privilege principal is allowed to act on behalf of a high-privilege one under a constrained arrangement.

Your example captures the distinction well:

- "look at this file then send the money to X" is dangerous because the file may influence the payment without an explicit authority transfer.
- "authorise Bob to send money, then read this file and send money to X" is different because the authority transfer is explicit and happens before the sensitive observation.

That distinction is exactly why delegation should be a first-class semantic object instead of an implicit exception.

The 3rd-year report already identified explicit delegation as future work, and the later review also noted that the project should not silently equate consent with authorisation. fileciteturn0file4 fileciteturn0file0

## Analysis

A delegation should be scoped, auditable, and attenuating. It should say what is being delegated, to whom, for how long, for what resources, and under what conditions.

A useful model is:

- issuer,
- beneficiary or bearer,
- action scope,
- resource scope,
- argument constraints,
- expiry,
- use count,
- revocation handle,
- redelegation permission,
- visibility scope.

The key security property is attenuation: a delegate cannot obtain more than the delegator had, and cannot expand the scope by composing multiple delegated fragments unless that composition is explicitly permitted.

Consent should remain separate. Consent is a runtime decision made by the decision principals or policy layer. Delegation is a standing authority transfer. If they are merged, the system becomes ambiguous about whether an action is allowed because a principal authorised it, because a capability exists, or because the system inferred implied permission.

## Rationale

This direction is important because it recovers legitimate organisational workflows without abandoning the security story. In practice, real work often requires someone to act on behalf of someone else, but only within a narrow scope. Delegation is the structured way to express that.

It also makes the project more realistic. Many systems that claim security still fail on ordinary business cases because they only model "user" and "model" rather than layered organisational authority.

## Constraints

Delegation should not:

- widen authority beyond the issuer,
- persist indefinitely without expiry,
- be generated implicitly from model behaviour,
- erase other principals from the influence set,
- allow arbitrary downstream redelegation unless explicitly allowed,
- replace read visibility checks.

Consent should not be treated as a substitute for delegation or authorisation.

## Open questions

- Should delegation be bearer-style or principal-bound?
- Should the act of granting delegation itself require a separate approval path?
- Should delegated authority survive replanning, retries, and subagent calls?
- How should revocation interact with already-issued plans or queued actions?

## Suggested first increment

Implement one narrow delegation type: a one-use, non-redelegable, resource-scoped authority transfer with a required expiry and full trace evidence.
