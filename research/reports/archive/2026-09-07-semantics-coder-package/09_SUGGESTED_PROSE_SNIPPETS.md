# Suggested prose snippets

These are not mandatory verbatim text. They exist to prevent semantic drift during a broad rewrite.

## Overview paragraph

Conflux does not assume that model-level prompt-injection defences are useless. Like security training for employees who read untrusted email, such defences can materially reduce the probability of a harmful decision. Their assurance is empirical: an adaptive input may still cause the model to choose badly. Conflux provides a complementary system-level property. It bounds the machine-enforceable authority available to any decision by tracking the Principals whose information may have influenced it and checking each against the applicable authority policy. A deployment can therefore combine model-level resistance with a hard authority boundary rather than treating them as alternatives.

## Human semantic-policy paragraph

Real organisational policy is often richer than the policy encoded in IAM, RBAC, ABAC, or another PDP. A support employee may have a machine-level `refund` permission while organisational rules require them to decide whether a particular request is legitimate. The employee resolves that semantic condition; the access-control system has not necessarily encoded it. An AI agent may be asked to perform the same role. Conflux does not prove that either decision-maker is correct. Instead, it constrains the authority exposed to that judgement wherever the restriction can be represented structurally.

## Authority-boundary paragraph

A model can be untrusted for authority establishment while still being relied upon for semantic judgement. Conflux never treats a model's assertion that an input is benign as permission to remove its provenance, narrow Principal Context, or grant a new effect. Model-level defences can nevertheless reduce security risk by making inappropriate choices within already available authority less likely.

## Delegation paragraph

Delegation is an explicit change to the authority available to a particular execution, not a way to erase low-privilege influence. Conflux distinguishes the organisation's persistent machine-readable policy (`ACS_explicit`) from the execution-effective relation (`ACS_effective`) obtained after applying valid scoped delegation. The Principal Context remains unchanged; every influencing Principal is checked against the effective relation.

## Planning paragraph

Planning may determine that a task uses a bounded set of privileged choices, and it may represent a delegation that the user has explicitly expressed. The plan itself has no authority. A planner cannot manufacture a grant merely because additional permissions would make a task succeed. Any authority extension must originate in an independently authorised, explicit delegation whose exact scope is subsequently enforced.

## Ephemeral-agent paragraph

Scoped delegation permits an ephemeral workflow in which a lower-privilege caller can initiate a prescribed set of privileged effects without receiving the sponsor's ambient role or credentials. The temporary execution may be constrained by exact resources, arguments, expiry, use count and revocation. This is an application of explicit scoped delegation: Conflux bounds what the temporary agent may choose, while model-level defences affect how reliably it chooses the appropriate permitted action.

## SLED scope paragraph

SLED-V evaluates system-level properties under arbitrary well-typed model proposals. It can check whether authority, provenance, delegation, or disclosure constraints hold in the represented transition system. It does not estimate whether a particular model recognises prompt injection or correctly judges a request's semantic legitimacy. Those questions require empirical model/agent benchmarks and should be reported separately from formal authority evidence.

## Maximality qualification

Principal Intersection is maximally permissive with respect to the Conflux privilege-escalation definition for a fixed represented authority relation and Principal Context. This is not a claim that it is the maximally permissive way to automate every organisational workflow: an organisation may intentionally create additional scoped authority through explicit delegation or rely on a human/model semantic decision-maker for conditions not represented in the machine policy.
