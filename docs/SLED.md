# SLED Native Verification

SLED explores a typed transition system breadth-first. It memoises canonical
state keys, retains predecessor edges, and returns the shortest discovered
counterexample.

| Verdict | Meaning |
|---|---|
| `SAFE` | The finite reachable state space was exhausted without violation |
| `BOUNDED_SAFE` | No violation was found, but a configured bound truncated work |
| `UNSAFE` | A safety property failed and has a counterexample |
| `UNKNOWN` | The model, property, or adapter failed |

Bounds cover depth, states, transitions, and model calls. Results report unique
states, transitions, duplicates, truncation, and counterexample length.
Initial ITES properties cover unauthorised authorisation, forbidden
observation, provenance preservation, and Principal Context monotonicity.
The planning transition system additionally models nondeterministic
schema-valid continuations and worst-case effects permitted by generated-code
capabilities. Plan, continuation, effect, and model-call bounds are retained in
the verdict.
The semantic corpus differentially checks direct policy composition and kernel
outcomes. Test-only defective variants implement empty-context allowance,
permission union, provenance-as-ACL, stale context, sibling leakage, and
rejected-proposal misclassification; SLED finds a one-transition witness for
each.

`conflux.verification` is a separate callback-free IR with a reference
interpreter, runtime differential checks, optional Z3 bounded checking, and a
nuXmv Boolean-subset adapter. Missing binaries and unsupported semantics return
`UNKNOWN`. Reductions, hyperproperties, arbitrary-program proofs, and
unbounded deployment claims remain future stages.
