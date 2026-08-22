# Scripts guidance

Scripts are the validation and evidence-generation layer. `validate.py` is the
portable entry point that chains audit, schema checks, deterministic
regeneration, pytest, Ruff, mypy, wheel build, and CLI smoke.
`audit_repository.py` enforces structural and documentation invariants.

When adding or modifying scripts:

- Keep scripts dependency-free or use only `dev` dependencies; never add
  runtime dependencies.
- Evidence-generation scripts must be deterministic: given the same input and
  source commit, they produce identical output. Use `--check` mode to verify
  retained evidence has not drifted.
- Do not hardcode absolute paths; resolve paths from `Path(__file__).parent`.
- Validation scripts must fail with a non-zero exit code and a clear message;
  never silently pass on degraded evidence.
