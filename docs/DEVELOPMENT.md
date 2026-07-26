# Conflux Development

Purpose: define the repeatable workflow for human and AI-assisted changes.

Owner: repository maintainers. This is the operational source of truth for
setup, validation, testing, and change review; architectural rationale belongs
in `ARCHITECTURE.md` and durable decisions belong in `decisions/`.

## Workflow

1. Read `README.md`, `ARCHITECTURE.md`, and the affected rows in `AUDIT.md`.
2. Identify the owning API and write a decision-complete feature specification.
3. Implement the smallest change that preserves provenance and Principal
   Context invariants.
4. Add security and regression tests before broad refactoring.
5. Update module docstrings, status, and the owning documentation page.
6. Run the repository audit, tests, Ruff, mypy, and compile/import checks.
7. Review the diff and commit one coherent change.

## Setup and validation

```powershell
.\scripts\setup.ps1
.\scripts\validate.ps1
```

The project targets Python 3.12+. The scripts use the repository `.venv`,
which is ignored by Git. The Microsoft Store Python alias may require running
the scripts from a host shell with access to `WindowsApps`.

Direct checks:

```powershell
.\.venv\Scripts\python.exe scripts\audit_repository.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m mypy src
```

## Required evidence

Security changes require allowed, denied, mixed-Principal Context,
provenance, immutability, nested-execution, visibility, and consent coverage
where relevant. Benchmark integrations must remain optional and offline core
tests must not require external services.

## AI change contract

Use [FEATURE_SPEC.md](templates/FEATURE_SPEC.md) before implementation and
[CHANGE_CHECKLIST.md](templates/CHANGE_CHECKLIST.md) before completion. Never
invent a new public abstraction without adding its ledger entry, owner,
docstring contract, tests, and documentation link.
