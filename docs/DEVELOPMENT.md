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

The solver boundary is the sharpest example, because it moves with the host. The
declared gate environment installs `.[dev,visualisation]` and carries no solver,
`scripts/validate.py` deliberately does not run solver-carrying `--check` steps,
and the positive `BOUNDED_SAFE`/`UNSAFE` results, including the counterexample
trace, appear only where a solver exists. A solver-dependent assertion must
therefore accept the documented unavailable verdict instead of failing, and
changes to the verification paths should be checked in an environment that has
the solver:

```bash
.local/venv-z3/bin/python -m pytest tests/test_plan_ir_extensions.py tests/test_verification_ir.py -q
```

That command passed 29 tests on 2026-10-09 with z3-solver 5.1.0.

Retained bundles that carry solver results follow the same rule, and the
measurements below show the boundary moving as this host gained the optional
backends during 2026-10-09:

| Environment | `generate_coi_scaling.py --check` | `generate_defence_evidence.py --check` | `generate_sledv_scaling_evidence.py --check` |
| --- | --- | --- | --- |
| `.venv`, no solver (baseline) | 1 | 1 | 1 |
| `.venv`, z3-solver 5.1.0.0 present | 0 | 0 | 0 |
| `.venv`, z3 and nuXmv 2.2.0 on `PATH` | 0 | 1 | 0 |

The last row is the one to keep in mind: the defence-model bundle records nuXmv
availability, so a bundle that says "nuXmv unavailable" is only reproducible on a
host where nuXmv is absent. Installing an optional backend is a change of
measurement environment, not just of tooling; record the environment with the
bundle instead of letting a local install silently change a `--check` outcome.

The compensating control holds in every one of those environments, because the
reproducibility tests branch on availability rather than assuming it:
`tests/test_defence_model_evidence.py`, `tests/test_coi_scaling_evidence.py` and
`tests/test_verification_ir.py` pass with both backends present (41 tests,
2026-10-09). Do not add a solver-carrying `--check` step to the gate. A host
without an optional backend records the unavailability marker and keeps the last
measured values with their source revision, so the boundary stays visible in the
bundle instead of disappearing from it.

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

nuXmv is optional and licence-gated. It has no package on PyPI or in the apt
index, so it cannot be installed like the two above. FBK publishes it directly
at <https://nuxmv.fbk.eu/download.html>, and the bundled `LICENSE.txt` permits
academic and non-commercial research use only while forbidding modification and
redistribution. Never vendor the tarball, bake it into an image, or ship it in
the artefact bundle; install it per host.

The backend finds nuXmv through `shutil.which("nuXmv")`, runs `nuXmv -h` for the
version line and `nuXmv -int model.smv` for the IC3 query, and reports
`optional_binary_unavailable:nuXmv` when the binary is absent. It uses the
version line as the recorded solver fingerprint, so the install must not emit
loader warnings: machine-local paths in a fingerprint would not reproduce.

Installed on this host on 2026-10-09 against version 2.2.0 (4 June 2026), from
the vendor URL with the published SHA-256 verified:

```bash
# Fetch the tarball and the vendor's digest, then check them.
curl -fsSO https://nuxmv.fbk.eu/downloads/2.2.0/nuXmv-2.2.0-linux64.tar.xz
curl -fsSO https://nuxmv.fbk.eu/downloads/2.2.0/nuXmv-2.2.0-linux64.tar.xz.sha256sum
sha256sum -c nuXmv-2.2.0-linux64.tar.xz.sha256sum

# Unpack into a user prefix, never into the repository.
mkdir -p ~/.local/opt/nuxmv-2.2.0
tar -xf nuXmv-2.2.0-linux64.tar.xz -C ~/.local/opt/nuxmv-2.2.0 --strip-components=1
```

Two compatibility libraries are then needed on a current Ubuntu host. The
vendor's own `usr/local/bin/nuXmv.sh` cannot be used as-is, because it puts the
whole bundled library directory first on the search path: that directory holds an
older `libc.so.6`, which the system `libstdc++.so.6` rejects, and a
`libxml2.so.2` built against ICU 70, which Ubuntu 26.04 no longer ships (it has
`libxml2.so.16` and ICU 78). Keeping the vendor's `libxml2.so.2` and supplying
ICU 70 beside it avoids the symbol-version warning that the system `libxml2.so.16`
would produce:

```bash
# The vendor's libxml2.so.2, plus the ICU 70 runtime it was built against
# (Ubuntu 22.04 libicu70, unpacked locally with dpkg-deb -x).
mkdir -p ~/.local/opt/nuxmv-compat
ln -sf ~/.local/opt/nuxmv-2.2.0/usr/local/lib/x86_64-linux-gnu/libxml2.so.2 ~/.local/opt/nuxmv-compat/libxml2.so.2
ln -sf libicuuc.so.70.1 ~/.local/opt/nuxmv-compat/libicuuc.so.70
ln -sf libicudata.so.70.1 ~/.local/opt/nuxmv-compat/libicudata.so.70

# A launcher that prepends only that directory, then execs the real binary.
mkdir -p ~/.local/opt/nuxmv-bin
cat > ~/.local/opt/nuxmv-bin/nuXmv <<'EOF'
#!/bin/sh
root="$HOME/.local/opt/nuxmv-2.2.0/usr/local"
LD_LIBRARY_PATH="$HOME/.local/opt/nuxmv-compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH
exec "$root/bin/nuXmv" "$@"
EOF
chmod 755 ~/.local/opt/nuxmv-bin/nuXmv
ln -sf ~/.local/opt/nuxmv-bin/nuXmv ~/.local/bin/nuXmv
```

Then `conflux verify --model model.json --backend nuxmv` reaches the IC3 path.

Installing an optional backend also moves the evidence boundary described under
"Offline and optional evidence": bundles record backend availability, so a
bundle that says "nuXmv unavailable" is only reproducible on a host where nuXmv
is absent. Record the environment that produced a bundle, and re-measure
deliberately rather than letting a local install change `--check` outcomes.

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
