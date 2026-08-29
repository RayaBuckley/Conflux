# Comparative Defence Model Validation Protocol

## Objective

Define the evidence required before a finite model of an external defence can support a workshop-paper claim.

## Core rule

A model written by the AI coder is a **hypothesis about the defence** until independently validated.

## Validation levels

### L0 — named sketch
Conceptual notes only. No comparative result may be published.

### L1 — source-traceable abstraction
Every state variable, transition, and native property is linked to a primary-source location.

Allowed claim:
“we constructed a source-traceable abstraction of the following supported fragment…”

### L2 — example-conformant abstraction
L1 plus all relevant published worked examples/tests in the supported fragment produce the same allow/block/transition behaviour.

### L3 — implementation-differential abstraction
L2 plus comparison with the reference implementation on a generated/curated corpus.

Report agreement:
- N/N total;
- disagreements;
- unsupported cases;
- version/commit.

### L4 — publication-approved comparative model
Human review confirms:
- supported fragment is relevant to the research question;
- omissions cannot trivially invalidate the comparison;
- native property is stated fairly;
- counterexample is manually inspected;
- wording does not imply more than L1–L3 evidence.

Only L4 may appear as a headline comparative result.

## Source-to-model matrix

For every external model create:

`research/verification_models/<defence>/MODEL_CARD.md`

with a table:

| Model element | Meaning | Primary source | Exact source location | Encoding | Fidelity | Notes |
|---|---|---|---|---|---|---|

Fidelity values:
- exact;
- conservative;
- permissive;
- approximate;
- unsupported.

Every transition rule must have a row.

## Supported-fragment specification

State:
- version/paper;
- trusted components;
- planner assumptions;
- provenance/taint semantics;
- policy semantics;
- argument semantics;
- replanning/error semantics;
- action execution semantics;
- omitted features;
- why each omission is or is not relevant to PE.

## Native property validation

Do not invent a defence's “own property Q” for convenience.

For each property:
- quote/paraphrase the actual paper claim with citation;
- formalise it;
- explain the mapping;
- state whether it is exact or a proxy.

If no clean formal property exists, say so.

## Published-example tests

Extract examples from:
- paper;
- appendix;
- official documentation;
- official tests.

Convert them into fixtures without changing their intended decisions.

Each fixture records:
- source;
- input;
- expected outcome;
- model outcome;
- pass/fail;
- notes.

## Differential testing

Where executable reference code exists:

1. pin repository commit/version;
2. construct scenarios inside the supported fragment;
3. execute reference implementation;
4. execute abstraction;
5. normalise only representation differences;
6. compare security-relevant decisions;
7. retain raw outputs;
8. investigate every disagreement.

Do not silently exclude disagreements.

## Counterexample validation

For each external-defence PE counterexample:

1. manually restate the trace in domain language;
2. identify the exact source rule that permits each transition;
3. check whether an omitted defence mechanism would block it;
4. attempt replay against reference implementation if possible;
5. classify:
   - model-only;
   - source-supported;
   - implementation-reproduced.

## Publication wording

Model-only:
> “Our preliminary finite abstraction admits…”

Source-supported:
> “Within the source-traceable supported fragment, the abstraction admits…”

Implementation-reproduced:
> “The abstract counterexample was additionally reproduced against reference implementation version X under configuration Y…”

Never write “Defence X is insecure” merely because it does not satisfy Conflux PE.
