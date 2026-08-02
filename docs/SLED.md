# SLED Native Verification

SLED explores a typed transition system breadth-first, memoises canonical
future-relevant state, retains predecessor edges, and reports a shortest
discovered counterexample.

| Verdict | Meaning |
|---|---|
| `SAFE` | The finite reachable state space was exhausted without violation |
| `BOUNDED_SAFE` | No violation was found, but a configured bound truncated work |
| `UNSAFE` | A safety property failed with a counterexample |
| `UNKNOWN` | Modelling, property, or adapter evaluation failed |

Depth, state, transition, and model-call bounds are explicit. Results retain
unique states, transitions, duplicates, truncation, and counterexample length.
ITES properties cover unauthorised execution, forbidden observation,
provenance preservation, Principal Context monotonicity, branch isolation, and
bounded resource use.

Planning SLED models any schema-valid continuation and worst-case effects
within a generated-code capability envelope. Plan, continuation, effect, and
model-call bounds remain part of the verdict. A shared semantic corpus checks
policy composition against the kernel. Executable defective variants cover
empty-context allowance, permission union, provenance-as-ACL, stale context,
sibling leakage, and rejected-proposal misclassification.

`conflux.verification` is a separate callback-free IR with a reference
interpreter, runtime differential tests, optional Z3 bounded checking, and a
nuXmv Boolean-subset adapter. Its property-scoped cone-of-influence reducer
closes over guards and assignment dependencies, projects synchronous updates,
and preserves rule IDs for witness replay. The comparison API checks original
and reduced reference verdicts and rejects an unliftable reduced witness.
Missing or unsupported backends return `UNKNOWN`. Partial-order reduction,
Principal symmetry, hyperproperties, arbitrary-program proofs, and unbounded
deployment claims remain future work.

## Rationale

Breadth-first search produces small diagnostic witnesses. Canonical state and
deduplication control repeated exploration without erasing distinctions that
can affect later security decisions.

`SAFE` is reserved for an exhausted finite state space. Bounds weaken the
verdict to `BOUNDED_SAFE`, while modelling failures yield `UNKNOWN`; neither is
silently promoted to proof. Native SLED stays close to the operational kernel,
while solver IR stays separate so automation cannot hide abstraction costs.
COI reduction is property-scoped because variables irrelevant to one safety
claim may be essential to another. It is accepted only with explicit
assumptions and original-versus-reduced comparison; a smaller model alone is
not evidence of preservation.
