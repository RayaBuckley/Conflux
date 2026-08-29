# CaMeL Deep Validation Protocol

## Why CaMeL first

CaMeL is the most appropriate first deep external model because:
- it is central to the historical motivation for ITES;
- the prior project already compared ITES with CaMeL;
- its architecture creates a meaningful contrast between trusted planning/capability/data-flow enforcement and Principal-Context authority;
- validating one model deeply is more valuable than retaining several shallow AI-authored abstractions.

## Phase 1 — Freeze the current model as preliminary

Do not modify it to fit the paper during validation.

Record:
- current model fingerprint;
- current tests/verdicts;
- implementation commit;
- current assumptions.

Rename only to make preliminary status clear.

## Phase 2 — Primary-source extraction

Read the CaMeL paper and official/reference implementation.

Produce:

`research/verification_models/camel/SOURCE_SPEC.md`

Sections:
1. threat model;
2. trusted components;
3. planner/processor roles;
4. capabilities;
5. data-flow/provenance rules;
6. policy checks;
7. tool-call semantics;
8. control-flow semantics;
9. replanning/error handling;
10. published security claims;
11. examples relevant to PE;
12. ambiguous points.

For every item give exact source location.

The AI coder may extract candidates, but the document must contain a `HUMAN_REVIEW` field for every security-critical rule.

## Phase 3 — Compare source spec to current IR

Create a discrepancy table:

| Source behaviour | Current IR behaviour | Match? | Severity | Required action |
|---|---|---:|---|---|

Expected possibilities:
- current IR is accurate;
- current IR is an over-simplification;
- current IR grants behaviours CaMeL would block;
- current IR blocks behaviours CaMeL would allow;
- source semantics are ambiguous.

Do not “fix” ambiguity by guessing.

## Phase 4 — Define CaMeL-PE supported fragment

The model does not need to represent all CaMeL.

Define the smallest fragment sufficient to ask:

> Can a principal whose information influences an authority-bearing decision cause an effect for which that principal lacks ACS permission, while the execution remains admitted by the modelled CaMeL rules?

The fragment must include every CaMeL mechanism that could prevent the candidate counterexample.

If that cannot be established, the PE comparison remains non-publishable.

## Phase 5 — Published-example conformance

Extract all applicable CaMeL examples/tests into fixtures.

Target: 100% agreement for in-fragment cases.

Any disagreement blocks publication approval until:
- model fixed;
- case classified out-of-fragment with justification; or
- source ambiguity documented.

## Phase 6 — Reference implementation differential

If practical:
- pin exact CaMeL implementation commit;
- create a deterministic adapter;
- run a small corpus;
- compare decisions and data-flow/capability state;
- retain raw traces.

Start with 10–30 carefully selected cases rather than hundreds of low-quality generated cases.

Include:
- benign plan;
- untrusted data handled only by processor;
- capability-permitted tool call;
- capability-denied call;
- data-dependent argument;
- attempted control-flow influence;
- replanning/error case if supported;
- proposed PE witness.

## Phase 7 — Human counterexample review

If SLED-V finds a PE counterexample, the researcher must be able to answer:

1. Which Principal is the unauthorised influencer?
2. How did their information enter the relevant decision?
3. Which CaMeL component processed it?
4. Why does CaMeL permit the resulting action under the model?
5. Which exact CaMeL rule supports that transition?
6. Is the behaviour inside the supported fragment?
7. Is there any omitted policy/capability/control-flow mechanism that would block it?
8. Was it reproduced against implementation?
9. Does it contradict CaMeL's own claimed property, or merely show PE is a different property?

## Gate

Do not restore a headline “CaMeL vs PE” result until this protocol reaches at least source-traceable + published-example-conformant status.

If validation reveals the current counterexample is inaccurate, treat that as a successful research result: the validation process prevented an incorrect claim.
