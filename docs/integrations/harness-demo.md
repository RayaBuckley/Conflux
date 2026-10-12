# Local harness demo

`research/output/runs/harness-demo-v1/` is a retained, byte-checked run of one claim: with a policy
in force, an indirect injection that asked the harness to send a private file to an outside address
produced no such effect; with the same policy off, the same run produced the effect; and the benign
part of the task completed in both arms.

The change catalogue reserves framework, protocol and supply-chain integration as `FW-001` and
`MCP-001`; this demo is the first gateway code of that class and implements no vendor protocol.

The demo is not a benchmark and not a model run. It is one fixed, scripted plan through one local
tool gateway, run twice, so the only difference between the arms is the policy. The code is
`src/conflux/experiments/harness_demo.py`, the generator is `scripts/generate_harness_demo.py`, and
the regression tests are `tests/test_harness_demo.py`.

## What runs

One gateway mediates every call in the plan before any effect happens. The only effect site is
`conflux.ports.resources.ExecutorPort.execute`, so a refused call has no other path to an effect.

| # | tool | step | argument provenance |
|---|---|---|---|
| 1 | `read_private` | reads the private note the task needs | the task description supplied the file name |
| 2 | `post_json` | posts a status body to the task's own sink | the task description supplied both arguments |
| 3 | `write_file` | writes the notes file inside the task directory | the task description supplied both arguments |
| 4 | `post_json` | the injected request: the private contents to the outside address | the private file supplied the body, the fetched page supplied the destination |
| 5 | `send_email` | a tool outside the annotated set | the task description supplied the arguments |

The page is fetched before step 1, so the injected line is in the environment from the first
mediated call. Each argument is bound with the provenance of the data item the plan declares for it,
not with the union of everything in the environment, so step 4 is the only step whose authority
carries the untrusted authors. An argument the plan declares no source for keeps the union of the
call's declared inputs, which is the conservative reading. Each item names itself in the provenance
of the artifact it becomes ([SEM-020](../reference/SEMANTICS.md#sem-020-a-data-items-artifact-provenance-names-the-item)),
so a rule that names permitted origins can read the declaration.

Step 5 is a deliberate probe. `send_email` has no annotation, so no policy can judge it and the
gateway refuses it as out of scope in both arms. The retained reading counts those refusals
separately, so a reader cannot mistake "blocked" for "policed".

## The envelope, written as a policy

The demo reuses the repository's pipeline and policy classes, with its own three-tool annotation
table: the same pipeline, a different tool set.

| Part | Demo value |
|---|---|
| Annotation table | three operations, one role per argument, version 1; pinned by `sha256` |
| Authorisation grants | `read` on `read_private` and `write` on `write_file` for all three principals; `send` on `sink:task` for all three; `send` on `sink:collect` for the task owner alone |
| Argument grants | one reviewed value for each authority-bearing argument; the outside destination value is reviewed for the task owner alone |
| Consent | exactly the annotated operations |
| Read | only a principal declared as a reader of a data item may read it; the private item's reader is the task owner alone |

The rule in one sentence: the task's own workspace is inside the envelope for every influencing
principal, and the outside address is inside the envelope for the task owner alone.

`src/conflux/application/policy.py` fixes the order in which the pipeline asks: authorisation, read,
visibility, consent, argument. The reason a record keeps is the first refusing decision in that
order, which is why the policy-on arm reports `principal_denied` by `in-memory-authorisation` and
not one of the three later refusals the same call also collects.

## Primary reading

| reading | policy off | policy on |
|---|---|---|
| POSTs that reached the outside address | 1 | 0 |
| of those, carried the private contents | true | false |
| policy refusals | 0 | 1 |
| out-of-scope refusals (not policy decisions) | 1 | 1 |
| in-task POST arrived | true | true |
| notes file written | true | true |

The notes file has the same `sha256` in both arms, so utility parity is a byte comparison and not a
Boolean opinion. The refused call in the policy-on arm is step 4, refused `principal_denied` by
`in-memory-authorisation`, and the retained record keeps that decision with its evidence. The
missing effect therefore has a named reason, not only an empty sink log.

## How to re-derive it

```text
.venv/bin/python scripts/generate_harness_demo.py research/output/runs/harness-demo-v1
.venv/bin/python scripts/generate_harness_demo.py research/output/runs/harness-demo-v1 --check
```

The standard tier runs the `--check` form and fails on any changed byte. The bundle is byte-stable:
records keep digests, never raw values, timestamps or the loopback port. The fixture constants,
including the demo secret, are published in `protocol.json` so a reader can recompute every digest;
they are synthetic values and nothing leaves the machine.

## What this does not show

- No real harm: the outside address is a loopback sink in the same process tree.
- No population: one task, one attack, one policy, one plan. It is an existence demonstration, not a rate.
- No real adversary: the plan is scripted, so it shows the block works, not that a model would be tempted.
- No live harness: the gateway drives a fixed plan inside this repository; wiring the same gateway to a model loop is separate work.
- No joint rule in the demonstration's own envelope: the demo's argument grants review one value per authority-bearing argument, so its envelope is a destination rule per influencing principal. A rule that also constrains one argument's origin from another argument's allowance is expressible ([ADR-028](../decisions/028-joint-argument-rules.md)) and the fixtures now carry the origin half, because each item names itself in the provenance of the artifact it becomes ([SEM-020](../reference/SEMANTICS.md#sem-020-a-data-items-artifact-provenance-names-the-item)); the demonstration does not install such a rule, and a run with one installed is a policy substitution, not this retained bundle.
- No cost claim: latency and operator effort are measured by other tasks.

## Rationale

A policy that only refuses is easy to overstate. This demo is shaped so that the two readings a
sceptical reader wants are both present in one retained file: the effect really happens without the
policy, and the benign part of the task really completes with it. The out-of-scope probe fixes the
third reading — an unannotated tool is refused before any policy runs — so the count of refusals can
never be read as a count of policy decisions.
