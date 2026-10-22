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

## Reading paths by audience

The general reading order above suits most readers. These tailored paths
prioritise different entry points for specific audiences:

- **Security researcher**: [Overview](OVERVIEW.md) →
  [Security model](reference/SECURITY_MODEL.md) →
  [Formal semantics](reference/SEMANTICS.md) →
  [SLED](reference/SLED.md) →
  [Claim ledger](evidence/CLAIMS.md) →
  [Related work](research/RELATED_WORK.md)
- **Developer**: [README quick start](../README.md#quick-start) →
  [Architecture](reference/ARCHITECTURE.md) →
  [Concept walkthrough](reference/CONCEPT_WALKTHROUGH.md) →
  [Public API reference](reference/REFERENCE.md) →
  [CLI](reference/CLI.md) →
  [Development](DEVELOPMENT.md) →
  [Runtime](reference/RUNTIME.md)
- **Examiner/reviewer**: [Overview](OVERVIEW.md) →
  [Research overview](research/RESEARCH_OVERVIEW.md) →
  [Security model](reference/SECURITY_MODEL.md) →
  [Status](evidence/STATUS.md) →
  [Claim ledger](evidence/CLAIMS.md) →
  [Contribution provenance](evidence/CONTRIBUTION_PROVENANCE.md) →
  [SLED](reference/SLED.md)
- **AI agent**: [AGENTS.md](../AGENTS.md) →
  [AI agent guide](AI_AGENT_GUIDE.md) →
  [Development](DEVELOPMENT.md) →
  [Formal semantics](reference/SEMANTICS.md) →
  [Security model](reference/SECURITY_MODEL.md)

## Documentation by task

Use this page to enter the documentation by task. Each fact has one canonical
owner; linked documents should reference that owner rather than restating it.

## First run and contribution

- [Root quick start](../README.md): install and run the offline vertical slice.
- [CLI](reference/CLI.md): commands, outputs, failures, and exit codes.
- [Development](DEVELOPMENT.md): setup, testing ladder, and validation.
- [AI-agent guide](AI_AGENT_GUIDE.md): change procedure, review checklist, commit conventions, trust order, and drift controls.
- [Security model](reference/SECURITY_MODEL.md): normative rules, trusted computing base, and operational boundary.

## Understand the system

- [Architecture](reference/ARCHITECTURE.md): packages, dependencies, and data flow.
- [Security model](reference/SECURITY_MODEL.md): normative rules and trusted computing base.
- [Formal semantics](reference/SEMANTICS.md): named invariants, transition rules, and current gaps.
- [Authority and influence proposal](decisions/029-authority-influence-and-policy-checker.md): proposed multi-principal and stateful checker semantics.
- [Policy checker contract](reference/POLICY_CHECKER.md): proposed checker interface, fact schema, verdicts, and justification format.
- [Public API reference](reference/REFERENCE.md): supported Python and CLI surfaces.
- [Runtime](reference/RUNTIME.md): scenario and provider contracts.
- [Glossary](reference/GLOSSARY.md): canonical terminology.
- [Decision records](decisions/README.md): ADRs and feature specifications.

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
- [Report sources and analysis](../research/reports/README.md): reconciled historical inputs.
- [Publication register](../research/publications/README.md): audience and goal of each retained publication.
- [Fourth-year report](../research/publications/manuscript/README.md): progress report for the fourth-year reviewer.
- [arXiv preprint](../research/publications/arxiv/README.md): cohesive international preprint.

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
| What did reports recommend? | `research/reports/analysis/` | Historical input needs current reconciliation |
| Which publication makes which claim? | `research/publications/README.md` and each artifact | Audiences and scopes differ; the archived paper is intentionally frozen |

When sources disagree, record and repair the discrepancy. Do not silently
promote a report, manuscript statement, or passing test above the normative
security contract.
