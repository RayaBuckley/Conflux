# Command-line Interface

Install the package and run `conflux --help`. Core commands are offline and do
not inspect credentials.

```text
conflux demo --scenario examples/basic.yaml --model scripted --output runs/demo
conflux chat --scenario examples/basic.yaml --endpoint https://model.example/v1/chat/completions --model example
conflux sled run --suite examples/basic.yaml --output runs/sled
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

`chat` uses the optional OpenAI-compatible adapter and retains each turn in the
session environment. Every proposed effect uses the same ITES and
certificate-bound executor; Ctrl-C and EOF abort safely. It returns unavailable
when the configured secret or `httpx` extra is absent. Solver-facing `verify`
and `benchmark agentdojo` remain reserved for M7 and M6.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Completed, including runs that securely blocked proposals |
| 2 | Invalid configuration, selection, or unavailable capability |
| 3 | Runtime or infrastructure failure, including `UNKNOWN` verification |
| 4 | Result evidence failed schema validation |

Argparse syntax errors also use code 2. Commands never interpret a security
denial as a runtime failure.
