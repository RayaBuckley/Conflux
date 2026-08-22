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
4. Run `python scripts/validate.py` before every review boundary. PowerShell
   users may call `.\scripts\validate.ps1`.
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
