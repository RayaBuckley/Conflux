# Development

Use Python 3.12 or newer.

```powershell
.\scripts\setup.ps1
.\scripts\validate.ps1
```

The portable validator runs audit, pytest with branch coverage, Ruff, strict
mypy, schema/regeneration checks, and package build/install/import checks.
Every security change requires allowed,
denied, empty, mixed-Principal Context, provenance, immutability, nested,
failure, and deterministic trace cases where applicable.

The 90% branch-coverage gate measures the credential-free offline core.
Optional process/network/binary boundaries—live model clients, AgentDojo,
container code execution, Z3, and nuXmv—are excluded from that aggregate
because their exhaustive paths require manual external jobs. They still have
offline contract, failure, parser, command-construction, or mock-runner tests.
Manual workflows retain their own logs and artefacts.

Read the architecture and security model, write a feature specification, make
one coherent change, update evidence/status, run validation, and review the
diff. Raw experiment outputs and local environments are not committed.
