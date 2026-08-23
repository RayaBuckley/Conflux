# Command-line Interface

Install the package and run `conflux --help`. Core commands are offline and do
not inspect credentials.

```text
conflux doctor --json
conflux demo --scenario examples/basic.yaml --output research/output/runs/demo
conflux plan demo --output research/output/runs/plan-demo
conflux plan laptop-smoke --plan research/experiments/manifests/planning-laptop-smoke-v1.json --transformers-config LOCAL_TRANSFORMERS.json --llama-config LOCAL_LLAMA.json
conflux sled run --suite examples/basic.yaml --output research/output/runs/sled
conflux sled delegation --output research/output/runs/delegation-check
conflux report research/output/runs/demo/result.json
conflux chat --scenario examples/basic.yaml --endpoint URL --model MODEL
conflux verify --model research/experiments/suites/sled-coi-v1/safe-noise.json --property safe --backend z3 --output research/output/runs/verify
conflux verify --model MODEL --property PROPERTY --reduce cone_of_influence --output research/output/runs/verify-reduced
conflux benchmark agentdojo translate --config research/experiments/manifests/agentdojo-smoke.yaml --upstream-log FIXTURE --output research/output/runs/agentdojo.json
conflux benchmark agentdojo preflight --model-config research/experiments/local-runs/smollm2-cpu/transformers.json --output research/experiments/local-runs/agentdojo-pilot
conflux benchmark agentdojo run --config PROTOCOL.json --output research/output/runs/agentdojo-pilot --execute-local
conflux policy cedar preflight --bundle research/experiments/manifests/cedar-policy-bundle-v1.json --corpus research/experiments/suites/cedar-differential-v1.json --output research/output/runs/cedar-preflight
```

`demo` validates a scenario, mediates its scripted proposals, executes one
explicitly selected authorised branch in memory, and writes `trace.jsonl`,
`result.json`, and `report.md`. Multiple authorised alternatives require
`--select-branch`; none executes implicitly.

`plan demo` writes a replayable blocked-action/recovery/subplan trace. `sled
run` checks the scenario action set with native bounded properties. `report`
validates result JSON before rendering it. `doctor` reports capabilities
without invoking models, containers, solvers, GPUs, or clusters.

`verify` invokes a supported finite IR backend; unavailable or unsupported
behavior returns `UNKNOWN`. With `--reduce cone_of_influence`, it writes the
reduced result, the original backend result, and a reference comparison. A
backend failure, verdict disagreement, or unliftable witness exits with code
3 rather than promoting a reduced claim. Every output directory also contains
`summary.md`, which states the exact claim strength, bound, reduction counts,
shortest known witness, or actionable reason why no conclusion was reached.
The checked-in models under `research/experiments/suites/sled-coi-v1/` are the canonical
review examples; evidence bundles copy them and retain their hashes.
`benchmark agentdojo translate` strictly
translates one pinned upstream record. Without the fixture it validates the
installed pinned suite, then stops at the explicit live-runner gate. Its
`preflight` command can build a fixed version-two six-cell protocol directly
from a resolved local-model configuration. `run --execute-local` is the only
command that invokes AgentDojo or the model. `chat`
uses the optional OpenAI-compatible adapter but routes every proposed effect
through the same ITES and certificate-bound executor.

`plan laptop-smoke` validates two separately identified local runtimes and
prints the fixed 16-cell matrix without invoking either model. Adding
`--execute-local` deliberately runs both eight-cell halves, writes distinct
backend results plus a combined checksummed bundle, and sets a mandatory human-
review stop. Local protocol creation is described in the
[model integration guide](../integrations/models.md).

`plan compare`, `plan laptop-smoke`, and `benchmark agentdojo preflight`
write `preflight.json` when `--output` is supplied without `--execute-local`.
`sled delegation` runs the canonical disabled-delegation model and its seven
negative controls. `policy cedar preflight` validates and translates the
corpus without invoking Cedar; optional `--binary` hashes the candidate bytes.
`doctor --cedar-bundle BUNDLE [--cedar-binary BINARY]` reports the same pinned
identity check without issuing a policy request. See the
[Cedar integration guide](../integrations/cedar.md).

## Subcommand reference

| Command | Subcommand | Key flags | Description |
|---|---|---|---|
| `demo` | — | `--scenario`, `--output`, `--manifest`, `--select-branch` | Run a scripted scenario and write trace, result, report |
| `sled` | `run` | `--suite`, `--output` | Bounded verification of a scenario action set |
| `sled` | `reproduce` | `--protocol`, `--output` | Native SLED reproduction with negative controls |
| `sled` | `delegation` | `--output` | Canonical disabled-delegation model and 7 mutants |
| `report` | — | `RESULT_JSON`, `--json` | Validate and render a result file as Markdown or JSON |
| `verify` | — | `--model`, `--property`, `--backend`, `--reduce`, `--output` | Formal verification with optional solver and COI reduction |
| `doctor` | — | `--json`, `--local-model-config`, `--cedar-bundle`, `--cedar-binary` | Report local capabilities without invoking models |
| `chat` | — | `--scenario`, `--endpoint`, `--model`, `--principal` | Interactive mediated chat loop |
| `plan` | `demo` | `--output` | Deterministic blocked-action/recovery/subplan trace |
| `plan` | `compare` | `--config`, `--output`, `--execute-local` | Planning comparison matrix |
| `plan` | `pilot` | `--model-config`, `--output`, `--execute-local` | Single-backend CPU planning pilot |
| `plan` | `laptop-smoke` | `--plan`, `--transformers-config`, `--llama-config`, `--output`, `--execute-local` | Dual-backend laptop planning smoke |
| `benchmark` | `agentdojo translate` | `--config`, `--upstream-log`, `--output` | Translate one pinned upstream record |
| `benchmark` | `agentdojo preflight` | `--config`, `--output` | Validate pinned suite and build protocol |
| `benchmark` | `agentdojo run` | `--config`, `--output`, `--execute-local` | Run AgentDojo comparison (requires model) |
| `policy` | `cedar preflight` | `--bundle`, `--corpus`, `--output` | Validate and translate Cedar corpus |
| `model` | `resolve transformers` | `--model-id`, `--revision`, `--output` | Resolve local-transformers model artifacts |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Completed, including securely blocked proposals |
| 2 | Invalid configuration, selection, or unavailable capability |
| 3 | Runtime or infrastructure failure, including `UNKNOWN` verification |
| 4 | Result evidence failed schema validation |

Argparse syntax errors use code 2. Detailed security and utility outcomes are
in result JSON rather than inferred from process success.

## Rationale

The CLI calls the same application services as tests instead of maintaining a
demonstration-only security path. Offline defaults give contributors useful
feedback before optional infrastructure is configured. Machine-readable modes
and stable exit codes distinguish successful defence, configuration problems,
infrastructure failure, and invalid evidence.
