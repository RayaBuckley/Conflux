# Testing and Validation

Tests live in `tests/` and should validate security invariants before
implementation details. The current suite covers core artifacts and
provenance, authorisation, operations, policies, ITES mediation/state, and
selected SLED benchmark runners. Tests are organised by purpose: unit,
security invariant, integration, adapter, benchmark smoke, and reproducibility
tests.

Run the complete local validation workflow with:

```powershell
.\scripts\validate.ps1
```

The workflow uses the project-local `.venv` and runs tests first, followed by
Ruff and mypy. Create or refresh that environment with:

```powershell
.\scripts\setup.ps1
```

If direct execution is needed, use the venv interpreter explicitly:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest --cov=src/conflux --cov-report=term-missing --cov-report=html
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m mypy src
```

The HTML report is written to `htmlcov/` as local output. Coverage is currently
reported and baselined, not enforced at an arbitrary threshold. Focused checks
can use normal pytest selectors, for example
`python -m pytest tests/test_provenance.py -k immutable`.

For the minimal ITES path, run only the self-contained MVP tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ites_mvp.py -v
.\.venv\Scripts\python.exe -c "from conflux.ites.mvp import MVPExplorer; print('MVP import OK')"
```

The full suite currently includes deferred legacy SLED compatibility work and
may fail during collection until the `Evaluator`/`EvaluationResult` facade and
other older APIs are restored. That work is separate from MVP validation.

The configured checks are defined in `pyproject.toml`: pytest discovers tests
under `tests`, Ruff uses the project line length and import rules, and mypy runs
in strict mode for Python 3.12.

`.venv/` is local development state and must not be committed. Rerun
`scripts\setup.ps1` to refresh dependencies after changing `pyproject.toml`.

New security behaviour should include allowed, denied, mixed-Principal Context,
provenance-preservation, immutability, and recursive-execution cases.
Provider adapters, external benchmark adapters, trace classification,
reporting, and consent/visibility interactions require additional integration
coverage as they become execution-critical. Prefer stable fixtures and assert
observable guarantees rather than private implementation details.
