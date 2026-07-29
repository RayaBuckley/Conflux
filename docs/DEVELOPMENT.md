# Development

Use Python 3.12 or newer.

```powershell
.\scripts\setup.ps1
.\scripts\validate.ps1
```

The portable validator runs audit, pytest with branch coverage, Ruff, strict
mypy, and a package import check. Every security change requires allowed,
denied, empty, mixed-Principal Context, provenance, immutability, nested,
failure, and deterministic trace cases where applicable.

Read the architecture and security model, write a feature specification, make
one coherent change, update evidence/status, run validation, and review the
diff. Raw experiment outputs and local environments are not committed.
