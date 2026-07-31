# Conflux Documentation

Use this page to enter the documentation by task. Each fact has one canonical
owner; linked documents should reference that owner rather than restating it.

## First run and contribution

- [Root quick start](../README.md): install and run the offline vertical slice.
- [CLI](CLI.md): commands, outputs, failures, and exit codes.
- [Development](DEVELOPMENT.md): setup, testing ladder, and validation.
- [Contributing](../CONTRIBUTING.md): human review and change workflow.
- [Changelog](../CHANGELOG.md): review-level repository history.
- [AI agent guide](AI_AGENT_GUIDE.md): trust order and drift controls.
- [Security policy](../SECURITY.md): trust boundary and private reporting.

## Understand the system

- [Architecture](ARCHITECTURE.md): packages, dependencies, and data flow.
- [Security model](SECURITY_MODEL.md): normative rules and trusted computing base.
- [Public API reference](REFERENCE.md): supported Python and CLI surfaces.
- [Runtime](RUNTIME.md): scenario and provider contracts.
- [Glossary](GLOSSARY.md): canonical terminology.
- [Architecture decisions](decisions/README.md) and
  [feature specifications](specifications/): decision history and accepted work.

## Verification and evidence

- [SLED](SLED.md): native bounded-checking semantics.
- [Evaluation](EVALUATION.md): result and trace evidence.
- [Negative controls](NEGATIVE_CONTROLS.md): deliberate defective variants.
- [Smoke result](MVP_RESULTS.md): bounded pipeline-readiness evidence.
- [Audit](AUDIT.md): automated repository invariants.
- [Claim ledger](CLAIMS.md): claim strength and limitations.

## Integrations and research

- [Model integrations](integrations/models.md) and
  [AgentDojo](integrations/agentdojo.md): optional external boundaries.
- [Related work](RELATED_WORK.md): positioning, not implementation status.
- [Change catalogue](CHANGE_CATALOG.md): report-derived work grouped by theme.
- [Status](STATUS.md): concise current capability summary.
- [Task registry](task-registry.json): authoritative machine-readable status.
- [Report sources and analysis](../reports/README.md): reconciled historical inputs.
- [Current manuscript](../manuscript/README.md): publication source and evidence policy.

## Ownership and rationale

| Question | Canonical owner | Why |
|---|---|---|
| What does the system enforce? | code, tests, schemas, security model | Executable behavior must support the prose contract |
| Why was a design selected? | accepted specification or ADR | Decision history should not be reconstructed from code |
| What is implemented? | `STATUS.md` and `task-registry.json` | One human summary and one machine registry prevent drift |
| What may be claimed? | `CLAIMS.md` and retained evidence | Implementation is not automatically empirical proof |
| What did reports recommend? | `reports/analysis/` | Historical input needs current reconciliation |
| What does the current paper claim? | `manuscript/` | The archived paper is intentionally frozen |

When sources disagree, record and repair the discrepancy. Do not silently
promote a report, manuscript statement, or passing test above the normative
security contract.
