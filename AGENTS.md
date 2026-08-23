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

See [docs/AI_AGENT_GUIDE.md](docs/AI_AGENT_GUIDE.md) for the change
workflow, review checklist, and commit message convention. For setup
and testing instructions, see [Development](docs/DEVELOPMENT.md) and the
[quick start](README.md#run-the-offline-system).

## Validation tooling

The repository has a multi-layer validation pipeline orchestrated by
`scripts/validate.py`.  AI agents should run `python scripts/validate.py`
before committing.  The following checkers are included:

- **ruff** — linting with a broad rule set (`E`, `F`, `I`, `UP`, `RUF`,
  `SIM`, `PERF`, `B`, `PIE`, `FURB`, `COM`, `C4`, `PTH`, `N`, `DTZ`,
  `S`, `PL`, `TRY`, `EM`, `FBT`, `LOG`, `G`, `RET`, `ERA`, `PT`, `ARG`,
  `ANN`, `SLF`, `INP`, `TC`, `D`).  Per-file ignores are configured in
  `pyproject.toml` for tests, scripts, and specific modules.
- **mypy** — strict type checking (`src`, `tests`, `scripts`).  mypy is
  the sole type-checking authority; Pyright/Pylance is configured with
  warnings (not errors) for supplemental IDE feedback only.
- **pytest** — full test suite with branch coverage (threshold: 89%).
- **yamllint** — YAML validation (`.yamllint.yml`).
- **vulture** — dead-code detection (`scripts/vulture_whitelist.py`).
- **pip-audit** — dependency vulnerability scanning (informational).
- **markdownlint-cli2** and **cspell** — via `scripts/validate_extensions.py`.
- **Schema validation** — 37 JSON schemas validated by
  `scripts/validate_schemas.py`.
- **Repository audit** — structural and governance checks via
  `scripts/audit_repository.py`.
- **Wheel build + smoke** — `python -m build` followed by
  `scripts/validate_wheel.py`.

### Quick commands for AI agents

```
python -m ruff check .                    # lint
python -m ruff check --fix .              # auto-fix lint
python -m mypy . --no-error-summary       # type check
python -m pytest tests -x -q              # run tests
python -m yamllint -c .yamllint.yml .     # YAML lint
python -m vulture src/conflux scripts/vulture_whitelist.py --min-confidence 60  # dead code
```
