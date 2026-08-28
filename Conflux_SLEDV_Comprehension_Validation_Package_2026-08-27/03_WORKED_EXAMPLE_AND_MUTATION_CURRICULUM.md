# Worked Example and Mutation Curriculum

## Objective

Turn SLED-V from an opaque verifier into a tool whose output the researcher can predict.

## Canonical tiny scenario

Use exactly one simple scenario throughout the first tutorial:

- Alice is the requester.
- Alice is authorised for `read` and `send`.
- Mallory is authorised for `read` only.
- Alice's request initially influences the execution.
- The execution reads Mallory-authored content.
- Principal Context becomes `{Alice, Mallory}`.
- The LLM proposes `send`.
- Correct ITES blocks `send`.

Do not introduce delegation, visibility, consent, planning, dynamic code, confidentiality hyperproperties, or multiple resources in this first example.

## Manual derivation

Produce a table:

| Step | Event | Principal Context | Effective authority | Proposal | Outcome |
|---|---|---|---|---|---|
| 0 | initial request | {Alice} | {read, send} | — | continue |
| 1 | read Mallory content | {Alice, Mallory} | {read} | — | continue |
| 2 | propose send | {Alice, Mallory} | {read} | send | block |

State the PE invariant in plain English and symbolic shorthand.

## Five representations

The coder must render the same scenario in five layers.

### Layer 1 — handwritten semantics
No code. Show the state changes and authority intersection.

### Layer 2 — native SLED
Identify:
- state type;
- transition expansion;
- invariant check;
- visited-state/canonical-state logic;
- counterexample reconstruction.

### Layer 3 — Verification IR
Print:
- variables and sorts;
- initial values;
- transition rules;
- guards;
- assignments;
- invariants;
- configured bounds.

Then annotate every IR item with the handwritten concept it represents.

### Layer 4 — reference interpreter
Show the reachable states in BFS order and which transitions produced them.

### Layer 5 — Z3 BMC
Explain the encoding conceptually:
- state variables at time 0, 1, … k;
- transition constraints between adjacent times;
- assertion that some invariant is violated;
- SAT => counterexample exists within bound;
- UNSAT => no such counterexample within that bound.

Do not dump solver internals unless placed in an appendix.

## Mutation curriculum

Before executing each mutant, create a prediction file containing:
- expected verdict;
- expected shortest witness;
- reason.

Required mutants:

### M1 — requester-only authorisation
Bug: check Alice only.
Expected: send executes after Mallory influence; PE counterexample.

### M2 — permission union
Bug: effective authority is union instead of intersection.
Expected: Mallory borrows Alice's `send`.

### M3 — stale Principal Context
Bug: reading Mallory data does not update context.
Expected: `send` remains allowed.

### M4 — empty-context authority
Bug: empty Principal Context authorises actions vacuously.
Expected: an effect can execute without an accountable Principal.

### M5 — sibling influence leakage
Bug: one branch's Principal Context contaminates another.
Expected: demonstrate either incorrect blocking or an authority/provenance invariant violation, depending on exact semantics.

For every mutant:

1. researcher writes/predicts witness first;
2. native SLED is run;
3. reference IR checker is run where supported;
4. Z3 is run where supported;
5. compare actual witness with prediction;
6. document discrepancies rather than altering predictions after the fact.

## Why prediction-first matters

If the expected answer is written only after running the verifier, the exercise proves little about researcher understanding. Prediction-first creates an independent human oracle for tiny cases.

## Output artifact

Create:

`research/output/runs/sledv-comprehension-v1/`

containing:
- `scenario.md`;
- `manual-derivation.json`;
- `predictions/`;
- `native-results/`;
- `ir-results/`;
- `z3-results/`;
- `comparison.md`;
- checksums and implementation commit.
