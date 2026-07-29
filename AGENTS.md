# Conflux repository guidance

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
- `tests`: offline unit, security, integration, and reproducibility tests.
- `docs`: architecture, contracts, decisions, status, and workflows.
- `paper`: archived LaTeX research artefact and post-paper reference.

## Non-negotiable invariants

- Provenance is never silently discarded.
- Principal Context is evaluated at action time.
- Authorisation, visibility, and consent are separate decisions.
- Consent never manufactures authority.
- Domain and ITES do not import benchmark-specific behavior.
- Evaluation code measures defences and does not encode benchmark shortcuts.

## Engineering rules

Use Python 3.12+, type hints, immutable dataclasses where practical, explicit
dependency injection, and pure functions for domain logic. Keep public APIs
small and documented. Add regression tests for every security invariant.

## Required workflow

Inspect the architecture and affected APIs, write a decision-complete feature
specification, implement the smallest coherent change, run
`scripts\validate.ps1`, update documentation and status, and review the diff.
Use `scripts\audit_repository.py` during AI-assisted changes.

## Terminology and paper policy

Use `Principal Context` and `Principal`; use `User` only for an explicitly
human user. The paper is archived reference material. Synchronise terminology
and record material implementation divergence as post-paper work; do not alter
paper claims silently.

## Definition of done

Implementation, tests, documentation, terminology, audit checks, and relevant
benchmark compatibility are complete. Generated caches, local environments,
and experiment outputs are not committed.
