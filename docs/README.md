# Conflux Documentation

This is the documentation entry point. Each page has one job and links to the
next level of detail.

## Start here

- [Architecture](ARCHITECTURE.md): system boundary, layers, dependencies, and
  security invariants.
- [Reference](REFERENCE.md): canonical concepts and public API ownership.
- [Audit ledger](AUDIT.md): purpose, evidence, disposition, and risk for every
  tracked file.
- [Glossary](GLOSSARY.md): required Principal and Principal Context terminology.

## Build and evaluate

- [Development](DEVELOPMENT.md): setup, validation, testing, and AI workflow.
- [Evaluation](EVALUATION.md): SLED methodology, benchmarks, evidence, and
  reproducibility.
- [Status](STATUS.md): implemented, blocked, and post-paper work.

## Decisions and templates

- [Architecture decisions](decisions/README.md): durable security and design
  decisions.
- [Feature specification](templates/FEATURE_SPEC.md): decision-complete change
  contract.
- [Change checklist](templates/CHANGE_CHECKLIST.md): completion and review gate.

## Reading paths

- New reviewer: `README.md` → Architecture → Reference → Audit.
- Implementer: Architecture → Audit → Development → affected module docstring.
- Security reviewer: Reference → ITES source → provenance/authorisation tests.
- Evaluation reviewer: Evaluation → SLED source → traces, metrics, and results.

The paper under `paper/` is an archived research artifact. New functionality
is post-paper work and must be labelled as such in Status and Evaluation.
