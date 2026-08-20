# Evaluation Negative Controls

The controls in `conflux.evaluation.defences` are deliberately vulnerable
decision engines used only to validate that an evaluator can find known
failures. They are not production policies and are not re-exported from the
top-level evaluation API.

| Control | Deliberate defect |
|---|---|
| `NoDefence` | Allows every independent decision |
| `UnionPermissions` | Allows when any influencing Principal has authority |
| `InitiatorOnly` | Discards every Principal except the deterministic initiator |
| `LatestInputOnly` | Evaluates only the latest input and its provenance |
| `NoReadCheck` | Replaces the read decision with allow |

Each control has a one-transition retained SLED counterexample. The same
fixture under canonical ITES is `SAFE`. This is evaluator evidence, not a
claim that these small fixtures measure real-world attack prevalence.
