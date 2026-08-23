# Conflux Documentation

## Start here

If you're new to Conflux, read in this order:

1. [README](../README.md) — what Conflux is and how to run it.
2. [Overview](OVERVIEW.md) — plain-language explanation of the problem
   and approach.
3. [Architecture](reference/ARCHITECTURE.md) — how the system is structured.
4. [Security model](reference/SECURITY_MODEL.md) — what it enforces and why.
5. [Status](evidence/STATUS.md) — what's implemented and what's next.
6. [Research overview](research/RESEARCH_OVERVIEW.md) — the research framing.

## Documentation by task

Use this page to enter the documentation by task. Each fact has one canonical
owner; linked documents should reference that owner rather than restating it.

## First run and contribution

- [Root quick start](../README.md): install and run the offline vertical slice.
- [CLI](reference/CLI.md): commands, outputs, failures, and exit codes.
- [Development](DEVELOPMENT.md): setup, testing ladder, and validation.
- [Workflow](AI_AGENT_GUIDE.md): change procedure, review checklist, and commit conventions.
- [Changelog](../CHANGELOG.md): review-level repository history.
- [AI agent guide](AI_AGENT_GUIDE.md): trust order and drift controls.
- [Security policy](../SECURITY.md): trust boundary and private reporting.

## Understand the system

- [Architecture](reference/ARCHITECTURE.md): packages, dependencies, and data flow.
- [Security model](reference/SECURITY_MODEL.md): normative rules and trusted computing base.
- [Public API reference](reference/REFERENCE.md): supported Python and CLI surfaces.
- [Runtime](reference/RUNTIME.md): scenario and provider contracts.
- [Glossary](reference/GLOSSARY.md): canonical terminology.
- [Architecture decisions](decisions/README.md) and
  [feature specifications](specifications/): decision history and accepted work.

## Verification and evidence

- [SLED](reference/SLED.md): native bounded-checking semantics.
- [Evaluation](evidence/EVALUATION.md): result and trace evidence.
- [Negative controls](evidence/NEGATIVE_CONTROLS.md): deliberate defective variants.
- [Smoke result](evidence/MVP_RESULTS.md): bounded pipeline-readiness evidence.
- [Audit](evidence/AUDIT.md): automated repository invariants.
- [Claim ledger](evidence/CLAIMS.md): claim strength and limitations.

## Integrations and research

- [Model integrations](integrations/models.md) and
  [AgentDojo](integrations/agentdojo.md): optional model and benchmark boundaries.
- [Cedar](integrations/cedar.md): pinned local PDP contract and offline preflight.
- [Related work](research/RELATED_WORK.md): positioning, not implementation status.
- [Change catalogue](evidence/CHANGE_CATALOG.md): report-derived work grouped by theme.
- [Status](evidence/STATUS.md): concise current capability summary.
- [Task registry](evidence/task-registry.json): authoritative machine-readable status.
- [Report sources and analysis](../reports/README.md): reconciled historical inputs.
- [Current manuscript](../publications/manuscript/README.md): publication source and evidence policy.

## Research context

- [Research overview](research/RESEARCH_OVERVIEW.md): reviewer-facing problem statement, ITES rule, and Part C direction.
- [Research questions](research/RESEARCH_QUESTIONS.md): prioritised open questions and evidence requirements.
- [Verification backends](integrations/verification.md): optional solver and model dependencies.

## Ownership and rationale

| Question | Canonical owner | Why |
|---|---|---|
| What does the system enforce? | code, tests, schemas, security model | Executable behavior must support the prose contract |
| Why was a design selected? | accepted specification or ADR | Decision history should not be reconstructed from code |
| What is implemented? | `evidence/STATUS.md` and `evidence/task-registry.json` | One human summary and one machine registry prevent drift |
| What may be claimed? | `evidence/CLAIMS.md` and retained evidence | Implementation is not automatically empirical proof |
| What did reports recommend? | `reports/analysis/` | Historical input needs current reconciliation |
| What does the current paper claim? | `publications/manuscript/` | The archived paper is intentionally frozen |

When sources disagree, record and repair the discrepancy. Do not silently
promote a report, manuscript statement, or passing test above the normative
security contract.
