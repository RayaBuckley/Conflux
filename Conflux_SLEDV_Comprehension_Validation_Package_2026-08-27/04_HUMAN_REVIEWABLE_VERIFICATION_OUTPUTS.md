# Human-Reviewable Verification Outputs

## Objective

Make every SLED/SLED-V result auditable without requiring the researcher to read solver encodings.

## Required report structure

Every result must expose:

### Property
- stable property ID;
- plain-English definition;
- formal expression if available.

### Model
- model ID/version/fingerprint;
- principals;
- resources/actions;
- initial state;
- policy assumptions;
- enabled features;
- explicit omissions.

### Bounds
- depth;
- state;
- transition;
- model-call;
- solver-unrolling bound;
- any planning/continuation bounds.

### Search
- backend;
- unique states;
- transitions;
- duplicates;
- truncation;
- runtime;
- reduction status.

### Verdict
- SAFE / BOUNDED_SAFE / UNSAFE / UNKNOWN;
- one-sentence interpretation specific to this model.

### Claim boundary
Automatically emit “This establishes…” and “This does not establish…”.

Example:

```text
This establishes:
No PE violation exists in the exhausted finite transition system identified by
model fingerprint X.

This does not establish:
- correctness of the ACS;
- correctness of input provenance;
- security of arbitrary deployments;
- fidelity to an external defence implementation;
- implementation conformance unless separately evidenced.
```

### Counterexample
For UNSAFE:
- initial ACS;
- initial provenance;
- numbered transitions;
- Principal Context after each transition;
- policy decision;
- executed effect;
- violating Principal/property;
- witness length;
- whether shortest under BFS model.

## Domain-language rendering

Never expose only variable assignments such as:

`planner_consumed_attacker=True`.

Also render:

> The planner consumed data attributed to Mallory. Mallory lacks permission to send. The model then executed `send`; therefore the Principal-Context PE invariant is violated.

## External-model warning

If fidelity registry status is not validated, every output must contain:

> This is a result about the Conflux abstraction `<model-id>`, not a verified claim about `<external-system>`.

## Implementation recommendation

Create a common `VerificationExplanation` / renderer rather than backend-specific prose. The renderer should consume structured result objects so the JSON and Markdown views cannot diverge.

Add snapshot/golden tests for:
- SAFE;
- BOUNDED_SAFE;
- UNSAFE;
- UNKNOWN;
- unvalidated external abstraction warning.
