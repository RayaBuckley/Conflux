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

Symbolic backends, reductions, hyperproperties, planning, and implementation
conformance are future stages and are not implied by native bounded results.
