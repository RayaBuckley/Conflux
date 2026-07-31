# Command-line Interface

Install the package and run `conflux --help`. Core commands are offline and do
not inspect credentials.

```text
conflux demo --scenario examples/basic.yaml --model scripted --output runs/demo
conflux chat --scenario examples/basic.yaml --endpoint https://model.example/v1/chat/completions --model example
conflux plan demo --output runs/plan-demo
conflux sled run --suite examples/basic.yaml --output runs/sled
conflux verify --model examples/verification.json --backend z3 --output runs/verify
conflux benchmark agentdojo --config experiments/manifests/agentdojo-smoke.yaml --upstream-log tests/fixtures/agentdojo/v0.1.35/workspace-user_task_17-injection_task_1.json --output runs/agentdojo-translation.json
conflux report runs/demo/result.json
conflux doctor --json
```

`demo` validates a versioned scenario, mediates its scripted proposal batch,
executes the sole selected authorised branch in memory, and writes
`trace.jsonl`, `result.json`, and `report.md`. A secure block is a successful
run, not an infrastructure error. If alternatives yield more than one
authorised branch, use `--select-branch`; no branch is executed implicitly.

`sled run` applies the native bounded checker and four canonical properties to
the scenario action set. `report` validates result JSON before rendering it.
`doctor` reports local capabilities without executing cluster, container, GPU,
or external-model commands.

`plan demo` executes the deterministic blocked-action/recovery/subplan example
and writes a replayable plan trace. `verify` loads the serialisable finite IR
and invokes Z3 or nuXmv; a missing or unsupported backend returns `UNKNOWN`.

`benchmark agentdojo --upstream-log` performs strict offline translation of an
exact upstream `TraceLogger` record. Without `--upstream-log`, the command
validates the pinned installed suite before stopping at the explicit live-runner
gate. It never substitutes a generic “AgentDojo-like” schema.

`chat` uses the optional OpenAI-compatible adapter and retains each turn in the
session environment. Every proposed effect uses the same ITES and
certificate-bound executor; Ctrl-C and EOF abort safely. It returns unavailable
when the configured secret or `httpx` extra is absent.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Completed, including runs that securely blocked proposals |
| 2 | Invalid configuration, selection, or unavailable capability |
| 3 | Runtime or infrastructure failure, including `UNKNOWN` verification |
| 4 | Result evidence failed schema validation |

Argparse syntax errors also use code 2. Commands never interpret a security
denial as a runtime failure.
