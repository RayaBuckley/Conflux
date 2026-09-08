# Planning experiments

## Core hypothesis

Planning can recover utility by changing the order and isolation of subtasks so that unnecessary principals or data do not enter the active Principal Context. Planning must never grant authority; every runtime action remains re-authorised by ITES.

## Experiment P1 — Planning mode comparison

### First step for the coder

Inspect the existing four-mode planning experiment and its aggregator. Reuse current mode names and data structures where possible. Do not create a parallel experiment framework.

The conceptual arms should cover these behaviours, even if the repository uses different names:

1. reactive/no planning baseline;
2. plan-first execution;
3. isolated-subtask planning;
4. authority/contamination-minimising planning.

If current modes differ, map them explicitly in the experiment report.

### Task suite design

Create a deterministic synthetic suite plus a model-backed suite.

#### Synthetic tasks

Build task families where the optimal order is known:

- read low-authority external data only after completing an independent privileged action;
- isolate a low-authority analysis subtask whose result is not needed for a privileged branch;
- choose between two data sources with different provenance footprints;
- avoid irrelevant confidential input;
- complete two independent branches whose contexts should not contaminate one another;
- tasks where no ordering can recover utility because low-authority influence genuinely determines the privileged action.

The last family is essential as a negative control.

#### Model-backed tasks

Use a model that passes structured-plan qualification. The existing 1.5B pilot is a pipeline smoke test only and should not be used for efficacy conclusions.

### Metrics

Per task and mode retain:

- task success;
- secure task success;
- blocked goal actions;
- unsafe executed actions (must remain zero under ITES);
- maximum Principal Context size;
- mean Principal Context size at effectful actions;
- number of distinct principals introduced;
- number of observed artefacts;
- sensitive artefacts observed;
- unnecessary observations relative to the task oracle/fixture definition;
- model calls;
- tool calls;
- plan-generation failures;
- replans;
- tokens;
- latency;
- plan length;
- runtime verification failures.

### Authority-footprint score

Add a transparent, non-security metric, for example:

`authority_footprint = sum_over_effectful_steps(|PC(step)|)`

Also retain the raw PC sizes so the headline result does not depend on one arbitrary composite score.

### Security control

For every generated plan:

- execute through the real ITES kernel;
- re-authorise every action at action time;
- reject any planner-supplied authority/provenance narrowing;
- retain the exact certificate/recheck outcome.

Seed adversarial plan variants that attempt to:

- omit a principal from PC;
- change an argument role;
- reuse a stale certificate;
- move a privileged action after contamination;
- introduce a new tool not in the authenticated catalogue.

All must fail closed.

### Statistical design

For deterministic synthetic tasks, report exact paired differences. For stochastic model planning, use repeated seeds and paired task instances. Bootstrap confidence intervals are acceptable for task-success deltas if sample size is sufficient; retain raw rows regardless.

### Primary result

The strongest result would be:

- planning increases secure task completion or reduces false blocking;
- it decreases unnecessary observations/PC footprint;
- authority violations remain zero because planning cannot bypass ITES.

If utility does not improve, retain that result and inspect whether tasks are genuinely unrecoverable under the current authority semantics.

---

## Experiment P2 — Error/recovery planning

### Goal

Test whether predeclared recovery strategies improve completion without introducing authority-seeking behaviour after failures.

### Failure outcomes

Model at least:

- NotFound;
- PermissionDenied;
- Timeout;
- TransientFailure;
- MalformedResponse;
- PartialEffect;
- Conflict.

### Safe recovery actions

Allow only predeclared transitions such as:

- stop;
- retry within a bound;
- use a lower-authority alternative;
- request approval/delegation without immediately gaining authority.

### Negative controls

Seed plans where `PermissionDenied` triggers credential search, stronger-principal substitution, or an administrator tool. These must be rejected unless a separately authorised delegation transition exists.
