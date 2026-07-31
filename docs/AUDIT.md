# Repository Audit Ledger

| Area | Owner | Required evidence | Risk |
|---|---|---|---|
| `src/conflux/domain` | security values | domain/property tests | provenance or identity drift |
| `src/conflux/ports` | dependency inversion | AST import audit and mypy | authority bypass |
| `src/conflux/application` | use-case composition | policy/integration tests | decision conflation |
| `src/conflux/ites` | sole transition kernel | invariant, branch, trace tests | semantic divergence |
| `src/conflux/evaluation` | SLED verification | checker and mutation tests | overstated bounds |
| `src/conflux/planning` | authenticated dynamic plans | grounding, continuation, sandbox, replay tests | authority laundering |
| `src/conflux/verification` | serialisable formal subset | schema and differential tests | proof overstatement |
| `src/conflux/experiments` | evidence aggregation/jobs | schema, regeneration, resume tests | result omission or duplication |
| `src/conflux/adapters` | external translation | failure and schema tests | external drift |
| `tests` | executable evidence | pytest and coverage | assertion gaps |
| `docs` | human/agent contract | link and terminology audit | claim drift |
| `reports` | immutable research input | change-catalog traceability | unverified sources |
| `paper` | archived artifact | no silent edits | claim divergence |
| `scripts` and CI | validation | cross-platform execution | guardrail drift |

The automated audit parses imports, verifies public boundaries, checks every
report task has one disposition and an existing evidence path, checksum-locks
the new-v2 report and raw AgentDojo fixture, rejects legacy modules, and checks
terminology and local links.
The portable validator also validates all versioned JSON Schemas, exercises the
CLI and deterministic runtime, enforces branch coverage, and verifies that the
built wheel contains its schema data.
Curated smoke evidence is checksum-verified and deterministically regenerated
from its committed manifest during the portable validation gate.
