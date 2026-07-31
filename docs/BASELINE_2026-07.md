# Conflux baseline: July 2026

## Snapshot

- Source commit: `26213bf042c5a94b5d8428974637c4abdcbc22c1`
- Python: CPython 3.12.12
- Platform: Windows
- Captured: 29 July 2026
- Validation evidence: `artifacts/validation/26213bf042c5/`

The source commit is the canonical-migration commit sequence rebased onto the
new report package. The working tree was clean, and the source package now
archived under `reports/archive/2026-07-29-implementation-programme/` matched
`origin/main` byte for byte.

## Commands

```powershell
python -m pytest -q
python -m mypy src tests --no-error-summary
python -m ruff check src tests
python scripts/audit_repository.py
.\scripts\validate.ps1 -Python .\.test-venv\Scripts\python.exe
```

All commands passed. The complete validator reported 54 passing tests and
90.64% branch-aware coverage.

## Known incomplete work

- Ordered-plan proposal semantics are not yet implemented.
- Trace and result JSON Schemas, supported CLI, scenario loader, experiment
  manifests, and current-code result bundles do not yet exist.
- Model and benchmark integrations have no live pinned evidence.
- The explicit-state checker exists, but solver-backed verification,
  runtime-to-IR conformance, and state/trace performance comparison remain.
- Formal delegation remains unsupported and denied.
- The archived paper is not evidence for the canonical implementation.

These gaps are tracked in Feature Specification 009 and the change catalogue.
