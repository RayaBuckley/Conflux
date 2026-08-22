# Conflux repository guidance (for AI agents)

## Purpose

Conflux researches principal-aware security for AI agents. An agent may be
influenced by multiple Principals; permissions are therefore derived from the
current Principal Context and provenance, not static prompt trust labels.

## Priorities

1. Security-model correctness.
2. Faithfulness to organisational access control.
3. Reproducibility.
4. Extensibility.
5. Performance.

## Repository map

- `src/conflux/domain`: immutable security-domain values and action taxonomy.
- `src/conflux/execution`: provenance-preserving transformations.
- `src/conflux/policy`, `application`: policy decisions and composition.
- `src/conflux/ites`: canonical security boundary and mediation.
- `src/conflux/adapters`: external policy, provider, and benchmark adapters.
- `src/conflux/evaluation`: SLED bounded verification and evaluation services.
- `src/conflux/planning`: authenticated dynamic plans and bounded execution.
- `src/conflux/verification`: serialisable formal subset and optional backends.
- `tests`: offline unit, security, integration, and reproducibility tests.
- `docs`: architecture, contracts, decisions, status, and workflows.
- `publications/manuscript`: current LaTeX paper and evidence-controlled generated inputs.
- `reports/analysis`: current synthesis of immutable historical reports.
- `reports/archive` and `publications/paper`: integrity-protected historical evidence.

## Non-negotiable invariants

- Provenance is never silently discarded.
- Principal Context is evaluated at action time.
- Authorisation, visibility, and consent are separate decisions.
- Consent never manufactures authority.
- Domain and ITES do not import benchmark-specific behavior.
- Evaluation code measures defences and does not encode benchmark shortcuts.

## Workflow and conventions

See [WORKFLOW.md](WORKFLOW.md) for the change workflow, review
checklist, and commit message convention. See
[docs/AI_AGENT_GUIDE.md](docs/AI_AGENT_GUIDE.md) for the AI-agent
collaboration contract, trust order, documentation routing, and stop
conditions.
