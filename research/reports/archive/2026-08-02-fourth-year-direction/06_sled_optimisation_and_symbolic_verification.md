# SLED Optimisation and Symbolic Verification

## What this direction is

This direction has two related parts.

First, optimise the current native SLED so it explores fewer equivalent states and traces. Second, create a symbolic or formally verified version of SLED for a restricted transition model where stronger guarantees are possible.

## Why it matters

Native SLED already gives useful exhaustive results on bounded environments, but the state space grows quickly. The earlier report and later review both note that exhaustive exploration is valuable but expensive, and the later review specifically points to the need for reductions and a more formal verification path. fileciteturn0file3 fileciteturn0file1

If Conflux can turn SLED from "bounded exhaustive search" into "reduced state exploration plus symbolic checking", it becomes much more than a benchmark runner.

## Analysis

### Native SLED optimisation

The first target should be semantic reductions that preserve the checked property:

- symmetry reduction over equivalent principals or resources,
- partial-order reduction for independent actions,
- memoisation of canonical state signatures,
- cone-of-influence reduction,
- pruning of semantically identical subplans,
- and explicit handling of branch-isolation semantics.

The goal is not just speed. The goal is to retain the same security verdict while visiting fewer states.

### Symbolic verification

Symbolic verification is only feasible if the defence is expressed as a finite, explicit transition relation. That means:
- no arbitrary callbacks,
- no hidden mutable state,
- no unbounded recursion,
- no unmodelled provider calls,
- no dependence on nondeterministic external services without an outcome model.

A sensible path is:
1. define a restricted verification IR,
2. encode bounded checking in SMT,
3. add induction or a model-checking backend for unbounded safety,
4. export counterexamples and proof artefacts,
5. check conformance between the verified IR and the runtime.

That is a stronger claim than "the code was explored." It becomes "the transition system was proven safe under a precise abstraction."

## Rationale

This direction is one of the best candidates for a real fourth-year contribution because it builds directly on the 3rd-year project while adding a genuinely stronger method.

The project already has the right conceptual elements:
- authoritative semantics,
- provenance,
- branching execution,
- bounded exploration,
- trace recording.

The next step is to reduce the search burden and, where possible, replace exploration with proof.

## Constraints

Symbolic verification should not:
- be claimed for arbitrary Python,
- assume the runtime is equivalent to the verifier without conformance tests,
- blur bounded results into unbounded guarantees,
- or ignore the difference between safety and liveness.

## Open questions

- Which subset of ITES is finite enough for symbolic checking?
- What should be abstracted first: principals, resources, actions, or memory?
- Should the formal backend be Z3-first, nuXmv-first, or both?
- What properties should remain purely empirical?

## Suggested first increment

Implement canonical state hashing and one reduction strategy, then measure the reduction factor on the current benchmark suite before adding any symbolic backend.
