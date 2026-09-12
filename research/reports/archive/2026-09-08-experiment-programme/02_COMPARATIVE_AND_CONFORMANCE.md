# Comparative defence and implementation-conformance experiments

## Experiment C1 — Comparative finite-model property matrix

### Goal

Compare ITES, Dual-LLM, CaMeL, Progent, and PACT under explicitly separated properties.

### Critical framing

Do not test every system only against the ITES privilege-escalation property and call failures security failures. For each system record:

- its native security property as represented by the source paper/code;
- ITES authority-confinement/PE property;
- confidentiality/read-safety property where representable;
- whether model/planner behaviour remains in the trusted base;
- whether the result is about a finite abstraction or the real implementation.

### Source-validation requirement

Before running the comparison, create a model-validation note for each external defence containing:

- pinned paper/version/repository commit;
- exact source passages or code paths that justify each transition rule;
- unsupported features omitted from the abstraction;
- native property definition;
- known mismatch risks;
- reviewer sign-off checklist.

Do not let the AI coder infer undocumented semantics from a high-level description.

### Test families

Use small, interpretable scenarios designed to separate properties:

1. untrusted data influences an action authorised only for requester;
2. planner chooses a privileged branch without reading untrusted data;
3. authority-bearing argument is attacker-controlled;
4. benign multi-step task whose next action depends on retrieved content;
5. confidential data influences an output with restricted audience;
6. tool output carries external provenance distinct from agency principal.

For each scenario, run every model under its native property and PE property.

### Output

Produce a matrix with cells from:

- `SAFE`;
- `UNSAFE` + shortest counterexample;
- `BOUNDED_SAFE`;
- `UNKNOWN`;
- `NOT_APPLICABLE`.

Every `UNSAFE` cell must include the property violated and why that property is or is not native to the defence.

### Acceptance criterion

No prose claim may say "X is insecure" solely because it violates a non-native property. Use wording such as "property Q does not imply property P under this finite abstraction".

---

## Experiment C2 — ITES implementation-to-IR conformance

### Goal

Establish that executable ITES transitions are represented faithfully by the verification IR.

### Required architecture

Do not create a second semantic implementation. Add an instrumentation/conformance layer around the existing canonical kernel.

For each deterministic scenario:

1. construct the same canonical starting state for runtime and IR;
2. execute one proposed transition through the actual ITES kernel;
3. project the runtime event/state into the IR representation;
4. compute allowed IR successors;
5. assert that the observed runtime successor is admitted;
6. where semantics are deterministic, assert exact equality after canonical projection;
7. repeat across the reachable finite state graph.

### Scenario coverage

Include:

- allow and deny;
- empty/unknown PC;
- nested execution;
- sibling isolation;
- read checks;
- visibility projection;
- consent deny;
- authority-bearing arguments;
- stale certificate/recheck failure;
- provider failure;
- currently-disabled delegation.

### Generated testing

Add property-based generation over small finite principal/resource/action domains. Generation must be deterministic under a retained seed. Shrink failing cases where possible and store the minimal mismatch fixture.

### Mutation controls

Introduce test-only mutants or monkeypatched transition variants to show the conformance harness catches mismatches. Do not mutate production code in the evidence commit.

### Metrics

Report:

- states compared;
- transitions compared;
- mismatches;
- mutation-detection count;
- unsupported projection cases;
- runtime.

### Acceptance criterion

A publishable conformance claim requires zero unexplained mismatches across the declared supported subset and positive detection of seeded semantic discrepancies.
