# AgentDojo integration

Conflux targets AgentDojo package `0.1.35`, Git tag `v0.1.35`, commit
`a75aba7631d3ca5fb7ab938965c97ead2f9ff84b`, and benchmark `v1.2.2`.
`research/experiments/agentdojo.lock` is authoritative. AgentDojo is MIT licensed and is
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
| `TaskSuite.benchmark_version` | required to share the pinned major.minor; the suite's own tag is recorded |
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

## Mediation records

Each mediated call appends one record to a cell's `augmentation` list. The record names the tool, the
call's argument fingerprint, the annotations the call was judged against, and one of three outcomes:
`executed`, `provider_failed`, or `blocked`.

A blocked record also names the rule that refused the call, so a reader does not have to unpack the
retained report to learn why:

| Field | Meaning |
|---|---|
| `reason` | the refusing decision's own reason token, for example `principal_denied` or `read_denied` |
| `policy_id` | the policy that produced the refusing decision, for example `in-memory-authorisation` |
| `policy_dimension` | the decision dimension that refused: `authorisation`, `argument_authorisation`, `read`, `visibility`, or `consent` |

The adapter's own refusals use the same `reason` field with a disjoint vocabulary
(`unsupported_tool`, `unsupported_arguments`), so `refusal_category` still separates an out-of-scope
refusal from a policy decision. Run bundles retained before this field existed record no `reason` on
a policy refusal; `research/output/runs/agentdojo-refusal-record-v1/` holds a small, byte-checked
example a reviewer can re-run without a model or a network. That bundle also retains the refusing
decision itself (`policy_id`, `category`, `reason`) beside the record's three fields, and its
`refusal_matches_the_retained_report` check re-derives the fields from that excerpt, so a reader can
verify the rule from the file alone.

## Recorded assessment verdicts

A record's report summary keeps each security assessment's `verdict` beside its `holds` flag. The two
event-conditioned properties (`no_unauthorised_execution`, `no_unauthorised_authorisation`) read
`not_exercised` when the run produced no event of that kind, `holds` when every observed event
satisfied them, and `broken` otherwise. A cell that refused every call therefore records
`not_exercised` with `holds: false` for both properties and `holds: true` only for the model-call
bound. This matters for counting: across the retained AgentDojo bundles under
`research/output/runs/agentdojo-*`, 132 of the 318 cells that carry a mediation record executed
nothing, and every one of the 318 reported `no_unauthorised_execution` as true, so the flag alone
cannot separate a guard that worked from a guard that was never asked to work. Run bundles retained
before the field existed carry only that flag.

## Refusal reasons in the retained bundles

Before the record copied the refusing rule into its own `reason` field, a blocked call still kept its
whole ITES report, and the refusing decision sits in that report's trace. The retained bundles can
therefore be read offline: `scripts/derive_agentdojo_refusal_reasons.py` walks every
`research/output/runs/agentdojo-*/result.json`, takes the **first denying decision in the first branch
that holds one** for each blocked record that carries no reason, and writes the table to
`research/output/runs/agentdojo-refusal-reasons-v1/`. No model runs and no retained bundle is
rewritten.

Measured on 2026-10-11 over the 21 retained bundles that hold a `result.json`:

| Quantity | Count |
|---|---|
| blocked records | 223 |
| blocked records that already name a reason | 130 |
| blocked records with no reason, listed in the table | 93 |
| of those, a refusing rule was derived | 93 |

| policy_id | dimension | reason | records |
|---|---|---|---|
| `snapshot-read-policy` | read | `read_denied` | 60 |
| `in-memory-authorisation` | authorisation | `principal_denied` | 29 |
| `in-memory-argument-policy` | authorisation | `argument_denied` | 4 |

By tool the 93 rows are 81 `search_emails` and 12 `delete_file` calls. The bundle stores one row per
record (bundle, cell index, record index, tool, and the derived rule), the totals above, and six
self-checks that compare the totals against the rows in the same pass. The standard validation tier
runs the tool with `--check`, which re-derives the table and fails on any byte difference. Each
`result.json` is recorded relative to the runs root, and the runs root relative to the repository, so the
same tree produces the same bundle whichever form of the root a caller passes.

What this does not show: it is not an AgentDojo result, it measures no model, and it says nothing about
how often a policy refuses in a real suite. The historical records keep no `reason` field, so a counter
that reads the record still sees no reason; the rule is recovered by reading the report beside it.

## Six-cell local pilot

The pilot fixes `workspace/user_task_17/injection_task_1`, one seed, and one
repetition. It compares benign and attacked inputs across no defence,
conservative ITES, and oracle ITES. Build and inspect the protocol before any
model invocation:

```text
conflux benchmark agentdojo preflight --model-config research/experiments/local-runs/smollm2-cpu/transformers.json --output research/experiments/local-runs/agentdojo-pilot
```

The conservative profile trusts authenticated human input while retaining an
external or unknown Principal on tool, document, message, and injected
content. The oracle profile uses benchmark ground truth and is a deliberately
non-deployable upper bound. Trusted argument roles are frozen in
`research/experiments/suites/agentdojo-tool-schemas-v1.json`; the small reviewed
selector allow-list is separate in
`research/experiments/suites/agentdojo-annotation-exceptions-v1.json`. Unknown tools,
roles, resources, and unreviewed selectors deny.

The generated `protocol.json` is run only with an explicit gate:

```text
conflux benchmark agentdojo run --config research/experiments/local-runs/agentdojo-pilot/protocol.json --output research/experiments/local-runs/agentdojo-pilot-run --execute-local
```

The comparison must retain upstream JSON and report:

- native AgentDojo utility and security;
- Conflux policy blocks, executions, provider failures, context size, and
  provenance annotations;
- setup, model, parser, policy, adapter, security, tool, utility, and bound failures
  separately, and the failing cell keeps a bounded summary of the message that produced its
  category. An out-of-scope refusal, where the mediator never annotated the tool, is counted
  as `adapter` rather than `policy`.

Benign state begins with only the authenticated human Principal. An injection
Principal is introduced only when injected content actually affects a retained
tool result. AgentDojo has no organisational Principal Context or access-
control data, so Conflux annotations are a declared benchmark augmentation,
not upstream ground truth. No live comparative result is currently claimed.

## Task selection

Breadth runs execute a frozen selection instead of an ad-hoc task list:
`research/experiments/manifests/agentdojo-stratified-selection-v1.json`, written by
`python scripts/select_agentdojo_tasks.py` and checked by `--check` against the
installed benchmark. It takes the lowest user-task id per (suite, injection vector)
stratum, records which suite defaults no task offers, and carries one protocol
`suite` block per suite. The five workspace task ids of the retained pilot cells are
excluded, so a sweep never counts a pair twice.

A protocol's suite comes from the prefix of `suite.id` before the first colon, so
`banking:stratified-v1` produces banking cells and a prefixless id keeps the historical
workspace behaviour. Build a protocol for any pinned suite from the resolved local model:

```bash
conflux benchmark agentdojo preflight \
    --model-config research/output/runs/<run>/transformers.json \
    --suite banking \
    --protocol-suite-id banking:stratified-v1 \
    --task-ids user_task_0,user_task_1 \
    --output research/output/runs/<run>
```

`--protocol-suite-id` records the selection's own suite id verbatim. The stratified sweep passes it,
so a run says `banking:stratified-v1` rather than the preflight's derived `banking:expanded:<task>`
spelling; an id whose prefix names another suite than `--suite` is refused with
`protocol_suite_id_suite_mismatch`.

That command reads the suite's own benchmark tag and injection task ids from the pinned
package and writes one goal per selected task into the protocol.
`suite.injection_task_ids` pairs each selected user task with its injection goal: a single
id applies to every task, a list of the same length pairs positionally, and any other length
is refused with `agentdojo_injection_task_pairing_mismatch` rather than guessed. The
preflight writes the suite's own list when its length matches the selected tasks and
otherwise the suite's lowest id, the same rule the selector applies to strata. The slack and travel
suites tag themselves `v1.2.0` while banking and workspace tag `v1.2.2`; each protocol
records the tag its own suite reports.

A whole sweep is one command: `python scripts/run_agentdojo_sweep.py --suite all --model-config
<run>/transformers.json` reads the frozen selection, preflights and runs each requested suite
(`--suite` repeats, `all` means every suite, and an unknown name is refused), and prints
`cells=… complete=… failed=… utility=… security=…` per suite. Each suite writes to
`research/output/runs/agentdojo-stratified-<suite>-v1/`; the bundles retained on 2026-10-09
(banking, slack, travel, workspace) each carry a `SUMMARY.md`, and
`docs/evidence/VERIFICATION.md` §27 records what they do and do not show. Run the script from an
environment that carries the AgentDojo extras, because the preflight loads the pinned package.

The manifest blocks carry no injection task ids, because the frozen body records only the
strata; take them from the pinned package or from a protocol this command wrote.

## Rationale

One exact upstream version and translation is easier to audit than permissive
field probing. Preserving upstream identifiers, raw records, and native metrics
makes translation errors visible and supports later re-analysis. Keeping
Principal Context annotations separate acknowledges that AgentDojo does not
supply organisational access-control ground truth. Comparing conservative and
oracle annotations makes annotation sensitivity visible instead of selecting
one favourable profile after observing results.
