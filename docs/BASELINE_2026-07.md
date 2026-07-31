# Conflux validated baseline: July 2026

## Current snapshot

| Field | Value |
|---|---|
| Source commit | `6fe6b584500e84f2cbc3d15876865243c4f01440` |
| Captured | 31 July 2026 |
| Runtime | CPython 3.12.12 on Windows |
| Retained evidence | `artifacts/validation/6fe6b584500e/` |
| Cross-platform CI | [run 30659302041](https://github.com/RayaBuckley/Conflux/actions/runs/30659302041): all four matrix jobs passed |
| Manuscript CI | [run 30659302028](https://github.com/RayaBuckley/Conflux/actions/runs/30659302028): passed |
| Result | 220 tests; 90.25% branch coverage; all validation stages passed |

The snapshot includes the portable archive checks, consolidated documentation
and report archive, and synchronized current manuscript. The evidence records
the exact source commit tested; later documentation-only commits do not alter
that historical result.

## Reproduce it

```powershell
.\.test-venv\Scripts\python.exe scripts\validate.py
```

The portable validator runs the repository audit, all 13 JSON Schema checks,
deterministic smoke regeneration, pytest with the 90% coverage floor, Ruff,
strict mypy, wheel build, and clean installed-wheel CLI smoke. Use
`scripts/validate.ps1` as the PowerShell wrapper or `python scripts/validate.py`
on any supported platform.

## Evidence boundary

This baseline proves that the offline implementation and repository contracts
passed on the recorded platform and commit. It is not evidence of production
deployment security, live-model utility, external AgentDojo efficacy, solver
binary availability, Docker isolation, or cluster execution. Those claims need
their own retained, versioned results.

## Rationale

A commit-addressed baseline prevents mutable documentation from becoming the
evidence for its own claims. One portable command also keeps local, installed-
wheel, and CI behavior aligned while optional infrastructure remains explicit.
