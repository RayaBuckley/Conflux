# Visibility Tracking for Confidentiality Checking

## What this direction is

Visibility tracking records which principals can observe which actions, outputs, states, and intermediate results. It goes beyond read access to model what becomes visible to whom at each stage of execution.

This is the right foundation for confidentiality checking because confidentiality is about observability, not only about possession of input data.

## Why it matters

The existing ITES story already checks whether an execution is allowed to read the data it consumes. That is useful, but it is not enough for a strong confidentiality analysis.

A system can satisfy a read rule and still leak information through:
- visible side effects,
- action names,
- error messages,
- approvals,
- denied actions,
- timing,
- choice of retry path,
- tool metadata,
- partial outputs,
- summaries or logs.

That means the confidentiality question should be framed as:
"Who can observe what, and at which point in the execution?"
not simply
"Who could read the input data?"

## Analysis

Visibility tracking should likely be modelled as a separate lattice or relation. An action can be:
- fully visible,
- visible to a subset of principals,
- visible only through abstracted metadata,
- invisible except in the audit trail,
- or visible only after a delay or redaction step.

This enables stronger confidentiality checks than read access alone. For example:

- A principal might be authorised to trigger a workflow but not to see the file contents.
- Another principal might be allowed to see that a payment was approved, but not the rationale.
- A denial might itself be confidential because it reveals a hidden policy or a hidden resource.

The most useful confidentiality analysis will therefore combine:
- input visibility,
- intermediate result visibility,
- action visibility,
- output visibility,
- and policy-decision visibility.

## Rationale

Visibility tracking matters because confidentiality failures often occur through system behaviour rather than through direct data return. If the system is intended to be useful in real organisations, then it must explain and limit what each actor can learn from the agent.

This also makes benchmarking more realistic. Many current evaluations over-emphasise whether a model can be tricked into exfiltration and under-emphasise the more general observability problem. Visibility tracking makes the policy layer and the evaluator closer to actual operational concerns.

## Constraints

Visibility tracking should not:
- be conflated with provenance,
- be inferred only from data authorship,
- depend on the model to self-report what it exposed,
- ignore error channels,
- ignore control-flow leakage.

A visibility model that omits denial and action metadata will be incomplete.

## Open questions

- What is the smallest useful visibility lattice?
- Should visibility be tracked per principal, per role, or per audience class?
- Should the audit trace preserve full visibility detail even when user-facing output is redacted?
- How should partial visibility interact with delegated authority?

## Suggested first increment

Add explicit visibility labels to traces and require confidentiality checks to report leaks through action declarations, blocked actions, outputs, and error/denial paths.
