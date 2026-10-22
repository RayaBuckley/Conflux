# Conflux Documentation

> **Status:** living · **Owner:** project owner · **Last reviewed:** 2026-10-22
> **Canonical for:** documentation navigation.

This page routes readers to the document that owns their question. The rules for
document status, ownership, and writing style are in
[Documentation policy](DOCUMENTATION_POLICY.md).

## Start here

If you are new to Conflux, read these in order:

1. [README](../README.md) - what Conflux is and how to run one offline path.
2. [Overview](OVERVIEW.md) - the problem, the ITES rule, and what is built.
3. [Architecture](reference/ARCHITECTURE.md) - the packages and data flow.
4. [Security model](reference/SECURITY_MODEL.md) - the normative security rules.
5. [Status](evidence/STATUS.md) - what is implemented today.
6. [Research overview](research/RESEARCH_OVERVIEW.md) - the research framing.

Do not read the claim ledger or the full verification record first. They are
reference material for checking a specific claim.

## Choose by purpose

| Purpose | Start with |
|---|---|
| Learn the idea | [Overview](OVERVIEW.md), then [Concept walkthrough](reference/CONCEPT_WALKTHROUGH.md) |
| Run or install it | [README quick start](../README.md#quick-start), then [Development](DEVELOPMENT.md) |
| Use the CLI | [CLI reference](reference/CLI.md) |
| Check a security rule | [Security model](reference/SECURITY_MODEL.md), then [Formal semantics](reference/SEMANTICS.md) |
| Check what is implemented | [Status](evidence/STATUS.md) |
| Check what may be claimed | [Claim ledger](evidence/CLAIMS.md) |
| Read an ADR | [Decision records](decisions/README.md) |
| Read a paper or report | [Publication register](../research/publications/README.md) |
| Change the code with an AI agent | [AGENTS.md](../AGENTS.md), then [AI agent guide](AI_AGENT_GUIDE.md) |

## Reading paths by audience

- **Security researcher:** [Overview](OVERVIEW.md) ->
  [Security model](reference/SECURITY_MODEL.md) ->
  [Formal semantics](reference/SEMANTICS.md) ->
  [SLED](reference/SLED.md) ->
  [Claim ledger](evidence/CLAIMS.md) ->
  [Related work](research/RELATED_WORK.md)
- **Developer:** [README quick start](../README.md#quick-start) ->
  [Architecture](reference/ARCHITECTURE.md) ->
  [Concept walkthrough](reference/CONCEPT_WALKTHROUGH.md) ->
  [Public API reference](reference/REFERENCE.md) ->
  [CLI](reference/CLI.md) ->
  [Development](DEVELOPMENT.md)
- **Examiner or reviewer:** [Overview](OVERVIEW.md) ->
  [Research overview](research/RESEARCH_OVERVIEW.md) ->
  [Security model](reference/SECURITY_MODEL.md) ->
  [Status](evidence/STATUS.md) ->
  [Claim ledger](evidence/CLAIMS.md) ->
  [Contribution provenance](evidence/CONTRIBUTION_PROVENANCE.md)
- **AI agent:** [AGENTS.md](../AGENTS.md) ->
  [AI agent guide](AI_AGENT_GUIDE.md) ->
  [Development](DEVELOPMENT.md) ->
  [Formal semantics](reference/SEMANTICS.md) ->
  [Security model](reference/SECURITY_MODEL.md)

## Reference and evidence

- [Security model](reference/SECURITY_MODEL.md): normative rules, TCB, and
  operational boundary.
- [Formal semantics](reference/SEMANTICS.md): named invariants, transition
  rules, and current gaps.
- [Authority and influence proposal](decisions/029-authority-influence-and-policy-checker.md):
  proposed multi-principal and stateful checker semantics.
- [Policy checker contract](reference/POLICY_CHECKER.md): proposed checker
  interface and justification format.
- [Public API reference](reference/REFERENCE.md): supported Python and CLI
  surfaces.
- [Runtime](reference/RUNTIME.md): scenario and provider contracts.
- [Glossary](reference/GLOSSARY.md): canonical terminology.
- [SLED](reference/SLED.md): native bounded-checking semantics.
- [Evaluation](evidence/EVALUATION.md): result and trace evidence.
- [Negative controls](evidence/NEGATIVE_CONTROLS.md): deliberately defective
  variants.
- [Smoke result](evidence/MVP_RESULTS.md): bounded pipeline-readiness evidence.
- [Audit](evidence/AUDIT.md): automated repository invariants.
- [Claim ledger](evidence/CLAIMS.md): claim strength and limits.
- [Status](evidence/STATUS.md): short current-capability summary.
- [Task registry](evidence/task-registry.json): machine-readable status.
- [Change catalogue](evidence/CHANGE_CATALOG.md): report-derived work grouped by
  theme.

## Integrations and research

- [Model integrations](integrations/models.md) and
  [AgentDojo](integrations/agentdojo.md): optional model and benchmark
  boundaries.
- [Cedar](integrations/cedar.md): pinned local PDP contract and offline
  preflight.
- [Verification backends](integrations/verification.md): optional solver and
  model dependencies.
- [Research overview](research/RESEARCH_OVERVIEW.md): reviewer-facing problem
  statement and Part C direction.
- [Research questions](research/RESEARCH_QUESTIONS.md): open questions and
  evidence requirements.
- [Related work](research/RELATED_WORK.md): positioning, not implementation
  status.
- [Report sources and analysis](../research/reports/README.md): reconciled
  historical inputs.
- [Publication register](../research/publications/README.md): audience and goal
  of each retained publication.
- [Fourth-year report](../research/publications/manuscript/README.md): progress
  report for the fourth-year reviewer.
- [arXiv preprint](../research/publications/arxiv/README.md): current preprint
  and submission record.

## Canonical owners

| Question | Canonical owner |
|---|---|
| What does the system enforce? | code, tests, schemas, and the security model |
| Why was a design selected? | accepted ADR or specification |
| What is implemented? | `evidence/STATUS.md` and `evidence/task-registry.json` |
| What may be claimed? | `evidence/CLAIMS.md` and the retained evidence |
| What did reports recommend? | `research/reports/analysis/` |
| Which publication makes which claim? | `research/publications/README.md` and each artifact |

When sources disagree, record and repair the discrepancy. Do not silently
promote a report, manuscript sentence, or passing test above the normative
security contract.

## Not documentation

The following are not navigation targets for current behaviour:

- `.local/` contains working notes and raw logs. It is not shipped and is not
  canonical.
- `research/output/` contains generated run output. Read it through the bundle's
  `SUMMARY.md` or the claim ledger, not as hand-written guidance.
- `research/reports/archive/` and `research/publications/paper/` are frozen
  historical records.
- A passing test is evidence for the tested behaviour, not a general claim.
