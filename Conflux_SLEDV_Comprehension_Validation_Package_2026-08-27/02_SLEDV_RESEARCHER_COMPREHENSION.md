# SLED-V Researcher Comprehension Programme

## Objective

Make the existing SLED-V implementation explainable by the researcher without requiring a general formal-methods course.

The programme should teach only the concepts needed to understand and defend Conflux's current verification claims.

## Deliverable

Create:

`docs/tutorials/SLEDV_FOR_PROJECT_AUTHOR.md`

It must be written from the repository outward, not as a generic model-checking textbook.

## Required conceptual ladder

### A. Start from original SLED

Explain the continuity:

- Original SLED enumerated bounded possible LLM/defence behaviours.
- Native SLED now represents security-relevant snapshots as states.
- Transitions represent possible next steps.
- Equivalent future-relevant states can be memoised instead of re-exploring every syntactically different history.
- An invariant is checked over reachable states.
- BFS gives a shortest discovered counterexample in the finite model.

The tutorial must explicitly connect this to the historical 1,462,607-trace experiment.

### B. Define only the essential terms

For every term provide:

1. one-sentence definition;
2. one Conflux example;
3. where it appears in code;
4. what misunderstanding would cause an incorrect claim.

Terms:

- state;
- initial state;
- transition;
- transition relation;
- reachable state;
- canonical/future-relevant state;
- invariant / safety property;
- counterexample;
- breadth-first search;
- finite-state exhaustion;
- bound;
- `SAFE`;
- `BOUNDED_SAFE`;
- `UNSAFE`;
- `UNKNOWN`;
- verification IR;
- reference interpreter;
- solver/backend;
- bounded model checking;
- cone of influence;
- self-composition;
- implementation conformance.

### C. Explain verdict strength

The tutorial must contain a table:

| Verdict | Exact meaning | What it does not mean |
|---|---|---|
| SAFE | finite reachable state space exhausted without violation | deployment security for arbitrary environments |
| BOUNDED_SAFE | no violation before configured truncation | proof beyond the bound |
| UNSAFE | model contains a concrete violating execution | external implementation necessarily has the bug |
| UNKNOWN | checker/model/backend could not establish a verdict | safe or unsafe |

### D. Explain the three correctness layers

This is mandatory:

#### Verifier correctness
Does the checker correctly answer questions about the supplied transition system?

Evidence:
- hand-computable fixtures;
- independent reference interpreter;
- Z3 agreement on supported subset;
- negative controls;
- mutation tests.

#### Model fidelity
Does the transition system accurately represent the system being discussed?

Evidence:
- source traceability;
- published examples;
- differential tests;
- explicit supported fragment;
- omissions.

#### Implementation conformance
Does executable Conflux/external software behave like the model?

Evidence:
- trace replay;
- differential execution;
- reference implementation comparisons.

State prominently:

> Verifier correctness does not imply model fidelity, and model fidelity does not imply implementation conformance.

### E. Explain current advanced features last

Only after the basic model is understood:

- COI reduction;
- Z3 BMC;
- self-composition;
- nuXmv adapter.

For each, answer:
- what problem it solves;
- whether it changes semantics or search;
- what new assumptions it introduces;
- current evidence;
- why it is not needed to understand the core PE invariant.

## Required comprehension checks

At the end, include questions the researcher should answer without looking at the tutorial:

1. Why can original SLED explore many traces that correspond to few future-relevant states?
2. What makes a state canonical?
3. Why does BFS tend to give short counterexamples?
4. What exact extra fact distinguishes SAFE from BOUNDED_SAFE?
5. Why can a correct UNSAFE result be irrelevant to CaMeL?
6. What is the difference between the IR and Z3?
7. Why does agreement between the reference interpreter and Z3 increase confidence but not prove the external model correct?
8. Why is observational confidentiality different from a one-trace safety property?
9. What does COI remove, and why must preservation be checked?
10. What would be required to claim implementation conformance?

Include answers in a collapsible/appendix section.
