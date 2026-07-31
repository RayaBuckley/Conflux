# AgentDojo integration

Conflux targets AgentDojo package `0.1.35`, Git tag `v0.1.35`, commit
`a75aba7631d3ca5fb7ab938965c97ead2f9ff84b`, and benchmark `v1.2.2`.
`external/agentdojo.lock` is authoritative. AgentDojo is MIT licensed and is
an optional, externally gated integration:

```text
python -m pip install agentdojo==0.1.35
```

The core installation never imports AgentDojo. The versioned adapter checks
the installed distribution version before importing it and rejects every
other version.

## Exact translation

| Upstream 0.1.35 structure | Conflux integration value |
|---|---|
| `TaskSuite.name` | immutable `suite_id` |
| `TaskSuite.benchmark_version` | required to equal `(1, 2, 2)` |
| `TaskSuite.user_tasks` keys | sorted, preserved `user_task_ids` |
| `TaskSuite.injection_tasks` keys | sorted, preserved `injection_task_ids` |
| `Function.name` | preserved authenticated tool ID |
| `Function.description` | tool description |
| `Function.parameters.model_json_schema()` | exact input schema |
| `TraceLogger` suite/pipeline/task/attack fields | preserved result IDs |
| `TraceLogger.injections` and `messages` | retained upstream evidence |
| `TraceLogger.utility` / `security` | native metrics, never conflated |

No alias list or “try several field names” parsing is used. Unknown fields,
missing fields, non-Boolean native results, malformed messages, an unpinned
package, and an unsupported benchmark version fail closed.

The raw fixture in `tests/fixtures/agentdojo/v0.1.35/` is copied without
normalisation from the pinned upstream repository's `runs/` tree. It is a
published upstream run, not a Conflux experiment: its native security failure
is useful parser evidence but does not establish Conflux efficacy.

## Comparative smoke boundary

`experiments/manifests/agentdojo-smoke.yaml` fixes the subset and required
conditions. A live run needs the optional package, a model credential supplied
only through its environment variable, and an explicit operator invocation.
The comparison must retain upstream JSON and report:

- native AgentDojo utility and security;
- Conflux policy blocks, executions, provider failures, context size, and
  provenance annotations;
- setup, model, parser, policy, security, and utility failures separately.

AgentDojo has no organisational Principal Context or access-control data.
Conflux annotations are therefore a declared benchmark augmentation, not
upstream ground truth. No live comparative result is currently claimed.

## Rationale

One exact upstream version and translation is easier to audit than permissive
field probing. Preserving upstream identifiers, raw records, and native metrics
makes translation errors visible and supports later re-analysis. Keeping
Principal Context annotations separate acknowledges that AgentDojo does not
supply organisational access-control ground truth.
