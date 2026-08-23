# GLM Synthesis Brief

## Goal

Use these supporting drafts to improve reviewer onboarding and accelerate evidence production without creating competing sources of truth.

## First action: inspect the repository

Before editing anything:
- read root README;
- read docs index;
- read canonical security model;
- read SLED/SLED-V documentation;
- read STATUS and CLAIMS;
- inspect current architecture and verification packages;
- inspect experiment/result conventions;
- inspect AGENTS/AI-development guidance.

Report any disagreement between these drafts and the current repository.

## Documentation task

Evaluate:
- `docs/research/RESEARCH_OVERVIEW.md`
- `docs/research/RESEARCH_QUESTIONS.md`

against canonical docs.

Desired outcome:
- preserve them as reviewer-facing summaries if useful;
- replace stale statements;
- add links rather than duplicating normative details;
- add a short "research reviewer / 10-minute path" to the root README or docs index if consistent with repo style.

Do not reorganise the source tree merely for reviewer friendliness.

## Research/formal task

Evaluate:
- `reports/analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md`
- `reports/analysis/COMPARATIVE_DEFENCE_VERIFICATION.md`

Then produce a concrete technical specification for the smallest implementation that can test:

    Is ITES equivalent to the maximally permissive controller satisfying PE?

Requirements:
- formal property;
- supported finite fragment;
- explicit assumptions;
- negative controls;
- solver/backend choice;
- machine-readable result;
- human-readable counterexample;
- tests;
- no claim inflation.

Do not implement a new verification framework if the current SLED-V IR/backends already provide the necessary primitives.

## Evidence task

Use `RESULTS_AND_EXPERIMENT_PLAN.md`.

Priority:
1. recover and normalise the existing AgentDojo run;
2. commit/preserve reproducible evidence;
3. reproduce original SLED environments under current state exploration;
4. obtain one clean verification result and defective-control counterexample;
5. investigate controller synthesis;
6. only then model external defences.

## External-defence rule

Do not write a CaMeL/PACT/Progent model from memory.

For any comparative model:
- pin primary paper/version;
- inspect available implementation;
- document abstraction;
- encode the defence's own intended property where feasible;
- validate the model;
- phrase Conflux-property counterexamples as property differences unless they actually contradict the external defence's own claim.

## Completion criterion

Prefer one evidence-producing vertical slice over additional architecture.

A task is complete only when it leaves:
- code/specification;
- tests;
- reproducible command;
- raw/machine-readable evidence;
- documented assumptions;
- updated claims/status where appropriate.
