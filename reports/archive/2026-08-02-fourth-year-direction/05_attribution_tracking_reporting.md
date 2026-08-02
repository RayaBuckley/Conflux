# Attribution Tracking Through LLMs

## What this direction is

Attribution tracking records which principals, inputs, documents, tool results, or subagent outputs influenced which model decisions or actions. It is a reporting layer over the influence story.

The goal is not to pretend that the model can provide perfect causal explanations. The goal is to produce conservative, useful attribution for human review.

## Why it matters

If the system is to be reviewable by supervisors, contributors, or organisational users, then people need to understand why an action was declared, blocked, or approved.

Attribution helps answer questions such as:
- which principals influenced this action,
- which data sources were consulted,
- which part of the execution introduced the risky influence,
- which approval or delegation made the action possible,
- whether the action was blocked because of provenance, visibility, or consent.

This is especially important in a project that aims to be understandable to humans as well as usable by AI agents.

## Analysis

Attribution should be conservative. If the model or mediator cannot prove that a principal did not contribute, then the attribution should include that principal rather than omit them.

A useful reporting structure is:

- action,
- declared inputs,
- observed outputs,
- principal context,
- delegated authority in force,
- visible and hidden observations,
- policy decision,
- attribution set,
- explanation category,
- confidence or uncertainty note.

The system should distinguish between:
- actual causal influence,
- conservative influence,
- and user-facing explanation.

That distinction matters because a model-generated explanation is not the same thing as a verified provenance record.

## Rationale

Attribution is valuable because it turns security from an opaque rule into an inspectable story. That is important for:
- auditability,
- supervisor review,
- debugging,
- trust calibration,
- and incident response.

It also supports future work on "reporting to users." If a user asks why an action happened, the system should not answer with a vague natural-language summary alone. It should be able to point to the inputs, policy state, and principal context that justified the decision.

## Constraints

Attribution should not:
- overclaim causality,
- rely on model self-explanation alone,
- erase uncertainty,
- leak hidden data through the explanation channel,
- or conflate influence with permission.

## Open questions

- What is the right minimum attribution granularity: principal, input, tool call, or sub-argument?
- Should attribution be stored as structured data only, with natural-language explanations generated on demand?
- How should attribution handle multiple incomparable causes?
- Should the system record "possible influence" separately from "verified influence"?

## Suggested first increment

Add structured attribution fields to the trace report and generate one human-readable explanation from them for each action class: allowed, denied, delegated, and visibility-blocked.
