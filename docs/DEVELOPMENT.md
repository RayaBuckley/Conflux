# Development

Use Python 3.12 or newer. Windows users can run `.\scripts\setup.ps1`; the
[root quick start](../README.md#run-the-offline-system) gives portable manual
setup. Local environments and ordinary run output are ignored.

## Testing ladder

Use the narrowest useful feedback first, then finish with the repository gate.

1. Run the affected unit or integration file with `python -m pytest -q`.
   Use `python -m pytest -m "not slow" -q` to skip slow (Hypothesis) tests.
2. Run Ruff and strict mypy over changed Python boundaries.
3. Run `python scripts/audit_repository.py` after architecture, evidence, or
   documentation changes.
4. Run `python scripts/validate.py` before every review boundary, at the
   depth the moment needs (`--tier quick` while iterating, `--tier standard`
   before a commit, the default full tier at infrequent checkpoints); the tier
   list is owned by `AGENTS.md`. PowerShell users may call
   `.\scripts\validate.ps1 -Tier standard`.
5. Review `git diff --check`, the staged diff, and the resulting evidence.

The portable validator checks the AST import graph, documentation and archive
integrity, JSON Schemas, deterministic smoke regeneration, pytest with branch
coverage, Ruff, strict mypy, wheel build/install, and installed CLI commands.

Security changes need explicit allow, deny, empty and mixed Principal Context,
provenance, immutability, nesting, revocation, failure, and deterministic-trace
cases where applicable. External boundaries need malformed, unsupported,
missing-dependency, timeout, and redaction tests. The semantic corpus and
executable mutants test system-wide invariants rather than implementation
details.

## Offline and optional evidence

The 90% branch-coverage gate measures the credential-free offline core.
Network, model, benchmark, container, solver, and cluster boundaries have
offline contract and failure tests, but their live results belong in explicit
optional workflows with retained manifests and logs. Missing optional access
is recorded as unavailable, not converted into a passing empirical claim.

The solver boundary is the sharpest example. The gate environment installs
`.[dev,visualisation]` and has no z3, so `verify_plan` returns the documented
`UNKNOWN` verdict there and the positive `BOUNDED_SAFE`/`UNSAFE` results,
including the counterexample trace, are only produced where the solver exists.
A z3-dependent assertion must therefore accept the documented unavailable
verdict instead of failing, and changes to the verification paths should be
checked in an environment that has the solver:

```bash
.local/venv-z3/bin/python -m pytest tests/test_plan_ir_extensions.py tests/test_verification_ir.py -q
```

That command passed 29 tests on 2026-10-09 with z3-solver 5.1.0.

Retained bundles that carry solver results follow the same rule. They are
regenerated in the environment that has the solver, so `--check` reports them
stale under the gate by construction: `scripts/generate_coi_scaling.py --check`,
`scripts/generate_defence_evidence.py --check`, and
`scripts/generate_sledv_scaling_evidence.py --check` exit 1 in `.venv` and 0 in
`.local/venv-z3` (measured 2026-10-09). `scripts/validate.py` therefore does not
run those checks, and the compensating control is the in-process reproducibility
tests (`tests/test_coi_scaling_evidence.py`,
`tests/test_defence_model_evidence.py`), which regenerate the bundle and assert
the recorded provenance in either environment. Do not add a solver-carrying
`--check` step to the gate. A host without an optional backend records the
unavailability marker and keeps the last measured values with their source
revision, so the boundary stays visible in the bundle instead of disappearing
from it.

## Rationale

Focused tests provide fast diagnosis; the full gate detects cross-boundary
drift that a local unit test cannot. Branch coverage is a floor rather than a
security guarantee, so adversarial cases and negative controls remain
mandatory. Building and running the installed wheel catches packaging and CLI
failures that editable-source tests can hide.

Read the relevant contract, write a decision-complete specification, implement
one coherent change, update the existing evidence and documentation owners,
then validate and review. Generated evidence is committed after the code that
produces it so the measured revision is unambiguous.

## Troubleshooting

### Python version

Conflux requires Python 3.12 or newer. Check with `python --version`. If
multiple versions are installed, use `py -3.12` (Windows) or a version
manager (`pyenv`, `mise`) to select the correct interpreter before creating
the virtual environment.

### Virtual environment activation on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

### Optional dependencies

Z3 solver (`z3-solver`) is optional. Without it, `conflux verify --backend z3`
returns `UNKNOWN` with exit code 3. Install with `pip install z3-solver`.

AgentDojo (`agentdojo`) is optional. Without it, `benchmark agentdojo`
preflight reports `not_installed`. Install with `pip install agentdojo`.

### CRLF / LF normalisation

The repository uses `.gitattributes` to manage line endings. If you see
checksum failures in evidence bundles, ensure Git is configured with
`core.autocrlf = input` on Windows. Run `git add --renormalize .` after
changing line-ending settings.

### Common mypy errors

- `Module "conflux" has no attribute` — install the package in editable mode
  (`pip install -e .`) or set `PYTHONPATH=src`.
- `Import "pytest" could not be resolved` — install dev dependencies
  (`pip install -e ".[dev]"`).
- `Import "hypothesis" could not be resolved` — install dev dependencies.

### Cedar binary checksum mismatch

The `doctor --cedar-binary` command checks the SHA-256 of the supplied binary
against the pinned identity. If the checksum differs, download the pinned
version or omit `--cedar-binary` to report `binary_not_supplied`.

### Extension checks (advisory)

The repository includes configuration files for VS Code extensions that
suppress false positives and standardise style:

- `.markdownlint-cli2.jsonc` — markdownlint rule configuration.
- `cspell.json` — spell-checker word list (British English, `en-GB`).
- `.vscode/ltexrc.json` — LTeX grammar and spell-check configuration (British English).
- `.editorconfig` — editor indentation and line-ending conventions.

Run `python scripts/validate_extensions.py` to execute markdownlint, cspell,
and LTeX checks from the command line. The script uses `npx` for the
Node.js tools (`npm install` to set up) and the VS Code extension's bundled
LTeX CLI. It exits 0 when all available tools pass or when no tools are
installed. The `validate.py` entry point runs this script as a non-blocking
advisory step.
